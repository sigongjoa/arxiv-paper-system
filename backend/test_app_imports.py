#!/usr/bin/env python3
"""
app.py 실행 전 import 테스트
"""
import sys
import os
import logging

# 프로젝트 루트 설정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 필수 모듈 임포트
from flask import Flask
import requests
from backend import pillow_compat
from backend.processor import PaperProcessor
from backend.core.pipeline import Pipeline
from backend.core.shorts import ArxivVideoGenerator
from backend.lm_studio_client import LMStudioClient
from backend.log_stream import setup_log_capture, log_capture
from backend.core.publisher.youtube_metadata import YouTubeMetadata
from backend.core.publisher.youtube_auth_web import YouTubeAuthWeb

def test_imports():
    """필수 import들을 하나씩 테스트"""
    
    logging.info("Testing basic imports...")
    logging.info("✓ Flask import success")
    logging.info("✓ requests import success")
    logging.info("✓ pillow_compat import success")
    logging.info("Testing processor imports...")
    logging.info("✓ PaperProcessor import success")
    logging.info("Testing core module imports...")
    logging.info("✓ Pipeline import success")
    logging.info("✓ ArxivVideoGenerator import success")
    logging.info("✓ LMStudioClient import success")
    logging.info("✓ log_stream imports success")
    logging.info("✓ YouTube modules import success")
    logging.info("🎉 All imports successful!")
    return True

def test_basic_functionality():
    """기본 기능 테스트"""
    
    logging.info("Testing basic functionality...")
    
    # Processor 인스턴스 생성 테스트
    processor = PaperProcessor()
    logging.info("✓ PaperProcessor instance created")
    
    # Pipeline 인스턴스 생성 테스트
    pipeline = Pipeline()
    logging.info("✓ Pipeline instance created")
    
    # ArxivVideoGenerator 인스턴스 생성 테스트
    shorts_generator = ArxivVideoGenerator()
    logging.info("✓ ArxivVideoGenerator instance created")
    
    # LMStudioClient 인스턴스 생성 테스트
    lm_studio_client = LMStudioClient()
    logging.info("✓ LMStudioClient instance created")
    
    logging.info("🎉 Basic functionality test passed!")
    return True

def main():
    """메인 테스트 실행"""
    logging.info("=== arXiv-to-Shorts Import Test ===")
    logging.info(f"Project root: {project_root}")
    logging.info(f"Python path: {sys.path[0]}")
    
    # Import 테스트
    imports_ok = test_imports()
    
    if imports_ok:
        # 기본 기능 테스트
        functionality_ok = test_basic_functionality()
        
        if functionality_ok:
            logging.info("✅ All tests passed! app.py should run without import errors.")
            print("\n🚀 Ready to run: python app.py")
        else:
            logging.error("❌ Functionality tests failed!")
            return 1
    else:
        logging.error("❌ Import tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
