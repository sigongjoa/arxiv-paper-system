import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class DateCalculator:
    @staticmethod
    def calculate_range(days_back: int):
        """Asia/Seoul 기준으로 오늘을 계산한 후 UTC로 변환하여 정확한 날짜 범위 계산"""
        # Asia/Seoul 기준 현재 시간
        now_seoul = datetime.now(timezone(timedelta(hours=9)))
        
        # N일전(Seoul) 00:00부터 오늘(Seoul) 23:59까지를 UTC로 변환
        # days_back=0일 때의 특별 처리는 crawling_routes.py에서 db.get_all_papers()로 대체됨
        start_seoul = (now_seoul - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_seoul = now_seoul.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_date = start_seoul.astimezone(timezone.utc)
        end_date = end_seoul.astimezone(timezone.utc)
        
        logger.debug(f"DateCalculator: days_back: {days_back}, range: {start_date.date()} to {end_date.date()}")
        logger.debug(f"UTC time range: {start_date.isoformat()} to {end_date.isoformat()}")
        return start_date, end_date
    
    @staticmethod
    def is_in_range(paper_date: datetime, start_date: datetime, end_date: datetime) -> bool:
        """논문이 날짜 범위에 포함되는지 확인 (date-only 비교)"""
        # date-only 비교로 변경
        return start_date.date() <= paper_date.date() <= end_date.date()
