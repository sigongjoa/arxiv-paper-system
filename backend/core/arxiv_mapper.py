"""arXiv 카테고리 매핑"""
from .category_mapper import CategoryMapper
import logging

logger = logging.getLogger(__name__)

class ArxivCategoryMapper(CategoryMapper):
    def __init__(self):
        super().__init__("arxiv")
        self.mapping_data = {
            # Computer Science
            'cs.AI': {"level1": "Computer Science", "level2": "Artificial Intelligence", "platform": "arxiv", "original": "cs.AI"},
            'cs.LG': {"level1": "Computer Science", "level2": "Machine Learning", "platform": "arxiv", "original": "cs.LG"},
            'cs.CV': {"level1": "Computer Science", "level2": "Computer Vision", "platform": "arxiv", "original": "cs.CV"},
            'cs.CL': {"level1": "Computer Science", "level2": "Natural Language Processing", "platform": "arxiv", "original": "cs.CL"},
            'cs.RO': {"level1": "Computer Science", "level2": "Robotics", "platform": "arxiv", "original": "cs.RO"},
            'cs.CR': {"level1": "Computer Science", "level2": "Cryptography", "platform": "arxiv", "original": "cs.CR"},
            'cs.DB': {"level1": "Computer Science", "level2": "Databases", "platform": "arxiv", "original": "cs.DB"},
            'cs.DS': {"level1": "Computer Science", "level2": "Data Structures", "platform": "arxiv", "original": "cs.DS"},
            'cs.SE': {"level1": "Computer Science", "level2": "Software Engineering", "platform": "arxiv", "original": "cs.SE"},
            'cs.NI': {"level1": "Computer Science", "level2": "Networking", "platform": "arxiv", "original": "cs.NI"},
            
            # Mathematics
            'math.NT': {"level1": "Mathematics", "level2": "Number Theory", "platform": "arxiv", "original": "math.NT"},
            'math.AG': {"level1": "Mathematics", "level2": "Algebraic Geometry", "platform": "arxiv", "original": "math.AG"},
            'math.ST': {"level1": "Mathematics", "level2": "Statistics", "platform": "arxiv", "original": "math.ST"},
            'math.PR': {"level1": "Mathematics", "level2": "Probability", "platform": "arxiv", "original": "math.PR"},
            'math.OC': {"level1": "Mathematics", "level2": "Optimization", "platform": "arxiv", "original": "math.OC"},
            'math.NA': {"level1": "Mathematics", "level2": "Numerical Analysis", "platform": "arxiv", "original": "math.NA"},
            
            # Physics
            'physics.optics': {"level1": "Physics", "level2": "Optics", "platform": "arxiv", "original": "physics.optics"},
            'physics.comp-ph': {"level1": "Physics", "level2": "Computational Physics", "platform": "arxiv", "original": "physics.comp-ph"},
            'quant-ph': {"level1": "Physics", "level2": "Quantum Physics", "platform": "arxiv", "original": "quant-ph"},
            'hep-ph': {"level1": "Physics", "level2": "High Energy Physics", "platform": "arxiv", "original": "hep-ph"},
            'astro-ph.CO': {"level1": "Physics", "level2": "Cosmology", "platform": "arxiv", "original": "astro-ph.CO"},
            'cond-mat.str-el': {"level1": "Physics", "level2": "Condensed Matter", "platform": "arxiv", "original": "cond-mat.str-el"}
        }
        logger.error(f"ArxivCategoryMapper loaded {len(self.mapping_data)} mappings")
