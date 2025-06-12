import os
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GmailEmailService:
    def __init__(self):
        self.test_mode = os.getenv('GMAIL_EMAIL_TEST_MODE', 'true').lower() == 'true'
        self.sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        self.sender_password = os.getenv('GMAIL_SENDER_PASSWORD') # App password for security
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        logger.info(f"DEBUG: GmailEmailService initialized (test_mode: {self.test_mode})")
        
        if not self.test_mode and (not self.sender_email or not self.sender_password):
            logger.error("ERROR: GMAIL_SENDER_EMAIL and GMAIL_SENDER_PASSWORD must be set for non-test mode.")
            raise ValueError("Gmail sender email/password not set for non-test mode.")

    def send_email(self,
                   subject: str,
                   html_content: str,
                   text_content: str,
                   recipients: List[str],
                   sender_alias: Optional[str] = None) -> Dict:
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{sender_alias} <{self.sender_email}>" if sender_alias else self.sender_email
        msg['To'] = ', '.join(recipients)
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        if self.test_mode:
            logger.info(f"TEST MODE (Gmail): Would send email")
            logger.info(f"  - Subject: {subject}")
            logger.info(f"  - Recipients: {recipients}")
            logger.info(f"  - Sender: {self.sender_email}")
            logger.info(f"  - HTML content length: {len(html_content)} chars")
            
            # 테스트용 파일로 저장
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'test_gmail_emails')
            os.makedirs(output_dir, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            with open(os.path.join(output_dir, f'gmail_email_{timestamp}.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {'success': True, 'message_id': f'gmail_test_{timestamp}', 'test_mode': True}

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            logger.info(f"DEBUG: Gmail email sent successfully to {recipients}")
            return {'success': True, 'message_id': f'gmail_{datetime.now().strftime("%Y%m%d_%H%M%S")}'}
        except Exception as e:
            logger.error(f"ERROR: Gmail email sending failed: {str(e)}", exc_info=True)
            raise 