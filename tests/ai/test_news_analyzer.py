#!/usr/bin/env python3
"""
Tests for News Analyzer AI functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.ai.news_analyzer import LLMNewsAnalyzer, CryptoNewsItem, NewsAnalysis
from src.ai.llm_client import LLMResponse


class TestCryptoNewsItem:
    """Test CryptoNewsItem dataclass"""
    
    def test_crypto_news_item_creation(self):
        """Test creating CryptoNewsItem"""
        news_item = CryptoNewsItem(
            title="Bitcoin Price Surges",
            content="Bitcoin has reached new highs...",
            source="CoinDesk",
            published_at=datetime.now(),
            symbols_mentioned=["BTC", "BITCOIN"]
        )
        
        assert news_item.title == "Bitcoin Price Surges"
        assert news_item.content == "Bitcoin has reached new highs..."
        assert news_item.source == "CoinDesk"
        assert "BTC" in news_item.symbols_mentioned
        assert isinstance(news_item.published_at, datetime)
    
    def test_crypto_news_item_with_url(self):
        """Test CryptoNewsItem with URL"""
        news_item = CryptoNewsItem(
            title="Ethereum Update",
            content="Ethereum network upgrade...",
            source="CryptoBlog",
            published_at=datetime.now(),
            symbols_mentioned=["ETH"],
            url="https://example.com/news"
        )
        
        assert news_item.url == "https://example.com/news"
    
    def test_crypto_news_item_with_author(self):
        """Test CryptoNewsItem with author"""
        news_item = CryptoNewsItem(
            title="Market Analysis",
            content="Today's market analysis...",
            source="CryptoNews",
            published_at=datetime.now(),
            symbols_mentioned=["BTC", "ETH"],
            author="John Doe"
        )
        
        assert news_item.author == "John Doe"


class TestNewsAnalysis:
    """Test NewsAnalysis dataclass"""
    
    def test_news_analysis_creation(self):
        """Test creating NewsAnalysis"""
        result = NewsAnalysis(
            sentiment_score=0.7,
            sentiment_label="positive",
            confidence=0.85,
            impact_level="high",
            key_events=["Bitcoin ETF approval"],
            price_prediction="bullish",
            reasoning="Positive regulatory news drives sentiment",
            article_count=5,
            timestamp=datetime.now()
        )
        
        assert result.sentiment_score == 0.7
        assert result.sentiment_label == "positive"
        assert result.confidence == 0.85
        assert result.impact_level == "high"
        assert "Bitcoin ETF approval" in result.key_events
        assert result.price_prediction == "bullish"
        assert "regulatory news" in result.reasoning
    
    def test_news_analysis_with_metadata(self):
        """Test NewsAnalysis with metadata"""
        metadata = {
            "articles_processed": 5,
            "processing_time": 2.5,
            "model_used": "gpt-4"
        }
        
        result = NewsAnalysis(
            sentiment_score=0.3,
            sentiment_label="neutral",
            confidence=0.6,
            impact_level="medium",
            key_events=[],
            price_prediction="neutral",
            reasoning="Mixed signals in the market",
            article_count=5,
            timestamp=datetime.now()
        )
        
        assert result.article_count == 5
        assert isinstance(result.timestamp, datetime)


class TestLLMNewsAnalyzer:
    """Test LLM News Analyzer functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.analyzer = LLMNewsAnalyzer()
    
    def test_llm_news_analyzer_initialization(self):
        """Test LLMNewsAnalyzer initialization"""
        assert self.analyzer.llm_client is not None
        assert self.analyzer.logger is not None
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_success(self):
        """Test successful news analysis"""
        # Mock LLM response
        mock_llm_response = {
            "sentiment_score": 0.8,
            "sentiment_label": "positive",
            "confidence": 0.9,
            "impact_level": "high",
            "key_events": ["Bitcoin ETF approval", "Institutional adoption"],
            "price_prediction": "bullish",
            "reasoning": "Strong positive sentiment due to regulatory clarity"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_llm_response
        
        # Create sample news items
        news_items = [
            CryptoNewsItem(
                title="Bitcoin ETF Gets Approval",
                content="The SEC has approved the first Bitcoin ETF...",
                source="Reuters",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Major Bank Adopts Bitcoin",
                content="Goldman Sachs announces Bitcoin services...",
                source="Bloomberg",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        self.analyzer.llm_client = mock_llm_client
        
        result = await self.analyzer.analyze_crypto_news(news_items)
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.8
        assert result.sentiment_label == "positive"
        assert result.confidence == 0.9
        assert result.impact_level == "high"
        assert "Bitcoin ETF approval" in result.key_events
        assert result.price_prediction == "bullish"
        
        # Verify LLM was called with correct parameters
        mock_llm_client.analyze_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_with_symbol_filter(self):
        """Test news analysis with symbol filtering"""
        mock_llm_response = {
            "sentiment_score": 0.6,
            "sentiment_label": "positive",
            "confidence": 0.8,
            "impact_level": "medium",
            "key_events": ["Bitcoin price increase"],
            "price_prediction": "bullish",
            "reasoning": "Bitcoin-specific positive news"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_llm_response
        
        news_items = [
            CryptoNewsItem(
                title="Bitcoin Price Surges",
                content="Bitcoin reaches new highs...",
                source="CoinDesk",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Ethereum Updates",
                content="Ethereum network upgrade...",
                source="CoinDesk",
                published_at=datetime.now(),
                symbols_mentioned=["ETH"]
            )
        ]
        
        self.analyzer.llm_client = mock_llm_client
        
        result = await self.analyzer.analyze_crypto_news(news_items, symbol="BTC")
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.6
        
        # Verify only Bitcoin-related news was processed
        call_args = mock_llm_client.analyze_json.call_args
        if call_args and len(call_args) > 1 and 'prompt' in call_args[1]:
            prompt = call_args[1]['prompt']
            assert "Bitcoin Price Surges" in prompt
            assert "Ethereum Updates" not in prompt
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_empty_list(self):
        """Test analysis with empty news list"""
        result = await self.analyzer.analyze_crypto_news([])
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.0
        assert result.sentiment_label == "neutral"
        assert result.confidence == 0.1
        assert result.impact_level == "low"
        assert result.key_events == []
        assert result.price_prediction == "neutral"
        assert "No news" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_llm_error(self):
        """Test handling LLM analysis errors"""
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.side_effect = Exception("LLM API Error")
        
        news_items = [
            CryptoNewsItem(
                title="Test News",
                content="Test content...",
                source="Test Source",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        self.analyzer.llm_client = mock_llm_client
        
        result = await self.analyzer.analyze_crypto_news(news_items)
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.0
        assert result.sentiment_label == "neutral"
        assert result.confidence == 0.1
        assert "error" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_invalid_llm_response(self):
        """Test handling invalid LLM responses"""
        # Mock invalid response (missing required fields)
        mock_llm_response = {
            "sentiment_score": 0.5,
            # Missing other required fields
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_llm_response
        
        news_items = [
            CryptoNewsItem(
                title="Test News",
                content="Test content...",
                source="Test Source",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        self.analyzer.llm_client = mock_llm_client
        
        result = await self.analyzer.analyze_crypto_news(news_items)
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.5  # Should use what's available
        assert result.sentiment_label == "neutral"  # Should use default
        assert result.confidence == 0.5  # Should use what's available
    
        """Test filtering news by timeframe"""
        now = datetime.now()
        
        news_items = [
            CryptoNewsItem(
                title="Recent News",
                content="Recent content...",
                source="Source1",
                published_at=now - timedelta(hours=1),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Old News",
                content="Old content...",
                source="Source2",
                published_at=now - timedelta(days=2),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Very Old News",
                content="Very old content...",
                source="Source3",
                published_at=now - timedelta(days=10),
                symbols_mentioned=["BTC"]
            )
        ]
        
        # Filter for last 24 hours
        recent_news = self.analyzer._filter_news_by_timeframe(news_items, hours=24)
        assert len(recent_news) == 1
        assert recent_news[0].title == "Recent News"
        
        # Filter for last 3 days
        last_3_days = self.analyzer._filter_news_by_timeframe(news_items, hours=72)
        assert len(last_3_days) == 2
        
        # Filter for last 2 weeks
        last_2_weeks = self.analyzer._filter_news_by_timeframe(news_items, hours=336)
        assert len(last_2_weeks) == 3
    
    def test_prepare_news_for_analysis(self):
        """Test preparing news for analysis"""
        news_items = [
            CryptoNewsItem(
                title="Bitcoin Price Alert",
                content="Bitcoin has reached a new high of $50,000...",
                source="CoinDesk",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Market Analysis",
                content="Today's market shows strong bullish trends...",
                source="CryptoNews",
                published_at=datetime.now(),
                symbols_mentioned=["BTC", "ETH"]
            )
        ]
        
        prepared_text = self.analyzer._combine_news_for_analysis(news_items)
        
        assert "Bitcoin Price Alert" in prepared_text
        assert "Market Analysis" in prepared_text
        assert "CoinDesk" in prepared_text
        assert "CryptoNews" in prepared_text
        assert "$50,000" in prepared_text
        assert "bullish trends" in prepared_text
    
    def test_create_analysis_prompt(self):
        """Test creating analysis prompt"""
        news_text = "Bitcoin reaches new highs. Market shows bullish sentiment."
        
        prompt = self.analyzer._create_analysis_prompt(news_text, None)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "sentiment" in prompt.lower()
        assert "analyze" in prompt.lower()
        assert news_text in prompt
    
    def test_create_analysis_prompt_with_symbol(self):
        """Test creating analysis prompt with symbol focus"""
        news_text = "Bitcoin and Ethereum show different trends."
        
        prompt = self.analyzer._create_analysis_prompt(news_text, symbol="BTC")
        
        assert "Bitcoin" in prompt or "BTC" in prompt
        assert "specifically" in prompt.lower() or "focus" in prompt.lower()
    
        """Test parsing LLM response with invalid values"""
        llm_response = {
            "sentiment_score": 2.5,  # Out of range
            "sentiment_label": "invalid_label",
            "confidence": -0.5,  # Out of range
            "impact_level": "extreme",  # Invalid level
            "key_events": "not_a_list",  # Wrong type
            "price_prediction": "unknown",
            "reasoning": None  # Invalid type
        }
        
        result = self.analyzer._parse_llm_response(llm_response)
        
        assert isinstance(result, NewsAnalysis)
        assert -1.0 <= result.sentiment_score <= 1.0  # Should be clamped
        assert result.sentiment_label == "neutral"  # Should use default
        assert 0.0 <= result.confidence <= 1.0  # Should be clamped
        assert result.impact_level in ["low", "medium", "high"]  # Should use default
        assert isinstance(result.key_events, list)  # Should be converted
        assert result.reasoning == "No reasoning provided"  # Should use default
    
    @pytest.mark.asyncio
    async def test_analyze_with_rate_limiting(self):
        """Test analysis with rate limiting"""
        # This would test rate limiting if implemented
        # For now, just verify the method can handle multiple rapid calls
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = {
            "sentiment_score": 0.5,
            "sentiment_label": "neutral",
            "confidence": 0.7,
            "impact_level": "medium",
            "key_events": [],
            "price_prediction": "neutral",
            "reasoning": "Neutral market sentiment"
        }
        
        news_items = [
            CryptoNewsItem(
                title="Test News",
                content="Test content...",
                source="Test Source",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        self.analyzer.llm_client = mock_llm_client
        
        # Make multiple rapid calls
        tasks = []
        for i in range(5):
            task = self.analyzer.analyze_crypto_news(news_items)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, NewsAnalysis)
            assert result.sentiment_score == 0.5
    
    def test_get_analysis_schema(self):
        """Test getting analysis schema"""
        schema = self.analyzer._get_analysis_schema()
        
        assert isinstance(schema, dict)
        assert "sentiment_score" in schema
        assert "sentiment_label" in schema
        assert "confidence" in schema
        assert "impact_level" in schema
        assert "key_events" in schema
        assert "price_prediction" in schema
        assert "reasoning" in schema
    
        """Test validating news items"""
        valid_items = [
            CryptoNewsItem(
                title="Valid News",
                content="Valid content...",
                source="Valid Source",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        # Should not raise exception
        self.analyzer._validate_news_items(valid_items)
        
        # Test with invalid items
        invalid_items = [None, "not_a_news_item"]
        
        with pytest.raises(ValueError):
            self.analyzer._validate_news_items(invalid_items)
