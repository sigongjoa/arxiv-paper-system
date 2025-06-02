import requests
import xml.etree.ElementTree as ET
import logging

class ProcessorImpl:
    def process_arxiv_paper(self, arxiv_id):
        logging.info(f"Starting paper processing for arXiv ID: {arxiv_id}")
        clean_id = arxiv_id.replace('v1', '').replace('v2', '').replace('v3', '')
        
        logging.info(f"Fetching paper data from arXiv API...")
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logging.error(f"arXiv API error: {response.status_code}")
            raise Exception(f"arXiv API error: {response.status_code}")
        
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        if not entries:
            logging.error(f"Paper {arxiv_id} not found")
            raise Exception(f"Paper {arxiv_id} not found in arXiv")
        
        entry = entries[0]
        
        paper_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip()
        abstract = entry.find('atom:summary', ns).text.strip()
        
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        
        categories = []
        for category in entry.findall('atom:category', ns):
            categories.append(category.get('term'))
        
        paper_dict = {
            'arxiv_id': paper_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories
        }
        
        logging.info(f"Successfully processed paper: {title}")
        logging.info(f"Authors: {', '.join(authors)}")
        logging.info(f"Categories: {', '.join(categories)}")
        
        return {
            'paper': paper_dict,
            'summary': abstract,
            'status': 'completed'
        }
