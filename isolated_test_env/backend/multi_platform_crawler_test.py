import os
import sys
import logging
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import uuid
import json
from bs4 import BeautifulSoup
import io

# Set stdout and stderr encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add the isolated_test_env/backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.config import Config
from core.models import Paper
from db.connection import engine, create_tables, SessionLocal
from core.arxiv_client import ArxivClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def fetch_arxiv_papers(query: str, max_results: int = 2) -> list:
    """Fetch papers from arXiv API based on a query."""
    params = {
        "search_query": query,
        "max_results": max_results
    }
    logger.info(f"Fetching papers from arXiv API with query: {query}, max_results: {max_results}")
    try:
        response = requests.get(ARXIV_API_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        root = ET.fromstring(response.content)
        
        papers_data = []
        # Namespace for parsing XML
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}

        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            abstract = entry.find('atom:summary', ns).text.strip()
            
            arxiv_id_full = entry.find('atom:id', ns).text
            arxiv_id = arxiv_id_full.split('/')[-1] # Extract the numeric ID part
            
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            pdf_url = pdf_link.attrib['href'] if pdf_link is not None else None

            published_date_str = entry.find('atom:published', ns).text
            published_date = datetime.strptime(published_date_str, '%Y-%m-%dT%H:%M:%SZ')
            
            updated_date_str = entry.find('atom:updated', ns).text
            updated_date = datetime.strptime(updated_date_str, '%Y-%m-%dT%H:%M:%SZ')

            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
            categories = [category.attrib['term'] for category in entry.findall('arxiv:category', ns)]
            
            papers_data.append({
                "paper_id": f"arxiv_{arxiv_id}", # Unique ID for the database
                "external_id": arxiv_id,
                "platform": "arxiv",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                "published_date": published_date,
                "updated_date": updated_date,
                "platform_metadata": {"arxiv_comments": "some arxiv specific comments"} # Example of platform-specific metadata
            })
        logger.info(f"Successfully fetched {len(papers_data)} papers from arXiv API.")
        return papers_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from arXiv API: {e}")
        return []
    except ET.ParseError as e:
        logger.error(f"Error parsing XML from arXiv API: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during API fetch: {e}", exc_info=True)
        return []

def fetch_rss_papers(feed_url: str, max_results: int = 2) -> list:
    """Simulate fetching papers from an RSS feed."""
    logger.info(f"Simulating fetching papers from RSS feed: {feed_url}, max_results: {max_results}")
    papers_data = []
    for i in range(max_results):
        paper_id = f"rss_paper_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        external_id = f"rss_external_id_{i}"
        title = f"RSS Feed Paper Title {i+1} - AI and ML Updates"
        abstract = f"This is an abstract for a simulated RSS feed paper number {i+1}. It talks about recent advancements in AI and Machine Learning from the {feed_url} source."
        authors = [f"RSS Author {i+1}"]
        categories = ["AI", "Machine Learning", "RSS"]
        pdf_url = f"http://rss.example.com/paper_{i+1}.pdf"
        published_date = datetime.now() - timedelta(days=i)
        updated_date = datetime.now()
        platform_metadata = {"rss_source": feed_url, "rss_category": "Tech News"} # Example of platform-specific metadata

        papers_data.append({
            "paper_id": paper_id,
            "external_id": external_id,
            "platform": "rss",
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": categories,
            "pdf_url": pdf_url,
            "embedding": [0.0] * 768, # Mock embedding
            "published_date": published_date,
            "updated_date": updated_date,
            "platform_metadata": platform_metadata
        })
    logger.info(f"Successfully simulated fetching {len(papers_data)} papers from RSS feed.")
    return papers_data

def save_papers_to_db(papers_data: list):
    """Save fetched papers to the database."""
    session = SessionLocal()
    try:
        saved_count = 0
        for data in papers_data:
            existing_paper = session.query(Paper).filter_by(paper_id=data['paper_id']).first()
            if existing_paper:
                logger.warning(f"Paper with ID {data['paper_id']} already exists. Skipping.")
                continue

            # Ensure the platform_metadata key exists in the data dictionary
            if "platform_metadata" not in data:
                data["platform_metadata"] = None # Or an empty dict {}

            new_paper = Paper(
                paper_id=data['paper_id'],
                external_id=data['external_id'],
                platform=data['platform'],
                title=data['title'],
                abstract=data['abstract'],
                authors=data['authors'],
                categories=data['categories'],
                pdf_url=data['pdf_url'],
                embedding=data['embedding'],
                published_date=data['published_date'],
                updated_date=data['updated_date'],
                platform_metadata=data['platform_metadata']
            )
            session.add(new_paper)
            saved_count += 1
        session.commit()
        logger.info(f"Successfully saved {saved_count} new papers to the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving papers to database: {e}", exc_info=True)
    finally:
        session.close()

