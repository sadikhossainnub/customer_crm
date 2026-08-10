# MicroSIP ➔ ERPNext Bridge (GUI & Background Service)

Windows-এ একবার Install করলেই স্বয়ংক্রিয়ভাবে ব্যাকগ্রাউন্ডে সার্ভিস চালু থাকবে। কোনো কালো Command Prompt খুলবে না এবং `config.ini` ম্যানুয়ালি এডিট করা লাগবে না (সম্পূর্ণ Graphical UI-ভিত্তিক)।

---

## 🌟 বৈশিষ্ট্যসমূহ (Key Features)

1. **১-ক্লিকে ইনস্টলেশন (`install.bat`):**
   - Windows Startup ফোল্ডারে VBScript রেজিস্টার করে, যাতে পিসি অন হওয়ার সাথে সাথে Background-এ সার্ভিস চালু হয়।
2. **সম্পূর্ণ UI-ভিত্তিক Settings:**
   - Graphical Window-এর মাধ্যমে ERPNext URL, API Key, API Secret এবং MicroSIP path কনফিগার করা যায়।
   - **Auto Detect MicroSIP Path** বাটনে চাপ দিলে MicroSIP history.xml ফাইলটি নিজে থেকেই খুঁজে নেয়।
   - **Test Connection** বাটন দিয়ে API Credentials কাজ করছে কিনা সাথে সাথে পরীক্ষা করে দেখা যায়।
3. **System Tray Integration:**
   - Windows Taskbar Tray-এ ছোট Green Icon হয়ে রানিং থাকে। Right Click করে যেকোনো সময় **Settings** বা **Log File** দেখা যায়।

---

## 🚀 ইনস্টলেশন নিয়মাবলী (Step-by-Step)

### Step 1: `microsip_bridge` ফোল্ডার আপনার Windows PC-তে কপি করুন
সার্ভার থেকে `microsip_bridge` ফোল্ডারের সব ফাইল নামিয়ে আপনার পিসির যেকোনো ফোল্ডারে রাখুন (যেমন: `C:\microsip_bridge`).

### Step 2: `install.bat` ফাইলটিতে ডাবল-ক্লিক করুন
`install.bat` রান করলে:
- প্রয়োজনীয় পাইথন লাইব্রেরি ইনস্টল হবে।
- Windows Auto-Start রেজিস্টার হবে (পিসি রিবুট হলেও সার্ভিস সচল থাকবে)।
- **MicroSIP Bridge Settings** নামের একটি সুন্দর UI Window আপনার স্ক্রিনে ভেসে উঠবে।

### Step 3: UI-তে তথ্য দিন ও Save করুন
1. **ERPNext Site URL:** `https://erp.dressup.com.bd`
2. **API Key & Secret:** ERPNext (My Profile > API Access) থেকে নেওয়া Key এবং Secret বসান।
3. **MicroSIP history.xml:** "Auto Detect MicroSIP Path" চাপুন অথবা Browse করে ধরিয়ে দিন।
4. **🔌 Test Connection** বাটনে চাপ দিয়ে দেখে নিন Connected দেখায় কিনা।
5. **💾 Save & Run in Background** বাটনে চাপ দিন!

কাজ শেষ! এখন থেকে মাইক্রোসিপ দিয়ে কল শেষ হওয়া মাত্রই ERPNext-এ Duration এবং Status সরাসরি সেভ হয়ে যাবে।
