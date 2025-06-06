"""CORE 카테고리 매핑"""
from .category_mapper import CategoryMapper
import logging

logger = logging.getLogger(__name__)

class CoreCategoryMapper(CategoryMapper):
    def __init__(self):
        super().__init__("core")
        self.mapping_data = {
            # 혼재된 분류 체계를 통합 매핑
            'Computer Science': {"level1": "Computer Science", "level2": "General Computing", "platform": "core", "original": "Computer Science"},
            'Artificial Intelligence': {"level1": "Computer Science", "level2": "Artificial Intelligence", "platform": "core", "original": "Artificial Intelligence"},
            'Machine Learning': {"level1": "Computer Science", "level2": "Machine Learning", "platform": "core", "original": "Machine Learning"},
            'Data Mining': {"level1": "Computer Science", "level2": "Data Mining", "platform": "core", "original": "Data Mining"},
            'Computer Vision': {"level1": "Computer Science", "level2": "Computer Vision", "platform": "core", "original": "Computer Vision"},
            'Natural Language Processing': {"level1": "Computer Science", "level2": "Natural Language Processing", "platform": "core", "original": "Natural Language Processing"},
            
            'Medicine': {"level1": "Medicine", "level2": "General Medicine", "platform": "core", "original": "Medicine"},
            'Biology': {"level1": "Life Sciences", "level2": "Biology", "platform": "core", "original": "Biology"},
            'Biochemistry': {"level1": "Life Sciences", "level2": "Biochemistry", "platform": "core", "original": "Biochemistry"},
            'Genetics': {"level1": "Life Sciences", "level2": "Genetics", "platform": "core", "original": "Genetics"},
            'Neuroscience': {"level1": "Life Sciences", "level2": "Neuroscience", "platform": "core", "original": "Neuroscience"},
            
            'Physics': {"level1": "Physics", "level2": "General Physics", "platform": "core", "original": "Physics"},
            'Mathematics': {"level1": "Mathematics", "level2": "General Mathematics", "platform": "core", "original": "Mathematics"},
            'Statistics': {"level1": "Mathematics", "level2": "Statistics", "platform": "core", "original": "Statistics"},
            
            'Engineering': {"level1": "Engineering", "level2": "General Engineering", "platform": "core", "original": "Engineering"},
            'Materials Science': {"level1": "Engineering", "level2": "Materials Science", "platform": "core", "original": "Materials Science"}
        }
        logger.error(f"CoreCategoryMapper loaded {len(self.mapping_data)} mappings")
