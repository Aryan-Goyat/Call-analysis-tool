import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
SMTP_FROM = os.getenv('SMTP_FROM', 'no-reply@honda.com')

def send_reset_email(to_email, reset_link):
    subject = "Honda IT Analytics - Password Reset Request"
    body = f"""
Hello,

We received a request to reset your password for the Honda IT Analytics Dashboard.
If you made this request, please click the link below to set a new password:

{reset_link}

This link will expire in 30 minutes.

If you did not request a password reset, please ignore this email or contact the Honda IT Service Desk.

Thank you,
Honda IT Service Desk
"""

    if all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = SMTP_FROM
            msg['To'] = to_email

            with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"Reset email sent successfully to {to_email} via SMTP.")
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")
            # Fallback to console
            print("\n--- FALLBACK: EMAIL CONTENT ---")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(body)
            print("-------------------------------\n")
    else:
        # Fallback to console for development/testing
        print("\n--- DEVELOPMENT MODE: EMAIL CONTENT ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("---------------------------------------\n")
