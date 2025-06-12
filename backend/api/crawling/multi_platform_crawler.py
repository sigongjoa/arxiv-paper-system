import logging
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import uuid
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin # For DOAJ urljoin

from core.models import Paper
from db.connection import SessionLocal

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def save_papers_to_db(papers_data: list):
    """Save fetched papers to the database."""
    session = SessionLocal()
    try:
        saved_count = 0
        skipped_count = 0
        for data in papers_data:
            existing_paper = session.query(Paper).filter_by(paper_id=data['paper_id']).first()
            if existing_paper:
                logger.info(f"Paper with ID {data['paper_id']} already exists. Skipping.")
                skipped_count += 1
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
            )
            session.add(new_paper)
            saved_count += 1
        session.commit()
        logger.info(f"Successfully processed {len(papers_data)} papers. Saved {saved_count} new papers, Skipped {skipped_count} existing papers to the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving papers to database: {e}", exc_info=True)
    finally:
        session.close()

def fetch_arxiv_papers(query: str, max_results: int = 2) -> list:
    """Fetch papers from arXiv API based on a query."""
    params = {
        "search_query": query,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
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

def fetch_biorxiv_papers(query: str, max_results: int = 2) -> list:
    logger.info(f"BioRxiv 논문 크롤링 시작 (API). query='{query}', max_results={max_results}")
    papers_data = []

    BIORXIV_API_BASE_URL = "https://api.biorxiv.org/details/"
    SERVER = "biorxiv" # 또는 medrxiv

    # 쿼리 매개변수 설정
    # BioRxiv API는 직접적인 텍스트 검색 쿼리를 지원하지 않고,
    # 카테고리 또는 날짜 범위로만 필터링을 지원합니다.
    # 여기서는 'query'를 카테고리 필터로 사용합니다.
    # "all"이거나 빈 문자열이면 모든 카테고리를 대상으로 합니다.
    category_param = ""
    if query and query.lower() != 'all' and query.lower() != 'paper':
        # 카테고리 이름에 공백이 있으면 밑줄로 대체해야 합니다.
        # 여러 카테고리가 ' OR '로 연결되어 있을 수 있으므로 분리하여 처리
        categories_for_api = [cat.replace(' ', '_') for cat in query.split(' OR ')]
        category_param = f"&category={'+'.join(categories_for_api)}"

    try:
        # BioRxiv API는 'N'개 최신 논문을 가져오는 대신, 'N'일 전부터의 논문을 가져오거나
        # 날짜 범위로 가져오는 방식이 더 유연합니다.
        # 여기서는 가장 최근 논문 'N'개를 가져오기 위해 간단히 limit을 사용하고,
        # API의 페이지네이션 한계(100개)를 고려해야 합니다.
        # 현재는 한 번의 API 호출로 limit을 충족하는 것으로 가정합니다.

        # 가장 최근 'max_results'개 논문을 가져오기 위한 API 호출
        # BioRxiv API는 max_results를 직접 지원하지 않고, cursor를 통해 페이지네이션을 처리합니다.
        # 여기서는 간단하게 'N'개의 최신 논문을 가져오는 엔드포인트를 사용합니다.
        # 실제로는 'cursor'와 'interval'을 사용하여 더 많은 논문을 가져와야 합니다.
        
        # BioRxiv API documentation: https://api.biorxiv.org/
        # Endpoint: https://api.biorxiv.org/details/[server]/[interval]/[cursor]/[format]
        # [interval] can be a numeric value for the N most recent posts.
        
        url = f"{BIORXIV_API_BASE_URL}{SERVER}/{max_results}/0/json{category_param}"
        
        logger.info(f"BioRxiv API URL: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status() # HTTP 오류 발생 시 예외 처리

        data = response.json()
        
        if 'collection' in data and data['collection']:
            for item in data['collection']:
                paper_id = f"biorxiv_{item.get('doi', '').replace('/', '_')}"
                title = item.get('title', 'No Title Provided').strip()
                abstract = item.get('abstract', 'No Abstract Provided').strip()
                
                authors_str = item.get('authors', '')
                authors = [author.strip() for author in authors_str.split(';') if author.strip()] if authors_str else []

                category = item.get('category', '').strip()
                categories = [category] if category else []

                published_date_str = item.get('date', '')
                published_date = datetime.strptime(published_date_str, '%Y-%m-%d') if published_date_str else datetime.now()
                
                # BioRxiv API는 updated_date를 직접 제공하지 않을 수 있습니다.
                updated_date = published_date # 임시로 published_date와 동일하게 설정

                # PDF URL 구성 (DOI 기반)
                doi_parts = item.get('doi', '').split('/')
                pdf_url = f"https://www.biorxiv.org/content/10.1101/{doi_parts[-1]}.full.pdf" if len(doi_parts) > 1 else "N/A_PDF_URL"
                
                papers_data.append({
                    "paper_id": paper_id,
                    "external_id": item.get('doi', ''),
                    "platform": "biorxiv",
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "categories": categories,
                    "pdf_url": pdf_url,
                    "embedding": [0.0] * 10, # Mock embedding
                    "published_date": published_date,
                    "updated_date": updated_date,
                    "platform_metadata": {"doi": item.get('doi', '')}
                })
                logger.info(f"BioRxiv: Yielding paper: {title[:50]}...")
        else:
            logger.info("BioRxiv API 응답에 'collection' 키가 없거나 비어 있습니다.")

    except requests.exceptions.RequestException as e:
        logger.error(f"BioRxiv API 요청 오류: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"BioRxiv API 응답 JSON 파싱 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"BioRxiv 크롤링 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return []

    logger.info(f"BioRxiv: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_pmc_papers(query: str, max_results: int = 2) -> list:
    logger.info(f"PMC 논문 크롤링 시작 (API). query='{query}', max_results={max_results}")
    papers_data = []
    
    EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    DB = "pmc"
    TOOL_NAME = "PaperPulse" # Replace with your application's name
    EMAIL = "your.email@example.com" # Replace with your email

    try:
        # Step 1: ESearch - Get PMC IDs based on query
        esearch_url = f"{EUTILS_BASE_URL}esearch.fcgi"
        esearch_params = {
            "db": DB,
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "tool": TOOL_NAME,
            "email": EMAIL,
            "sort": "pub_date",
            "sortOrder": "desc"
        }
        
        logger.info(f"PMC ESearch URL: {esearch_url}, Params: {esearch_params}")
        esearch_response = requests.get(esearch_url, params=esearch_params, timeout=60)
        esearch_response.raise_for_status()
        
        esearch_root = ET.fromstring(esearch_response.content)
        pmc_ids = [id_tag.text for id_tag in esearch_root.findall(".//IdList/Id")]
        
        if not pmc_ids:
            logger.info("PMC ESearch에서 논문 ID를 찾을 수 없습니다.")
            return []

        logger.info(f"PMC ESearch에서 {len(pmc_ids)}개 논문 ID 가져옴: {pmc_ids}")

        # Step 2: EFetch - Get full details for each PMC ID
        efetch_url = f"{EUTILS_BASE_URL}efetch.fcgi"
        efetch_params = {
            "db": DB,
            "id": ",".join(pmc_ids),
            "retmode": "xml", # Request XML format
            "rettype": "full", # Request full record
            "tool": TOOL_NAME,
            "email": EMAIL
        }

        logger.info(f"PMC EFetch URL: {efetch_url}, Params: {efetch_params}")
        efetch_response = requests.get(efetch_url, params=efetch_params, timeout=60)
        efetch_response.raise_for_status()

        efetch_root = ET.fromstring(efetch_response.content)

        # Parse EFetch XML response
        # PMC XML 구조는 복잡할 수 있으므로, 필요한 정보만 추출하도록 파싱 로직을 구현합니다.
        # 이 예시에서는 간단한 구조를 가정하고, 실제 PMC XML에 맞게 조정해야 합니다.
        # 일반적인 PMC XML 구조 예시: <article><front><article-meta><title-group><article-title>
        # 저자: <contrib-group><contrib><name>
        # 초록: <abstract>
        # PDF URL은 직접 구성해야 할 수 있습니다.

        for article_tag in efetch_root.findall(".//article"):
            try:
                title_tag = article_tag.find(".//article-title")
                title = title_tag.text.strip() if title_tag is not None and title_tag.text else "N/A Title"

                abstract_tag = article_tag.find(".//abstract")
                abstract = ""
                if abstract_tag is not None:
                    # Abstract can have multiple paragraphs or other tags
                    for p_tag in abstract_tag.findall(".//p"):
                        if p_tag.text:
                            abstract += p_tag.text.strip() + "\n"
                    abstract = abstract.strip() if abstract else "N/A Abstract"


                authors_list = []
                for author_tag in article_tag.findall(".//contrib-group/contrib/name"):
                    surname_tag = author_tag.find("surname")
                    given_names_tag = author_tag.find("given-names")
                    
                    author_name = ""
                    if given_names_tag is not None and given_names_tag.text:
                        author_name += given_names_tag.text.strip()
                    if surname_tag is not None and surname_tag.text:
                        if author_name:
                            author_name += " "
                        author_name += surname_tag.text.strip()
                    
                    if author_name:
                        authors_list.append(author_name)
                authors = authors_list if authors_list else ["N/A Author"]

                # Extracting PMC ID (assuming it's available within the article tag or passed from ESearch)
                # The PMC ID is usually in the <article-id pub-id-type="pmc"> tag
                pmc_id_tag = article_tag.find(".//article-id[@pub-id-type='pmc']")
                pmc_id = pmc_id_tag.text.strip() if pmc_id_tag is not None and pmc_id_tag.text else "N/A_PMC_ID"

                # Categories might be in <article-categories> or similar. This is a simplified example.
                categories = ["Medicine", "Public Health"] # Default categories, needs more robust parsing

                # PDF URL construction based on PMC ID
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/" if pmc_id != "N/A_PMC_ID" else "N/A_PDF_URL"

                # Published Date - usually in <pub-date>
                pub_date_tag = article_tag.find(".//pub-date")
                published_date = None
                if pub_date_tag is not None:
                    year_tag = pub_date_tag.find("year")
                    month_tag = pub_date_tag.find("month")
                    day_tag = pub_date_tag.find("day")

                    try:
                        year = int(year_tag.text.strip()) if year_tag is not None and year_tag.text else None
                        month = int(month_tag.text.strip()) if month_tag is not None and month_tag.text else 1
                        day = int(day_tag.text.strip()) if day_tag is not None and day_tag.text else 1

                        # 유효한 날짜인지 확인
                        if year is not None:
                            # 월 또는 일이 없는 경우, 1월 1일로 설정
                            if month is None: month = 1
                            if day is None: day = 1
                            published_date = datetime(year, month, day)
                        else:
                            logger.warning("PMC: pub-date 태그에서 유효한 연도 정보를 찾을 수 없습니다. 날짜를 None으로 설정합니다.")

                    except (ValueError, TypeError) as e:
                        logger.warning(f"PMC: 날짜 파싱 오류 발생. 날짜를 None으로 설정합니다. 원본 XML: {ET.tostring(pub_date_tag, encoding='unicode') if pub_date_tag is not None else 'N/A'}. 오류: {e}", exc_info=True)

                updated_date = None # PMC XML에서는 명확한 업데이트 날짜를 찾기 어려우므로 기본값은 None으로 설정

                papers_data.append({
                    "paper_id": f"pmc_{pmc_id}",
                    "external_id": pmc_id,
                    "platform": "pmc",
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "categories": categories,
                    "pdf_url": pdf_url,
                    "embedding": [0.0] * 10, # Mock embedding
                    "published_date": published_date,
                    "updated_date": updated_date,
                    "platform_metadata": {"pmc_id": pmc_id}
                })
                logger.info(f"PMC: 논문 처리 중: {title[:50]}...")

            except Exception as e:
                logger.error(f"PMC 논문 파싱 오류: {e}", exc_info=True)
                papers_data.append({
                    "paper_id": f"pmc_{uuid.uuid4().hex[:10]}",
                    "external_id": "N/A",
                    "platform": "pmc",
                    "title": "PMC Paper (Parsing Error)",
                    "abstract": "Error during parsing.",
                    "authors": [],
                    "categories": [],
                    "pdf_url": "http://error.pmc.org/mock.pdf",
                    "embedding": [0.0] * 10,
                    "published_date": None,
                    "updated_date": None,
                    "platform_metadata": {"error": str(e)}
                })

    except requests.exceptions.RequestException as e:
        logger.error(f"PMC API 요청 오류: {e}")
        return []
    except ET.ParseError as e:
        logger.error(f"PMC XML 파싱 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"PMC 크롤링 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return []

    logger.info(f"PMC: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_plos_papers(query: str, max_results: int = 2) -> list:
    logger.info(f"PLOS 논문 크롤링 시작 (API). query='{query}', max_results={max_results}")
    papers_data = []

    PLOS_API_BASE_URL = "http://api.plos.org/search"

    # PLOS API 쿼리 매개변수 설정
    # PLOS API는 Solr 쿼리 문법을 사용합니다.
    # https://api.plos.org/solr/examples/
    # query는 common_query에서 오므로, 일반 검색어나 카테고리 목록일 수 있습니다.
    solr_query_terms = []
    if query.lower() == 'all' or query.lower() == 'paper':
        solr_query_terms.append("*:*") # 모든 문서 검색
    else:
        # 카테고리 또는 키워드를 OR로 연결된 검색 쿼리로 변환
        keywords = [k.strip() for k in query.split(' OR ') if k.strip()]
        for keyword in keywords:
            # 제목 또는 초록에서 키워드 검색
            solr_query_terms.append(f'title:"{keyword}" OR abstract:"{keyword}"')

    params = {
        "q": " AND ".join(solr_query_terms) if solr_query_terms else "*:*", # 검색 쿼리
        "wt": "json", # JSON 형식 응답 요청
        "rows": min(max_results, 100), # 최대 100개 결과 제한 (API 제한)
        "fl": "id,title,abstract,author,journal,publication_date,article_type,pmcid,doi", # 필요한 필드만 요청
        "sort": "publication_date desc" # 최신순으로 정렬
    }
    
    # PLOS API는 날짜 범위 검색을 pub_date 필드를 사용하여 다음과 같이 할 수 있습니다.
    # 예를 들어, 지난 1년 내 논문: "q=publication_date:[NOW-1YEAR/DAY TO NOW/DAY]"
    # 현재는 날짜 제한이 없으므로 추가하지 않습니다.

    try:
        logger.info(f"PLOS API URL: {PLOS_API_BASE_URL}, Params: {params}")
        response = requests.get(PLOS_API_BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        docs = data.get('response', {}).get('docs', [])
        for doc in docs:
            paper_id = doc.get('id')
            title = doc.get('title', 'N/A Title')
            abstract = doc.get('abstract', 'N/A Abstract')
            authors_list = doc.get('author', []) # PLOS API는 저자 리스트를 반환
            authors = [author.get('literal') for author in authors_list if author.get('literal')] if authors_list else ['N/A Author']
            
            # Categories can be inferred from article_type or other fields
            categories = [doc.get('article_type')] if doc.get('article_type') else []

            # PLOS API provides 'publication_date' in ISO 8601 format
            published_date_str = doc.get('publication_date')
            published_date = None
            if published_date_str:
                try:
                    published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"PLOS: 날짜 파싱 오류 발생. '{published_date_str}'. 날짜를 None으로 설정합니다.", exc_info=True)

            updated_date = published_date # PLOS API는 별도의 업데이트 날짜를 제공하지 않으므로 발행일을 사용

            # PDF URL은 직접 구성해야 할 수 있습니다. PLOS는 DOI를 기반으로 PDF URL을 제공합니다.
            doi = doc.get('doi')
            pdf_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable" if doi else "N/A_PDF_URL"
            
            papers_data.append({
                "paper_id": f"plos_{paper_id}",
                "external_id": paper_id,
                "platform": "plos",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding
                "published_date": published_date,
                "updated_date": updated_date,
                "platform_metadata": {"doi": doi}
            })
            logger.info(f"PLOS: 논문 처리 중: {title[:50]}...")

    except requests.exceptions.RequestException as e:
        logger.error(f"PLOS API 요청 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"PLOS 크롤링 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return []

    logger.info(f"PLOS: {len(papers_data)}개 논문 처리 완료.")
    return papers_data

def fetch_doaj_papers(query: str, max_results: int = 2) -> list:
    logger.info(f"DOAJ 논문 크롤링 시작 (API). query='{query}', max_results={max_results}")
    papers_data = []

    DOAJ_API_BASE_URL = "https://doaj.org/api/v1/search/articles"

    # DOAJ API 쿼리 매개변수 설정 (Elasticsearch 쿼리 문법)
    # https://doaj.org/docs/faq/ (Searching the Directory of Open Access Journals (DOAJ))
    doaj_query_terms = []
    if query.lower() == 'all' or query.lower() == 'paper':
        doaj_query_terms.append("*") # 모든 문서 검색
    else:
        # 카테고리 또는 키워드를 OR로 연결된 검색 쿼리로 변환
        keywords = [k.strip() for k in query.split(' OR ') if k.strip()]
        for keyword in keywords:
            # 제목 또는 초록에서 키워드 검색
            # DOAJ는 Elasticsearch 쿼리 문법을 사용하며, 필드 검색이 가능합니다.
            doaj_query_terms.append(f'title:"{keyword}" OR bibjson.abstract:"{keyword}" OR bibjson.keywords:"{keyword}"')

    # DOAJ API는 'query' 파라미터에 Elasticsearch 쿼리 문자열을 받습니다.
    # 'pageSize'는 반환할 결과의 최대 수를 지정합니다.
    params = {
        "query": " AND ".join(doaj_query_terms) if doaj_query_terms else "*",
        "pageSize": min(max_results, 1000), # DOAJ API는 최대 1000개 결과 제한
        "sort": "journal.publication_start_date:desc" # 최신순으로 정렬
    }

    try:
        logger.info(f"DOAJ API URL: {DOAJ_API_BASE_URL}, Params: {params}")
        response = requests.get(DOAJ_API_BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        # DOAJ API 응답은 'results' 배열 안에 각 논문의 'bibjson' 객체를 포함합니다.
        results = data.get('results', [])
        for item in results:
            bibjson = item.get('bibjson', {})
            
            paper_id = item.get('id')
            title = bibjson.get('title', 'N/A Title')
            abstract = bibjson.get('abstract', 'N/A Abstract')

            authors_list = bibjson.get('author', [])
            authors = [author.get('name', 'N/A Author') for author in authors_list] if authors_list else ['N/A Author']

            # Categories are usually in 'keywords' field
            categories = bibjson.get('keywords', [])

            # PDF URL can be found in 'link' field with 'type': 'fulltext' or 'pdf'
            pdf_url = "N/A_PDF_URL"
            for link in bibjson.get('link', []):
                if link.get('type') == 'fulltext' or link.get('type') == 'pdf':
                    pdf_url = link.get('url', 'N/A_PDF_URL')
                    break
            
            # Published Date - DOAJ provides year, month, day in 'journal.publication'
            published_date = None
            journal_pub = bibjson.get('journal', {}).get('publication_start_date')
            if journal_pub:
                try:
                    published_date = datetime.strptime(journal_pub, '%Y-%m-%d')
                except ValueError:
                    # Try parsing only year if full date fails
                    try:
                        published_date = datetime.strptime(journal_pub[:4], '%Y')
                        logger.warning(f"DOAJ: 전체 날짜 파싱 오류, 연도만 파싱합니다: {journal_pub}")
                    except ValueError:
                        logger.warning(f"DOAJ: 날짜 파싱 오류 발생. '{journal_pub}'. 날짜를 None으로 설정합니다.", exc_info=True)

            updated_date = None # DOAJ API는 별도의 업데이트 날짜를 제공하지 않으므로 None으로 설정

            papers_data.append({
                "paper_id": f"doaj_{paper_id}",
                "external_id": paper_id,
                "platform": "doaj",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "pdf_url": pdf_url,
                "embedding": [0.0] * 10, # Mock embedding
                "published_date": published_date,
                "updated_date": updated_date,
                "platform_metadata": {"doi": bibjson.get('identifier', {}).get('doi', 'N/A')}
            })
            logger.info(f"DOAJ: 논문 처리 중: {title[:50]}...")

    except requests.exceptions.RequestException as e:
        logger.error(f"DOAJ API 요청 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"DOAJ 크롤링 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return []

    logger.info(f"DOAJ: {len(papers_data)}개 논문 처리 완료.")
    return papers_data