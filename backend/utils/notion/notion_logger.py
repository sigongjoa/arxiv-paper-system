import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

class NotionLogger:
    def __init__(self, notion_token=None, database_id=None):
        self.token = notion_token
        self.database_id = database_id
        
    def log_analysis_result(self, analysis_result, error_details=None):
        """분석 결과 또는 오류를 Notion에 문서화"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'paper_id': getattr(analysis_result, 'paper_id', 'unknown'),
                'title': getattr(analysis_result, 'title', 'Unknown'),
                'platform': getattr(analysis_result, 'platform', 'Unknown'),
                'confidence_score': getattr(analysis_result, 'confidence_score', 0.0),
                'analysis_data': {
                    'summary': getattr(analysis_result, 'summary', ''),
                    'key_insights': getattr(analysis_result, 'key_insights', []),
                    'methodology': getattr(analysis_result, 'methodology', ''),
                    'main_findings': getattr(analysis_result, 'main_findings', []),
                    'limitations': getattr(analysis_result, 'limitations', []),
                    'future_work': getattr(analysis_result, 'future_work', []),
                    'keywords': getattr(analysis_result, 'technical_keywords', [])
                }
            }
            
            if error_details:
                log_data['error'] = error_details
                log_data['status'] = 'ERROR'
            else:
                log_data['status'] = 'SUCCESS'
            
            # JSON 형태로 로깅 (ERROR 레벨)
            logging.error(f"NOTION_LOG: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
            
            return log_data
            
        except Exception as e:
            logging.error(f"Notion 로깅 실패: {e}")
            raise
    
    def log_pdf_generation(self, paper_data, pdf_path, error_details=None):
        """PDF 생성 결과를 Notion에 문서화"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'operation': 'PDF_GENERATION',
                'paper_id': paper_data.get('paper_id', 'unknown'),
                'title': paper_data.get('title', 'Unknown'),
                'pdf_path': pdf_path,
                'platform': paper_data.get('platform', 'Unknown')
            }
            
            if error_details:
                log_data['error'] = error_details
                log_data['status'] = 'ERROR'
            else:
                log_data['status'] = 'SUCCESS'
            
            logging.error(f"NOTION_LOG: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
            
            return log_data
            
        except Exception as e:
            logging.error(f"PDF 생성 Notion 로깅 실패: {e}")
            raise
    
    def log_debug_info(self, operation, details, error=None):
        """디버그 정보를 Notion에 문서화"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'details': details,
                'level': 'DEBUG'
            }
            
            if error:
                log_data['error'] = str(error)
                log_data['status'] = 'ERROR'
            else:
                log_data['status'] = 'SUCCESS'
            
            logging.error(f"NOTION_DEBUG: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
            
            return log_data
            
        except Exception as e:
            logging.error(f"디버그 Notion 로깅 실패: {e}")
            raise
