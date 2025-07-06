#!/usr/bin/env python3
"""
CryptoPanic API Client for Cryptocurrency News with Sentiment Analysis
Provides access to curated cryptocurrency news with sentiment scoring.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class CryptoPanicAPIClient:
    """
    CryptoPanic API Client for fetching cryptocurrency news with sentiment analysis
    Supports both free and pro API tiers
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CryptoPanic API client.
        
        Args:
            api_key: CryptoPanic API key (optional, will use from settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'CRYPTOPANIC_API_KEY', None)
        self.base_url = "https://cryptopanic.com/api"
        self.session = None
        self.rate_limit_delay = 1.0  # 1 second between requests for free tier
        self.last_request_time = 0
        
        # News filters and categories
        self.news_filters = {
            "rising": "trending",
            "hot": "popular",
            "bullish": "positive",
            "bearish": "negative",
            "important": "important",
            "saved": "saved",
            "lol": "funny"
        }
        
        # Currency mappings
        self.currency_mappings = {
            "BTC": "BTC",
            "ETH": "ETH", 
            "BNB": "BNB",
            "ADA": "ADA",
            "DOT": "DOT",
            "LINK": "LINK",
            "UNI": "UNI",
            "DOGE": "DOGE",
            "SHIB": "SHIB",
            "SOL": "SOL",
            "MATIC": "MATIC",
            "AVAX": "AVAX",
            "XRP": "XRP",
            "LTC": "LTC"
        }
        
        if not self.api_key:
            logger.warning("CryptoPanic API key not provided. Using free tier with limited features.")
        else:
            logger.info("CryptoPanicAPIClient initialized with API key")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
            headers={
                'User-Agent': 'Robot-Crypt/1.0.0',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting to respect CryptoPanic limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to CryptoPanic API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.session:
            raise Exception("HTTP session not initialized. Use async context manager.")
        
        await self._rate_limit()
        
        # Determine API version based on availability of API key
        api_version = "v1" if self.api_key else "free/v1"
        url = f"{self.base_url}/{api_version}/{endpoint}"
        
        params = params or {}
        if self.api_key:
            params['auth_token'] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful CryptoPanic API request: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"CryptoPanic rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                elif response.status == 401:
                    logger.error("CryptoPanic API key is invalid or missing")
                    return None
                elif response.status == 400:
                    logger.error(f"CryptoPanic API bad request: {endpoint}")
                    return None
                else:
                    logger.error(f"CryptoPanic API error: {response.status} - {endpoint}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"CryptoPanic API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in CryptoPanic API request: {e}")
            return None
    
    def _analyze_sentiment(self, votes: Dict) -> tuple[str, float]:
        """
        Analyze sentiment from CryptoPanic votes.
        
        Args:
            votes: Votes data from API
            
        Returns:
            Tuple of (sentiment, score) where sentiment is 'positive', 'negative', or 'neutral'
            and score is between -1 and 1
        """
        try:
            negative = votes.get('negative', 0)
            positive = votes.get('positive', 0)
            important = votes.get('important', 0)
            liked = votes.get('liked', 0)
            disliked = votes.get('disliked', 0)
            lol = votes.get('lol', 0)
            toxic = votes.get('toxic', 0)
            saved = votes.get('saved', 0)
            
            # Calculate weighted sentiment score
            total_positive = positive + liked + important + saved
            total_negative = negative + disliked + toxic
            total_neutral = lol  # LOL is generally neutral
            
            total_votes = total_positive + total_negative + total_neutral
            
            if total_votes == 0:
                return "neutral", 0.0
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = (total_positive - total_negative) / total_votes
            
            # Determine sentiment category
            if sentiment_score > 0.2:
                return "positive", sentiment_score
            elif sentiment_score < -0.2:
                return "negative", sentiment_score
            else:
                return "neutral", sentiment_score
                
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return "neutral", 0.0
    
    def _parse_published_date(self, published_at: str) -> Optional[datetime]:
        """
        Parse published date string to datetime object.
        
        Args:
            published_at: Date string from API
            
        Returns:
            Parsed datetime or None
        """
        try:
            # CryptoPanic uses ISO format with timezone
            return datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse date: {published_at}")
            return None
    
    async def get_posts(
        self,
        filter_type: str = "hot",
        currencies: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cryptocurrency news posts.
        
        Args:
            filter_type: Filter type (hot, trending, bullish, bearish, important, saved, lol)
            currencies: List of currency codes to filter by
            regions: List of region codes to filter by
            page: Page number (1-based)
            limit: Number of posts per page
            
        Returns:
            List of news posts
        """
        try:
            params = {
                'filter': filter_type,
                'page': page,
                'limit': min(limit, 100)  # API limit
            }
            
            if currencies:
                # Convert symbols to CryptoPanic format
                crypto_currencies = []
                for currency in currencies:
                    mapped_currency = self.currency_mappings.get(currency.upper(), currency.upper())
                    crypto_currencies.append(mapped_currency)
                params['currencies'] = ','.join(crypto_currencies)
            
            if regions:
                params['regions'] = ','.join(regions)
            
            data = await self._make_request("posts", params)
            
            if data and 'results' in data:
                posts = []
                
                for post in data['results']:
                    # Analyze sentiment from votes
                    sentiment, sentiment_score = self._analyze_sentiment(post.get('votes', {}))
                    
                    # Parse published date
                    published_date = self._parse_published_date(post.get('published_at', ''))
                    
                    post_data = {
                        "id": post.get('id'),
                        "title": post.get('title'),
                        "url": post.get('url'),
                        "source": post.get('source', {}).get('title', 'Unknown'),
                        "domain": post.get('source', {}).get('domain'),
                        "published_at": published_date.isoformat() if published_date else None,
                        "created_at": post.get('created_at'),
                        "sentiment": sentiment,
                        "sentiment_score": sentiment_score,
                        "votes": post.get('votes', {}),
                        "currencies": [
                            {
                                "code": currency.get('code'),
                                "title": currency.get('title'),
                                "slug": currency.get('slug'),
                                "url": currency.get('url')
                            }
                            for currency in post.get('currencies', [])
                        ],
                        "kind": post.get('kind'),  # news, media, article
                        "metadata": post.get('metadata', {}),
                        "importance": self._calculate_importance(post)
                    }
                    
                    posts.append(post_data)
                
                return posts
            else:
                logger.warning("No posts data received from CryptoPanic")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return None
    
    def _calculate_importance(self, post: Dict) -> str:
        """
        Calculate post importance based on various factors.
        
        Args:
            post: Post data from API
            
        Returns:
            Importance level (high, medium, low)
        """
        try:
            votes = post.get('votes', {})
            total_votes = sum(votes.values())
            important_votes = votes.get('important', 0)
            
            # High importance criteria
            if important_votes > 10 or total_votes > 50:
                return "high"
            elif important_votes > 5 or total_votes > 20:
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "low"
    
    async def get_trending_news(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get trending cryptocurrency news.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of trending news posts
        """
        try:
            return await self.get_posts(filter_type="rising", limit=limit)
        except Exception as e:
            logger.error(f"Error fetching trending news: {e}")
            return None
    
    async def get_bullish_news(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get bullish cryptocurrency news.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of bullish news posts
        """
        try:
            return await self.get_posts(filter_type="bullish", limit=limit)
        except Exception as e:
            logger.error(f"Error fetching bullish news: {e}")
            return None
    
    async def get_bearish_news(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get bearish cryptocurrency news.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of bearish news posts
        """
        try:
            return await self.get_posts(filter_type="bearish", limit=limit)
        except Exception as e:
            logger.error(f"Error fetching bearish news: {e}")
            return None
    
    async def get_important_news(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get important cryptocurrency news.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of important news posts
        """
        try:
            return await self.get_posts(filter_type="important", limit=limit)
        except Exception as e:
            logger.error(f"Error fetching important news: {e}")
            return None
    
    async def get_news_by_currency(self, currency: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get news for a specific cryptocurrency.
        
        Args:
            currency: Cryptocurrency symbol (e.g., BTC, ETH)
            limit: Maximum number of posts to return
            
        Returns:
            List of news posts for the currency
        """
        try:
            return await self.get_posts(currencies=[currency], limit=limit)
        except Exception as e:
            logger.error(f"Error fetching news for {currency}: {e}")
            return None
    
    async def get_sentiment_analysis(self, currency: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get sentiment analysis for a specific cryptocurrency.
        
        Args:
            currency: Cryptocurrency symbol
            days: Number of days to analyze (not directly supported by API, but we filter client-side)
            
        Returns:
            Sentiment analysis results
        """
        try:
            # Get recent news for the currency
            posts = await self.get_news_by_currency(currency, limit=100)
            
            if not posts:
                return None
            
            # Filter posts by date range (client-side filtering)
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_posts = []
            
            for post in posts:
                if post['published_at']:
                    published_date = datetime.fromisoformat(post['published_at'])
                    if published_date >= cutoff_date:
                        recent_posts.append(post)
            
            if not recent_posts:
                return {
                    "currency": currency,
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "post_count": 0,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "analyzed_days": days
                }
            
            # Calculate sentiment distribution
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total_score = 0.0
            
            for post in recent_posts:
                sentiment_counts[post['sentiment']] += 1
                total_score += post['sentiment_score']
            
            # Calculate overall metrics
            total_posts = len(recent_posts)
            avg_sentiment_score = total_score / total_posts
            
            # Determine overall sentiment
            if avg_sentiment_score > 0.2:
                overall_sentiment = "positive"
            elif avg_sentiment_score < -0.2:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            # Calculate confidence based on post count and sentiment consistency
            confidence = min(0.5 + (total_posts / 100), 0.95)
            
            return {
                "currency": currency,
                "sentiment": overall_sentiment,
                "sentiment_score": avg_sentiment_score,
                "confidence": confidence,
                "post_count": total_posts,
                "sentiment_distribution": sentiment_counts,
                "analyzed_days": days,
                "source": "cryptopanic"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {currency}: {e}")
            return None
    
    async def get_market_sentiment_overview(self, currencies: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get overall market sentiment overview.
        
        Args:
            currencies: List of currencies to analyze (if None, analyzes general market)
            
        Returns:
            Market sentiment overview
        """
        try:
            # Get hot news posts
            hot_posts = await self.get_posts(filter_type="hot", currencies=currencies, limit=50)
            
            if not hot_posts:
                return None
            
            # Analyze overall sentiment
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total_score = 0.0
            
            for post in hot_posts:
                sentiment_counts[post['sentiment']] += 1
                total_score += post['sentiment_score']
            
            total_posts = len(hot_posts)
            avg_sentiment_score = total_score / total_posts
            
            # Determine overall market sentiment
            if avg_sentiment_score > 0.1:
                market_sentiment = "positive"
            elif avg_sentiment_score < -0.1:
                market_sentiment = "negative"
            else:
                market_sentiment = "neutral"
            
            return {
                "market_sentiment": market_sentiment,
                "sentiment_score": avg_sentiment_score,
                "post_count": total_posts,
                "sentiment_distribution": sentiment_counts,
                "currencies_analyzed": currencies or ["general"],
                "timestamp": datetime.now().isoformat(),
                "source": "cryptopanic"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return None


# Convenience functions for easy usage
async def get_crypto_news(
    currencies: Optional[List[str]] = None, 
    filter_type: str = "hot", 
    limit: int = 20,
    api_key: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get cryptocurrency news from CryptoPanic.
    
    Args:
        currencies: List of currency codes to filter by
        filter_type: News filter type
        limit: Number of articles
        api_key: CryptoPanic API key
        
    Returns:
        List of news articles
    """
    async with CryptoPanicAPIClient(api_key) as client:
        return await client.get_posts(filter_type=filter_type, currencies=currencies, limit=limit)


async def get_crypto_sentiment(currency: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get sentiment analysis for a cryptocurrency.
    
    Args:
        currency: Cryptocurrency symbol
        api_key: CryptoPanic API key
        
    Returns:
        Sentiment analysis results
    """
    async with CryptoPanicAPIClient(api_key) as client:
        return await client.get_sentiment_analysis(currency)


# Example usage
async def main():
    """Example usage of the CryptoPanic API client."""
    
    print("Testing CryptoPanic API client...")
    
    # Note: API key is optional for basic features
    api_key = getattr(settings, 'CRYPTOPANIC_API_KEY', None)
    
    async with CryptoPanicAPIClient(api_key) as client:
        # Test hot news
        print("\n1. Testing hot news...")
        hot_news = await client.get_posts(filter_type="hot", limit=5)
        if hot_news:
            print("Hot cryptocurrency news:")
            for post in hot_news:
                currencies = ', '.join([c['code'] for c in post['currencies'][:3]])
                print(f"  {post['title']} - {currencies} ({post['sentiment']})")
        
        # Test news by currency
        print("\n2. Testing news for BTC...")
        btc_news = await client.get_news_by_currency("BTC", limit=3)
        if btc_news:
            print("BTC news:")
            for post in btc_news:
                print(f"  {post['title']} ({post['sentiment']}: {post['sentiment_score']:.2f})")
        
        # Test sentiment analysis
        print("\n3. Testing sentiment analysis for BTC...")
        btc_sentiment = await client.get_sentiment_analysis("BTC", days=3)
        if btc_sentiment:
            print(f"BTC sentiment: {btc_sentiment['sentiment']} "
                  f"(score: {btc_sentiment['sentiment_score']:.2f}, "
                  f"posts: {btc_sentiment['post_count']})")
        
        # Test market sentiment overview
        print("\n4. Testing market sentiment overview...")
        market_sentiment = await client.get_market_sentiment_overview()
        if market_sentiment:
            print(f"Market sentiment: {market_sentiment['market_sentiment']} "
                  f"(score: {market_sentiment['sentiment_score']:.2f})")


if __name__ == "__main__":
    asyncio.run(main())
