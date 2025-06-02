import Database from 'sqlite3';
import path from 'path';

// SQLite 데이터베이스 파일 경로
const DB_PATH = path.join(__dirname, '../../data/paper_shorts_auth.db');

// 데이터베이스 인스턴스
const db = new Database.Database(DB_PATH);

export const executeQuery = async (query: string, params: any[] = []): Promise<any> => {
  return new Promise((resolve, reject) => {
    console.log('Executing query:', query, 'with params:', params);
    
    if (query.trim().toLowerCase().startsWith('select')) {
      db.all(query, params, (err, rows) => {
        if (err) {
          console.error('Database query error:', err);
          reject(err);
        } else {
          resolve(rows);
        }
      });
    } else {
      db.run(query, params, function(err) {
        if (err) {
          console.error('Database query error:', err);
          reject(err);
        } else {
          resolve({ lastID: this.lastID, changes: this.changes });
        }
      });
    }
  });
};

// 데이터베이스 초기화 - schema.ts에서 가져오기
export const initDatabase = async () => {
  const { createTables } = await import('../migrations/schema');
  await createTables();
};
