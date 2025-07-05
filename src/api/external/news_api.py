"""
News API integration for cryptocurrency news and market sentiment.
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.config import settings
from core.logging_setup import logger


class NewsAPIException(Exception):
    """Exception raised for News API errors."""
    pass


class NewsAPI:
    """
    Class for accessing cryptocurrency news and market sentiment data.
    """

    def __init__(self, api_key: str):
        """
        Initialize NewsAPI.

        Args:
            api_key (str): API key for the news service.
        """
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the News API.

        Args:
            endpoint (str): API endpoint path.
            params (Dict[str, Any], optional): Query parameters. Defaults to None.

        Returns:
            Dict[str, Any]: Response data.

        Raises:
            NewsAPIException: If the request fails.
        """
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params["apiKey"] = self.api_key

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"News API request failed: {e}")
            raise NewsAPIException(f"Request failed: {e}")

        data = response.json()
        if data.get("status") != "ok":
            logger.error(f"News API error: {data.get('message', 'Unknown error')}")
            raise NewsAPIException(f"API error: {data.get('message', 'Unknown error')}")

        return data

    def get_crypto_news(
        self,
        keywords: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        days: int = 1,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cryptocurrency news articles.

        Args:
            keywords (List[str], optional): List of keywords or phrases to search for.
            sources (List[str], optional): List of news sources or domains.
            days (int, optional): Number of days to look back. Defaults to 1.
            language (str, optional): Language of articles. Defaults to "en".
            sort_by (str, optional): Sort order. Defaults to "publishedAt".
            page_size (int, optional): Number of results to return. Defaults to 20.

        Returns:
            List[Dict[str, Any]]: News articles.
        """
        # Calculate date range
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days)

        # Format dates as ISO strings
        to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")
        from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")

        # Build query string for keywords
        if keywords:
            query = " OR ".join([f'"{keyword}"' for keyword in keywords])
        else:
            query = "cryptocurrency OR bitcoin OR ethereum OR crypto"

        # Build params
        params = {
            "q": query,
            "from": from_date_str,
            "to": to_date_str,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size
        }

        if sources:
            params["sources"] = ",".join(sources)

        # Make request
        data = self._request("everything", params)
        
        # Process articles
        articles = data.get("articles", [])
        
        # Add sentiment analysis placeholder (could be replaced with actual NLP)
        for article in articles:
            # Simple placeholder for sentiment based on title words
            title = article.get("title", "").lower()
            if any(word in title for word in ["bullish", "surge", "soar", "gain", "rally"]):
                article["sentiment"] = "positive"
            elif any(word in title for word in ["bearish", "crash", "plunge", "fall", "drop"]):
                article["sentiment"] = "negative"
            else:
                article["sentiment"] = "neutral"
        
        return articles

    def get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate market sentiment for a specific cryptocurrency.

        Args:
            symbol (str): Cryptocurrency symbol (e.g., "BTC", "ETH").

        Returns:
            Dict[str, Any]: Sentiment analysis results.
        """
        # Get news specifically about this symbol
        news = self.get_crypto_news(keywords=[symbol], days=3, page_size=50)
        
        # Count sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for article in news:
            sentiment = article.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1
        
        total_articles = len(news)
        if total_articles == 0:
            return {
                "symbol": symbol,
                "sentiment_score": 0,
                "sentiment": "neutral",
                "confidence": 0,
                "article_count": 0,
                "sentiment_distribution": sentiment_counts
            }
        
        # Calculate sentiment score (-1 to 1 scale)
        sentiment_score = (sentiment_counts["positive"] - sentiment_counts["negative"]) / total_articles
        
        # Determine overall sentiment
        if sentiment_score > 0.2:
            sentiment = "positive"
        elif sentiment_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate confidence based on article count and sentiment distribution
        confidence = min(0.5 + (total_articles / 100), 0.95)
        
        return {
            "symbol": symbol,
            "sentiment_score": sentiment_score,
            "sentiment": sentiment,
            "confidence": confidence,
            "article_count": total_articles,
            "sentiment_distribution": sentiment_counts
        }
