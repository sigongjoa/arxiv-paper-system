import { executeQuery } from '../config/database';

export async function healthCheck(): Promise<{
  status: string;
  database: string;
  timestamp: string;
  services: {
    [key: string]: string;
  };
}> {
  const services: { [key: string]: string } = {};
  
  // 데이터베이스 연결 확인
  try {
    await executeQuery('SELECT 1');
    services.database = 'OK';
  } catch (error) {
    services.database = 'ERROR';
  }

  // ORCID 설정 확인
  services.orcid = (process.env.ORCID_CLIENT_ID && process.env.ORCID_CLIENT_SECRET) ? 'CONFIGURED' : 'NOT_CONFIGURED';
  
  // SMTP 설정 확인
  services.smtp = (process.env.SMTP_HOST && process.env.SMTP_USER) ? 'CONFIGURED' : 'NOT_CONFIGURED';

  // JWT 설정 확인
  services.jwt = process.env.JWT_SECRET ? 'CONFIGURED' : 'NOT_CONFIGURED';

  const allServicesOk = Object.values(services).every(status => 
    status === 'OK' || status === 'CONFIGURED'
  );

  return {
    status: allServicesOk ? 'OK' : 'PARTIAL',
    database: services.database,
    timestamp: new Date().toISOString(),
    services
  };
}
