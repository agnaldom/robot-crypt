"""
Sistema de coleta de dados históricos da Binance.
Coleta dados históricos de 24 meses para análise e comparação em tempo real.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

from src.api.binance.client import BinanceClient, BinanceAPIException
from src.core.config import settings
from src.core.database import get_async_session
from src.models.price_history import PriceHistory
from src.core.logging_setup import logger


class HistoricalDataCollector:
    """
    Coletor de dados históricos da Binance para análise de 24 meses.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Inicializa o coletor de dados históricos.
        
        Args:
            api_key: Chave da API Binance (opcional para dados públicos)
            api_secret: Segredo da API Binance (opcional para dados públicos)
        """
        self.client = BinanceClient(api_key=api_key, api_secret=api_secret)
        self.symbols = []
        self.intervals = ['1d', '4h', '1h', '15m']  # Intervalos para análise
        self.months_back = 24  # 24 meses de dados históricos
        
        # Rate limiting para evitar sobrecarga da API
        self.requests_per_minute = 1200  # Limite da Binance
        self.request_interval = 60 / self.requests_per_minute  # Intervalo entre requests
        
    async def get_top_symbols(self, limit: int = 50) -> List[str]:
        """
        Obtém os top símbolos por volume de negociação.
        
        Args:
            limit: Número de símbolos para retornar
            
        Returns:
            Lista de símbolos ordenados por volume
        """
        try:
            # Obter estatísticas de 24h para todos os símbolos
            ticker_stats = self.client._request('GET', 'ticker/24hr')
            
            # Filtrar apenas pares com USDT
            usdt_pairs = [
                ticker for ticker in ticker_stats
                if ticker['symbol'].endswith('USDT') and float(ticker['quoteVolume']) > 1000000
            ]
            
            # Ordenar por volume de negociação
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Retornar apenas os símbolos
            symbols = [ticker['symbol'] for ticker in usdt_pairs[:limit]]
            
            logger.info(f"Top {len(symbols)} símbolos obtidos: {symbols[:10]}...")
            return symbols
            
        except Exception as e:
            logger.error(f"Erro ao obter top símbolos: {str(e)}")
            # Retornar lista padrão em caso de erro
            return [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
                'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT',
                'LTCUSDT', 'MATICUSDT', 'UNIUSDT', 'ATOMUSDT', 'FILUSDT',
                'TRXUSDT', 'XLMUSDT', 'VETUSDT', 'ETCUSDT', 'THETAUSDT'
            ]
    
    def calculate_date_range(self) -> Tuple[int, int]:
        """
        Calcula o range de datas para coleta de dados históricos.
        
        Returns:
            Tuple com timestamps de início e fim em milliseconds
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.months_back * 30)
        
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        
        return start_timestamp, end_timestamp
    
    async def collect_symbol_data(
        self, 
        symbol: str, 
        interval: str, 
        start_time: int, 
        end_time: int
    ) -> List[Dict[str, Any]]:
        """
        Coleta dados históricos para um símbolo específico.
        
        Args:
            symbol: Símbolo da criptomoeda
            interval: Intervalo de tempo (1d, 4h, 1h, 15m)
            start_time: Timestamp de início
            end_time: Timestamp de fim
            
        Returns:
            Lista de dados históricos
        """
        try:
            all_data = []
            current_start = start_time
            
            # Binance limita a 1000 klines por request
            max_limit = 1000
            
            while current_start < end_time:
                # Rate limiting
                await asyncio.sleep(self.request_interval)
                
                try:
                    klines = self.client.get_klines(
                        symbol=symbol,
                        interval=interval,
                        start_time=current_start,
                        end_time=end_time,
                        limit=max_limit
                    )
                    
                    if not klines:
                        break
                    
                    # Processar dados recebidos
                    for kline in klines:
                        data_point = {
                            'symbol': symbol,
                            'interval': interval,
                            'open_time': kline[0],
                            'close_time': kline[6],
                            'open_price': float(kline[1]),
                            'high_price': float(kline[2]),
                            'low_price': float(kline[3]),
                            'close_price': float(kline[4]),
                            'volume': float(kline[5]),
                            'quote_volume': float(kline[7]),
                            'trades_count': int(kline[8]),
                            'timestamp': datetime.fromtimestamp(kline[0] / 1000)
                        }
                        all_data.append(data_point)
                    
                    # Atualizar próximo timestamp
                    current_start = klines[-1][0] + 1
                    
                    logger.info(f"Coletados {len(klines)} pontos para {symbol} {interval}")
                    
                except BinanceAPIException as e:
                    logger.error(f"Erro na API Binance para {symbol} {interval}: {str(e)}")
                    break
                    
            logger.info(f"Total coletado para {symbol} {interval}: {len(all_data)} pontos")
            return all_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados para {symbol} {interval}: {str(e)}")
            return []
    
    async def save_to_database(self, data: List[Dict[str, Any]]) -> bool:
        """
        Salva dados históricos no banco de dados.
        
        Args:
            data: Lista de dados históricos
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            async for session in get_async_session():
                for data_point in data:
                    # Verificar se já existe
                    existing = await session.execute(
                        text("""
                            SELECT id FROM price_history 
                            WHERE symbol = :symbol 
                            AND interval = :interval 
                            AND timestamp = :timestamp
                        """),
                        {
                            'symbol': data_point['symbol'],
                            'interval': data_point['interval'],
                            'timestamp': data_point['timestamp']
                        }
                    )
                    
                    if not existing.fetchone():
                        # Criar novo registro
                        price_history = PriceHistory(
                            symbol=data_point['symbol'],
                            interval=data_point['interval'],
                            open_price=data_point['open_price'],
                            high_price=data_point['high_price'],
                            low_price=data_point['low_price'],
                            close_price=data_point['close_price'],
                            volume=data_point['volume'],
                            quote_asset_volume=data_point['quote_volume'],
                            number_of_trades=data_point['trades_count'],
                            timestamp=data_point['timestamp']
                        )
                        session.add(price_history)
                
                await session.commit()
                logger.info(f"Salvos {len(data)} registros no banco de dados")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar no banco de dados: {str(e)}")
            return False
    
    async def collect_all_historical_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Coleta todos os dados históricos para os símbolos especificados.
        
        Args:
            symbols: Lista de símbolos (se None, usa os top símbolos)
            
        Returns:
            Relatório da coleta de dados
        """
        if symbols is None:
            symbols = await self.get_top_symbols()
        
        self.symbols = symbols
        start_time, end_time = self.calculate_date_range()
        
        report = {
            'start_time': datetime.fromtimestamp(start_time / 1000),
            'end_time': datetime.fromtimestamp(end_time / 1000),
            'symbols': symbols,
            'intervals': self.intervals,
            'total_symbols': len(symbols),
            'total_intervals': len(self.intervals),
            'success_count': 0,
            'error_count': 0,
            'total_data_points': 0
        }
        
        logger.info(f"Iniciando coleta de dados históricos para {len(symbols)} símbolos")
        
        for symbol in symbols:
            for interval in self.intervals:
                try:
                    logger.info(f"Coletando dados para {symbol} {interval}")
                    
                    data = await self.collect_symbol_data(
                        symbol=symbol,
                        interval=interval,
                        start_time=start_time,
                        end_time=end_time
                    )
                    
                    if data:
                        # Salvar no banco de dados
                        if await self.save_to_database(data):
                            report['success_count'] += 1
                            report['total_data_points'] += len(data)
                        else:
                            report['error_count'] += 1
                    else:
                        report['error_count'] += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao processar {symbol} {interval}: {str(e)}")
                    report['error_count'] += 1
        
        logger.info(f"Coleta concluída. Sucessos: {report['success_count']}, Erros: {report['error_count']}")
        return report
    
    async def get_historical_analysis(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtém análise dos dados históricos para um símbolo.
        
        Args:
            symbol: Símbolo da criptomoeda
            days: Número de dias para análise
            
        Returns:
            Análise dos dados históricos
        """
        try:
            async for session in get_async_session():
                # Buscar dados históricos
                result = await session.execute(
                    text("""
                        SELECT * FROM price_history 
                        WHERE symbol = :symbol 
                        AND interval = '1d'
                        AND timestamp >= :start_date
                        ORDER BY timestamp DESC
                        LIMIT :limit
                    """),
                    {
                        'symbol': symbol,
                        'start_date': datetime.now() - timedelta(days=days),
                        'limit': days
                    }
                )
                
                data = result.fetchall()
                
                if not data:
                    return {'error': 'Sem dados históricos disponíveis'}
                
                # Converter para DataFrame para análise
                df = pd.DataFrame([dict(row) for row in data])
                
                # Calcular métricas
                analysis = {
                    'symbol': symbol,
                    'period_days': days,
                    'data_points': len(df),
                    'price_change_percent': ((df['close_price'].iloc[0] - df['close_price'].iloc[-1]) / df['close_price'].iloc[-1]) * 100,
                    'highest_price': float(df['high_price'].max()),
                    'lowest_price': float(df['low_price'].min()),
                    'average_price': float(df['close_price'].mean()),
                    'average_volume': float(df['volume'].mean()),
                    'volatility': float(df['close_price'].std()),
                    'total_volume': float(df['volume'].sum()),
                    'price_trend': 'up' if df['close_price'].iloc[0] > df['close_price'].iloc[-1] else 'down'
                }
                
                # Adicionar análise de suporte e resistência
                analysis['support_level'] = float(df['low_price'].quantile(0.1))
                analysis['resistance_level'] = float(df['high_price'].quantile(0.9))
                
                return analysis
                
        except Exception as e:
            logger.error(f"Erro ao analisar dados históricos para {symbol}: {str(e)}")
            return {'error': str(e)}
    
    async def compare_with_realtime(self, symbol: str) -> Dict[str, Any]:
        """
        Compara dados históricos com dados em tempo real.
        
        Args:
            symbol: Símbolo da criptomoeda
            
        Returns:
            Comparação entre dados históricos e tempo real
        """
        try:
            # Obter preço atual
            current_price_data = self.client.get_ticker_price(symbol)
            current_price = float(current_price_data['price'])
            
            # Obter análise histórica
            historical_analysis = await self.get_historical_analysis(symbol, days=30)
            
            if 'error' in historical_analysis:
                return historical_analysis
            
            # Comparar com histórico
            comparison = {
                'symbol': symbol,
                'current_price': current_price,
                'historical_average': historical_analysis['average_price'],
                'vs_average_percent': ((current_price - historical_analysis['average_price']) / historical_analysis['average_price']) * 100,
                'vs_support_level': current_price - historical_analysis['support_level'],
                'vs_resistance_level': current_price - historical_analysis['resistance_level'],
                'price_position': 'above_average' if current_price > historical_analysis['average_price'] else 'below_average',
                'recommendation': self._generate_recommendation(current_price, historical_analysis)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Erro ao comparar dados para {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _generate_recommendation(self, current_price: float, historical_analysis: Dict[str, Any]) -> str:
        """
        Gera recomendação baseada na análise histórica.
        
        Args:
            current_price: Preço atual
            historical_analysis: Análise histórica
            
        Returns:
            Recomendação de compra/venda
        """
        try:
            avg_price = historical_analysis['average_price']
            support_level = historical_analysis['support_level']
            resistance_level = historical_analysis['resistance_level']
            volatility = historical_analysis['volatility']
            
            # Lógica de recomendação
            if current_price <= support_level * 1.05:  # Próximo ao suporte
                return "BUY - Preço próximo ao suporte histórico"
            elif current_price >= resistance_level * 0.95:  # Próximo à resistência
                return "SELL - Preço próximo à resistência histórica"
            elif current_price < avg_price * 0.9:  # Bem abaixo da média
                return "STRONG_BUY - Preço significativamente abaixo da média"
            elif current_price > avg_price * 1.1:  # Bem acima da média
                return "STRONG_SELL - Preço significativamente acima da média"
            elif volatility > avg_price * 0.1:  # Alta volatilidade
                return "HOLD - Alta volatilidade, aguarde estabilização"
            else:
                return "HOLD - Preço dentro da faixa normal"
                
        except Exception as e:
            logger.error(f"Erro ao gerar recomendação: {str(e)}")
            return "HOLD - Erro na análise"


async def main():
    """
    Função principal para teste do sistema.
    """
    # Inicializar coletor
    collector = HistoricalDataCollector()
    
    # Obter top símbolos
    symbols = await collector.get_top_symbols(limit=10)
    print(f"Top símbolos: {symbols}")
    
    # Coletar dados históricos
    report = await collector.collect_all_historical_data(symbols[:5])  # Apenas 5 para teste
    print(f"Relatório de coleta: {report}")
    
    # Análise para Bitcoin
    if 'BTCUSDT' in symbols:
        analysis = await collector.get_historical_analysis('BTCUSDT', days=30)
        print(f"Análise Bitcoin: {analysis}")
        
        comparison = await collector.compare_with_realtime('BTCUSDT')
        print(f"Comparação Bitcoin: {comparison}")


if __name__ == "__main__":
    asyncio.run(main())
