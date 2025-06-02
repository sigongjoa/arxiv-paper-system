import logging
import sys
from io import StringIO
from datetime import datetime
from threading import Lock

class LogCapture:
    def __init__(self):
        self.logs = []
        self.lock = Lock()
        self.max_logs = 1000
        
    def add_log(self, level, message):
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
            self.logs.append(log_entry)
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)
    
    def get_logs(self, last_n=None):
        with self.lock:
            if last_n:
                return self.logs[-last_n:]
            return self.logs.copy()
    
    def clear_logs(self):
        with self.lock:
            self.logs.clear()

class LogHandler(logging.Handler):
    def __init__(self, log_capture):
        super().__init__()
        self.log_capture = log_capture
        
    def emit(self, record):
        msg = self.format(record)
        self.log_capture.add_log(record.levelname, msg)

class StdoutCapture:
    def __init__(self, log_capture):
        self.log_capture = log_capture
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        self.original_stdout.write(text)
        text = text.strip()
        if text and not text.startswith('['):  # 기존 로그 형식이 아닌 경우만
            if 'chunk:' in text or 't:' in text or '%' in text:
                self.log_capture.add_log('PROGRESS', text)
        
    def flush(self):
        self.original_stdout.flush()

# 글로벌 로그 캡처 인스턴스
log_capture = LogCapture()

def setup_log_capture():
    handler = LogHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    
    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # stdout 캡처 설정
    stdout_capture = StdoutCapture(log_capture)
    sys.stdout = stdout_capture
    
    return log_capture
