import smtplib
import os
import requests
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_benign_email(source):
    if os.path.isfile(source):
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()
    elif source.startswith("http://") or source.startswith("https://"):
        response = requests.get(source)
        return response.text
    else:
        return source


def extract_and_replace_names(text, victim_name):
    """
    Advanced name detection and replacement function
    Detects various name patterns and replaces them with the victim's name
    """

    # Common name patterns to detect and replace
    name_patterns = [
        # Greeting patterns: "Hi Michael", "Hello John", "Dear Sarah"
        (r'\b(Hi|Hello|Hey|Dear)\s+([A-Z][a-z]+)\b', r'\1 ' + victim_name),

        # Name with punctuation: "Michael,", "John:", "Sarah -", "Michael –"
        (r'\b([A-Z][a-z]+)(\s*[,:\-–—]\s*)', victim_name + r'\2'),

        # Name at start of line: "Michael this is urgent"
        (r'^([A-Z][a-z]+)(\s+)', victim_name + r'\2'),

        # Name in middle with dash/em-dash: "Michael – this is", "John - please"
        (r'\b([A-Z][a-z]+)(\s*[–—\-]\s*)', victim_name + r'\2'),

        # Possessive forms: "Michael's account", "John's information"
        (r"\b([A-Z][a-z]+)'s\b", victim_name + "'s"),

        # Name before newline or end of sentence
        (r'\b([A-Z][a-z]+)(\s*[.!?]*\s*$)', victim_name + r'\2'),
    ]

    # Apply replacements while preserving original structure
    modified_text = text
    replaced_names = set()

    for pattern, replacement in name_patterns:
        matches = re.findall(pattern, modified_text, re.MULTILINE | re.IGNORECASE)

        for match in matches:
            if isinstance(match, tuple):
                # Extract the actual name from the match
                original_name = match[1] if len(match) > 1 else match[0]
            else:
                original_name = match

            # Only replace if it looks like a real name (capitalized, 2+ chars, not common words)
            if (len(original_name) >= 2 and
                    original_name[0].isupper() and
                    original_name.lower() not in ['the', 'this', 'that', 'and', 'but', 'for', 'you', 'are', 'can',
                                                  'will', 'have', 'has', 'not', 'all', 'any', 'may', 'new', 'now',
                                                  'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put',
                                                  'say', 'she', 'too', 'use']):
                replaced_names.add(original_name)

        # Apply the pattern replacement
        modified_text = re.sub(pattern, replacement, modified_text, flags=re.MULTILINE | re.IGNORECASE)

    # Log what names were replaced for debugging
    if replaced_names:
        print(f"Names replaced: {', '.join(replaced_names)} → {victim_name}")

    return modified_text


def rewrite_benign_to_phishing_html(benign_text, mail_service, victim_name):
    """
    Enhanced version that includes name replacement before link injection
    """
    import html

    # STEP 1: Replace names with victim's name BEFORE any other processing
    personalized_text = extract_and_replace_names(benign_text, victim_name)

    # STEP 2: Apply phishing link injection (existing logic)
    phishing_link = f"http://{mail_service.lower()}-secure-verify.com/login"
    keywords = ["review", "access", "confirm", "check", "open",
                "update", "verify", "credentials", "login", "information"]

    injected = False

    def smart_link_replace_escaped(line):
        nonlocal injected
        for verb in keywords:
            pattern = rf"\b({verb})\b"
            if re.search(pattern, line, re.IGNORECASE):
                line = re.sub(
                    pattern,
                    rf'<a href="{phishing_link}">\1</a>',
                    line,
                    count=1,
                    flags=re.IGNORECASE
                )
                injected = True
                break
        return line

    html_lines = []
    for line in personalized_text.splitlines():
        escaped_line = html.escape(line, quote=True)
        replaced_line = smart_link_replace_escaped(escaped_line)
        html_lines.append(replaced_line)

    if not injected:
        html_lines.append(f'Please <a href="{phishing_link}">verify here</a> that you\'ve received my message.')

    return "<br>\n".join(html_lines)


