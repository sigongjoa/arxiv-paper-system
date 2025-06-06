# 전역 메모리 저장소 - 크롤링 결과 즉시 표시용
latest_crawled_papers = []

def set_crawled_papers(papers):
    """크롤링 결과 저장"""
    global latest_crawled_papers
    latest_crawled_papers = papers

def get_crawled_papers():
    """크롤링 결과 반환"""
    return latest_crawled_papers

def clear_crawled_papers():
    """크롤링 결과 초기화"""
    global latest_crawled_papers
    latest_crawled_papers = []
