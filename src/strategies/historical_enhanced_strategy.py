"""
Estratégia de trading aprimorada com análise histórica da Binance.
Integra dados históricos de até 24 meses para tomar decisões mais informadas.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from src.api.binance.client import BinanceClient
from src.api.binance.historical_data_manager import HistoricalDataManager, HistoricalAnalysis
from src.strategies.enhanced_strategy import EnhancedTradingStrategy
from src.core.logging_setup import logger


@dataclass
class HistoricalTradingSignal:
    """Sinal de trading baseado em análise histórica."""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    current_price: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reasoning: List[str]
    historical_context: Dict[str, Any]
    timestamp: datetime


class HistoricalEnhancedStrategy(EnhancedTradingStrategy):
    """
    Estratégia de trading aprimorada com análise histórica.
    Combina análise técnica tradicional com insights de dados históricos.
    """
    
    def __init__(self, binance_client: Optional[BinanceClient] = None):
        """
        Inicializa a estratégia com análise histórica.
        
        Args:
            binance_client: Cliente Binance opcional
        """
        super().__init__(binance_client)
        self.historical_manager = HistoricalDataManager(binance_client)
        self.analysis_cache = {}
        self.cache_expiry = timedelta(hours=1)
        
    async def analyze_symbol_with_history(
        self, 
        symbol: str, 
        timeframe: str = "1d",
        months_back: int = 12
    ) -> HistoricalTradingSignal:
        """
        Analisa um símbolo com contexto histórico.
        
        Args:
            symbol: Par de moedas
            timeframe: Intervalo de tempo
            months_back: Meses de histórico para análise
        
        Returns:
            Sinal de trading com contexto histórico
        """
        try:
            # Verifica cache
            cache_key = f"{symbol}_{timeframe}_{months_back}"
            if self._is_cache_valid(cache_key):
                return self.analysis_cache[cache_key]['signal']
            
            # Busca preço atual
            current_price_data = self.binance_client.get_ticker_price(symbol)
            current_price = float(current_price_data['price'])
            
            # Análise histórica
            historical_analysis = await self.historical_manager.analyze_historical_vs_current(
                symbol=symbol,
                current_price=current_price,
                interval=timeframe,
                months_back=months_back
            )
            
            # Análise técnica tradicional
            technical_signal = await self.analyze_symbol(symbol)
            
            # Combina análises
            combined_signal = await self._combine_analyses(
                symbol=symbol,
                historical_analysis=historical_analysis,
                technical_signal=technical_signal,
                current_price=current_price
            )
            
            # Atualiza cache
            self.analysis_cache[cache_key] = {
                'signal': combined_signal,
                'timestamp': datetime.now()
            }
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Erro na análise histórica de {symbol}: {str(e)}")
            raise
    
    async def _combine_analyses(
        self,
        symbol: str,
        historical_analysis: HistoricalAnalysis,
        technical_signal: Dict[str, Any],
        current_price: float
    ) -> HistoricalTradingSignal:
        """
        Combina análise histórica com análise técnica.
        
        Args:
            symbol: Par de moedas
            historical_analysis: Análise histórica
            technical_signal: Sinal técnico tradicional
            current_price: Preço atual
        
        Returns:
            Sinal de trading combinado
        """
        reasoning = []
        confidence_factors = []
        
        # Análise da recomendação histórica
        hist_weight = 0.6  # Peso da análise histórica
        tech_weight = 0.4  # Peso da análise técnica
        
        # Mapeia recomendação histórica
        hist_score = 0
        if historical_analysis.recommendation == "COMPRAR":
            hist_score = 1
            reasoning.append(f"Análise histórica sugere COMPRA (confiança: {historical_analysis.confidence_score:.1f}%)")
        elif historical_analysis.recommendation == "VENDER":
            hist_score = -1
            reasoning.append(f"Análise histórica sugere VENDA (confiança: {historical_analysis.confidence_score:.1f}%)")
        else:
            reasoning.append("Análise histórica sugere AGUARDAR")
        
        confidence_factors.append(historical_analysis.confidence_score / 100)
        
        # Mapeia sinal técnico
        tech_score = 0
        if technical_signal.get('action') == 'BUY':
            tech_score = 1
            reasoning.append("Análise técnica sugere COMPRA")
        elif technical_signal.get('action') == 'SELL':
            tech_score = -1
            reasoning.append("Análise técnica sugere VENDA")
        else:
            reasoning.append("Análise técnica sugere AGUARDAR")
        
        if 'confidence' in technical_signal:
            confidence_factors.append(technical_signal['confidence'] / 100)
        
        # Calcula score combinado
        combined_score = (hist_score * hist_weight) + (tech_score * tech_weight)
        
        # Análise adicional de contexto
        price_vs_avg = (current_price - historical_analysis.historical_avg) / historical_analysis.historical_avg
        
        # Ajustes baseados em contexto histórico
        if abs(price_vs_avg) > 0.2:  # Desvio significativo da média
            if price_vs_avg < -0.2:  # Muito abaixo da média
                combined_score += 0.2
                reasoning.append(f"Preço {abs(price_vs_avg):.1%} abaixo da média histórica")
            elif price_vs_avg > 0.2:  # Muito acima da média
                combined_score -= 0.2
                reasoning.append(f"Preço {price_vs_avg:.1%} acima da média histórica")
        
        # Ajuste por volatilidade
        if historical_analysis.volatility > 0.1:  # Alta volatilidade
            combined_score *= 0.8  # Reduz confiança
            reasoning.append(f"Alta volatilidade detectada ({historical_analysis.volatility:.1%})")
        
        # Ajuste por tendência
        if historical_analysis.trend_direction == "alta":
            combined_score += 0.1
            reasoning.append("Tendência histórica de alta")
        elif historical_analysis.trend_direction == "baixa":
            combined_score -= 0.1
            reasoning.append("Tendência histórica de baixa")
        
        # Determina ação final
        if combined_score >= 0.3:
            action = "BUY"
        elif combined_score <= -0.3:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Calcula confiança final
        final_confidence = min(sum(confidence_factors) / len(confidence_factors) * 100, 95)
        
        # Calcula níveis de entrada, stop loss e take profit
        entry_price, stop_loss, take_profit = self._calculate_trade_levels(
            current_price=current_price,
            historical_analysis=historical_analysis,
            action=action
        )
        
        # Contexto histórico adicional
        historical_context = {
            'avg_price': historical_analysis.historical_avg,
            'max_price': historical_analysis.historical_max,
            'min_price': historical_analysis.historical_min,
            'volatility': historical_analysis.volatility,
            'trend': historical_analysis.trend_direction,
            'support_levels': historical_analysis.support_levels,
            'resistance_levels': historical_analysis.resistance_levels,
            'price_vs_avg_pct': price_vs_avg * 100
        }
        
        return HistoricalTradingSignal(
            symbol=symbol,
            action=action,
            confidence=final_confidence,
            current_price=current_price,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            historical_context=historical_context,
            timestamp=datetime.now()
        )
    
    def _calculate_trade_levels(
        self,
        current_price: float,
        historical_analysis: HistoricalAnalysis,
        action: str
    ) -> Tuple[float, float, float]:
        """
        Calcula níveis de entrada, stop loss e take profit.
        
        Args:
            current_price: Preço atual
            historical_analysis: Análise histórica
            action: Ação (BUY/SELL/HOLD)
        
        Returns:
            Tuple com (entry_price, stop_loss, take_profit)
        """
        entry_price = current_price
        
        if action == "BUY":
            # Stop loss baseado em suporte mais próximo ou 5% abaixo
            nearest_support = 0
            for support in historical_analysis.support_levels:
                if support < current_price:
                    nearest_support = max(nearest_support, support)
            
            if nearest_support > 0:
                stop_loss = nearest_support * 0.98  # 2% abaixo do suporte
            else:
                stop_loss = current_price * 0.95  # 5% abaixo do preço atual
            
            # Take profit baseado em resistência mais próxima ou 10% acima
            nearest_resistance = float('inf')
            for resistance in historical_analysis.resistance_levels:
                if resistance > current_price:
                    nearest_resistance = min(nearest_resistance, resistance)
            
            if nearest_resistance != float('inf'):
                take_profit = nearest_resistance * 0.98  # 2% abaixo da resistência
            else:
                take_profit = current_price * 1.10  # 10% acima do preço atual
        
        elif action == "SELL":
            # Stop loss baseado em resistência mais próxima ou 5% acima
            nearest_resistance = float('inf')
            for resistance in historical_analysis.resistance_levels:
                if resistance > current_price:
                    nearest_resistance = min(nearest_resistance, resistance)
            
            if nearest_resistance != float('inf'):
                stop_loss = nearest_resistance * 1.02  # 2% acima da resistência
            else:
                stop_loss = current_price * 1.05  # 5% acima do preço atual
            
            # Take profit baseado em suporte mais próximo ou 10% abaixo
            nearest_support = 0
            for support in historical_analysis.support_levels:
                if support < current_price:
                    nearest_support = max(nearest_support, support)
            
            if nearest_support > 0:
                take_profit = nearest_support * 1.02  # 2% acima do suporte
            else:
                take_profit = current_price * 0.90  # 10% abaixo do preço atual
        
        else:  # HOLD
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05
        
        return entry_price, stop_loss, take_profit
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido."""
        if cache_key not in self.analysis_cache:
            return False
        
        cache_time = self.analysis_cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_expiry
    
    async def scan_market_opportunities(
        self, 
        symbols: List[str],
        min_confidence: float = 70.0
    ) -> List[HistoricalTradingSignal]:
        """
        Escaneia múltiplos símbolos em busca de oportunidades.
        
        Args:
            symbols: Lista de símbolos para analisar
            min_confidence: Confiança mínima para incluir o sinal
        
        Returns:
            Lista de sinais de trading promissores
        """
        opportunities = []
        
        for symbol in symbols:
            try:
                signal = await self.analyze_symbol_with_history(symbol)
                
                if signal.confidence >= min_confidence and signal.action != "HOLD":
                    opportunities.append(signal)
                    logger.info(f"Oportunidade encontrada: {symbol} - {signal.action} (confiança: {signal.confidence:.1f}%)")
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol}: {str(e)}")
                continue
        
        # Ordena por confiança
        opportunities.sort(key=lambda x: x.confidence, reverse=True)
        
        return opportunities
    
    async def generate_market_report(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Gera relatório detalhado do mercado.
        
        Args:
            symbols: Lista de símbolos para analisar
        
        Returns:
            Relatório detalhado do mercado
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(symbols),
            'signals': {},
            'opportunities': [],
            'market_summary': {
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'avg_confidence': 0.0
            }
        }
        
        total_confidence = 0
        
        for symbol in symbols:
            try:
                signal = await self.analyze_symbol_with_history(symbol)
                
                report['signals'][symbol] = {
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'current_price': signal.current_price,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'reasoning': signal.reasoning,
                    'historical_context': signal.historical_context
                }
                
                # Atualiza estatísticas
                if signal.action == "BUY":
                    report['market_summary']['bullish_count'] += 1
                elif signal.action == "SELL":
                    report['market_summary']['bearish_count'] += 1
                else:
                    report['market_summary']['neutral_count'] += 1
                
                total_confidence += signal.confidence
                
                # Adiciona oportunidades de alta confiança
                if signal.confidence >= 75.0 and signal.action != "HOLD":
                    report['opportunities'].append({
                        'symbol': symbol,
                        'action': signal.action,
                        'confidence': signal.confidence,
                        'potential_return': self._calculate_potential_return(signal),
                        'risk_reward_ratio': self._calculate_risk_reward_ratio(signal)
                    })
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol} para relatório: {str(e)}")
                report['signals'][symbol] = {'error': str(e)}
        
        # Calcula médias
        if len(symbols) > 0:
            report['market_summary']['avg_confidence'] = total_confidence / len(symbols)
        
        # Ordena oportunidades por confiança
        report['opportunities'].sort(key=lambda x: x['confidence'], reverse=True)
        
        return report
    
    def _calculate_potential_return(self, signal: HistoricalTradingSignal) -> float:
        """Calcula retorno potencial do sinal."""
        if signal.action == "BUY":
            return ((signal.take_profit - signal.entry_price) / signal.entry_price) * 100
        elif signal.action == "SELL":
            return ((signal.entry_price - signal.take_profit) / signal.entry_price) * 100
        return 0.0
    
    def _calculate_risk_reward_ratio(self, signal: HistoricalTradingSignal) -> float:
        """Calcula relação risco/recompensa."""
        if signal.action == "BUY":
            risk = abs(signal.entry_price - signal.stop_loss)
            reward = abs(signal.take_profit - signal.entry_price)
        elif signal.action == "SELL":
            risk = abs(signal.stop_loss - signal.entry_price)
            reward = abs(signal.entry_price - signal.take_profit)
        else:
            return 0.0
        
        return reward / risk if risk > 0 else 0.0
    
    async def backtest_strategy(
        self,
        symbol: str,
        days_back: int = 365,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Testa a estratégia com dados históricos.
        
        Args:
            symbol: Símbolo para backtest
            days_back: Dias de história para testar
            initial_capital: Capital inicial
        
        Returns:
            Resultados do backtest
        """
        # Implementação básica do backtest
        # Você pode expandir isso com mais detalhes
        
        try:
            # Busca dados históricos
            historical_data = await self.historical_manager.fetch_historical_data(
                symbol=symbol,
                interval="1d",
                months_back=days_back // 30
            )
            
            trades = []
            current_capital = initial_capital
            position = None
            
            for i, data_point in enumerate(historical_data[:-1]):  # Exclui o último ponto
                current_price = float(data_point['close'])
                
                # Simula análise (simplificada)
                if i % 10 == 0:  # Análise a cada 10 dias
                    # Aqui você implementaria a lógica de análise
                    # Por agora, uma simulação básica
                    continue
            
            return {
                'symbol': symbol,
                'initial_capital': initial_capital,
                'final_capital': current_capital,
                'total_return': ((current_capital - initial_capital) / initial_capital) * 100,
                'total_trades': len(trades),
                'winning_trades': len([t for t in trades if t.get('profit', 0) > 0]),
                'losing_trades': len([t for t in trades if t.get('profit', 0) < 0])
            }
            
        except Exception as e:
            logger.error(f"Erro no backtest: {str(e)}")
            return {'error': str(e)}
