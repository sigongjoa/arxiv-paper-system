import asyncio
import os
import logging
from .figure_analyzer import ScientificFigureAnalyzer
from .short_script_generator import ShortScriptGenerator
from .short_video_creator import ShortVideoCreator

class ArxivVideoGenerator:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.figure_analyzer = ScientificFigureAnalyzer(base_url)
        self.script_generator = ShortScriptGenerator(base_url)
        self.video_creator = ShortVideoCreator()

    async def process_paper(self, arxiv_id, paper_content, audience_level="general"):
        logging.info(f"Processing paper {arxiv_id} for {audience_level} audience")
        
        try:
            # 1. 그림 추출 및 분석
            figures = await self._extract_figures(paper_content)
            figure_analysis = await self._analyze_figures(figures)
            
            # 2. 쇼츠 스크립트 생성 (LM Studio)
            script = self.script_generator.generate_short_script(
                paper_content, figure_analysis, audience_level
            )
            
            # 3. 비디오 생성 (ResearchVideoTemplate)
            video_path = await self._generate_video(script, figures, arxiv_id, paper_content)
            
            result = {
                "script": script,
                "video_path": video_path,
                "processing_status": "completed"
            }
            
            logging.info(f"Paper processing complete for {arxiv_id}")
            return result
            
        except Exception as e:
            logging.error(f"Paper processing failed for {arxiv_id}: {str(e)}")
            raise

    async def _extract_figures(self, paper_content):
        figures = paper_content.get('figures', [])
        logging.info(f"Extracted {len(figures)} figures from paper")
        return figures if figures else []

    async def _analyze_figures(self, figures):
        if not figures:
            return "논문에서 추출된 그림이 없습니다."
        
        analysis_results = []
        for figure in figures:
            try:
                # figure는 dict 객체 (image_base64 포함)
                if isinstance(figure, dict) and 'image_base64' in figure:
                    analysis = self.figure_analyzer.analyze_figure_from_base64(
                        figure['image_base64'], 
                        figure.get('caption', ''),
                        figure.get('figure_type', 'figure')
                    )
                    analysis_results.append(analysis)
            except Exception as e:
                logging.warning(f"Figure analysis failed: {e}")
                continue
        
        return " ".join(analysis_results) if analysis_results else "그림 분석 실패"

    async def _generate_video(self, script, figures, arxiv_id, paper_content):
        from ..narrator.tts_engine import TTSEngine
        import time
        
        # TTS 오디오 생성
        tts = TTSEngine()
        full_text = self._combine_script_text(script)
        
        # 출력 디렉토리 설정
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_dir = os.path.join(project_root, "output", "videos")
        os.makedirs(output_dir, exist_ok=True)
        
        # 파일명 생성
        safe_title = self._create_safe_filename(paper_content.get('title', arxiv_id))
        timestamp = int(time.time())
        
        audio_path = os.path.join(output_dir, f"{safe_title}_{arxiv_id}_{timestamp}.wav")
        tts.generate(full_text, audio_path)
        
        video_path = os.path.join(output_dir, f"{safe_title}_{arxiv_id}_{timestamp}.mp4")
        
        logging.info(f"Creating video with ResearchVideoTemplate: {video_path}")
        
        # ResearchVideoTemplate으로 비디오 생성 (paper_data 포함)
        self.video_creator.create_short_video(script, figures, audio_path, video_path, paper_content)
        
        return video_path
    
    def _create_safe_filename(self, title):
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '', title)
        safe = re.sub(r'\s+', '_', safe)
        return safe[:50]

    def _combine_script_text(self, script):
        text_parts = []
        for section_data in script.values():
            if isinstance(section_data, dict) and "content" in section_data:
                text_parts.append(section_data["content"])
        return " ".join(text_parts)
