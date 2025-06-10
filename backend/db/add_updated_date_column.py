import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'arxiv_papers.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 먼저 NULL 허용으로 컬럼 추가
    cursor.execute('ALTER TABLE papers ADD COLUMN updated_date TEXT;')
    print('updated_date 컬럼을 NULL 허용으로 성공적으로 추가했습니다.')
    
    # 기존 행에 updated_date 값 채우기
    cursor.execute('UPDATE papers SET updated_date = datetime(\'now\') WHERE updated_date IS NULL;')
    print('기존 논문의 updated_date를 현재 시간으로 업데이트했습니다.')
    
    conn.commit()

except sqlite3.OperationalError as e:
    if "duplicate column name: updated_date" in str(e):
        print('오류: updated_date 컬럼이 이미 존재합니다. 스키마 변경이 필요하지 않습니다.')
    else:
        print(f'오류: {e}')
    conn.rollback()
finally:
    conn.close() 