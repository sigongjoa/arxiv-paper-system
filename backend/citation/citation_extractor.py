from .semantic_scholar_client import SemanticScholarClient
from .neo4j_manager import Neo4jManager
from .paper_classifier import PaperClassifier
import logging
from typing import Dict, List, Optional

class CitationExtractor:
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        self.s2_client = SemanticScholarClient()
        self.neo4j = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
        self.classifier = PaperClassifier()
        
    def extract_and_store_citations(self, arxiv_id: str) -> Dict:
        """arXiv ID로 citation 네트워크 추출 및 저장"""
        try:
            # Semantic Scholar에서 논문 정보 조회
            paper_data = self.s2_client.get_paper_by_arxiv_id(arxiv_id)
            if not paper_data:
                logging.error(f"Paper not found in S2: {arxiv_id}")
                return {'success': False, 'error': 'Paper not found'}
            
            # 논문 분류
            if paper_data.get('abstract'):
                classification = self.classifier.classify_paper(
                    paper_data.get('title', ''),
                    paper_data.get('abstract', '')
                )
            else:
                classification = {'problem_domain': 'unknown', 'solution_type': 'unknown'}
            
            # 논문 데이터 준비
            paper_node = {
                'id': paper_data['paperId'],
                'title': paper_data.get('title', ''),
                'abstract': paper_data.get('abstract', ''),
                'year': paper_data.get('year', 0),
                'authors': [author.get('name', '') for author in paper_data.get('authors', [])],
                'venue': paper_data.get('venue', ''),
                'citation_count': paper_data.get('citationCount', 0),
                'arxiv_id': arxiv_id,
                'problem_domain': classification['problem_domain'],
                'solution_type': classification['solution_type']
            }
            
            # Neo4j에 논문 저장
            if not self.neo4j.add_paper(paper_node):
                return {'success': False, 'error': 'Failed to save paper'}
            
            # 인용 논문들 처리
            citations = self.s2_client.get_paper_citations(paper_data['paperId'], limit=50)
            references = self.s2_client.get_paper_references(paper_data['paperId'], limit=50)
            
            saved_citations = 0
            saved_references = 0
            
            # 인용 논문들 저장
            for citation in citations:
                if citation.get('citedPaper'):
                    cited_paper = citation['citedPaper']
                    if self._save_related_paper(cited_paper):
                        if self.neo4j.add_citation(cited_paper['paperId'], paper_data['paperId']):
                            saved_citations += 1
            
            # 참고문헌들 저장            
            for reference in references:
                if reference.get('citedPaper'):
                    cited_paper = reference['citedPaper']
                    if self._save_related_paper(cited_paper):
                        if self.neo4j.add_citation(paper_data['paperId'], cited_paper['paperId']):
                            saved_references += 1
            
            logging.error(f"Citation extraction completed: {arxiv_id}, cites: {saved_citations}, refs: {saved_references}")
            
            return {
                'success': True,
                'paper_id': paper_data['paperId'],
                'citations': saved_citations,
                'references': saved_references
            }
            
        except Exception as e:
            logging.error(f"Citation extraction error for {arxiv_id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _save_related_paper(self, paper_data: Dict) -> bool:
        """관련 논문 저장"""
        try:
            paper_node = {
                'id': paper_data['paperId'],
                'title': paper_data.get('title', ''),
                'abstract': paper_data.get('abstract', ''),
                'year': paper_data.get('year', 0),
                'authors': [author.get('name', '') for author in paper_data.get('authors', [])],
                'venue': paper_data.get('venue', ''),
                'citation_count': paper_data.get('citationCount', 0),
                'arxiv_id': '',
                'problem_domain': 'unknown',
                'solution_type': 'unknown'
            }
            
            return self.neo4j.add_paper(paper_node)
            
        except Exception as e:
            logging.error(f"Save related paper error: {str(e)}")
            return False
            
    def get_citation_network(self, arxiv_id: str, depth: int = 2) -> Dict:
        """Citation 네트워크 조회"""
        try:
            # arXiv ID로 S2 paper ID 찾기
            paper_data = self.s2_client.get_paper_by_arxiv_id(arxiv_id)
            if not paper_data:
                return {'nodes': [], 'edges': []}
            
            return self.neo4j.get_citation_network(paper_data['paperId'], depth)
            
        except Exception as e:
            logging.error(f"Get citation network error: {str(e)}", exc_info=True)
            return {'nodes': [], 'edges': []}
            
    def close(self):
        """리소스 정리"""
        if self.neo4j:
            self.neo4j.close()
