"""실제 동작하는 multi-platform 크롤러 - 전체 플랫폼 지원"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add core path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

class WorkingMultiPlatformCrawlerAPI:
    def __init__(self):
        # DB 매니저 우선 초기화
        try:
            from core.database import DatabaseManager
            self.db = DatabaseManager()
            logger.info("DatabaseManager initialized successfully")
        except Exception as e:
            logger.error(f"DatabaseManager init failed: {e}")
            import traceback
            traceback.print_exc()
            self.db = None
        
        self.platforms = {
            'arxiv': {'status': 'success', 'message': 'ArXiv crawler ready'},
            'biorxiv': {'status': 'success', 'message': 'BioRxiv/MedRxiv ready'},
            'pmc': {'status': 'success', 'message': 'PMC ready'},
            'plos': {'status': 'success', 'message': 'PLOS ready'},
            'doaj': {'status': 'success', 'message': 'DOAJ ready'},
            'core': {'status': 'success', 'message': 'CORE ready (demo mode if no API key)'}
        }
        
        # 크롤러 초기화
        self.crawlers = {}
        self._initialize_crawlers()
            
        logger.info("WorkingMultiPlatformCrawlerAPI initialized")
    
    def _initialize_crawlers(self):
        """모든 크롤러 초기화"""
        try:
            # ArXiv 크롤러
            from api.crawling.arxiv_crawler import ArxivCrawler
            self.crawlers['arxiv'] = ArxivCrawler(delay=3.0)
            logger.info("ArXiv crawler initialized")
        except Exception as e:
            logger.error(f"ArXiv crawler init failed: {e}")
            self.platforms['arxiv']['status'] = 'error'
            self.platforms['arxiv']['message'] = 'ArXiv init failed'
        
        try:
            # BioRxiv 크롤러
            from api.crawling.biorxiv_crawler import BioRxivCrawler
            self.crawlers['biorxiv'] = BioRxivCrawler()
            logger.info("BioRxiv crawler initialized")
        except Exception as e:
            logger.error(f"BioRxiv crawler init failed: {e}")
            self.platforms['biorxiv']['status'] = 'error'
            self.platforms['biorxiv']['message'] = f'BioRxiv init failed: {str(e)[:50]}'
        
        try:
            # PMC 크롤러
            from api.crawling.pmc_crawler import PMCCrawler
            self.crawlers['pmc'] = PMCCrawler()
            logger.info("PMC crawler initialized")
        except Exception as e:
            logger.error(f"PMC crawler init failed: {e}")
            self.platforms['pmc']['status'] = 'error'
            self.platforms['pmc']['message'] = 'PMC init failed'
        
        try:
            # PLOS 크롤러
            from api.crawling.plos_crawler import PLOSCrawler
            self.crawlers['plos'] = PLOSCrawler()
            logger.info("PLOS crawler initialized")
        except Exception as e:
            logger.error(f"PLOS crawler init failed: {e}")
            self.platforms['plos']['status'] = 'error'
            self.platforms['plos']['message'] = 'PLOS init failed'
        
        try:
            # DOAJ 크롤러
            from api.crawling.doaj_crawler import DOAJCrawler
            self.crawlers['doaj'] = DOAJCrawler()
            logger.info("DOAJ crawler initialized")
        except Exception as e:
            logger.error(f"DOAJ crawler init failed: {e}")
            self.platforms['doaj']['status'] = 'error'
            self.platforms['doaj']['message'] = 'DOAJ init failed'
        
        try:
            # CORE 크롤러
            from api.crawling.core_crawler import CORECrawler
            self.crawlers['core'] = CORECrawler()
            logger.info("CORE crawler initialized")
        except Exception as e:
            logger.error(f"CORE crawler init failed: {e}")
            self.platforms['core']['status'] = 'error'
            self.platforms['core']['message'] = 'CORE init failed'
    
    def GetAvailablePlatforms(self) -> Dict[str, Any]:
        """사용 가능한 플랫폼 목록"""
        try:
            platform_info = {}
            
            for platform, status in self.platforms.items():
                categories = self.get_platform_categories(platform)
                platform_info[platform] = {
                    'name': platform.title(),
                    'categories': categories,
                    'status': status['status'],
                    'message': status['message']
                }
            
            logger.info(f"Available platforms: {list(platform_info.keys())}")
            return {'platforms': platform_info}
            
        except Exception as e:
            logger.error(f"GetAvailablePlatforms error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_platform_categories(self, platform: str) -> List[str]:
        """플랫폼별 카테고리 목록"""
        categories = {
            'arxiv': ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.NE', 'cs.RO', 'math.ST', 'physics.comp-ph'],
            'biorxiv': ['Biochemistry', 'Cell Biology', 'Neuroscience', 'Genetics', 'Bioinformatics'],
            'pmc': ['Medicine', 'Biomedical Research', 'Genetics', 'Molecular Biology'],
            'plos': ['Biology', 'Computational Biology', 'Medicine', 'Genetics'],
            'doaj': ['Computer Science', 'Medicine', 'Biology', 'Engineering'],
            'core': ['Computer Science', 'Artificial Intelligence', 'Engineering', 'Medicine']
        }
        return categories.get(platform, [])
    
    def StartMultiPlatformCrawl(self, platforms: List[str], categories: Optional[List[str]] = None, 
                              limit_per_platform: int = 20) -> Dict[str, Any]:
        """다중 플랫폼 크롤링 시작"""
        try:
            logger.info(f"=== STARTING MULTI-PLATFORM CRAWL ===")
            logger.info(f"Platforms: {platforms}")
            logger.info(f"Categories: {categories}")
            logger.info(f"Limit per platform: {limit_per_platform}")
            logger.info(f"DB Status: {'Available' if self.db else 'Not Available'}")
            
            # 메모리 초기화 (새로운 크롤링 위해 기존 결과 제거)
            from api.memory_store import clear_crawled_papers, set_crawled_papers
            clear_crawled_papers()
            logger.info("=== 새로운 크롤링 시작: 기존 메모리 결과 초기화 ===")
            
            total_saved = 0
            platform_results = {}
            crawled_papers_list = []  # 메모리용 리스트
            
            for platform in platforms:
                logger.info(f"Processing platform: {platform}")
                
                if platform in self.crawlers and self.platforms[platform]['status'] == 'success':
                    try:
                        saved_count, papers = self._crawl_platform(platform, categories, limit_per_platform)
                        platform_results[platform] = {
                            'status': 'success',
                            'saved_count': saved_count
                        }
                        total_saved += saved_count
                        crawled_papers_list.extend(papers)  # 메모리에 추가
                        logger.info(f"Platform {platform} completed: {saved_count} papers")
                    except Exception as e:
                        logger.error(f"Platform {platform} failed: {e}")
                        import traceback
                        traceback.print_exc()
                        platform_results[platform] = {
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    logger.info(f"Platform {platform} not available - status: {self.platforms.get(platform, {}).get('status', 'unknown')}")
                    platform_results[platform] = {
                        'status': 'error',
                        'error': f'Platform {platform} not available'
                    }
            
            # 메모리에 크롤링 결과 저장
            set_crawled_papers(crawled_papers_list)
            logger.info(f"Stored {len(crawled_papers_list)} papers in memory")
            
            logger.info(f"=== CRAWL COMPLETED: {total_saved} papers saved ===")
            return {
                'status': 'success',
                'total_saved': total_saved,
                'platform_results': platform_results
            }
            
        except Exception as e:
            logger.error(f"StartMultiPlatformCrawl error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _crawl_platform(self, platform: str, categories: Optional[List[str]], limit: int):
        """개별 플랫폼 크롤링 - 논문 리스트도 반환"""
        try:
            # 플랫폼 상태 확인
            if self.platforms[platform]['status'] != 'success':
                logger.warning(f"Skipping {platform} - status: {self.platforms[platform]['status']}")
                return 0, []
                
            crawler = self.crawlers.get(platform)
            if not crawler:
                raise Exception(f"Crawler for {platform} not found")
            
            logger.info(f"Crawling {platform}: categories={categories}, limit={limit}")
            
            saved_count = 0
            papers_list = []  # 메모리얩 논문 리스트
            
            # ArXiv는 특별 처리 (기존 방식 유지)
            if platform == 'arxiv':
                return self._crawl_arxiv(categories, limit)
            
            # 다른 플랫폼들 크롤링 - 카테고리를 None으로 넘김
            for paper in crawler.crawl_papers(
                categories=None,  # 카테고리 필터링 완전 비활성화
                start_date=None,
                end_date=None,
                limit=limit
            ):
                try:
                    logger.info(f"Processing paper: {getattr(paper, 'title', 'Unknown')[:50]}...")
                    
                    # 데이터베이스에 저장
                    paper_data = {
                        'paper_id': paper.paper_id if hasattr(paper, 'paper_id') else paper.arxiv_id,
                        'platform': platform,
                        'title': paper.title,
                        'abstract': paper.abstract,
                        'authors': paper.authors,
                        'categories': paper.categories,
                        'pdf_url': paper.pdf_url,
                        'published_date': paper.published_date,
                        'created_at': datetime.now()
                    }
                    
                    # 메모리용 논문 데이터 (화면 표시용)
                    paper_dict = {
                        'arxiv_id': paper.paper_id if hasattr(paper, 'paper_id') else paper.arxiv_id,
                        'platform': platform,
                        'title': paper.title,
                        'abstract': paper.abstract,
                        'authors': paper.authors,
                        'categories': paper.categories,
                        'pdf_url': paper.pdf_url,
                        'published_date': paper.published_date.isoformat() if hasattr(paper, 'published_date') and paper.published_date else '',
                        'crawled': datetime.now().isoformat()
                    }
                    papers_list.append(paper_dict)
                    
                    # DB 저장 (백그라운드)
                    if self.db:
                        saved_obj = self.db.save_paper(paper_data)
                        if saved_obj is None:
                            logger.warning(f"Paper not saved (returned None): {paper_data['paper_id']}")
                        else:
                            saved_count += 1
                            logger.info(f"✓ Saved {platform} paper #{saved_count}: {paper_data['paper_id']}")
                    else:
                        logger.warning(f"DB not available for saving paper: {paper_data['paper_id']}")
                    
                    if saved_count >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error saving paper from {platform}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            return saved_count, papers_list
            
        except Exception as e:
            logger.error(f"Platform {platform} crawling failed: {e}")
            import traceback
            traceback.print_exc()
            return 0, []
    
    def _crawl_arxiv(self, categories: List[str], limit: int):
        """ArXiv 크롤링 (기존 방식) - 논문 리스트도 반환"""
        try:
            arxiv_crawler = self.crawlers.get('arxiv')
            if not arxiv_crawler or not self.db:
                return 0, []
            
            # 날짜 설정 (최근 일주일)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            logger.info(f"Crawling ArXiv: categories={categories}, limit={limit}")
            
            saved_count = 0
            papers_list = []  # 메모리용 리스트
            
            for paper in arxiv_crawler.crawl_papers(
                categories=categories,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            ):
                try:
                    # 데이터베이스에 저장
                    paper_data = {
                        'paper_id': paper.paper_id,
                        'platform': 'arxiv',
                        'title': paper.title,
                        'abstract': paper.abstract,
                        'authors': ','.join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors),
                        'categories': ','.join(paper.categories) if isinstance(paper.categories, list) else str(paper.categories),
                        'pdf_url': paper.pdf_url,
                        'published_date': paper.published_date,
                        'created_at': datetime.now()
                    }
                    
                    # 메모리용 논문 데이터
                    paper_dict = {
                        'arxiv_id': paper.paper_id,
                        'platform': 'arxiv',
                        'title': paper.title,
                        'abstract': paper.abstract,
                        'authors': ','.join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors),
                        'categories': ','.join(paper.categories) if isinstance(paper.categories, list) else str(paper.categories),
                        'pdf_url': paper.pdf_url,
                        'published_date': paper.published_date.isoformat() if hasattr(paper, 'published_date') and paper.published_date else '',
                        'crawled': datetime.now().isoformat()
                    }
                    papers_list.append(paper_dict)
                    
                    saved_obj = self.db.save_paper(paper_data)
                    if saved_obj:
                        saved_count += 1
                        logger.info(f"✓ Saved ArXiv paper #{saved_count}: {paper.paper_id}")
                    
                except Exception as e:
                    logger.error(f"Error saving ArXiv paper {paper.paper_id}: {e}")
                    continue
            
            return saved_count, papers_list
            
        except Exception as e:
            logger.error(f"ArXiv crawling failed: {e}")
            return 0, []
    
    def GetCrawlingStatus(self) -> Dict[str, Any]:
        """크롤링 시스템 상태"""
        try:
            active_count = len([p for p in self.platforms.values() if p['status'] == 'success'])
            status = {
                'total_platforms': len(self.platforms),
                'active_platforms': active_count,
                'platform_details': self.platforms,
                'database_status': 'connected' if self.db else 'disconnected'
            }
            logger.info(f"Crawling status: {active_count}/{len(self.platforms)} active")
            return status
        except Exception as e:
            logger.error(f"GetCrawlingStatus error: {e}")
            import traceback
            traceback.print_exc()
            raise
