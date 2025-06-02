import rateLimit from 'express-rate-limit';

export const generalLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1분
  max: 100, // IP당 분당 100요청
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

export const authLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1분
  max: 5, // 로그인 시도 분당 5회
  message: {
    error: 'Too many authentication attempts, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

export const commentLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1분
  max: 10, // 댓글 작성 분당 10개
  message: {
    error: 'Too many comments posted, please slow down.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

export const verificationLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5분
  max: 3, // 인증 시도 5분에 3회
  message: {
    error: 'Too many verification attempts, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});
