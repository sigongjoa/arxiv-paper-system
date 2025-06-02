import { executeQuery } from '../config/database';

export interface Post {
  id: number;
  user_id: number;
  title: string;
  content: string;
  category: string;
  created_at: Date;
  updated_at: Date;
  upvotes: number;
  downvotes: number;
  is_published: boolean;
}

export interface PostWithUser extends Post {
  username: string;
  trust_level: string;
  comment_count: number;
}

export class PostModel {
  static async create(postData: {
    user_id: number;
    title: string;
    content: string;
    category: string;
  }): Promise<Post> {
    const { user_id, title, content, category } = postData;
    
    const query = `
      INSERT INTO posts (user_id, title, content, category, is_published, upvotes, downvotes)
      VALUES (?, ?, ?, ?, 1, 0, 0)
    `;
    
    const result = await executeQuery(query, [user_id, title, content, category]);
    const postId = (result as any).lastID;
    const post = await this.findById(postId);
    if (!post) throw new Error('Failed to create post');
    return post;
  }

  static async findAll(
    page: number = 1,
    pageSize: number = 10,
    search?: string,
    category?: string
  ): Promise<{ posts: PostWithUser[]; total: number }> {
    let whereClause = 'WHERE p.is_published = 1';
    const params: any[] = [];
    
    if (search) {
      whereClause += ' AND (p.title LIKE ? OR p.content LIKE ?)';
      const searchParam = `%${search}%`;
      params.push(searchParam, searchParam);
    }
    
    if (category) {
      whereClause += ' AND p.category = ?';
      params.push(category);
    }
    
    const offset = (page - 1) * pageSize;
    
    const countQuery = `
      SELECT COUNT(*) as total
      FROM posts p
      JOIN users u ON p.user_id = u.id
      ${whereClause}
    `;
    
    const query = `
      SELECT 
        p.*,
        u.username,
        u.trust_level,
        COALESCE(comment_counts.count, 0) as comment_count,
        COALESCE(upvote_counts.count, 0) as upvotes,
        COALESCE(downvote_counts.count, 0) as downvotes
      FROM posts p
      JOIN users u ON p.user_id = u.id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM comments 
        WHERE is_approved = 1 
        GROUP BY post_id
      ) comment_counts ON p.id = comment_counts.post_id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM votes 
        WHERE vote_type = 'up'
        GROUP BY post_id
      ) upvote_counts ON p.id = upvote_counts.post_id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM votes 
        WHERE vote_type = 'down'
        GROUP BY post_id
      ) downvote_counts ON p.id = downvote_counts.post_id
      ${whereClause}
      ORDER BY p.created_at DESC
      LIMIT ? OFFSET ?
    `;
    
    const [totalResult, posts] = await Promise.all([
      executeQuery(countQuery, params),
      executeQuery(query, [...params, pageSize, offset])
    ]);
    
    return {
      posts,
      total: totalResult[0].total
    };
  }

  static async findById(id: number): Promise<Post | null> {
    const query = 'SELECT * FROM posts WHERE id = ? AND is_published = 1';
    const result = await executeQuery(query, [id]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async findByIdWithUser(id: number): Promise<PostWithUser | null> {
    const query = `
      SELECT 
        p.*,
        u.username,
        u.trust_level,
        COALESCE(comment_counts.count, 0) as comment_count,
        COALESCE(upvote_counts.count, 0) as upvotes,
        COALESCE(downvote_counts.count, 0) as downvotes
      FROM posts p
      JOIN users u ON p.user_id = u.id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM comments 
        WHERE is_approved = 1 
        GROUP BY post_id
      ) comment_counts ON p.id = comment_counts.post_id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM votes 
        WHERE vote_type = 'up'
        GROUP BY post_id
      ) upvote_counts ON p.id = upvote_counts.post_id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM votes 
        WHERE vote_type = 'down'
        GROUP BY post_id
      ) downvote_counts ON p.id = downvote_counts.post_id
      WHERE p.id = ? AND p.is_published = 1
    `;
    
    const result = await executeQuery(query, [id]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async updateVotes(id: number, upvotes: number, downvotes: number): Promise<Post> {
    const query = `UPDATE posts SET upvotes = ?, downvotes = ? WHERE id = ?`;
    await executeQuery(query, [upvotes, downvotes, id]);
    const post = await this.findById(id);
    if (!post) throw new Error('Post not found');
    return post;
  }

  static async delete(id: number, userId: number): Promise<boolean> {
    const query = `UPDATE posts SET is_published = 0 WHERE id = ? AND user_id = ?`;
    const result = await executeQuery(query, [id, userId]);
    return (result as any).changes > 0;
  }

  static async findByUserId(userId: number, page: number = 1, pageSize: number = 10): Promise<PostWithUser[]> {
    const offset = (page - 1) * pageSize;
    
    const query = `
      SELECT 
        p.*,
        u.username,
        u.trust_level,
        COALESCE(comment_counts.count, 0) as comment_count
      FROM posts p
      JOIN users u ON p.user_id = u.id
      LEFT JOIN (
        SELECT post_id, COUNT(*) as count 
        FROM comments 
        WHERE is_approved = 1 
        GROUP BY post_id
      ) comment_counts ON p.id = comment_counts.post_id
      WHERE p.user_id = ? AND p.is_published = 1
      ORDER BY p.created_at DESC
      LIMIT ? OFFSET ?
    `;
    
    const result = await executeQuery(query, [userId, pageSize, offset]);
    return result;
  }
}
