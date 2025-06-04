import logging
import re
from typing import Dict

class HookGenerator:
    def __init__(self):
        self.hook_patterns = {
            "curiosity": [
                "이 AI 연구가 {impact}를 바꿀 수 있다고?",
                "연구자들이 발견한 놀라운 사실: {finding}",
                "당신이 모르는 {topic}의 진실"
            ],
            "urgency": [
                "지금 당장 알아야 할 {topic} 연구", 
                "60초만에 이해하는 {topic}",
                "놓치면 후회할 {topic} 발견"
            ],
            "impact": [
                "이 연구가 {field} 분야를 완전히 바꾼다",
                "{performance}% 성능 향상, 어떻게 가능했을까?",
                "불가능했던 {task}가 현실이 되었다"
            ]
        }
        
    def generate(self, paper_data: Dict) -> str:
        logging.info(f"Generating hook for: {paper_data.get('title')}")
        
        if not paper_data.get('title') or not paper_data.get('abstract'):
            raise ValueError("Paper title and abstract required for hook generation")
            
        impact = self._extract_impact(paper_data)
        finding = self._extract_key_finding(paper_data)
        topic = self._extract_topic(paper_data)
        field = self._extract_field(paper_data)
        performance = self._extract_performance(paper_data)
        task = self._extract_task(paper_data)
        
        # 가장 적합한 패턴 선택
        if performance:
            template = self.hook_patterns["impact"][1]
            return template.format(performance=performance)
        elif impact:
            template = self.hook_patterns["curiosity"][0] 
            return template.format(impact=impact)
        elif topic:
            template = self.hook_patterns["urgency"][1]
            return template.format(topic=topic)
        else:
            raise ValueError(f"Cannot generate hook from paper data: insufficient content")
            
    def _extract_impact(self, paper_data: Dict) -> str:
        title = paper_data.get('title', '').lower()
        abstract = paper_data.get('abstract', '').lower()
        
        impact_keywords = {
            'efficiency': '효율성',
            'performance': '성능', 
            'accuracy': '정확도',
            'speed': '속도',
            'cost': '비용',
            'healthcare': '의료',
            'education': '교육',
            'industry': '산업'
        }
        
        for eng, kor in impact_keywords.items():
            if eng in title or eng in abstract:
                return kor
                
        return "AI 기술"
        
    def _extract_key_finding(self, paper_data: Dict) -> str:
        abstract = paper_data.get('abstract', '')
        
        # 수치 패턴 찾기
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%', abstract)
        if numbers:
            return f"{numbers[0]}% 개선"
            
        # 성능 향상 키워드
        performance_words = ['improve', 'enhance', 'increase', 'better', 'superior']
        for word in performance_words:
            if word in abstract.lower():
                return "성능 대폭 향상"
                
        return "혁신적 결과"
        
    def _extract_topic(self, paper_data: Dict) -> str:
        title = paper_data.get('title', '')
        categories = paper_data.get('categories', [])
        
        category_map = {
            'cs.AI': 'AI',
            'cs.LG': '머신러닝', 
            'cs.CV': '컴퓨터 비전',
            'cs.CL': '자연어처리',
            'cs.RO': '로보틱스',
            'stat.ML': '머신러닝',
            'math.OC': '최적화'
        }
        
        for cat in categories:
            if cat in category_map:
                return category_map[cat]
                
        # 제목에서 주요 키워드 추출
        tech_keywords = ['neural', 'deep', 'learning', 'network', 'algorithm', 'model']
        for keyword in tech_keywords:
            if keyword in title.lower():
                return 'AI'
                
        return '최신 연구'
        
    def _extract_field(self, paper_data: Dict) -> str:
        categories = paper_data.get('categories', [])
        
        field_map = {
            'cs': '컴퓨터과학',
            'stat': '통계학',
            'math': '수학',
            'physics': '물리학',
            'q-bio': '생물학'
        }
        
        for cat in categories:
            prefix = cat.split('.')[0]
            if prefix in field_map:
                return field_map[prefix]
                
        return '연구'
        
    def _extract_performance(self, paper_data: Dict) -> str:
        abstract = paper_data.get('abstract', '')
        
        # 퍼센트 숫자 찾기
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', abstract)
        if percentages:
            return percentages[0]
            
        # 배수 표현 찾기  
        multipliers = re.findall(r'(\d+(?:\.\d+)?)\s*[×x]\s*(?:faster|better|more)', abstract)
        if multipliers:
            return str(int(float(multipliers[0]) * 100))
            
        return ""
        
    def _extract_task(self, paper_data: Dict) -> str:
        title = paper_data.get('title', '').lower()
        abstract = paper_data.get('abstract', '').lower()
        
        task_keywords = {
            'classification': '분류',
            'detection': '탐지', 
            'recognition': '인식',
            'generation': '생성',
            'translation': '번역',
            'prediction': '예측',
            'optimization': '최적화'
        }
        
        for eng, kor in task_keywords.items():
            if eng in title or eng in abstract:
                return kor
                
        return "문제 해결"
