from datetime import datetime, timedelta
import logging

class DateCalculator:
    @staticmethod
    def calculate_range(days_back):
        """날짜 범위 계산"""
        end_date = datetime.now()
        
        if days_back == 0:
            # 오늘 날짜 범위
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # N일 전부터 지금까지
            start_date = end_date - timedelta(days=days_back)
        
        logging.error(f"DateCalculator: days_back={days_back}, range: {start_date.date()} to {end_date.date()}")
        
        return start_date, end_date
