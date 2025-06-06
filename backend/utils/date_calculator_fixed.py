from datetime import datetime, timedelta, timezone

class DateCalculator:
    @staticmethod
    def calculate_range(days_back: int):
        """정확한 날짜 범위 계산 - 시간대 문제 해결"""
        # UTC 기준으로 계산하되, 미래 날짜도 포함
        end_date = datetime.now(timezone.utc) + timedelta(days=1)  # 미래 1일 추가
        
        if days_back == 0:
            # 오늘과 내일 포함 (시간대 차이 고려)
            start_date = (end_date - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif days_back < 0:
            # 미래 날짜 검색
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date + timedelta(days=abs(days_back))
        else:
            # N일전부터 미래 1일까지
            start_date = (end_date - timedelta(days=days_back + 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"DEBUG: DateCalculator (FIXED) - days_back: {days_back}, range: {start_date.date()} to {end_date.date()}")
        return start_date, end_date
    
    @staticmethod
    def is_in_range(paper_date: datetime, start_date: datetime, end_date: datetime) -> bool:
        """논문이 날짜 범위에 포함되는지 확인"""
        return start_date <= paper_date <= end_date
