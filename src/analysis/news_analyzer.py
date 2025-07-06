#!/usr/bin/env python3
"""
News Analyzer Wrapper
Backwards compatibility wrapper that imports from contextual_analysis
"""

# Import from the actual location in contextual_analysis
import sys
import os
from pathlib import Path

# Add the parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the actual NewsAnalyzer class
from contextual_analysis.news_analyzer import NewsAnalyzer

# Export for backwards compatibility
__all__ = ['NewsAnalyzer']
