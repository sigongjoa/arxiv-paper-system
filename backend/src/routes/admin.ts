import express from 'express';
import { CommentModel } from '../models/Comment';
import { UserModel } from '../models/User';
import { authenticateToken, requireTrustLevel } from '../middleware/auth';

const router = express.Router();

// 관리자 권한 체크 미들웨어 (임시로 ORCID 레벨 이상으로 설정)
const requireAdmin = requireTrustLevel('ORCID');

// 승인 대기 중인 게스트 댓글 목록
router.get('/comments/pending', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const pendingComments = await CommentModel.getPendingGuestComments();

    res.json({
      success: true,
      comments: pendingComments.map(comment => ({
        id: comment.id,
        user_id: comment.user_id,
        username: comment.username,
        post_id: comment.post_id,
        content: comment.content,
        trust_level: comment.trust_level,
        created_at: comment.created_at
      }))
    });
  } catch (error) {
    console.error('Pending comments fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch pending comments' });
  }
});

// 댓글 승인
router.patch('/comments/:commentId/approve', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const commentId = parseInt(req.params.commentId);

    if (isNaN(commentId)) {
      return res.status(400).json({ error: 'Invalid comment ID' });
    }

    const comment = await CommentModel.findById(commentId);
    
    if (!comment) {
      return res.status(404).json({ error: 'Comment not found' });
    }

    if (comment.is_approved) {
      return res.status(400).json({ error: 'Comment is already approved' });
    }

    const approvedComment = await CommentModel.approve(commentId);

    res.json({
      success: true,
      message: 'Comment approved successfully',
      comment: approvedComment
    });
  } catch (error) {
    console.error('Comment approval error:', error);
    res.status(500).json({ error: 'Failed to approve comment' });
  }
});

// 사용자 목록 조회 (관리자용)
router.get('/users', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const pageSize = Math.min(parseInt(req.query.page_size as string) || 20, 100);
    const trustLevel = req.query.trust_level as string;

    const offset = (page - 1) * pageSize;
    let query = `
      SELECT id, username, email, orcid, is_orcid_verified, is_doi_verified, 
             is_student_verified, trust_level, verified_detail, created_at
      FROM users
    `;
    let params: any[] = [];

    if (trustLevel && ['ORCID', 'DOI', 'STUDENT', 'GUEST'].includes(trustLevel)) {
      query += ' WHERE trust_level = ?';
      params.push(trustLevel);
    }

    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(pageSize, offset);

    const { executeQuery } = await import('../config/database');
    const users = await executeQuery(query, params);

    // 총 사용자 수 조회
    let countQuery = 'SELECT COUNT(*) as count FROM users';
    let countParams: any[] = [];
    
    if (trustLevel && ['ORCID', 'DOI', 'STUDENT', 'GUEST'].includes(trustLevel)) {
      countQuery += ' WHERE trust_level = ?';
      countParams.push(trustLevel);
    }

    const countResult = await executeQuery(countQuery, countParams);
    const totalCount = parseInt(countResult[0].count);

    res.json({
      success: true,
      users,
      pagination: {
        page,
        pageSize,
        totalCount,
        totalPages: Math.ceil(totalCount / pageSize)
      }
    });
  } catch (error) {
    console.error('Users fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// 사용자 상세 정보 조회
router.get('/users/:userId', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const userId = parseInt(req.params.userId);

    if (isNaN(userId)) {
      return res.status(400).json({ error: 'Invalid user ID' });
    }

    const user = await UserModel.findById(userId);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        orcid: user.orcid,
        isOrcidVerified: user.is_orcid_verified,
        isDoiVerified: user.is_doi_verified,
        isStudentVerified: user.is_student_verified,
        trustLevel: user.trust_level,
        verifiedDetail: user.verified_detail,
        createdAt: user.created_at,
        updatedAt: user.updated_at
      }
    });
  } catch (error) {
    console.error('User fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

// 시스템 통계 (공개)
router.get('/stats/public', async (req, res) => {
  try {
    const { executeQuery } = await import('../config/database');

    // 사용자 통계
    const totalUsers = await executeQuery('SELECT COUNT(*) as count FROM users');
    const verifiedUsers = await executeQuery(
      'SELECT COUNT(*) as count FROM users WHERE trust_level IN (?, ?, ?)',
      ['ORCID', 'DOI', 'STUDENT']
    );

    // 게시글 통계
    const totalPosts = await executeQuery('SELECT COUNT(*) as count FROM posts WHERE is_published = 1');
    const thisMonthPosts = await executeQuery(`
      SELECT COUNT(*) as count FROM posts 
      WHERE is_published = 1 AND created_at >= date('now', 'start of month')
    `);

    // 댓글 통계
    const totalComments = await executeQuery('SELECT COUNT(*) as count FROM comments WHERE is_approved = 1');

    res.json({
      success: true,
      stats: {
        activeResearchers: parseInt(totalUsers[0].count),
        postsThisMonth: parseInt(thisMonthPosts[0].count),
        totalComments: parseInt(totalComments[0].count),
        verifiedPercentage: Math.round((parseInt(verifiedUsers[0].count) / parseInt(totalUsers[0].count)) * 100)
      }
    });
  } catch (error) {
    console.error('Public stats fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// 시스템 통계
router.get('/stats', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { executeQuery } = await import('../config/database');

    // 사용자 통계
    const userStats = await executeQuery(`
      SELECT 
        trust_level,
        COUNT(*) as count
      FROM users
      GROUP BY trust_level
    `);

    // 댓글 통계
    const commentStats = await executeQuery(`
      SELECT 
        trust_level,
        is_approved,
        COUNT(*) as count
      FROM comments
      GROUP BY trust_level, is_approved
    `);

    // 전체 통계
    const totalUsers = await executeQuery('SELECT COUNT(*) as count FROM users');
    const totalComments = await executeQuery('SELECT COUNT(*) as count FROM comments');
    const pendingComments = await executeQuery('SELECT COUNT(*) as count FROM comments WHERE is_approved = FALSE');

    res.json({
      success: true,
      stats: {
        users: {
          total: parseInt(totalUsers[0].count),
          byTrustLevel: userStats.reduce((acc: any, stat: any) => {
            acc[stat.trust_level] = parseInt(stat.count);
            return acc;
          }, {})
        },
        comments: {
          total: parseInt(totalComments[0].count),
          pending: parseInt(pendingComments[0].count),
          byTrustLevel: commentStats.reduce((acc: any, stat: any) => {
            if (!acc[stat.trust_level]) acc[stat.trust_level] = {};
            acc[stat.trust_level][stat.is_approved ? 'approved' : 'pending'] = parseInt(stat.count);
            return acc;
          }, {})
        }
      }
    });
  } catch (error) {
    console.error('Stats fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

export default router;
