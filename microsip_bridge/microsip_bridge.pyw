"""
MicroSIP Bridge for ERPNext (GUI & Background Service)
======================================================
Windows GUI App & Background Service.
- UI-based Configuration (Tkinter)
- Auto-detects MicroSIP history.xml
- Runs silently in background / tray
- Single installation - auto-starts on Windows login
"""

import os
import sys
import json
import time
import logging
import threading
import configparser
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Try importing requests and pystray/Pillow for tray icon
try:
    import requests
except ImportError:
    requests = None

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


# ── File Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
STATE_FILE = os.path.join(BASE_DIR, "sent_calls.json")
LOG_FILE = os.path.join(BASE_DIR, "microsip_bridge.log")

# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("MicroSIPBridge")

# Add stdout handler if console exists
if sys.stdout:
    log.addHandler(logging.StreamHandler(sys.stdout))


# ── Helper Functions ───────────────────────────────────────────────────────
def get_default_history_path():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        path = os.path.join(appdata, "MicroSIP", "history.xml")
        return path if os.path.exists(path) else path
    return r"C:\Users\Default\AppData\Roaming\MicroSIP\history.xml"


def load_config():
    cfg = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        cfg.read(CONFIG_FILE, encoding="utf-8")
    return cfg


def save_config(url, api_key, api_secret, history_file):
    cfg = configparser.ConfigParser()
    cfg["erpnext"] = {
        "url": url.strip().rstrip("/"),
        "api_key": api_key.strip(),
        "api_secret": api_secret.strip(),
    }
    cfg["microsip"] = {
        "history_file": history_file.strip(),
        "poll_interval": "3",
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_state(sent_set):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(sent_set), f, indent=2)
    except Exception as e:
        log.warning(f"Could not save state: {e}")


CALL_TYPE = {0: "Inbound", 1: "Outbound", 2: "Missed"}

def parse_history(history_file: str) -> list[dict]:
    if not history_file or not os.path.exists(history_file):
        return []
    try:
        tree = ET.parse(history_file)
        root = tree.getroot()
        calls = []
        for call_el in root.findall("call"):
            number   = (call_el.findtext("number") or "").strip()
            date_str = (call_el.findtext("date")   or "0").strip()
            dur_str  = (call_el.findtext("duration") or "0").strip()
            type_str = (call_el.findtext("type")   or "0").strip()

            try:
                date_ts  = int(date_str)
                duration = int(dur_str)
                type_int = int(type_str)
            except ValueError:
                continue

            call_id   = f"{number}_{date_ts}"
            direction = CALL_TYPE.get(type_int, "Outbound")
            status    = "Completed" if duration > 0 else "Missed"

            calls.append({
                "id":        call_id,
                "number":    number,
                "date":      date_ts,
                "duration":  duration,
                "type_int":  type_int,
                "direction": direction,
                "status":    status,
            })
        return calls
    except Exception as e:
        log.error(f"Error parsing history.xml: {e}")
        return []


def post_call_to_erpnext(url, api_key, api_secret, call: dict) -> tuple[bool, str]:
    if not requests:
        return False, "requests module missing"
    
    endpoint = f"{url.rstrip('/')}/api/method/customer_crm.customer_crm.api.call_api.update_call_from_microsip"
    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
        "Content-Type": "application/json",
    }
    payload = {
        "phone_number":   call["number"],
        "duration":       call["duration"],
        "call_time_unix": call["date"],
        "call_id":        call["id"],
        "direction":      call["direction"],
        "status":         call["status"],
    }
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            res = resp.json().get("message", {})
            st = res.get("status") if isinstance(res, dict) else "ok"
            return True, f"Success ({st})"
        elif resp.status_code in (401, 403):
            return False, f"Auth Error HTTP {resp.status_code}: Check API credentials"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:150]}"
    except Exception as e:
        return False, str(e)


def test_erpnext_connection(url, api_key, api_secret):
    if not requests:
        return False, "Python 'requests' library is missing. Run installer again."
    url = url.strip().rstrip("/")
    endpoint = f"{url}/api/method/frappe.auth.get_logged_user"
    headers = {"Authorization": f"token {api_key}:{api_secret}"}
    try:
        resp = requests.get(endpoint, headers=headers, timeout=8)
        if resp.status_code == 200:
            user = resp.json().get("message", "User")
            return True, f"Connected successfully as: {user}"
        elif resp.status_code in (401, 403):
            return False, "Invalid API Key or Secret."
        else:
            return False, f"Server returned HTTP status {resp.status_code}"
    except Exception as e:
        return False, f"Could not connect to ERPNext: {e}"


