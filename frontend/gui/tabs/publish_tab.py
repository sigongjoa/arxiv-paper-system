import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import logging
from .publish_manager import PublishManager

class PublishTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.publish_manager = PublishManager()
        self.setup_ui()
        self.load_videos()
        
    def setup_ui(self):
        container = ttk.Frame(self.frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 비디오 선택
        video_frame = ttk.LabelFrame(container, text="Select Video to Publish", padding=15)
        video_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(video_frame, text="Video:").grid(row=0, column=0, sticky='w', pady=5)
        self.video_var = tk.StringVar()
        self.video_combo = ttk.Combobox(
            video_frame,
            textvariable=self.video_var,
            width=50
        )
        self.video_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # 플랫폼 선택
        platform_frame = ttk.LabelFrame(container, text="Select Platforms", padding=15)
        platform_frame.pack(fill=tk.X, pady=10)
        
        self.platform_vars = {
            'youtube': tk.BooleanVar(value=True),
            'instagram': tk.BooleanVar(value=True),
            'tiktok': tk.BooleanVar(value=True)
        }
        
        platforms = [
            ('YouTube Shorts', 'youtube', '📺'),
            ('Instagram Reels', 'instagram', '📷'),
            ('TikTok', 'tiktok', '🎵')
        ]
        
        for i, (name, key, icon) in enumerate(platforms):
            check = ttk.Checkbutton(
                platform_frame,
                text=f"{icon} {name}",
                variable=self.platform_vars[key]
            )
            check.grid(row=i//3, column=i%3, sticky='w', padx=20, pady=5)
        
        # 게시 설정
        settings_frame = ttk.LabelFrame(container, text="Publishing Settings", padding=15)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # 제목
        ttk.Label(settings_frame, text="Title:").grid(row=0, column=0, sticky='w', pady=5)
        self.title_entry = ttk.Entry(settings_frame, width=60)
        self.title_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=5)
        self.title_entry.insert(0, "Amazing Research Discovery! 🔬 #shorts")
        
        # 설명
        ttk.Label(settings_frame, text="Description:").grid(row=1, column=0, sticky='nw', pady=5)
        self.desc_text = tk.Text(settings_frame, height=4, width=60)
        self.desc_text.grid(row=1, column=1, columnspan=2, padx=10, pady=5)
        self.desc_text.insert(1.0, "Check out this groundbreaking research! 🚀\n\nPaper: [arXiv link]\n\n#science #research #ai")
        
        # 해시태그
        ttk.Label(settings_frame, text="Hashtags:").grid(row=2, column=0, sticky='w', pady=5)
        self.hashtag_entry = ttk.Entry(settings_frame, width=60)
        self.hashtag_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5)
        self.hashtag_entry.insert(0, "#shorts #science #research #ai #machinelearning #arxiv")
        
        # 스케줄링
        schedule_frame = ttk.Frame(settings_frame)
        schedule_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.schedule_var = tk.BooleanVar(value=False)
        schedule_check = ttk.Checkbutton(
            schedule_frame,
            text="Schedule for later",
            variable=self.schedule_var,
            command=self.toggle_schedule
        )
        schedule_check.pack(side=tk.LEFT)
        
        self.schedule_time = ttk.Entry(schedule_frame, width=20, state='disabled')
        self.schedule_time.pack(side=tk.LEFT, padx=10)
        self.schedule_time.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # 게시 버튼
        publish_btn_frame = ttk.Frame(container)
        publish_btn_frame.pack(pady=20)
        
        self.publish_btn = ttk.Button(
            publish_btn_frame,
            text="🚀 Publish Now",
            command=self.publish_video,
            style='Accent.TButton'
        )
        self.publish_btn.pack()
        
        # 게시 기록
        history_frame = ttk.LabelFrame(container, text="Publishing History", padding=15)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 트리뷰
        columns = ('Date', 'Video', 'Platforms', 'Status')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, height=8)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # 샘플 데이터
        self.add_history_item(
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "arxiv_2401_00001.mp4",
            "YouTube, Instagram",
            "✅ Success"
        )
        
    def toggle_schedule(self):
        """스케줄 토글"""
        if self.schedule_var.get():
            self.schedule_time.config(state='normal')
            self.publish_btn.config(text="📅 Schedule Publishing")
        else:
            self.schedule_time.config(state='disabled')
            self.publish_btn.config(text="🚀 Publish Now")
            
    def publish_video(self):
        """비디오 게시"""
        if not self.video_var.get():
            messagebox.showwarning("No Video", "Please select a video to publish")
            return
            
        platforms = [name for name, var in self.platform_vars.items() if var.get()]
        
        if not platforms:
            messagebox.showwarning("No Platform", "Please select at least one platform")
            return
            
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("No Title", "Please enter a title")
            return
            
        # 확인 대화상자
        platform_str = ", ".join(platforms)
        msg = f"Publish to {platform_str}?"
        
        if self.schedule_var.get():
            msg += f"\n\nScheduled for: {self.schedule_time.get()}"
            
        if messagebox.askyesno("Confirm Publishing", msg):
            self.perform_publish(platforms)
            
    def perform_publish(self, platforms):
        """실제 게시 수행"""
        video_path = self.get_video_path()
        if not video_path:
            messagebox.showerror("Error", "Video file not found")
            return
        
        title = self.title_entry.get().strip()
        description = self.desc_text.get(1.0, tk.END).strip()
        hashtags = self.hashtag_entry.get().strip()
        
        history_item = self.add_history_item(
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            self.video_var.get(),
            ", ".join([p.capitalize() for p in platforms]),
            "🔄 Processing"
        )
        
        def upload_callback(results):
            status_messages = []
            for platform, result in results.items():
                if result['status'] == 'success':
                    status_messages.append(f"✅ {platform.capitalize()}")
                else:
                    status_messages.append(f"❌ {platform.capitalize()}: {result.get('message', 'Failed')}")
            
            final_status = " | ".join(status_messages)
            self.update_history_item(history_item, final_status)
            
            if any(r['status'] == 'success' for r in results.values()):
                messagebox.showinfo("Upload Complete", f"Upload finished!\n\n{final_status}")
            else:
                messagebox.showerror("Upload Failed", f"All uploads failed!\n\n{final_status}")
        
        self.publish_manager.publish_to_platforms(
            video_path, platforms, title, description, hashtags, upload_callback
        )
        
        messagebox.showinfo(
            "Publishing Started",
            f"Publishing to {len(platforms)} platform(s)...\n\nCheck the history for status updates."
        )
        
    def add_history_item(self, date, video, platforms, status):
        """히스토리 항목 추가"""
        item = self.history_tree.insert('', 0, values=(date, video, platforms, status))
        
        # 최대 50개 유지
        children = self.history_tree.get_children()
        if len(children) > 50:
            self.history_tree.delete(children[-1])
        
        return item
    
    def update_history_item(self, item, status):
        """히스토리 항목 상태 업데이트"""
        values = list(self.history_tree.item(item, 'values'))
        values[3] = status
        self.history_tree.item(item, values=values)
    
    def load_videos(self):
        """비디오 파일 목록 로드"""
        video_dir = "output/videos"
        if os.path.exists(video_dir):
            videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
            self.video_combo['values'] = videos
            if videos:
                self.video_combo.set(videos[0])
    
    def get_video_path(self):
        """선택된 비디오의 전체 경로 반환"""
        video_name = self.video_var.get()
        if video_name:
            return os.path.join("output/videos", video_name)
        return None
