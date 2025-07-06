#!/usr/bin/env python3
"""
Testes para APIs Reais de Market Data
Verifica conectividade e funcionalidade de todas as APIs integradas.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.external.binance_client import BinanceAPIClient
from src.api.external.coinmarketcap_client import CoinMarketCapAPIClient
from src.api.external.coinmarketcal_client import CoinMarketCalAPIClient
from src.api.external.cryptopanic_client import CryptoPanicAPIClient
from src.api.external.news_api_client import NewsAPIClient
from src.api.external.market_data_aggregator import MarketDataAggregator
from src.core.config import settings


class APITester:
    """Classe para testar todas as APIs de market data."""
    
    def __init__(self):
        self.results = {
            'binance': {'status': '❓', 'tests': []},
            'coinmarketcap': {'status': '❓', 'tests': []},
            'coinmarketcal': {'status': '❓', 'tests': []},
            'cryptopanic': {'status': '❓', 'tests': []},
            'news_api': {'status': '❓', 'tests': []},
            'aggregator': {'status': '❓', 'tests': []}
        }
        
        self.api_keys = {
            'coinmarketcap': getattr(settings, 'COINMARKETCAP_API_KEY', None),
            'coinmarketcal': getattr(settings, 'COINMARKETCAL_API_KEY', None),
            'cryptopanic': getattr(settings, 'CRYPTOPANIC_API_KEY', None),
            'news_api': getattr(settings, 'NEWS_API_KEY', None)
        }
    
    def log_test(self, api: str, test_name: str, success: bool, message: str = ""):
        """Log resultado de um teste."""
        status = "✅" if success else "❌"
        self.results[api]['tests'].append({
            'name': test_name,
            'status': status,
            'message': message
        })
        print(f"  {status} {test_name}: {message}")
    
    def set_api_status(self, api: str, success: bool):
        """Define status geral da API."""
        self.results[api]['status'] = "✅" if success else "❌"
    
    async def test_binance_api(self):
        """Testa a API da Binance."""
        print("\n🟡 Testando Binance API...")
        
        try:
            async with BinanceAPIClient() as client:
                # Teste 1: Preço atual
                try:
                    price_data = await client.get_current_price("BTC/USDT")
                    if price_data and price_data.get('price'):
                        self.log_test('binance', 'Current Price', True, 
                                    f"BTC/USDT: ${price_data['price']:,.2f}")
                    else:
                        self.log_test('binance', 'Current Price', False, "No price data returned")
                except Exception as e:
                    self.log_test('binance', 'Current Price', False, str(e))
                
                # Teste 2: Dados históricos
                try:
                    historical = await client.get_historical_data("BTC/USDT", "1d", 7)
                    if historical and len(historical) > 0:
                        self.log_test('binance', 'Historical Data', True, 
                                    f"{len(historical)} data points retrieved")
                    else:
                        self.log_test('binance', 'Historical Data', False, "No historical data")
                except Exception as e:
                    self.log_test('binance', 'Historical Data', False, str(e))
                
                # Teste 3: Top symbols
                try:
                    top_symbols = await client.get_top_symbols(5)
                    if top_symbols and len(top_symbols) > 0:
                        self.log_test('binance', 'Top Symbols', True, 
                                    f"{len(top_symbols)} trending symbols")
                    else:
                        self.log_test('binance', 'Top Symbols', False, "No trending data")
                except Exception as e:
                    self.log_test('binance', 'Top Symbols', False, str(e))
                
                # Teste 4: Exchange info
                try:
                    exchange_info = await client.get_exchange_info()
                    if exchange_info:
                        self.log_test('binance', 'Exchange Info', True, 
                                    f"Server time: {exchange_info.get('server_time', 'N/A')}")
                    else:
                        self.log_test('binance', 'Exchange Info', False, "No exchange info")
                except Exception as e:
                    self.log_test('binance', 'Exchange Info', False, str(e))
                
                self.set_api_status('binance', True)
                
        except Exception as e:
            self.log_test('binance', 'Connection', False, f"Failed to connect: {e}")
            self.set_api_status('binance', False)
    
    async def test_coinmarketcap_api(self):
        """Testa a API do CoinMarketCap."""
        print("\n🔵 Testando CoinMarketCap API...")
        
        if not self.api_keys['coinmarketcap']:
            self.log_test('coinmarketcap', 'API Key', False, "API key not provided")
            self.set_api_status('coinmarketcap', False)
            return
        
        try:
            async with CoinMarketCapAPIClient(self.api_keys['coinmarketcap']) as client:
                # Teste 1: Latest quotes
                try:
                    quotes = await client.get_latest_quotes(["BTC", "ETH"])
                    if quotes and len(quotes) > 0:
                        btc_data = quotes.get('BTC', {})
                        self.log_test('coinmarketcap', 'Latest Quotes', True, 
                                    f"BTC: ${btc_data.get('price', 0):,.2f}")
                    else:
                        self.log_test('coinmarketcap', 'Latest Quotes', False, "No quotes data")
                except Exception as e:
                    self.log_test('coinmarketcap', 'Latest Quotes', False, str(e))
                
                # Teste 2: Global metrics
                try:
                    global_metrics = await client.get_global_metrics()
                    if global_metrics:
                        total_mcap = global_metrics.get('total_market_cap', 0)
                        self.log_test('coinmarketcap', 'Global Metrics', True, 
                                    f"Total Market Cap: ${total_mcap:,.0f}")
                    else:
                        self.log_test('coinmarketcap', 'Global Metrics', False, "No global metrics")
                except Exception as e:
                    self.log_test('coinmarketcap', 'Global Metrics', False, str(e))
                
                # Teste 3: Listings
                try:
                    listings = await client.get_listings_latest(1, 10)
                    if listings and len(listings) > 0:
                        self.log_test('coinmarketcap', 'Listings', True, 
                                    f"{len(listings)} coins retrieved")
                    else:
                        self.log_test('coinmarketcap', 'Listings', False, "No listings data")
                except Exception as e:
                    self.log_test('coinmarketcap', 'Listings', False, str(e))
                
                self.set_api_status('coinmarketcap', True)
                
        except Exception as e:
            self.log_test('coinmarketcap', 'Connection', False, f"Failed to connect: {e}")
            self.set_api_status('coinmarketcap', False)
    
    async def test_coinmarketcal_api(self):
        """Testa a API do CoinMarketCal."""
        print("\n🟠 Testando CoinMarketCal API...")
        
        if not self.api_keys['coinmarketcal']:
            self.log_test('coinmarketcal', 'API Key', False, "API key not provided")
            self.set_api_status('coinmarketcal', False)
            return
        
        try:
            async with CoinMarketCalAPIClient(self.api_keys['coinmarketcal']) as client:
                # Teste 1: Upcoming events
                try:
                    events = await client.get_upcoming_events(7, 10)
                    if events and len(events) > 0:
                        self.log_test('coinmarketcal', 'Upcoming Events', True, 
                                    f"{len(events)} events found")
                    else:
                        self.log_test('coinmarketcal', 'Upcoming Events', False, "No events found")
                except Exception as e:
                    self.log_test('coinmarketcal', 'Upcoming Events', False, str(e))
                
                # Teste 2: Events by coin
                try:
                    btc_events = await client.get_events_by_coin("BTC", 5)
                    if btc_events is not None:
                        self.log_test('coinmarketcal', 'BTC Events', True, 
                                    f"{len(btc_events)} BTC events")
                    else:
                        self.log_test('coinmarketcal', 'BTC Events', False, "No BTC events")
                except Exception as e:
                    self.log_test('coinmarketcal', 'BTC Events', False, str(e))
                
                # Teste 3: Hot events
                try:
                    hot_events = await client.get_hot_events(5)
                    if hot_events is not None:
                        self.log_test('coinmarketcal', 'Hot Events', True, 
                                    f"{len(hot_events)} hot events")
                    else:
                        self.log_test('coinmarketcal', 'Hot Events', False, "No hot events")
                except Exception as e:
                    self.log_test('coinmarketcal', 'Hot Events', False, str(e))
                
                self.set_api_status('coinmarketcal', True)
                
        except Exception as e:
            self.log_test('coinmarketcal', 'Connection', False, f"Failed to connect: {e}")
            self.set_api_status('coinmarketcal', False)
    
    async def test_cryptopanic_api(self):
        """Testa a API do CryptoPanic."""
        print("\n🟣 Testando CryptoPanic API...")
        
        # CryptoPanic funciona sem API key, mas com limitações
        try:
            async with CryptoPanicAPIClient(self.api_keys['cryptopanic']) as client:
                # Teste 1: Hot posts
                try:
                    posts = await client.get_posts("hot", limit=5)
                    if posts and len(posts) > 0:
                        self.log_test('cryptopanic', 'Hot Posts', True, 
                                    f"{len(posts)} hot posts retrieved")
                    else:
                        self.log_test('cryptopanic', 'Hot Posts', False, "No posts retrieved")
                except Exception as e:
                    self.log_test('cryptopanic', 'Hot Posts', False, str(e))
                
                # Teste 2: BTC news
                try:
                    btc_news = await client.get_news_by_currency("BTC", 3)
                    if btc_news is not None:
                        self.log_test('cryptopanic', 'BTC News', True, 
                                    f"{len(btc_news)} BTC articles")
                    else:
                        self.log_test('cryptopanic', 'BTC News', False, "No BTC news")
                except Exception as e:
                    self.log_test('cryptopanic', 'BTC News', False, str(e))
                
                # Teste 3: Sentiment analysis
                try:
                    sentiment = await client.get_sentiment_analysis("BTC", 3)
                    if sentiment:
                        self.log_test('cryptopanic', 'Sentiment Analysis', True, 
                                    f"BTC sentiment: {sentiment['sentiment']}")
                    else:
                        self.log_test('cryptopanic', 'Sentiment Analysis', False, "No sentiment data")
                except Exception as e:
                    self.log_test('cryptopanic', 'Sentiment Analysis', False, str(e))
                
                self.set_api_status('cryptopanic', True)
                
        except Exception as e:
            self.log_test('cryptopanic', 'Connection', False, f"Failed to connect: {e}")
            self.set_api_status('cryptopanic', False)
    
    async def test_news_api(self):
        """Testa a NewsAPI."""
        print("\n🔴 Testando NewsAPI...")
        
        if not self.api_keys['news_api']:
            self.log_test('news_api', 'API Key', False, "API key not provided")
            self.set_api_status('news_api', False)
            return
        
        try:
            async with NewsAPIClient(self.api_keys['news_api']) as client:
                # Teste 1: Crypto news
                try:
                    crypto_news = await client.get_crypto_news(limit=5)
                    if crypto_news and len(crypto_news) > 0:
                        self.log_test('news_api', 'Crypto News', True, 
                                    f"{len(crypto_news)} crypto articles")
                    else:
                        self.log_test('news_api', 'Crypto News', False, "No crypto news")
                except Exception as e:
                    self.log_test('news_api', 'Crypto News', False, str(e))
                
                # Teste 2: Financial news
                try:
                    financial_news = await client.get_financial_news(limit=3)
                    if financial_news and len(financial_news) > 0:
                        self.log_test('news_api', 'Financial News', True, 
                                    f"{len(financial_news)} financial articles")
                    else:
                        self.log_test('news_api', 'Financial News', False, "No financial news")
                except Exception as e:
                    self.log_test('news_api', 'Financial News', False, str(e))
                
                # Teste 3: Headlines
                try:
                    headlines = await client.get_headlines(category="business", page_size=3)
                    if headlines and len(headlines) > 0:
                        self.log_test('news_api', 'Headlines', True, 
                                    f"{len(headlines)} business headlines")
                    else:
                        self.log_test('news_api', 'Headlines', False, "No headlines")
                except Exception as e:
                    self.log_test('news_api', 'Headlines', False, str(e))
                
                self.set_api_status('news_api', True)
                
        except Exception as e:
            self.log_test('news_api', 'Connection', False, f"Failed to connect: {e}")
            self.set_api_status('news_api', False)
    
    async def test_aggregator(self):
        """Testa o agregador de market data."""
        print("\n🔧 Testando Market Data Aggregator...")
        
        try:
            async with MarketDataAggregator() as aggregator:
                print(f"  📊 API Status: {aggregator.api_status}")
                
                # Teste 1: Current prices
                try:
                    prices = await aggregator.get_current_prices(["BTC/USDT", "ETH/USDT"])
                    if prices and len(prices) > 0:
                        self.log_test('aggregator', 'Current Prices', True, 
                                    f"{len(prices)} price points retrieved")
                    else:
                        self.log_test('aggregator', 'Current Prices', False, "No price data")
                except Exception as e:
                    self.log_test('aggregator', 'Current Prices', False, str(e))
                
                # Teste 2: Trending cryptocurrencies
                try:
                    trending = await aggregator.get_trending_cryptocurrencies(5)
                    if trending and len(trending) > 0:
                        self.log_test('aggregator', 'Trending Cryptos', True, 
                                    f"{len(trending)} trending coins")
                    else:
                        self.log_test('aggregator', 'Trending Cryptos', False, "No trending data")
                except Exception as e:
                    self.log_test('aggregator', 'Trending Cryptos', False, str(e))
                
                # Teste 3: News analysis
                try:
                    news = await aggregator.get_news_analysis(["BTC"], 3)
                    if news is not None:
                        self.log_test('aggregator', 'News Analysis', True, 
                                    f"{len(news)} news articles")
                    else:
                        self.log_test('aggregator', 'News Analysis', False, "No news data")
                except Exception as e:
                    self.log_test('aggregator', 'News Analysis', False, str(e))
                
                # Teste 4: Comprehensive analysis
                try:
                    analysis = await aggregator.get_comprehensive_market_analysis(
                        ["BTC/USDT"], 
                        include_news=True, 
                        include_events=True, 
                        include_sentiment=True
                    )
                    if analysis and 'market_data' in analysis:
                        self.log_test('aggregator', 'Comprehensive Analysis', True, 
                                    f"Analysis completed with {len(analysis.get('market_data', []))} data points")
                    else:
                        self.log_test('aggregator', 'Comprehensive Analysis', False, "Analysis failed")
                except Exception as e:
                    self.log_test('aggregator', 'Comprehensive Analysis', False, str(e))
                
                self.set_api_status('aggregator', True)
                
        except Exception as e:
            self.log_test('aggregator', 'Connection', False, f"Failed to initialize: {e}")
            self.set_api_status('aggregator', False)
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        print("\n" + "="*60)
        print("📋 RESUMO DOS TESTES")
        print("="*60)
        
        for api, results in self.results.items():
            print(f"\n{results['status']} {api.upper()}")
            for test in results['tests']:
                print(f"    {test['status']} {test['name']}: {test['message']}")
        
        # Estatísticas gerais
        total_apis = len(self.results)
        working_apis = sum(1 for api in self.results.values() if api['status'] == '✅')
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"    APIs funcionando: {working_apis}/{total_apis}")
        print(f"    Taxa de sucesso: {(working_apis/total_apis)*100:.1f}%")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        for api, results in self.results.items():
            if results['status'] == '❌':
                if api in ['coinmarketcap', 'coinmarketcal', 'cryptopanic', 'news_api']:
                    print(f"    - Configure {api.upper()}_API_KEY no arquivo .env")
                else:
                    print(f"    - Verifique conectividade da internet para {api}")
        
        print(f"\n🔗 Para obter chaves de API, consulte REAL_MARKET_DATA_APIS.md")
        print("="*60)
    
    async def run_all_tests(self):
        """Executa todos os testes."""
        print("🧪 INICIANDO TESTES DAS APIs DE MARKET DATA")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        print(f"🔑 Chaves configuradas: {sum(1 for k in self.api_keys.values() if k)}/4")
        
        # Executar testes
        await self.test_binance_api()
        await self.test_coinmarketcap_api()
        await self.test_coinmarketcal_api()
        await self.test_cryptopanic_api()
        await self.test_news_api()
        await self.test_aggregator()
        
        # Imprimir resumo
        self.print_summary()


async def main():
    """Função principal para executar os testes."""
    tester = APITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar testes: {e}")
