import { Request, Response, NextFunction } from 'express';
import { JwtService, TokenPayload } from '../services/JwtService';

declare global {
  namespace Express {
    interface Request {
      user?: TokenPayload;
    }
  }
}

export const authenticateToken = (req: Request, res: Response, next: NextFunction): void => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    res.status(401).json({ error: 'Access token required' });
    return;
  }

  const payload = JwtService.verifyToken(token);
  if (!payload) {
    res.status(403).json({ error: 'Invalid or expired token' });
    return;
  }

  req.user = payload;
  next();
};

export const requireTrustLevel = (minTrustLevel: string) => {
  const trustLevelHierarchy = ['GUEST', 'STUDENT', 'DOI', 'ORCID'];
  
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Authentication required' });
      return;
    }

    const userLevel = trustLevelHierarchy.indexOf(req.user.trustLevel);
    const requiredLevel = trustLevelHierarchy.indexOf(minTrustLevel);

    if (userLevel < requiredLevel) {
      res.status(403).json({ error: 'Insufficient trust level' });
      return;
    }

    next();
  };
};

export const optionalAuth = (req: Request, res: Response, next: NextFunction): void => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (token) {
    const payload = JwtService.verifyToken(token);
    if (payload) {
      req.user = payload;
    }
  }

  next();
};
