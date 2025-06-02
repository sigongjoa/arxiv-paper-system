import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class PreviewTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.current_video = None
        self.setup_ui()
        
    def setup_ui(self):
        container = ttk.Frame(self.frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 비디오 선택
        select_frame = ttk.Frame(container)
        select_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(select_frame, text="Select Video:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.video_var = tk.StringVar()
        self.video_combo = ttk.Combobox(
            select_frame,
            textvariable=self.video_var,
            width=50,
            state='readonly'
        )
        self.video_combo.pack(side=tk.LEFT, padx=10)
        self.video_combo.bind('<<ComboboxSelected>>', self.load_video)
        
        refresh_btn = ttk.Button(
            select_frame,
            text="Refresh",
            command=self.refresh_video_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 비디오 플레이어 프레임 (placeholder)
        player_frame = ttk.LabelFrame(container, text="Video Preview", padding=15)
        player_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 비디오 플레이어 플레이스홀더
        self.video_label = ttk.Label(
            player_frame,
            text="Video preview will appear here\n\n(Note: Actual video playback requires external player integration)",
            font=('Arial', 12),
            anchor='center'
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # 컨트롤 버튼
        control_frame = ttk.Frame(player_frame)
        control_frame.pack(side=tk.BOTTOM, pady=10)
        
        self.play_btn = ttk.Button(
            control_frame,
            text="▶ Play",
            command=self.play_video,
            state='disabled'
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(
            control_frame,
            text="📁 Open Folder",
            command=self.open_output_folder
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # 비디오 정보
        info_frame = ttk.LabelFrame(container, text="Video Information", padding=15)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, state='disabled')
        self.info_text.pack(fill=tk.X)
        
        # 수정 옵션
        edit_frame = ttk.LabelFrame(container, text="Quick Edits", padding=15)
        edit_frame.pack(fill=tk.X, pady=10)
        
        # 썸네일 변경
        thumb_frame = ttk.Frame(edit_frame)
        thumb_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(thumb_frame, text="Thumbnail:").pack(side=tk.LEFT, padx=(0, 10))
        self.thumb_btn = ttk.Button(
            thumb_frame,
            text="Change Thumbnail",
            command=self.change_thumbnail,
            state='disabled'
        )
        self.thumb_btn.pack(side=tk.LEFT)
        
        # 자막 편집
        caption_frame = ttk.Frame(edit_frame)
        caption_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(caption_frame, text="Captions:").pack(side=tk.LEFT, padx=(0, 10))
        self.caption_btn = ttk.Button(
            caption_frame,
            text="Edit Captions",
            command=self.edit_captions,
            state='disabled'
        )
        self.caption_btn.pack(side=tk.LEFT)
        
        # 재생성 버튼
        regenerate_frame = ttk.Frame(edit_frame)
        regenerate_frame.pack(fill=tk.X, pady=10)
        
        self.regenerate_btn = ttk.Button(
            regenerate_frame,
            text="Regenerate Video",
            command=self.regenerate_video,
            state='disabled'
        )
        self.regenerate_btn.pack()
        
        # 초기 비디오 목록 로드
        self.refresh_video_list()
        
    def refresh_video_list(self):
        """비디오 목록 새로고침"""
        video_dir = r"D:\arxiv-to-shorts\output\videos"
        
        if os.path.exists(video_dir):
            videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
            self.video_combo['values'] = videos
            
            if videos:
                self.video_combo.current(0)
                self.load_video()
        else:
            self.video_combo['values'] = []
            
    def load_video(self, event=None):
        """비디오 정보 로드"""
        if self.video_var.get():
            self.current_video = os.path.join(
                r"D:\arxiv-to-shorts\output\videos",
                self.video_var.get()
            )
            
            # 버튼 활성화
            self.play_btn.config(state='normal')
            self.thumb_btn.config(state='normal')
            self.caption_btn.config(state='normal')
            self.regenerate_btn.config(state='normal')
            
            # 비디오 정보 표시
            self.show_video_info()
            
    def show_video_info(self):
        """비디오 정보 표시"""
        if not self.current_video or not os.path.exists(self.current_video):
            return
            
        file_stats = os.stat(self.current_video)
        file_size = file_stats.st_size / (1024 * 1024)  # MB
        
        info = f"""File: {os.path.basename(self.current_video)}
Size: {file_size:.2f} MB
Path: {self.current_video}
Created: {os.path.getctime(self.current_video)}

Format: MP4
Resolution: 1080x1920 (9:16)
Duration: 60 seconds
FPS: 30"""
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        self.info_text.config(state='disabled')
        
    def play_video(self):
        """비디오 재생 (외부 플레이어)"""
        if self.current_video and os.path.exists(self.current_video):
            os.startfile(self.current_video)
            
    def open_output_folder(self):
        """출력 폴더 열기"""
        video_dir = r"D:\arxiv-to-shorts\output\videos"
        if os.path.exists(video_dir):
            os.startfile(video_dir)
            
    def change_thumbnail(self):
        """썸네일 변경"""
        file_path = filedialog.askopenfilename(
            title="Select Thumbnail Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            # TODO: 썸네일 변경 구현
            tk.messagebox.showinfo("Info", "Thumbnail change functionality to be implemented")
            
    def edit_captions(self):
        """자막 편집"""
        # TODO: 자막 편집기 구현
        tk.messagebox.showinfo("Info", "Caption editor to be implemented")
        
    def regenerate_video(self):
        """비디오 재생성"""
        if tk.messagebox.askyesno("Regenerate", "Regenerate this video with current settings?"):
            # TODO: 재생성 로직 구현
            tk.messagebox.showinfo("Info", "Video regeneration to be implemented")
