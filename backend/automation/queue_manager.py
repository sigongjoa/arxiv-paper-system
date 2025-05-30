import redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.task_queue = 'arxiv_newsletter_tasks'
        self.result_queue = 'arxiv_newsletter_results'
        logger.info(f"DEBUG: QueueManager initialized with Redis {redis_host}:{redis_port}")
    
    def add_newsletter_task(self, 
                          task_type: str,
                          papers: list,
                          recipients: list,
                          config: Dict[str, Any]) -> str:
        
        task_id = str(uuid.uuid4())
        task_data = {
            'task_id': task_id,
            'task_type': task_type,
            'papers': papers,
            'recipients': recipients,
            'config': config,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.redis_client.lpush(self.task_queue, json.dumps(task_data))
        logger.info(f"DEBUG: Task added to queue: {task_id}, type: {task_type}")
        return task_id
    
    def get_next_task(self) -> Optional[Dict]:
        task_json = self.redis_client.brpop(self.task_queue, timeout=10)
        if task_json:
            task_data = json.loads(task_json[1])
            logger.info(f"DEBUG: Retrieved task: {task_data['task_id']}")
            return task_data
        return None
    
    def update_task_status(self, task_id: str, status: str, result: Dict = None):
        status_data = {
            'task_id': task_id,
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        if result:
            status_data['result'] = result
        
        self.redis_client.hset(f"task:{task_id}", mapping=status_data)
        self.redis_client.expire(f"task:{task_id}", 86400)  # 24시간 후 삭제
        logger.info(f"DEBUG: Task status updated: {task_id} -> {status}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        task_data = self.redis_client.hgetall(f"task:{task_id}")
        if task_data:
            return dict(task_data)
        return None
    
    def add_scheduled_task(self, 
                         task_type: str,
                         schedule_time: datetime,
                         task_data: Dict) -> str:
        
        task_id = str(uuid.uuid4())
        scheduled_data = {
            'task_id': task_id,
            'task_type': task_type,
            'schedule_time': schedule_time.isoformat(),
            'task_data': task_data,
            'created_at': datetime.now().isoformat()
        }
        
        score = schedule_time.timestamp()
        self.redis_client.zadd('scheduled_tasks', {json.dumps(scheduled_data): score})
        logger.info(f"DEBUG: Scheduled task added: {task_id} at {schedule_time}")
        return task_id
    
    def get_due_tasks(self) -> list:
        now = datetime.now().timestamp()
        due_tasks = self.redis_client.zrangebyscore('scheduled_tasks', 0, now)
        
        if due_tasks:
            self.redis_client.zremrangebyscore('scheduled_tasks', 0, now)
            logger.info(f"DEBUG: Found {len(due_tasks)} due tasks")
            return [json.loads(task) for task in due_tasks]
        
        return []
    
    def clear_queue(self, queue_name: str = None):
        if queue_name:
            self.redis_client.delete(queue_name)
        else:
            self.redis_client.delete(self.task_queue)
            self.redis_client.delete(self.result_queue)
        logger.info(f"DEBUG: Queue cleared: {queue_name or 'all'}")
