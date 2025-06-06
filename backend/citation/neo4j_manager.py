from neo4j import GraphDatabase
import logging
from typing import Dict, List, Optional

class Neo4jManager:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self._setup_constraints()
            logging.error(f"Neo4j connected: {uri}")
        except Exception as e:
            logging.error(f"Neo4j connection failed: {str(e)}", exc_info=True)
            self.driver = None
            
    def _setup_constraints(self):
        """데이터베이스 제약조건 설정"""
        if not self.driver:
            return
            
        constraints = [
            "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
            "CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year)",
            "CREATE INDEX paper_domain IF NOT EXISTS FOR (p:Paper) ON (p.problem_domain)"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logging.error(f"Constraint creation error: {str(e)}")
                    
    def add_paper(self, paper_data: Dict) -> bool:
        """논문 노드 추가"""
        if not self.driver:
            return False
            
        query = """
        MERGE (p:Paper {id: $id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.authors = $authors,
            p.venue = $venue,
            p.citation_count = $citation_count,
            p.arxiv_id = $arxiv_id,
            p.problem_domain = $problem_domain,
            p.solution_type = $solution_type,
            p.last_updated = datetime()
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, **paper_data)
            return True
        except Exception as e:
            logging.error(f"Add paper error: {str(e)}", exc_info=True)
            return False
            
    def add_citation(self, citing_id: str, cited_id: str, context: str = "") -> bool:
        """인용 관계 추가"""
        if not self.driver:
            return False
            
        query = """
        MATCH (citing:Paper {id: $citing_id})
        MATCH (cited:Paper {id: $cited_id})
        MERGE (citing)-[r:CITES]->(cited)
        SET r.context = $context,
            r.created_date = datetime()
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, citing_id=citing_id, cited_id=cited_id, context=context)
            return True
        except Exception as e:
            logging.error(f"Add citation error: {str(e)}", exc_info=True)
            return False
            
    def get_citation_network(self, paper_id: str, depth: int = 2) -> Dict:
        """논문 주변 인용 네트워크 조회"""
        if not self.driver:
            return {'nodes': [], 'edges': []}
            
        query = """
        MATCH (center:Paper {id: $paper_id})
        OPTIONAL MATCH (center)-[:CITES*1..$depth]-(connected:Paper)
        RETURN center, collect(DISTINCT connected) as connected_papers
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, paper_id=paper_id, depth=depth)
                record = result.single()
                
                if not record:
                    return {'nodes': [], 'edges': []}
                
                nodes = []
                center = record['center']
                nodes.append({
                    'data': {
                        'id': center['id'],
                        'label': center['title'][:50] + '...',
                        'year': center.get('year', 0),
                        'citation_count': center.get('citation_count', 0),
                        'type': 'center'
                    }
                })
                
                for paper in record['connected_papers']:
                    if paper:
                        nodes.append({
                            'data': {
                                'id': paper['id'],
                                'label': paper['title'][:50] + '...',
                                'year': paper.get('year', 0),
                                'citation_count': paper.get('citation_count', 0),
                                'type': 'connected'
                            }
                        })
                
                edges = self._get_citation_edges([n['data']['id'] for n in nodes])
                
                return {'nodes': nodes, 'edges': edges}
                
        except Exception as e:
            logging.error(f"Get citation network error: {str(e)}", exc_info=True)
            return {'nodes': [], 'edges': []}
            
    def _get_citation_edges(self, paper_ids: List[str]) -> List[Dict]:
        """논문들 간 인용 관계 조회"""
        if not self.driver or not paper_ids:
            return []
            
        query = """
        MATCH (p1:Paper)-[r:CITES]->(p2:Paper)
        WHERE p1.id IN $paper_ids AND p2.id IN $paper_ids
        RETURN p1.id as source, p2.id as target
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, paper_ids=paper_ids)
                edges = []
                for record in result:
                    edges.append({
                        'data': {
                            'source': record['source'],
                            'target': record['target']
                        }
                    })
                return edges
                
        except Exception as e:
            logging.error(f"Get citation edges error: {str(e)}", exc_info=True)
            return []
            
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
