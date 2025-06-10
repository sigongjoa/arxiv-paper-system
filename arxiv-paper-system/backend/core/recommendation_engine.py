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
            logger.error(f"콘텐츠 기반 추천 생성 실패: {e}", exc_info=True)
            return []

    def get_cluster_based_recommendations(self, paper_id: str, n_recommendations: int = 10) -> List[Dict]:
        """클러스터 기반 추천 (주제별 인기도 반영)"""
        try:
            if paper_id not in self.paper_ids or self.paper_clusters is None or self.cluster_popularity is None:
                return []

            paper_idx = self.paper_ids.index(paper_id)
            target_cluster_id = self.paper_clusters[paper_idx]
            
            # 해당 클러스터의 논문들
            cluster_papers_indices = [i for i, c in enumerate(self.paper_clusters) if c == target_cluster_id]
            
            # 클러스터 인기도 점수 사용 (미리 계산된 값)
            cluster_score = self.cluster_popularity.get(target_cluster_id, 0.0)
            
            # 현재 논문과 같은 클러스터 내의 다른 논문들을 가져옴
            # 여기서는 단순히 무작위로 선택하거나 최신순으로 정렬하여 반환할 수 있음
            # 실제 시스템에서는 클러스터 내에서도 더 정교한 랭킹이 필요
            
            # 간단하게 클러스터 내에서 무작위로 n_recommendations 만큼 선택
            # 자기 자신 제외
            candidates = [idx for idx in cluster_papers_indices if idx != paper_idx]
            if len(candidates) > n_recommendations:
                selected_indices = np.random.choice(candidates, n_recommendations, replace=False)
            else:
                selected_indices = candidates
            
            recommendations = []
            for idx in selected_indices:
                recommendations.append({
                    'paper_id': self.paper_ids[idx],
                    'cluster_score': float(cluster_score),
                    'method': 'cluster_based'
                })
            
            logger.info(f"🎯 클러스터 기반 추천 {len(recommendations)}개 생성")
            return recommendations

        except Exception as e:
            logger.error(f"클러스터 기반 추천 생성 실패: {e}", exc_info=True)
            return []

    def get_hybrid_recommendations(self, paper_id: str, n_recommendations: int = 10) -> List[Dict]:
        """하이브리드 추천 (콘텐츠 기반 + 클러스터 기반)"""
        try:
            content_recs = self.get_content_based_recommendations(paper_id, n_recommendations)
            cluster_recs = self.get_cluster_based_recommendations(paper_id, n_recommendations)
            
            combined_recs = {rec['paper_id']: rec for rec in content_recs}
            for rec in cluster_recs:
                if rec['paper_id'] in combined_recs:
                    # 점수 병합 또는 가중치 부여
                    combined_recs[rec['paper_id']]['hybrid_score'] = (
                        combined_recs[rec['paper_id']].get('similarity_score', 0) * 0.7 +
                        rec.get('cluster_score', 0) * 0.3
                    )
                    combined_recs[rec['paper_id']]['methods'] = 'hybrid'
                else:
                    rec['hybrid_score'] = rec.get('cluster_score', 0)
                    rec['methods'] = 'cluster_based'
                    combined_recs[rec['paper_id']] = rec
            
            # 최종 점수로 정렬 및 상위 N개 선택
            final_recommendations = sorted(
                combined_recs.values(),
                key=lambda x: x.get('hybrid_score', 0), # hybrid_score가 없으면 0으로 간주
                reverse=True
            )[:n_recommendations]
            
            # 제목 정보 추가 (성능 최적화를 위해 여기서 한 번에 조회)
            paper_ids_to_fetch = [rec['paper_id'] for rec in final_recommendations]
            paper_details = self.get_paper_details(paper_ids_to_fetch)
            paper_details_map = {p['paper_id']: p for p in paper_details}

            for rec in final_recommendations:
                detail = paper_details_map.get(rec['paper_id'])
                if detail:
                    rec['title'] = detail.get('title')
                    rec['abstract'] = detail.get('abstract')
                    rec['authors'] = detail.get('authors')
                    rec['categories'] = detail.get('categories')
                    rec['published_date'] = detail.get('published_date')
            
            logger.info(f"🎯 하이브리드 추천 {len(final_recommendations)}개 생성")
            return final_recommendations

        except Exception as e:
            logger.error(f"하이브리드 추천 생성 실패: {e}", exc_info=True)
            return []

    def get_paper_details(self, paper_ids: List[str]) -> List[Dict]:
        """주어진 논문 ID 목록에 대한 상세 정보 검색"""
        if not paper_ids:
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            placeholders = ', '.join(['?' for _ in paper_ids])
            query = f"SELECT paper_id, title, abstract, authors, categories, published_date, updated_date FROM papers WHERE paper_id IN ({placeholders})"
            
            cursor = conn.execute(query, paper_ids)
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            
            # JSON 필드 파싱
            for row in results:
                if 'authors' in row and row['authors']:
                    row['authors'] = json.loads(row['authors'])
                if 'categories' in row and row['categories']:
                    row['categories'] = json.loads(row['categories'])
            
            logger.info(f"논문 상세 정보 {len(results)}개 조회")
            return results
            
        except Exception as e:
            logger.error(f"논문 상세 정보 조회 실패: {e}", exc_info=True)
            return []

    def initialize_system(self, force_rebuild: bool = False):
        """추천 시스템 초기화: 논문 로드, 임베딩 생성, Faiss 인덱스 구축, 클러스터링"""
        logger.info("🚀 추천 시스템 초기화 시작...")
        
        # 데이터베이스 파일 존재 여부 확인
        if not os.path.exists(self.db_path):
            logger.error(f"❌ 데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
            raise FileNotFoundError(f"데이터베이스 파일이 없습니다: {self.db_path}")

        # 임베딩 및 인덱스 파일 경로 설정
        embeddings_path = os.path.join(self.model_cache_dir, "paper_embeddings.npy")
        faiss_index_path = os.path.join(self.model_cache_dir, "faiss_index.bin")
        paper_ids_path = os.path.join(self.model_cache_dir, "paper_ids.json")
        clusters_path = os.path.join(self.model_cache_dir, "paper_clusters.npy")
        cluster_model_path = os.path.join(self.model_cache_dir, "cluster_model.pkl")
        
        # 캐시된 데이터 로드 시도
        if not force_rebuild and \
           os.path.exists(embeddings_path) and \
           os.path.exists(faiss_index_path) and \
           os.path.exists(paper_ids_path) and \
           os.path.exists(clusters_path) and \
           os.path.exists(cluster_model_path):
            try:
                self.paper_embeddings = np.load(embeddings_path)
                self.faiss_index = faiss.read_index(faiss_index_path)
                with open(paper_ids_path, 'r') as f:
                    self.paper_ids = json.load(f)
                self.paper_clusters = np.load(clusters_path)
                with open(cluster_model_path, 'rb') as f:
                    import pickle
                    self.cluster_model = pickle.load(f) # scikit-learn 모델 로드
                
                self.papers_df = self.load_papers_from_db() # DataFrame은 항상 DB에서 로드
                self._calculate_cluster_popularity() # 클러스터 인기도 다시 계산 (최신 데이터 반영)
                
                logger.info("✅ 캐시된 임베딩, 인덱스 및 클러스터 로드 성공")
                return
            except Exception as e:
                logger.warning(f"캐시 로드 실패 ({e}), 시스템 재구축 시작...")
        
        # 데이터 로드 및 처리
        self.papers_df = self.load_papers_from_db()
        if self.papers_df.empty:
            logger.warning("데이터베이스에 논문이 없습니다. 추천 시스템을 초기화할 수 없습니다.")
            return
            
        embeddings = self.generate_paper_embeddings(self.papers_df)
        self.build_faiss_index(embeddings)
        self.create_paper_clusters(embeddings) # 클러스터링을 먼저 수행
        
        # 캐시 저장
        try:
            np.save(embeddings_path, embeddings)
            faiss.write_index(self.faiss_index, faiss_index_path)
            with open(paper_ids_path, 'w') as f:
                json.dump(self.paper_ids, f)
            np.save(clusters_path, self.paper_clusters)
            with open(cluster_model_path, 'wb') as f:
                import pickle
                pickle.dump(self.cluster_model, f) # scikit-learn 모델 저장
            logger.info("✅ 임베딩, 인덱스 및 클러스터 캐시 저장 성공")
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

        logger.info("✅ 추천 시스템 초기화 완료")

    def get_recommendations_for_paper(self, paper_id: str, recommendation_type: str = 'hybrid', n_recommendations: int = 10) -> Dict:
        """주어진 논문 ID에 대한 추천을 생성"""
        if paper_id not in self.paper_ids:
            return {"error": f"논문 ID '{paper_id}'를 찾을 수 없습니다.", "recommendations": []}

        if recommendation_type == 'content_based':
            recs = self.get_content_based_recommendations(paper_id, n_recommendations)
        elif recommendation_type == 'cluster_based':
            recs = self.get_cluster_based_recommendations(paper_id, n_recommendations)
        elif recommendation_type == 'hybrid':
            recs = self.get_hybrid_recommendations(paper_id, n_recommendations)
        else:
            return {"error": "유효하지 않은 추천 유형입니다.", "recommendations": []}
        
        if not recs:
            return {"error": "추천을 생성할 수 없습니다.", "recommendations": []}
            
        return {"recommendations": recs}

def get_recommendation_engine():
    """싱글톤 추천 엔진 인스턴스 반환"""
    global _recommendation_engine_instance
    if _recommendation_engine_instance is None:
        db_path = os.path.join(os.path.dirname(__file__), 'arxiv_papers.db')
        model_cache_dir = os.path.join(os.path.dirname(__file__), 'models')
        _recommendation_engine_instance = ModernRecommendationEngine(db_path=db_path, model_cache_dir=model_cache_dir)
        _recommendation_engine_instance.initialize_system()
    return _recommendation_engine_instance

_recommendation_engine_instance = None 