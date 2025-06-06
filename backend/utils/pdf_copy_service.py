import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PdfCopyService:
    def __init__(self):
        self.source_dir = "D:\\arxiv-paper-system\\backend\\output\\pdfs"
        self.target_dir = "D:\\arxiv-paper-system\\pdfs"
        os.makedirs(self.target_dir, exist_ok=True)
        logger.error(f"DEBUG: PdfCopyService initialized - source: {self.source_dir}, target: {self.target_dir}")
    
    def copy_new_pdfs(self):
        copied_count = 0
        
        for filename in os.listdir(self.source_dir):
            if filename.endswith('.pdf'):
                source_path = os.path.join(self.source_dir, filename)
                target_path = os.path.join(self.target_dir, filename)
                
                if not os.path.exists(target_path):
                    shutil.copy2(source_path, target_path)
                    copied_count += 1
                    logger.error(f"DEBUG: Copied {filename} to target directory")
        
        logger.error(f"DEBUG: Copied {copied_count} new PDF files")
        return copied_count
    
    def sync_directories(self):
        self.copy_new_pdfs()
        logger.error(f"DEBUG: Directory sync completed at {datetime.now()}")
