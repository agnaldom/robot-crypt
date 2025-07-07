#!/usr/bin/env python3
"""
Contextual Analysis Module
Provides news analysis and context-aware trading insights
"""

from src.contextual_analysis.news_analyzer import NewsAnalyzer
from src.contextual_analysis.advanced_context_analyzer import AdvancedContextAnalyzer

# NewsApiClient está localizado em api.external.news_api_client
# Import será feito dinamicamente quando necessário para evitar problemas com imports relativos

__all__ = ['NewsAnalyzer', 'AdvancedContextAnalyzer']
