import requests
import json
import logging
import time

class LMStudioClient:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url
        
    def generate_figure_based_script(self, paper_data):
        """그림 기반 60초 쇼츠 대본 생성"""
        logging.info(f"Generating figure-based script for {paper_data['arxiv_id']}")
        
        # 그림 정보가 없으면 기존 텍스트 기반으로 폴백
        if not paper_data.get('figures') or len(paper_data['figures']) == 0:
            return self._generate_text_based_script(paper_data)
        
        # 그림 기반 대본 생성
        script_sections = []
        
        # 1. 후크 생성 (3-5초)
        hook = self._generate_hook(paper_data)
        script_sections.append({
            'type': 'hook',
            'duration': 4,
            'content': hook,
            'visual_cue': 'title_card'
        })
        
        # 2. 메인 그림들 기반 설명 (45-50초)
        main_content = self._generate_figure_explanations(paper_data)
        script_sections.extend(main_content)
        
        # 3. 마무리 및 CTA (5-7초)
        conclusion = self._generate_conclusion(paper_data)
        script_sections.append({
            'type': 'conclusion',
            'duration': 6,
            'content': conclusion,
            'visual_cue': 'end_card'
        })
        
        # 총 대본 조합
        full_script = self._combine_script_sections(script_sections)
        
        return {
            'script': full_script,
            'sections': script_sections,
            'total_duration': sum(section['duration'] for section in script_sections),
            'figure_count': len(paper_data['figures'])
        }
    
    def _generate_hook(self, paper_data):
        """3-5초 후킹 문구 생성"""
        figures = paper_data['figures']
        title = paper_data['title']
        categories = paper_data.get('categories', [])
        
        # 그림 유형에 따른 후크 전략
        primary_figure = figures[0] if figures else None
        
        hook_templates = {
            'performance_plot': f"이 그래프가 보여주는 놀라운 AI 성능 향상을 보세요!",
            'architecture_diagram': f"이 구조도 하나가 {self._get_field_name(categories)} 분야를 바꿀 수 있을까요?",
            'comparison_chart': f"기존 방법 vs 새로운 방법, 그 차이가 이렇게 클 줄이야!",
            'table': f"이 수치들이 말해주는 놀라운 사실은 뭘까요?",
            'figure': f"과학자들이 발견한 이 패턴, 당신의 생각을 바꿀 겁니다!"
        }
        
        if primary_figure and primary_figure['figure_type'] in hook_templates:
            hook = hook_templates[primary_figure['figure_type']]
        else:
            # 일반적인 후크
            hook = f"{self._get_field_name(categories)} 연구의 이 발견이 당신을 놀라게 할 거예요!"
        
        return hook
    
    def _generate_figure_explanations(self, paper_data):
        """그림들을 기반으로 한 메인 설명 생성 (45-50초)"""
        figures = paper_data['figures']
        title = paper_data['title']
        abstract = paper_data['abstract']
        
        sections = []
        remaining_duration = 46  # 46초 할당
        
        # 최대 3개 그림 사용 (쇼츠에 적합)
        key_figures = figures[:3]
        duration_per_figure = remaining_duration // len(key_figures)
        
        for i, figure in enumerate(key_figures):
            explanation = self._generate_single_figure_explanation(
                figure, paper_data, duration_per_figure
            )
            
            sections.append({
                'type': 'figure_explanation',
                'figure_index': i,
                'duration': duration_per_figure,
                'content': explanation,
                'visual_cue': f'figure_{i}',
                'figure_type': figure['figure_type']
            })
        
        return sections
    
    def _generate_single_figure_explanation(self, figure, paper_data, duration):
        """개별 그림에 대한 설명 생성"""
        
        # LM Studio에 보낼 프롬프트 구성
        prompt = f"""
당신은 과학 커뮤니케이션 전문가입니다. 다음 조건에 맞춰 {duration}초 분량의 설명을 생성하세요:

**논문 정보:**
- 제목: {paper_data['title']}
- 분야: {', '.join(paper_data.get('categories', []))}
- 요약: {paper_data['abstract'][:200]}...

**그림 정보:**
- 유형: {figure['figure_type']}
- 캡션: {figure.get('caption', 'No caption')}
- 추출된 텍스트: {figure.get('extracted_text', 'No text')}

**생성 규칙:**
1. {duration}초 분량 (약 {duration * 2.5}단어)
2. 일반인도 이해할 수 있는 쉬운 언어 사용
3. 그림의 핵심 내용을 단계별로 설명
4. 실제 응용이나 의미 포함
5. 흥미로운 요소나 놀라운 사실 강조

**설명 생성:**
"""

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": "당신은 과학을 쉽게 설명하는 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": duration * 15  # 초당 약 15 토큰
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                explanation = result['choices'][0]['message']['content'].strip()
                
                # 길이 조정
                words = explanation.split()
                target_words = duration * 2.5
                if len(words) > target_words:
                    explanation = ' '.join(words[:int(target_words)])
                
                return explanation
            else:
                logging.error(f"LM Studio error: {response.status_code}")
                return self._get_fallback_explanation(figure, duration)
                
        except Exception as e:
            logging.error(f"LM Studio request failed: {e}")
            return self._get_fallback_explanation(figure, duration)
    
    def _generate_conclusion(self, paper_data):
        """마무리 및 CTA 생성 (5-7초)"""
        categories = paper_data.get('categories', [])
        field_name = self._get_field_name(categories)
        
        conclusions = [
            f"이런 {field_name} 연구가 더 궁금하다면 팔로우하세요!",
            f"{field_name}의 미래가 어떻게 바뀔지, 더 알아보고 싶지 않나요?",
            f"과학의 놀라운 발견들, 계속 함께 탐험해요!",
            f"이런 연구 결과들이 우리 삶을 어떻게 바꿀까요? 더 보러 가시죠!"
        ]
        
        return conclusions[hash(paper_data['arxiv_id']) % len(conclusions)]
    
    def _combine_script_sections(self, sections):
        """섹션들을 하나의 대본으로 결합"""
        script_parts = []
        
        for section in sections:
            if section['type'] == 'hook':
                script_parts.append(f"[후크 - {section['duration']}초]")
                script_parts.append(section['content'])
                script_parts.append("")
            
            elif section['type'] == 'figure_explanation':
                script_parts.append(f"[그림 {section['figure_index'] + 1} - {section['duration']}초]")
                script_parts.append(section['content'])
                script_parts.append("")
            
            elif section['type'] == 'conclusion':
                script_parts.append(f"[마무리 - {section['duration']}초]")
                script_parts.append(section['content'])
        
        return "\n".join(script_parts)
    
    def _get_fallback_explanation(self, figure, duration):
        """LM Studio 실패시 폴백 설명"""
        figure_type = figure['figure_type']
        caption = figure.get('caption', '')
        
        fallback_templates = {
            'performance_plot': f"이 성능 그래프를 보면 새로운 방법이 기존보다 훨씬 좋은 결과를 보여줍니다. {caption[:50]}",
            'architecture_diagram': f"이 시스템 구조를 보면 각 부분이 어떻게 연결되어 작동하는지 알 수 있습니다. {caption[:50]}",
            'comparison_chart': f"이 비교표는 서로 다른 방법들의 장단점을 명확히 보여줍니다. {caption[:50]}",
            'table': f"이 데이터 표에서 핵심 수치들을 확인할 수 있습니다. {caption[:50]}",
            'figure': f"이 그림은 연구의 중요한 발견을 시각적으로 보여줍니다. {caption[:50]}"
        }
        
        base_explanation = fallback_templates.get(figure_type, f"이 그림은 연구의 핵심 내용을 담고 있습니다. {caption[:50]}")
        
        # 길이 조정
        target_words = duration * 2.5
        words = base_explanation.split()
        if len(words) < target_words:
            base_explanation += " 이런 결과들이 실제로 우리 생활에 어떤 변화를 가져올지 기대됩니다."
        
        return base_explanation[:int(target_words * 6)]  # 대략적인 글자 수 제한
    
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
    
    def _generate_text_based_script(self, paper_data):
        """그림이 없을 때 텍스트 기반 폴백 대본 생성"""
        logging.info("No figures found, generating text-based script")
        
        prompt = f"""
다음 논문을 60초 쇼츠 영상 대본으로 만들어주세요:

제목: {paper_data['title']}
요약: {paper_data['abstract'][:300]}
분야: {', '.join(paper_data.get('categories', []))}

구조:
1. 후크 (3-5초): 시청자 주의를 끄는 문구
2. 메인 설명 (45-50초): 핵심 내용을 쉽게 설명
3. 마무리 (5-7초): 행동 유도

일반인도 이해할 수 있게 쉬운 언어로 작성하세요.
"""

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": "당신은 과학을 쉽게 설명하는 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 400
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                script = result['choices'][0]['message']['content'].strip()
                
                return {
                    'script': script,
                    'sections': [{'type': 'text_based', 'content': script}],
                    'total_duration': 60,
                    'figure_count': 0
                }
            else:
                logging.error(f"LM Studio error: {response.status_code}")
                raise Exception(f"LM Studio API error: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Text-based script generation failed: {e}")
            raise Exception(f"Script generation failed: {e}")
