import logging
import os
from datetime import datetime

from automation import (
    EmailService, 
    PdfGenerator, 
    QueueManager, 
    NewsletterService,
    AutomationManager
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArxivNewsletterAutomation:
    def __init__(self):
        # 서비스 컴포넌트 초기화
        self.email_service = EmailService(aws_region=os.getenv('AWS_REGION', 'us-east-1'))
        self.pdf_generator = PdfGenerator(headless=True)
        self.queue_manager = QueueManager(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379))
        )
        
        self.newsletter_service = NewsletterService(
            self.email_service,
            self.pdf_generator, 
            self.queue_manager
        )
        
        self.automation_manager = AutomationManager(
            self.queue_manager,
            self.newsletter_service
        )
        
        logger.info("DEBUG: ArxivNewsletterAutomation initialized")
    
    def start_automation_system(self, num_workers: int = 2):
        """자동화 시스템 시작"""
        try:
            self.automation_manager.start_automation(num_workers)
            logger.info(f"DEBUG: Automation system started with {num_workers} workers")
        except Exception as e:
            logger.error(f"ERROR: Failed to start automation system: {str(e)}", exc_info=True)
            raise
    
    def stop_automation_system(self):
        """자동화 시스템 중지"""
        try:
            self.automation_manager.stop_automation()
            logger.info("DEBUG: Automation system stopped")
        except Exception as e:
            logger.error(f"ERROR: Failed to stop automation system: {str(e)}", exc_info=True)
            raise
    
    def create_manual_newsletter(self, papers: list, recipients: list, config: dict) -> str:
        """수동으로 뉴스레터 생성"""
        try:
            task_id = self.newsletter_service.create_newsletter_task(papers, recipients, config)
            logger.info(f"DEBUG: Manual newsletter task created: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"ERROR: Failed to create manual newsletter: {str(e)}", exc_info=True)
            raise
    
    def schedule_daily_newsletter(self, hour: int = 9, minute: int = 0, config: dict = None) -> str:
        """일일 뉴스레터 스케줄링"""
        try:
            task_id = self.newsletter_service.schedule_daily_newsletter(hour, minute, config)
            logger.info(f"DEBUG: Daily newsletter scheduled: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"ERROR: Failed to schedule daily newsletter: {str(e)}", exc_info=True)
            raise
    
    def get_system_status(self) -> dict:
        """시스템 상태 조회"""
        try:
            status = self.automation_manager.get_status()
            logger.info(f"DEBUG: System status retrieved: {status}")
            return status
        except Exception as e:
            logger.error(f"ERROR: Failed to get system status: {str(e)}", exc_info=True)
            raise

def main():
    automation = ArxivNewsletterAutomation()
    
    print("=== arXiv Newsletter Automation System ===")
    print("1. Start automation system")
    print("2. Stop automation system")
    print("3. Create manual newsletter")
    print("4. Schedule daily newsletter")
    print("5. Check system status")
    
    choice = input("Select option (1-5): ").strip()
    
    if choice == '1':
        workers = int(input("Number of workers (default 2): ") or 2)
        automation.start_automation_system(workers)
        print("Automation system started. Press Ctrl+C to stop.")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            automation.stop_automation_system()
            print("Automation system stopped.")
    
    elif choice == '2':
        automation.stop_automation_system()
        print("Automation system stopped.")
    
    elif choice == '3':
        # 샘플 데이터로 테스트
        sample_papers = [
            {
                'title': 'Sample Paper 1',
                'authors': ['Author A', 'Author B'],
                'categories': ['cs.AI'],
                'arxiv_id': '2024.0001',
                'summary': 'This is a sample paper summary.',
                'pdf_url': 'https://arxiv.org/pdf/2024.0001.pdf'
            }
        ]
        sample_recipients = ['test@example.com']
        sample_config = {
            'subject': 'Test Newsletter',
            'title': 'Test arXiv Newsletter',
            'sender_email': 'newsletter@example.com'
        }
        
        task_id = automation.create_manual_newsletter(sample_papers, sample_recipients, sample_config)
        print(f"Manual newsletter task created: {task_id}")
    
    elif choice == '4':
        hour = int(input("Hour (0-23, default 9): ") or 9)
        minute = int(input("Minute (0-59, default 0): ") or 0)
        config = {
            'title': 'Daily arXiv Newsletter',
            'sender_email': 'daily-newsletter@example.com'
        }
        
        task_id = automation.schedule_daily_newsletter(hour, minute, config)
        print(f"Daily newsletter scheduled: {task_id}")
    
    elif choice == '5':
        status = automation.get_system_status()
        print(f"System Status: {status}")

if __name__ == "__main__":
    main()
