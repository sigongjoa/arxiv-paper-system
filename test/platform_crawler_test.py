#!/usr/bin/env python3
"""
플랫폼별 크롤러 테스트 도구
키 입력으로 플랫폼 선택하여 3개씩 크롤링 테스트
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# 루트 경로 추가
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, os.path.join(ROOT_PATH, 'backend'))

# 로깅 설정
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

class PlatformCrawlerTest:
    def __init__(self):
        self.platforms = {
            '1': {'name': 'ArXiv', 'module': 'arxiv_crawler', 'class': 'ArxivCrawler'},
            '2': {'name': 'BioRxiv', 'module': 'biorxiv_crawler', 'class': 'BioRxivCrawler'},
            '3': {'name': 'PMC', 'module': 'pmc_crawler', 'class': 'PMCCrawler'},
            '4': {'name': 'PLOS', 'module': 'plos_crawler', 'class': 'PLOSCrawler'},
            '5': {'name': 'DOAJ', 'module': 'doaj_crawler', 'class': 'DOAJCrawler'},
            '6': {'name': 'CORE', 'module': 'core_crawler', 'class': 'CORECrawler'}
        }
        
        print("=== 플랫폼 크롤러 테스트 도구 ===")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def show_menu(self):
        print("\n사용 가능한 플랫폼:")
        for key, platform in self.platforms.items():
            print(f"  {key}. {platform['name']}")
        print("  7. 모든 플랫폼 테스트")
        print("  0. 종료")
        
    def get_crawler(self, platform_info):
        try:
            module_path = f"api.crawling.{platform_info['module']}"
            module = __import__(module_path, fromlist=[platform_info['class']])
            crawler_class = getattr(module, platform_info['class'])
            return crawler_class()
        except Exception as e:
            logging.error(f"크롤러 초기화 실패 {platform_info['name']}: {e}")
            return None
            
    def test_platform(self, platform_key):
        platform_info = self.platforms[platform_key]
        platform_name = platform_info['name']
        
        print(f"\n{'='*50}")
        print(f"{platform_name} 크롤링 테스트 시작")
        print(f"{'='*50}")
        
        crawler = self.get_crawler(platform_info)
        if not crawler:
            print(f"❌ {platform_name} 크롤러 초기화 실패")
            return
            
        print(f"✅ {platform_name} 크롤러 초기화 완료")
        
        # 크롤링 파라미터 설정
        test_limit = 3
        start_time = datetime.now()
        
        try:
            if platform_name == 'ArXiv':
                categories = ['cs.AI']
                start_date = datetime.now() - timedelta(days=7)
                end_date = datetime.now()
                papers = []
                # 정확히 3개만 가져오기
                for i, paper in enumerate(crawler.crawl_papers(categories, start_date, end_date, test_limit)):
                    papers.append(paper)
                    if len(papers) >= test_limit:
                        break
            else:
                papers = []
                # 다른 플랫폼도 정확히 3개만
                for i, paper in enumerate(crawler.crawl_papers(None, None, None, test_limit)):
                    papers.append(paper)
                    if len(papers) >= test_limit:
                        break
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n📊 크롤링 결과:")
            print(f"   • 플랫폼: {platform_name}")
            print(f"   • 수집된 논문 수: {len(papers)}")
            print(f"   • 소요 시간: {duration:.2f}초")
            
            # 논문 상세 정보 출력
            for i, paper in enumerate(papers, 1):
                print(f"\n📄 논문 {i}:")
                print(f"   • ID: {getattr(paper, 'paper_id', 'N/A')}")
                print(f"   • 제목: {getattr(paper, 'title', 'N/A')[:80]}...")
                print(f"   • 플랫폼: {getattr(paper, 'platform', 'N/A')}")
                print(f"   • 저자: {str(getattr(paper, 'authors', 'N/A'))[:60]}...")
                print(f"   • 카테고리: {str(getattr(paper, 'categories', 'N/A'))[:40]}...")
                print(f"   • PDF URL: {getattr(paper, 'pdf_url', 'N/A')[:60]}...")
                
        except Exception as e:
            print(f"❌ {platform_name} 크롤링 실패: {e}")
            logging.error(f"{platform_name} 크롤링 에러: {e}")
            import traceback
            traceback.print_exc()
            
    def run_single_platform_test(self, platform_key='1'): # 기본값으로 ArXiv 테스트
        if platform_key in self.platforms:
            self.test_platform(platform_key)
        else:
            print(f"❌ 잘못된 플랫폼 키: {platform_key}")

    def run_all_platform_tests(self):
        print(f"\n{'='*60}")
        print("모든 플랫폼 순차 테스트")
        print(f"{'='*60}")
        
        results = {}
        total_start = datetime.now()
        
        for key, platform_info in self.platforms.items():
            platform_name = platform_info['name']
            start_time = datetime.now()
            
            try:
                self.test_platform(key)
                results[platform_name] = 'SUCCESS'
            except Exception as e:
                results[platform_name] = f'FAILED: {str(e)[:50]}'
                logging.error(f"플랫폼 {platform_name} 테스트 실패: {e}")
                
        total_duration = (datetime.now() - total_start).total_seconds()
        
        print(f"\n{'='*60}")
        print("전체 테스트 결과 요약")
        print(f"{'='*60}")
        print(f"총 소요 시간: {total_duration:.2f}초")
        
        for platform, result in results.items():
            status = "✅" if result == 'SUCCESS' else "❌"
            print(f"{status} {platform}: {result}")
            
def main(test_type='single', platform_key='1'):
    """메인 실행 함수"""
    try:
        tester = PlatformCrawlerTest()
        if test_type == 'all':
            tester.run_all_platform_tests()
        else:
            tester.run_single_platform_test(platform_key)
    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
        logging.error(f"메인 함수 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 이 스크립트를 직접 실행할 때 기본 동작 (ArXiv 단일 테스트)
    # 또는 명령줄 인수를 통해 다른 테스트 실행 가능
    # 예: python platform_crawler_test.py --type all
    # 예: python platform_crawler_test.py --type single --platform 2
    import argparse
    parser = argparse.ArgumentParser(description='Platform Crawler Test Runner')
    parser.add_argument('--type', type=str, default='single', choices=['single', 'all'],
                        help='Type of test to run (single or all)')
    parser.add_argument('--platform', type=str, default='1',
                        help='Platform key for single test (e.g., 1 for ArXiv)')
    args = parser.parse_args()
    
    main(args.type, args.platform)
