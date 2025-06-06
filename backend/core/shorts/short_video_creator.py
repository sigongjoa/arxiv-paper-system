import os
import logging
from moviepy.editor import ImageClip, AudioFileClip
from templates.research_template import ResearchVideoTemplate

class ShortVideoCreator:
    def __init__(self):
        self.video_resolution = (1080, 1920)
        self.max_duration = 60
        self.template = ResearchVideoTemplate()

    def create_short_video(self, script, figures, audio_path, output_path, paper_data=None):
        logging.info(f"Creating short video with template: {output_path}")
        
        title = self._extract_title_from_script(script, paper_data)
        author = self._extract_author_from_paper(paper_data)
        arxiv_id = self._extract_arxiv_id_from_paper(paper_data)
        category = self._extract_category_from_paper(paper_data)
        hashtags = self._extract_hashtags_from_script(script)
        description = self._extract_description_from_script(script, paper_data)
        
        logging.info(f"Extracted title: {title}")
        logging.info(f"Extracted author: {author}")
        logging.info(f"Extracted arxiv_id: {arxiv_id}")
        logging.info(f"Extracted category: {category}")
        logging.info(f"Available figures: {figures}")
        
        # figures는 dict 리스트이므로 base64 데이터를 임시 파일로 저장
        content_image_path = None
        if figures:
            try:
                first_figure = figures[0]
                if isinstance(first_figure, dict) and 'image_base64' in first_figure:
                    # base64 데이터를 임시 파일로 저장
                    import base64
                    import tempfile
                    
                    temp_dir = os.path.dirname(output_path)
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    temp_image_path = os.path.join(temp_dir, f"figure_temp_{os.getpid()}.png")
                    
                    image_data = base64.b64decode(first_figure['image_base64'])
                    with open(temp_image_path, 'wb') as f:
                        f.write(image_data)
                    
                    content_image_path = temp_image_path
                    logging.info(f"Saved figure to temp file: {content_image_path}")
            except Exception as e:
                logging.warning(f"Failed to save figure to temp file: {e}")
                content_image_path = None
        logging.info(f"Content image path: {content_image_path}")
        
        template_image = self.template.CreateTemplate(
            title=title,
            author=author,
            arxiv_id=arxiv_id,
            category=category,
            hashtags=hashtags,
            content_image_path=content_image_path,
            description_text=description
        )
        
        temp_image_path = output_path.replace('.mp4', '_temp.png')
        logging.info(f"Saving template image to: {temp_image_path}")
        template_image.save(temp_image_path)
        
        if os.path.exists(temp_image_path):
            logging.info(f"Template image saved successfully: {os.path.getsize(temp_image_path)} bytes")
        else:
            logging.error(f"Template image NOT saved: {temp_image_path}")
        
        if os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            total_duration = audio.duration
            logging.info(f"Audio duration: {total_duration} seconds")
        else:
            total_duration = 30
            logging.warning(f"Audio file not found: {audio_path}, using default duration")
            
        logging.info(f"Creating video clip from image: {temp_image_path}")
        video = ImageClip(temp_image_path, duration=total_duration)
        
        if os.path.exists(audio_path):
            video = video.set_audio(audio)
        
        logging.info(f"Writing video file: {output_path}")
        video.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            logging.info(f"Temporary image file removed: {temp_image_path}")
        
        final_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        logging.info(f"Short video created: {output_path} ({final_size} bytes)")
        return output_path

    def _extract_title_from_script(self, script, paper_data):
        if paper_data and 'title' in paper_data:
            return paper_data['title'][:80]
        if isinstance(script, dict):
            if 'hook' in script and 'content' in script['hook']:
                return script['hook']['content'][:80]
            elif 'full_script' in script:
                return script['full_script'][:80]
        return "AI Research Insights"
    
    def _extract_author_from_paper(self, paper_data):
        if paper_data and 'authors' in paper_data:
            authors = paper_data['authors']
            if isinstance(authors, list) and authors:
                return authors[0][:30]
            elif isinstance(authors, str):
                return authors[:30]
        return "AI Research Team"
    
    def _extract_arxiv_id_from_paper(self, paper_data):
        if paper_data and 'arxiv_id' in paper_data:
            return paper_data['arxiv_id']
        return "arXiv:2025.0001"
    
    def _extract_category_from_paper(self, paper_data):
        if paper_data and 'category' in paper_data:
            return paper_data['category']
        if paper_data and 'subject_class' in paper_data:
            return paper_data['subject_class']
        return "cs.AI"
    
    def _extract_description_from_script(self, script, paper_data):
        description_parts = []
        
        if paper_data and 'abstract' in paper_data:
            description_parts.append(paper_data['abstract'][:200])
        
        if isinstance(script, dict):
            if 'explanation' in script and 'content' in script['explanation']:
                description_parts.append(script['explanation']['content'][:150])
            elif 'summary' in script and 'content' in script['summary']:
                description_parts.append(script['summary']['content'][:150])
        
        return ' '.join(description_parts)[:500] if description_parts else "논문의 핵심 내용과 혁신적인 아이디어를 간결하게 설명합니다."

    def _extract_hashtags_from_script(self, script):
        if isinstance(script, dict) and 'cta' in script and 'content' in script['cta']:
            cta_content = script['cta']['content'].lower()
            
            # CTA 내용에서 키워드 추출
            keywords = []
            if 'ai' in cta_content or '인공지능' in cta_content:
                keywords.append('#AI')
            if 'research' in cta_content or '연구' in cta_content:
                keywords.append('#Research')
            if 'science' in cta_content or '과학' in cta_content:
                keywords.append('#Science')
            if 'tech' in cta_content or '기술' in cta_content:
                keywords.append('#Tech')
                
            return ' '.join(keywords) if keywords else '#Research'
        
        return '#Research #AI #Science'
