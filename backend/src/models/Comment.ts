import { executeQuery } from '../config/database';

export interface Comment {
  id: number;
  user_id: number;
  post_id: number;
  content: string;
  created_at: Date;
  is_approved: boolean;
}

export interface CommentWithUser extends Comment {
  username: string;
  trust_level: string;
}

export class CommentModel {
  static async create(commentData: {
    user_id: number;
    post_id: number;
    content: string;
    trust_level: string;
  }): Promise<Comment> {
    const { user_id, post_id, content, trust_level } = commentData;
    
    // 인증된 사용자는 자동 승인, 게스트는 승인 대기
    const is_approved = trust_level !== 'GUEST' ? 1 : 0;
    
    const query = `
      INSERT INTO comments (user_id, post_id, content, is_approved)
      VALUES (?, ?, ?, ?)
    `;
    
    const result = await executeQuery(query, [user_id, post_id, content, is_approved]);
    const commentId = (result as any).lastID;
    const comment = await this.findById(commentId);
    if (!comment) throw new Error('Failed to create comment');
    return comment;
  }

  static async findByPostId(
    postId: number, 
    filter: 'verified_only' | 'all' | 'guest_only' = 'all',
    page: number = 1,
    pageSize: number = 20
  ): Promise<CommentWithUser[]> {
    let whereClause = 'WHERE c.post_id = ?';
    const params: any[] = [postId];
    
    switch (filter) {
      case 'verified_only':
        whereClause += ' AND u.trust_level IN (?, ?, ?) AND c.is_approved = 1';
        params.push('ORCID', 'DOI', 'STUDENT');
        break;
      case 'guest_only':
        whereClause += ' AND u.trust_level = ?';
        params.push('GUEST');
        break;
      case 'all':
        whereClause += ' AND c.is_approved = 1';
        break;
    }
    
    const offset = (page - 1) * pageSize;
    
    const query = `
      SELECT 
        c.*,
        u.username,
        u.trust_level
      FROM comments c
      JOIN users u ON c.user_id = u.id
      ${whereClause}
      ORDER BY c.created_at DESC
      LIMIT ? OFFSET ?
    `;
    
    const result = await executeQuery(query, [...params, pageSize, offset]);
    return result;
  }

  static async findById(id: number): Promise<Comment | null> {
    const query = 'SELECT * FROM comments WHERE id = ?';
    const result = await executeQuery(query, [id]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async approve(id: number): Promise<Comment> {
    const query = `UPDATE comments SET is_approved = 1 WHERE id = ?`;
    await executeQuery(query, [id]);
    const comment = await this.findById(id);
    if (!comment) throw new Error('Comment not found');
    return comment;
  }

  static async countByPostId(postId: number, filter: 'verified_only' | 'all' | 'guest_only' = 'all'): Promise<number> {
    let whereClause = 'WHERE c.post_id = ?';
    const params: any[] = [postId];
    
    switch (filter) {
      case 'verified_only':
        whereClause += ' AND u.trust_level IN (?, ?, ?) AND c.is_approved = 1';
        params.push('ORCID', 'DOI', 'STUDENT');
        break;
      case 'guest_only':
        whereClause += ' AND u.trust_level = ?';
        params.push('GUEST');
        break;
      case 'all':
        whereClause += ' AND c.is_approved = 1';
        break;
    }
    
    const query = `
      SELECT COUNT(*) as count 
      FROM comments c
      JOIN users u ON c.user_id = u.id
      ${whereClause}
    `;
    const result = await executeQuery(query, params);
    return parseInt(result[0].count);
  }

  static async getPendingGuestComments(): Promise<CommentWithUser[]> {
    const query = `
      SELECT 
        c.*,
        u.username,
        u.trust_level
      FROM comments c
      JOIN users u ON c.user_id = u.id
      WHERE u.trust_level = 'GUEST' AND c.is_approved = 0
      ORDER BY c.created_at ASC
    `;
    
    const result = await executeQuery(query);
    return result;
  }
}
