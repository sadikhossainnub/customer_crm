"""
MicroSIP Bridge for ERPNext (Console/CLI Wrapper)
=================================================
Launches microsip_bridge.pyw in GUI/Background mode.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYW_FILE = os.path.join(BASE_DIR, "microsip_bridge.pyw")

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system(f'start pythonw "{PYW_FILE}"')
    else:
        os.system(f'python3 "{PYW_FILE}"')
