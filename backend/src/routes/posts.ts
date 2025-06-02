import express from 'express';
import { PostModel } from '../models/Post';
import { VoteModel } from '../models/Vote';
import { UserModel } from '../models/User';
import { authenticateToken, optionalAuth } from '../middleware/auth';
import { commentLimiter } from '../middleware/rateLimiter';

const router = express.Router();

// 게시글 작성
router.post('/', authenticateToken, commentLimiter, async (req, res) => {
  try {
    const { title, content, category } = req.body;
    const userId = req.user!.userId;

    if (!title || !content || !category) {
      return res.status(400).json({ error: 'Title, content, and category are required' });
    }

    if (title.trim().length === 0 || content.trim().length === 0) {
      return res.status(400).json({ error: 'Title and content cannot be empty' });
    }

    if (title.length > 200) {
      return res.status(400).json({ error: 'Title is too long (max 200 characters)' });
    }

    if (content.length > 10000) {
      return res.status(400).json({ error: 'Content is too long (max 10000 characters)' });
    }

    const validCategories = ['general', 'tech', 'science', 'discussion', 'question'];
    if (!validCategories.includes(category)) {
      return res.status(400).json({ error: 'Invalid category' });
    }

    const user = await UserModel.findById(userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const post = await PostModel.create({
      user_id: userId,
      title: title.trim(),
      content: content.trim(),
      category
    });

    res.status(201).json({
      success: true,
      post: {
        id: post.id,
        user_id: post.user_id,
        title: post.title,
        content: post.content,
        category: post.category,
        created_at: post.created_at,
        upvotes: post.upvotes,
        downvotes: post.downvotes
      },
      message: 'Post created successfully'
    });
  } catch (error) {
    console.error('Post creation error:', error);
    res.status(500).json({ error: 'Failed to create post' });
  }
});

// 게시글 목록 조회
router.get('/', optionalAuth, async (req, res) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const pageSize = Math.min(parseInt(req.query.page_size as string) || 10, 50);
    const search = req.query.search as string;
    const category = req.query.category as string;

    const { posts, total } = await PostModel.findAll(page, pageSize, search, category);

    res.json({
      success: true,
      posts,
      pagination: {
        page,
        pageSize,
        totalCount: total,
        totalPages: Math.ceil(total / pageSize)
      },
      filters: {
        search: search || null,
        category: category || null
      }
    });
  } catch (error) {
    console.error('Posts fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch posts' });
  }
});

// 특정 게시글 조회
router.get('/:postId', optionalAuth, async (req, res) => {
  try {
    const postId = parseInt(req.params.postId);

    if (isNaN(postId)) {
      return res.status(400).json({ error: 'Invalid post ID' });
    }

    const post = await PostModel.findByIdWithUser(postId);

    if (!post) {
      return res.status(404).json({ error: 'Post not found' });
    }

    res.json({
      success: true,
      post
    });
  } catch (error) {
    console.error('Post fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch post' });
  }
});

// 게시글 투표
router.post('/:postId/vote', authenticateToken, async (req, res) => {
  try {
    const postId = parseInt(req.params.postId);
    const { direction } = req.body; // 'up' or 'down'
    const userId = req.user!.userId;

    if (isNaN(postId)) {
      return res.status(400).json({ error: 'Invalid post ID' });
    }

    if (!['up', 'down'].includes(direction)) {
      return res.status(400).json({ error: 'Invalid vote direction' });
    }

    // 게시글 존재 확인
    const post = await PostModel.findById(postId);
    if (!post) {
      return res.status(404).json({ error: 'Post not found' });
    }

    // 투표 처리
    const vote = await VoteModel.createOrUpdate({
      user_id: userId,
      post_id: postId,
      vote_type: direction
    });

    // 투표 수 업데이트
    const voteCounts = await VoteModel.getPostVoteCounts(postId);
    
    res.json({
      success: true,
      vote: vote ? {
        vote_type: vote.vote_type,
        created_at: vote.created_at
      } : null,
      voteCounts,
      message: vote ? `${direction === 'up' ? 'Upvoted' : 'Downvoted'} successfully` : 'Vote removed'
    });
  } catch (error) {
    console.error('Vote error:', error);
    res.status(500).json({ error: 'Failed to process vote' });
  }
});

// 게시글 삭제 (작성자만)
router.delete('/:postId', authenticateToken, async (req, res) => {
  try {
    const postId = parseInt(req.params.postId);
    const userId = req.user!.userId;

    if (isNaN(postId)) {
      return res.status(400).json({ error: 'Invalid post ID' });
    }

    const deleted = await PostModel.delete(postId, userId);

    if (!deleted) {
      return res.status(404).json({ error: 'Post not found or you do not have permission to delete it' });
    }

    res.json({
      success: true,
      message: 'Post deleted successfully'
    });
  } catch (error) {
    console.error('Post deletion error:', error);
    res.status(500).json({ error: 'Failed to delete post' });
  }
});

export default router;
