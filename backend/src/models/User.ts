import { executeQuery } from '../config/database';
import bcrypt from 'bcrypt';

export interface User {
  id: number;
  username: string;
  email?: string;
  password_hash?: string;
  orcid?: string;
  is_orcid_verified: boolean;
  is_doi_verified: boolean;
  is_student_verified: boolean;
  trust_level: 'ORCID' | 'DOI' | 'STUDENT' | 'GUEST';
  verified_detail?: string;
  created_at: Date;
  updated_at: Date;
}

export class UserModel {
  static async create(userData: {
    username: string;
    email?: string;
    password?: string;
    orcid?: string;
  }): Promise<User> {
    const { username, email, password, orcid } = userData;
    
    const password_hash = password ? await bcrypt.hash(password, 10) : null;
    
    const query = `
      INSERT INTO users (username, email, password_hash, orcid)
      VALUES (?, ?, ?, ?)
    `;
    
    const result = await executeQuery(query, [username, email, password_hash, orcid]);
    const userId = (result as any).lastID;
    const user = await this.findById(userId);
    if (!user) throw new Error('Failed to create user');
    return user;
  }

  static async findById(id: number): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE id = ?';
    const result = await executeQuery(query, [id]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async findByEmail(email: string): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE email = ?';
    const result = await executeQuery(query, [email]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async findByOrcid(orcid: string): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE orcid = ?';
    const result = await executeQuery(query, [orcid]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async findByUsername(username: string): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE username = ?';
    const result = await executeQuery(query, [username]);
    return Array.isArray(result) && result.length > 0 ? result[0] : null;
  }

  static async updateTrustLevel(userId: number, trustLevel: string, verifiedDetail?: string): Promise<User> {
    const query = `
      UPDATE users 
      SET trust_level = ?, verified_detail = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `;
    
    await executeQuery(query, [trustLevel, verifiedDetail, userId]);
    const user = await this.findById(userId);
    if (!user) throw new Error('User not found');
    return user;
  }

  static async updateOrcidVerification(userId: number, orcid: string): Promise<User> {
    const query = `
      UPDATE users 
      SET orcid = ?, is_orcid_verified = 1, trust_level = 'ORCID', updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `;
    
    await executeQuery(query, [orcid, userId]);
    const user = await this.findById(userId);
    if (!user) throw new Error('User not found');
    return user;
  }

  static async updateDoiVerification(userId: number, doi: string): Promise<User> {
    const query = `
      UPDATE users 
      SET is_doi_verified = 1, 
          trust_level = CASE WHEN is_orcid_verified = 1 THEN 'ORCID' ELSE 'DOI' END,
          verified_detail = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `;
    
    await executeQuery(query, [`DOI:${doi}`, userId]);
    const user = await this.findById(userId);
    if (!user) throw new Error('User not found');
    return user;
  }

  static async updateStudentVerification(userId: number, email: string): Promise<User> {
    const query = `
      UPDATE users 
      SET is_student_verified = 1,
          trust_level = CASE 
            WHEN is_orcid_verified = 1 THEN 'ORCID'
            WHEN is_doi_verified = 1 THEN 'DOI'
            ELSE 'STUDENT'
          END,
          verified_detail = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `;
    
    await executeQuery(query, [`STU_EMAIL:${email}`, userId]);
    const user = await this.findById(userId);
    if (!user) throw new Error('User not found');
    return user;
  }

  static async verifyPassword(email: string, password: string): Promise<User | null> {
    const user = await this.findByEmail(email);
    if (!user || !user.password_hash) return null;
    
    const isValid = await bcrypt.compare(password, user.password_hash);
    return isValid ? user : null;
  }
}
