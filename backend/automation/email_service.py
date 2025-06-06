import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, aws_region: str = 'us-east-1'):
        self.test_mode = os.getenv('EMAIL_TEST_MODE', 'true').lower() == 'true'
        if not self.test_mode:
            import boto3
            self.ses_client = boto3.client('ses', region_name=aws_region)
        logger.info(f"DEBUG: EmailService initialized (test_mode: {self.test_mode})")
    
    def send_newsletter(self, 
                       subject: str,
                       html_content: str,
                       text_content: str,
                       recipients: List[str],
                       sender_email: str,
                       pdf_attachment: Optional[bytes] = None,
                       pdf_filename: str = "newsletter.pdf") -> Dict:
        
        logger.info(f"DEBUG: Sending newsletter to {len(recipients)} recipients")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        if pdf_attachment:
            pdf_part = MIMEApplication(pdf_attachment, _subtype='pdf')
            pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
            msg.attach(pdf_part)
            logger.info(f"DEBUG: PDF attachment added: {pdf_filename}")
        
        if self.test_mode:
            # 테스트 모드: 이메일 전송하지 않고 로그만 남김
            logger.info(f"TEST MODE: Would send email")
            logger.info(f"  - Subject: {subject}")
            logger.info(f"  - Recipients: {recipients}")
            logger.info(f"  - Sender: {sender_email}")
            logger.info(f"  - PDF attachment: {'Yes' if pdf_attachment else 'No'}")
            logger.info(f"  - HTML content length: {len(html_content)} chars")
            logger.info(f"  - Text content length: {len(text_content)} chars")
            
            # 테스트용 파일로 저장
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'test_emails')
            os.makedirs(output_dir, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # HTML 저장
            with open(os.path.join(output_dir, f'email_{timestamp}.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # PDF 저장 (있다면)
            if pdf_attachment:
                with open(os.path.join(output_dir, f'newsletter_{timestamp}.pdf'), 'wb') as f:
                    f.write(pdf_attachment)
            
            return {'success': True, 'message_id': f'test_{timestamp}', 'test_mode': True}
        
        try:
            response = self.ses_client.send_raw_email(
                Source=sender_email,
                Destinations=recipients,
                RawMessage={'Data': msg.as_string()}
            )
            logger.info(f"DEBUG: Email sent successfully, MessageId: {response['MessageId']}")
            return {'success': True, 'message_id': response['MessageId']}
        except Exception as e:
            logger.error(f"ERROR: Email sending failed: {str(e)}", exc_info=True)
            raise
    
    def send_batch_emails(self, 
                         emails: List[Dict],
                         batch_size: int = 50) -> List[Dict]:
        
        results = []
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            logger.info(f"DEBUG: Processing batch {i//batch_size + 1}, size: {len(batch)}")
            
            for email_data in batch:
                try:
                    result = self.send_newsletter(**email_data)
                    results.append(result)
                except Exception as e:
                    logger.error(f"ERROR: Batch email failed: {str(e)}", exc_info=True)
                    results.append({'success': False, 'error': str(e)})
        
        return results
