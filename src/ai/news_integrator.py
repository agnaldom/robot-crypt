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
from src.models.market_analysis import MarketAnalysis
from src.database.database import get_database, get_safe_database_session

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
        
        # Set to track background tasks
        self.background_tasks = set()
    
    async def get_market_sentiment(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Obtém sentimento do mercado baseado em notícias recentes
        
        Args:
            symbols: Lista de símbolos para análise específica
            
        Returns:
            Análise de sentimento do mercado
        """
        try:
            # Busca notícias recentes com timeout
            news_items = await asyncio.wait_for(
                self._fetch_recent_news(symbols),
                timeout=15.0  # 15 segundos para buscar notícias
            )
            
            if not news_items:
                self.logger.warning("Nenhuma notícia encontrada para análise")
                return self._create_neutral_sentiment()
            
            # Analisa sentimento com IA - com timeout mais longo
            try:
                sentiment_analysis = await asyncio.wait_for(
                    self.news_analyzer.analyze_crypto_news(
                        news_items, 
                        symbol=symbols[0] if symbols else None
                    ),
                    timeout=30.0  # 30 segundos para análise de sentimento
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout na análise de sentimento para {symbols[0] if symbols else 'mercado geral'}")
                return self._create_neutral_sentiment_with_timeout(symbols)
            
            # Validar se a análise de sentimento foi bem-sucedida
            if sentiment_analysis is None:
                self.logger.warning("Análise de sentimento retornou None")
                return self._create_neutral_sentiment()
            
            # Verificar se é um objeto dict válido
            if not isinstance(sentiment_analysis, dict):
                self.logger.warning(f"Análise de sentimento retornou tipo inválido: {type(sentiment_analysis)}")
                return self._create_neutral_sentiment()
            
            # Detecta eventos importantes - com timeout menor
            try:
                events = await asyncio.wait_for(
                    self.news_analyzer.detect_market_events(news_items),
                    timeout=10.0  # 10 segundos para detecção de eventos
                )
            except asyncio.TimeoutError:
                self.logger.warning("Timeout na detecção de eventos")
                events = []
            
            # Criar dados de sentimento de forma segura
            sentiment_data = {
                'sentiment_score': sentiment_analysis.get('sentiment_score', 0.0),
                'sentiment_label': sentiment_analysis.get('sentiment_label', 'neutral'),
                'confidence': sentiment_analysis.get('confidence', 0.1),
                'impact_level': sentiment_analysis.get('impact_level', 'low'),
                'key_events': sentiment_analysis.get('key_events', []),
                'price_prediction': sentiment_analysis.get('price_prediction', 'neutral'),
                'reasoning': sentiment_analysis.get('reasoning', 'Analysis completed'),
                'article_count': sentiment_analysis.get('article_count', 0),
                'detected_events': events if events is not None else [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Salva análise no banco de dados de forma não-bloqueante
            try:
                # Cria uma tarefa para salvar no banco sem bloquear o retorno
                save_task = asyncio.create_task(self._save_analysis_to_database(
                    symbol=symbols[0] if symbols else 'MARKET',
                    analysis_type='news_sentiment',
                    data=sentiment_data
                ))
                
                # Adiciona tarefa ao conjunto para rastreamento
                self.background_tasks.add(save_task)
                
                # Remove a tarefa do conjunto quando concluída
                save_task.add_done_callback(self.background_tasks.discard)
                
                # Não aguarda a conclusão - permite que execute em segundo plano
                self.logger.debug(f"Tarefa de salvamento criada para {symbols[0] if symbols else 'MARKET'}")
                
            except Exception as save_error:
                self.logger.warning(f"Erro ao criar tarefa de salvamento: {save_error}")
            
            return sentiment_data
            
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
                # Temporarily disable CryptoPanic due to API issues
                # self._fetch_cryptopanic_news(symbols, hours)
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
            
            # Fetch from News API using async context manager
            # Convert hours to days for NewsAPI (minimum 1 day)
            days_back = max(1, hours // 24) if hours >= 24 else 1
            
            async with self.news_api_client as client:
                articles = await client.get_crypto_news(
                    query=query,
                    days_back=days_back,
                    limit=20
                )
            
            news_items = []
            if not articles:
                self.logger.warning("No articles returned from NewsAPI")
                return news_items
            
            for article in articles:
                # Ensure article is a dictionary
                if not isinstance(article, dict):
                    self.logger.warning(f"Invalid article format: {type(article)}")
                    continue
                    
                # Determine mentioned symbols
                mentioned_symbols = self._extract_symbols_from_text(
                    f"{article.get('title', '')} {article.get('description', '')}"
                )
                
                # Handle source field safely
                source_name = 'NewsAPI'
                if article.get('source'):
                    if isinstance(article['source'], dict):
                        source_name = article['source'].get('name', 'NewsAPI')
                    elif isinstance(article['source'], str):
                        source_name = article['source']
                
                # Handle published date safely
                published_at = datetime.now()
                if article.get('publishedAt'):
                    try:
                        published_at = datetime.fromisoformat(
                            article.get('publishedAt').replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                elif article.get('published_at'):
                    try:
                        published_at = datetime.fromisoformat(
                            article.get('published_at').replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                
                news_item = CryptoNewsItem(
                    title=article.get('title', ''),
                    content=article.get('description', '') or article.get('content', ''),
                    source=source_name,
                    published_at=published_at,
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
            # Fetch from CryptoPanic using async context manager
            async with self.cryptopanic as client:
                news_data = await client.get_posts(
                    currencies=symbols if symbols else None,
                    limit=20
                )
            
            news_items = []
            if news_data:
                for item in news_data:
                    # Filter by time if needed
                    if item.get('published_at'):
                        try:
                            published_date = datetime.fromisoformat(
                                item.get('published_at').replace('Z', '+00:00')
                            )
                            # Filter by hours_back
                            if datetime.now().replace(tzinfo=published_date.tzinfo) - published_date > timedelta(hours=hours):
                                continue
                        except (ValueError, AttributeError):
                            # If we can't parse the date, include the article
                            pass
                    
                    # Extract currency symbols from the currencies array
                    currency_symbols = []
                    for currency in item.get('currencies', []):
                        if isinstance(currency, dict) and currency.get('code'):
                            currency_symbols.append(currency.get('code'))
                    
                    news_item = CryptoNewsItem(
                        title=item.get('title', ''),
                        content=item.get('title', ''),  # CryptoPanic doesn't provide content, use title
                        source=item.get('source', 'CryptoPanic'),
                        published_at=datetime.fromisoformat(
                            item.get('published_at', datetime.now().isoformat()).replace('Z', '+00:00')
                        ) if item.get('published_at') else datetime.now(),
                        symbols_mentioned=currency_symbols,
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
    
    def _create_neutral_sentiment_with_timeout(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Cria análise de sentimento neutra para casos de timeout"""
        symbol_str = symbols[0] if symbols else 'mercado geral'
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.1,
            'impact_level': 'low',
            'key_events': [],
            'price_prediction': 'neutral',
            'reasoning': f'Timeout during sentiment analysis for {symbol_str} - using neutral fallback',
            'article_count': 0,
            'detected_events': [],
            'timestamp': datetime.now().isoformat()
        }
    
    async def _save_analysis_to_database(self, symbol: str, analysis_type: str, data: Dict[str, Any]):
        """Salva análise no banco de dados"""
        try:
            # Tenta salvar no banco com timeout e manejo de exceções melhorado
            async with await get_safe_database_session() as db:
                await MarketAnalysis.save_analysis(db, symbol, analysis_type, data)
                self.logger.info(f"Análise salva no banco: {symbol} - {analysis_type}")
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout ao salvar análise no banco: {symbol} - {analysis_type}")
        except Exception as e:
            error_message = str(e)
            
            # Verifica se é o erro de event loop específico
            if "got Future" in error_message and "attached to a different loop" in error_message:
                self.logger.warning(f"Event loop conflict detectado ao salvar {symbol} - {analysis_type}. Pulando salvamento.")
                return
            
            self.logger.error(f"Erro ao salvar análise no banco: {e}")
            # Log mais detalhado para diagnóstico
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Tenta salvar novamente com uma sessão nova após pequeno delay
            try:
                await asyncio.sleep(0.1)
                async with await get_safe_database_session() as db:
                    await MarketAnalysis.save_analysis(db, symbol, analysis_type, data)
                    self.logger.info(f"Análise salva no banco (segunda tentativa): {symbol} - {analysis_type}")
            except Exception as retry_error:
                retry_error_message = str(retry_error)
                if "got Future" in retry_error_message and "attached to a different loop" in retry_error_message:
                    self.logger.warning(f"Event loop conflict na segunda tentativa para {symbol} - {analysis_type}. Salvamento cancelado.")
                else:
                    self.logger.error(f"Erro na segunda tentativa de salvar análise: {retry_error}")
    
    async def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Obtém sentimento específico para um símbolo"""
        try:
            # Add timeout to prevent hanging
            return await asyncio.wait_for(
                self.get_market_sentiment([symbol]),
                timeout=8.0  # 8 second timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout na análise de sentimento para {symbol}")
            return self._create_neutral_sentiment_with_timeout([symbol])
        except Exception as e:
            self.logger.error(f"Erro ao obter sentimento para {symbol}: {e}")
            return self._create_neutral_sentiment_with_timeout([symbol])
    
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
    
    async def cleanup(self):
        """Limpa tarefas em segundo plano e recursos"""
        try:
            # Aguarda conclusão de todas as tarefas em segundo plano
            if self.background_tasks:
                self.logger.info(f"Aguardando conclusão de {len(self.background_tasks)} tarefas em segundo plano...")
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
                self.background_tasks.clear()
                self.logger.info("Todas as tarefas em segundo plano concluídas.")
        except Exception as e:
            self.logger.error(f"Erro durante limpeza: {e}")
