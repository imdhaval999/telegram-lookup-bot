from flask import Flask
import requests
import time
from datetime import datetime
import os
import threading
import re

# ===== KEEP ALIVE FOR RENDER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web, daemon=True).start()
# ================================

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render se environment variable
if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set in environment variables!")
    print("Please set BOT_TOKEN in Render Environment Variables")
    exit(1)

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MOBILE_API = "https://api.b77bf911.workers.dev/mobile?number="
AADHAAR_API = "https://api.b77bf911.workers.dev/aadhaar?id="
GST_API = "https://api.b77bf911.workers.dev/gst?number="
IFSC_API = "https://api.b77bf911.workers.dev/ifsc?code="
UPI_API = "https://api.b77bf911.workers.dev/upi?id="
FAM_API = "https://api.b77bf911.workers.dev/upi2?id="
VEHICLE_API = "https://api.b77bf911.workers.dev/vehicle?registration="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json"
}

# ================= HELPERS =================
def parse_address(addr):
    if not addr:
        return "Not Available"
    parts = addr.replace("!!", "!").split("!")
    parts = [x.title() for x in parts if x.strip()]
    return ", ".join(parts)

def send_message(chat_id, text):
    r = requests.post(
        TG_API + "/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=20
    )
    return r.json()["result"]["message_id"]

def delete_message(chat_id, message_id):
    requests.post(
        TG_API + "/deleteMessage",
        json={"chat_id": chat_id, "message_id": message_id},
        timeout=20
    )

