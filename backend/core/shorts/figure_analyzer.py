import requests
import base64
import logging

class ScientificFigureAnalyzer:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url
        self.analysis_prompt = """
[ROLE] 당신은 과학 분야의 전문 연구자입니다.
[TASK] 이 과학 그림을 분석하고 다음을 수행하세요:
1) 그림 유형 식별 (표/사진/다이어그램/지도/플롯)
2) 축과 레이블의 모든 수치값 추출
3) 통계적 유의성 지표 파악
4) 생물학적/과학적 의미 설명
[FORMAT] 분석 결과를 다음 형식으로 제공하세요:
- 그림 유형: 
- 주요 발견:
- 데이터 포인트:
- 과학적 해석:
[CONSTRAINTS] 정확한 과학적 해석에 집중하세요.
"""

    def analyze_figure_from_base64(self, image_base64, caption="", figure_type="figure"):
        """Base64 인코딩된 이미지 분석"""
        logging.info(f"Analyzing figure from base64 data: {figure_type}")
        
        if not self.base_url:
            # LM Studio 연결 실패시 폴백 분석
            return self._get_fallback_analysis(caption, figure_type)
            
        return self._analyze_base64_with_lm_studio(image_base64, caption, figure_type)
    
    def _analyze_base64_with_lm_studio(self, image_base64, caption, figure_type):
        """LM Studio를 사용한 base64 이미지 분석"""
        payload = {
            "model": "current-vision-model",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"{self.analysis_prompt}\n\n캡션: {caption}\n그림 유형: {figure_type}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        try:
            response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logging.error(f"LM Studio API error: {response.status_code}")
                return self._get_fallback_analysis(caption, figure_type)
                
        except Exception as e:
            logging.warning(f"LM Studio request failed: {e}")
            return self._get_fallback_analysis(caption, figure_type)
    
    def _get_fallback_analysis(self, caption, figure_type):
        """LM Studio 실패시 폴백 분석"""
        fallback_map = {
            'performance_plot': f"성능 차트: {caption[:100]}",
            'architecture_diagram': f"구조도: {caption[:100]}", 
            'comparison_chart': f"비교 차트: {caption[:100]}",
            'table': f"데이터 표: {caption[:100]}",
            'figure': f"연구 그림: {caption[:100]}"
        }
        
        return fallback_map.get(figure_type, f"그림 분석: {caption[:100]}")

    def _analyze_with_lm_studio(self, image_path):
        image_base64 = self._encode_image_to_base64(image_path)
        
        payload = {
            "model": "current-vision-model",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": self.analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logging.error(f"LM Studio API error: {response.status_code}")
            raise Exception(f"LM Studio API error: {response.status_code}")

    def _encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
