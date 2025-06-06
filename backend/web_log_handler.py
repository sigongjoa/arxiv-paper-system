import logging
import requests

class WebLogHandler(logging.Handler):
    def __init__(self, web_endpoint=None):
        super().__init__()
        self.web_endpoint = web_endpoint or "http://localhost:5000/api/logs"
        
    def emit(self, record):
        log_entry = {
            'timestamp': self.format(record),
            'level': record.levelname,
            'message': record.getMessage()
        }
        # GUI와 웹에서 동시에 볼 수 있도록 백엔드 로그 캡처로 전송
        from backend.log_stream import log_capture
        log_capture.add_log(record.levelname, record.getMessage())
