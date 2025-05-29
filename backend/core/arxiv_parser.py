import xml.etree.ElementTree as ET
from datetime import datetime
import logging

logging.basicConfig(level=logging.ERROR)

class ArxivParser:
    def parse_response(self, xml_content):
        print(f"DEBUG: Parsing XML content, length={len(xml_content)}")
        root = ET.fromstring(xml_content)
        
        entries = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper = self._extract_paper_data(entry)
            entries.append(paper)
            print(f"DEBUG: Parsed paper: {paper['title'][:50]}...")
        
        print(f"DEBUG: Total papers parsed: {len(entries)}")
        return entries
    
    def _extract_paper_data(self, entry):
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
        summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
        
        # arXiv ID 추출
        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
        
        # 저자들
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        
        # 카테고리들
        categories = []
        for category in entry.findall('atom:category', ns):
            categories.append(category.get('term'))
        
        # 발행일
        published = entry.find('atom:published', ns).text
        published_date = datetime.fromisoformat(published.replace('Z', '+00:00')).date()
        
        # PDF URL
        pdf_url = None
        for link in entry.findall('atom:link', ns):
            if link.get('type') == 'application/pdf':
                pdf_url = link.get('href')
                break
        
        return {
            'arxiv_id': arxiv_id,
            'title': title,
            'abstract': summary,
            'authors': authors,
            'categories': categories,
            'published_date': published_date,
            'pdf_url': pdf_url
        }
