#!/usr/bin/env python3
"""
Sistema de Comparação Histórica
Integra dados históricos com candles atuais para análise preditiva
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, text

from src.api.binance.historical_data_manager import HistoricalDataManager, HistoricalAnalysis
from src.data.historical_data_collector import HistoricalDataCollector
from src.models.price_history import PriceHistory
from src.database.postgres_manager import PostgresManager
from src.core.logging_setup import logger


@dataclass
class ComparisonResult:
    """Resultado da comparação histórica"""
    symbol: str
    current_price: float
    historical_pattern_match: float  # 0-1 score
    trend_similarity: float  # 0-1 score
    volatility_comparison: Dict[str, float]
    support_resistance_levels: Dict[str, List[float]]
    price_prediction: Dict[str, Any]
    recommendation: str
    confidence_score: float
    similar_periods: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]


class HistoricalComparator:
    """
    Sistema de comparação entre dados históricos e candles atuais
    """
    
    def __init__(self, binance_client=None, postgres_manager=None):
        """
        Inicializa o comparador histórico
        
        Args:
            binance_client: Cliente Binance opcional
            postgres_manager: Gerenciador PostgreSQL opcional
        """
        self.historical_manager = HistoricalDataManager(binance_client)
        self.data_collector = HistoricalDataCollector()
        self.postgres_db = postgres_manager or PostgresManager()
        
        # Configurações de análise
        self.config = {
            'lookback_days': 365,  # Dias para análise histórica
            'pattern_window': 30,  # Janela para detecção de padrões
            'similarity_threshold': 0.7,  # Threshold para similaridade
            'min_confidence': 0.6,  # Confiança mínima para recomendações
            'prediction_horizon': 7,  # Dias para previsão
        }
        
    async def compare_with_historical(
        self, 
        symbol: str, 
        current_candle: Dict[str, Any],
        analysis_depth: str = "medium"
    ) -> ComparisonResult:
        """
        Compara candle atual com dados históricos
        
        Args:
            symbol: Par de moedas
            current_candle: Dados do candle atual
            analysis_depth: Profundidade da análise ("quick", "medium", "deep")
            
        Returns:
            Resultado da comparação histórica
        """
        try:
            logger.info(f"Iniciando comparação histórica para {symbol}")
            
            # Busca dados históricos
            historical_data = await self._get_historical_data(symbol, analysis_depth)
            
            if not historical_data:
                return self._create_default_result(symbol, current_candle)
            
            # Análise de padrões
            pattern_match = self._analyze_pattern_similarity(
                current_candle, historical_data
            )
            
            # Análise de tendência
            trend_similarity = self._analyze_trend_similarity(
                current_candle, historical_data
            )
            
            # Análise de volatilidade
            volatility_comparison = self._analyze_volatility_comparison(
                current_candle, historical_data
            )
            
            # Níveis de suporte e resistência
            support_resistance = self._calculate_support_resistance_levels(
                historical_data, current_candle['close']
            )
            
            # Previsão de preços
            price_prediction = await self._predict_price_movement(
                symbol, historical_data, current_candle
            )
            
            # Busca períodos similares
            similar_periods = self._find_similar_periods(
                current_candle, historical_data
            )
            
            # Avaliação de risco
            risk_assessment = self._assess_risk_based_on_history(
                historical_data, current_candle, volatility_comparison
            )
            
            # Gera recomendação
            recommendation, confidence = self._generate_recommendation(
                pattern_match, trend_similarity, price_prediction, risk_assessment
            )
            
            result = ComparisonResult(
                symbol=symbol,
                current_price=float(current_candle['close']),
                historical_pattern_match=pattern_match,
                trend_similarity=trend_similarity,
                volatility_comparison=volatility_comparison,
                support_resistance_levels=support_resistance,
                price_prediction=price_prediction,
                recommendation=recommendation,
                confidence_score=confidence,
                similar_periods=similar_periods,
                risk_assessment=risk_assessment
            )
            
            # Salva resultado no banco
            await self._save_comparison_result(result)
            
            logger.info(f"Comparação histórica para {symbol} concluída. Recomendação: {recommendation}")
            return result
            
        except Exception as e:
            logger.error(f"Erro na comparação histórica para {symbol}: {str(e)}")
            return self._create_default_result(symbol, current_candle)
    
    async def _get_historical_data(self, symbol: str, depth: str) -> Optional[List[Dict]]:
        """Busca dados históricos baseado na profundidade"""
        try:
            if depth == "quick":
                months_back = 3
            elif depth == "medium":
                months_back = 6
            else:  # deep
                months_back = 12
            
            # Primeiro tenta buscar do cache/banco
            cached_data = self._get_cached_historical_data(symbol, months_back)
            if cached_data:
                return cached_data
            
            # Se não tem cache, busca da API
            historical_data = await self.historical_manager.fetch_historical_data(
                symbol=symbol,
                interval="1d",
                months_back=months_back
            )
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos: {str(e)}")
            return None
    
    def _get_cached_historical_data(self, symbol: str, months_back: int) -> Optional[List[Dict]]:
        """Busca dados históricos do cache PostgreSQL"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            data = self.postgres_db.get_price_history(
                symbol=symbol,
                interval="1d",
                limit=months_back * 30,
                start_time=start_date,
                end_time=end_date
            )
            
            if len(data) > 30:  # Pelo menos 30 dias de dados
                return data
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados em cache: {str(e)}")
            return None
    
    def _analyze_pattern_similarity(
        self, 
        current_candle: Dict[str, Any], 
        historical_data: List[Dict]
    ) -> float:
        """Analisa similaridade de padrões"""
        try:
            if len(historical_data) < 30:
                return 0.5
            
            # Converte para DataFrame
            df = pd.DataFrame(historical_data)
            df['returns'] = df['close'].pct_change()
            
            # Calcula estatísticas do candle atual
            current_price = float(current_candle['close'])
            avg_price = df['close'].mean()
            price_position = (current_price - avg_price) / avg_price
            
            # Analisa posição relativa
            percentile = df['close'].rank(pct=True).iloc[-1] if len(df) > 0 else 0.5
            
            # Calcula score baseado em posição e tendência
            pattern_score = (percentile + abs(price_position)) / 2
            
            return min(max(pattern_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Erro na análise de padrões: {str(e)}")
            return 0.5
    
    def _analyze_trend_similarity(
        self, 
        current_candle: Dict[str, Any], 
        historical_data: List[Dict]
    ) -> float:
        """Analisa similaridade de tendência"""
        try:
            if len(historical_data) < 20:
                return 0.5
            
            df = pd.DataFrame(historical_data)
            df = df.sort_values('open_time')
            
            # Calcula médias móveis
            df['sma_10'] = df['close'].rolling(10).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            
            # Tendência atual
            latest_prices = df['close'].tail(10)
            current_trend = "up" if latest_prices.iloc[-1] > latest_prices.iloc[0] else "down"
            
            # Força da tendência
            trend_strength = abs(latest_prices.pct_change().mean())
            
            # Score baseado em tendência e força
            base_score = 0.7 if current_trend == "up" else 0.3
            trend_score = base_score + (trend_strength * 0.3)
            
            return min(max(trend_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Erro na análise de tendência: {str(e)}")
            return 0.5
    
    def _analyze_volatility_comparison(
        self, 
        current_candle: Dict[str, Any], 
        historical_data: List[Dict]
    ) -> Dict[str, float]:
        """Compara volatilidade atual com histórica"""
        try:
            df = pd.DataFrame(historical_data)
            df['returns'] = df['close'].pct_change()
            
            # Volatilidade histórica
            historical_volatility = df['returns'].std() * np.sqrt(252)  # Anualizada
            
            # Volatilidade recente (últimos 30 dias)
            recent_volatility = df['returns'].tail(30).std() * np.sqrt(252)
            
            # Volatilidade do candle atual
            current_range = (float(current_candle['high']) - float(current_candle['low']))
            current_volatility = current_range / float(current_candle['close'])
            
            return {
                'historical_volatility': float(historical_volatility),
                'recent_volatility': float(recent_volatility),
                'current_volatility': float(current_volatility),
                'volatility_ratio': float(recent_volatility / historical_volatility) if historical_volatility > 0 else 1.0,
                'volatility_percentile': float(df['returns'].abs().rank(pct=True).iloc[-1]) if len(df) > 0 else 0.5
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de volatilidade: {str(e)}")
            return {
                'historical_volatility': 0.2,
                'recent_volatility': 0.2,
                'current_volatility': 0.1,
                'volatility_ratio': 1.0,
                'volatility_percentile': 0.5
            }
    
    def _calculate_support_resistance_levels(
        self, 
        historical_data: List[Dict], 
        current_price: float
    ) -> Dict[str, List[float]]:
        """Calcula níveis de suporte e resistência"""
        try:
            df = pd.DataFrame(historical_data)
            
            # Identifica máximos e mínimos locais
            window = 20
            df['high_peak'] = df['high'].rolling(window, center=True).max() == df['high']
            df['low_valley'] = df['low'].rolling(window, center=True).min() == df['low']
            
            # Extrai níveis
            resistance_levels = df[df['high_peak']]['high'].tolist()
            support_levels = df[df['low_valley']]['low'].tolist()
            
            # Filtra níveis próximos ao preço atual
            price_range = current_price * 0.1  # 10% do preço atual
            
            relevant_resistance = [
                r for r in resistance_levels 
                if current_price < r < current_price + price_range
            ]
            
            relevant_support = [
                s for s in support_levels 
                if current_price - price_range < s < current_price
            ]
            
            # Ordena e pega os mais relevantes
            relevant_resistance.sort()
            relevant_support.sort(reverse=True)
            
            return {
                'resistance_levels': relevant_resistance[:5],
                'support_levels': relevant_support[:5],
                'nearest_resistance': relevant_resistance[0] if relevant_resistance else None,
                'nearest_support': relevant_support[0] if relevant_support else None
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de suporte/resistência: {str(e)}")
            return {
                'resistance_levels': [],
                'support_levels': [],
                'nearest_resistance': None,
                'nearest_support': None
            }
    
    async def _predict_price_movement(
        self, 
        symbol: str, 
        historical_data: List[Dict], 
        current_candle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prediz movimento de preços baseado em histórico"""
        try:
            df = pd.DataFrame(historical_data)
            current_price = float(current_candle['close'])
            
            # Análise de momentum
            df['returns'] = df['close'].pct_change()
            recent_momentum = df['returns'].tail(10).mean()
            
            # Análise de padrões sazonais (dia da semana, etc.)
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['hour'] = df['timestamp'].dt.hour
            
            # Previsão simples baseada em momentum e média
            sma_20 = df['close'].tail(20).mean()
            trend_direction = "up" if current_price > sma_20 else "down"
            
            # Calcula targets baseados em volatilidade histórica
            volatility = df['returns'].std()
            
            target_high = current_price * (1 + volatility * 2)
            target_low = current_price * (1 - volatility * 2)
            
            # Probabilidade baseada em tendência e momentum
            if trend_direction == "up" and recent_momentum > 0:
                up_probability = 0.7
            elif trend_direction == "down" and recent_momentum < 0:
                up_probability = 0.3
            else:
                up_probability = 0.5
            
            return {
                'direction': trend_direction,
                'up_probability': float(up_probability),
                'down_probability': float(1 - up_probability),
                'target_high': float(target_high),
                'target_low': float(target_low),
                'expected_return': float(recent_momentum),
                'confidence': min(abs(recent_momentum) * 10, 0.9)
            }
            
        except Exception as e:
            logger.error(f"Erro na previsão de preços: {str(e)}")
            return {
                'direction': 'neutral',
                'up_probability': 0.5,
                'down_probability': 0.5,
                'target_high': float(current_candle['close']) * 1.02,
                'target_low': float(current_candle['close']) * 0.98,
                'expected_return': 0.0,
                'confidence': 0.1
            }
    
    def _find_similar_periods(
        self, 
        current_candle: Dict[str, Any], 
        historical_data: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Encontra períodos históricos similares"""
        try:
            df = pd.DataFrame(historical_data)
            current_price = float(current_candle['close'])
            
            # Calcula similaridade baseada em preço e volatilidade
            df['price_similarity'] = 1 - abs(df['close'] - current_price) / current_price
            df['returns'] = df['close'].pct_change()
            
            # Filtra períodos com alta similaridade
            similar_periods = df[df['price_similarity'] > 0.95].copy()
            
            if len(similar_periods) > 0:
                # Adiciona informações sobre o que aconteceu depois
                similar_periods['future_return'] = similar_periods['close'].shift(-7).pct_change()
                
                # Remove períodos sem dados futuros
                similar_periods = similar_periods.dropna(subset=['future_return'])
                
                # Converte para lista de dicionários
                similar_list = []
                for _, row in similar_periods.iterrows():
                    similar_list.append({
                        'date': str(row.get('timestamp', row.get('open_time'))),
                        'price': float(row['close']),
                        'similarity_score': float(row['price_similarity']),
                        'future_return': float(row['future_return']),
                        'outcome': 'positive' if row['future_return'] > 0 else 'negative'
                    })
                
                return similar_list[:10]  # Top 10 períodos similares
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar períodos similares: {str(e)}")
            return []
    
    def _assess_risk_based_on_history(
        self, 
        historical_data: List[Dict], 
        current_candle: Dict[str, Any],
        volatility_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Avalia risco baseado em dados históricos"""
        try:
            df = pd.DataFrame(historical_data)
            current_price = float(current_candle['close'])
            
            # Calcula Value at Risk (VaR)
            df['returns'] = df['close'].pct_change()
            var_95 = df['returns'].quantile(0.05)  # 5% pior retorno
            var_99 = df['returns'].quantile(0.01)  # 1% pior retorno
            
            # Máximo drawdown histórico
            df['cumulative'] = (1 + df['returns']).cumprod()
            running_max = df['cumulative'].expanding().max()
            drawdown = (df['cumulative'] - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Score de risco baseado em volatilidade e drawdown
            volatility_score = min(volatility_data['volatility_ratio'], 2.0) / 2.0
            drawdown_score = min(abs(max_drawdown), 0.5) / 0.5
            
            overall_risk_score = (volatility_score + drawdown_score) / 2
            
            # Classificação de risco
            if overall_risk_score < 0.3:
                risk_level = "baixo"
            elif overall_risk_score < 0.7:
                risk_level = "médio"
            else:
                risk_level = "alto"
            
            return {
                'risk_level': risk_level,
                'risk_score': float(overall_risk_score),
                'var_95': float(var_95),
                'var_99': float(var_99),
                'max_drawdown': float(max_drawdown),
                'recommended_position_size': self._calculate_position_size(overall_risk_score),
                'stop_loss_suggestion': float(current_price * (1 + var_95 * 1.5)),
                'take_profit_suggestion': float(current_price * (1 - var_95 * 0.75))
            }
            
        except Exception as e:
            logger.error(f"Erro na avaliação de risco: {str(e)}")
            return {
                'risk_level': "médio",
                'risk_score': 0.5,
                'var_95': -0.02,
                'var_99': -0.05,
                'max_drawdown': -0.2,
                'recommended_position_size': 0.02,
                'stop_loss_suggestion': float(current_candle['close']) * 0.98,
                'take_profit_suggestion': float(current_candle['close']) * 1.02
            }
    
    def _calculate_position_size(self, risk_score: float) -> float:
        """Calcula tamanho de posição baseado no risco"""
        # Quanto maior o risco, menor a posição
        base_size = 0.05  # 5% do capital base
        risk_adjustment = 1 - risk_score
        return base_size * risk_adjustment
    
    def _generate_recommendation(
        self, 
        pattern_match: float, 
        trend_similarity: float, 
        price_prediction: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Gera recomendação final baseada em todas as análises"""
        try:
            # Pontuação combinada
            technical_score = (pattern_match + trend_similarity) / 2
            prediction_score = price_prediction['up_probability']
            risk_score = 1 - risk_assessment['risk_score']  # Inverso do risco
            
            # Média ponderada
            combined_score = (
                technical_score * 0.4 + 
                prediction_score * 0.4 + 
                risk_score * 0.2
            )
            
            # Gera recomendação
            if combined_score >= 0.7:
                recommendation = "COMPRAR"
                confidence = combined_score
            elif combined_score <= 0.3:
                recommendation = "VENDER"
                confidence = 1 - combined_score
            else:
                recommendation = "AGUARDAR"
                confidence = 0.5
            
            return recommendation, min(confidence, 0.95)
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendação: {str(e)}")
            return "AGUARDAR", 0.1
    
    def _create_default_result(self, symbol: str, current_candle: Dict[str, Any]) -> ComparisonResult:
        """Cria resultado padrão em caso de erro"""
        return ComparisonResult(
            symbol=symbol,
            current_price=float(current_candle['close']),
            historical_pattern_match=0.5,
            trend_similarity=0.5,
            volatility_comparison={'historical_volatility': 0.2, 'recent_volatility': 0.2, 'current_volatility': 0.1, 'volatility_ratio': 1.0, 'volatility_percentile': 0.5},
            support_resistance_levels={'resistance_levels': [], 'support_levels': [], 'nearest_resistance': None, 'nearest_support': None},
            price_prediction={'direction': 'neutral', 'up_probability': 0.5, 'down_probability': 0.5, 'target_high': float(current_candle['close']) * 1.02, 'target_low': float(current_candle['close']) * 0.98, 'expected_return': 0.0, 'confidence': 0.1},
            recommendation="AGUARDAR",
            confidence_score=0.1,
            similar_periods=[],
            risk_assessment={'risk_level': "médio", 'risk_score': 0.5, 'var_95': -0.02, 'var_99': -0.05, 'max_drawdown': -0.2, 'recommended_position_size': 0.02, 'stop_loss_suggestion': float(current_candle['close']) * 0.98, 'take_profit_suggestion': float(current_candle['close']) * 1.02}
        )
    
    async def _save_comparison_result(self, result: ComparisonResult) -> None:
        """Salva resultado da comparação no banco"""
        try:
            analysis_data = {
                'symbol': result.symbol,
                'current_price': result.current_price,
                'pattern_match': result.historical_pattern_match,
                'trend_similarity': result.trend_similarity,
                'volatility_comparison': result.volatility_comparison,
                'support_resistance': result.support_resistance_levels,
                'price_prediction': result.price_prediction,
                'recommendation': result.recommendation,
                'confidence_score': result.confidence_score,
                'similar_periods': result.similar_periods,
                'risk_assessment': result.risk_assessment,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            self.postgres_db.save_analysis(
                symbol=result.symbol,
                analysis_type='historical_comparison',
                data=analysis_data
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultado da comparação: {str(e)}")
    
    async def get_symbol_historical_insights(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém insights históricos completos para um símbolo
        
        Args:
            symbol: Par de moedas
            
        Returns:
            Insights históricos completos
        """
        try:
            # Busca dados históricos
            historical_data = await self._get_historical_data(symbol, "deep")
            
            if not historical_data:
                return {'error': 'Sem dados históricos disponíveis'}
            
            df = pd.DataFrame(historical_data)
            
            # Análises estatísticas
            insights = {
                'symbol': symbol,
                'data_period': {
                    'start_date': str(df['open_time'].min()),
                    'end_date': str(df['open_time'].max()),
                    'total_days': len(df)
                },
                'price_statistics': {
                    'min_price': float(df['low'].min()),
                    'max_price': float(df['high'].max()),
                    'avg_price': float(df['close'].mean()),
                    'current_vs_avg': float((df['close'].iloc[-1] - df['close'].mean()) / df['close'].mean()),
                    'price_range': float(df['high'].max() - df['low'].min())
                },
                'volatility_analysis': {
                    'daily_volatility': float(df['close'].pct_change().std()),
                    'monthly_volatility': float(df['close'].pct_change().std() * np.sqrt(30)),
                    'annual_volatility': float(df['close'].pct_change().std() * np.sqrt(365))
                },
                'trend_analysis': {
                    'overall_trend': 'up' if df['close'].iloc[-1] > df['close'].iloc[0] else 'down',
                    'total_return': float((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]),
                    'best_month_return': float(df['close'].pct_change().rolling(30).sum().max()),
                    'worst_month_return': float(df['close'].pct_change().rolling(30).sum().min())
                },
                'volume_analysis': {
                    'avg_volume': float(df['volume'].mean()),
                    'volume_trend': 'increasing' if df['volume'].tail(30).mean() > df['volume'].head(30).mean() else 'decreasing',
                    'high_volume_days': int((df['volume'] > df['volume'].quantile(0.9)).sum())
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Erro ao obter insights históricos: {str(e)}")
            return {'error': str(e)}
    
    async def batch_analyze_symbols(self, symbols: List[str]) -> Dict[str, ComparisonResult]:
        """
        Analisa múltiplos símbolos em batch
        
        Args:
            symbols: Lista de símbolos para analisar
            
        Returns:
            Dicionário com resultados por símbolo
        """
        results = {}
        
        for symbol in symbols:
            try:
                # Busca dados atuais (simulado - você deve integrar com sua fonte de dados)
                current_candle = {
                    'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500,
                    'volume': 1000, 'open_time': int(datetime.now().timestamp() * 1000)
                }
                
                result = await self.compare_with_historical(symbol, current_candle)
                results[symbol] = result
                
                # Delay para evitar rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol}: {str(e)}")
                results[symbol] = self._create_default_result(symbol, current_candle)
        
        return results


# Função de conveniência para uso fácil
async def compare_symbol_with_history(
    symbol: str, 
    current_candle: Dict[str, Any],
    depth: str = "medium"
) -> ComparisonResult:
    """
    Função de conveniência para comparar símbolo com histórico
    
    Args:
        symbol: Par de moedas
        current_candle: Dados do candle atual
        depth: Profundidade da análise
        
    Returns:
        Resultado da comparação
    """
    comparator = HistoricalComparator()
    return await comparator.compare_with_historical(symbol, current_candle, depth)