# ── Background Worker Thread ───────────────────────────────────────────────
class BackgroundWorker(threading.Thread):
    def __init__(self, on_status_change=None):
        super().__init__(daemon=True)
        self.running = True
        self.on_status_change = on_status_change
        self.last_status = "Starting..."

    def update_status(self, msg):
        self.last_status = msg
        log.info(msg)
        if self.on_status_change:
            try:
                self.on_status_change(msg)
            except Exception:
                pass

    def stop(self):
        self.running = False

    def run(self):
        self.update_status("Worker started")
        sent_calls = load_state()
        last_mtime = 0

        while self.running:
            cfg = load_config()
            if "erpnext" not in cfg or "microsip" not in cfg:
                self.update_status("Waiting for configuration...")
                time.sleep(5)
                continue

            url = cfg["erpnext"].get("url", "")
            api_key = cfg["erpnext"].get("api_key", "")
            api_secret = cfg["erpnext"].get("api_secret", "")
            history_file = cfg["microsip"].get("history_file", "")

            if not url or not api_key or not api_secret:
                self.update_status("Configuration incomplete")
                time.sleep(5)
                continue

            if not os.path.exists(history_file):
                self.update_status(f"Waiting for MicroSIP history.xml at {history_file}")
                time.sleep(5)
                continue

            # First run check
            if not sent_calls and os.path.exists(history_file):
                existing = parse_history(history_file)
                for c in existing:
                    sent_calls.add(c["id"])
                save_state(sent_calls)
                self.update_status(f"Initialized: monitoring new calls (skipped {len(existing)} past calls)")

            try:
                cur_mtime = os.path.getmtime(history_file)
                if cur_mtime != last_mtime:
                    last_mtime = cur_mtime
                    all_calls = parse_history(history_file)
                    new_calls = [c for c in all_calls if c["id"] not in sent_calls]

                    for call in new_calls:
                        # Wait 3s if call ended very recently
                        if time.time() - call["date"] < 3:
                            continue

                        ok, msg = post_call_to_erpnext(url, api_key, api_secret, call)
                        sent_calls.add(call["id"])
                        save_state(sent_calls)
                        self.update_status(f"Synced Call {call['number']}: {msg}")

                self.update_status("Monitoring calls... (Active)")
            except Exception as e:
                log.error(f"Error in poll loop: {e}")
                self.update_status(f"Error: {e}")

            time.sleep(3)


