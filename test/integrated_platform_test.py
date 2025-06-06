#!/usr/bin/env python3
"""
통합 플랫폼 테스트: 크롤링 -> AI분석 -> PDF생성
"""
import sys
import os
import logging
import asyncio
import re
from datetime import datetime, timedelta
import shutil

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, os.path.join(ROOT_PATH, 'backend'))

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s: %(message)s')

class IntegratedPlatformTest:
    def __init__(self):
        self.platforms = {
            '1': {'name': 'ArXiv', 'module': 'arxiv_crawler', 'class': 'ArxivCrawler'},
            '2': {'name': 'BioRxiv', 'module': 'biorxiv_crawler', 'class': 'BioRxivCrawler'},
            '3': {'name': 'PMC', 'module': 'pmc_crawler', 'class': 'PMCCrawler'},
            '4': {'name': 'PLOS', 'module': 'plos_crawler', 'class': 'PLOSCrawler'},
            '5': {'name': 'DOAJ', 'module': 'doaj_crawler', 'class': 'DOAJCrawler'},
            '6': {'name': 'CORE', 'module': 'core_crawler', 'class': 'CORECrawler'}
        }
        
        print("=== 통합 플랫폼 테스트 (크롤링->AI분석->PDF생성) ===")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def show_menu(self):
        print("\n사용 가능한 플랫폼:")
        for key, platform in self.platforms.items():
            print(f"  {key}. {platform['name']}")
        print("  7. 모든 플랫폼 테스트")
        print("  0. 종료")
        
    def get_crawler(self, platform_info):
        module_path = f"api.crawling.{platform_info['module']}"
        module = __import__(module_path, fromlist=[platform_info['class']])
        crawler_class = getattr(module, platform_info['class'])
        return crawler_class()

    def setup_ai_components(self):
        from agents.lm_studio_client import LMStudioClient
        from agents.multi_platform_analysis_agent import MultiPlatformAnalysisAgent
        from automation.pdf_generator import PdfGenerator
        # NotionLogger 임포트 및 초기화 비활성화
        # from utils.notion import NotionLogger 
        
        lm_client = LMStudioClient()
        analysis_agent = MultiPlatformAnalysisAgent(lm_client)
        pdf_generator = PdfGenerator()
        # notion_logger = NotionLogger() # NotionLogger 초기화 비활성화
        notion_logger = None # NotionLogger를 None으로 설정하여 사용하지 않도록 함
        
        print("✅ AI 컴포넌트 (멀티플랫폼 + Notion 로깅) 초기화 완료")
        return lm_client, analysis_agent, pdf_generator, notion_logger

            
    async def test_platform_integrated(self, platform_key):
        platform_info = self.platforms[platform_key]
        platform_name = platform_info['name']
        
        print(f"\n{'='*60}")
        print(f"{platform_name} 통합 테스트 시작")
        print(f"{'='*60}")
        
        # 대상 PDF 디렉토리 정리
        self.clear_pdf_target_directory()
        
        # 1. 크롤러 초기화
        crawler = self.get_crawler(platform_info)
        if not crawler:
            print(f"❌ {platform_name} 크롤러 초기화 실패")
            return
            
        # 2. AI 컴포넌트 초기화

        lm_client, analysis_agent, pdf_generator, notion_logger = self.setup_ai_components()
 
            
        print(f"✅ {platform_name} 모든 컴포넌트 초기화 완료")
        
        # 3. 크롤링
        print(f"\n📡 {platform_name} 크롤링 시작...")
        test_limit = 1
        crawling_start = datetime.now()
        
        try:
            papers = []
            if platform_name == 'ArXiv':
                categories = ['cs.AI']
                start_date = datetime.now() - timedelta(days=7)
                end_date = datetime.now()
                for i, paper in enumerate(crawler.crawl_papers(categories, start_date, end_date, test_limit)):
                    papers.append(paper)
                    if len(papers) >= test_limit:
                        break
            else:
                for i, paper in enumerate(crawler.crawl_papers(None, None, None, test_limit)):
                    papers.append(paper)
                    if len(papers) >= test_limit:
                        break
                        
            crawling_time = (datetime.now() - crawling_start).total_seconds()
            print(f"✅ 크롤링 완료: {len(papers)}개 논문, {crawling_time:.2f}초")
            
            if not papers:
                print("❌ 크롤링된 논문이 없음")
                return
                
        except Exception as e:
            print(f"❌ 크롤링 실패: {e}")
            logging.error(f"{platform_name} 크롤링 에러: {e}")
            return
            
        # 4. AI 분석 및 개별 PDF 생성
        print(f"\n🤖 AI 분석 및 PDF 생성 시작...")
        analysis_start = datetime.now()
        
        for i, paper in enumerate(papers, 1):
            try:
                print(f"\n📄 논문 {i}/{len(papers)} 처리 중...")
                
                # 논문 메타데이터 준비
                paper_metadata = {
                    'id': getattr(paper, 'paper_id', f'unknown_{i}'),
                    'title': getattr(paper, 'title', 'Unknown Title'),
                    'authors': getattr(paper, 'authors', []),
                    'platform': platform_name
                }
                
                # 논문 내용 (요약이나 초록 사용)
                paper_content = getattr(paper, 'summary', '') or getattr(paper, 'abstract', '') or paper_metadata['title']
                
                print(f"  ⚡ 논문 {i} AI 분석 중...")
                # AI 분석 수행
                analysis_result = await analysis_agent.analyze_paper(paper_content, paper_metadata)
                
                # 분석 결과를 PDF용 데이터로 변환
                analyzed_paper = {
                    'paper_id': paper_metadata['id'],
                    'title': analysis_result.title,
                    'authors': paper_metadata['authors'],
                    'categories': getattr(paper, 'categories', [platform_name]),
                    'summary': analysis_result.summary,
                    'key_insights': analysis_result.key_insights,
                    'methodology': analysis_result.methodology,
                    'main_findings': analysis_result.main_findings,
                    'limitations': analysis_result.limitations,
                    'future_work': analysis_result.future_work,
                    'keywords': analysis_result.technical_keywords,
                    'confidence_score': analysis_result.confidence_score,
                    'platform': platform_name,
                    'pdf_url': getattr(paper, 'pdf_url', ''),
                    'published_date': getattr(paper, 'published_date', '')
                }
                
                print(f"  ✅ 논문 {i} 분석 완료 (신뢰도: {analysis_result.confidence_score:.2f})")
                
                # Notion에 분석 결과 로깅 (비활성화)
                # try:
                #     if notion_logger:
                #         notion_logger.log_analysis_result(analysis_result)
                #         print(f"  📝 논문 {i} 분석 결과 Notion 로깅 완료")
                # except Exception as e:
                #     print(f"  ⚠️ 논문 {i} Notion 로깅 실패: {e}")
                
                # 즉시 개별 PDF 생성
                print(f"  📄 논문 {i} PDF 생성 중...")
                pdf_start = datetime.now()
                
                try:
                    # 파일명에 사용될 수 없는 문자 제거 및 공백을 언더스코어로 대체
                    safe_title = re.sub(r'[\/:*?"<>|]', '', analysis_result.title).replace(' ', '_')
                    # PDF 파일명으로 논문 제목 사용
                    pdf_title = safe_title
                    pdf_bytes = pdf_generator.generate_from_papers([analyzed_paper], pdf_title)
                    
                    pdf_time = (datetime.now() - pdf_start).total_seconds()
                    print(f"  ✅ 논문 {i} PDF 생성 완료: output/pdfs/{safe_title}.pdf ({pdf_time:.2f}초)") # 출력 메시지 수정
                    
                    # Notion에 PDF 생성 결과 로깅 (비활성화)
                    # try:
                    #     if notion_logger:
                    #         notion_logger.log_pdf_generation(analyzed_paper, "PDF 생성 성공")
                    #         print(f"  📝 논문 {i} PDF 생성 결과 Notion 로깅 완료")
                    # except Exception as e:
                    #     print(f"  ⚠️ 논문 {i} PDF Notion 로깅 실패: {e}")
                    
                except Exception as e:
                    print(f"  ❌ 논문 {i} PDF 생성 실패: {e}")
                    logging.error(f"논문 {i} PDF 생성 에러: {e}")
                    
                    # PDF 생성 실패도 Notion에 로깅 (비활성화)
                    # try:
                    #     if notion_logger:
                    #         notion_logger.log_pdf_generation(analyzed_paper, "PDF 생성 실패", str(e))
                    # except:
                    #     pass
                    continue
                
            except Exception as e:
                print(f"  ❌ 논문 {i} 처리 실패: {e}")
                logging.error(f"논문 처리 실패: {e}")
                continue
                
        analysis_time = (datetime.now() - analysis_start).total_seconds()
        print(f"✅ 모든 논문 처리 완료: {analysis_time:.2f}초")
            
        # 6. 결과 요약
        total_time = (datetime.now() - crawling_start).total_seconds()
        print(f"\n📊 {platform_name} 통합 테스트 완료:")
        print(f"   • 크롤링: {len(papers)}개 논문")
        print(f"   • 총 소요 시간: {total_time:.2f}초")
        print(f"   • 개별 PDF 생성 완료")
            
    async def test_all_platforms_integrated(self):
        print(f"\n{'='*80}")
        print("모든 플랫폼 통합 테스트")
        print(f"{'='*80}")
        
        results = {}
        total_start = datetime.now()
        
        for key, platform_info in self.platforms.items():
            platform_name = platform_info['name']
            await self.test_platform_integrated(key)
            results[platform_name] = 'SUCCESS'

                
        total_duration = (datetime.now() - total_start).total_seconds()
        
        print(f"\n{'='*80}")
        print("전체 통합 테스트 결과 요약")
        print(f"{'='*80}")
        print(f"총 소요 시간: {total_duration:.2f}초")
        
        for platform, result in results.items():
            status = "✅" if result == 'SUCCESS' else "❌"
            print(f"{status} {platform}: {result}")
            
    def run(self):
        while True:
            self.show_menu()
            
            try:
                choice = input("\n선택하세요 (0-7): ").strip()
                
                if choice == '0':
                    print("통합 테스트 도구를 종료합니다.")
                    break
                elif choice == '7':
                    asyncio.run(self.test_all_platforms_integrated())
                elif choice in self.platforms:
                    asyncio.run(self.test_platform_integrated(choice))
                else:
                    print("❌ 잘못된 선택입니다. 다시 입력해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n테스트가 중단되었습니다.")
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                logging.error(f"메인 루프 에러: {e}")

    def clear_pdf_target_directory(self):
        target_dir = os.path.join(ROOT_PATH, "pdfs")
        if os.path.exists(target_dir):
            for filename in os.listdir(target_dir):
                file_path = os.path.join(target_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    logging.error(f"Cleared old PDF: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}. Reason: {e}")
        else:
            os.makedirs(target_dir, exist_ok=True)
        logging.error(f"PDF target directory {target_dir} cleared or created.")

def main():
    try:
        tester = IntegratedPlatformTest()
        tester.run()
    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
        logging.error(f"메인 함수 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
