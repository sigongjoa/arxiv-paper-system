import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.lm_studio_client import LMStudioClient
from backend.paper_analyzer import PaperAnalyzer
from backend.core.shorts.hook_generator import HookGenerator
import logging

class ScriptGeneratorImpl:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.client = LMStudioClient(base_url)
        self.analyzer = PaperAnalyzer()
        self.hook_generator = HookGenerator()
        
    def generate_script(self, summary_data, paper_data):
        logging.info(f"ERROR 레벨: Generating figure-based shorts script for {paper_data.get('title', 'Unknown')}")
        
        if not paper_data or not summary_data:
            raise ValueError("ERROR: Paper data and summary required for script generation")
        
        # 그림 기반 대본 생성 (새로운 방식)
        try:
            script_data = self.client.generate_figure_based_script(paper_data)
            
            # paper_id 추가 (고유 파일명 생성용)
            script_data['paper_id'] = paper_data['arxiv_id']
            script_data['paper_title'] = paper_data.get('title', 'Unknown Paper')
            script_data['arxiv_id'] = paper_data['arxiv_id']
            
            # 그림 정보가 있으면 scenes 구조로 변환
            if paper_data.get('figures') and len(paper_data['figures']) > 0:
                script_data['scenes'] = self._convert_to_scenes(script_data, paper_data)
            else:
                # 그림이 없으면 기존 방식으로 폴백
                script_data['scenes'] = self._generate_text_based_scenes(summary_data, paper_data)
            
            # 60초 초과 시 자동 조정
            total_duration = sum(scene.get('duration', 0) for scene in script_data.get('scenes', []))
            if total_duration > 60:
                scale_factor = 60 / total_duration
                for scene in script_data.get('scenes', []):
                    scene['duration'] = int(scene.get('duration', 0) * scale_factor)
                
                total_duration = sum(scene.get('duration', 0) for scene in script_data.get('scenes', []))
                logging.info(f"Script duration adjusted: {total_duration}s (scale: {scale_factor:.2f})")
            
            logging.info(f"Generated figure-based script: {paper_data['arxiv_id']} - {len(script_data.get('scenes', []))} scenes, {total_duration}s total, {script_data.get('figure_count', 0)} figures")
            return script_data
            
        except Exception as e:
            logging.error(f"ERROR 레벨: Figure-based script generation failed: {e}")
            # 완전 폴백: 기존 텍스트 기반 방식
            return self._generate_fallback_script(summary_data, paper_data)
    
    def _convert_to_scenes(self, script_data, paper_data):
        """그림 기반 스크립트를 scenes 구조로 변환"""
        scenes = []
        
        if 'sections' in script_data:
            for i, section in enumerate(script_data['sections']):
                scene = {
                    'id': i,
                    'content': section['content'],
                    'duration': section['duration'],
                    'type': section['type']
                }
                
                # 그림 정보 추가
                if section['type'] == 'figure_explanation' and 'figure_index' in section:
                    fig_idx = section['figure_index']
                    if fig_idx < len(paper_data['figures']):
                        scene['figure_data'] = paper_data['figures'][fig_idx]
                        scene['figure_type'] = section.get('figure_type', 'figure')
                
                scenes.append(scene)
        
        return scenes
    
    def _generate_text_based_scenes(self, summary_data, paper_data):
        """그림이 없을 때 텍스트 기반 scenes 생성"""
        logging.info("Generating text-based scenes (no figures)")
        
        # 기본 3개 씬 구조
        scenes = [
            {
                'id': 0,
                'content': self._generate_hook_content(paper_data),
                'duration': 5,
                'type': 'hook'
            },
            {
                'id': 1,
                'content': self._generate_main_content(summary_data, paper_data),
                'duration': 45,
                'type': 'main_content'
            },
            {
                'id': 2,
                'content': self._generate_conclusion_content(paper_data),
                'duration': 10,
                'type': 'conclusion'
            }
        ]
        
        return scenes
    
    def _generate_hook_content(self, paper_data):
        """후크 콘텐츠 생성"""
        categories = paper_data.get('categories', [])
        title = paper_data.get('title', '')
        
        hooks = [
            f"이 연구가 {self._get_field_name(categories)} 분야를 바꿀 수 있을까요?",
            f"과학자들이 발견한 놀라운 사실을 보여드릴게요!",
            f"{self._get_field_name(categories)} 기술의 새로운 돌파구를 발견했습니다!",
            f"이 연구 결과가 당신을 놀라게 할 거예요!"
        ]
        
        return hooks[hash(paper_data['arxiv_id']) % len(hooks)]
    
    def _generate_main_content(self, summary_data, paper_data):
        """메인 콘텐츠 생성"""
        title = paper_data.get('title', '')
        abstract = paper_data.get('abstract', '')[:200]
        
        return f"""
이 연구는 {title}에 대한 내용입니다. 
연구진들은 {abstract}라는 중요한 발견을 했습니다. 
이런 결과들이 실제로 우리 생활에 어떤 변화를 가져올지 기대됩니다.
"""
    
    def _generate_conclusion_content(self, paper_data):
        """결론 콘텐츠 생성"""
        categories = paper_data.get('categories', [])
        field_name = self._get_field_name(categories)
        
        conclusions = [
            f"이런 {field_name} 연구가 더 궁금하다면 팔로우하세요!",
            f"{field_name}의 미래가 어떻게 바뀔지, 더 알아보고 싶지 않나요?",
            f"과학의 놀라운 발견들, 계속 함께 탐험해요!",
            f"이런 연구 결과들이 우리 삶을 어떻게 바꿀까요?"
        ]
        
        return conclusions[hash(paper_data['arxiv_id']) % len(conclusions)]
    
    def _get_field_name(self, categories):
        """카테고리를 한국어 분야명으로 변환"""
        field_map = {
            'cs.AI': 'AI',
            'cs.LG': '머신러닝',
            'cs.CL': '자연어처리',
            'cs.CV': '컴퓨터비전',
            'stat.ML': '통계학습',
            'cs.IR': '정보검색',
            'cs.DC': '분산컴퓨팅',
            'cs.NE': '신경망',
            'cs.CR': '암호학',
            'cs.DB': '데이터베이스',
            'cs.HC': '인간-컴퓨터 상호작용',
            'cs.SE': '소프트웨어공학'
        }
        
        for category in categories:
            if category in field_map:
                return field_map[category]
        
        return '과학기술'
    
    def _generate_fallback_script(self, summary_data, paper_data):
        """완전 폴백 스크립트 생성"""
        logging.warning(f"Using fallback script generation for {paper_data['arxiv_id']}")
        
        scenes = self._generate_text_based_scenes(summary_data, paper_data)
        
        return {
            'paper_id': paper_data['arxiv_id'],
            'paper_title': paper_data.get('title', 'Unknown Paper'),
            'arxiv_id': paper_data['arxiv_id'],
            'script': "\n".join(scene['content'] for scene in scenes),
            'scenes': scenes,
            'total_duration': sum(scene['duration'] for scene in scenes),
            'figure_count': 0,
            'fallback_used': True
        }