def fetch_biorxiv_papers(max_results: int = 2) -> list:
    logger.info(f"BioRxiv 논문 크롤링 시작 (실제). 논문 {max_results}개 검색.")
    papers_data = []
    
    # 실제 BioRxiv 논문 URL 예시 (최신 논문 페이지 또는 특정 논문 ID를 통해 접근)
    # 여기서는 몇 가지 샘플 DOI를 사용하여 PDF URL을 파싱하는 것을 보여줍니다.
    sample_biorxiv_dois = [
        "10.1101/2023.06.05.543791v1", # 일반 논문 페이지, PDF 링크 파싱 필요
        "10.1101/2023.01.05.522896",   # 일반 논문 페이지, PDF 링크 파싱 필요 (이전 검색에서 PDF로 바로 가는 링크로 인식되었지만, 실제로는 페이지가 더 일반적)
    ]

    for i, doi_id in enumerate(sample_biorxiv_dois):
        if i >= max_results:
            break

        base_url = f"https://www.biorxiv.org/content/{doi_id}"
        pdf_url = None
        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # PDF 다운로드 링크 찾기 (일반적으로 'Download PDF' 텍스트를 포함하는 링크)
            # BioRxiv 페이지 구조에 따라 셀렉터가 변경될 수 있습니다.
            pdf_link_tag = soup.find('a', {'data-icon': 'pdf'}, href=True)
            if pdf_link_tag and pdf_link_tag['href']:
                pdf_url = f"https://www.biorxiv.org" + pdf_link_tag['href']
                logger.info(f"BioRxiv: {base_url}에서 PDF URL 찾음: {pdf_url}")
            else:
                # data-icon 속성으로 찾지 못했다면, 'Download PDF' 텍스트로 찾아봅니다.
                pdf_link_tag = soup.find('a', string=lambda text: text and 'Download PDF' in text)
                if pdf_link_tag and pdf_link_tag['href']:
                    pdf_url = f"https://www.biorxiv.org" + pdf_link_tag['href']
                    logger.info(f"BioRxiv: {base_url}에서 'Download PDF' 링크 찾음: {pdf_url}")
                else:
                    logger.warning(f"BioRxiv: {base_url}에서 PDF 링크를 찾을 수 없습니다. 기본 DOI 기반 URL 사용.")
                    # 일반적인 BioRxiv PDF URL 패턴 (DOI + .full.pdf)
                    pdf_url = f"https://www.biorxiv.org/content/{doi_id}.full.pdf"

            # 논문 제목, 초록, 저자 등도 실제 페이지에서 파싱할 수 있지만,
            # 현재는 PDF URL 기능 시연에 중점을 둡니다.
            title_tag = soup.find('h1', class_='highwire-cite-title')
            title = title_tag.text.strip() if title_tag else f"BioRxiv Paper {i+1} Title (Crawled)"

            abstract_tag = soup.find('div', class_='abstract')
            abstract = abstract_tag.text.strip() if abstract_tag else f"This is a crawled abstract for BioRxiv paper {i+1}."

            authors_list = []
            authors_div = soup.find('div', class_='highwire-cite-authors')
            if authors_div:
                author_tags = authors_div.find_all('span', class_='highwire-citation-author')
                authors_list = [author_tag.find('a', class_='author-name').text.strip() for author_tag in author_tags if author_tag.find('a', class_='author-name')]
            authors = authors_list if authors_list else [f"BioRxiv Author {j+1}" for j in range(2)]

            papers_data.append({
                "paper_id": f"biorxiv.{doi_id.split('/')[-1]}",
                "external_id": doi_id.split('/')[-1],
                "platform": "biorxiv",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": ["Biology", "Bioinformatics"], # 예시 카테고리
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                "published_date": datetime.now() - timedelta(days=i), # 임시 날짜
                "updated_date": datetime.now(), # 임시 날짜
                "platform_metadata": {"doi": doi_id}
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"BioRxiv 크롤링 오류 ({base_url}): {e}")
            papers_data.append({
                "paper_id": f"biorxiv.{uuid.uuid4().hex[:10]}",
                "external_id": doi_id.split('/')[-1],
                "platform": "biorxiv",
                "title": f"BioRxiv Paper {i+1} (Error)",
                "abstract": "Error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://error.biorxiv.org/mock.pdf", # 오류 시 목업 URL
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })
        except Exception as e:
            logger.error(f"BioRxiv 일반 오류 ({base_url}): {e}", exc_info=True)
            papers_data.append({
                "paper_id": f"biorxiv.{uuid.uuid4().hex[:10]}",
                "external_id": doi_id.split('/')[-1],
                "platform": "biorxiv",
                "title": f"BioRxiv Paper {i+1} (Unexpected Error)",
                "abstract": "Unexpected error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://unexpected.biorxiv.org/mock.pdf", # 오류 시 목업 URL
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })

    logger.info(f"BioRxiv: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_pmc_papers(max_results: int = 2) -> list:
    logger.info(f"PMC 논문 크롤링 시작 (실제). 논문 {max_results}개 검색.")
    papers_data = []
    
    # 실제 PMC 논문 ID 예시 (PubMed에서 검색하여 가져옴)
    sample_pmc_ids = [
        "PMC10394350", # 'An optimal medicinal and edible Chinese herbal formula...' 논문
        "PMC9779313",  # 다른 샘플 논문
    ]

    for i, pmc_id in enumerate(sample_pmc_ids):
        if i >= max_results:
            break

        # PMC 논문 페이지 URL (PDF 링크를 찾을 수 있는 곳)
        base_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
        pdf_url = None
        try:
            response = requests.get(base_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # PDF 다운로드 링크 찾기 (일반적으로 'PDF' 버튼 또는 링크)
            # PMC 페이지 구조에 따라 셀렉터가 변경될 수 있습니다.
            pdf_link_tag = soup.find('a', class_='resolve-target', attrs={'href': lambda href: href and '/pdf/' in href}, string='Download PDF')
            if pdf_link_tag and pdf_link_tag['href']:
                pdf_url = f"https://www.ncbi.nlm.nih.gov" + pdf_link_tag['href']
                logger.info(f"PMC: {base_url}에서 PDF URL 찾음: {pdf_url}")
            else:
                logger.warning(f"PMC: {base_url}에서 PDF 링크를 찾을 수 없습니다. 기본 PMC ID 기반 PDF URL 사용.")
                # 일반적인 PMC PDF URL 패턴 (ID + /pdf/)
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"

            # 논문 제목, 초록, 저자 등도 실제 페이지에서 파싱할 수 있지만,
            # 현재는 PDF URL 기능 시연에 중점을 둡니다.
            title_tag = soup.find('h1', class_='content-title')
            title = title_tag.text.strip() if title_tag else f"PMC Paper {i+1} Title (Crawled)"

            abstract_tag = soup.find('div', class_='abstract-content')
            abstract = abstract_tag.text.strip() if abstract_tag else f"This is a crawled abstract for PMC paper {i+1}."

            authors_list = []
            authors_div = soup.find('div', class_='authors')
            if authors_div:
                author_tags = authors_div.find_all('a', class_='full-name')
                authors_list = [author_tag.text.strip() for author_tag in author_tags if author_tag.text.strip() != '...']
            authors = authors_list if authors_list else [f"PMC Author {j+1}" for j in range(2)]

            papers_data.append({
                "paper_id": f"pmc_{pmc_id}",
                "external_id": pmc_id,
                "platform": "pmc",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": ["Medicine", "Public Health"], # 예시 카테고리
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                "published_date": datetime.now() - timedelta(days=i), # 임시 날짜
                "updated_date": datetime.now(), # 임시 날짜
                "platform_metadata": {"pmc_id": pmc_id}
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"PMC 크롤링 오류 ({base_url}): {e}")
            papers_data.append({
                "paper_id": f"pmc.{uuid.uuid4().hex[:10]}",
                "external_id": pmc_id,
                "platform": "pmc",
                "title": f"PMC Paper {i+1} (Error)",
                "abstract": "Error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://error.pmc.org/mock.pdf", # 오류 시 목업 URL
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })
        except Exception as e:
            logger.error(f"PMC 일반 오류 ({base_url}): {e}", exc_info=True)
            papers_data.append({
                "paper_id": f"pmc.{uuid.uuid4().hex[:10]}",
                "external_id": pmc_id,
                "platform": "pmc",
                "title": f"PMC Paper {i+1} (Unexpected Error)",
                "abstract": "Unexpected error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://unexpected.pmc.org/mock.pdf", # 오류 시 목업 URL
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })

    logger.info(f"PMC: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_plos_papers(max_results: int = 2) -> list:
    logger.info(f"PLOS 논문 크롤링 시작 (실제). 논문 {max_results}개 검색.")
    papers_data = []

    # 실제 PLOS 논문 DOI 예시 (PLOS One에서 검색하여 가져옴)
    sample_plos_dois = [
        "10.1371/journal.pone.0286654", # 'Association of 25(OH)-Vitamin D and metabolic factors with colorectal polyps' 논문
        "10.1371/journal.pone.0130136", # 'SerpinB2 (PAI-2) Modulates Proteostasis via Binding Misfolded Proteins...' 논문
    ]

    for i, plos_doi in enumerate(sample_plos_dois):
        if i >= max_results:
            break

        # PLOS 논문 페이지 URL (PDF 링크를 찾을 수 있는 곳)
        base_url = f"https://journals.plos.org/plosone/article?id={plos_doi}"
        pdf_url = None
        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            soup = BeautifulSoup(response.content, 'html.parser')

            # PDF 다운로드 링크 찾기 (PLOS는 'Download PDF' 버튼이 있음)
            pdf_link_tag = soup.find('a', class_='metrics-buttons__link', string='Download PDF')
            if pdf_link_tag and pdf_link_tag['href']:
                # PLOS의 PDF URL은 DOI를 기반으로 함
                pdf_url = f"https://journals.plos.org/plosone/article/file?id={plos_doi}&type=printable"
                logger.info(f"PLOS: {base_url}에서 PDF URL 찾음: {pdf_url}")
            else:
                logger.warning(f"PLOS: {base_url}에서 PDF 링크를 찾을 수 없습니다. 기본 DOI 기반 PDF URL 사용.")
                pdf_url = f"https://journals.plos.org/plosone/article/file?id={plos_doi}&type=printable"

            # 논문 제목, 초록, 저자 등도 실제 페이지에서 파싱할 수 있지만,
            # 현재는 PDF URL 기능 시연에 중점을 둡니다.
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.text.strip() if title_tag else f"PLOS Paper {i+1} Title (Crawled)"

            abstract_tag = soup.find('div', class_='abstract-content')
            abstract = abstract_tag.text.strip() if abstract_tag else f"This is a crawled abstract for PLOS paper {i+1}."

            authors_list = []
            authors_span = soup.find('span', class_='authors')
            if authors_span:
                author_tags = authors_span.find_all('a', class_='author-name') # 정확한 클래스명 확인 필요
                authors_list = [author_tag.text.strip() for author_tag in author_tags]
            authors = authors_list if authors_list else [f"PLOS Author {j+1}" for j in range(2)]

            papers_data.append({
                "paper_id": f"plos_{plos_doi.replace('/', '_').replace('.', '_')}",
                "external_id": plos_doi,
                "platform": "plos",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": ["Biology", "Medicine"], # 예시 카테고리
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                "published_date": datetime.now() - timedelta(days=i),
                "updated_date": datetime.now(),
                "platform_metadata": {"doi": plos_doi}
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"PLOS 크롤링 오류 ({base_url}): {e}")
            papers_data.append({
                "paper_id": f"plos.{uuid.uuid4().hex[:10]}",
                "external_id": plos_doi,
                "platform": "plos",
                "title": f"PLOS Paper {i+1} (Error)",
                "abstract": "Error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://error.plos.org/mock.pdf",
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })
        except Exception as e:
            logger.error(f"PLOS 일반 오류 ({base_url}): {e}", exc_info=True)
            papers_data.append({
                "paper_id": f"plos.{uuid.uuid4().hex[:10]}",
                "external_id": plos_doi,
                "platform": "plos",
                "title": f"PLOS Paper {i+1} (Unexpected Error)",
                "abstract": "Unexpected error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://unexpected.plos.org/mock.pdf",
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })

    logger.info(f"PLOS: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_doaj_papers(max_results: int = 2) -> list:
    logger.info(f"DOAJ 논문 크롤링 시작 (실제). 논문 {max_results}개 검색.")
    papers_data = []

    # 실제 DOAJ에 등재된 저널 및 논문 DOI 예시 (DOAJ에서 검색하여 가져옴)
    # DOAJ는 개별 PDF를 직접 호스팅하지 않으므로, 저널 페이지로 이동하여 PDF 링크를 찾아야 합니다.
    # 여기서는 DOAJ에 등재된 특정 저널의 샘플 논문 DOI를 사용합니다.
    sample_doaj_dois = [
        "10.7187/rbcs.v10i1.2023.e1017", # Revista Brasileira de Ciência do Solo의 샘플 논문
    ]

    for i, doaj_doi in enumerate(sample_doaj_dois):
        if i >= max_results:
            break

        # DOI를 통해 논문 메타데이터를 가져올 수 있는 Crossref API 사용
        # DOAJ는 직접 PDF를 호스팅하지 않으므로, DOI를 통해 실제 출판사의 페이지로 이동해야 합니다.
        crossref_api_url = f"https://api.crossref.org/works/{doaj_doi}"
        pdf_url = None
        try:
            response = requests.get(crossref_api_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            crossref_data = response.json()
            
            # Crossref에서 PDF URL을 직접 제공하는 경우가 있음
            if 'link' in crossref_data['message']:
                for link in crossref_data['message']['link']:
                    if link.get('content-type') == 'application/pdf':
                        pdf_url = link['URL']
                        logger.info(f"DOAJ (Crossref): {doaj_doi}에서 PDF URL 찾음: {pdf_url}")
                        break
            
            # PDF URL을 Crossref에서 찾지 못했다면, 논문 웹 페이지를 방문하여 파싱 시도
            if not pdf_url and 'URL' in crossref_data['message']:
                article_url = crossref_data['message']['URL']
                logger.info(f"DOAJ (Crossref): PDF URL을 찾지 못함. 논문 페이지 파싱 시도: {article_url}")
                try:
                    article_response = requests.get(article_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
                    article_response.raise_for_status()
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # 일반적인 PDF 링크 찾기 (텍스트에 'PDF' 또는 확장자가 '.pdf'인 링크)
                    pdf_link_tag = article_soup.find('a', href=lambda href: href and '.pdf' in href.lower())
                    if not pdf_link_tag:
                         pdf_link_tag = article_soup.find('a', text=lambda text: text and 'PDF' in text.upper(), href=True)
                    
                    if pdf_link_tag and pdf_link_tag['href']:
                        if pdf_link_tag['href'].startswith('http'):
                            pdf_url = pdf_link_tag['href']
                        else:
                            # 상대 경로일 경우 기본 URL과 결합
                            from urllib.parse import urljoin
                            pdf_url = urljoin(article_url, pdf_link_tag['href'])
                        logger.info(f"DOAJ (웹 파싱): {article_url}에서 PDF URL 찾음: {pdf_url}")

                    title_list = crossref_data['message'].get('title')
                    if title_list:
                        title = title_list[0]
                    else:
                        title = f"DOAJ Paper {i+1} Title"

                    abstract = crossref_data['message'].get('abstract')
                    if abstract:
                        abstract = BeautifulSoup(abstract, 'html.parser').get_text().strip()
                    else:
                        abstract = f"This is a crawled abstract for DOAJ paper {i+1}."

                    authors_data = crossref_data['message'].get('author', [])
                    authors = [author.get('given', '') + ' ' + author.get('family', '') for author in authors_data]
                    if not authors:
                        authors = [f"DOAJ Author {j+1}" for j in range(2)]
                    categories = crossref_data['message'].get('subject', ["General Science"]) # 주제를 카테고리로 사용

                    published_date_parts = crossref_data['message'].get('published', {}).get('date-parts', [[None]])[0]
                    published_date = None
                    if published_date_parts and published_date_parts[0]:
                        try:
                            published_date = datetime(*published_date_parts[:3])
                        except TypeError:
                            logger.warning(f"DOAJ: published_date 파싱 오류: {published_date_parts}")
                    if not published_date:
                        published_date = datetime.now() - timedelta(days=i)
                    
                    updated_date = datetime.now()

                    papers_data.append({
                        "paper_id": f"doaj_{doaj_doi.replace('/','_').replace('.','_')}",
                        "external_id": doaj_doi,
                        "platform": "doaj",
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "categories": categories,
                        "pdf_url": pdf_url if pdf_url else "http://no.pdf.found.doaj.org/mock.pdf", # PDF를 찾지 못할 경우 목업 URL
                        "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                        "published_date": published_date,
                        "updated_date": updated_date,
                        "platform_metadata": {"doi": doaj_doi, "journal_url": crossref_data['message'].get('URL')}
                    })

                except requests.exceptions.RequestException as e:
                    logger.error(f"DOAJ (Crossref API) 크롤링 오류 ({crossref_api_url}): {e}")
                    papers_data.append({
                        "paper_id": f"doaj.{uuid.uuid4().hex[:10]}",
                        "external_id": doaj_doi,
                        "platform": "doaj",
                        "title": f"DOAJ Paper {i+1} (Error)",
                        "abstract": "Error during crawling.",
                        "authors": [],
                        "categories": [],
                        "pdf_url": "http://error.doaj.org/mock.pdf",
                        "embedding": [0.0] * 10,
                        "published_date": datetime.now(),
                        "updated_date": datetime.now(),
                        "platform_metadata": {"error": str(e)}
                    })
                except Exception as e:
                    logger.error(f"DOAJ 일반 오류 ({doaj_doi}): {e}", exc_info=True)
                    papers_data.append({
                        "paper_id": f"doaj.{uuid.uuid4().hex[:10]}",
                        "external_id": doaj_doi,
                        "platform": "doaj",
                        "title": f"DOAJ Paper {i+1} (Unexpected Error)",
                        "abstract": "Unexpected error during crawling.",
                        "authors": [],
                        "categories": [],
                        "pdf_url": "http://unexpected.doaj.org/mock.pdf",
                        "embedding": [0.0] * 10,
                        "published_date": datetime.now(),
                        "updated_date": datetime.now(),
                        "platform_metadata": {"error": str(e)}
                    })

        except requests.exceptions.RequestException as e:
            logger.error(f"DOAJ (Crossref API) 크롤링 오류 ({crossref_api_url}): {e}")
            papers_data.append({
                "paper_id": f"doaj.{uuid.uuid4().hex[:10]}",
                "external_id": doaj_doi,
                "platform": "doaj",
                "title": f"DOAJ Paper {i+1} (Error)",
                "abstract": "Error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://error.doaj.org/mock.pdf",
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })
        except Exception as e:
            logger.error(f"DOAJ 일반 오류 ({doaj_doi}): {e}", exc_info=True)
            papers_data.append({
                "paper_id": f"doaj.{uuid.uuid4().hex[:10]}",
                "external_id": doaj_doi,
                "platform": "doaj",
                "title": f"DOAJ Paper {i+1} (Unexpected Error)",
                "abstract": "Unexpected error during crawling.",
                "authors": [],
                "categories": [],
                "pdf_url": "http://unexpected.doaj.org/mock.pdf",
                "embedding": [0.0] * 10,
                "published_date": datetime.now(),
                "updated_date": datetime.now(),
                "platform_metadata": {"error": str(e)}
            })

    logger.info(f"DOAJ: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def run_multi_platform_crawler_test():
    print("run_multi_platform_crawler_test 함수가 호출되었습니다.")
    print("멀티 플랫폼 크롤러 테스트 시작...")
    create_tables()

    db = SessionLocal()
    try:
        # 기존 Paper 데이터 모두 삭제
        db.query(Paper).delete()
        db.commit()
        print("기존 Paper 데이터 삭제 완료.")

        all_papers_data = []

        # 1. arXiv 크롤링 (실제)
        print("arXiv 논문 크롤링 시작 (실제)...")
        arxiv_client = ArxivClient()
        arxiv_query = "LLM" # LLM 관련 논문 검색
        crawled_arxiv_papers = arxiv_client.search(query=arxiv_query, max_results=3)
        for paper in crawled_arxiv_papers:
            # Paper 모델에 맞게 데이터 준비 (arxiv_client에서 반환된 데이터 구조에 따라 매핑)
            # platform 필드도 설정
            
            published_date_str = paper.get("published_date")
            published_date_obj = None
            if published_date_str:
                try:
                    # 예시 형식: '2024-06-20T12:00:00Z' 또는 'Thu, 20 Jun 2024 12:00:00 GMT' 등
                    # feedparser는 RFC 822 또는 ISO 8601 형식을 반환할 수 있으므로 여러 형식을 시도합니다.
                    published_date_obj = datetime.strptime(published_date_str, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    try:
                        published_date_obj = datetime.strptime(published_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    except ValueError:
                        print(f"경고: 알 수 없는 published_date 형식: {published_date_str}")

            # updated_date는 arxiv_client에서 'updated_date' 필드로 직접 제공됨
            updated_date_str = paper.get("updated_date")
            updated_date_obj = None
            if updated_date_str:
                try:
                    updated_date_obj = datetime.strptime(updated_date_str, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    try:
                        updated_date_obj = datetime.strptime(updated_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    except ValueError:
                        print(f"경고: 알 수 없는 updated_date 형식: {updated_date_str}")

            paper_data = {
                "paper_id": f"arxiv_{paper.get('arxiv_id')}",
                "external_id": paper.get("arxiv_id"),
                "platform": "arxiv",
                "title": paper.get("title"),
                "abstract": paper.get("abstract"),
                "authors": paper.get("authors"),
                "categories": paper.get("categories"),
                "pdf_url": paper.get("pdf_url"),
                "embedding": [0.0] * 10, # Mock embedding을 짧게 줄임
                "published_date": published_date_obj,
                "updated_date": updated_date_obj,
                "platform_metadata": {
                    "arxiv_comments": paper.get("comment"),
                    "journal_ref": paper.get("journal_ref"),
                    "doi": paper.get("doi")
                }
            }
            all_papers_data.append(paper_data)

        # 2. BioRxiv 크롤링 (실제)
        all_papers_data.extend(fetch_biorxiv_papers(max_results=3)) # 3개 논문 크롤링

        # 3. PMC 크롤링 (실제)
        all_papers_data.extend(fetch_pmc_papers(max_results=3))

        # 4. PLOS 크롤링 (실제)
        all_papers_data.extend(fetch_plos_papers(max_results=3))

        # 5. DOAJ 크롤링 (실제)
        # all_papers_data.extend(fetch_doaj_papers(max_results=3)) # 3개 논문 크롤링

        save_papers_to_db(all_papers_data)

        print("저장된 논문 조회 및 출력...")
        retrieved_papers = db.query(Paper).all()

        output_filename = "crawled_papers.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            for i, paper in enumerate(retrieved_papers):
                # Paper 객체를 딕셔너리로 변환하여 JSON 직렬화 가능하도록 준비
                paper_dict = {
                    "paper_id": paper.paper_id,
                    "external_id": paper.external_id,
                    "platform": paper.platform,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "categories": paper.categories,
                    "pdf_url": paper.pdf_url,
                    # "embedding": paper.embedding, # 임베딩은 목록이므로 직접 직렬화 가능 (출력에서 제외)
                    "published_date": paper.published_date.isoformat() if paper.published_date else None,
                    "updated_date": paper.updated_date.isoformat() if paper.updated_date else None,
                    "platform_metadata": paper.platform_metadata
                }
                # JSON Pretty Print 및 파일에 쓰기
                f.write(json.dumps(paper_dict, indent=4, ensure_ascii=False))
                f.write("\n" + "="*80 + "\n") # 구분선

        print(f"총 논문 수: {len(retrieved_papers)}개. 결과는 {output_filename} 파일에 저장되었습니다.")

    except Exception as e:
        db.rollback()
        print(f"테스트 중 오류 발생: {e}")
        logger.error(f"Error during multi-platform crawling test: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    print("스크립트의 메인 블록이 실행됩니다.")
    run_multi_platform_crawler_test() 