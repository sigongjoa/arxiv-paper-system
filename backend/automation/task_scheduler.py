import time
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime
import threading

from .queue_manager import QueueManager
from .newsletter_service import NewsletterService

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, 
                 queue_manager: QueueManager,
                 newsletter_service: NewsletterService,
                 check_interval: int = 60):
        
        self.queue_manager = queue_manager
        self.newsletter_service = newsletter_service
        self.check_interval = check_interval
        self.is_running = False
        self.worker_thread = None
        logger.info("DEBUG: TaskScheduler initialized")
    
    def start_scheduler(self):
        if self.is_running:
            logger.warning("DEBUG: Scheduler already running")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.worker_thread.start()
        logger.info("DEBUG: TaskScheduler started")
    
    def stop_scheduler(self):
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("DEBUG: TaskScheduler stopped")
    
    def _scheduler_loop(self):
        while self.is_running:
            try:
                self._check_scheduled_tasks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"ERROR: Scheduler loop error: {str(e)}", exc_info=True)
                time.sleep(5)
    
    def _check_scheduled_tasks(self):
        due_tasks = self.queue_manager.get_due_tasks()
        
        for task in due_tasks:
            try:
                self._process_scheduled_task(task)
            except Exception as e:
                logger.error(f"ERROR: Scheduled task processing failed: {str(e)}", exc_info=True)
    
    def _process_scheduled_task(self, task: Dict):
        task_type = task['task_type']
        task_data = task['task_data']
        
        logger.info(f"DEBUG: Processing scheduled task: {task_type}")
        
        if task_type == 'daily_newsletter':
            self._handle_daily_newsletter(task_data)
        else:
            logger.warning(f"DEBUG: Unknown scheduled task type: {task_type}")
    
    def _handle_daily_newsletter(self, task_data: Dict):
        # 여기서 실제 논문 수집 및 뉴스레터 생성 로직을 구현
        # 기존 크롤러와 연동
        pass


class TaskWorker:
    def __init__(self, 
                 queue_manager: QueueManager,
                 newsletter_service: NewsletterService,
                 worker_id: str = "worker-1"):
        
        self.queue_manager = queue_manager
        self.newsletter_service = newsletter_service
        self.worker_id = worker_id
        self.is_running = False
        logger.info(f"DEBUG: TaskWorker {worker_id} initialized")
    
    def start_worker(self):
        self.is_running = True
        logger.info(f"DEBUG: TaskWorker {self.worker_id} started")
        
        while self.is_running:
            try:
                task = self.queue_manager.get_next_task()
                if task:
                    self._process_task(task)
            except KeyboardInterrupt:
                logger.info(f"DEBUG: TaskWorker {self.worker_id} stopped by user")
                break
            except Exception as e:
                logger.error(f"ERROR: TaskWorker {self.worker_id} error: {str(e)}", exc_info=True)
                time.sleep(5)
    
    def stop_worker(self):
        self.is_running = False
        logger.info(f"DEBUG: TaskWorker {self.worker_id} stopping")
    
    def _process_task(self, task: Dict):
        task_id = task['task_id']
        task_type = task['task_type']
        
        logger.info(f"DEBUG: Processing task {task_id} of type {task_type}")
        
        if task_type == 'generate_newsletter':
            asyncio.run(self.newsletter_service.process_newsletter_task(task))
        else:
            logger.warning(f"DEBUG: Unknown task type: {task_type}")


class AutomationManager:
    def __init__(self,
                 queue_manager: QueueManager,
                 newsletter_service: NewsletterService):
        
        self.queue_manager = queue_manager
        self.newsletter_service = newsletter_service
        self.scheduler = TaskScheduler(queue_manager, newsletter_service)
        self.workers = []
        logger.info("DEBUG: AutomationManager initialized")
    
    def start_automation(self, num_workers: int = 2):
        # 스케줄러 시작
        self.scheduler.start_scheduler()
        
        # 워커들 시작
        for i in range(num_workers):
            worker = TaskWorker(
                self.queue_manager,
                self.newsletter_service,
                f"worker-{i+1}"
            )
            worker_thread = threading.Thread(target=worker.start_worker, daemon=True)
            worker_thread.start()
            self.workers.append((worker, worker_thread))
        
        logger.info(f"DEBUG: Automation started with {num_workers} workers")
    
    def stop_automation(self):
        # 스케줄러 중지
        self.scheduler.stop_scheduler()
        
        # 워커들 중지
        for worker, thread in self.workers:
            worker.stop_worker()
        
        logger.info("DEBUG: Automation stopped")
    
    def get_status(self) -> Dict:
        return {
            'scheduler_running': self.scheduler.is_running,
            'active_workers': len([w for w, t in self.workers if w.is_running]),
            'queue_size': self.queue_manager.redis_client.llen(self.queue_manager.task_queue)
        }
