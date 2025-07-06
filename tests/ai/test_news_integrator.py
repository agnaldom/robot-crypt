"""Test suite for AI news integrator module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.ai.news_integrator import NewsIntegrator
from src.ai.news_analyzer import CryptoNewsItem


class TestNewsIntegrator:
    """Test cases for NewsIntegrator class."""
    
    def setup_method(self):
        """Set up test news integrator."""
        with patch('src.ai.news_integrator.LLMNewsAnalyzer') as mock_analyzer, \
             patch('src.ai.news_integrator.NewsAPIClient') as mock_news_api, \
             patch('src.ai.news_integrator.CryptoPanicAPIClient') as mock_cryptopanic:
            
            # Mock the news analyzer
            self.mock_analyzer = Mock()
            mock_analyzer.return_value = self.mock_analyzer
            
            # Mock the API clients
            self.mock_news_api = Mock()
            self.mock_cryptopanic = Mock()
            mock_news_api.return_value = self.mock_news_api
            mock_cryptopanic.return_value = self.mock_cryptopanic
            
            self.integrator = NewsIntegrator()
            
    def create_sample_news_items(self):
        """Create sample news items for testing."""
        return [
            CryptoNewsItem(
                title="Bitcoin Reaches New All-Time High",
                content="Bitcoin has surged to a new record high of $75,000...",
                source="CoinDesk",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["BTC"],
                url="https://example.com/btc-ath"
            ),
            CryptoNewsItem(
                title="Ethereum Network Upgrade Successful",
                content="The latest Ethereum upgrade has been completed successfully...",
                source="CoinTelegraph",
                published_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["ETH"],
                url="https://example.com/eth-upgrade"
            ),
            CryptoNewsItem(
                title="Regulatory Clarity Boosts Crypto Market",
                content="New regulatory guidelines provide clarity for crypto markets...",
                source="The Block",
                published_at=datetime.now() - timedelta(hours=3),
                symbols_mentioned=["BTC", "ETH"],
                url="https://example.com/regulatory-clarity"
            )
        ]
    
    def test_news_integrator_initialization(self):
        """Test NewsIntegrator initialization."""
        assert self.integrator is not None
        assert hasattr(self.integrator, 'news_analyzer')
        assert hasattr(self.integrator, 'news_cache')
        assert hasattr(self.integrator, 'cache_duration')
        assert self.integrator.sources_available is True
        assert isinstance(self.integrator.news_cache, dict)
    
    def test_news_integrator_initialization_without_sources(self):
        """Test NewsIntegrator initialization when sources are not available."""
        with patch('src.ai.news_integrator.NewsAPIClient', side_effect=Exception("API not available")), \
             patch('src.ai.news_integrator.CryptoPanicAPIClient', side_effect=Exception("API not available")), \
             patch('src.ai.news_integrator.LLMNewsAnalyzer'):
            
            integrator = NewsIntegrator()
            assert integrator.sources_available is False
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_success(self):
        """Test successful market sentiment retrieval."""
        symbols = ["BTC", "ETH"]
        news_items = self.create_sample_news_items()
        
        # Mock news fetching
        with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
            mock_fetch.return_value = news_items
            
            # Mock news analyzer responses
            mock_sentiment_analysis = Mock()
            mock_sentiment_analysis.sentiment_score = 0.75
            mock_sentiment_analysis.sentiment_label = "bullish"
            mock_sentiment_analysis.confidence = 0.85
            mock_sentiment_analysis.impact_level = "high"
            mock_sentiment_analysis.key_events = ["Bitcoin ATH", "ETH upgrade"]
            mock_sentiment_analysis.price_prediction = "short_term_up"
            mock_sentiment_analysis.reasoning = "Strong positive sentiment from major developments"
            mock_sentiment_analysis.article_count = 3
            
            self.mock_analyzer.analyze_crypto_news = AsyncMock(return_value=mock_sentiment_analysis)
            self.mock_analyzer.detect_market_events = AsyncMock(return_value=[
                {"event_type": "price_milestone", "description": "Bitcoin ATH"},
                {"event_type": "technical", "description": "Ethereum upgrade"}
            ])
            
            result = await self.integrator.get_market_sentiment(symbols)
            
            assert isinstance(result, dict)
            assert result["sentiment_score"] == 0.75
            assert result["sentiment_label"] == "bullish"
            assert result["confidence"] == 0.85
            assert result["impact_level"] == "high"
            assert len(result["key_events"]) == 2
            assert result["price_prediction"] == "short_term_up"
            assert result["article_count"] == 3
            assert len(result["detected_events"]) == 2
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_no_news(self):
        """Test market sentiment retrieval when no news is found."""
        symbols = ["BTC"]
        
        # Mock empty news fetching
        with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
            mock_fetch.return_value = []
            
            result = await self.integrator.get_market_sentiment(symbols)
            
            assert isinstance(result, dict)
            assert result["sentiment_score"] == 0.0
            assert result["sentiment_label"] == "neutral"
            assert result["confidence"] == 0.1
            assert result["impact_level"] == "low"
            assert result["article_count"] == 0
            assert "Unable to analyze news sentiment" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_error_handling(self):
        """Test market sentiment retrieval error handling."""
        symbols = ["BTC"]
        
        # Mock fetch error
        with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
            mock_fetch.side_effect = Exception("News fetch error")
            
            result = await self.integrator.get_market_sentiment(symbols)
            
            assert isinstance(result, dict)
            assert result["sentiment_score"] == 0.0
            assert result["sentiment_label"] == "neutral"
            assert result["confidence"] == 0.1
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_with_sources(self):
        """Test fetching recent news with available sources."""
        symbols = ["BTC", "ETH"]
        
        # Mock news API responses
        mock_news_api_data = [
            {
                'title': 'Bitcoin News from NewsAPI',
                'description': 'Bitcoin content',
                'source': {'name': 'NewsAPI Source'},
                'publishedAt': datetime.now().isoformat(),
                'url': 'https://example.com/news1',
                'author': 'Author 1'
            }
        ]
        
        mock_cryptopanic_data = [
            {
                'title': 'Crypto News from CryptoPanic',
                'summary': 'Crypto content',
                'source': {'title': 'CryptoPanic Source'},
                'published_at': datetime.now().isoformat(),
                'currencies': ['BTC', 'ETH'],
                'url': 'https://example.com/news2'
            }
        ]
        
        with patch.object(self.integrator, '_fetch_news_api_news') as mock_news_api_fetch, \
             patch.object(self.integrator, '_fetch_cryptopanic_news') as mock_cryptopanic_fetch:
            
            mock_news_api_fetch.return_value = [
                CryptoNewsItem(
                    title="Bitcoin News from NewsAPI",
                    content="Bitcoin content",
                    source="NewsAPI Source",
                    published_at=datetime.now(),
                    symbols_mentioned=["BTC"],
                    url="https://example.com/news1"
                )
            ]
            
            mock_cryptopanic_fetch.return_value = [
                CryptoNewsItem(
                    title="Crypto News from CryptoPanic",
                    content="Crypto content",
                    source="CryptoPanic Source",
                    published_at=datetime.now(),
                    symbols_mentioned=["BTC", "ETH"],
                    url="https://example.com/news2"
                )
            ]
            
            news_items = await self.integrator._fetch_recent_news(symbols, 24)
            
            assert isinstance(news_items, list)
            assert len(news_items) == 2
            assert news_items[0].title == "Bitcoin News from NewsAPI"
            assert news_items[1].title == "Crypto News from CryptoPanic"
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_without_sources(self):
        """Test fetching recent news when sources are not available."""
        self.integrator.sources_available = False
        
        news_items = await self.integrator._fetch_recent_news(["BTC"], 24)
        
        assert isinstance(news_items, list)
        assert len(news_items) == 2  # Sample news items
        assert "Bitcoin Shows Steady Growth" in news_items[0].title
        assert "Ethereum Network Upgrades" in news_items[1].title
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_caching(self):
        """Test news fetching caching functionality."""
        symbols = ["BTC"]
        
        with patch.object(self.integrator, '_fetch_news_api_news') as mock_news_api_fetch, \
             patch.object(self.integrator, '_fetch_cryptopanic_news') as mock_cryptopanic_fetch:
            
            mock_news_api_fetch.return_value = []
            mock_cryptopanic_fetch.return_value = []
            
            # First call should fetch from sources
            news_items1 = await self.integrator._fetch_recent_news(symbols, 24)
            assert mock_news_api_fetch.call_count == 1
            assert mock_cryptopanic_fetch.call_count == 1
            
            # Reset mocks
            mock_news_api_fetch.reset_mock()
            mock_cryptopanic_fetch.reset_mock()
            
            # Second call should use cache
            news_items2 = await self.integrator._fetch_recent_news(symbols, 24)
            assert mock_news_api_fetch.call_count == 0
            assert mock_cryptopanic_fetch.call_count == 0
            
            # Results should be the same
            assert len(news_items1) == len(news_items2)
    
    @pytest.mark.asyncio
    async def test_fetch_news_api_news(self):
        """Test fetching news from News API."""
        symbols = ["BTC"]
        
        # Mock news API response
        mock_articles = [
            {
                'title': 'Bitcoin Price Surges',
                'description': 'Bitcoin reaches new heights',
                'source': {'name': 'CoinDesk'},
                'publishedAt': '2023-01-01T12:00:00Z',
                'url': 'https://example.com/btc-surge',
                'author': 'Crypto Reporter'
            }
        ]
        
        self.mock_news_api.get_crypto_news = AsyncMock(return_value=mock_articles)
        
        news_items = await self.integrator._fetch_news_api_news(symbols, 24)
        
        assert isinstance(news_items, list)
        assert len(news_items) == 1
        assert news_items[0].title == "Bitcoin Price Surges"
        assert news_items[0].source == "CoinDesk"
        assert "BTC" in news_items[0].symbols_mentioned
    
    @pytest.mark.asyncio
    async def test_fetch_news_api_news_error(self):
        """Test fetching news from News API with error."""
        symbols = ["BTC"]
        
        self.mock_news_api.get_crypto_news = AsyncMock(side_effect=Exception("API error"))
        
        news_items = await self.integrator._fetch_news_api_news(symbols, 24)
        
        assert isinstance(news_items, list)
        assert len(news_items) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_cryptopanic_news(self):
        """Test fetching news from CryptoPanic."""
        symbols = ["BTC", "ETH"]
        
        # Mock CryptoPanic response
        mock_news_data = [
            {
                'title': 'Crypto Market Update',
                'summary': 'Latest crypto market developments',
                'source': {'title': 'CryptoPanic'},
                'published_at': '2023-01-01T12:00:00Z',
                'currencies': ['BTC', 'ETH'],
                'url': 'https://example.com/crypto-update'
            }
        ]
        
        self.mock_cryptopanic.get_news = AsyncMock(return_value=mock_news_data)
        
        news_items = await self.integrator._fetch_cryptopanic_news(symbols, 24)
        
        assert isinstance(news_items, list)
        assert len(news_items) == 1
        assert news_items[0].title == "Crypto Market Update"
        assert news_items[0].source == "CryptoPanic"
        assert news_items[0].symbols_mentioned == ['BTC', 'ETH']
    
    @pytest.mark.asyncio
    async def test_fetch_cryptopanic_news_error(self):
        """Test fetching news from CryptoPanic with error."""
        symbols = ["BTC"]
        
        self.mock_cryptopanic.get_news = AsyncMock(side_effect=Exception("API error"))
        
        news_items = await self.integrator._fetch_cryptopanic_news(symbols, 24)
        
        assert isinstance(news_items, list)
        assert len(news_items) == 0
    
    def test_extract_symbols_from_text(self):
        """Test symbol extraction from text."""
        test_cases = [
            ("Bitcoin reaches new highs", ["BTC"]),
            ("Ethereum network upgrade completed", ["ETH"]),
            ("Bitcoin and Ethereum show strong performance", ["BTC", "ETH"]),
            ("Binance Coin and Cardano rally", ["BNB", "ADA"]),
            ("Solana, Dogecoin, and Polygon gain momentum", ["SOL", "DOGE", "MATIC"]),
            ("No crypto mentions here", []),
            ("BTC ETH ADA mentioned directly", ["BTC", "ETH", "ADA"])
        ]
        
        for text, expected_symbols in test_cases:
            symbols = self.integrator._extract_symbols_from_text(text)
            # Check that all expected symbols are present (order doesn't matter)
            for symbol in expected_symbols:
                assert symbol in symbols
    
    def test_create_sample_news(self):
        """Test creation of sample news."""
        sample_news = self.integrator._create_sample_news()
        
        assert isinstance(sample_news, list)
        assert len(sample_news) == 2
        
        # Check first sample news item
        assert "Bitcoin Shows Steady Growth" in sample_news[0].title
        assert sample_news[0].source == "Sample News"
        assert "BTC" in sample_news[0].symbols_mentioned
        
        # Check second sample news item
        assert "Ethereum Network Upgrades" in sample_news[1].title
        assert "ETH" in sample_news[1].symbols_mentioned
    
    def test_create_neutral_sentiment(self):
        """Test creation of neutral sentiment."""
        neutral_sentiment = self.integrator._create_neutral_sentiment()
        
        assert isinstance(neutral_sentiment, dict)
        assert neutral_sentiment["sentiment_score"] == 0.0
        assert neutral_sentiment["sentiment_label"] == "neutral"
        assert neutral_sentiment["confidence"] == 0.1
        assert neutral_sentiment["impact_level"] == "low"
        assert neutral_sentiment["article_count"] == 0
        assert "Unable to analyze news sentiment" in neutral_sentiment["reasoning"]
        assert "timestamp" in neutral_sentiment
    
    @pytest.mark.asyncio
    async def test_get_symbol_sentiment(self):
        """Test getting sentiment for a specific symbol."""
        symbol = "BTC"
        
        with patch.object(self.integrator, 'get_market_sentiment') as mock_get_market:
            mock_sentiment = {"sentiment_score": 0.8, "sentiment_label": "bullish"}
            mock_get_market.return_value = mock_sentiment
            
            result = await self.integrator.get_symbol_sentiment(symbol)
            
            assert result == mock_sentiment
            mock_get_market.assert_called_once_with([symbol])
    
    @pytest.mark.asyncio
    async def test_get_sentiment_summary(self):
        """Test getting sentiment summary for multiple symbols."""
        symbols = ["BTC", "ETH"]
        
        with patch.object(self.integrator, 'get_market_sentiment') as mock_get_market, \
             patch.object(self.integrator, 'get_symbol_sentiment') as mock_get_symbol:
            
            # Mock general market sentiment
            mock_get_market.return_value = {
                "sentiment_score": 0.6,
                "sentiment_label": "bullish",
                "confidence": 0.7
            }
            
            # Mock symbol-specific sentiments
            mock_get_symbol.side_effect = [
                {"sentiment_score": 0.8, "sentiment_label": "very_bullish"},
                {"sentiment_score": 0.4, "sentiment_label": "neutral"}
            ]
            
            result = await self.integrator.get_sentiment_summary(symbols)
            
            assert isinstance(result, dict)
            assert "market_general" in result
            assert "BTC" in result
            assert "ETH" in result
            
            assert result["market_general"]["sentiment_score"] == 0.6
            assert result["BTC"]["sentiment_score"] == 0.8
            assert result["ETH"]["sentiment_score"] == 0.4
    
    @pytest.mark.asyncio
    async def test_get_sentiment_summary_with_error(self):
        """Test getting sentiment summary when one symbol fails."""
        symbols = ["BTC", "ETH"]
        
        with patch.object(self.integrator, 'get_market_sentiment') as mock_get_market, \
             patch.object(self.integrator, 'get_symbol_sentiment') as mock_get_symbol:
            
            # Mock general market sentiment
            mock_get_market.return_value = {"sentiment_score": 0.5}
            
            # Mock one successful and one failed symbol sentiment
            mock_get_symbol.side_effect = [
                {"sentiment_score": 0.7},
                Exception("Symbol analysis failed")
            ]
            
            result = await self.integrator.get_sentiment_summary(symbols)
            
            assert isinstance(result, dict)
            assert "market_general" in result
            assert "BTC" in result
            assert "ETH" in result
            
            # BTC should have successful result
            assert result["BTC"]["sentiment_score"] == 0.7
            
            # ETH should have neutral result due to error
            assert result["ETH"]["sentiment_score"] == 0.0
            assert result["ETH"]["sentiment_label"] == "neutral"
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_duplicate_removal(self):
        """Test that duplicate news items are removed."""
        symbols = ["BTC"]
        
        with patch.object(self.integrator, '_fetch_news_api_news') as mock_news_api_fetch, \
             patch.object(self.integrator, '_fetch_cryptopanic_news') as mock_cryptopanic_fetch:
            
            # Return news items with duplicate titles
            duplicate_news = CryptoNewsItem(
                title="Same News Title",
                content="Content 1",
                source="Source 1",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
            
            another_duplicate = CryptoNewsItem(
                title="Same News Title",  # Same title
                content="Content 2",
                source="Source 2",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
            
            mock_news_api_fetch.return_value = [duplicate_news]
            mock_cryptopanic_fetch.return_value = [another_duplicate]
            
            news_items = await self.integrator._fetch_recent_news(symbols, 24)
            
            # Should only have one item due to duplicate removal
            assert len(news_items) == 1
            assert news_items[0].title == "Same News Title"


if __name__ == '__main__':
    pytest.main([__file__])
