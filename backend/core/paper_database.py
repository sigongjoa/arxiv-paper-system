import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from .models import Paper

class PaperDatabase:
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """데이터베이스 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
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
        
        conn.commit()
        conn.close()
    
    def save_paper(self, paper: Paper) -> bool:
        """논문 저장, 중복시 False 반환"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """arXiv ID로 논문 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM papers WHERE arxiv_id = ?', (arxiv_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_paper(row)
        return None
    
    def get_papers_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[Paper]:
        """날짜 범위로 논문 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"DEBUG: DB query range: {start_date.isoformat()} to {end_date.isoformat()}")
        
        cursor.execute('''
            SELECT * FROM papers 
            WHERE updated_date BETWEEN ? AND ? 
            ORDER BY updated_date DESC 
            LIMIT ?
        ''', (start_date.isoformat(), end_date.isoformat(), limit))
        
        rows = cursor.fetchall()
        print(f"DEBUG: DB returned {len(rows)} papers")
        
        # 전체 논문 수도 확인
        cursor.execute('SELECT COUNT(*) FROM papers')
        total_count = cursor.fetchone()[0]
        print(f"DEBUG: Total papers in DB: {total_count}")
        
        # 최근 3개 논문의 날짜 확인
        cursor.execute('SELECT arxiv_id, updated_date FROM papers ORDER BY updated_date DESC LIMIT 3')
        recent = cursor.fetchall()
        print(f"DEBUG: Recent papers: {recent}")
        
        conn.close()
        
        return [self._row_to_paper(row) for row in rows]
    
    def search_papers(self, query: str, category: str = None, limit: int = 100) -> List[Paper]:
        """제목/초록으로 논문 검색"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM papers WHERE (title LIKE ? OR abstract LIKE ?)'
        params = [f'%{query}%', f'%{query}%']
        
        if category:
            sql += ' AND categories LIKE ?'
            params.append(f'%{category}%')
        
        sql += ' ORDER BY updated_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_paper(row) for row in rows]
    
    def get_total_count(self) -> int:
        """총 논문 수"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM papers')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def _row_to_paper(self, row) -> Paper:
        """DB row를 Paper 객체로 변환"""
        return Paper(
            arxiv_id=row[1],
            title=row[2],
            abstract=row[3],
            authors=json.loads(row[4]) if row[4] else [],
            categories=json.loads(row[5]) if row[5] else [],
            pdf_url=row[6],
            published_date=datetime.fromisoformat(row[7]),
            updated_date=datetime.fromisoformat(row[8])
        )
