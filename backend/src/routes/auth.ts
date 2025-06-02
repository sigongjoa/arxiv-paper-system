import express from 'express';
import { UserModel } from '../models/User';
import { JwtService } from '../services/JwtService';
import { OrcidService } from '../services/OrcidService';
import { CrossRefService } from '../services/CrossRefService';
import { EmailService } from '../services/EmailService';
import { authenticateToken } from '../middleware/auth';
import { authLimiter, verificationLimiter } from '../middleware/rateLimiter';

const router = express.Router();

// 일반 로그인 (이메일/패스워드)
router.post('/login', authLimiter, async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const user = await UserModel.verifyPassword(email, password);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const tokenPayload = {
      userId: user.id,
      username: user.username,
      trustLevel: user.trust_level
    };

    const tokens = JwtService.generateTokenPair(tokenPayload);

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        trustLevel: user.trust_level,
        verifiedDetail: user.verified_detail
      },
      tokens
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 회원가입
router.post('/register', authLimiter, async (req, res) => {
  try {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Username, email, and password are required' });
    }

    const existingUser = await UserModel.findByEmail(email);
    if (existingUser) {
      return res.status(409).json({ error: 'Email already registered' });
    }

    const existingUsername = await UserModel.findByUsername(username);
    if (existingUsername) {
      return res.status(409).json({ error: 'Username already taken' });
    }

    const user = await UserModel.create({ username, email, password });

    const tokenPayload = {
      userId: user.id,
      username: user.username,
      trustLevel: user.trust_level
    };

    const tokens = JwtService.generateTokenPair(tokenPayload);

    res.status(201).json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        trustLevel: user.trust_level
      },
      tokens
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// ORCID 인증 시작
router.get('/orcid/login', (req, res) => {
  try {
    const authUrl = OrcidService.getAuthorizationUrl();
    res.json({ authUrl });
  } catch (error) {
    console.error('ORCID auth URL error:', error);
    res.status(500).json({ error: 'Failed to generate ORCID authorization URL' });
  }
});

// ORCID 콜백 처리
router.get('/orcid/callback', async (req, res) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const { access_token, orcid } = await OrcidService.exchangeCodeForToken(code as string);
    const profile = await OrcidService.getProfile(orcid, access_token);

    let user = await UserModel.findByOrcid(orcid);
    
    if (!user) {
      // 새 사용자 생성
      user = await UserModel.create({
        username: profile.name || `orcid_${orcid.replace(/-/g, '')}`,
        email: profile.email,
        orcid
      });
    }

    // ORCID 인증 업데이트
    user = await UserModel.updateOrcidVerification(user.id, orcid);

    const tokenPayload = {
      userId: user.id,
      username: user.username,
      trustLevel: user.trust_level
    };

    const tokens = JwtService.generateTokenPair(tokenPayload);

    // 프론트엔드로 리디렉션 (토큰과 함께)
    const redirectUrl = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/auth/success?token=${tokens.accessToken}&refresh=${tokens.refreshToken}`;
    res.redirect(redirectUrl);
  } catch (error) {
    console.error('ORCID callback error:', error);
    const errorUrl = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/auth/error?message=ORCID authentication failed`;
    res.redirect(errorUrl);
  }
});

// DOI 인증
router.post('/doi/verify', authenticateToken, verificationLimiter, async (req, res) => {
  try {
    const { doi } = req.body;
    const userId = req.user!.userId;

    if (!doi) {
      return res.status(400).json({ error: 'DOI is required' });
    }

    const normalizedDoi = CrossRefService.normalizeDoi(doi);
    
    if (!CrossRefService.validateDoi(normalizedDoi)) {
      return res.status(400).json({ error: 'Invalid DOI format' });
    }

    const user = await UserModel.findById(userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const userProfile = {
      name: user.username,
      orcid: user.orcid
    };

    const isVerified = await CrossRefService.verifyAuthor(normalizedDoi, userProfile);

    if (!isVerified) {
      return res.status(400).json({ 
        error: 'Author verification failed',
        message: 'Your name or ORCID does not match the authors of this publication'
      });
    }

    const updatedUser = await UserModel.updateDoiVerification(userId, normalizedDoi);

    res.json({
      success: true,
      message: 'DOI author verified successfully',
      verifiedDetail: `DOI:${normalizedDoi}`,
      trustLevel: updatedUser.trust_level
    });
  } catch (error) {
    console.error('DOI verification error:', error);
    res.status(500).json({ error: 'DOI verification failed' });
  }
});

// 학생 이메일 인증 요청
router.post('/student/email-request', authenticateToken, verificationLimiter, async (req, res) => {
  try {
    const { email } = req.body;
    const userId = req.user!.userId;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    if (!EmailService.isAcademicEmail(email)) {
      return res.status(400).json({ 
        error: 'Invalid email domain',
        message: 'Email must be from an academic institution (.ac.kr, .edu, etc.)'
      });
    }

    await EmailService.sendVerificationEmail(userId, email);

    res.json({
      success: true,
      message: 'Verification email sent successfully'
    });
  } catch (error) {
    console.error('Student email verification request error:', error);
    res.status(500).json({ error: (error as Error).message || 'Failed to send verification email' });
  }
});

// 학생 이메일 인증 확인
router.get('/student/email-verify', async (req, res) => {
  try {
    const { token } = req.query;

    if (!token) {
      return res.status(400).json({ error: 'Verification token required' });
    }

    const verification = await EmailService.verifyEmailToken(token as string);

    if (!verification) {
      return res.status(400).json({ 
        error: 'Invalid or expired verification token'
      });
    }

    const updatedUser = await UserModel.updateStudentVerification(
      verification.userId, 
      verification.email
    );

    res.json({
      success: true,
      message: 'Student email verified successfully',
      trustLevel: updatedUser.trust_level,
      verifiedDetail: `STU_EMAIL:${verification.email}`
    });
  } catch (error) {
    console.error('Student email verification error:', error);
    res.status(500).json({ error: 'Email verification failed' });
  }
});

// 토큰 새로고침
router.post('/refresh-token', async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ error: 'Refresh token required' });
    }

    const payload = JwtService.verifyToken(refreshToken);
    if (!payload) {
      return res.status(403).json({ error: 'Invalid or expired refresh token' });
    }

    const user = await UserModel.findById(payload.userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const newTokenPayload = {
      userId: user.id,
      username: user.username,
      trustLevel: user.trust_level
    };

    const tokens = JwtService.generateTokenPair(newTokenPayload);

    res.json({
      success: true,
      tokens
    });
  } catch (error) {
    console.error('Token refresh error:', error);
    res.status(500).json({ error: 'Token refresh failed' });
  }
});

// 사용자 프로필 조회
router.get('/profile', authenticateToken, async (req, res) => {
  try {
    const userId = req.user!.userId;
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
        createdAt: user.created_at
      }
    });
  } catch (error) {
    console.error('Profile fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

export default router;
