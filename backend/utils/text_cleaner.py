import re
import logging

logger = logging.getLogger(__name__)

def clean_text_for_analysis(text):
    logger.debug(f"Cleaning text of length: {len(text)}")
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
    text = text.strip()
    
    logger.debug(f"Cleaned text length: {len(text)}")
    return text
