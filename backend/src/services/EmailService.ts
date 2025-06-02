import nodemailer from 'nodemailer';
import { EmailVerificationTokenModel } from '../models/EmailVerificationToken';

export class EmailService {
  private static transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'localhost',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });

  private static readonly ACADEMIC_DOMAINS = [
    '.ac.kr',
    '.edu',
    '.edu.au',
    '.ac.uk',
    '.edu.cn',
    '.ac.jp',
    '.edu.sg'
  ];

  static isAcademicEmail(email: string): boolean {
    return this.ACADEMIC_DOMAINS.some(domain => email.toLowerCase().endsWith(domain));
  }

  static async sendVerificationEmail(userId: number, email: string): Promise<string> {
    if (!this.isAcademicEmail(email)) {
      throw new Error('Email domain is not from an academic institution');
    }

    const token = await EmailVerificationTokenModel.create(userId, email);
    const verificationUrl = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/auth/student/verify?token=${token.token}`;

    const mailOptions = {
      from: process.env.SMTP_FROM || 'noreply@papershorts.com',
      to: email,
      subject: 'PaperShorts 학생 인증 - 이메일 확인',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2>PaperShorts 학생 인증</h2>
          <p>안녕하세요!</p>
          <p>PaperShorts에서 학생 인증을 요청하셨습니다.</p>
          <p>아래 링크를 클릭하여 이메일 인증을 완료해주세요:</p>
          <a href="${verificationUrl}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">이메일 인증하기</a>
          <p>이 링크는 24시간 동안 유효합니다.</p>
          <p>만약 본인이 요청하지 않았다면 이 메일을 무시해주세요.</p>
          <hr>
          <p style="font-size: 12px; color: #666;">
            PaperShorts Team<br>
            이 메일은 자동으로 발송된 메일입니다.
          </p>
        </div>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      return token.token;
    } catch (error) {
      console.error('Failed to send verification email:', error);
      throw new Error('Failed to send verification email');
    }
  }

  static async verifyEmailToken(token: string): Promise<{ userId: number; email: string } | null> {
    const tokenData = await EmailVerificationTokenModel.findByToken(token);
    
    if (!tokenData) {
      return null;
    }

    await EmailVerificationTokenModel.deleteByToken(token);
    
    return {
      userId: tokenData.user_id,
      email: tokenData.email
    };
  }
}