# ── GUI Settings Window ───────────────────────────────────────────────────
class SettingsWindow:
    def __init__(self, root, worker=None, on_close_callback=None):
        self.root = root
        self.worker = worker
        self.on_close_callback = on_close_callback

        self.root.title("MicroSIP Bridge Settings")
        self.root.geometry("540x480")
        self.root.resizable(False, False)

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        # Main Container
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title Header
        lbl_title = ttk.Label(frame, text="MicroSIP ➔ ERPNext Bridge", font=("Segoe UI", 14, "bold"))
        lbl_title.pack(anchor=tk.W, pady=(0, 5))

        lbl_sub = ttk.Label(frame, text="Configure your ERPNext API connection and MicroSIP path", font=("Segoe UI", 9))
        lbl_sub.pack(anchor=tk.W, pady=(0, 15))

        # Form Fields
        form_frame = ttk.Frame(frame)
        form_frame.pack(fill=tk.X, expand=True)

        # ERPNext URL
        ttk.Label(form_frame, text="ERPNext Site URL:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=6)
        self.ent_url = ttk.Entry(form_frame, width=42)
        self.ent_url.grid(row=0, column=1, sticky=tk.W, pady=6, padx=(10, 0))

        # API Key
        ttk.Label(form_frame, text="API Key:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.ent_key = ttk.Entry(form_frame, width=42)
        self.ent_key.grid(row=1, column=1, sticky=tk.W, pady=6, padx=(10, 0))

        # API Secret
        ttk.Label(form_frame, text="API Secret:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.ent_secret = ttk.Entry(form_frame, width=42, show="•")
        self.ent_secret.grid(row=2, column=1, sticky=tk.W, pady=6, padx=(10, 0))

        # MicroSIP File Path
        ttk.Label(form_frame, text="MicroSIP history.xml:", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky=tk.W, pady=6)

        path_frame = ttk.Frame(form_frame)
        path_frame.grid(row=3, column=1, sticky=tk.W, pady=6, padx=(10, 0))

        self.ent_path = ttk.Entry(path_frame, width=30)
        self.ent_path.pack(side=tk.LEFT)

        btn_browse = ttk.Button(path_frame, text="Browse...", width=9, command=self.browse_file)
        btn_browse.pack(side=tk.LEFT, padx=(5, 0))

        # Auto Detect Button
        btn_autodetect = ttk.Button(form_frame, text="Auto Detect MicroSIP Path", command=self.auto_detect_path)
        btn_autodetect.grid(row=4, column=1, sticky=tk.W, pady=(2, 10), padx=(10, 0))

        # Divider
        ttk.Separator(frame, orient="horizontal").pack(fill=tk.X, pady=15)

        # Status Bar
        self.lbl_status = ttk.Label(frame, text="Status: Idle", font=("Segoe UI", 9, "italic"), foreground="#444444")
        self.lbl_status.pack(anchor=tk.W, pady=(0, 10))

        # Action Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        btn_test = ttk.Button(btn_frame, text="🔌 Test Connection", command=self.on_test_connection)
        btn_test.pack(side=tk.LEFT)

        btn_save = ttk.Button(btn_frame, text="💾 Save & Run in Background", command=self.on_save)
        btn_save.pack(side=tk.RIGHT, padx=(5, 0))

        # Load current config into fields
        self.load_fields()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_fields(self):
        cfg = load_config()
        url = cfg.get("erpnext", "url", fallback="https://erp.dressup.com.bd")
        key = cfg.get("erpnext", "api_key", fallback="")
        secret = cfg.get("erpnext", "api_secret", fallback="")
        path = cfg.get("microsip", "history_file", fallback=get_default_history_path())

        self.ent_url.insert(0, url)
        self.ent_key.insert(0, key)
        self.ent_secret.insert(0, secret)
        self.ent_path.insert(0, path)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select MicroSIP history.xml File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.ent_path.delete(0, tk.END)
            self.ent_path.insert(0, filename)

    def auto_detect_path(self):
        path = get_default_history_path()
        self.ent_path.delete(0, tk.END)
        self.ent_path.insert(0, path)
        if os.path.exists(path):
            messagebox.showinfo("Auto Detect", f"MicroSIP history file found:\n{path}")
        else:
            messagebox.showwarning("Auto Detect", f"Default path does not exist yet:\n{path}\n\nMake sure MicroSIP is installed and has made at least 1 call.")

    def on_test_connection(self):
        url = self.ent_url.get()
        key = self.ent_key.get()
        secret = self.ent_secret.get()

        if not url or not key or not secret:
            messagebox.showerror("Error", "Please fill in ERPNext URL, API Key, and API Secret.")
            return

        self.lbl_status.config(text="Status: Testing connection...", foreground="#0055ff")
        self.root.update_idletasks()

        ok, msg = test_erpnext_connection(url, key, secret)
        if ok:
            self.lbl_status.config(text=f"Status: {msg}", foreground="#00aa00")
            messagebox.showinfo("Success", msg)
        else:
            self.lbl_status.config(text=f"Status: Connection failed", foreground="#cc0000")
            messagebox.showerror("Connection Failed", msg)

    def on_save(self):
        url = self.ent_url.get()
        key = self.ent_key.get()
        secret = self.ent_secret.get()
        path = self.ent_path.get()

        if not url or not key or not secret or not path:
            messagebox.showerror("Error", "All fields are required.")
            return

        save_config(url, key, secret, path)
        messagebox.showinfo("Saved", "Configuration saved successfully!\n\nThe bridge will now run silently in the background.")
        
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.destroy()

    def on_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.destroy()


# ── System Tray Icon & Application App Class ─────────────────────────────
class MicroSIPBridgeApp:
    def __init__(self):
        self.worker = None
        self.tray_icon = None
        self.tk_root = None

    def create_tray_image(self):
        # Generate a small phone icon image for system tray
        image = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(image)
        # Draw a nice green circle with a white phone symbol / dot
        d.ellipse((4, 4, 60, 60), fill="#10b981", outline="#047857", width=3)
        d.rectangle((24, 20, 40, 44), fill="#ffffff")
        return image

    def open_settings_gui(self):
        if self.tk_root and self.tk_root.winfo_exists():
            self.tk_root.deiconify()
            self.tk_root.lift()
            return

        self.tk_root = tk.Tk()
        
        def on_close():
            self.tk_root.withdraw()

        SettingsWindow(self.tk_root, worker=self.worker, on_close_callback=on_close)
        self.tk_root.mainloop()

    def start(self):
        # Start worker thread
        self.worker = BackgroundWorker()
        self.worker.start()

        cfg = load_config()

        # If config is missing, open GUI immediately
        if "erpnext" not in cfg or not cfg.get("erpnext", "api_key", fallback=""):
            self.open_settings_gui()

        # If pystray is available, setup system tray icon
        if TRAY_AVAILABLE:
            menu = pystray.Menu(
                pystray.MenuItem("MicroSIP Bridge (Active)", lambda: None, enabled=False),
                pystray.MenuItem("⚙️ Settings", lambda: self.open_settings_gui()),
                pystray.MenuItem("📋 Open Log File", lambda: os.system(f'notepad "{LOG_FILE}"')),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Exit", lambda: self.stop())
            )
            self.tray_icon = pystray.Icon("MicroSIPBridge", self.create_tray_image(), "MicroSIP ➔ ERPNext Bridge", menu)
            self.tray_icon.run()
        else:
            # Fallback if pystray not installed: keep simple tk event loop alive hidden
            self.tk_root = tk.Tk()
            self.tk_root.withdraw()
            self.tk_root.mainloop()

    def stop(self):
        if self.worker:
            self.worker.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        if self.tk_root:
            self.tk_root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = MicroSIPBridgeApp()
    app.start()
