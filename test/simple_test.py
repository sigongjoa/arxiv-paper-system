#!/usr/bin/env python3
"""
간단한 플랫폼별 크롤러 테스트 도구 (정확히 3개만)
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# 루트 경로 추가
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, os.path.join(ROOT_PATH, 'backend'))

# 로깅 설정 (에러만)
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

class SimpleCrawlerTest:
    def __init__(self):
        self.platforms = {
            '1': {'name': 'ArXiv', 'module': 'arxiv_crawler', 'class': 'ArxivCrawler'},
            '2': {'name': 'BioRxiv', 'module': 'biorxiv_crawler', 'class': 'BioRxivCrawler'},
            '3': {'name': 'PMC', 'module': 'pmc_crawler', 'class': 'PMCCrawler'},
            '4': {'name': 'PLOS', 'module': 'plos_crawler', 'class': 'PLOSCrawler'},
            '5': {'name': 'DOAJ', 'module': 'doaj_crawler', 'class': 'DOAJCrawler'},
            '6': {'name': 'CORE', 'module': 'core_crawler', 'class': 'CORECrawler'}
        }
        
        print("=== 간단 크롤러 테스트 (정확히 3개만) ===")
        
    def show_menu(self):
        print("\n플랫폼 선택:")
        for key, platform in self.platforms.items():
            print(f"  {key}. {platform['name']}")
        print("  0. 종료")
        
    def get_crawler(self, platform_info):
        try:
            module_path = f"api.crawling.{platform_info['module']}"
            module = __import__(module_path, fromlist=[platform_info['class']])
            crawler_class = getattr(module, platform_info['class'])
            return crawler_class()
        except Exception as e:
            print(f"❌ {platform_info['name']} 크롤러 초기화 실패: {e}")
            return None
            
    def test_platform(self, platform_key):
        platform_info = self.platforms[platform_key]
        platform_name = platform_info['name']
        
        print(f"\n=== {platform_name} 테스트 (3개만) ===")
        
        crawler = self.get_crawler(platform_info)
        if not crawler:
            return
            
        print(f"✅ {platform_name} 크롤러 초기화 완료")
        
        papers = []
        start_time = datetime.now()
        
        try:
            # 크롤링 파라미터
            if platform_name == 'ArXiv':
                categories = ['cs.AI']
                start_date = datetime.now() - timedelta(days=7)
                end_date = datetime.now()
                crawler_gen = crawler.crawl_papers(categories, start_date, end_date, 3)
            else:
                crawler_gen = crawler.crawl_papers(None, None, None, 3)
                
            # 정확히 3개만 수집
            count = 0
            for paper in crawler_gen:
                papers.append(paper)
                count += 1
                print(f"  📄 {count}/3: {getattr(paper, 'title', 'N/A')[:50]}...")
                if count >= 3:
                    break
                    
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n📊 결과: {len(papers)}개 수집 완료 ({duration:.1f}초)")
            
            # 상세 정보
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {getattr(paper, 'title', 'N/A')[:60]}...")
                print(f"   ID: {getattr(paper, 'paper_id', getattr(paper, 'arxiv_id', 'N/A'))}")
                print(f"   플랫폼: {getattr(paper, 'platform', 'N/A')}")
                authors = getattr(paper, 'authors', 'N/A')
                if isinstance(authors, list):
                    authors = ', '.join(authors[:2])
                print(f"   저자: {str(authors)[:50]}...")
                
        except Exception as e:
            print(f"❌ {platform_name} 크롤링 실패: {e}")
            
    def run_single_test(self, platform_key='1'): # 기본값으로 ArXiv 테스트
        if platform_key in self.platforms:
            self.test_platform(platform_key)
                else:
            print(f"❌ 잘못된 플랫폼 키: {platform_key}")

def main():
    test_runner = SimpleCrawlerTest()
    test_runner.run_single_test()

if __name__ == "__main__":
    main()
