"""
Módulo para gerenciar dados históricos da Binance para análise comparativa.
Permite buscar até 24 meses de dados históricos e compará-los com dados em tempo real.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from src.api.binance.client import BinanceClient
from src.models.price_history import PriceHistory
from src.database.database import sync_session_maker
from src.core.logging_setup import logger


@dataclass
class HistoricalAnalysis:
    """Classe para armazenar análise histórica."""
    symbol: str
    current_price: float
    historical_avg: float
    historical_max: float
    historical_min: float
    support_levels: List[float]
    resistance_levels: List[float]
    trend_direction: str
    volatility: float
    recommendation: str
    confidence_score: float


class HistoricalDataManager:
    """Gerenciador de dados históricos da Binance."""
    
    def __init__(self, binance_client: Optional[BinanceClient] = None):
        """
        Inicializa o gerenciador de dados históricos.
        
        Args:
            binance_client: Cliente Binance opcional. Se não fornecido, cria um novo.
        """
        self.client = binance_client or BinanceClient()
        self.rate_limit_delay = 0.5  # 500ms entre requisições para evitar rate limit
        
    async def fetch_historical_data(
        self, 
        symbol: str, 
        interval: str = "1d",
        months_back: int = 24,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Busca dados históricos da Binance.
        
        Args:
            symbol: Par de moedas (ex: BTCUSDT)
            interval: Intervalo dos candles (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            months_back: Número de meses para buscar (max 24)
            force_refresh: Se True, força nova busca mesmo se dados existem no BD
        
        Returns:
            Lista de dados históricos OHLCV
        """
        try:
            # Calcula as datas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            # Verifica se dados já existem no banco
            if not force_refresh:
                existing_data = self._get_cached_data(symbol, interval, start_date, end_date)
                if existing_data:
                    logger.info(f"Usando dados em cache para {symbol} {interval}")
                    return existing_data
            
            logger.info(f"Buscando dados históricos para {symbol} {interval} - {months_back} meses")
            
            # Busca dados da API
            historical_data = await self._fetch_paginated_data(
                symbol, interval, start_date, end_date
            )
            
            # Salva no banco de dados
            await self._save_to_database(symbol, interval, historical_data)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos: {str(e)}")
            raise
    
    async def _fetch_paginated_data(
        self, 
        symbol: str, 
        interval: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Busca dados paginados da API da Binance.
        
        Args:
            symbol: Par de moedas
            interval: Intervalo dos candles
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Lista completa de dados históricos
        """
        all_data = []
        current_start = start_date
        
        while current_start < end_date:
            # Calcula o timestamp
            start_ts = int(current_start.timestamp() * 1000)
            
            # Limita a busca para não exceder o end_date
            next_end = min(
                current_start + timedelta(days=1000),  # Máximo 1000 candles por vez
                end_date
            )
            end_ts = int(next_end.timestamp() * 1000)
            
            try:
                # Busca dados da API
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_ts,
                    end_time=end_ts,
                    limit=1000
                )
                
                if not klines:
                    break
                
                # Converte para formato padronizado
                for kline in klines:
                    data_point = {
                        'open_time': int(kline[0]),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'close_time': int(kline[6]),
                        'quote_asset_volume': float(kline[7]),
                        'number_of_trades': int(kline[8]),
                        'taker_buy_base_volume': float(kline[9]),
                        'taker_buy_quote_volume': float(kline[10])
                    }
                    all_data.append(data_point)
                
                # Atualiza para próxima iteração
                current_start = datetime.fromtimestamp(klines[-1][0] / 1000) + timedelta(milliseconds=1)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Erro ao buscar dados paginados: {str(e)}")
                break
        
        logger.info(f"Coletados {len(all_data)} pontos de dados históricos")
        return all_data
    
    def _get_cached_data(
        self, 
        symbol: str, 
        interval: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Busca dados em cache no banco de dados.
        
        Args:
            symbol: Par de moedas
            interval: Intervalo dos candles
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Lista de dados em cache ou None se não encontrado
        """
        try:
            with sync_session_maker() as db:
                cached_data = db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.interval == interval,
                        PriceHistory.timestamp >= start_date,
                        PriceHistory.timestamp <= end_date
                    )
                ).order_by(PriceHistory.timestamp).all()
                
                if len(cached_data) > 0:
                    return [item.to_dict() for item in cached_data]
                    
        except Exception as e:
            logger.error(f"Erro ao buscar dados em cache: {str(e)}")
        
        return None
    
    async def _save_to_database(
        self, 
        symbol: str, 
        interval: str, 
        historical_data: List[Dict[str, Any]]
    ) -> None:
        """
        Salva dados históricos no banco de dados.
        
        Args:
            symbol: Par de moedas
            interval: Intervalo dos candles
            historical_data: Lista de dados históricos
        """
        try:
            with sync_session_maker() as db:
                saved_count = 0
                
                for data_point in historical_data:
                    # Verifica se já existe
                    timestamp = datetime.fromtimestamp(data_point['open_time'] / 1000)
                    
                    existing = db.query(PriceHistory).filter(
                        and_(
                            PriceHistory.symbol == symbol,
                            PriceHistory.interval == interval,
                            PriceHistory.timestamp == timestamp
                        )
                    ).first()
                    
                    if not existing:
                        price_history = PriceHistory.from_ohlcv_data(
                            symbol=symbol,
                            ohlcv_data=data_point,
                            interval=interval
                        )
                        db.add(price_history)
                        saved_count += 1
                
                db.commit()
                logger.info(f"Salvos {saved_count} novos registros no banco de dados")
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados no banco: {str(e)}")
            raise
    
    async def analyze_historical_vs_current(
        self, 
        symbol: str, 
        current_price: float,
        interval: str = "1d",
        months_back: int = 24
    ) -> HistoricalAnalysis:
        """
        Analisa dados históricos vs preço atual para tomar decisões.
        
        Args:
            symbol: Par de moedas
            current_price: Preço atual
            interval: Intervalo dos candles
            months_back: Meses de histórico para análise
        
        Returns:
            Análise histórica com recomendações
        """
        try:
            # Busca dados históricos
            historical_data = await self.fetch_historical_data(
                symbol=symbol,
                interval=interval,
                months_back=months_back
            )
            
            if not historical_data:
                raise ValueError(f"Nenhum dado histórico encontrado para {symbol}")
            
            # Calcula métricas
            prices = [float(item['close']) for item in historical_data]
            
            historical_avg = sum(prices) / len(prices)
            historical_max = max(prices)
            historical_min = min(prices)
            
            # Calcula volatilidade
            volatility = self._calculate_volatility(prices)
            
            # Identifica níveis de suporte e resistência
            support_levels = self._find_support_levels(prices)
            resistance_levels = self._find_resistance_levels(prices)
            
            # Determina tendência
            trend_direction = self._determine_trend(prices[-50:])  # Últimos 50 pontos
            
            # Gera recomendação
            recommendation, confidence = self._generate_recommendation(
                current_price=current_price,
                historical_avg=historical_avg,
                historical_max=historical_max,
                historical_min=historical_min,
                trend_direction=trend_direction,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                volatility=volatility
            )
            
            return HistoricalAnalysis(
                symbol=symbol,
                current_price=current_price,
                historical_avg=historical_avg,
                historical_max=historical_max,
                historical_min=historical_min,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                trend_direction=trend_direction,
                volatility=volatility,
                recommendation=recommendation,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Erro na análise histórica: {str(e)}")
            raise
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calcula volatilidade dos preços."""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        if not returns:
            return 0.0
        
        # Desvio padrão dos retornos
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def _find_support_levels(self, prices: List[float], window: int = 20) -> List[float]:
        """Encontra níveis de suporte."""
        support_levels = []
        
        for i in range(window, len(prices) - window):
            if prices[i] == min(prices[i-window:i+window]):
                support_levels.append(prices[i])
        
        # Remove duplicatas próximas
        support_levels = sorted(list(set(support_levels)))
        filtered_supports = []
        
        for level in support_levels:
            if not filtered_supports or abs(level - filtered_supports[-1]) / filtered_supports[-1] > 0.02:
                filtered_supports.append(level)
        
        return filtered_supports[-5:]  # Últimos 5 níveis
    
    def _find_resistance_levels(self, prices: List[float], window: int = 20) -> List[float]:
        """Encontra níveis de resistência."""
        resistance_levels = []
        
        for i in range(window, len(prices) - window):
            if prices[i] == max(prices[i-window:i+window]):
                resistance_levels.append(prices[i])
        
        # Remove duplicatas próximas
        resistance_levels = sorted(list(set(resistance_levels)))
        filtered_resistances = []
        
        for level in resistance_levels:
            if not filtered_resistances or abs(level - filtered_resistances[-1]) / filtered_resistances[-1] > 0.02:
                filtered_resistances.append(level)
        
        return filtered_resistances[-5:]  # Últimos 5 níveis
    
    def _determine_trend(self, recent_prices: List[float]) -> str:
        """Determina a tendência baseada nos preços recentes."""
        if len(recent_prices) < 3:
            return "indefinido"
        
        # Média móvel simples
        short_ma = sum(recent_prices[-10:]) / min(10, len(recent_prices))
        long_ma = sum(recent_prices[-20:]) / min(20, len(recent_prices))
        
        if short_ma > long_ma * 1.02:
            return "alta"
        elif short_ma < long_ma * 0.98:
            return "baixa"
        else:
            return "lateral"
    
    def _generate_recommendation(
        self,
        current_price: float,
        historical_avg: float,
        historical_max: float,
        historical_min: float,
        trend_direction: str,
        support_levels: List[float],
        resistance_levels: List[float],
        volatility: float
    ) -> Tuple[str, float]:
        """
        Gera recomendação de compra/venda baseada na análise.
        
        Returns:
            Tuple com recomendação e score de confiança
        """
        score = 0.0
        factors = []
        
        # Análise de preço vs histórico
        if current_price < historical_avg * 0.8:
            score += 0.3
            factors.append("Preço abaixo da média histórica")
        elif current_price > historical_avg * 1.2:
            score -= 0.3
            factors.append("Preço acima da média histórica")
        
        # Análise de tendência
        if trend_direction == "alta":
            score += 0.2
            factors.append("Tendência de alta")
        elif trend_direction == "baixa":
            score -= 0.2
            factors.append("Tendência de baixa")
        
        # Análise de suporte/resistência
        nearest_support = max([s for s in support_levels if s < current_price], default=0)
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=float('inf'))
        
        if nearest_support and (current_price - nearest_support) / current_price < 0.05:
            score += 0.2
            factors.append("Próximo ao suporte")
        
        if nearest_resistance != float('inf') and (nearest_resistance - current_price) / current_price < 0.05:
            score -= 0.2
            factors.append("Próximo à resistência")
        
        # Análise de volatilidade
        if volatility > 0.1:  # Alta volatilidade
            score -= 0.1
            factors.append("Alta volatilidade")
        
        # Determina recomendação
        if score >= 0.3:
            recommendation = "COMPRAR"
            confidence = min(score * 100, 95)
        elif score <= -0.3:
            recommendation = "VENDER"
            confidence = min(abs(score) * 100, 95)
        else:
            recommendation = "AGUARDAR"
            confidence = 50
        
        logger.info(f"Recomendação para {current_price}: {recommendation} (Confiança: {confidence:.1f}%)")
        logger.info(f"Fatores analisados: {', '.join(factors)}")
        
        return recommendation, confidence
    
    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Gera resumo do mercado para múltiplos símbolos.
        
        Args:
            symbols: Lista de símbolos para analisar
        
        Returns:
            Resumo do mercado com análises
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(symbols),
            'analyses': {},
            'market_sentiment': 'neutro'
        }
        
        buy_count = 0
        sell_count = 0
        
        for symbol in symbols:
            try:
                # Busca preço atual
                current_price_data = self.client.get_ticker_price(symbol)
                current_price = float(current_price_data['price'])
                
                # Análise histórica
                analysis = await self.analyze_historical_vs_current(
                    symbol=symbol,
                    current_price=current_price,
                    months_back=12  # 12 meses para resumo
                )
                
                summary['analyses'][symbol] = {
                    'current_price': current_price,
                    'recommendation': analysis.recommendation,
                    'confidence': analysis.confidence_score,
                    'trend': analysis.trend_direction,
                    'volatility': analysis.volatility
                }
                
                if analysis.recommendation == "COMPRAR":
                    buy_count += 1
                elif analysis.recommendation == "VENDER":
                    sell_count += 1
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol}: {str(e)}")
                summary['analyses'][symbol] = {
                    'error': str(e)
                }
        
        # Determina sentimento do mercado
        if buy_count > sell_count * 1.5:
            summary['market_sentiment'] = 'otimista'
        elif sell_count > buy_count * 1.5:
            summary['market_sentiment'] = 'pessimista'
        
        return summary
