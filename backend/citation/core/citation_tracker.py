import logging
import requests
import json
from typing import Dict, List, Optional
from neo4j import GraphDatabase

logging.basicConfig(level=logging.ERROR)

class CitationTracker:
    def __init__(self, neo4j_uri="bolt://localhost:7687", neo4j_user="neo4j", neo4j_password="password"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.s2_api_key = None
        
        logging.error(f"CitationTracker initialized with Neo4j: {neo4j_uri}")
        
    def create_schema(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT paper_id_unique IF NOT EXISTS ON (p:Paper) ASSERT p.id IS UNIQUE")
            session.run("CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year)")
            session.run("CREATE INDEX paper_domain IF NOT EXISTS FOR (p:Paper) ON (p.problem_domain)")
            
        logging.error("Neo4j schema created")
    
    def get_paper_data_from_s2(self, arxiv_id: str) -> Optional[Dict]:
        """Semantic Scholar API에서 논문 데이터 조회"""
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
            params = {
                'fields': 'paperId,title,abstract,year,authors,citations,references,citationCount,referenceCount,fieldsOfStudy,venue'
            }
            
            headers = {}
            if self.s2_api_key:
                headers['x-api-key'] = self.s2_api_key
                
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logging.error(f"Retrieved paper data for {arxiv_id}: {data.get('title', 'No title')}")
                return data
            else:
                logging.error(f"S2 API error for {arxiv_id}: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error getting paper data for {arxiv_id}: {str(e)}", exc_info=True)
            
        return None
    
    def store_paper_and_citations(self, arxiv_id: str) -> Dict:
        """논문과 인용 관계를 Neo4j에 저장"""
        try:
            paper_data = self.get_paper_data_from_s2(arxiv_id)
            if not paper_data:
                return {"success": False, "error": "Paper not found in Semantic Scholar"}
            
            with self.driver.session() as session:
                # 메인 논문 저장
                session.run("""
                    MERGE (p:Paper {id: $paper_id})
                    SET p.arxiv_id = $arxiv_id,
                        p.title = $title,
                        p.abstract = $abstract,
                        p.year = $year,
                        p.authors = $authors,
                        p.citation_count = $citation_count,
                        p.reference_count = $reference_count,
                        p.venue = $venue,
                        p.fields_of_study = $fields,
                        p.updated_date = datetime()
                """, 
                    paper_id=paper_data['paperId'],
                    arxiv_id=arxiv_id,
                    title=paper_data.get('title', ''),
                    abstract=paper_data.get('abstract', ''),
                    year=paper_data.get('year', 0),
                    authors=[a.get('name', '') for a in paper_data.get('authors', [])],
                    citation_count=paper_data.get('citationCount', 0),
                    reference_count=paper_data.get('referenceCount', 0),
                    venue=paper_data.get('venue', ''),
                    fields=paper_data.get('fieldsOfStudy', [])
                )
                
                # 인용하는 논문들 처리
                citations_stored = 0
                for citation in paper_data.get('citations', [])[:50]:  # 최대 50개만
                    citing_paper = citation.get('citingPaper', {})
                    if citing_paper.get('paperId'):
                        session.run("""
                            MERGE (citing:Paper {id: $citing_id})
                            SET citing.title = $citing_title,
                                citing.year = $citing_year,
                                citing.citation_count = $citing_count
                            MERGE (citing)-[:CITES]->(p:Paper {id: $cited_id})
                        """,
                            citing_id=citing_paper['paperId'],
                            citing_title=citing_paper.get('title', ''),
                            citing_year=citing_paper.get('year', 0),
                            citing_count=citing_paper.get('citationCount', 0),
                            cited_id=paper_data['paperId']
                        )
                        citations_stored += 1
                
                # 참고문헌들 처리
                references_stored = 0
                for reference in paper_data.get('references', [])[:50]:  # 최대 50개만
                    cited_paper = reference.get('citedPaper', {})
                    if cited_paper.get('paperId'):
                        session.run("""
                            MERGE (cited:Paper {id: $cited_id})
                            SET cited.title = $cited_title,
                                cited.year = $cited_year,
                                cited.citation_count = $cited_count
                            MERGE (p:Paper {id: $citing_id})-[:CITES]->(cited)
                        """,
                            cited_id=cited_paper['paperId'],
                            cited_title=cited_paper.get('title', ''),
                            cited_year=cited_paper.get('year', 0),
                            cited_count=cited_paper.get('citationCount', 0),
                            citing_id=paper_data['paperId']
                        )
                        references_stored += 1
                
                logging.error(f"Stored paper {arxiv_id}: {citations_stored} citations, {references_stored} references")
                
                return {
                    "success": True,
                    "paper_id": paper_data['paperId'],
                    "citations_stored": citations_stored,
                    "references_stored": references_stored
                }
                
        except Exception as e:
            logging.error(f"Error storing citations for {arxiv_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def get_citation_network(self, arxiv_id: str, depth: int = 2) -> Dict:
        """Citation network 데이터 조회"""
        try:
            paper_data = self.get_paper_data_from_s2(arxiv_id)
            if not paper_data:
                return {"nodes": [], "edges": []}
            
            paper_id = paper_data['paperId']
            
            with self.driver.session() as session:
                # 지정된 깊이까지 citation network 조회
                result = session.run("""
                    MATCH (center:Paper {id: $paper_id})
                    OPTIONAL MATCH path1 = (center)-[:CITES*1..$depth]-(connected1:Paper)
                    OPTIONAL MATCH path2 = (connected2:Paper)-[:CITES*1..$depth]-(center)
                    WITH center, 
                         collect(DISTINCT connected1) as cited_papers,
                         collect(DISTINCT connected2) as citing_papers
                    RETURN center, cited_papers, citing_papers
                """, paper_id=paper_id, depth=depth)
                
                record = result.single()
                if not record:
                    return {"nodes": [], "edges": []}
                
                center = record['center']
                cited_papers = record['cited_papers'] or []
                citing_papers = record['citing_papers'] or []
                
                # 노드 생성
                nodes = []
                all_papers = [center] + cited_papers + citing_papers
                
                for paper in all_papers:
                    if paper:
                        nodes.append({
                            'data': {
                                'id': paper['id'],
                                'label': paper.get('title', 'Unknown')[:50] + ('...' if len(paper.get('title', '')) > 50 else ''),
                                'type': 'center' if paper['id'] == paper_id else 'connected',
                                'year': paper.get('year', 0),
                                'citation_count': paper.get('citation_count', 0)
                            }
                        })
                
                # 엣지 조회
                edge_result = session.run("""
                    MATCH (center:Paper {id: $paper_id})
                    MATCH (p1:Paper)-[r:CITES]->(p2:Paper)
                    WHERE (p1.id = $paper_id OR p2.id = $paper_id OR 
                           (p1)-[:CITES*1..$depth]-(center) OR 
                           (p2)-[:CITES*1..$depth]-(center))
                    RETURN DISTINCT p1.id as source, p2.id as target
                    LIMIT 200
                """, paper_id=paper_id, depth=depth)
                
                edges = []
                for edge_record in edge_result:
                    edges.append({
                        'data': {
                            'id': f"{edge_record['source']}-{edge_record['target']}",
                            'source': edge_record['source'],
                            'target': edge_record['target']
                        }
                    })
                
                logging.error(f"Citation network for {arxiv_id}: {len(nodes)} nodes, {len(edges)} edges")
                
                return {"nodes": nodes, "edges": edges}
                
        except Exception as e:
            logging.error(f"Error getting citation network for {arxiv_id}: {str(e)}", exc_info=True)
            return {"nodes": [], "edges": []}
    
    def analyze_citation_patterns(self, arxiv_id: str) -> Dict:
        """인용 패턴 분석"""
        try:
            paper_data = self.get_paper_data_from_s2(arxiv_id)
            if not paper_data:
                return {"error": "Paper not found"}
            
            paper_id = paper_data['paperId']
            
            with self.driver.session() as session:
                # 기본 통계
                stats_result = session.run("""
                    MATCH (p:Paper {id: $paper_id})
                    OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
                    OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
                    RETURN p,
                           count(DISTINCT citing) as citing_count,
                           count(DISTINCT cited) as cited_count
                """, paper_id=paper_id)
                
                stats = stats_result.single()
                
                # 인용 도메인 분석
                domain_result = session.run("""
                    MATCH (p:Paper {id: $paper_id})
                    OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
                    OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
                    RETURN collect(DISTINCT citing.fields_of_study) as citing_domains,
                           collect(DISTINCT cited.fields_of_study) as cited_domains
                """, paper_id=paper_id)
                
                domains = domain_result.single()
                
                # 영향력 점수 계산 (간단한 버전)
                impact_score = (stats['citing_count'] or 0) * 0.7 + (stats['cited_count'] or 0) * 0.3
                
                analysis = {
                    "citation_count": stats['citing_count'] or 0,
                    "reference_count": stats['cited_count'] or 0,
                    "impact_score": impact_score,
                    "citing_domains": [domain for domain_list in (domains['citing_domains'] or []) for domain in (domain_list or [])],
                    "cited_domains": [domain for domain_list in (domains['cited_domains'] or []) for domain in (domain_list or [])]
                }
                
                logging.error(f"Citation analysis for {arxiv_id}: impact_score={impact_score}")
                
                return {"analysis": analysis}
                
        except Exception as e:
            logging.error(f"Error analyzing citations for {arxiv_id}: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def find_similar_papers(self, arxiv_id: str, limit: int = 5) -> List[Dict]:
        """유사한 논문 찾기"""
        try:
            paper_data = self.get_paper_data_from_s2(arxiv_id)
            if not paper_data:
                return []
            
            paper_id = paper_data['paperId']
            
            with self.driver.session() as session:
                # 공통 인용 논문을 많이 가진 논문들 찾기
                result = session.run("""
                    MATCH (target:Paper {id: $paper_id})-[:CITES]->(common:Paper)<-[:CITES]-(similar:Paper)
                    WHERE target <> similar
                    WITH similar, count(common) as common_citations
                    ORDER BY common_citations DESC
                    LIMIT $limit
                    RETURN similar.title as title, 
                           similar.year as year,
                           similar.citation_count as citation_count,
                           common_citations
                """, paper_id=paper_id, limit=limit)
                
                similar_papers = []
                for record in result:
                    similar_papers.append({
                        "title": record['title'] or 'Unknown',
                        "year": record['year'] or 0,
                        "citation_count": record['citation_count'] or 0,
                        "common_citations": record['common_citations']
                    })
                
                logging.error(f"Found {len(similar_papers)} similar papers for {arxiv_id}")
                
                return similar_papers
                
        except Exception as e:
            logging.error(f"Error finding similar papers for {arxiv_id}: {str(e)}", exc_info=True)
            return []
    
    def close(self):
        if self.driver:
            self.driver.close()