def generate_phishing_email(username, mail_service, title, job_title, status, kids):
    def format_kids_message(kids):
        if not kids:
            return ""
        ages = [int(age.strip()) for age in kids.split(",") if age.strip().isdigit()]
        if not ages:
            return ""
        if len(ages) == 1:
            return f"especially with a young child aged {ages[0]}"
        return f"especially with children aged between {min(ages)} and {max(ages)}"

    kids_note = format_kids_message(kids)
    fake_link = f"http://{mail_service.lower()}-secure-verify.com/login"

    email_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f9f9f9;
                color: #333;
                padding: 20px;
            }}
            .email-container {{
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: auto;
            }}
            .header {{
                background-color: #0073e6;
                padding: 10px;
                text-align: center;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px 6px 0 0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                margin-top: 20px;
                background-color: #0073e6;
                color: #ffffff;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            .footer {{
                font-size: 12px;
                color: #888;
                margin-top: 30px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                SecureMail Internal Notification
            </div><br>
            <p>Dear {title} {username},</p>

            <p>As a valued {job_title} in our organization, and considering your {status} status{(" - " + kids_note) if kids_note else ""}, we want to ensure uninterrupted access to your {mail_service} account.</p>

            <p>We've detected system-wide updates affecting some user accounts. To avoid disruptions, please validate your credentials through our secure portal.</p>

            <a href="{fake_link}" class="button">Update Now</a>

            <p>If you've already completed this step, no further action is needed.</p>

            <div class="footer">
                © 2025 SecureMail IT Division · This is an internal security notification.<br>
                Please do not reply to this email.
            </div>
        </div>
    </body>
    </html>
    """
    return email_html


def send_email(from_email, to_email, subject, body_text, use_local=True, smtp_info=None):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    part = MIMEText(body_text, "html")
    msg.attach(part)

    try:
        if use_local:
            with smtplib.SMTP("localhost", 25) as server:
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_info["host"], smtp_info["port"]) as server:
                server.starttls()
                server.login(smtp_info["user"], smtp_info["pass"])
                server.sendmail(from_email, [to_email], msg.as_string())
        print(f"\nEmail sent successfully to {to_email}")
    except Exception as e:
        print(f"\nFailed to send email: {e}")


if __name__ == "__main__":
    print("=== Smart Phishing Tool (Combined Mode) ===")
    benign_input = input("Enter benign email (string, .txt path, URL, or leave empty to generate manually): ").strip()

    if benign_input:
        print("Loading benign email...")
        benign_text = load_benign_email(benign_input)
        username = input("Victim's name: ")
        mail_service = input("Mail service (e.g., Gmail): ")

        print("Personalizing email and injecting phishing links...")
        phishing_body = rewrite_benign_to_phishing_html(benign_text, mail_service, username)
    else:
        print("Manual email generation mode")
        username = input("Victim's name: ")
        mail_service = input("Mail service (e.g., Gmail): ")
        title = input("Title (Mr./Ms./Dr.): ")
        job_title = input("Job title: ")
        status = input("Personal status: ").lower()
        has_kids = input("Has kids? (y/N): ").lower()
        kids_ages = input("Enter kids' ages (comma-separated): ") if has_kids in ("y", "yes") else ""
        phishing_body = generate_phishing_email(username, mail_service, title, job_title, status, kids_ages)

    print("\n--- Phishing Email Preview ---\n")
    print(phishing_body)

    send_now = input("\nSend this email? (y/N): ").lower()
    if send_now in ("y", "yes"):
        from_email = input("From (e.g., joseph@company.com): ")
        to_email = input("To [default: victim@victim.local]: ") or "victim@victim.local"

        mode = input("Use local Postfix? (Y/n): ").lower()
        use_local = (mode != "no" and mode != "n")

        smtp_info = {}
        if not use_local:
            smtp_info["host"] = input("SMTP server (e.g., smtp.mail.com): ")
            smtp_info["port"] = int(input("SMTP port (e.g., 587): "))
            smtp_info["user"] = input("SMTP username: ")
            smtp_info["pass"] = input("SMTP password: ")

        subject = "Important: Immediate Action Required" if benign_input else "Account Security Update"
        send_email(from_email, to_email, subject, phishing_body, use_local, smtp_info if not use_local else None)
    else:
        print("Email sending cancelled.")