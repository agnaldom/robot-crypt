#!/usr/bin/env python3
"""
NewsAPI Client for General Cryptocurrency and Financial News
Provides access to mainstream news sources for broader market context.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import re

from src.core.config import settings

logger = logging.getLogger(__name__)


class NewsAPIClient:
    """
    NewsAPI Client for fetching general cryptocurrency and financial news
    Requires API key from NewsAPI.org
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NewsAPI client.
        
        Args:
            api_key: NewsAPI key (optional, will use from settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'NEWS_API_KEY', None)
        self.base_url = "https://newsapi.org/v2"
        self.session = None
        self.rate_limit_delay = 1.0  # 1 second between requests for free tier
        self.last_request_time = 0
        
        # Cryptocurrency keywords for filtering
        self.crypto_keywords = [
            "bitcoin", "btc", "ethereum", "eth", "cryptocurrency", "crypto", 
            "blockchain", "defi", "nft", "binance", "coinbase", "dogecoin", 
            "shiba", "cardano", "solana", "polygon", "avalanche", "chainlink",
            "uniswap", "ripple", "litecoin", "digital currency", "altcoin",
            "stablecoin", "web3", "metaverse", "mining", "wallet", "exchange"
        ]
        
        # Financial keywords for broader context
        self.financial_keywords = [
            "federal reserve", "inflation", "interest rates", "stock market",
            "nasdaq", "s&p 500", "dow jones", "gold", "dollar", "economy",
            "recession", "bull market", "bear market", "trading", "investment"
        ]
        
        # Sentiment keywords for basic analysis
        self.positive_keywords = [
            "surge", "rally", "gain", "rise", "bull", "bullish", "positive",
            "growth", "adoption", "breakthrough", "partnership", "launch",
            "approval", "success", "optimistic", "recovery", "upward"
        ]
        
        self.negative_keywords = [
            "crash", "plunge", "fall", "drop", "bear", "bearish", "negative",
            "decline", "loss", "ban", "hack", "scam", "regulation", "warning",
            "concern", "selloff", "collapse", "downward", "volatile"
        ]
        
        if not self.api_key:
            logger.warning("NewsAPI key not provided. Some features may not work.")
        else:
            logger.info("NewsAPIClient initialized with API key")
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'User-Agent': 'Robot-Crypt/1.0.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting to respect NewsAPI limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to NewsAPI with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.session:
            raise Exception("HTTP session not initialized. Use async context manager.")
        
        if not self.api_key:
            logger.error("NewsAPI key is required for API requests")
            return None
        
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful NewsAPI request: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"NewsAPI rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                elif response.status == 401:
                    logger.error("NewsAPI key is invalid or missing")
                    return None
                elif response.status == 400:
                    logger.error(f"NewsAPI bad request: {endpoint}")
                    return None
                else:
                    logger.error(f"NewsAPI error: {response.status} - {endpoint}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"NewsAPI request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in NewsAPI request: {e}")
            return None
    
    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text using keyword matching.
        
        Args:
            text: Text to analyze (title + description)
            
        Returns:
            Tuple of (sentiment, score) where sentiment is 'positive', 'negative', or 'neutral'
            and score is between -1 and 1
        """
        try:
            text_lower = text.lower()
            
            positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
            negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
            
            total_keywords = positive_count + negative_count
            
            if total_keywords == 0:
                return "neutral", 0.0
            
            # Calculate sentiment score
            score = (positive_count - negative_count) / total_keywords
            
            # Determine sentiment category
            if score > 0.3:
                return "positive", score
            elif score < -0.3:
                return "negative", score
            else:
                return "neutral", score
                
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return "neutral", 0.0
    
    def _is_crypto_related(self, title: str, description: str) -> bool:
        """
        Check if an article is cryptocurrency related.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            True if crypto-related, False otherwise
        """
        try:
            text = f"{title} {description}".lower()
            return any(keyword in text for keyword in self.crypto_keywords)
        except Exception:
            return False
    
    def _calculate_relevance(self, title: str, description: str) -> float:
        """
        Calculate relevance score for an article.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            Relevance score between 0 and 1
        """
        try:
            text = f"{title} {description}".lower()
            
            # Count crypto keywords
            crypto_matches = sum(1 for keyword in self.crypto_keywords if keyword in text)
            financial_matches = sum(1 for keyword in self.financial_keywords if keyword in text)
            
            # Weight crypto keywords higher
            relevance_score = (crypto_matches * 0.8 + financial_matches * 0.2) / 10
            
            return min(relevance_score, 1.0)
            
        except Exception:
            return 0.0
    
    async def get_everything(
        self,
        query: str,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "relevancy",
        page: int = 1,
        page_size: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get articles from NewsAPI everything endpoint.
        
        Args:
            query: Search query
            sources: Comma-separated list of sources
            domains: Comma-separated list of domains
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            language: Language code
            sort_by: Sort order (relevancy, popularity, publishedAt)
            page: Page number
            page_size: Articles per page (max 100)
            
        Returns:
            List of articles
        """
        try:
            params = {
                'q': query,
                'language': language,
                'sortBy': sort_by,
                'page': page,
                'pageSize': min(page_size, 100)
            }
            
            if sources:
                params['sources'] = sources
            if domains:
                params['domains'] = domains
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            data = await self._make_request("everything", params)
            
            if data and 'articles' in data:
                articles = []
                
                for article in data['articles']:
                    title = article.get('title', '')
                    description = article.get('description', '') or ''
                    
                    # Analyze sentiment
                    sentiment, sentiment_score = self._analyze_sentiment(f"{title} {description}")
                    
                    # Calculate relevance
                    relevance = self._calculate_relevance(title, description)
                    
                    # Parse published date
                    published_at = article.get('publishedAt', '')
                    try:
                        parsed_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        parsed_date = datetime.now()
                    
                    article_data = {
                        "title": title,
                        "description": description,
                        "url": article.get('url'),
                        "source": article.get('source', {}).get('name', 'Unknown'),
                        "author": article.get('author'),
                        "published_at": parsed_date.isoformat(),
                        "url_to_image": article.get('urlToImage'),
                        "content": article.get('content'),
                        "sentiment": sentiment,
                        "sentiment_score": sentiment_score,
                        "relevance_score": relevance,
                        "is_crypto_related": self._is_crypto_related(title, description),
                        "source_type": "news_api"
                    }
                    
                    articles.append(article_data)
                
                return articles
            else:
                logger.warning("No articles data received from NewsAPI")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return None
    
    async def get_crypto_news(
        self,
        query: str = "cryptocurrency OR bitcoin OR ethereum OR blockchain",
        days_back: int = 7,
        limit: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cryptocurrency-related news.
        
        Args:
            query: Search query for crypto news
            days_back: Number of days to look back
            limit: Maximum number of articles
            
        Returns:
            List of crypto news articles
        """
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            articles = await self.get_everything(
                query=query,
                from_date=from_date,
                sort_by="relevancy",
                page_size=limit
            )
            
            if articles:
                # Filter for crypto-related articles and sort by relevance
                crypto_articles = [
                    article for article in articles 
                    if article['is_crypto_related'] or article['relevance_score'] > 0.3
                ]
                
                crypto_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
                return crypto_articles[:limit]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return None
    
    async def get_financial_news(
        self,
        query: str = "stock market OR federal reserve OR inflation OR economy",
        days_back: int = 7,
        limit: int = 30
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get financial news for broader market context.
        
        Args:
            query: Search query for financial news
            days_back: Number of days to look back
            limit: Maximum number of articles
            
        Returns:
            List of financial news articles
        """
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            articles = await self.get_everything(
                query=query,
                from_date=from_date,
                sort_by="relevancy",
                page_size=limit,
                domains="reuters.com,bloomberg.com,cnbc.com,marketwatch.com,wsj.com"
            )
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching financial news: {e}")
            return None
    
    async def get_headlines(
        self,
        country: str = "us",
        category: str = "business",
        sources: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get top headlines from NewsAPI.
        
        Args:
            country: Country code (us, gb, etc.)
            category: News category
            sources: Specific sources
            query: Search query
            page_size: Number of articles
            
        Returns:
            List of headline articles
        """
        try:
            params = {
                'pageSize': min(page_size, 100)
            }
            
            if sources:
                params['sources'] = sources
            else:
                params['country'] = country
                params['category'] = category
            
            if query:
                params['q'] = query
            
            data = await self._make_request("top-headlines", params)
            
            if data and 'articles' in data:
                articles = []
                
                for article in data['articles']:
                    title = article.get('title', '')
                    description = article.get('description', '') or ''
                    
                    # Analyze sentiment
                    sentiment, sentiment_score = self._analyze_sentiment(f"{title} {description}")
                    
                    # Parse published date
                    published_at = article.get('publishedAt', '')
                    try:
                        parsed_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        parsed_date = datetime.now()
                    
                    article_data = {
                        "title": title,
                        "description": description,
                        "url": article.get('url'),
                        "source": article.get('source', {}).get('name', 'Unknown'),
                        "author": article.get('author'),
                        "published_at": parsed_date.isoformat(),
                        "url_to_image": article.get('urlToImage'),
                        "content": article.get('content'),
                        "sentiment": sentiment,
                        "sentiment_score": sentiment_score,
                        "is_crypto_related": self._is_crypto_related(title, description),
                        "source_type": "headlines"
                    }
                    
                    articles.append(article_data)
                
                return articles
            else:
                logger.warning("No headlines data received from NewsAPI")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching headlines: {e}")
            return None
    
    async def get_market_context_news(self, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive market context news including crypto and financial news.
        
        Args:
            limit: Total number of articles to return
            
        Returns:
            Dictionary with categorized news
        """
        try:
            # Get crypto news
            crypto_news = await self.get_crypto_news(limit=limit//2)
            
            # Get financial headlines for context
            financial_news = await self.get_financial_news(limit=limit//2)
            
            # Get business headlines
            business_headlines = await self.get_headlines(
                category="business",
                query="cryptocurrency OR bitcoin OR blockchain",
                page_size=10
            )
            
            return {
                "crypto_news": crypto_news or [],
                "financial_news": financial_news or [],
                "business_headlines": business_headlines or [],
                "total_articles": len(crypto_news or []) + len(financial_news or []) + len(business_headlines or []),
                "timestamp": datetime.now().isoformat(),
                "source": "news_api"
            }
            
        except Exception as e:
            logger.error(f"Error fetching market context news: {e}")
            return None


# Convenience functions for easy usage
async def get_crypto_news_articles(
    query: str = "cryptocurrency OR bitcoin OR ethereum",
    days_back: int = 7,
    limit: int = 20,
    api_key: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get cryptocurrency news articles.
    
    Args:
        query: Search query
        days_back: Days to look back
        limit: Number of articles
        api_key: NewsAPI key
        
    Returns:
        List of news articles
    """
    async with NewsAPIClient(api_key) as client:
        return await client.get_crypto_news(query=query, days_back=days_back, limit=limit)


async def get_market_news_context(api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive market news context.
    
    Args:
        api_key: NewsAPI key
        
    Returns:
        Market news context
    """
    async with NewsAPIClient(api_key) as client:
        return await client.get_market_context_news()


# Example usage
async def main():
    """Example usage of the NewsAPI client."""
    
    print("Testing NewsAPI client...")
    
    # Note: You need a valid API key for this to work
    api_key = getattr(settings, 'NEWS_API_KEY', None)
    
    if not api_key:
        print("⚠️  NewsAPI key not found. Please set NEWS_API_KEY in settings.")
        return
    
    async with NewsAPIClient(api_key) as client:
        # Test crypto news
        print("\n1. Testing crypto news...")
        crypto_news = await client.get_crypto_news(limit=5)
        if crypto_news:
            print("Cryptocurrency news:")
            for article in crypto_news:
                print(f"  {article['title']} - {article['source']} ({article['sentiment']})")
        
        # Test financial news
        print("\n2. Testing financial news...")
        financial_news = await client.get_financial_news(limit=3)
        if financial_news:
            print("Financial news:")
            for article in financial_news:
                print(f"  {article['title']} - {article['source']}")
        
        # Test market context
        print("\n3. Testing market context news...")
        market_context = await client.get_market_context_news(limit=10)
        if market_context:
            print(f"Market context: {market_context['total_articles']} articles")
            print(f"  Crypto: {len(market_context['crypto_news'])}")
            print(f"  Financial: {len(market_context['financial_news'])}")
            print(f"  Headlines: {len(market_context['business_headlines'])}")


if __name__ == "__main__":
    asyncio.run(main())
