import asyncio
import os
import sys
import json
import logging
import pytest

# Adjust the path to include the project root for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 로깅 설정 추가
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Explicitly set logger levels for relevant modules
logging.getLogger('arxiv_paper_system.backend.core.recommendation_engine').setLevel(logging.DEBUG)
logging.getLogger('arxiv_paper_system.backend.agents.lm_studio_client').setLevel(logging.DEBUG)
logging.getLogger('arxiv_paper_system.backend.agents.research_discovery_agent').setLevel(logging.DEBUG)

# These imports will now work because of sys.path adjustment
from arxiv_paper_system.backend.core.recommendation_engine import ModernRecommendationEngine
from arxiv_paper_system.backend.core.database import create_tables, Base, engine
from arxiv_paper_system.backend.agents.lm_studio_client import LMStudioClient, LMStudioConfig

@pytest.mark.asyncio
async def test_lm_studio_response_format():
    """
    LM Studio 응답 형식 문제가 해결되었는지 확인하는 Pytest 테스트.
    """
    test_paper_id = "2506.04226v1" # Use a known paper ID for testing
    logger.info(f"테스트 시작: 논문 ID {test_paper_id}에 대한 추천 생성 (LM Studio 응답 형식 확인)")

    # LM Studio 연결 확인
    lm_config = LMStudioConfig()
    lm_client = LMStudioClient(config=lm_config)
    if not lm_client.check_connection():
        pytest.fail("LM Studio 서버에 연결할 수 없습니다. LM Studio가 실행 중인지 확인하고 포트 설정을 확인하세요.")
    else:
        logger.info("LM Studio 서버에 성공적으로 연결되었습니다.")

    # 추천 엔진 인스턴스 생성 및 초기화
    backend_dir = os.path.join(project_root, 'arxiv-paper-system', 'backend')
    db_path = os.path.join(backend_dir, 'arxiv_papers.db')
    model_cache_dir = os.path.join(backend_dir, 'models')

    rec_engine = ModernRecommendationEngine(db_path=db_path, model_cache_dir=model_cache_dir)
    rec_engine.initialize_system(force_rebuild=True) # 캐시를 사용하지 않고 항상 재구축

    logger.info(f"로드된 논문 ID 개수: {len(rec_engine.paper_ids)}")
    logger.info(f"로드된 논문 ID 목록 미리보기: {rec_engine.paper_ids[:5]}...")
    assert test_paper_id in rec_engine.paper_ids, f"테스트 논문 ID ({test_paper_id})가 로드된 논문 목록에 없습니다."

    # 추천 생성
    recommendations = await rec_engine.get_recommendations_for_paper(test_paper_id, recommendation_type='hybrid', n_recommendations=3)

    assert not recommendations.get('error'), f"오류 발생: {recommendations.get('error')}"
    assert recommendations.get('recommendations'), "추천을 생성할 수 없습니다."

    logger.info("\n--- 추천 결과 ---")
    for i, rec in enumerate(recommendations['recommendations']):
        logger.info(f"추천 {i+1}:")
        logger.info(f"  논문 ID: {rec.get('paper_id')}")
        logger.info(f"  제목: {rec.get('title')[:70]}...")
        logger.info(f"  하이브리드 점수: {rec.get('hybrid_score'):.4f}")
        logger.info(f"  메서드: {rec.get('methods')}")
        logger.info(f"  추천 이유: {rec.get('reason', '없음')}") # LM Studio가 생성하는 reason 필드 확인
        assert rec.get('reason') is not None and len(rec.get('reason')) > 0, "LM Studio 응답의 'reason' 필드가 비어 있습니다."
        logger.info("------------------")

    logger.info("\n테스트 완료.")

if __name__ == "__main__":
    pytest.main([__file__]) 