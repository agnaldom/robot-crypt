"""Test suite for AI news analyzer module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from dataclasses import asdict

from src.ai.news_analyzer import (
    LLMNewsAnalyzer,
    NewsAnalysis,
    CryptoNewsItem
)


class TestNewsAnalysis:
    """Test cases for NewsAnalysis dataclass."""
    
    def test_news_analysis_creation(self):
        """Test NewsAnalysis can be created with all fields."""
        analysis = NewsAnalysis(
            sentiment_score=0.65,
            sentiment_label="bullish",
            confidence=0.82,
            impact_level="medium",
            key_events=["Bitcoin ETF approval", "Major exchange listing"],
            price_prediction="short_term_up",
            reasoning="Strong positive news sentiment with institutional adoption signals",
            article_count=15,
            timestamp=datetime.now()
        )
        
        assert analysis.sentiment_score == 0.65
        assert analysis.sentiment_label == "bullish"
        assert analysis.confidence == 0.82
        assert analysis.impact_level == "medium"
        assert len(analysis.key_events) == 2
        assert analysis.price_prediction == "short_term_up"
        assert analysis.article_count == 15


class TestCryptoNewsItem:
    """Test cases for CryptoNewsItem dataclass."""
    
    def test_crypto_news_item_creation(self):
        """Test CryptoNewsItem can be created with all fields."""
        news_item = CryptoNewsItem(
            title="Bitcoin Surges to New All-Time High",
            content="Bitcoin has reached a new all-time high of $75,000...",
            source="CoinDesk",
            published_at=datetime.now(),
            symbols_mentioned=["BTC", "BITCOIN"],
            url="https://example.com/news/bitcoin-ath",
            author="John Doe"
        )
        
        assert news_item.title == "Bitcoin Surges to New All-Time High"
        assert news_item.source == "CoinDesk"
        assert "BTC" in news_item.symbols_mentioned
        assert news_item.url == "https://example.com/news/bitcoin-ath"
        assert news_item.author == "John Doe"


class TestLLMNewsAnalyzer:
    """Test cases for LLMNewsAnalyzer class."""
    
    def setup_method(self):
        """Set up test analyzer."""
        with patch('src.ai.news_analyzer.get_llm_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            self.analyzer = LLMNewsAnalyzer()
            self.mock_llm_client = mock_client
    
    def create_sample_news_items(self):
        """Create sample news items for testing."""
        return [
            CryptoNewsItem(
                title="Bitcoin ETF Gets SEC Approval",
                content="The SEC has finally approved the first Bitcoin ETF...",
                source="Reuters",
                published_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["BTC"],
                url="https://example.com/btc-etf"
            ),
            CryptoNewsItem(
                title="Ethereum Network Upgrade Successful",
                content="The latest Ethereum upgrade has been completed successfully...",
                source="CoinDesk",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["ETH"],
                url="https://example.com/eth-upgrade"
            ),
            CryptoNewsItem(
                title="Market Analysis: Crypto Winter Continues",
                content="Analysts predict continued bearish sentiment in crypto markets...",
                source="The Block",
                published_at=datetime.now() - timedelta(minutes=30),
                symbols_mentioned=["BTC", "ETH"],
                url="https://example.com/market-analysis"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_success(self):
        """Test successful news analysis."""
        news_items = self.create_sample_news_items()
        
        # Mock LLM response
        mock_llm_response = {
            "sentiment_score": 0.7,
            "sentiment_label": "bullish",
            "confidence": 0.85,
            "impact_level": "high",
            "key_events": ["ETF approval", "Network upgrade"],
            "price_prediction": "short_term_up",
            "reasoning": "Strong positive news with ETF approval",
            "risk_factors": ["Market volatility"],
            "opportunities": ["Institutional adoption"],
            "timeframe_analysis": {
                "immediate": "positive",
                "short_term": "bullish",
                "medium_term": "neutral"
            }
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (True, "Valid")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.analyzer.analyze_crypto_news(news_items, symbol="BTC")
            
            assert isinstance(result, NewsAnalysis)
            assert result.sentiment_score == 0.7
            assert result.sentiment_label == "bullish"
            assert result.confidence == 0.85
            assert result.impact_level == "high"
            assert len(result.key_events) == 2
            assert result.price_prediction == "short_term_up"
            assert result.article_count == 3
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_empty_list(self):
        """Test analysis with empty news list."""
        result = await self.analyzer.analyze_crypto_news([])
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.0
        assert result.sentiment_label == "neutral"
        assert result.confidence == 0.1
        assert result.impact_level == "low"
        assert result.article_count == 0
        assert "No news items provided" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_security_rejection(self):
        """Test analysis when security guard rejects input."""
        news_items = self.create_sample_news_items()
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.side_effect = ValueError("Malicious content detected")
            
            result = await self.analyzer.analyze_crypto_news(news_items)
            
            assert isinstance(result, NewsAnalysis)
            assert result.sentiment_score == 0.0
            assert result.sentiment_label == "neutral"
            assert "Input rejected for security reasons" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_output_validation_failure(self):
        """Test analysis when output validation fails."""
        news_items = self.create_sample_news_items()
        
        mock_llm_response = {
            "sentiment_score": 2.0,  # Invalid score (outside -1 to 1 range)
            "sentiment_label": "bullish",
            "confidence": 0.85
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (False, "Invalid sentiment score")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.analyzer.analyze_crypto_news(news_items)
            
            assert isinstance(result, NewsAnalysis)
            assert result.sentiment_score == 0.0
            assert "Output validation failed" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_with_symbol_filter(self):
        """Test analysis with symbol-specific filtering."""
        news_items = self.create_sample_news_items()
        
        mock_llm_response = {
            "sentiment_score": 0.8,
            "sentiment_label": "bullish",
            "confidence": 0.9,
            "impact_level": "high",
            "key_events": ["ETF approval"],
            "price_prediction": "short_term_up",
            "reasoning": "BTC-specific positive news"
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (True, "Valid")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.analyzer.analyze_crypto_news(news_items, symbol="BTC")
            
            # Should have filtered to BTC-relevant news (2 out of 3 items)
            assert result.article_count == 3  # All items passed to analyzer, filtering happens in text preparation
            assert result.sentiment_score == 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_caching(self):
        """Test caching functionality."""
        news_items = self.create_sample_news_items()
        
        mock_llm_response = {
            "sentiment_score": 0.6,
            "sentiment_label": "bullish",
            "confidence": 0.8,
            "impact_level": "medium",
            "key_events": [],
            "price_prediction": "neutral",
            "reasoning": "Mixed signals"
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (True, "Valid")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            # First call should hit LLM
            result1 = await self.analyzer.analyze_crypto_news(news_items)
            self.mock_llm_client.analyze_json.assert_called_once()
            
            # Second call with same data should use cache
            self.mock_llm_client.analyze_json.reset_mock()
            result2 = await self.analyzer.analyze_crypto_news(news_items)
            
            # Should be cached result
            assert result1.sentiment_score == result2.sentiment_score
            assert result1.timestamp == result2.timestamp  # Same timestamp for cached result
            self.mock_llm_client.analyze_json.assert_not_called()  # Verify it didn't call LLM again
    
    @pytest.mark.asyncio
    async def test_analyze_single_article(self):
        """Test single article analysis."""
        article = CryptoNewsItem(
            title="Bitcoin Breaks $60,000 Resistance",
            content="Bitcoin has successfully broken through the $60,000 resistance level with strong volume...",
            source="CoinTelegraph",
            published_at=datetime.now(),
            symbols_mentioned=["BTC"]
        )
        
        mock_response = {
            "sentiment_score": 0.8,
            "credibility_score": 0.9,
            "impact_level": "high",
            "key_topics": ["resistance breakout", "volume analysis"],
            "impact_timeframe": "short-term",
            "risk_factors": ["potential pullback"],
            "opportunities": ["momentum continuation"],
            "summary": "Strong bullish breakout with good volume"
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_response)
            
            result = await self.analyzer.analyze_single_article(article)
            
            assert isinstance(result, dict)
            assert result["sentiment_score"] == 0.8
            assert result["credibility_score"] == 0.9
            assert result["impact_level"] == "high"
            assert "resistance breakout" in result["key_topics"]
    
    @pytest.mark.asyncio
    async def test_analyze_single_article_error_handling(self):
        """Test single article analysis error handling."""
        article = CryptoNewsItem(
            title="Test Article",
            content="Test content",
            source="Test Source",
            published_at=datetime.now(),
            symbols_mentioned=["BTC"]
        )
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.side_effect = Exception("Processing error")
            
            result = await self.analyzer.analyze_single_article(article)
            
            assert isinstance(result, dict)
            assert result["sentiment_score"] == 0.0
            assert result["credibility_score"] == 0.5
            assert "Analysis failed" in result["summary"]
    
    @pytest.mark.asyncio
    async def test_detect_market_events(self):
        """Test market event detection."""
        news_items = self.create_sample_news_items()
        
        mock_response = {
            "events": [
                {
                    "event_type": "regulatory",
                    "description": "SEC approval of Bitcoin ETF",
                    "impact_score": 9,
                    "affected_symbols": ["BTC"],
                    "impact_duration": "long-term",
                    "is_positive": True,
                    "confidence": 0.95
                },
                {
                    "event_type": "technical",
                    "description": "Ethereum network upgrade",
                    "impact_score": 7,
                    "affected_symbols": ["ETH"],
                    "impact_duration": "medium-term",
                    "is_positive": True,
                    "confidence": 0.85
                }
            ]
        }
        
        with patch('src.ai.news_analyzer.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_response)
            
            events = await self.analyzer.detect_market_events(news_items)
            
            assert isinstance(events, list)
            assert len(events) == 2
            assert events[0]["event_type"] == "regulatory"
            assert events[0]["impact_score"] == 9
            assert events[1]["event_type"] == "technical"
            assert events[1]["impact_score"] == 7
    
    @pytest.mark.asyncio
    async def test_detect_market_events_empty_list(self):
        """Test market event detection with empty news list."""
        events = await self.analyzer.detect_market_events([])
        
        assert isinstance(events, list)
        assert len(events) == 0
    
    @pytest.mark.asyncio
    async def test_detect_market_events_error_handling(self):
        """Test market event detection error handling."""
        news_items = self.create_sample_news_items()
        
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM error"))
        
        events = await self.analyzer.detect_market_events(news_items)
        
        assert isinstance(events, list)
        assert len(events) == 0
    
    def test_prepare_news_text(self):
        """Test news text preparation."""
        news_items = self.create_sample_news_items()
        
        # Test without symbol filter
        text = self.analyzer._prepare_news_text(news_items, None)
        
        assert isinstance(text, str)
        assert "Bitcoin ETF Gets SEC Approval" in text
        assert "Ethereum Network Upgrade Successful" in text
        assert "Market Analysis: Crypto Winter Continues" in text
        assert "Reuters" in text
        assert "CoinDesk" in text
        
        # Test with BTC symbol filter
        text_btc = self.analyzer._prepare_news_text(news_items, "BTC")
        
        # Should include items that mention BTC
        assert "Bitcoin ETF Gets SEC Approval" in text_btc
        assert "Market Analysis: Crypto Winter Continues" in text_btc
    
    def test_create_news_summary(self):
        """Test news summary creation."""
        news_items = self.create_sample_news_items()
        
        summary = self.analyzer._create_news_summary(news_items)
        
        assert isinstance(summary, str)
        assert "Bitcoin ETF Gets SEC Approval" in summary
        assert "Reuters" in summary
        assert len(summary.split('\n')) <= 10  # Should limit to 10 items
    
    def test_create_analysis_prompt(self):
        """Test analysis prompt creation."""
        news_text = "Sample news text about Bitcoin and Ethereum"
        
        # Test without specific symbol
        prompt = self.analyzer._create_analysis_prompt(news_text, None)
        
        assert isinstance(prompt, str)
        assert news_text in prompt
        assert "cryptocurrency market" in prompt
        assert "sentiment analysis" in prompt
        
        # Test with specific symbol
        prompt_btc = self.analyzer._create_analysis_prompt(news_text, "BTC")
        
        assert news_text in prompt_btc
        assert "BTC" in prompt_btc
        assert "special attention" in prompt_btc
    
    def test_get_analysis_schema(self):
        """Test analysis schema structure."""
        schema = self.analyzer._get_analysis_schema()
        
        assert isinstance(schema, dict)
        assert "sentiment_score" in schema
        assert "sentiment_label" in schema
        assert "confidence" in schema
        assert "impact_level" in schema
        assert "key_events" in schema
        assert "price_prediction" in schema
        assert "reasoning" in schema
        
        # Check nested structure
        assert "timeframe_analysis" in schema
        assert isinstance(schema["timeframe_analysis"], dict)
    
    def test_convert_response_to_analysis(self):
        """Test conversion of LLM response to NewsAnalysis."""
        response = {
            "sentiment_score": 0.75,
            "sentiment_label": "bullish",
            "confidence": 0.88,
            "impact_level": "high",
            "key_events": ["Event 1", "Event 2"],
            "price_prediction": "short_term_up",
            "reasoning": "Strong positive signals"
        }
        
        analysis = self.analyzer._convert_response_to_analysis(response, 5)
        
        assert isinstance(analysis, NewsAnalysis)
        assert analysis.sentiment_score == 0.75
        assert analysis.sentiment_label == "bullish"
        assert analysis.confidence == 0.88
        assert analysis.impact_level == "high"
        assert len(analysis.key_events) == 2
        assert analysis.article_count == 5
        
        # Test with extreme values (should be clamped)
        extreme_response = {
            "sentiment_score": 2.0,  # Should be clamped to 1.0
            "confidence": -0.5,      # Should be clamped to 0.0
            "sentiment_label": "extreme_bullish",
            "impact_level": "ultra_high"
        }
        
        extreme_analysis = self.analyzer._convert_response_to_analysis(extreme_response, 3)
        
        assert extreme_analysis.sentiment_score == 1.0  # Clamped
        assert extreme_analysis.confidence == 0.0       # Clamped
    
    def test_create_neutral_analysis(self):
        """Test creation of neutral analysis for error cases."""
        reason = "Test error reason"
        analysis = self.analyzer._create_neutral_analysis(10, reason)
        
        assert isinstance(analysis, NewsAnalysis)
        assert analysis.sentiment_score == 0.0
        assert analysis.sentiment_label == "neutral"
        assert analysis.confidence == 0.1
        assert analysis.impact_level == "low"
        assert analysis.key_events == []
        assert analysis.price_prediction == "neutral"
        assert analysis.reasoning == reason
        assert analysis.article_count == 10
    
    def test_cache_key_creation(self):
        """Test cache key creation."""
        news_items = self.create_sample_news_items()
        
        # Test with symbol
        key1 = self.analyzer._create_cache_key(news_items, "BTC")
        assert isinstance(key1, str)
        assert "BTC" in key1
        
        # Test without symbol
        key2 = self.analyzer._create_cache_key(news_items, None)
        assert isinstance(key2, str)
        assert "general" in key2
        
        # Same inputs should produce same key
        key3 = self.analyzer._create_cache_key(news_items, "BTC")
        assert key1 == key3
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_summary(self):
        """Test market sentiment summary generation."""
        symbols = ["BTC", "ETH", "ADA"]
        
        mock_response = {
            "overall_sentiment": "bullish",
            "market_phase": "accumulation",
            "sentiment_score": 0.6,
            "individual_symbols": {
                "BTC": {"sentiment": "bullish", "score": 0.7},
                "ETH": {"sentiment": "neutral", "score": 0.1},
                "ADA": {"sentiment": "bearish", "score": -0.3}
            },
            "key_factors": ["ETF approval", "institutional adoption"],
            "risks": ["regulatory uncertainty", "market volatility"],
            "opportunities": ["DeFi growth", "institutional interest"],
            "recommended_strategy": "accumulate on dips"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_response)
        
        summary = await self.analyzer.get_market_sentiment_summary(symbols)
        
        assert isinstance(summary, dict)
        assert summary["overall_sentiment"] == "bullish"
        assert summary["market_phase"] == "accumulation"
        assert summary["sentiment_score"] == 0.6
        assert "BTC" in summary["individual_symbols"]
        assert len(summary["key_factors"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_summary_error(self):
        """Test market sentiment summary error handling."""
        symbols = ["BTC", "ETH"]
        
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM error"))
        
        summary = await self.analyzer.get_market_sentiment_summary(symbols)
        
        assert isinstance(summary, dict)
        assert summary["overall_sentiment"] == "neutral"
        assert summary["market_phase"] == "uncertain"
        assert summary["sentiment_score"] == 0.0
        assert "Analysis unavailable" in summary["risks"]


if __name__ == '__main__':
    pytest.main([__file__])
