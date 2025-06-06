"""카테고리 매핑 베이스 클래스"""
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class CategoryMapper:
    def __init__(self, platform_name):
        self.platform = platform_name
        self.mapping_data = {}
        logger.error(f"CategoryMapper initialized for {platform_name}")
    
    def normalize_category(self, original_category):
        try:
            normalized = self.mapping_data.get(original_category, {
                "level1": "Unknown",
                "level2": original_category,
                "platform": self.platform,
                "original": original_category
            })
            logger.error(f"Normalized {original_category} -> {normalized}")
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing category {original_category}: {e}")
            raise
    
    def get_all_mappings(self):
        logger.error(f"Total mappings: {len(self.mapping_data)}")
        return self.mapping_data