def send_txt_file_with_caption(chat_id, filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    caption = (
        "✅ File Generated Successfully\n"
        f"📂 {filename}\n"
        "⏳ This message will auto-delete in 60s"
    )

    with open(filename, "rb") as f:
        r = requests.post(
            TG_API + "/sendDocument",
            files={"document": f},
            data={"chat_id": chat_id, "caption": caption},
            timeout=30
        )

    os.remove(filename)
    return r.json()["result"]["message_id"]

def auto_delete_file(chat_id, file_msg_id, delay=60):
    time.sleep(delay)
    delete_message(chat_id, file_msg_id)

# ================= TXT BUILDERS =================
def build_common_txt(d):
    address = parse_address(d.get("address"))
    return f"""
LOOKUP REPORT
-------------------

Name        : {d.get('name')}
Father Name : {d.get('father_name')}
Mobile      : {d.get('mobile')}
Alt Mobile  : {d.get('alt_mobile')}
Circle      : {d.get('circle')}
Address     : {address}
ID Number   : {d.get('id_number')}
Email       : {d.get('email') if d.get('email') else 'Not Available'}

Checked On  : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_gst_txt(d):
    addr = ", ".join(str(x) for x in [
        d.get("AddrBnm"), d.get("AddrBno"), d.get("AddrFlno"),
        d.get("AddrSt"), d.get("AddrLoc"), d.get("AddrPncd")
    ] if x)

    return f"""
GST LOOKUP REPORT
-------------------

GSTIN            : {d.get('Gstin')}
Trade Name       : {d.get('TradeName')}
Legal Name       : {d.get('LegalName')}
Address          : {addr}
State Code       : {d.get('StateCode')}
Taxpayer Type    : {d.get('TxpType')}
Status           : {d.get('Status')}
Block Status     : {d.get('BlkStatus')}
Registration Dt  : {d.get('DtReg')}
Deregistration Dt: {d.get('DtDReg') if d.get('DtDReg') else 'Not Available'}

Checked On       : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_ifsc_txt(d):
    return f"""
IFSC LOOKUP REPORT
-------------------

Bank Name    : {d.get('BANK')}
Bank Code    : {d.get('BANKCODE')}
IFSC Code    : {d.get('IFSC')}
Branch       : {d.get('BRANCH')}
Address      : {d.get('ADDRESS')}
City         : {d.get('CITY')}
District     : {d.get('DISTRICT')}
State        : {d.get('STATE')}
Contact      : {d.get('CONTACT')}
MICR         : {d.get('MICR')}
NEFT         : {d.get('NEFT')}
RTGS         : {d.get('RTGS')}
IMPS         : {d.get('IMPS')}
UPI          : {d.get('UPI')}
SWIFT        : {d.get('SWIFT') if d.get('SWIFT') else 'Not Available'}
ISO Code     : {d.get('ISO3166')}
Centre       : {d.get('CENTRE')}

Checked On   : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_upi_txt(d):
    return f"""
UPI LOOKUP REPORT
-------------------

Name                 : {d.get('name')}
VPA                  : {d.get('vpa')}
IFSC                 : {d.get('ifsc')}
Account Number       : {d.get('acc_no')}
Merchant             : {d.get('is_merchant')}
Merchant Verified    : {d.get('is_merchant_verified')}
Internal Merchant    : {d.get('is_internal_merchant')}
FamPay User          : {d.get('is_fampay_user')}
FamPay Username      : {d.get('fampay_username')}
FamPay First Name    : {d.get('fampay_first_name')}
FamPay Last Name     : {d.get('fampay_last_name')}

Checked On           : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_fam_txt(d):
    return f"""
FAM LOOKUP REPORT
-------------------

FAM ID      : {d.get('fam_id')}
Name        : {d.get('name')}
Phone       : {d.get('phone')}
Source      : {d.get('source')}
Status      : {d.get('status')}
Type        : {d.get('type')}

Checked On  : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_vehicle_txt(reg, data):
    """Build vehicle report from single API response"""
    return f"""
VEHICLE LOOKUP REPORT
---------------------

Registration Number : {reg}
Owner Name         : {data.get('owner_name', 'Not Available')}
Make / Model       : {data.get('make_model', 'Not Available')}
Fuel Type          : {data.get('fuel_type', 'Not Available')}
Vehicle Type       : {data.get('vehicle_type', 'Not Available')}
Registration Date  : {data.get('registration_date', 'Not Available')}
Registration Place : {data.get('registration_address', 'Not Available')}
Engine Number      : {data.get('engine_number', 'Not Available')}
Chassis Number     : {data.get('chassis_number', 'Not Available')}
Commercial Vehicle : {data.get('is_commercial', 'Not Available')}
Previous Insurer   : {data.get('previous_insurer', 'Not Available')}
Policy Expiry Date : {data.get('previous_policy_expiry_date', 'Not Available')}
Permanent Address  : {data.get('permanent_address', 'Not Available')}
Present Address    : {data.get('present_address', 'Not Available')}

Checked On         : {datetime.now().strftime('%d-%m-%Y')}
"""

# ================= VALIDATION FUNCTIONS =================
def is_mobile_number(text):
    """Check if text is a valid mobile number"""
    if not text.isdigit() or len(text) != 10:
        return False
    if text[0] not in '6789':
        return False
    return True

def is_aadhaar_number(text):
    """Check if text is a valid Aadhaar number"""
    if not text.isdigit() or len(text) != 12:
        return False
    if text[0] in '01':
        return False
    return True

def is_gstin(text):
    """Check if text is a valid GSTIN"""
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'
    return bool(re.match(pattern, text))

def is_ifsc_code(text):
    """Check if text is a valid IFSC code"""
    if len(text) != 11:
        return False
    if not text[:4].isalpha():
        return False
    if text[4] != '0':
        return False
    return True

def is_upi_id(text):
    """Check if text is a valid UPI ID"""
    return '@' in text and not text.endswith('@fam')

def is_fam_id(text):
    """Check if text is a valid FAM ID"""
    return '@' in text and text.endswith('@fam')

def is_vehicle_number(text):
    """Check if text is a valid vehicle number"""
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
    return bool(re.match(pattern, text))

# ================= BOT LOGIC =================
def process_message(chat_id, text):
    raw = text.strip()
    lower = raw.lower()
    
    # Remove command prefix if present for validation
    clean_text = raw
    if raw.startswith('/'):
        parts = raw.split(' ', 1)
        if len(parts) > 1:
            clean_text = parts[1].strip()
        else:
            clean_text = ""

    # ---------- /start ----------
    if lower == "/start":
        send_message(
            chat_id,
            "🔍 Lookup Bot\n\n"
            "📱 Mobile: /num 9876543210\n"
            "🆔 Aadhaar: /aadhaar 123456789012\n"
            "🏢 GST: /gst 24ABCDE1234F1Z5\n"
            "🏦 IFSC: /ifsc SBIN0000000\n"
            "💸 UPI: /upi username@bank\n"
            "👨‍👩‍👧‍👦 FAM: /fam username@fam\n"
            "🚗 Vehicle: /vehicle GJ01AB1234\n\n"
            "📄 Note: Result file auto-deletes in 60 seconds"
        )
        return

    # ---------- Direct info without command ----------
    if not raw.startswith('/'):
        if is_mobile_number(raw):
            send_message(
                chat_id,
                f"📱 Looks like you entered a mobile number!\n\n"
                f"💡 Please use:\n/num {raw}\n\n"
                f"📝 Example: /num {raw}"
            )
            return
            
        elif is_aadhaar_number(raw):
            send_message(
                chat_id,
                f"🆔 Looks like you entered an Aadhaar number!\n\n"
                f"💡 Please use:\n/aadhaar {raw}\n\n"
                f"📝 Example: /aadhaar {raw}"
            )
            return
            
        elif is_gstin(raw):
            send_message(
                chat_id,
                f"🏢 Looks like you entered a GSTIN!\n\n"
                f"💡 Please use:\n/gst {raw}\n\n"
                f"📝 Example: /gst {raw}"
            )
            return
            
        elif is_ifsc_code(raw):
            send_message(
                chat_id,
                f"🏦 Looks like you entered an IFSC code!\n\n"
                f"💡 Please use:\n/ifsc {raw}\n\n"
                f"📝 Example: /ifsc {raw}"
            )
            return
            
        elif is_upi_id(raw):
            send_message(
                chat_id,
                f"💸 Looks like you entered a UPI ID!\n\n"
                f"💡 Please use:\n/upi {raw}\n\n"
                f"📝 Example: /upi {raw}"
            )
            return
            
        elif is_fam_id(raw):
            send_message(
                chat_id,
                f"👨‍👩‍👧‍👦 Looks like you entered a FAM ID!\n\n"
                f"💡 Please use:\n/fam {raw}\n\n"
                f"📝 Example: /fam {raw}"
            )
            return
            
        elif is_vehicle_number(raw):
            send_message(
                chat_id,
                f"🚗 Looks like you entered a vehicle number!\n\n"
                f"💡 Please use:\n/vehicle {raw}\n\n"
                f"📝 Example: /vehicle {raw}"
            )
            return
            
        else:
            # Random text - NO RESPONSE
            return

    # ---------- /num ----------
    if lower.startswith("/num "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide mobile number\n💡 Example: /num 9876543210")
            return
            
        if not is_mobile_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid mobile number!\n\n"
                "💡 Example: /num 9876543210\n"
                "📌 Format: 10 digits, starts with 6-9"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(MOBILE_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", {}).get("data", {}).get("result", [])
            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_common_txt(r[0]))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /aadhaar ----------
    if lower.startswith("/aadhaar "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide Aadhaar number\n💡 Example: /aadhaar 123456789012")
            return
            
        if not is_aadhaar_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid Aadhaar number!\n\n"
                "💡 Example: /aadhaar 123456789012\n"
                "📌 Format: 12 digits, no spaces"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(AADHAAR_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", {}).get("result", [])
            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_common_txt(r[0]))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /gst ----------
    if lower.startswith("/gst "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide GSTIN\n💡 Example: /gst 24ABCDE1234F1Z5")
            return
            
        if not is_gstin(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid GSTIN!\n\n"
                "💡 Example: /gst 24ABCDE1234F1Z5\n"
                "📌 Format: 24ABCDE1234F1Z5"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(GST_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {}).get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_gst_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /ifsc ----------
    if lower.startswith("/ifsc "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide IFSC code\n💡 Example: /ifsc SBIN0000000")
            return
            
        if not is_ifsc_code(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid IFSC code!\n\n"
                "💡 Example: /ifsc SBIN0000000\n"
                "📌 Format: SBIN0000000 (11 chars, 5th char=0)"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(IFSC_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_ifsc_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /upi ----------
    if lower.startswith("/upi "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide UPI ID\n💡 Example: /upi username@bank")
            return
            
        if not is_upi_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid UPI ID!\n\n"
                "💡 Example: /upi username@bank\n"
                "📌 Format: Must contain @ symbol"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(UPI_API + clean_text, headers=HEADERS, timeout=30).json()
            arr = res.get("data", {}).get("data", {}).get("verify_chumts", [])
            if not arr:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_upi_txt(arr[0]))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /fam ----------
    if lower.startswith("/fam "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide FAM ID\n💡 Example: /fam username@fam")
            return
            
        if not is_fam_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid FAM ID!\n\n"
                "💡 Example: /fam username@fam\n"
                "📌 Format: Must end with @fam"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(FAM_API + clean_text, headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_fam_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- /vehicle ----------
    if lower.startswith("/vehicle "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide vehicle number\n💡 Example: /vehicle GJ01AB1234")
            return
            
        reg = clean_text.upper()
        if not is_vehicle_number(reg):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vehicle GJ01AB1234\n"
                "📌 Format: XX##XXX####"
            )
            return

        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")

        try:
            # Try v1 API
            res = requests.get(VEHICLE_API + reg, headers=HEADERS, timeout=30).json()
            
            if res.get("success"):
                # Use v1 API data
                address_data = res.get("address", {})
                content = build_vehicle_txt(reg, address_data)
                
                # Send file
                fid = send_txt_file_with_caption(
                    chat_id,
                    f"Vehicle_Report_{reg}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                    content
                )

                delete_message(chat_id, loading)
                threading.Thread(
                    target=auto_delete_file,
                    args=(chat_id, fid),
                  daemon=True
                ).start()
            else:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found for this vehicle")

        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "⚠️ Server error, please try again")
        return

    # ---------- Invalid command (starts with / but not valid) ----------
    # NO RESPONSE - just return
    return

# ================= START =================
def main():
    print("🤖 Bot is running...")
    offset = 0
    while True:
        try:
            upd = requests.get(TG_API + "/getUpdates", params={"timeout": 30, "offset": offset}).json()
            for u in upd.get("result", []):
                offset = u["update_id"] + 1
                if "message" in u and "text" in u["message"]:
                    process_message(u["message"]["chat"]["id"], u["message"]["text"])
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
