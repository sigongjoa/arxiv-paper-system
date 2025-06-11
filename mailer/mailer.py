import smtplib
from email.mime.text import MIMEText
from .config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def send_email(subject: str, body: str, to_email: str) -> None:
    """Send an email using SMTP settings.

    Parameters
    ----------
    subject : str
        Subject of the email.
    body : str
        Body content of the email.
    to_email : str
        Recipient email address.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
