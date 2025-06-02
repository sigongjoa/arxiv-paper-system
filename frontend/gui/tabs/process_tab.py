import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime

class ProcessTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.current_arxiv_id = None
        self.setup_ui()
        
    def setup_ui(self):
        container = ttk.Frame(self.frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 현재 처리 중인 논문
        current_frame = ttk.LabelFrame(container, text="Current Processing", padding=15)
        current_frame.pack(fill=tk.X, pady=10)
        
        self.current_label = ttk.Label(
            current_frame,
            text="No paper currently processing",
            font=('Arial', 12)
        )
        self.current_label.pack()
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            current_frame,
            variable=self.progress_var,
            maximum=100,
            length=600
        )
        self.progress_bar.pack(pady=10, fill=tk.X)
        
        # 단계별 상태
        stages_frame = ttk.LabelFrame(container, text="Processing Stages", padding=15)
        stages_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 각 단계 상태 표시
        self.stages = {
            'extract': {'label': '1. Extract Paper Data', 'status': '⏸️ Waiting'},
            'summarize': {'label': '2. AI Summarization', 'status': '⏸️ Waiting'},
            'visualize': {'label': '3. Generate Visuals', 'status': '⏸️ Waiting'},
            'narrate': {'label': '4. Create Narration', 'status': '⏸️ Waiting'},
            'compose': {'label': '5. Compose Video', 'status': '⏸️ Waiting'},
            'publish': {'label': '6. Publish to Platforms', 'status': '⏸️ Waiting'}
        }
        
        self.stage_labels = {}
        
        for i, (key, stage) in enumerate(self.stages.items()):
            frame = ttk.Frame(stages_frame)
            frame.grid(row=i, column=0, sticky='ew', pady=5)
            
            # 단계 이름
            label = ttk.Label(frame, text=stage['label'], width=30)
            label.grid(row=0, column=0, sticky='w')
            
            # 상태
            status_label = ttk.Label(frame, text=stage['status'], width=20)
            status_label.grid(row=0, column=1, padx=20)
            
            # 시간
            time_label = ttk.Label(frame, text='--:--', width=10)
            time_label.grid(row=0, column=2)
            
            self.stage_labels[key] = {
                'status': status_label,
                'time': time_label,
                'start_time': None
            }
        
        # 로그 출력
        log_frame = ttk.LabelFrame(container, text="Process Log", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 텍스트 위젯과 스크롤바
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container, height=10, wrap=tk.WORD, bg='#1e1e1e', fg='white')
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 컨트롤 버튼
        control_frame = ttk.Frame(container)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.pause_btn = ttk.Button(
            control_frame,
            text="Pause",
            command=self.pause_processing,
            state='disabled'
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(
            control_frame,
            text="Cancel",
            command=self.cancel_processing,
            state='disabled'
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_log_btn = ttk.Button(
            control_frame,
            text="Clear Log",
            command=self.clear_log
        )
        self.clear_log_btn.pack(side=tk.RIGHT, padx=5)
        
    def start_processing(self, arxiv_id, main_window=None):
        """처리 시작"""
        self.current_arxiv_id = arxiv_id
        self.main_window = main_window
        self.current_label.config(text=f"Processing: {arxiv_id}")
        
        # 버튼 활성화
        self.pause_btn.config(state='normal')
        self.cancel_btn.config(state='normal')
        
        # 로그 추가
        self.add_log(f"Starting processing for paper: {arxiv_id}")
        
        # 진행률 초기화
        self.progress_var.set(0)
        
        # 모든 단계 초기화
        for key in self.stages:
            self.update_stage(key, '⏸️ Waiting', '')
        
        # 처리 스레드 시작
        thread = threading.Thread(target=self.process_paper_thread, args=(arxiv_id,))
        thread.daemon = True
        thread.start()
        
    def process_paper_thread(self, arxiv_id):
        """실제 처리 스레드"""
        try:
            # 실제 파이프라인 사용
            import sys
            import os
            
            # 프로젝트 루트를 sys.path에 추가
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            sys.path.insert(0, project_root)
            
            from backend.core.pipeline import Pipeline
            from backend.processor import PaperProcessor
            
            processor = PaperProcessor()
            pipeline = Pipeline()
            
            # 1. Extract
            self.update_stage('extract', '🔄 Processing')
            self.add_log("Extracting paper data from arXiv...")
            paper_result = processor.process_arxiv_paper(arxiv_id)
            self.update_stage('extract', '✅ Complete')
            self.progress_var.set(16)
            
            # 2. Summarize (실제 논문 분석)
            self.update_stage('summarize', '🔄 Processing')
            self.add_log("Analyzing full paper content with AI...")
            script = pipeline.summarizer.generate_script(paper_result['paper'])
            self.update_stage('summarize', '✅ Complete')
            self.progress_var.set(33)
            
            # 3. Visualize (실제 데이터 기반)
            self.update_stage('visualize', '🔄 Processing')
            self.add_log("Creating charts from real paper data...")
            visuals = pipeline.visualizer.create_visuals(paper_result['paper'], script)
            self.update_stage('visualize', '✅ Complete')
            self.progress_var.set(50)
            
            # 4. Narrate
            self.update_stage('narrate', '🔄 Processing')
            self.add_log("Generating narration...")
            narration = pipeline.narrator.generate_narration(script)
            self.update_stage('narrate', '✅ Complete')
            self.progress_var.set(66)
            
            # 5. Compose
            self.update_stage('compose', '🔄 Processing')
            self.add_log("Composing final video...")
            video_paths = pipeline.composer.compose_video(visuals, narration, script)
            self.update_stage('compose', '✅ Complete')
            self.progress_var.set(83)
            
            # 6. Publish
            self.update_stage('publish', '🔄 Processing')
            self.add_log("Publishing to local storage...")
            results = pipeline.publisher.distribute(video_paths)
            self.update_stage('publish', '✅ Complete')
            self.progress_var.set(100)
            
            self.add_log(f"✅ Real paper analysis complete for {arxiv_id}!")
            self.add_log(f"📹 Video saved: {video_paths[0]}")
            self.current_label.config(text="Real analysis complete!")
            
            # 메인 윈도우 상태 업데이트
            if self.main_window:
                self.main_window.set_status("Ready", '#4CAF50')
            
        except Exception as e:
            self.add_log(f"❌ Error: {str(e)}")
            self.current_label.config(text=f"Error processing {arxiv_id}")
            
        finally:
            self.pause_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            
    def update_stage(self, stage_key, status, time_str=None):
        """단계 상태 업데이트"""
        if stage_key in self.stage_labels:
            self.stage_labels[stage_key]['status'].config(text=status)
            
            if '🔄' in status and self.stage_labels[stage_key]['start_time'] is None:
                self.stage_labels[stage_key]['start_time'] = time.time()
                
            if '✅' in status and self.stage_labels[stage_key]['start_time']:
                elapsed = time.time() - self.stage_labels[stage_key]['start_time']
                self.stage_labels[stage_key]['time'].config(text=f"{elapsed:.1f}s")
                self.stage_labels[stage_key]['start_time'] = None
                
    def add_log(self, message):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
        
    def pause_processing(self):
        """처리 일시정지"""
        self.add_log("Processing paused")
        # TODO: 실제 일시정지 구현
        
    def cancel_processing(self):
        """처리 취소"""
        self.add_log("Processing cancelled")
        self.current_label.config(text="Processing cancelled")
        self.pause_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
        # TODO: 실제 취소 구현
