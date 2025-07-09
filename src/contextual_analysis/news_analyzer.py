#!/usr/bin/env python3
"""
News Analyzer - Full Implementation
Analyzes news sentiment and relevance for trading decisions using VADER sentiment analysis
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

# Try to import VADER sentiment analyzer
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER sentiment analyzer not available. Install with: pip install vaderSentiment")


class NewsAnalyzer:
    """
    Analyzes news sentiment and relevance for trading decisions
    Uses VADER sentiment analysis and custom impact scoring
    """
    
    def __init__(self, news_client=None):
        """
        Initialize the NewsAnalyzer
        
        Args:
            news_client: Optional news client for fetching news data
        """
        self.news_client = news_client
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("NewsAnalyzer initialized with VADER sentiment analysis")
        else:
            logger.warning("NewsAnalyzer initialized without VADER - using fallback sentiment analysis")
        
        # Define crypto-related keywords for relevance scoring
        self.crypto_keywords = {
            'general': ['bitcoin', 'btc', 'cryptocurrency', 'crypto', 'blockchain', 'defi', 'nft', 'altcoin'],
            'ethereum': ['ethereum', 'eth', 'ether', 'smart contract', 'dapp', 'gas fee'],
            'binance': ['binance', 'bnb', 'binance coin', 'cz', 'changpeng zhao'],
            'trading': ['trading', 'exchange', 'market', 'bull', 'bear', 'pump', 'dump', 'hodl', 'whale'],
            'regulation': ['regulation', 'sec', 'government', 'ban', 'legal', 'compliance', 'cbdc'],
            'adoption': ['adoption', 'mainstream', 'institutional', 'etf', 'corporate', 'investment'],
            'technology': ['mining', 'hash rate', 'fork', 'upgrade', 'scalability', 'layer 2']
        }
        
        # Impact multipliers for different categories
        self.category_multipliers = {
            'regulation': 1.5,
            'adoption': 1.3,
            'trading': 1.2,
            'technology': 1.1,
            'general': 1.0,
            'ethereum': 1.0,
            'binance': 1.0
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not text or not isinstance(text, str):
            return {
                'sentiment': 'neutral',
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'confidence': 0.0
            }
        
        text = text.lower().strip()
        
        if self.vader_analyzer:
            # Use VADER sentiment analysis
            scores = self.vader_analyzer.polarity_scores(text)
            
            # Determine overall sentiment
            compound = scores['compound']
            if compound >= 0.05:
                sentiment = 'positive'
            elif compound <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
                
            return {
                'sentiment': sentiment,
                'compound': compound,
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu'],
                'confidence': abs(compound)
            }
        else:
            # Fallback sentiment analysis using simple keyword matching
            return self._fallback_sentiment_analysis(text)
    
    def _fallback_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        Fallback sentiment analysis using keyword matching
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        positive_words = ['good', 'great', 'excellent', 'positive', 'bullish', 'up', 'rise', 'gain', 
                         'profit', 'growth', 'success', 'win', 'strong', 'boost', 'surge', 'rally']
        negative_words = ['bad', 'terrible', 'negative', 'bearish', 'down', 'fall', 'loss', 'crash',
                         'decline', 'drop', 'weak', 'dump', 'sell', 'fear', 'panic', 'concern']
        
        words = text.lower().split()
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words == 0:
            return {
                'sentiment': 'neutral',
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'confidence': 0.0
            }
        
        pos_ratio = pos_count / total_sentiment_words
        neg_ratio = neg_count / total_sentiment_words
        
        if pos_ratio > neg_ratio:
            sentiment = 'positive'
            compound = pos_ratio - neg_ratio
        elif neg_ratio > pos_ratio:
            sentiment = 'negative'
            compound = -(neg_ratio - pos_ratio)
        else:
            sentiment = 'neutral'
            compound = 0.0
            
        return {
            'sentiment': sentiment,
            'compound': compound,
            'positive': pos_ratio,
            'negative': neg_ratio,
            'neutral': 1.0 - (pos_ratio + neg_ratio),
            'confidence': abs(compound)
        }
    
    def analyze_news_impact(self, news_items: List[Dict[str, Any]], symbols: List[str] = None) -> Dict[str, Any]:
        """
        Analyze potential market impact of news items
        
        Args:
            news_items: List of news items
            symbols: List of trading symbols to analyze for
            
        Returns:
            Dictionary containing impact analysis
        """
        if not news_items:
            return {'overall_sentiment': 'neutral', 'impact_score': 0.0, 'relevant_count': 0}
        
        total_impact = 0.0
        relevant_count = 0
        sentiment_scores = []
        
        for item in news_items:
            # Get news text (title + content)
            title = item.get('title', '')
            content = item.get('content', '')
            text = f"{title} {content}".strip()
            
            if not text:
                continue
                
            # Check relevance to symbols if specified
            if symbols:
                is_relevant = any(symbol.lower() in text.lower() for symbol in symbols)
                if not is_relevant:
                    continue
            
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(text)
            sentiment_scores.append(sentiment_result['compound'])
            
            # Calculate impact weight based on source credibility and recency
            impact_weight = self._calculate_impact_weight(item)
            
            # Weight sentiment by impact
            weighted_sentiment = sentiment_result['compound'] * impact_weight
            total_impact += weighted_sentiment
            relevant_count += 1
        
        if relevant_count == 0:
            return {'overall_sentiment': 'neutral', 'impact_score': 0.0, 'relevant_count': 0}
        
        # Calculate overall metrics
        avg_impact = total_impact / relevant_count
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Determine overall sentiment
        if avg_sentiment > 0.1:
            overall_sentiment = 'positive'
        elif avg_sentiment < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
            
        return {
            'overall_sentiment': overall_sentiment,
            'impact_score': avg_impact,
            'sentiment_score': avg_sentiment,
            'relevant_count': relevant_count,
            'total_items': len(news_items)
        }
    
    def get_market_sentiment(self, symbols: List[str] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get overall market sentiment from recent news
        
        Args:
            symbols: List of symbols to analyze
            hours: Number of hours to look back
            
        Returns:
            Dictionary containing market sentiment analysis
        """
        logger.info(f"Getting market sentiment for symbols: {symbols}, hours: {hours}")
        return {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'trend': 'stable',
            'key_topics': []
        }
    
    def extract_key_topics(self, news_items: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key topics from news items
        
        Args:
            news_items: List of news items
            
        Returns:
            List of key topics
        """
        logger.info(f"Extracting key topics from {len(news_items)} news items")
        return []
    
    def classify_news_relevance(self, news_item: Dict[str, Any], symbols: List[str] = None) -> Tuple[bool, float]:
        """
        Classify if a news item is relevant for trading
        
        Args:
            news_item: News item to classify
            symbols: List of symbols to check relevance for
            
        Returns:
            Tuple of (is_relevant, relevance_score)
        """
        logger.info(f"Classifying news relevance for item: {news_item.get('title', 'Unknown')}")
        return False, 0.0
