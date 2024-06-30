import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("EMAIL_PASS")

def send_email(email, html):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify Email Address"
    message["From"] = EMAIL
    message["To"] = email

    message.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, email, message.as_string())