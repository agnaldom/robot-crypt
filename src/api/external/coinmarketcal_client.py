#!/usr/bin/env python3
"""
CoinMarketCal API Client for Cryptocurrency Events Calendar
Provides access to cryptocurrency events, announcements, and calendar data.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class CoinMarketCalAPIClient:
    """
    CoinMarketCal API Client for fetching cryptocurrency events and calendar data
    Requires API key from CoinMarketCal
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoinMarketCal API client.
        
        Args:
            api_key: CoinMarketCal API key (optional, will use from settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'COINMARKETCAL_API_KEY', None)
        self.base_url = "https://developers.coinmarketcal.com/v1"
        self.session = None
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
        # Event categories mapping
        self.event_categories = {
            1: "Coin",
            2: "Exchange", 
            3: "ICO",
            4: "Conference",
            5: "Blockchain",
            6: "Airdrop",
            7: "Burn",
            8: "Mining",
            9: "Partnership",
            10: "Product",
            11: "Regulation",
            12: "Release",
            13: "Update",
            14: "Hardfork",
            15: "Softfork",
            16: "Listing",
            17: "Delisting"
        }
        
        if not self.api_key:
            logger.warning("CoinMarketCal API key not provided. Some features may not work.")
        else:
            logger.info("CoinMarketCalAPIClient initialized with API key")
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Robot-Crypt/1.0.0'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
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
        """Apply rate limiting to respect CoinMarketCal limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to CoinMarketCal API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.session:
            raise Exception("HTTP session not initialized. Use async context manager.")
        
        if not self.api_key:
            logger.error("CoinMarketCal API key is required for API requests")
            return None
        
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful CoinMarketCal API request: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"CoinMarketCal rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                elif response.status == 401:
                    logger.error("CoinMarketCal API key is invalid or missing")
                    return None
                elif response.status == 400:
                    logger.error(f"CoinMarketCal API bad request: {endpoint}")
                    return None
                else:
                    logger.error(f"CoinMarketCal API error: {response.status} - {endpoint}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"CoinMarketCal API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in CoinMarketCal API request: {e}")
            return None
    
    def _parse_event_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse event date string to datetime object.
        
        Args:
            date_str: Date string from API
            
        Returns:
            Parsed datetime or None
        """
        try:
            # Handle different date formats from CoinMarketCal
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    async def get_events(
        self,
        page: int = 1,
        max_results: int = 50,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
        coins: Optional[List[str]] = None,
        categories: Optional[List[int]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cryptocurrency events from the calendar.
        
        Args:
            page: Page number (1-based)
            max_results: Maximum number of results per page
            date_range_start: Start date (YYYY-MM-DD format)
            date_range_end: End date (YYYY-MM-DD format)
            coins: List of coin symbols to filter by
            categories: List of category IDs to filter by
            
        Returns:
            List of event data
        """
        try:
            params = {
                'page': page,
                'max': min(max_results, 300)  # API limit
            }
            
            if date_range_start:
                params['dateRangeStart'] = date_range_start
            if date_range_end:
                params['dateRangeEnd'] = date_range_end
            if coins:
                params['coins'] = ','.join(coins)
            if categories:
                params['categories'] = ','.join(map(str, categories))
            
            data = await self._make_request("events", params)
            
            if data and 'body' in data:
                events = []
                
                for event in data['body']:
                    parsed_date = self._parse_event_date(event.get('date_event', ''))
                    
                    event_data = {
                        "id": event.get('id'),
                        "title": event.get('title'),
                        "description": event.get('description'),
                        "date_event": parsed_date.isoformat() if parsed_date else None,
                        "date_added": event.get('created_date'),
                        "source": event.get('source'),
                        "source_url": event.get('source_url'),
                        "is_hot": event.get('is_hot', False),
                        "vote_count": event.get('vote_count', 0),
                        "positive_vote_count": event.get('positive_vote_count', 0),
                        "percentage": event.get('percentage', 0),
                        "category": {
                            "id": event.get('categories', {}).get('id'),
                            "name": event.get('categories', {}).get('name')
                        },
                        "coins": [
                            {
                                "id": coin.get('id'),
                                "name": coin.get('name'),
                                "symbol": coin.get('symbol'),
                                "fullname": coin.get('fullname')
                            }
                            for coin in event.get('coins', [])
                        ],
                        "can_occur_before": event.get('can_occur_before', False),
                        "proof": event.get('proof'),
                        "importance": self._calculate_importance(event)
                    }
                    
                    events.append(event_data)
                
                return events
            else:
                logger.warning("No events data received from CoinMarketCal")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return None
    
    def _calculate_importance(self, event: Dict) -> str:
        """
        Calculate event importance based on various factors.
        
        Args:
            event: Event data from API
            
        Returns:
            Importance level (high, medium, low)
        """
        try:
            vote_count = event.get('vote_count', 0)
            percentage = event.get('percentage', 0)
            is_hot = event.get('is_hot', False)
            
            # High importance criteria
            if is_hot or vote_count > 100 or percentage > 80:
                return "high"
            elif vote_count > 50 or percentage > 60:
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "low"
    
    async def get_upcoming_events(self, days_ahead: int = 7, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get upcoming cryptocurrency events.
        
        Args:
            days_ahead: Number of days to look ahead
            limit: Maximum number of events to return
            
        Returns:
            List of upcoming events
        """
        try:
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            events = await self.get_events(
                max_results=limit,
                date_range_start=start_date,
                date_range_end=end_date
            )
            
            if events:
                # Sort by event date
                events.sort(key=lambda x: x['date_event'] or '9999-12-31')
                return events[:limit]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {e}")
            return None
    
    async def get_events_by_coin(self, symbol: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get events for a specific cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            limit: Maximum number of events to return
            
        Returns:
            List of events for the coin
        """
        try:
            events = await self.get_events(
                max_results=limit,
                coins=[symbol.upper()]
            )
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching events for {symbol}: {e}")
            return None
    
    async def get_hot_events(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get hot/trending cryptocurrency events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of hot events
        """
        try:
            # Get recent events and filter for hot ones
            all_events = await self.get_events(max_results=100)
            
            if all_events:
                hot_events = [
                    event for event in all_events 
                    if event.get('is_hot') or event.get('vote_count', 0) > 50
                ]
                
                # Sort by vote count and percentage
                hot_events.sort(
                    key=lambda x: (x.get('vote_count', 0), x.get('percentage', 0)), 
                    reverse=True
                )
                
                return hot_events[:limit]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching hot events: {e}")
            return None
    
    async def get_categories(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get available event categories.
        
        Returns:
            List of event categories
        """
        try:
            data = await self._make_request("categories")
            
            if data and 'body' in data:
                categories = []
                
                for category in data['body']:
                    categories.append({
                        "id": category.get('id'),
                        "name": category.get('name'),
                        "description": category.get('description')
                    })
                
                return categories
            else:
                # Return default categories if API fails
                return [
                    {"id": cat_id, "name": cat_name, "description": f"{cat_name} related events"}
                    for cat_id, cat_name in self.event_categories.items()
                ]
                
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return None
    
    async def get_market_impact_events(self, days_ahead: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        Get events that might have market impact.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of high-impact events
        """
        try:
            # Categories that typically have market impact
            high_impact_categories = [1, 2, 11, 12, 14, 15, 16, 17]  # Coin, Exchange, Regulation, Release, Forks, Listings
            
            events = await self.get_upcoming_events(days_ahead=days_ahead, limit=50)
            
            if events:
                # Filter for high-impact events
                impact_events = [
                    event for event in events
                    if (event.get('category', {}).get('id') in high_impact_categories or
                        event.get('importance') == 'high' or
                        event.get('vote_count', 0) > 30)
                ]
                
                # Sort by importance and date
                impact_events.sort(key=lambda x: (
                    x.get('importance') == 'high',
                    x.get('vote_count', 0),
                    x.get('date_event', '9999-12-31')
                ), reverse=True)
                
                return impact_events
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market impact events: {e}")
            return None


# Convenience functions for easy usage
async def get_upcoming_crypto_events(days_ahead: int = 7, api_key: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Get upcoming cryptocurrency events.
    
    Args:
        days_ahead: Number of days to look ahead
        api_key: CoinMarketCal API key
        
    Returns:
        List of upcoming events
    """
    async with CoinMarketCalAPIClient(api_key) as client:
        return await client.get_upcoming_events(days_ahead=days_ahead)


async def get_coin_events(symbol: str, api_key: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Get events for a specific cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol
        api_key: CoinMarketCal API key
        
    Returns:
        List of events for the coin
    """
    async with CoinMarketCalAPIClient(api_key) as client:
        return await client.get_events_by_coin(symbol)


# Example usage
async def main():
    """Example usage of the CoinMarketCal API client."""
    
    print("Testing CoinMarketCal API client...")
    
    # Note: You need a valid API key for this to work
    api_key = getattr(settings, 'COINMARKETCAL_API_KEY', None)
    
    if not api_key:
        print("⚠️  CoinMarketCal API key not found. Please set COINMARKETCAL_API_KEY in settings.")
        return
    
    async with CoinMarketCalAPIClient(api_key) as client:
        # Test upcoming events
        print("\n1. Testing upcoming events (next 7 days)...")
        upcoming = await client.get_upcoming_events(days_ahead=7, limit=5)
        if upcoming:
            print("Upcoming events:")
            for event in upcoming:
                print(f"  {event['date_event']}: {event['title']} ({event['importance']} importance)")
        
        # Test events by coin
        print("\n2. Testing events for BTC...")
        btc_events = await client.get_events_by_coin("BTC", limit=3)
        if btc_events:
            print("BTC events:")
            for event in btc_events:
                print(f"  {event['title']} - {event['date_event']}")
        
        # Test hot events
        print("\n3. Testing hot events...")
        hot_events = await client.get_hot_events(limit=3)
        if hot_events:
            print("Hot events:")
            for event in hot_events:
                print(f"  {event['title']} (votes: {event['vote_count']})")
        
        # Test market impact events
        print("\n4. Testing market impact events...")
        impact_events = await client.get_market_impact_events(days_ahead=3)
        if impact_events:
            print("High-impact events:")
            for event in impact_events:
                coins_str = ', '.join([coin['symbol'] for coin in event['coins'][:3]])
                print(f"  {event['title']} - {coins_str} ({event['importance']})")


if __name__ == "__main__":
    asyncio.run(main())
