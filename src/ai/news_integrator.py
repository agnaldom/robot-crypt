#!/usr/bin/env python3
"""
News Integrator for AI Analysis
Fetches news from various sources and feeds into AI analysis
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp

from .news_analyzer import CryptoNewsItem, LLMNewsAnalyzer
from src.api.external.news_api_client import NewsAPIClient
from src.api.external.cryptopanic_client import CryptoPanicAPIClient

logger = logging.getLogger(__name__)


class NewsIntegrator:
    """Integrador de notícias para análise de IA"""
    
    def __init__(self):
        self.logger = logging.getLogger("robot-crypt.news_integrator")
        self.news_analyzer = LLMNewsAnalyzer()
        
        # Initialize news sources
        try:
            self.news_api_client = NewsAPIClient()
            self.cryptopanic = CryptoPanicAPIClient()
            self.sources_available = True
        except Exception as e:
            self.logger.warning(f"News sources not fully available: {e}")
            self.sources_available = False
        
        # Cache para evitar análise duplicada
        self.news_cache = {}
        self.cache_duration = timedelta(minutes=30)
    
    async def get_market_sentiment(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Obtém sentimento do mercado baseado em notícias recentes
        
        Args:
            symbols: Lista de símbolos para análise específica
            
        Returns:
            Análise de sentimento do mercado
        """
        try:
            # Busca notícias recentes
            news_items = await self._fetch_recent_news(symbols)
            
            if not news_items:
                self.logger.warning("Nenhuma notícia encontrada para análise")
                return self._create_neutral_sentiment()
            
            # Analisa sentimento com IA
            sentiment_analysis = await self.news_analyzer.analyze_crypto_news(
                news_items, 
                symbol=symbols[0] if symbols else None
            )
            
            # Detecta eventos importantes
            events = await self.news_analyzer.detect_market_events(news_items)
            
            return {
                'sentiment_score': sentiment_analysis.sentiment_score,
                'sentiment_label': sentiment_analysis.sentiment_label,
                'confidence': sentiment_analysis.confidence,
                'impact_level': sentiment_analysis.impact_level,
                'key_events': sentiment_analysis.key_events,
                'price_prediction': sentiment_analysis.price_prediction,
                'reasoning': sentiment_analysis.reasoning,
                'article_count': sentiment_analysis.article_count,
                'detected_events': events,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {e}")
            return self._create_neutral_sentiment()
    
    async def _fetch_recent_news(self, symbols: List[str] = None, hours: int = 24) -> List[CryptoNewsItem]:
        """Busca notícias recentes de várias fontes"""
        news_items = []
        
        try:
            # Cache key
            cache_key = f"news_{'-'.join(symbols) if symbols else 'general'}_{hours}h"
            
            # Check cache
            if cache_key in self.news_cache:
                cache_time, cached_news = self.news_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    self.logger.info(f"Returning cached news: {len(cached_news)} items")
                    return cached_news
            
            if not self.sources_available:
                # Create sample news if no sources available
                return self._create_sample_news()
            
            # Busca de múltiplas fontes
            sources = [
                self._fetch_news_api_news(symbols, hours),
                self._fetch_cryptopanic_news(symbols, hours)
            ]
            
            # Executa buscas em paralelo
            results = await asyncio.gather(*sources, return_exceptions=True)
            
            # Combina resultados
            for result in results:
                if isinstance(result, list):
                    news_items.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"News source error: {result}")
            
            # Remove duplicatas baseado no título
            seen_titles = set()
            unique_news = []
            
            for item in news_items:
                if item.title not in seen_titles:
                    seen_titles.add(item.title)
                    unique_news.append(item)
            
            # Cache result
            self.news_cache[cache_key] = (datetime.now(), unique_news)
            
            self.logger.info(f"Fetched {len(unique_news)} unique news items")
            return unique_news
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return []
    
    async def _fetch_news_api_news(self, symbols: List[str], hours: int) -> List[CryptoNewsItem]:
        """Busca notícias da News API"""
        try:
            # Query terms for crypto news
            query_terms = ["cryptocurrency", "bitcoin", "ethereum", "crypto"]
            
            if symbols:
                # Add specific symbols to query
                symbol_terms = []
                for symbol in symbols:
                    if symbol.upper() == "BTC":
                        symbol_terms.append("bitcoin")
                    elif symbol.upper() == "ETH":
                        symbol_terms.append("ethereum")
                    else:
                        symbol_terms.append(symbol.lower())
                query_terms.extend(symbol_terms)
            
            query = " OR ".join(query_terms)
            
            # Fetch from News API
            articles = await self.news_api_client.get_crypto_news(
                query=query,
                hours_back=hours,
                max_articles=20
            )
            
            news_items = []
            for article in articles:
                # Determine mentioned symbols
                mentioned_symbols = self._extract_symbols_from_text(
                    f"{article.get('title', '')} {article.get('description', '')}"
                )
                
                news_item = CryptoNewsItem(
                    title=article.get('title', ''),
                    content=article.get('description', '') or article.get('content', ''),
                    source=article.get('source', {}).get('name', 'NewsAPI'),
                    published_at=datetime.fromisoformat(
                        article.get('publishedAt', datetime.now().isoformat()).replace('Z', '+00:00')
                    ),
                    symbols_mentioned=mentioned_symbols,
                    url=article.get('url'),
                    author=article.get('author')
                )
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            self.logger.error(f"Error fetching News API news: {e}")
            return []
    
    async def _fetch_cryptopanic_news(self, symbols: List[str], hours: int) -> List[CryptoNewsItem]:
        """Busca notícias do CryptoPanic"""
        try:
            # Fetch from CryptoPanic
            news_data = await self.cryptopanic.get_news(
                currencies=symbols if symbols else None,
                hours_back=hours
            )
            
            news_items = []
            for item in news_data:
                news_item = CryptoNewsItem(
                    title=item.get('title', ''),
                    content=item.get('summary', ''),
                    source=item.get('source', {}).get('title', 'CryptoPanic'),
                    published_at=datetime.fromisoformat(
                        item.get('published_at', datetime.now().isoformat()).replace('Z', '+00:00')
                    ),
                    symbols_mentioned=item.get('currencies', []),
                    url=item.get('url')
                )
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            self.logger.error(f"Error fetching CryptoPanic news: {e}")
            return []
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """Extrai símbolos de criptomoedas do texto"""
        symbols = []
        text_upper = text.upper()
        
        # Common crypto symbols and names
        crypto_map = {
            'BITCOIN': 'BTC',
            'ETHEREUM': 'ETH', 
            'BINANCE COIN': 'BNB',
            'CARDANO': 'ADA',
            'SOLANA': 'SOL',
            'DOGECOIN': 'DOGE',
            'SHIBA INU': 'SHIB',
            'POLYGON': 'MATIC',
            'AVALANCHE': 'AVAX',
            'CHAINLINK': 'LINK'
        }
        
        # Check for crypto names and symbols
        for name, symbol in crypto_map.items():
            if name in text_upper or symbol in text_upper:
                symbols.append(symbol)
        
        return list(set(symbols))  # Remove duplicates
    
    def _create_sample_news(self) -> List[CryptoNewsItem]:
        """Cria notícias de exemplo quando fontes não estão disponíveis"""
        return [
            CryptoNewsItem(
                title="Bitcoin Shows Steady Growth Amid Institutional Interest",
                content="Bitcoin continues to demonstrate resilience with steady price appreciation...",
                source="Sample News",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Ethereum Network Upgrades Drive Developer Activity",
                content="The Ethereum ecosystem sees increased developer engagement following recent updates...",
                source="Sample News", 
                published_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["ETH"]
            )
        ]
    
    def _create_neutral_sentiment(self) -> Dict[str, Any]:
        """Cria análise de sentimento neutra para casos de erro"""
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.1,
            'impact_level': 'low',
            'key_events': [],
            'price_prediction': 'neutral',
            'reasoning': 'Unable to analyze news sentiment - no data available',
            'article_count': 0,
            'detected_events': [],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Obtém sentimento específico para um símbolo"""
        return await self.get_market_sentiment([symbol])
    
    async def get_sentiment_summary(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Obtém resumo de sentimento para múltiplos símbolos"""
        results = {}
        
        # Get general market sentiment
        results['market_general'] = await self.get_market_sentiment()
        
        # Get symbol-specific sentiment
        for symbol in symbols:
            try:
                results[symbol] = await self.get_symbol_sentiment(symbol)
            except Exception as e:
                self.logger.error(f"Error getting sentiment for {symbol}: {e}")
                results[symbol] = self._create_neutral_sentiment()
        
        return results
