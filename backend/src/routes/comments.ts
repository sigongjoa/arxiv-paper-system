import express from 'express';
import { CommentModel } from '../models/Comment';
import { UserModel } from '../models/User';
import { authenticateToken, optionalAuth } from '../middleware/auth';
import { commentLimiter } from '../middleware/rateLimiter';

const router = express.Router();

// 댓글 작성
router.post('/', authenticateToken, commentLimiter, async (req, res) => {
  try {
    const { post_id, content, parent_comment_id } = req.body;
    const userId = req.user!.userId;

    if (!post_id || !content) {
      return res.status(400).json({ error: 'Post ID and content are required' });
    }

    if (content.trim().length === 0) {
      return res.status(400).json({ error: 'Comment content cannot be empty' });
    }

    if (content.length > 2000) {
      return res.status(400).json({ error: 'Comment is too long (max 2000 characters)' });
    }

    const user = await UserModel.findById(userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const comment = await CommentModel.create({
      user_id: userId,
      post_id,
      content: content.trim(),
      trust_level: user.trust_level
    });

    res.status(201).json({
      success: true,
      comment: {
        id: comment.id,
        user_id: comment.user_id,
        post_id: comment.post_id,
        content: comment.content,
        is_approved: comment.is_approved,
        created_at: comment.created_at
      },
      message: comment.is_approved ? 'Comment posted successfully' : 'Comment submitted for approval'
    });
  } catch (error) {
    console.error('Comment creation error:', error);
    res.status(500).json({ error: 'Failed to create comment' });
  }
});

// 특정 게시글의 댓글 목록 조회
router.get('/post/:postId', optionalAuth, async (req, res) => {
  try {
    const postId = parseInt(req.params.postId);
    const filter = req.query.filter as 'verified_only' | 'all' | 'guest_only' || 'all';
    const page = parseInt(req.query.page as string) || 1;
    const pageSize = Math.min(parseInt(req.query.page_size as string) || 20, 100);

    if (isNaN(postId)) {
      return res.status(400).json({ error: 'Invalid post ID' });
    }

    const comments = await CommentModel.findByPostId(postId, filter, page, pageSize);
    const totalCount = await CommentModel.countByPostId(postId, filter);

    res.json({
      success: true,
      comments: comments.map(comment => ({
        id: comment.id,
        user_id: comment.user_id,
        username: comment.username,
        content: comment.content,
        trust_level: comment.trust_level,
        created_at: comment.created_at,
        is_approved: comment.is_approved
      })),
      pagination: {
        page,
        pageSize,
        totalCount,
        totalPages: Math.ceil(totalCount / pageSize)
      },
      filter
    });
  } catch (error) {
    console.error('Comments fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch comments' });
  }
});

// 특정 댓글 조회
router.get('/:commentId', async (req, res) => {
  try {
    const commentId = parseInt(req.params.commentId);

    if (isNaN(commentId)) {
      return res.status(400).json({ error: 'Invalid comment ID' });
    }

    const comment = await CommentModel.findById(commentId);

    if (!comment) {
      return res.status(404).json({ error: 'Comment not found' });
    }

    res.json({
      success: true,
      comment
    });
  } catch (error) {
    console.error('Comment fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch comment' });
  }
});

export default router;
