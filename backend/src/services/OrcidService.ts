import axios from 'axios';

export interface OrcidProfile {
  orcid: string;
  name: string;
  email?: string;
}

export class OrcidService {
  private static readonly ORCID_API_BASE = 'https://pub.orcid.org/v3.0';
  private static readonly ORCID_OAUTH_BASE = 'https://orcid.org/oauth';
  
  private static readonly CLIENT_ID = process.env.ORCID_CLIENT_ID;
  private static readonly CLIENT_SECRET = process.env.ORCID_CLIENT_SECRET;
  private static readonly REDIRECT_URI = process.env.ORCID_REDIRECT_URI || 'http://localhost:3001/auth/orcid/callback';

  static getAuthorizationUrl(): string {
    const params = new URLSearchParams({
      client_id: this.CLIENT_ID!,
      response_type: 'code',
      scope: '/authenticate',
      redirect_uri: this.REDIRECT_URI
    });

    return `${this.ORCID_OAUTH_BASE}/authorize?${params.toString()}`;
  }

  static async exchangeCodeForToken(code: string): Promise<{ access_token: string; orcid: string }> {
    try {
      const response = await axios.post(`${this.ORCID_OAUTH_BASE}/token`, {
        client_id: this.CLIENT_ID,
        client_secret: this.CLIENT_SECRET,
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: this.REDIRECT_URI
      }, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      return {
        access_token: response.data.access_token,
        orcid: response.data.orcid
      };
    } catch (error) {
      console.error('ORCID token exchange error:', error);
      throw new Error('Failed to exchange ORCID authorization code');
    }
  }

  static async getProfile(orcid: string, accessToken?: string): Promise<OrcidProfile> {
    try {
      const headers: any = {
        'Accept': 'application/json'
      };

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      const response = await axios.get(`${this.ORCID_API_BASE}/${orcid}/person`, {
        headers
      });

      const data = response.data;
      const name = data.name ? 
        `${data.name['given-names']?.value || ''} ${data.name['family-name']?.value || ''}`.trim() : 
        'Unknown';

      return {
        orcid,
        name,
        email: data.emails?.email?.[0]?.email || undefined
      };
    } catch (error) {
      console.error('ORCID profile fetch error:', error);
      throw new Error('Failed to fetch ORCID profile');
    }
  }

  static async verifyOrcid(orcid: string): Promise<boolean> {
    try {
      await this.getProfile(orcid);
      return true;
    } catch (error) {
      return false;
    }
  }
}
