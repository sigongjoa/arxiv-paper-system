#!/usr/bin/env python3
import time
import requests
import logging
import traceback
import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.core.pipeline import Pipeline
from backend.processor import PaperProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def test_llm_server():
    """LM Studio 서버 연결 테스트"""
    try:
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if response.status_code == 200:
            logging.info("LM Studio server OK")
            return True
        else:
            logging.error(f"LM Studio server error: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"LM Studio server connection failed: {e}")
        return False

def test_paper_processing():
    """논문 처리 테스트"""
    processor = PaperProcessor()
    test_arxiv_id = "2301.00001"
    
    try:
        start_time = time.time()
        paper_result = processor.process_arxiv_paper(test_arxiv_id)
        end_time = time.time()
        
        logging.info(f"Paper processing completed in {end_time - start_time:.2f}s")
        logging.info(f"Title: {paper_result['paper']['title'][:100]}...")
        
        return paper_result
    except Exception as e:
        logging.error(f"Paper processing failed: {e}")
        logging.error(traceback.format_exc())
        raise

def test_pipeline(paper_data):
    """파이프라인 테스트"""
    pipeline = Pipeline()
    
    try:
        start_time = time.time()
        video_result = pipeline.process_paper("2301.00001", paper_data['paper'])
        end_time = time.time()
        
        logging.info(f"Pipeline completed in {end_time - start_time:.2f}s")
        for result in video_result:
            logging.info(f"Video: {result['video_path']}")
            
        return video_result
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        logging.error(traceback.format_exc())
        raise

def main():
    print("=== arXiv to Shorts 전체 테스트 (실제 논문 분석) ===\n")
    
    # 1. LM Studio 서버 확인
    print("1. LM Studio 서버 상태 확인...")
    if not test_llm_server():
        print("✗ LM Studio 서버 연결 실패")
        print("LM Studio에서 모델 로드 후 다시 시도")
        return
    print("✓ LM Studio 서버 연결 성공")
    
    # 2. 논문 처리
    print("\n2. 논문 데이터 처리...")
    try:
        paper_result = test_paper_processing()
        print("✓ 논문 처리 완료")
    except Exception:
        print("✗ 논문 처리 실패")
        return
    
    # 3. 비디오 생성 (실제 PDF 분석 포함)
    print("\n3. 비디오 생성 (실제 논문 분석)...")
    try:
        video_result = test_pipeline(paper_result)
        print("✓ 비디오 생성 완료")
        print(f"출력: {video_result[0]['video_path']}")
    except Exception:
        print("✗ 비디오 생성 실패")
        return
    
    print("\n🎉 실제 논문 분석 기반 테스트 완료!")
    print("이제 하드코딩이 아닌 실제 PDF 내용을 분석합니다.")

if __name__ == "__main__":
    main()
