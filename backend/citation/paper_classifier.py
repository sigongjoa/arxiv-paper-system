from transformers import pipeline
import logging
from typing import Dict

class PaperClassifier:
    def __init__(self):
        try:
            self.classifier = pipeline("zero-shot-classification", 
                                     model="facebook/bart-large-mnli",
                                     device=-1)  # CPU 사용
            
            self.problem_domains = [
                "optimization", "prediction", "classification", 
                "generation", "analysis", "detection", "simulation",
                "recommendation", "clustering", "regression"
            ]
            
            self.solution_types = [
                "neural_network", "statistical_method", "algorithmic",
                "hybrid_approach", "framework", "tool", "deep_learning",
                "machine_learning", "mathematical_model", "heuristic"
            ]
            
            logging.error("Paper classifier initialized")
            
        except Exception as e:
            logging.error(f"Classifier initialization error: {str(e)}", exc_info=True)
            self.classifier = None
            
    def classify_paper(self, title: str, abstract: str) -> Dict:
        """논문의 문제 도메인과 해결방법 분류"""
        if not self.classifier:
            return {
                'problem_domain': 'unknown',
                'solution_type': 'unknown',
                'confidence': {'problem': 0.0, 'solution': 0.0}
            }
            
        try:
            text = f"{title}. {abstract[:500]}"  # 길이 제한
            
            # 문제 도메인 분류
            problem_result = self.classifier(text, candidate_labels=self.problem_domains)
            problem_domain = problem_result['labels'][0]
            problem_confidence = problem_result['scores'][0]
            
            # 해결방법 유형 분류
            solution_result = self.classifier(text, candidate_labels=self.solution_types)
            solution_type = solution_result['labels'][0]
            solution_confidence = solution_result['scores'][0]
            
            return {
                'problem_domain': problem_domain,
                'solution_type': solution_type,
                'confidence': {
                    'problem': problem_confidence,
                    'solution': solution_confidence
                }
            }
            
        except Exception as e:
            logging.error(f"Classification error: {str(e)}", exc_info=True)
            return {
                'problem_domain': 'unknown',
                'solution_type': 'unknown',
                'confidence': {'problem': 0.0, 'solution': 0.0}
            }
