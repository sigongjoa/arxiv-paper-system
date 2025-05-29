import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from paper_model import Paper

class PaperDatabase:
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        print(f"DEBUG: Database initialized at {db_path}")
    
    def _create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                authors TEXT,
                categories TEXT,
                pdf_url TEXT,
                published_date TEXT,
                updated_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_arxiv_id ON papers(arxiv_id)
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_published_date ON papers(published_date)
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_categories ON papers(categories)
        ''')
        
        self.conn.commit()
        print("DEBUG: Database tables created/verified")
    
    def save_paper(self, paper: Paper) -> bool:
        cursor = self.conn.cursor()
        
        # Check if paper already exists (more efficient query)
        cursor.execute('SELECT 1 FROM papers WHERE arxiv_id = ? LIMIT 1', (paper.arxiv_id,))
        if cursor.fetchone():
            return False  # Paper already exists
        
        # Insert new paper
        try:
            cursor.execute('''
                INSERT INTO papers (arxiv_id, title, abstract, authors, categories, pdf_url, published_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                paper.arxiv_id,
                paper.title,
                paper.abstract,
                json.dumps(paper.authors),
                json.dumps(paper.categories),
                paper.pdf_url,
                paper.published_date.isoformat(),
                paper.updated_date.isoformat()
            ))
            
            self.conn.commit()
            return True  # New paper saved
            
        except sqlite3.IntegrityError:
            # Handle race condition
            return False
    
    def get_papers_by_category(self, category: str, limit: int = 100) -> List[Paper]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM papers 
            WHERE categories LIKE ? 
            ORDER BY published_date DESC 
            LIMIT ?
        ''', (f'%{category}%', limit))
        
        papers = []
        for row in cursor.fetchall():
            paper = Paper(
                arxiv_id=row['arxiv_id'],
                title=row['title'],
                abstract=row['abstract'],
                authors=json.loads(row['authors']),
                categories=json.loads(row['categories']),
                pdf_url=row['pdf_url'],
                published_date=datetime.fromisoformat(row['published_date']),
                updated_date=datetime.fromisoformat(row['updated_date'])
            )
            papers.append(paper)
        
        print(f"DEBUG: Retrieved {len(papers)} papers for category {category}")
        return papers
    
    def get_papers_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 1000) -> List[Paper]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM papers 
            WHERE published_date BETWEEN ? AND ? 
            ORDER BY published_date DESC 
            LIMIT ?
        ''', (start_date.isoformat(), end_date.isoformat(), limit))
        
        papers = []
        for row in cursor.fetchall():
            paper = Paper(
                arxiv_id=row['arxiv_id'],
                title=row['title'],
                abstract=row['abstract'],
                authors=json.loads(row['authors']),
                categories=json.loads(row['categories']),
                pdf_url=row['pdf_url'],
                published_date=datetime.fromisoformat(row['published_date']),
                updated_date=datetime.fromisoformat(row['updated_date'])
            )
            papers.append(paper)
        
        print(f"DEBUG: Retrieved {len(papers)} papers for date range {start_date.date()} to {end_date.date()}")
        return papers
    
    def get_total_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM papers')
        count = cursor.fetchone()[0]
        print(f"DEBUG: Total papers in database: {count}")
        return count
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM papers WHERE arxiv_id = ?', (arxiv_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"DEBUG: Paper {arxiv_id} not found")
            return None
        
        paper = Paper(
            arxiv_id=row['arxiv_id'],
            title=row['title'],
            abstract=row['abstract'],
            authors=json.loads(row['authors']),
            categories=json.loads(row['categories']),
            pdf_url=row['pdf_url'],
            published_date=datetime.fromisoformat(row['published_date']),
            updated_date=datetime.fromisoformat(row['updated_date'])
        )
        
        print(f"DEBUG: Retrieved paper {arxiv_id}")
        return paper
    
    def search_papers(self, query: str, category: str = None, limit: int = 10) -> List[Paper]:
        cursor = self.conn.cursor()
        
        if category:
            sql = '''
                SELECT * FROM papers 
                WHERE (title LIKE ? OR abstract LIKE ?) AND categories LIKE ?
                ORDER BY published_date DESC 
                LIMIT ?
            '''
            params = (f'%{query}%', f'%{query}%', f'%{category}%', limit)
        else:
            sql = '''
                SELECT * FROM papers 
                WHERE title LIKE ? OR abstract LIKE ?
                ORDER BY published_date DESC 
                LIMIT ?
            '''
            params = (f'%{query}%', f'%{query}%', limit)
        
        cursor.execute(sql, params)
        
        papers = []
        for row in cursor.fetchall():
            paper = Paper(
                arxiv_id=row['arxiv_id'],
                title=row['title'],
                abstract=row['abstract'],
                authors=json.loads(row['authors']),
                categories=json.loads(row['categories']),
                pdf_url=row['pdf_url'],
                published_date=datetime.fromisoformat(row['published_date']),
                updated_date=datetime.fromisoformat(row['updated_date'])
            )
            papers.append(paper)
        
        print(f"DEBUG: Search found {len(papers)} papers for query '{query}'")
        return papers
    
    def close(self):
        self.conn.close()
        print("DEBUG: Database connection closed")
