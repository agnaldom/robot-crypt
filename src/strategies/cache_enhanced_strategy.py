#!/usr/bin/env python3
"""
Cache-Enhanced Strategy Wrapper
==============================

Este módulo fornece um wrapper para estratégias existentes que integra
automaticamente o sistema de cache histórico, permitindo:

1. Acesso prioritário ao cache local
2. Fallback automático para API da Binance
3. Análise mais rápida com dados pré-carregados
4. Melhores decisões com dados históricos completos

Autor: Robot-Crypt Team
Data: 2024
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from src.cache import get_historical_data_cached, get_cache_status
from src.core.logging_setup import logger


class CacheEnhancedStrategyMixin:
    """
    Mixin para adicionar capacidades de cache a estratégias existentes.
    
    Pode ser usado com qualquer estratégia que implemente os métodos básicos
    de análise de mercado.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa o mixin com configurações de cache."""
        super().__init__(*args, **kwargs)
        self.cache_enabled = True
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'api_calls': 0
        }
        
    def get_historical_data_smart(
        self, 
        symbol: str, 
        interval: str = '1d',
        days_back: int = 30,
        force_api: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém dados históricos usando cache inteligente.
        
        Args:
            symbol: Símbolo da moeda (formato Binance: BTCUSDT)
            interval: Intervalo dos dados (1d, 4h, 1h, 15m)
            days_back: Quantos dias buscar
            force_api: Se True, força busca na API
            
        Returns:
            Lista de dados históricos ou None
        """
        try:
            # Converte símbolo se necessário (BTC/USDT -> BTCUSDT)
            if '/' in symbol:
                symbol = symbol.replace('/', '')
            
            # Busca dados usando o sistema de cache
            data = get_historical_data_cached(
                symbol=symbol,
                interval=interval,
                days_back=days_back,
                force_api=force_api
            )
            
            if data:
                # Atualiza estatísticas internas
                if force_api:
                    self.cache_stats['api_calls'] += 1
                else:
                    self.cache_stats['hits'] += 1
                
                logger.debug(f"📊 Obtidos {len(data)} pontos de dados para {symbol} {interval}")
                return data
            else:
                self.cache_stats['misses'] += 1
                logger.warning(f"⚠️ Nenhum dado histórico disponível para {symbol} {interval}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados históricos para {symbol}: {str(e)}")
            self.cache_stats['misses'] += 1
            return None
    
    def analyze_historical_trends(
        self, 
        symbol: str, 
        current_price: float,
        analysis_periods: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Analisa tendências históricas usando dados do cache.
        
        Args:
            symbol: Símbolo da moeda
            current_price: Preço atual
            analysis_periods: Períodos de análise personalizados
            
        Returns:
            Dict com análise de tendências históricas
        """
        if analysis_periods is None:
            analysis_periods = {
                'short_term': 7,    # 7 dias
                'medium_term': 30,  # 30 dias
                'long_term': 90     # 90 dias
            }
        
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'trends': {},
            'support_resistance': {},
            'volatility': {},
            'recommendations': []
        }
        
        try:
            for period_name, days in analysis_periods.items():
                # Busca dados históricos para este período
                data = self.get_historical_data_smart(symbol, '1d', days)
                
                if data:
                    # Analisa tendência
                    trend_analysis = self._analyze_trend_period(data, current_price, period_name)
                    analysis['trends'][period_name] = trend_analysis
                    
                    # Identifica suporte e resistência
                    sr_levels = self._find_support_resistance(data)
                    analysis['support_resistance'][period_name] = sr_levels
                    
                    # Calcula volatilidade
                    volatility = self._calculate_volatility([float(d['close']) for d in data])
                    analysis['volatility'][period_name] = volatility
                else:
                    logger.warning(f"⚠️ Sem dados para análise de {period_name} ({days} dias)")
            
            # Gera recomendações baseadas na análise completa
            analysis['recommendations'] = self._generate_smart_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise histórica de {symbol}: {str(e)}")
            return analysis
    
    def _analyze_trend_period(
        self, 
        data: List[Dict[str, Any]], 
        current_price: float, 
        period_name: str
    ) -> Dict[str, Any]:
        """
        Analisa tendência para um período específico.
        
        Args:
            data: Dados históricos
            current_price: Preço atual
            period_name: Nome do período
            
        Returns:
            Dict com análise da tendência
        """
        try:
            prices = [float(d['close']) for d in data]
            
            if len(prices) < 2:
                return {'direction': 'indefinido', 'strength': 0}
            
            # Calcula médias móveis
            short_ma = sum(prices[-min(5, len(prices)):]) / min(5, len(prices))
            long_ma = sum(prices) / len(prices)
            
            # Determina direção da tendência
            if current_price > long_ma * 1.05:
                direction = 'alta_forte'
                strength = min((current_price / long_ma - 1) * 100, 100)
            elif current_price > long_ma * 1.02:
                direction = 'alta'
                strength = (current_price / long_ma - 1) * 100
            elif current_price < long_ma * 0.95:
                direction = 'baixa_forte'
                strength = min((1 - current_price / long_ma) * 100, 100)
            elif current_price < long_ma * 0.98:
                direction = 'baixa'
                strength = (1 - current_price / long_ma) * 100
            else:
                direction = 'lateral'
                strength = abs(current_price / long_ma - 1) * 100
            
            return {
                'direction': direction,
                'strength': round(strength, 2),
                'short_ma': round(short_ma, 8),
                'long_ma': round(long_ma, 8),
                'price_vs_ma': round((current_price / long_ma - 1) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de tendência: {str(e)}")
            return {'direction': 'indefinido', 'strength': 0}
    
    def _find_support_resistance(self, data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Identifica níveis de suporte e resistência.
        
        Args:
            data: Dados históricos
            
        Returns:
            Dict com níveis de suporte e resistência
        """
        try:
            highs = [float(d['high']) for d in data]
            lows = [float(d['low']) for d in data]
            
            # Encontra máximos e mínimos locais
            support_levels = []
            resistance_levels = []
            
            window = min(5, len(data) // 4)  # Janela adaptativa
            
            for i in range(window, len(lows) - window):
                # Verifica se é um mínimo local (suporte)
                if lows[i] == min(lows[i-window:i+window+1]):
                    support_levels.append(lows[i])
                
                # Verifica se é um máximo local (resistência)
                if highs[i] == max(highs[i-window:i+window+1]):
                    resistance_levels.append(highs[i])
            
            # Remove duplicatas próximas e ordena
            support_levels = self._filter_close_levels(support_levels)
            resistance_levels = self._filter_close_levels(resistance_levels)
            
            return {
                'support': sorted(support_levels)[-3:],  # 3 principais suportes
                'resistance': sorted(resistance_levels, reverse=True)[:3]  # 3 principais resistências
            }
            
        except Exception as e:
            logger.error(f"Erro ao encontrar suporte/resistência: {str(e)}")
            return {'support': [], 'resistance': []}
    
    def _filter_close_levels(self, levels: List[float], threshold: float = 0.02) -> List[float]:
        """
        Remove níveis muito próximos entre si.
        
        Args:
            levels: Lista de níveis de preço
            threshold: Limiar de proximidade (2% por padrão)
            
        Returns:
            Lista filtrada de níveis
        """
        if not levels:
            return []
        
        filtered = [levels[0]]
        
        for level in sorted(levels[1:]):
            # Adiciona apenas se não estiver muito próximo dos existentes
            if all(abs(level - existing) / existing > threshold for existing in filtered):
                filtered.append(level)
        
        return filtered
    
    def _calculate_volatility(self, prices: List[float]) -> Dict[str, float]:
        """
        Calcula métricas de volatilidade.
        
        Args:
            prices: Lista de preços
            
        Returns:
            Dict com métricas de volatilidade
        """
        try:
            if len(prices) < 2:
                return {'daily_volatility': 0, 'price_range': 0}
            
            # Calcula retornos diários
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            
            # Calcula volatilidade (desvio padrão dos retornos)
            if returns:
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                daily_volatility = (variance ** 0.5) * 100  # Em percentual
            else:
                daily_volatility = 0
            
            # Calcula range de preços
            price_range = ((max(prices) - min(prices)) / min(prices)) * 100
            
            return {
                'daily_volatility': round(daily_volatility, 2),
                'price_range': round(price_range, 2),
                'avg_return': round(avg_return * 100, 4) if returns else 0
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de volatilidade: {str(e)}")
            return {'daily_volatility': 0, 'price_range': 0}
    
    def _generate_smart_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gera recomendações inteligentes baseadas na análise completa.
        
        Args:
            analysis: Análise histórica completa
            
        Returns:
            Lista de recomendações com scores de confiança
        """
        recommendations = []
        
        try:
            trends = analysis.get('trends', {})
            volatility = analysis.get('volatility', {})
            
            # Analisa tendências de curto, médio e longo prazo
            short_trend = trends.get('short_term', {}).get('direction', 'indefinido')
            medium_trend = trends.get('medium_term', {}).get('direction', 'indefinido')
            long_trend = trends.get('long_term', {}).get('direction', 'indefinido')
            
            # Score baseado em consenso de tendências
            trend_score = 0
            if short_trend in ['alta', 'alta_forte']:
                trend_score += 1
            elif short_trend in ['baixa', 'baixa_forte']:
                trend_score -= 1
                
            if medium_trend in ['alta', 'alta_forte']:
                trend_score += 1
            elif medium_trend in ['baixa', 'baixa_forte']:
                trend_score -= 1
                
            if long_trend in ['alta', 'alta_forte']:
                trend_score += 1
            elif long_trend in ['baixa', 'baixa_forte']:
                trend_score -= 1
            
            # Considera volatilidade
            avg_volatility = sum(v.get('daily_volatility', 0) for v in volatility.values()) / max(len(volatility), 1)
            
            # Gera recomendação principal
            if trend_score >= 2:
                action = 'COMPRAR'
                confidence = min(85 + trend_score * 5, 95)
                reason = f"Tendência de alta consistente ({trend_score}/3 períodos)"
            elif trend_score <= -2:
                action = 'VENDER'
                confidence = min(85 + abs(trend_score) * 5, 95)
                reason = f"Tendência de baixa consistente ({abs(trend_score)}/3 períodos)"
            else:
                action = 'AGUARDAR'
                confidence = 60
                reason = "Tendências conflitantes ou laterais"
            
            # Ajusta confiança baseado na volatilidade
            if avg_volatility > 5:  # Alta volatilidade
                confidence -= 15
                reason += " (alta volatilidade detectada)"
            elif avg_volatility < 1:  # Baixa volatilidade
                confidence += 5
                reason += " (baixa volatilidade favorável)"
            
            recommendations.append({
                'action': action,
                'confidence': max(min(confidence, 95), 30),  # Entre 30% e 95%
                'reason': reason,
                'trend_score': trend_score,
                'avg_volatility': round(avg_volatility, 2)
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
            recommendations.append({
                'action': 'AGUARDAR',
                'confidence': 50,
                'reason': 'Erro na análise histórica',
                'trend_score': 0,
                'avg_volatility': 0
            })
        
        return recommendations
    
    def get_cache_performance(self) -> Dict[str, Any]:
        """
        Retorna métricas de performance do cache.
        
        Returns:
            Dict com estatísticas de uso do cache
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / max(total_requests, 1)) * 100
        
        return {
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'api_calls': self.cache_stats['api_calls'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }


def enhance_strategy_with_cache(strategy_class):
    """
    Decorator para adicionar capacidades de cache a uma estratégia existente.
    
    Args:
        strategy_class: Classe da estratégia a ser aprimorada
        
    Returns:
        Classe estratégia com capacidades de cache
    """
    class CacheEnhancedStrategy(CacheEnhancedStrategyMixin, strategy_class):
        """Estratégia aprimorada com sistema de cache."""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            logger.info(f"✅ Estratégia {strategy_class.__name__} aprimorada com sistema de cache")
    
    CacheEnhancedStrategy.__name__ = f"CacheEnhanced{strategy_class.__name__}"
    CacheEnhancedStrategy.__qualname__ = f"CacheEnhanced{strategy_class.__name__}"
    
    return CacheEnhancedStrategy


if __name__ == "__main__":
    # Exemplo de uso do sistema
    print("🧪 Testando wrapper de cache para estratégias...")
    
    # Simula uma estratégia básica
    class ExampleStrategy:
        def __init__(self, config, client):
            self.config = config
            self.client = client
        
        def analyze_market(self, symbol):
            return True, "buy", 50000.0
    
    # Aplica o enhancement de cache
    EnhancedStrategy = enhance_strategy_with_cache(ExampleStrategy)
    
    # Testa a estratégia aprimorada
    class MockConfig:
        pass
    
    class MockClient:
        pass
    
    strategy = EnhancedStrategy(MockConfig(), MockClient())
    
    # Testa análise histórica
    analysis = strategy.analyze_historical_trends('BTCUSDT', 50000.0)
    print(f"📊 Análise: {analysis}")
    
    # Mostra performance do cache
    performance = strategy.get_cache_performance()
    print(f"📈 Performance: {performance}")
    
    print("✅ Teste concluído!")
