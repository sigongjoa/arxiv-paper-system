import tkinter as tk
from tkinter import ttk, messagebox
import os

class SettingsTab:
    def __init__(self, parent, config_manager):
        self.config_manager = config_manager
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(self.frame, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 설정 컨텐츠
        container = ttk.Frame(scrollable_frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # API 설정
        self.create_api_section(container)
        
        # 비디오 설정
        self.create_video_section(container)
        
        # 소셜 미디어 설정
        self.create_social_section(container)
        
        # 저장 버튼
        save_btn = ttk.Button(
            container,
            text="Save Settings",
            command=self.save_settings,
            style='Accent.TButton'
        )
        save_btn.pack(pady=20)
        
    def create_api_section(self, parent):
        """AI API 설정 섹션"""
        api_frame = ttk.LabelFrame(parent, text="AI API Settings", padding=15)
        api_frame.pack(fill=tk.X, pady=10)
        
        # OpenAI
        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=0, column=0, sticky='w', pady=5)
        self.openai_entry = ttk.Entry(api_frame, width=50, show='*')
        self.openai_entry.grid(row=0, column=1, padx=10, pady=5)
        self.openai_entry.insert(0, self.config_manager.get('OPENAI_API_KEY', ''))
        
        # Anthropic
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=1, column=0, sticky='w', pady=5)
        self.anthropic_entry = ttk.Entry(api_frame, width=50, show='*')
        self.anthropic_entry.grid(row=1, column=1, padx=10, pady=5)
        self.anthropic_entry.insert(0, self.config_manager.get('ANTHROPIC_API_KEY', ''))
        
        # AI Model 선택
        ttk.Label(api_frame, text="Preferred AI Model:").grid(row=2, column=0, sticky='w', pady=5)
        self.ai_model_var = tk.StringVar(value=self.config_manager.get('AI_MODEL', 'gpt-4'))
        ai_model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.ai_model_var,
            values=['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet'],
            width=47
        )
        ai_model_combo.grid(row=2, column=1, padx=10, pady=5)
        
    def create_video_section(self, parent):
        """비디오 설정 섹션"""
        video_frame = ttk.LabelFrame(parent, text="Video Settings", padding=15)
        video_frame.pack(fill=tk.X, pady=10)
        
        # 해상도
        ttk.Label(video_frame, text="Resolution:").grid(row=0, column=0, sticky='w', pady=5)
        self.resolution_var = tk.StringVar(value=self.config_manager.get('RESOLUTION', '1080x1920'))
        resolution_combo = ttk.Combobox(
            video_frame,
            textvariable=self.resolution_var,
            values=['1080x1920', '720x1280', '540x960'],
            width=20
        )
        resolution_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # FPS
        ttk.Label(video_frame, text="FPS:").grid(row=1, column=0, sticky='w', pady=5)
        self.fps_var = tk.StringVar(value=self.config_manager.get('FPS', '30'))
        fps_combo = ttk.Combobox(
            video_frame,
            textvariable=self.fps_var,
            values=['24', '30', '60'],
            width=20
        )
        fps_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # 비디오 길이
        ttk.Label(video_frame, text="Max Duration (seconds):").grid(row=2, column=0, sticky='w', pady=5)
        self.duration_var = tk.StringVar(value=self.config_manager.get('MAX_DURATION', '60'))
        duration_spin = ttk.Spinbox(
            video_frame,
            textvariable=self.duration_var,
            from_=30,
            to=180,
            increment=10,
            width=21
        )
        duration_spin.grid(row=2, column=1, padx=10, pady=5)
        
        # TTS 엔진
        ttk.Label(video_frame, text="TTS Engine:").grid(row=3, column=0, sticky='w', pady=5)
        self.tts_var = tk.StringVar(value=self.config_manager.get('TTS_ENGINE', 'edge-tts'))
        tts_combo = ttk.Combobox(
            video_frame,
            textvariable=self.tts_var,
            values=['edge-tts', 'google-cloud-tts', 'elevenlabs'],
            width=20
        )
        tts_combo.grid(row=3, column=1, padx=10, pady=5)
        
        # 음성 선택
        ttk.Label(video_frame, text="Voice:").grid(row=4, column=0, sticky='w', pady=5)
        self.voice_var = tk.StringVar(value=self.config_manager.get('VOICE', 'en-US-AriaNeural'))
        voice_combo = ttk.Combobox(
            video_frame,
            textvariable=self.voice_var,
            values=['en-US-AriaNeural', 'en-US-GuyNeural', 'en-GB-SoniaNeural'],
            width=20
        )
        voice_combo.grid(row=4, column=1, padx=10, pady=5)
        
    def create_social_section(self, parent):
        """소셜 미디어 설정 섹션"""
        social_frame = ttk.LabelFrame(parent, text="Social Media Settings", padding=15)
        social_frame.pack(fill=tk.X, pady=10)
        
        # YouTube
        youtube_frame = ttk.Frame(social_frame)
        youtube_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(youtube_frame, text="YouTube Client ID:").grid(row=0, column=0, sticky='w', pady=2)
        self.youtube_id_entry = ttk.Entry(youtube_frame, width=50)
        self.youtube_id_entry.grid(row=0, column=1, padx=10, pady=2)
        self.youtube_id_entry.insert(0, self.config_manager.get('YOUTUBE_CLIENT_ID', ''))
        
        ttk.Label(youtube_frame, text="YouTube Client Secret:").grid(row=1, column=0, sticky='w', pady=2)
        self.youtube_secret_entry = ttk.Entry(youtube_frame, width=50, show='*')
        self.youtube_secret_entry.grid(row=1, column=1, padx=10, pady=2)
        self.youtube_secret_entry.insert(0, self.config_manager.get('YOUTUBE_CLIENT_SECRET', ''))
        
        # Instagram
        ttk.Separator(social_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        instagram_frame = ttk.Frame(social_frame)
        instagram_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(instagram_frame, text="Instagram Username:").grid(row=0, column=0, sticky='w', pady=2)
        self.instagram_user_entry = ttk.Entry(instagram_frame, width=50)
        self.instagram_user_entry.grid(row=0, column=1, padx=10, pady=2)
        self.instagram_user_entry.insert(0, self.config_manager.get('INSTAGRAM_USERNAME', ''))
        
        ttk.Label(instagram_frame, text="Instagram Password:").grid(row=1, column=0, sticky='w', pady=2)
        self.instagram_pass_entry = ttk.Entry(instagram_frame, width=50, show='*')
        self.instagram_pass_entry.grid(row=1, column=1, padx=10, pady=2)
        self.instagram_pass_entry.insert(0, self.config_manager.get('INSTAGRAM_PASSWORD', ''))
        
        # 자동 업로드 옵션
        ttk.Separator(social_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        options_frame = ttk.Frame(social_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.auto_upload_var = tk.BooleanVar(value=self.config_manager.get('AUTO_UPLOAD', False))
        auto_upload_check = ttk.Checkbutton(
            options_frame,
            text="Auto-upload after processing",
            variable=self.auto_upload_var
        )
        auto_upload_check.pack(anchor='w')
        
        self.add_hashtags_var = tk.BooleanVar(value=self.config_manager.get('ADD_HASHTAGS', True))
        add_hashtags_check = ttk.Checkbutton(
            options_frame,
            text="Add hashtags automatically",
            variable=self.add_hashtags_var
        )
        add_hashtags_check.pack(anchor='w')
        
    def save_settings(self):
        """설정 저장"""
        settings = {
            'OPENAI_API_KEY': self.openai_entry.get(),
            'ANTHROPIC_API_KEY': self.anthropic_entry.get(),
            'AI_MODEL': self.ai_model_var.get(),
            'RESOLUTION': self.resolution_var.get(),
            'FPS': self.fps_var.get(),
            'MAX_DURATION': self.duration_var.get(),
            'TTS_ENGINE': self.tts_var.get(),
            'VOICE': self.voice_var.get(),
            'YOUTUBE_CLIENT_ID': self.youtube_id_entry.get(),
            'YOUTUBE_CLIENT_SECRET': self.youtube_secret_entry.get(),
            'INSTAGRAM_USERNAME': self.instagram_user_entry.get(),
            'INSTAGRAM_PASSWORD': self.instagram_pass_entry.get(),
            'AUTO_UPLOAD': self.auto_upload_var.get(),
            'ADD_HASHTAGS': self.add_hashtags_var.get()
        }
        
        self.config_manager.save_all(settings)
        messagebox.showinfo("Success", "Settings saved successfully!")
