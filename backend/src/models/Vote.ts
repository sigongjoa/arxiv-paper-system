import { executeQuery } from '../config/database';

export interface Vote {
  id: number;
  user_id: number;
  post_id: number;
  vote_type: 'up' | 'down';
  created_at: Date;
}

export class VoteModel {
  static async createOrUpdate(voteData: {
    user_id: number;
    post_id: number;
    vote_type: 'up' | 'down';
  }): Promise<Vote> {
    const { user_id, post_id, vote_type } = voteData;
    
    // 기존 투표가 있는지 확인
    const existingVote = await executeQuery(
      'SELECT * FROM votes WHERE user_id = ? AND post_id = ?',
      [user_id, post_id]
    );
    
    if (existingVote.length > 0) {
      // 기존 투표가 같은 타입이면 삭제, 다른 타입이면 업데이트
      if (existingVote[0].vote_type === vote_type) {
        await executeQuery(
          'DELETE FROM votes WHERE user_id = ? AND post_id = ?',
          [user_id, post_id]
        );
        return null; // 투표 취소
      } else {
        await executeQuery(
          'UPDATE votes SET vote_type = ? WHERE user_id = ? AND post_id = ?',
          [vote_type, user_id, post_id]
        );
      }
    } else {
      // 새 투표 생성
      await executeQuery(
        'INSERT INTO votes (user_id, post_id, vote_type) VALUES (?, ?, ?)',
        [user_id, post_id, vote_type]
      );
    }
    
    // 업데이트된 투표 반환
    const vote = await executeQuery(
      'SELECT * FROM votes WHERE user_id = ? AND post_id = ?',
      [user_id, post_id]
    );
    
    return vote[0] || null;
  }
  
  static async getPostVoteCounts(post_id: number): Promise<{ upvotes: number; downvotes: number }> {
    const upvotes = await executeQuery(
      'SELECT COUNT(*) as count FROM votes WHERE post_id = ? AND vote_type = ?',
      [post_id, 'up']
    );
    
    const downvotes = await executeQuery(
      'SELECT COUNT(*) as count FROM votes WHERE post_id = ? AND vote_type = ?',
      [post_id, 'down']
    );
    
    return {
      upvotes: parseInt(upvotes[0].count),
      downvotes: parseInt(downvotes[0].count)
    };
  }
  
  static async getUserVote(user_id: number, post_id: number): Promise<Vote | null> {
    const result = await executeQuery(
      'SELECT * FROM votes WHERE user_id = ? AND post_id = ?',
      [user_id, post_id]
    );
    
    return result.length > 0 ? result[0] : null;
  }
}
