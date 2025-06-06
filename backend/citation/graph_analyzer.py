import networkx as nx
from .neo4j_manager import Neo4jManager
import logging
from typing import Dict, List

class GraphAnalyzer:
    def __init__(self, neo4j_manager: Neo4jManager):
        self.neo4j = neo4j_manager
        
    def analyze_citation_patterns(self, paper_id: str) -> Dict:
        """인용 패턴 분석"""
        try:
            if not self.neo4j.driver:
                return {'error': 'Neo4j not connected'}
                
            query = """
            MATCH (center:Paper {id: $paper_id})
            OPTIONAL MATCH (center)<-[:CITES]-(citing:Paper)
            OPTIONAL MATCH (center)-[:CITES]->(cited:Paper)
            RETURN center,
                   count(DISTINCT citing) as citation_count,
                   count(DISTINCT cited) as reference_count,
                   collect(DISTINCT citing.problem_domain) as citing_domains,
                   collect(DISTINCT cited.problem_domain) as cited_domains
            """
            
            with self.neo4j.driver.session() as session:
                result = session.run(query, paper_id=paper_id)
                record = result.single()
                
                if not record:
                    return {'error': 'Paper not found'}
                
                return {
                    'citation_count': record['citation_count'],
                    'reference_count': record['reference_count'], 
                    'citing_domains': [d for d in record['citing_domains'] if d],
                    'cited_domains': [d for d in record['cited_domains'] if d],
                    'impact_score': self._calculate_impact_score(paper_id)
                }
                
        except Exception as e:
            logging.error(f"Citation pattern analysis error: {str(e)}", exc_info=True)
            return {'error': str(e)}
            
    def find_similar_papers(self, paper_id: str, limit: int = 10) -> List[Dict]:
        """유사한 논문 찾기"""
        try:
            if not self.neo4j.driver:
                return []
                
            query = """
            MATCH (center:Paper {id: $paper_id})
            MATCH (similar:Paper)
            WHERE similar.problem_domain = center.problem_domain 
            AND similar.id <> center.id
            RETURN similar.id as id, similar.title as title, 
                   similar.citation_count as citation_count,
                   similar.year as year
            ORDER BY similar.citation_count DESC
            LIMIT $limit
            """
            
            with self.neo4j.driver.session() as session:
                result = session.run(query, paper_id=paper_id, limit=limit)
                papers = []
                for record in result:
                    papers.append({
                        'id': record['id'],
                        'title': record['title'],
                        'citation_count': record['citation_count'],
                        'year': record['year']
                    })
                return papers
                
        except Exception as e:
            logging.error(f"Similar papers error: {str(e)}", exc_info=True)
            return []
            
    def _calculate_impact_score(self, paper_id: str) -> float:
        """영향력 점수 계산"""
        try:
            query = """
            MATCH (p:Paper {id: $paper_id})<-[:CITES]-(citing:Paper)
            RETURN avg(citing.citation_count) as avg_citing_impact,
                   count(citing) as citation_count
            """
            
            with self.neo4j.driver.session() as session:
                result = session.run(query, paper_id=paper_id)
                record = result.single()
                
                if record and record['citation_count'] > 0:
                    avg_impact = record['avg_citing_impact'] or 0
                    citation_count = record['citation_count']
                    return (avg_impact * 0.3 + citation_count * 0.7)
                    
                return 0.0
                
        except Exception as e:
            logging.error(f"Impact score calculation error: {str(e)}")
            return 0.0
            
    def get_citation_path(self, source_id: str, target_id: str, max_depth: int = 3) -> List[Dict]:
        """두 논문 간 인용 경로 찾기"""
        try:
            if not self.neo4j.driver:
                return []
                
            query = """
            MATCH path = (source:Paper {id: $source_id})-[:CITES*1..$max_depth]->(target:Paper {id: $target_id})
            RETURN path
            ORDER BY length(path)
            LIMIT 5
            """
            
            with self.neo4j.driver.session() as session:
                result = session.run(query, source_id=source_id, target_id=target_id, max_depth=max_depth)
                paths = []
                
                for record in result:
                    path = record['path']
                    path_nodes = []
                    for node in path.nodes:
                        path_nodes.append({
                            'id': node['id'],
                            'title': node['title']
                        })
                    paths.append({
                        'nodes': path_nodes,
                        'length': len(path_nodes) - 1
                    })
                    
                return paths
                
        except Exception as e:
            logging.error(f"Citation path error: {str(e)}", exc_info=True)
            return []
