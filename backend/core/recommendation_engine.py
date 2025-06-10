import os
import json
import sqlite3
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime, timedelta
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger(__name__)

class ModernRecommendationEngine:
    def __init__(self, db_path: str = None, model_cache_dir: str = None):
        self.db_path = db_path or "papers.db"
        self.model_cache_dir = model_cache_dir or "models"
        
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
        logger.info("SPECTER2 모델 로딩 중...")
        try:
            # SPECTER2: 논문 특화 임베딩 모델
            self.specter_model = SentenceTransformer('allenai/specter2')
            logger.info("✅ SPECTER2 모델 로드 성공")
        except Exception as e:
            logger.error(f"SPECTER2 로드 실패: {e}")
            # SciBERT로 폴백
            try:
                self.specter_model = SentenceTransformer('allenai/scibert_scivocab_uncased')
                logger.info("✅ SciBERT 모델 로드 성공 (폴백)")
            except Exception as e2:
                logger.error(f"SciBERT도 실패: {e2}")
                # all-MiniLM으로 최종 폴백
                self.specter_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ MiniLM 모델 로드 성공 (최종 폴백)")
        
        # 데이터 저장소
        self.paper_embeddings = None
        self.paper_ids = []
        self.papers_df = None
        self.faiss_index = None
        self.paper_clusters = None
        self.cluster_model = None
        
        # 사용자 프로필 시뮬레이션을 위한 데이터
        self.user_preferences = {}
        self.paper_popularity = {}
        
        logger.info("🎯 현대적 추천 엔진 초기화 완료")

    def load_papers_from_db(self, limit: int = None) -> pd.DataFrame:
        """데이터베이스에서 논문 데이터 로드"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT paper_id, title, abstract, authors, categories, 
                   published_date, updated_date
            FROM papers 
            WHERE abstract IS NOT NULL AND title IS NOT NULL
            ORDER BY published_date DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"📊 데이터베이스에서 {len(df)}개 논문 로드")
            return df
            
        except Exception as e:
            logger.error(f"논문 데이터 로드 실패: {e}")
            raise

    def generate_paper_embeddings(self, papers_df: pd.DataFrame) -> np.ndarray:
        """SPECTER2로 고품질 논문 임베딩 생성"""
        logger.info("🧠 SPECTER2 임베딩 생성 시작...")
        
        # 논문 텍스트 준비 (제목 + 초록)
        paper_texts = []
        for _, row in papers_df.iterrows():
            # SPECTER2에 최적화된 형식
            text = f"Title: {row['title']}\nAbstract: {row['abstract']}"
            paper_texts.append(text)
        
        # SPECTER2 임베딩 생성
        embeddings = self.specter_model.encode(
            paper_texts,
            batch_size=8,  # 메모리 최적화
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # 코사인 유사도 최적화
        )
        
        self.paper_embeddings = embeddings
        self.paper_ids = papers_df['paper_id'].tolist()
        
        logger.info(f"✅ 임베딩 생성 완료: {embeddings.shape}")
        return embeddings

    def build_faiss_index(self, embeddings: np.ndarray):
        """Faiss로 고성능 벡터 검색 인덱스 구축"""
        logger.info("⚡ Faiss 인덱스 구축 중...")
        
        # Inner Product 인덱스 (정규화된 벡터에서 코사인 유사도와 동일)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        
        # GPU 사용 가능하면 GPU 인덱스 사용
        try:
            if faiss.get_num_gpus() > 0:
                index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
                logger.info("🚀 GPU 가속 인덱스 사용")
        except:
            logger.info("💻 CPU 인덱스 사용")
        
        index.add(embeddings.astype('float32'))
        
        self.faiss_index = index
        logger.info(f"✅ Faiss 인덱스 구축 완료: {index.ntotal}개 벡터")

    def create_paper_clusters(self, embeddings: np.ndarray, n_clusters: int = 50):
        """논문을 주제별로 클러스터링"""
        effective_n_clusters = max(1, min(n_clusters, len(embeddings) // 2))
        logger.info(f"🎯 논문 클러스터링 시작 (k={effective_n_clusters})...")
        
        # K-means 클러스터링
        self.cluster_model = KMeans(n_clusters=effective_n_clusters, random_state=42, n_init=10)
        cluster_labels = self.cluster_model.fit_predict(embeddings)
        
        self.paper_clusters = cluster_labels
        
        # 클러스터별 인기도 계산
        self._calculate_cluster_popularity()
        
        logger.info(f"✅ 클러스터링 완료: {effective_n_clusters}개 주제 클러스터")

    def _calculate_cluster_popularity(self):
        """클러스터별 인기도 계산 (최신성 + 다양성 기반)"""
        cluster_popularity = {}
        
        for cluster_id in np.unique(self.paper_clusters):
            cluster_papers = [i for i, c in enumerate(self.paper_clusters) if c == cluster_id]
            
            # 최신성 점수 계산
            recency_scores = []
            for paper_idx in cluster_papers:
                try:
                    paper_date = datetime.fromisoformat(
                        self.papers_df.iloc[paper_idx]['published_date'].replace('Z', '+00:00')
                    )
                    days_old = (datetime.now() - paper_date.replace(tzinfo=None)).days
                    recency_score = max(0.1, 1.0 - (days_old / 365))  # 1년으로 정규화
                    recency_scores.append(recency_score)
                except:
                    recency_scores.append(0.5)
            
            # 클러스터 인기도 = 평균 최신성 + 논문 수 가중치
            avg_recency = np.mean(recency_scores)
            size_weight = min(1.0, len(cluster_papers) / 10)  # 10개 이상이면 최대 가중치
            
            cluster_popularity[cluster_id] = avg_recency * 0.7 + size_weight * 0.3
        
        self.cluster_popularity = cluster_popularity

    def get_content_based_recommendations(self, paper_id: str, n_recommendations: int = 10) -> List[Dict]:
        """SPECTER2 기반 의미적 유사성 추천"""
        try:
            if paper_id not in self.paper_ids:
                logger.warning(f"❌ 논문 ID {paper_id}를 찾을 수 없음")
                return []
            
            paper_idx = self.paper_ids.index(paper_id)
            query_embedding = self.paper_embeddings[paper_idx:paper_idx+1]
            
            # Faiss로 유사 논문 검색
            scores, indices = self.faiss_index.search(
                query_embedding.astype('float32'),
                n_recommendations + 1  # 자기 자신 제외
            )
            
            recommendations = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx != paper_idx:  # 자기 자신 제외
                    recommendations.append({
                        'paper_id': self.paper_ids[idx],
                        'similarity_score': float(score),
                        'rank': len(recommendations) + 1,
                        'method': 'semantic_similarity'
                    })
                
                if len(recommendations) >= n_recommendations:
                    break
            
            logger.info(f"🎯 의미적 유사성 추천 {len(recommendations)}개 생성")
            return recommendations
            
        except Exception as e:
            logger.error(f"콘텐츠 기반 추천 실패: {e}")
            return []

    def get_cluster_based_recommendations(self, paper_id: str, n_recommendations: int = 10) -> List[Dict]:
        """클러스터 기반 추천 (주제별 협업 필터링)"""
        try:
            if paper_id not in self.paper_ids or self.paper_clusters is None:
                return []
            
            paper_idx = self.paper_ids.index(paper_id)
            paper_cluster = self.paper_clusters[paper_idx]
            
            # 같은 클러스터의 논문들 찾기
            cluster_papers = []
            for i, cluster_id in enumerate(self.paper_clusters):
                if cluster_id == paper_cluster and i != paper_idx:
                    # 시간 가중치 적용
                    try:
                        paper_date = datetime.fromisoformat(
                            self.papers_df.iloc[i]['published_date'].replace('Z', '+00:00')
                        )
                        days_old = (datetime.now() - paper_date.replace(tzinfo=None)).days
                        time_weight = max(0.1, 1.0 - (days_old / 730))
                        
                        # 클러스터 인기도와 시간 가중치 결합
                        cluster_pop = self.cluster_popularity.get(paper_cluster, 0.5)
                        final_score = time_weight * 0.6 + cluster_pop * 0.4
                        
                        cluster_papers.append({
                            'paper_id': self.paper_ids[i],
                            'cluster_score': final_score,
                            'cluster_id': int(paper_cluster),
                            'time_weight': time_weight
                        })
                    except:
                        continue
            
            # 점수 순으로 정렬
            cluster_papers.sort(key=lambda x: x['cluster_score'], reverse=True)
            
            recommendations = []
            for i, rec in enumerate(cluster_papers[:n_recommendations]):
                rec['rank'] = i + 1
                rec['method'] = 'cluster_based'
                recommendations.append(rec)
            
            logger.info(f"🎯 클러스터 기반 추천 {len(recommendations)}개 생성")
            return recommendations
            
        except Exception as e:
            logger.error(f"클러스터 기반 추천 실패: {e}")
            return []

    def get_hybrid_recommendations(self, paper_id: str, n_recommendations: int = 10) -> List[Dict]:
        """고급 하이브리드 추천 (의미적 + 클러스터 + 최신성)"""
        try:
            # 각 방법별 추천 생성
            content_recs = self.get_content_based_recommendations(paper_id, n_recommendations * 2)
            cluster_recs = self.get_cluster_based_recommendations(paper_id, n_recommendations * 2)
            
            # 점수 통합 (더 정교한 가중치)
            paper_scores = {}
            
            # 의미적 유사성 점수 (가중치 0.6)
            for rec in content_recs:
                paper_id_rec = rec['paper_id']
                score = rec['similarity_score'] * 0.6
                paper_scores[paper_id_rec] = {
                    'total_score': score,
                    'semantic_score': rec['similarity_score'],
                    'cluster_score': 0,
                    'methods': ['semantic']
                }
            
            # 클러스터 점수 (가중치 0.4)
            max_cluster_score = max([r['cluster_score'] for r in cluster_recs]) if cluster_recs else 1
            for rec in cluster_recs:
                paper_id_rec = rec['paper_id']
                normalized_score = rec['cluster_score'] / max_cluster_score
                score = normalized_score * 0.4
                
                if paper_id_rec in paper_scores:
                    paper_scores[paper_id_rec]['total_score'] += score
                    paper_scores[paper_id_rec]['cluster_score'] = rec['cluster_score']
                    paper_scores[paper_id_rec]['methods'].append('cluster')
                else:
                    paper_scores[paper_id_rec] = {
                        'total_score': score,
                        'semantic_score': 0,
                        'cluster_score': rec['cluster_score'],
                        'methods': ['cluster']
                    }
            
            # 상위 추천 선택
            sorted_papers = sorted(paper_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
            
            hybrid_recs = []
            for i, (paper_id_rec, scores) in enumerate(sorted_papers[:n_recommendations]):
                hybrid_recs.append({
                    'paper_id': paper_id_rec,
                    'hybrid_score': float(scores['total_score']),
                    'semantic_score': float(scores['semantic_score']),
                    'cluster_score': float(scores['cluster_score']),
                    'methods': scores['methods'],
                    'rank': i + 1,
                    'method': 'hybrid'
                })
            
            logger.info(f"🚀 하이브리드 추천 {len(hybrid_recs)}개 생성")
            return hybrid_recs
            
        except Exception as e:
            logger.error(f"하이브리드 추천 실패: {e}")
            return self.get_content_based_recommendations(paper_id, n_recommendations)

    def get_paper_details(self, paper_ids: List[str]) -> List[Dict]:
        """논문 상세 정보 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            placeholders = ','.join(['?' for _ in paper_ids])
            query = f"""
            SELECT paper_id, title, abstract, authors, categories, 
                   published_date, updated_date
            FROM papers 
            WHERE paper_id IN ({placeholders})
            """
            
            df = pd.read_sql_query(query, conn, params=paper_ids)
            conn.close()
            
            papers = []
            for _, row in df.iterrows():
                # JSON 파싱 처리
                try:
                    authors = json.loads(row['authors']) if isinstance(row['authors'], str) else row['authors']
                    categories = json.loads(row['categories']) if isinstance(row['categories'], str) else row['categories']
                except:
                    authors = row['authors'].split(', ') if row['authors'] else []
                    categories = row['categories'].split(', ') if row['categories'] else []
                
                papers.append({
                    'paper_id': row['paper_id'],
                    'title': row['title'],
                    'abstract': row['abstract'][:300] + '...' if len(row['abstract']) > 300 else row['abstract'],
                    'authors': authors,
                    'categories': categories,
                    'published_date': row['published_date'],
                    'pdf_url': f"https://arxiv.org/pdf/{row['paper_id']}.pdf"
                })
            
            return papers
            
        except Exception as e:
            logger.error(f"논문 상세 정보 조회 실패: {e}")
            return []

    def initialize_system(self, force_rebuild: bool = False):
        """추천 시스템 초기화"""
        logger.info("🚀 현대적 추천 시스템 초기화 시작...")
        
        # 캐시 파일 경로
        embeddings_cache = os.path.join(self.model_cache_dir, 'specter2_embeddings.npy')
        index_cache = os.path.join(self.model_cache_dir, 'faiss_index.bin')
        clusters_cache = os.path.join(self.model_cache_dir, 'paper_clusters.npy')
        metadata_cache = os.path.join(self.model_cache_dir, 'metadata.json')
        
        if not force_rebuild and os.path.exists(embeddings_cache) and os.path.exists(metadata_cache):
            logger.info("💾 캐시에서 모델 로드 중...")
            try:
                # 임베딩 로드
                self.paper_embeddings = np.load(embeddings_cache)
                
                # 메타데이터 로드
                with open(metadata_cache, 'r') as f:
                    metadata = json.load(f)
                    self.paper_ids = metadata['paper_ids']
                
                # Faiss 인덱스 로드
                if os.path.exists(index_cache):
                    self.faiss_index = faiss.read_index(index_cache)
                else:
                    self.build_faiss_index(self.paper_embeddings)
                
                # 클러스터 로드
                if os.path.exists(clusters_cache):
                    self.paper_clusters = np.load(clusters_cache)
                    self._calculate_cluster_popularity()
                
                # papers_df 로드
                self.papers_df = self.load_papers_from_db()
                
                logger.info("✅ 캐시에서 모델 로드 완료")
                return
                
            except Exception as e:
                logger.warning(f"⚠️ 캐시 로드 실패, 새로 구축: {e}")
        
        # 새로 구축
        papers_df = self.load_papers_from_db(limit=3000)  # 성능과 품질의 균형
        
        if papers_df.empty:
            logger.error("❌ 논문 데이터가 없습니다")
            return
        
        self.papers_df = papers_df
        
        # SPECTER2 임베딩 생성
        embeddings = self.generate_paper_embeddings(papers_df)
        
        # Faiss 인덱스 구축
        self.build_faiss_index(embeddings)
        
        # 클러스터링 수행
        self.create_paper_clusters(embeddings)
        
        # 캐시 저장
        try:
            np.save(embeddings_cache, self.paper_embeddings)
            faiss.write_index(self.faiss_index, index_cache)
            np.save(clusters_cache, self.paper_clusters)
            
            metadata = {
                'paper_ids': self.paper_ids,
                'created_at': datetime.now().isoformat(),
                'paper_count': len(self.paper_ids),
                'model_type': 'SPECTER2'
            }
            
            with open(metadata_cache, 'w') as f:
                json.dump(metadata, f)
            
            logger.info("💾 모델 캐시 저장 완료")
            
        except Exception as e:
            logger.warning(f"⚠️ 캐시 저장 실패: {e}")
        
        logger.info("🎉 현대적 추천 시스템 초기화 완료!")

    def get_recommendations_for_paper(self, paper_id: str, recommendation_type: str = 'hybrid', n_recommendations: int = 10) -> Dict:
        """논문에 대한 추천 생성"""
        if self.paper_embeddings is None:
            logger.error("❌ 추천 시스템이 초기화되지 않았습니다")
            return {'error': '추천 시스템이 초기화되지 않았습니다'}
        
        if recommendation_type == 'content':
            recommendations = self.get_content_based_recommendations(paper_id, n_recommendations)
        elif recommendation_type == 'hybrid':
            recommendations = self.get_hybrid_recommendations(paper_id, n_recommendations)
        else:
            recommendations = self.get_content_based_recommendations(paper_id, n_recommendations)
        
        if not recommendations:
            return {'error': '추천을 생성할 수 없습니다'}
        
        # 추천된 논문들의 상세 정보 조회
        recommended_paper_ids = [rec['paper_id'] for rec in recommendations]
        paper_details = self.get_paper_details(recommended_paper_ids)
        
        # 추천 점수와 논문 정보 결합
        result = []
        for rec in recommendations:
            paper_detail = next((p for p in paper_details if p['paper_id'] == rec['paper_id']), None)
            if paper_detail:
                paper_detail.update(rec)
                result.append(paper_detail)
        
        return {
            'recommendations': result,
            'total_count': len(result),
            'recommendation_type': recommendation_type,
            'source_paper_id': paper_id,
            'model_info': {
                'embedding_model': 'SPECTER2',
                'vector_search': 'Faiss',
                'clustering': 'K-means'
            }
        }

# 전역 추천 엔진 인스턴스
recommendation_engine = None

def get_recommendation_engine():
    """추천 엔진 싱글톤 인스턴스 반환"""
    global recommendation_engine
    if recommendation_engine is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'papers.db')
        model_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        recommendation_engine = ModernRecommendationEngine(db_path, model_cache_dir)
    return recommendation_engine
