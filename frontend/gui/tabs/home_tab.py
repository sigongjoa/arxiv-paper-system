import tkinter as tk
from tkinter import ttk, messagebox
import re

class HomeTab:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 컨테이너
        container = ttk.Frame(self.frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(
            container,
            text="Convert arXiv Papers to Short Videos",
            font=('Arial', 18, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # arXiv ID 입력
        input_frame = ttk.LabelFrame(container, text="Paper Input", padding=20)
        input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(input_frame, text="arXiv ID:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.arxiv_entry = ttk.Entry(input_frame, width=30, font=('Arial', 12))
        self.arxiv_entry.grid(row=0, column=1, padx=10)
        self.arxiv_entry.insert(0, "2401.00001")  # 예시
        
        # 처리 버튼
        self.process_btn = ttk.Button(
            input_frame,
            text="Process Paper",
            command=self.process_paper,
            style='Accent.TButton'
        )
        self.process_btn.grid(row=0, column=2, padx=10)
        
        # 배치 처리
        batch_frame = ttk.LabelFrame(container, text="Batch Processing", padding=20)
        batch_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(batch_frame, text="Multiple IDs (one per line):").grid(row=0, column=0, sticky='nw')
        
        self.batch_text = tk.Text(batch_frame, height=5, width=40)
        self.batch_text.grid(row=1, column=0, pady=10)
        
        self.batch_btn = ttk.Button(
            batch_frame,
            text="Process Batch",
            command=self.process_batch
        )
        self.batch_btn.grid(row=2, column=0)
        
        # 최근 처리 목록
        recent_frame = ttk.LabelFrame(container, text="Recent Papers", padding=20)
        recent_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        # 트리뷰로 최근 항목 표시
        columns = ('ID', 'Title', 'Status', 'Date')
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, height=5)
        
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=150)
        
        self.recent_tree.grid(row=0, column=0, sticky='ew')
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', command=self.recent_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        # 통계
        stats_frame = ttk.Frame(container)
        stats_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="Total Processed: 0 | Success: 0 | Failed: 0",
            font=('Arial', 10)
        )
        self.stats_label.pack()
        
    def validate_arxiv_id(self, arxiv_id):
        """arXiv ID 유효성 검사"""
        pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'
        return re.match(pattern, arxiv_id) is not None
        
    def process_paper(self):
        """단일 논문 처리"""
        arxiv_id = self.arxiv_entry.get().strip()
        
        if not arxiv_id:
            messagebox.showwarning("Input Error", "Please enter an arXiv ID")
            return
            
        if not self.validate_arxiv_id(arxiv_id):
            messagebox.showwarning("Invalid ID", "Please enter a valid arXiv ID (e.g., 2401.00001)")
            return
        
        # 처리 시작
        self.main_window.process_paper(arxiv_id)
        
        # 최근 목록에 추가
        self.add_to_recent(arxiv_id, "Processing...", "🔄")
        
    def process_batch(self):
        """배치 처리"""
        text = self.batch_text.get("1.0", tk.END).strip()
        
        if not text:
            messagebox.showwarning("Input Error", "Please enter arXiv IDs")
            return
            
        ids = [line.strip() for line in text.split('\n') if line.strip()]
        valid_ids = [id for id in ids if self.validate_arxiv_id(id)]
        
        if not valid_ids:
            messagebox.showwarning("Invalid IDs", "No valid arXiv IDs found")
            return
            
        if len(valid_ids) < len(ids):
            messagebox.showinfo("Info", f"Processing {len(valid_ids)} valid IDs out of {len(ids)}")
        
        # 배치 처리 시작
        for arxiv_id in valid_ids:
            self.add_to_recent(arxiv_id, "Queued", "⏳")
            
        messagebox.showinfo("Batch Processing", f"Added {len(valid_ids)} papers to queue")
        
    def add_to_recent(self, arxiv_id, title, status):
        """최근 목록에 추가"""
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self.recent_tree.insert('', 0, values=(arxiv_id, title, status, date))
        
        # 최대 10개만 유지
        children = self.recent_tree.get_children()
        if len(children) > 10:
            self.recent_tree.delete(children[-1])
