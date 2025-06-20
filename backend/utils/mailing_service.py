import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MailingService:
    def _get_default_mailing_config(self) -> Dict[str, Any]:
        """Get default mailing configuration"""
        return {
            'smtpHost': '',
            'smtpPort': 587,
            'smtpUser': '',
            'smtpPassword': '',
            'fromEmail': '',
            'fromName': 'arXiv Newsletter',
            'testEmail': ''
        }
    
    def test_smtp_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test SMTP connection"""
        try:
            smtp_host = config.get('smtpHost')
            smtp_port = config.get('smtpPort', 587)
            smtp_user = config.get('smtpUser')
            smtp_password = config.get('smtpPassword')
            test_email = config.get('testEmail')
            
            logger.info(f"DEBUG: Test config received: host={smtp_host}, port={smtp_port}, user={smtp_user}, password={'***' if smtp_password else 'None'}, test_email={test_email}")
            
            if not all([smtp_host, smtp_user, smtp_password, test_email]):
                missing = []
                if not smtp_host: missing.append('smtpHost')
                if not smtp_user: missing.append('smtpUser')
                if not smtp_password: missing.append('smtpPassword')
                if not test_email: missing.append('testEmail')
                logger.error(f"DEBUG: Missing fields: {missing}")
                return {'success': False, 'error': f'Missing required SMTP configuration: {missing}'}
            
            logger.info(f"DEBUG: Testing SMTP connection to {smtp_host}:{smtp_port}")
            
            # Create connection
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = config.get('fromEmail', smtp_user)
            msg['To'] = test_email
            msg['Subject'] = 'arXiv Newsletter - SMTP Test'
            
            body = '''이것은 arXiv Paper Management System의 SMTP 설정 테스트 이메일입니다.
            
이 이메일을 받으셨다면 SMTP 설정이 올바르게 구성되었습니다.

테스트 시간: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Send test email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"DEBUG: Test email sent successfully to {test_email}")
            return {'success': True, 'message': f'Test email sent to {test_email}'}
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "인증 실패: 사용자명 또는 비밀번호를 확인하세요. Gmail의 경우 앱 비밀번호를 사용해야 합니다."
            logger.error(f"ERROR: SMTP auth failed: {str(e)}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"ERROR: SMTP test failed: {error_msg}")
            return {'success': False, 'error': f'SMTP test failed: {error_msg}'} 