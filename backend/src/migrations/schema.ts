import { executeQuery } from '../config/database';

export const createTables = async (): Promise<void> => {
  console.log('Creating database tables...');

  // Users table
  await executeQuery(`
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username VARCHAR(100) UNIQUE NOT NULL,
      email VARCHAR(255) UNIQUE,
      password_hash VARCHAR(255),
      
      -- ORCID 인증 관련
      orcid VARCHAR(19) UNIQUE,
      is_orcid_verified BOOLEAN DEFAULT FALSE,
      orcid_verified_at TIMESTAMP NULL,
      
      -- DOI 인증 관련
      is_doi_verified BOOLEAN DEFAULT FALSE,
      doi_verified_at TIMESTAMP NULL,
      
      -- 학생 인증 관련
      is_student_verified BOOLEAN DEFAULT FALSE,
      student_email VARCHAR(255) NULL,
      student_verified_at TIMESTAMP NULL,
      
      -- 공통 필드
      trust_level VARCHAR(20) NOT NULL DEFAULT 'GUEST',
      verified_detail VARCHAR(255) NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW(),
      
      CONSTRAINT chk_trust_level CHECK (trust_level IN ('ORCID','DOI','STUDENT','GUEST'))
    );
  `);

  // Posts table
  await executeQuery(`
    CREATE TABLE IF NOT EXISTS posts (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title VARCHAR(200) NOT NULL,
      content TEXT NOT NULL,
      category VARCHAR(50) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW(),
      upvotes INTEGER DEFAULT 0,
      downvotes INTEGER DEFAULT 0,
      is_published BOOLEAN DEFAULT TRUE,
      
      CONSTRAINT chk_posts_category CHECK (category IN ('general','tech','science','discussion','question'))
    );
  `);

  // Votes table
  await executeQuery(`
    CREATE TABLE IF NOT EXISTS votes (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
      vote_type VARCHAR(10) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      
      UNIQUE(user_id, post_id),
      CONSTRAINT chk_vote_type CHECK (vote_type IN ('up','down'))
    );
  `);

  // Comments table
  await executeQuery(`
    CREATE TABLE IF NOT EXISTS comments (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      
      -- 노출 및 승인 관련
      is_approved BOOLEAN DEFAULT FALSE,
      trust_level VARCHAR(20) NOT NULL,
      verified_detail VARCHAR(255) NULL,
      
      -- FK 외 추가 컬럼
      parent_comment_id INTEGER NULL,
      FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE SET NULL,
      
      CONSTRAINT chk_comments_trust_level CHECK (trust_level IN ('ORCID','DOI','STUDENT','GUEST'))
    );
  `);

  // Email verification tokens table
  await executeQuery(`
    CREATE TABLE IF NOT EXISTS email_verification_tokens (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token VARCHAR(255) UNIQUE NOT NULL,
      email VARCHAR(255) NOT NULL,
      expires_at TIMESTAMP NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  // Indexes for performance
  await executeQuery(`
    CREATE INDEX IF NOT EXISTS idx_users_orcid ON users(orcid);
    CREATE INDEX IF NOT EXISTS idx_users_trust_level ON users(trust_level);
    CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
    CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
    CREATE INDEX IF NOT EXISTS idx_posts_is_published ON posts(is_published);
    CREATE INDEX IF NOT EXISTS idx_votes_post_id ON votes(post_id);
    CREATE INDEX IF NOT EXISTS idx_votes_user_post ON votes(user_id, post_id);
    CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
    CREATE INDEX IF NOT EXISTS idx_comments_trust_level ON comments(trust_level);
    CREATE INDEX IF NOT EXISTS idx_comments_is_approved ON comments(is_approved);
    CREATE INDEX IF NOT EXISTS idx_email_tokens_token ON email_verification_tokens(token);
  `);

  console.log('Database tables created successfully');
  
  // 개발용 더미 데이터 생성
  await createSampleData();
};

export const dropTables = async (): Promise<void> => {
  console.log('Dropping database tables...');
  
  await executeQuery('DROP TABLE IF EXISTS email_verification_tokens CASCADE;');
  await executeQuery('DROP TABLE IF EXISTS comments CASCADE;');
  await executeQuery('DROP TABLE IF EXISTS votes CASCADE;');
  await executeQuery('DROP TABLE IF EXISTS posts CASCADE;');
  await executeQuery('DROP TABLE IF EXISTS users CASCADE;');
  
  console.log('Database tables dropped successfully');
};

// 개발용 더미 데이터 생성
export const createSampleData = async (): Promise<void> => {
  console.log('Creating sample data...');
  
  try {
    // 샘플 사용자 생성
    const users = [
      {
        username: 'admin',
        email: 'admin@papershorts.com',
        password_hash: '$2b$10$K8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9Q',
        trust_level: 'ORCID',
        orcid: '0000-0000-0000-0000',
        is_orcid_verified: true
      },
      {
        username: 'ai_researcher',
        email: 'ai@university.edu',
        password_hash: '$2b$10$K8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9Q',
        trust_level: 'DOI',
        is_doi_verified: true
      },
      {
        username: 'student_user',
        email: 'student@university.ac.kr',
        password_hash: '$2b$10$K8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9QZ5VtKZ8QZ5VtKOeK8gBqJ9Q',
        trust_level: 'STUDENT',
        is_student_verified: true,
        student_email: 'student@university.ac.kr'
      }
    ];

    for (const user of users) {
      await executeQuery(`
        INSERT OR IGNORE INTO users (username, email, password_hash, trust_level, orcid, is_orcid_verified, is_doi_verified, is_student_verified, student_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        user.username,
        user.email,
        user.password_hash,
        user.trust_level,
        user.orcid || null,
        user.is_orcid_verified || false,
        user.is_doi_verified || false,
        user.is_student_verified || false,
        user.student_email || null
      ]);
    }

    // 샘플 게시글 생성
    const posts = [
      {
        user_id: 1,
        title: 'Welcome to the PaperShorts Research Community',
        content: `We're excited to launch this new platform for researchers to connect, share insights, and collaborate. This is a space where academic minds meet to discuss everything from breakthrough discoveries to research methodologies.

Feel free to introduce yourself, share your research interests, and engage with fellow researchers. Let's build an amazing community together!`,
        category: 'general'
      },
      {
        user_id: 2,
        title: 'The Future of AI in Academic Research: Opportunities and Challenges',
        content: `As AI tools become increasingly sophisticated, they're transforming how we conduct research. From literature reviews to data analysis, AI is becoming an invaluable research assistant.

Key areas where AI is making an impact:
• Automated literature synthesis
• Pattern recognition in large datasets
• Hypothesis generation
• Peer review assistance

What are your experiences with AI in research? What opportunities and challenges do you see?`,
        category: 'tech'
      },
      {
        user_id: 3,
        title: 'First-time researcher here - How long does peer review typically take?',
        content: `Hi everyone! I just submitted my first paper to a journal and I'm wondering about the peer review timeline. The journal website says 'several months' but I'd love to hear about real experiences.

Also, any tips for a nervous first-time author? What should I expect during the review process?`,
        category: 'question'
      },
      {
        user_id: 2,
        title: 'Breakthrough in Quantum Computing: New Error Correction Method',
        content: `Just read an fascinating paper about a novel quantum error correction technique that could significantly improve quantum computer stability. The researchers achieved a 99.9% fidelity rate in their experiments.

This could be a game-changer for practical quantum computing applications. The implications for cryptography, drug discovery, and complex simulations are enormous.

What do you think about the potential impact of this research?`,
        category: 'science'
      },
      {
        user_id: 1,
        title: 'Open Access vs Traditional Publishing: Where Do We Stand in 2024?',
        content: `The debate between open access and traditional publishing continues to evolve. With new funding mandates and changing attitudes toward research accessibility, I'm curious about the community's current perspective.

Pros of Open Access:
✅ Wider accessibility
✅ Faster dissemination
✅ Higher citation rates
✅ Public funding transparency

Challenges:
❌ Publication fees
❌ Quality concerns (predatory journals)
❌ Career advancement considerations

What's your publishing strategy? How do you balance impact, accessibility, and career considerations?`,
        category: 'discussion'
      }
    ];

    for (const post of posts) {
      await executeQuery(`
        INSERT OR IGNORE INTO posts (user_id, title, content, category, is_published, upvotes, downvotes)
        VALUES (?, ?, ?, ?, 1, ?, ?)
      `, [
        post.user_id,
        post.title,
        post.content,
        post.category,
        Math.floor(Math.random() * 100) + 10, // 램덤 upvotes
        Math.floor(Math.random() * 10)      // 램덤 downvotes
      ]);
    }

    // 샘플 댓글 생성
    const comments = [
      {
        user_id: 2,
        post_id: 1,
        content: 'This is exactly what the research community needed! Looking forward to connecting with fellow researchers and sharing insights.'
      },
      {
        user_id: 3,
        post_id: 1,
        content: 'Welcome to everyone joining! As someone new to research, I\'m excited to learn from experienced researchers here.'
      },
      {
        user_id: 1,
        post_id: 2,
        content: 'Great overview! I\'ve been using AI for literature reviews and it\'s been a game-changer. However, human creativity and domain expertise remain crucial.'
      },
      {
        user_id: 2,
        post_id: 3,
        content: 'Peer review timelines vary widely by field and journal. In my experience, expect 3-6 months for most journals. Good luck with your first submission!'
      }
    ];

    for (const comment of comments) {
      // 사용자의 trust_level 가져오기
      const userResult = await executeQuery('SELECT trust_level FROM users WHERE id = ?', [comment.user_id]);
      const trustLevel = userResult[0]?.trust_level || 'GUEST';
      
      await executeQuery(`
        INSERT OR IGNORE INTO comments (user_id, post_id, content, trust_level, is_approved)
        VALUES (?, ?, ?, ?, ?)
      `, [
        comment.user_id,
        comment.post_id,
        comment.content,
        trustLevel,
        trustLevel !== 'GUEST' ? 1 : 0
      ]);
    }

    console.log('Sample data created successfully');
  } catch (error) {
    console.error('Error creating sample data:', error);
  }
};
