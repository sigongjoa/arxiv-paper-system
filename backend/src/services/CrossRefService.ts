import axios from 'axios';

export interface CrossRefAuthor {
  given?: string;
  family?: string;
  ORCID?: string;
}

export interface CrossRefWork {
  DOI: string;
  title: string[];
  author: CrossRefAuthor[];
  published?: any;
}

export class CrossRefService {
  private static readonly CROSSREF_API_BASE = 'https://api.crossref.org';
  private static readonly USER_AGENT = process.env.CROSSREF_USER_AGENT || 'PaperShorts/1.0 (mailto:admin@example.com)';

  static async getWorkByDoi(doi: string): Promise<CrossRefWork> {
    try {
      const response = await axios.get(`${this.CROSSREF_API_BASE}/works/${doi}`, {
        headers: {
          'User-Agent': this.USER_AGENT
        }
      });

      return response.data.message;
    } catch (error) {
      console.error('CrossRef API error:', error);
      throw new Error('Failed to fetch work from CrossRef');
    }
  }

  static async verifyAuthor(doi: string, userProfile: { name?: string; orcid?: string }): Promise<boolean> {
    try {
      const work = await this.getWorkByDoi(doi);
      
      if (!work.author || work.author.length === 0) {
        return false;
      }

      // ORCID 매칭 (우선순위 높음)
      if (userProfile.orcid) {
        const orcidMatch = work.author.some(author => 
          author.ORCID && author.ORCID.includes(userProfile.orcid!)
        );
        if (orcidMatch) return true;
      }

      // 이름 매칭
      if (userProfile.name) {
        const userNameParts = userProfile.name.toLowerCase().split(' ');
        const nameMatch = work.author.some(author => {
          if (!author.given || !author.family) return false;
          
          const authorFullName = `${author.given} ${author.family}`.toLowerCase();
          const authorNameReversed = `${author.family} ${author.given}`.toLowerCase();
          
          return userNameParts.every(part => 
            authorFullName.includes(part) || authorNameReversed.includes(part)
          );
        });
        
        if (nameMatch) return true;
      }

      return false;
    } catch (error) {
      console.error('Author verification error:', error);
      return false;
    }
  }

  static validateDoi(doi: string): boolean {
    // DOI 형식 검증: 10.xxxx/yyyy 패턴
    const doiRegex = /^10\.\d{4,}\/[^\s]+$/;
    return doiRegex.test(doi);
  }

  static normalizeDoi(doi: string): string {
    // DOI 정규화: 앞의 'doi:' 또는 'DOI:' 제거
    return doi.replace(/^(doi:|DOI:)/i, '').trim();
  }
}
