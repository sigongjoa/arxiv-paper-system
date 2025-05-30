import boto3
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, aws_region: str = 'us-east-1'):
        self.ses_client = boto3.client('ses', region_name=aws_region)
        logger.info(f"DEBUG: EmailService initialized with region {aws_region}")
    
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
