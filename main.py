from datetime import datetime, timedelta
from arxiv_crawler import ArxivCrawler
from database import PaperDatabase
from categories import COMPUTER_CATEGORIES, MATH_CATEGORIES, PHYSICS_CATEGORIES, ALL_CATEGORIES

class PaperCrawlManager:
    def __init__(self):
        self.crawler = ArxivCrawler()
        self.db = PaperDatabase()
        print("DEBUG: PaperCrawlManager initialized")
    
    def crawl_by_domain(self, domain: str, days_back: int = 7):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        if domain.lower() == 'computer':
            categories = COMPUTER_CATEGORIES
        elif domain.lower() == 'math':
            categories = MATH_CATEGORIES
        elif domain.lower() == 'physics':
            categories = PHYSICS_CATEGORIES
        elif domain.lower() == 'all':
            categories = ALL_CATEGORIES
        else:
            raise ValueError(f"Unknown domain: {domain}")
        
        print(f"DEBUG: Crawling {domain} papers from {start_date.date()} to {end_date.date()}")
        print(f"DEBUG: Categories: {categories}")
        
        saved_count = 0
        for paper in self.crawler.crawl_papers(categories, start_date, end_date):
            if self.db.save_paper(paper):
                saved_count += 1
        
        print(f"DEBUG: Crawling completed. Saved {saved_count} new papers")
        return saved_count
    
    def crawl_by_categories(self, categories: list, days_back: int = 7):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"DEBUG: Crawling custom categories from {start_date.date()} to {end_date.date()}")
        print(f"DEBUG: Categories: {categories}")
        
        saved_count = 0
        for paper in self.crawler.crawl_papers(categories, start_date, end_date):
            if self.db.save_paper(paper):
                saved_count += 1
        
        print(f"DEBUG: Crawling completed. Saved {saved_count} new papers")
        return saved_count
    
    def show_recent_papers(self, domain: str = 'all', days_back: int = 7, limit: int = 50):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        papers = self.db.get_papers_by_date_range(start_date, end_date, limit)
        
        if domain.lower() != 'all':
            if domain.lower() == 'computer':
                filter_cats = COMPUTER_CATEGORIES
            elif domain.lower() == 'math':
                filter_cats = MATH_CATEGORIES
            elif domain.lower() == 'physics':
                filter_cats = PHYSICS_CATEGORIES
            
            papers = [p for p in papers if any(cat in filter_cats for cat in p.categories)]
        
        print(f"\n=== {domain.upper()} PAPERS ({len(papers)} found) ===")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   arXiv ID: {paper.arxiv_id}")
            print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
            print(f"   Categories: {', '.join(paper.categories)}")
            print(f"   Published: {paper.published_date.strftime('%Y-%m-%d')}")
            print(f"   PDF: {paper.pdf_url}")
            print(f"   Abstract: {paper.abstract[:200]}...")
        
        return papers
    
    def get_stats(self):
        total = self.db.get_total_count()
        print(f"\n=== DATABASE STATS ===")
        print(f"Total papers: {total}")
        return total

def main():
    manager = PaperCrawlManager()
    
    print("=== arXiv Paper Crawler ===")
    print("1. Crawl Computer Science papers")
    print("2. Crawl Mathematics papers") 
    print("3. Crawl Physics papers")
    print("4. Crawl ALL papers")
    print("5. Show recent papers")
    print("6. Show database stats")
    
    choice = input("Select option (1-6): ").strip()
    
    if choice == '1':
        days = int(input("Days back to crawl (default 7): ") or 7)
        manager.crawl_by_domain('computer', days)
        manager.show_recent_papers('computer', days)
    elif choice == '2':
        days = int(input("Days back to crawl (default 7): ") or 7)
        manager.crawl_by_domain('math', days)
        manager.show_recent_papers('math', days)
    elif choice == '3':
        days = int(input("Days back to crawl (default 7): ") or 7)
        manager.crawl_by_domain('physics', days)
        manager.show_recent_papers('physics', days)
    elif choice == '4':
        days = int(input("Days back to crawl (default 7): ") or 7)
        manager.crawl_by_domain('all', days)
        manager.show_recent_papers('all', days)
    elif choice == '5':
        domain = input("Domain (computer/math/physics/all): ").strip() or 'all'
        days = int(input("Days back (default 7): ") or 7)
        limit = int(input("Max papers to show (default 50): ") or 50)
        manager.show_recent_papers(domain, days, limit)
    elif choice == '6':
        manager.get_stats()

if __name__ == "__main__":
    main()
