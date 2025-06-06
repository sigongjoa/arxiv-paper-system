"""플랫폼별 실제 카테고리 API"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

category_router = APIRouter()

# 실제 플랫폼별 세부 카테고리 데이터
PLATFORM_DETAILED_CATEGORIES = {
    'arxiv': {
        'Computer Science': {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning', 
            'cs.CV': 'Computer Vision and Pattern Recognition',
            'cs.CL': 'Computation and Language',
            'cs.NE': 'Neural and Evolutionary Computing',
            'cs.RO': 'Robotics',
            'cs.GT': 'Computer Science and Game Theory',
            'cs.HC': 'Human-Computer Interaction',
            'cs.IR': 'Information Retrieval',
            'cs.CR': 'Cryptography and Security',
            'cs.DB': 'Databases',
            'cs.DS': 'Data Structures and Algorithms'
        },
        'Mathematics': {
            'math.ST': 'Statistics Theory',
            'math.PR': 'Probability',
            'math.NA': 'Numerical Analysis',
            'math.OC': 'Optimization and Control',
            'math.CO': 'Combinatorics',
            'math.AG': 'Algebraic Geometry',
            'math.NT': 'Number Theory'
        },
        'Physics': {
            'physics.comp-ph': 'Computational Physics',
            'physics.data-an': 'Data Analysis, Statistics and Probability',
            'cond-mat.stat-mech': 'Statistical Mechanics',
            'quant-ph': 'Quantum Physics',
            'physics.soc-ph': 'Physics and Society'
        },
        'Statistics': {
            'stat.ML': 'Machine Learning',
            'stat.AP': 'Applications',
            'stat.TH': 'Statistics Theory',
            'stat.CO': 'Computation'
        }
    },
    'biorxiv': {
        'Life Sciences': [
            'Animal Behavior and Cognition',
            'Biochemistry',
            'Bioengineering', 
            'Bioinformatics',
            'Biophysics',
            'Cancer Biology',
            'Cell Biology',
            'Developmental Biology'
        ],
        'Medical Sciences': [
            'Epidemiology',
            'Genetics',
            'Genomics', 
            'Immunology',
            'Microbiology',
            'Molecular Biology',
            'Neuroscience',
            'Pathology'
        ]
    },
    'pmc': {
        'Medical Research': [
            'Medicine',
            'Public Health',
            'Clinical Research',
            'Pharmacology',
            'Epidemiology'
        ],
        'Life Sciences': [
            'Biomedical Research',
            'Genetics',
            'Molecular Biology',
            'Computational Biology'
        ]
    },
    'plos': {
        'Sciences': [
            'Biology',
            'Computational Biology',
            'Genetics',
            'Medicine',
            'Environmental Science'
        ]
    },
    'doaj': {
        'Sciences': [
            'Computer Science',
            'Engineering',
            'Medicine',
            'Biology'
        ],
        'Social Sciences': [
            'Education',
            'Psychology',
            'Social Sciences'
        ]
    },
    'core': {
        'All Subjects': [
            'Computer Science',
            'Engineering', 
            'Medicine',
            'Social Sciences',
            'Natural Sciences'
        ]
    }
}

@category_router.get("/platform-categories")
async def get_platform_categories():
    """모든 플랫폼의 세부 카테고리 반환"""
    try:
        logger.error("Platform categories requested")
        return {
            "success": True,
            "categories": PLATFORM_DETAILED_CATEGORIES
        }
    except Exception as e:
        logger.error(f"Error getting platform categories: {e}")
        return {
            "success": False,
            "error": str(e),
            "categories": {}
        }

@category_router.get("/platform-categories/{platform}")
async def get_platform_specific_categories(platform: str):
    """특정 플랫폼의 카테고리 반환"""
    try:
        platform_lower = platform.lower()
        if platform_lower in PLATFORM_DETAILED_CATEGORIES:
            return {
                "success": True,
                "platform": platform_lower,
                "categories": PLATFORM_DETAILED_CATEGORIES[platform_lower]
            }
        else:
            return {
                "success": False,
                "error": f"Platform {platform} not found",
                "categories": {}
            }
    except Exception as e:
        logger.error(f"Error getting categories for {platform}: {e}")
        return {
            "success": False,
            "error": str(e),
            "categories": {}
        }
