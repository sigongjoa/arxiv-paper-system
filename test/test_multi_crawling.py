"""다중 플랫폼 크롤링 테스트"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
import logging

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.unified_crawler_manager import UnifiedCrawlerManager
from backend.core.unified_mapper import UnifiedCategoryMapper

logging.basicConfig(level=logging.ERROR)

async def test_multi_platform_crawling():
    print("=== 다중 플랫폼 크롤링 테스트 ===\n")
    
    # API 키 설정 (환경변수에서)
    config = {
        'pmc_api_key': os.getenv('PMC_API_KEY'),
        'core_api_key': os.getenv('CORE_API_KEY')
    }
    
    # 매니저 초기화
    manager = UnifiedCrawlerManager(config)
    mapper = UnifiedCategoryMapper()
    
    print("사용 가능한 플랫폼:")
    platforms = manager.get_available_platforms()
    for platform in platforms:
        status = manager.test_platform_connection(platform)
        print(f"  - {platform}: {status['status']} ({status['message']})")
    
    print("\n어떤 플랫폼을 테스트하시겠습니까?")
    for i, platform in enumerate(platforms, 1):
        print(f"{i}. {platform}")
    print("0. 전체 플랫폼")
    
    try:
        choice = int(input("선택: "))
        
        if choice == 0:
            selected_platforms = platforms
        elif 1 <= choice <= len(platforms):
            selected_platforms = [platforms[choice - 1]]
        else:
            print("잘못된 선택")
            return
            
        # 카테고리 선택
        print(f"\n선택된 플랫폼: {', '.join(selected_platforms)}")
        categories = input("카테고리 (빈 값으로 기본값 사용): ").strip().split(',') if input("카테고리를 입력하시겠습니까? (y/n): ").lower() == 'y' else None
        if categories and categories[0] == '':
            categories = None
            
        limit = int(input("논문 수 제한 (기본값 5): ") or "5")
        
        print(f"\n크롤링 시작...")
        start_time = datetime.now()
        
        # 크롤링 실행
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        papers = []
        for platform in selected_platforms:
            print(f"\n[{platform}] 크롤링 중...")
            
            try:
                platform_papers = list(manager.crawl_single_platform(
                    platform,
                    categories=categories,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                ))
                
                papers.extend(platform_papers)
                print(f"[{platform}] {len(platform_papers)}개 논문 수집 완료")
                
                # 첫 번째 논문 미리보기
                if platform_papers:
                    paper = platform_papers[0]
                    print(f"  예시: {paper.title[:50]}...")
                    print(f"  저자: {', '.join(paper.authors[:2])}...")
                    print(f"  카테고리: {', '.join(paper.categories[:3])}")
                    
                    # 카테고리 매핑 테스트
                    if paper.categories:
                        mapped = mapper.normalize_category(platform, paper.categories[0])
                        print(f"  매핑: {paper.categories[0]} -> {mapped['level1']}.{mapped['level2']}")
                        
            except Exception as e:
                print(f"[{platform}] 크롤링 실패: {e}")
                continue
        
        elapsed = datetime.now() - start_time
        
        print(f"\n=== 크롤링 완료 ===")
        print(f"총 소요시간: {elapsed.total_seconds():.2f}초")
        print(f"총 논문 수: {len(papers)}개")
        
        # 플랫폼별 통계
        platform_stats = {}
        for paper in papers:
            platform = paper.platform
            if platform not in platform_stats:
                platform_stats[platform] = 0
            platform_stats[platform] += 1
            
        for platform, count in platform_stats.items():
            print(f"  - {platform}: {count}개")
            
        # 저장 여부 선택
        if papers and input("\n결과를 JSON 파일로 저장하시겠습니까? (y/n): ").lower() == 'y':
            import json
            
            output_data = []
            for paper in papers:
                output_data.append({
                    'platform': paper.platform,
                    'paper_id': paper.paper_id,
                    'title': paper.title,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'abstract': paper.abstract[:200] + '...' if len(paper.abstract) > 200 else paper.abstract,
                    'published_date': paper.published_date.isoformat(),
                    'pdf_url': paper.pdf_url,
                    'url': paper.url
                })
            
            filename = f"multi_platform_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"결과 저장: {filename}")
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_platform_crawling())

def main():
    asyncio.run(test_multi_platform_crawling())
