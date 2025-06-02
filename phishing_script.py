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

def rewrite_benign_to_phishing_html(benign_text, mail_service, sender_name="Joseph"):
    import html
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
    for line in benign_text.splitlines():
        escaped_line = html.escape(line, quote=True)
        replaced_line = smart_link_replace_escaped(escaped_line)
        html_lines.append(replaced_line)

    if not injected:
        html_lines.append(f'Please <a href="{phishing_link}">verify here</a> that you\'ve received my message.')
        html_lines.append(f"<i>Thanks, {html.escape(sender_name)}</i>")

    return "<br>\n".join(html_lines)

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
    print("=== Smart Phishing Mimic Tool (Stage 2) ===")
    benign_input = input("Enter benign email (text, .txt path, or URL): ")
    benign_text = load_benign_email(benign_input)

    username = input("Victim's name: ")
    mail_service = input("Mail service (e.g., Gmail): ")

    phishing_body = rewrite_benign_to_phishing_html(benign_text, mail_service, sender_name="Joseph")

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

        send_email(from_email, to_email, "Important: Immediate Action Required", phishing_body, use_local,
                   smtp_info if not use_local else None)