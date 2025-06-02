import { executeQuery } from '../config/database';
import { v4 as uuidv4 } from 'uuid';

export interface EmailVerificationToken {
  id: number;
  user_id: number;
  token: string;
  email: string;
  expires_at: string;
  created_at: string;
}

export class EmailVerificationTokenModel {
  static async create(userId: number, email: string, expiresInHours: number = 24): Promise<EmailVerificationToken> {
    const token = uuidv4();
    const expires_at = new Date();
    expires_at.setHours(expires_at.getHours() + expiresInHours);
    
    const query = `
      INSERT INTO email_verification_tokens (user_id, token, email, expires_at)
      VALUES (?, ?, ?, ?)
    `;
    
    const result = await executeQuery(query, [userId, token, email, expires_at.toISOString()]);
    const tokenId = (result as any).lastID;
    const verificationToken = await this.findByTokenId(tokenId);
    if (!verificationToken) throw new Error('Failed to create verification token');
    return verificationToken;
  }

  static async findByTokenId(id: number): Promise<EmailVerificationToken | null> {
    const query = 'SELECT * FROM email_verification_tokens WHERE id = ?';
    const result = await executeQuery(query, [id]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async findByToken(token: string): Promise<EmailVerificationToken | null> {
    const query = `
      SELECT * FROM email_verification_tokens 
      WHERE token = ? AND expires_at > datetime('now')
    `;
    
    const result = await executeQuery(query, [token]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async deleteByToken(token: string): Promise<void> {
    const query = 'DELETE FROM email_verification_tokens WHERE token = ?';
    await executeQuery(query, [token]);
  }

  static async deleteExpiredTokens(): Promise<void> {
    const query = "DELETE FROM email_verification_tokens WHERE expires_at <= datetime('now')";
    await executeQuery(query);
  }

  static async deleteByUserId(userId: number): Promise<void> {
    const query = 'DELETE FROM email_verification_tokens WHERE user_id = ?';
    await executeQuery(query, [userId]);
  }
}
