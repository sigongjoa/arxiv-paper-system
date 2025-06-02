import tkinter as tk
from tkinter import ttk
import os
from .tabs import HomeTab, SettingsTab, ProcessTab, PreviewTab, PublishTab
from .utils import ConfigManager, StatusBar

class ArxivToShortsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("arXiv to Shorts - Video Generator")
        self.root.geometry("1200x800")
        
        # 설정 관리자
        self.config_manager = ConfigManager()
        
        # 스타일 설정
        self.setup_styles()
        
        # UI 구성
        self.create_widgets()
        
        # 상태바
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 초기 메시지
        self.status_bar.set_status("Ready to process arXiv papers")
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # 다크 테마 색상
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        select_color = '#404040'
        
        self.root.configure(bg=bg_color)
        
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TButton', background=select_color, foreground=fg_color)
        style.map('TButton', background=[('active', '#505050')])
        
    def create_widgets(self):
        # 메인 컨테이너
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 헤더
        self.create_header(main_container)
        
        # 탭 위젯
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 각 탭 추가
        self.home_tab = HomeTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self.config_manager)
        self.process_tab = ProcessTab(self.notebook)
        self.preview_tab = PreviewTab(self.notebook)
        self.publish_tab = PublishTab(self.notebook)
        
        self.notebook.add(self.home_tab.frame, text="🏠 Home")
        self.notebook.add(self.process_tab.frame, text="⚙️ Process")
        self.notebook.add(self.preview_tab.frame, text="👁️ Preview")
        self.notebook.add(self.publish_tab.frame, text="📤 Publish")
        self.notebook.add(self.settings_tab.frame, text="⚡ Settings")
        
    def create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 로고/타이틀
        title_label = ttk.Label(
            header_frame, 
            text="arXiv to Shorts",
            font=('Arial', 24, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # 상태 인디케이터
        self.status_indicator = ttk.Label(
            header_frame,
            text="● Ready",
            font=('Arial', 12),
            foreground='#4CAF50'
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
    def set_status(self, status, color='#4CAF50'):
        """상태 업데이트"""
        self.status_indicator.config(text=f"● {status}", foreground=color)
        self.status_bar.set_status(status)
        
    def process_paper(self, arxiv_id):
        """논문 처리 시작"""
        self.set_status("Processing...", '#FF9800')
        self.notebook.select(self.process_tab.frame)
        self.process_tab.start_processing(arxiv_id, self)
