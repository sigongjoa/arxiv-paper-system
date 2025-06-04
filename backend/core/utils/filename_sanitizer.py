import re
import os

class FilenameSanitizer:
    @staticmethod
    def sanitize_title(title, max_length=100):
        """논문 제목을 파일명으로 안전하게 변환"""
        # 특수문자 제거 및 공백을 언더스코어로 변경
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = re.sub(r'\s+', '_', safe_title.strip())
        safe_title = re.sub(r'[^\w\-_.]', '', safe_title)
        
        # 길이 제한
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length]
        
        # 빈 문자열 방지
        if not safe_title:
            safe_title = "untitled_paper"
            
        return safe_title
    
    @staticmethod
    def create_unique_filename(title, arxiv_id, extension, timestamp=None):
        """논문명 + arxiv_id로 고유 파일명 생성"""
        import time
        if timestamp is None:
            timestamp = int(time.time())
            
        sanitized_title = FilenameSanitizer.sanitize_title(title, 50)
        safe_arxiv_id = arxiv_id.replace('.', '_').replace('v', '_')
        
        filename = f"{sanitized_title}_{safe_arxiv_id}_{timestamp}.{extension}"
        return filename
