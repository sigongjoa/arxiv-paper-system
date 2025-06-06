import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DocumentationService:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info("DEBUG: DocumentationService initialized with file logging")
    
    def document_smtp_fix(self):
        """Document the SMTP import error fix"""
        title = "SMTP MIMEText Import Error Fix"
        error = "cannot import name 'MimeText' from 'email.mime.text'"
        solution = "Changed MimeText to MIMEText - correct capitalization"
        file_path = "backend/config/manager.py"
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.log_dir, f"error_fix_{timestamp}.txt")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Error: {error}\n")
                f.write(f"Solution: {solution}\n")
                f.write(f"File: {file_path}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
            
            logger.error(f"ERROR FIX DOCUMENTED: {title} -> {log_file}")
            return log_file
        except Exception as e:
            logger.error(f"ERROR: Failed to document fix: {str(e)}", exc_info=True)
            raise
