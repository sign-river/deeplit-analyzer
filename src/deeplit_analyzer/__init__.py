"""
DeepLit Analyzer - A literature analysis tool based on DeepSeek API.

This package provides tools for efficient academic paper reading, including:
- Abstract generation
- Section summarization  
- Key point extraction
- Evidence mapping
"""

__version__ = "0.1.0"
__author__ = "DeepLit Team"
__email__ = "team@deeplit.com"

from .analyzer import DeepLitAnalyzer
from .config import Config

__all__ = ["DeepLitAnalyzer", "Config"]