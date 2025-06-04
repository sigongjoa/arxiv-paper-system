"""
Shorts generation module for mass-production YouTube Shorts
"""

from .hook_generator import HookGenerator
from .config import get_config, validate_shorts_config, SHORTS_CONFIG

__all__ = ['HookGenerator', 'get_config', 'validate_shorts_config', 'SHORTS_CONFIG']
