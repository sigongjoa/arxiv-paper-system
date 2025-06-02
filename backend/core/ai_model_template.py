import os
import logging
from openai import OpenAI
import anthropic

class AIModelIntegration:
    """
    AI 모델 통합을 위한 템플릿 클래스
    실제 구현 시 이 코드를 key_extractor.py에 통합
    """
    
    def __init__(self):
        # API 키 확인
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.openai_key and not self.anthropic_key:
            raise ValueError(
                "No AI API keys found. Please set either:\n"
                "- OPENAI_API_KEY for GPT-4\n"
                "- ANTHROPIC_API_KEY for Claude"
            )
        
        # 클라이언트 초기화
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
        if self.anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
    
    def extract_key_findings_gpt4(self, paper_data):
        """GPT-4를 사용한 핵심 내용 추출"""
        prompt = f"""
        Extract 3 key findings from this research paper:
        
        Title: {paper_data['title']}
        Abstract: {paper_data['abstract']}
        
        Format your response as JSON:
        {{
            "main_contribution": "...",
            "methodology": "...",
            "results": "...",
            "impact": "..."
        }}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def extract_key_findings_claude(self, paper_data):
        """Claude를 사용한 핵심 내용 추출"""
        prompt = f"""
        Extract 3 key findings from this research paper:
        
        Title: {paper_data['title']}
        Abstract: {paper_data['abstract']}
        
        Format your response as JSON:
        {{
            "main_contribution": "...",
            "methodology": "...", 
            "results": "...",
            "impact": "..."
        }}
        """
        
        response = self.anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        import json
        return json.loads(response.content[0].text)
    
    def generate_video_script(self, key_findings, paper_data):
        """비디오 스크립트 생성"""
        prompt = f"""
        Create a 60-second video script for a scientific paper.
        
        Paper: {paper_data['title']}
        Key findings: {key_findings}
        
        Structure:
        1. Hook (5 seconds) - Attention-grabbing opening
        2. Problem (10 seconds) - What problem does this solve?
        3. Solution (30 seconds) - How does it work?
        4. Impact (15 seconds) - Why does it matter?
        
        Requirements:
        - Use simple language (8th grade level)
        - Include specific numbers/results
        - Make it engaging and shareable
        
        Format as JSON with timing and visual suggestions.
        """
        
        if self.openai_key:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.content[0].text
