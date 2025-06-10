import json
import os
from typing import Dict, Any
from ..utils.mailing_service import MailingService

class ConfigManager:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        print(f"DEBUG: ConfigManager initialized with dir: {self.config_dir}")
        self.mailing_service = MailingService()
    
    def save_mailing_config(self, config: Dict[str, Any]) -> bool:
        """Save mailing configuration to file"""
        try:
            config_path = os.path.join(self.config_dir, 'mailing_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"DEBUG: Mailing config saved to {config_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save mailing config: {str(e)}")
            return False
    
    def load_mailing_config(self) -> Dict[str, Any]:
        """Load mailing configuration from file"""
        try:
            config_path = os.path.join(self.config_dir, 'mailing_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"DEBUG: Mailing config loaded from {config_path}")
                return config
            else:
                print("DEBUG: No mailing config file found, returning defaults")
                return self.mailing_service._get_default_mailing_config()
        except Exception as e:
            print(f"ERROR: Failed to load mailing config: {str(e)}")
            return self.mailing_service._get_default_mailing_config()

# Global instance
config_manager = ConfigManager()
