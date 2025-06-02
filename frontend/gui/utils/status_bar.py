import tkinter as tk
from tkinter import ttk
from datetime import datetime

class StatusBar:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, relief=tk.SUNKEN)
        self.setup_ui()
        
    def setup_ui(self):
        # 상태 메시지
        self.status_label = ttk.Label(
            self.frame,
            text="Ready",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # 구분선
        separator1 = ttk.Separator(self.frame, orient='vertical')
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 진행 중인 작업
        self.task_label = ttk.Label(
            self.frame,
            text="No active tasks",
            anchor=tk.W
        )
        self.task_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # 구분선
        separator2 = ttk.Separator(self.frame, orient='vertical')
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 메모리 사용량
        self.memory_label = ttk.Label(
            self.frame,
            text="Memory: --",
            anchor=tk.W
        )
        self.memory_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # 시간
        self.time_label = ttk.Label(
            self.frame,
            text="",
            anchor=tk.E
        )
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # 시간 업데이트 시작
        self.update_time()
        self.update_memory()
        
    def pack(self, **kwargs):
        """프레임 pack"""
        self.frame.pack(**kwargs)
        
    def set_status(self, message):
        """상태 메시지 설정"""
        self.status_label.config(text=message)
        
    def set_task(self, task):
        """현재 작업 설정"""
        self.task_label.config(text=task)
        
    def update_time(self):
        """시간 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        
        # 1초마다 업데이트
        self.frame.after(1000, self.update_time)
        
    def update_memory(self):
        """메모리 사용량 업데이트"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.config(text=f"Memory: {memory_mb:.1f} MB")
        except:
            self.memory_label.config(text="Memory: N/A")
            
        # 5초마다 업데이트
        self.frame.after(5000, self.update_memory)
