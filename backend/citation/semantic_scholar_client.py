import requests
import time
import logging
from typing import Dict, List, Optional

class SemanticScholarClient:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"x-api-key": api_key})
        self.rate_limit_delay = 1.0
        
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """arXiv ID로 논문 정보 조회"""
        try:
            url = f"{self.base_url}/paper/arXiv:{arxiv_id}"
            params = {
                'fields': 'paperId,title,abstract,authors,venue,year,citationCount,referenceCount,citations,references,influentialCitationCount'
            }
            
            response = self.session.get(url, params=params)
            logging.error(f"S2 API request: {arxiv_id}, status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(self.rate_limit_delay * 2)
                return self.get_paper_by_arxiv_id(arxiv_id)
            else:
                return None
                
        except Exception as e:
            logging.error(f"S2 API error for {arxiv_id}: {str(e)}", exc_info=True)
            return None
            
    def get_paper_citations(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """논문의 인용 논문들 조회"""
        try:
            url = f"{self.base_url}/paper/{paper_id}/citations"
            params = {
                'fields': 'paperId,title,authors,year,citationCount',
                'limit': limit
            }
            
            response = self.session.get(url, params=params)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
            
        except Exception as e:
            logging.error(f"Citations API error for {paper_id}: {str(e)}", exc_info=True)
            return []
            
    def get_paper_references(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """논문의 참고문헌들 조회"""
        try:
            url = f"{self.base_url}/paper/{paper_id}/references"
            params = {
                'fields': 'paperId,title,authors,year,citationCount',
                'limit': limit
            }
            
            response = self.session.get(url, params=params)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
            
        except Exception as e:
            logging.error(f"References API error for {paper_id}: {str(e)}", exc_info=True)
            return []
