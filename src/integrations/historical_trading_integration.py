#!/usr/bin/env python3
"""
Sistema de Integração Histórica para Trading
Integra análise histórica ao sistema de trading do robô
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from src.analysis.historical_comparator import HistoricalComparator, ComparisonResult
from src.api.binance.client import BinanceClient
from src.database.postgres_manager import PostgresManager
from src.notifications.telegram_notifier import TelegramNotifier
from src.core.logging_setup import logger


@dataclass
class TradingSignal:
    """Sinal de trading gerado pela análise histórica"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float
    reasoning: str
    timestamp: datetime
    historical_context: Dict[str, Any]


class HistoricalTradingIntegration:
    """
    Sistema que integra análise histórica ao processo de trading
    """
    
    def __init__(self, binance_client=None, postgres_manager=None, telegram_notifier=None):
        """
        Inicializa o sistema de integração
        
        Args:
            binance_client: Cliente Binance
            postgres_manager: Gerenciador PostgreSQL
            telegram_notifier: Notificador Telegram
        """
        self.binance_client = binance_client or BinanceClient()
        self.postgres_db = postgres_manager or PostgresManager()
        self.telegram = telegram_notifier
        self.historical_comparator = HistoricalComparator(binance_client, postgres_manager)
        
        # Configurações de trading
        self.config = {
            'min_confidence_for_signal': 0.65,  # Confiança mínima para gerar sinal
            'max_position_risk': 0.02,  # Máximo 2% do capital por posição
            'enable_notifications': True,  # Enviar notificações
            'analysis_interval': 300,  # Analisar a cada 5 minutos
            'symbols_to_monitor': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
            'enable_auto_trading': False,  # Se deve executar trades automaticamente
            'risk_management_enabled': True,  # Gerenciamento de risco ativo
        }
        
        # Cache para evitar análises repetidas
        self.last_analysis_cache = {}
        self.active_signals = {}
        
    async def analyze_market_with_history(self, symbols: List[str] = None) -> Dict[str, TradingSignal]:
        """
        Analisa o mercado usando dados históricos
        
        Args:
            symbols: Lista de símbolos para analisar (usa configuração se None)
            
        Returns:
            Dicionário com sinais de trading por símbolo
        """
        if symbols is None:
            symbols = self.config['symbols_to_monitor']
        
        signals = {}
        
        logger.info(f"Iniciando análise histórica de {len(symbols)} símbolos")
        
        for symbol in symbols:
            try:
                # Verifica cache para evitar análises muito frequentes
                if self._should_skip_analysis(symbol):
                    continue
                
                # Busca dados atuais do símbolo
                current_candle = await self._get_current_candle(symbol)
                if not current_candle:
                    continue
                
                # Executa comparação histórica
                comparison_result = await self.historical_comparator.compare_with_historical(
                    symbol=symbol,
                    current_candle=current_candle,
                    analysis_depth="medium"
                )
                
                # Gera sinal de trading baseado na análise
                signal = self._generate_trading_signal(symbol, comparison_result, current_candle)
                
                if signal and signal.confidence >= self.config['min_confidence_for_signal']:
                    signals[symbol] = signal
                    
                    # Salva sinal no banco
                    await self._save_trading_signal(signal)
                    
                    # Envia notificação se habilitado
                    if self.config['enable_notifications'] and self.telegram:
                        await self._send_signal_notification(signal, comparison_result)
                
                # Atualiza cache
                self.last_analysis_cache[symbol] = datetime.now()
                
                # Pequeno delay para evitar rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol}: {str(e)}")
                continue
        
        logger.info(f"Análise concluída. {len(signals)} sinais gerados")
        return signals
    
    async def _get_current_candle(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Busca dados do candle atual"""
        try:
            # Busca dados de 24h
            ticker = self.binance_client.get_ticker_24hr(symbol)
            
            # Busca últimos klines
            klines = self.binance_client.get_klines(symbol=symbol, interval='1h', limit=1)
            
            if not klines:
                return None
            
            kline = klines[0]
            current_candle = {
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'open_time': int(kline[0]),
                'close_time': int(kline[6]),
                'quote_volume': float(kline[7]),
                'count': int(kline[8])
            }
            
            return current_candle
            
        except Exception as e:
            logger.error(f"Erro ao buscar candle atual para {symbol}: {str(e)}")
            return None
    
    def _should_skip_analysis(self, symbol: str) -> bool:
        """Verifica se deve pular análise baseado no cache"""
        if symbol not in self.last_analysis_cache:
            return False
        
        last_analysis = self.last_analysis_cache[symbol]
        time_since_last = (datetime.now() - last_analysis).total_seconds()
        
        # Pula se analisou há menos de 5 minutos
        return time_since_last < self.config['analysis_interval']
    
    def _generate_trading_signal(
        self, 
        symbol: str, 
        comparison_result: ComparisonResult,
        current_candle: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """Gera sinal de trading baseado na comparação histórica"""
        try:
            recommendation = comparison_result.recommendation
            confidence = comparison_result.confidence_score
            
            if confidence < self.config['min_confidence_for_signal']:
                return None
            
            # Determina ação
            if recommendation == "COMPRAR":
                action = "BUY"
            elif recommendation == "VENDER":
                action = "SELL"
            else:
                action = "HOLD"
            
            # Calcula níveis de stop loss e take profit
            entry_price = comparison_result.current_price
            stop_loss = comparison_result.risk_assessment.get('stop_loss_suggestion')
            take_profit = comparison_result.risk_assessment.get('take_profit_suggestion')
            
            # Ajusta níveis baseado na direção
            if action == "BUY":
                if not stop_loss or stop_loss > entry_price:
                    stop_loss = entry_price * 0.98  # 2% stop loss
                if not take_profit or take_profit < entry_price:
                    take_profit = entry_price * 1.04  # 4% take profit
            elif action == "SELL":
                if not stop_loss or stop_loss < entry_price:
                    stop_loss = entry_price * 1.02  # 2% stop loss
                if not take_profit or take_profit > entry_price:
                    take_profit = entry_price * 0.96  # 4% take profit
            
            # Calcula tamanho da posição
            position_size = self._calculate_position_size(
                comparison_result.risk_assessment, 
                entry_price
            )
            
            # Gera reasoning detalhado
            reasoning = self._generate_reasoning(comparison_result)
            
            # Cria contexto histórico
            historical_context = {
                'pattern_match': comparison_result.historical_pattern_match,
                'trend_similarity': comparison_result.trend_similarity,
                'volatility_analysis': comparison_result.volatility_comparison,
                'support_resistance': comparison_result.support_resistance_levels,
                'similar_periods': comparison_result.similar_periods,
                'prediction': comparison_result.price_prediction
            }
            
            signal = TradingSignal(
                symbol=symbol,
                action=action,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                reasoning=reasoning,
                timestamp=datetime.now(),
                historical_context=historical_context
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinal de trading: {str(e)}")
            return None
    
    def _calculate_position_size(self, risk_assessment: Dict[str, Any], entry_price: float) -> float:
        """Calcula tamanho da posição baseado no risco"""
        try:
            # Usa recomendação do sistema de risco
            recommended_size = risk_assessment.get('recommended_position_size', 0.02)
            
            # Aplica limite máximo
            max_size = self.config['max_position_risk']
            position_size = min(recommended_size, max_size)
            
            # Ajusta baseado no nível de risco
            risk_level = risk_assessment.get('risk_level', 'médio')
            if risk_level == 'alto':
                position_size *= 0.5  # Reduz pela metade em risco alto
            elif risk_level == 'baixo':
                position_size *= 1.2  # Aumenta 20% em risco baixo
            
            return max(position_size, 0.001)  # Mínimo 0.1%
            
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return 0.01  # 1% padrão
    
    def _generate_reasoning(self, comparison_result: ComparisonResult) -> str:
        """Gera explicação detalhada para o sinal"""
        try:
            reasoning_parts = []
            
            # Análise de padrões
            pattern_score = comparison_result.historical_pattern_match
            if pattern_score > 0.7:
                reasoning_parts.append(f"Forte similaridade de padrão histórico ({pattern_score:.1%})")
            elif pattern_score < 0.3:
                reasoning_parts.append(f"Padrão histórico divergente ({pattern_score:.1%})")
            
            # Análise de tendência
            trend_score = comparison_result.trend_similarity
            if trend_score > 0.7:
                reasoning_parts.append("Tendência alinhada com histórico")
            elif trend_score < 0.3:
                reasoning_parts.append("Tendência diverge do histórico")
            
            # Análise de volatilidade
            vol_ratio = comparison_result.volatility_comparison.get('volatility_ratio', 1.0)
            if vol_ratio > 1.5:
                reasoning_parts.append("Volatilidade elevada vs histórico")
            elif vol_ratio < 0.7:
                reasoning_parts.append("Volatilidade baixa vs histórico")
            
            # Níveis de suporte/resistência
            nearest_support = comparison_result.support_resistance_levels.get('nearest_support')
            nearest_resistance = comparison_result.support_resistance_levels.get('nearest_resistance')
            
            if nearest_support:
                reasoning_parts.append(f"Suporte próximo em {nearest_support:.2f}")
            if nearest_resistance:
                reasoning_parts.append(f"Resistência próxima em {nearest_resistance:.2f}")
            
            # Previsão de preços
            prediction = comparison_result.price_prediction
            direction = prediction.get('direction', 'neutral')
            probability = prediction.get('up_probability', 0.5)
            
            if direction != 'neutral':
                reasoning_parts.append(f"Previsão: {direction} ({probability:.1%} probabilidade)")
            
            # Períodos similares
            similar_periods = comparison_result.similar_periods
            if similar_periods:
                positive_outcomes = sum(1 for p in similar_periods if p.get('outcome') == 'positive')
                reasoning_parts.append(f"{positive_outcomes}/{len(similar_periods)} períodos similares tiveram resultado positivo")
            
            return "; ".join(reasoning_parts) if reasoning_parts else "Análise inconclusiva"
            
        except Exception as e:
            logger.error(f"Erro ao gerar reasoning: {str(e)}")
            return "Análise baseada em dados históricos"
    
    async def _save_trading_signal(self, signal: TradingSignal) -> None:
        """Salva sinal de trading no banco"""
        try:
            signal_data = {
                'symbol': signal.symbol,
                'action': signal.action,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'position_size': signal.position_size,
                'reasoning': signal.reasoning,
                'timestamp': signal.timestamp.isoformat(),
                'historical_context': signal.historical_context
            }
            
            self.postgres_db.save_trading_signal(
                symbol=signal.symbol,
                signal_type=signal.action.lower(),
                strength=signal.confidence,
                price=signal.entry_price,
                source='historical_analysis',
                reasoning=signal.reasoning,
                indicators_data=signal_data
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar sinal de trading: {str(e)}")
    
    async def _send_signal_notification(
        self, 
        signal: TradingSignal, 
        comparison_result: ComparisonResult
    ) -> None:
        """Envia notificação do sinal via Telegram"""
        try:
            if not self.telegram:
                return
            
            # Emoji baseado na ação
            emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
            
            # Monta mensagem
            message = f"{emoji} **SINAL HISTÓRICO - {signal.symbol}**\n\n"
            message += f"**Ação:** {signal.action}\n"
            message += f"**Confiança:** {signal.confidence:.1%}\n"
            message += f"**Preço:** ${signal.entry_price:.4f}\n"
            
            if signal.stop_loss:
                message += f"**Stop Loss:** ${signal.stop_loss:.4f}\n"
            if signal.take_profit:
                message += f"**Take Profit:** ${signal.take_profit:.4f}\n"
            
            message += f"**Tamanho:** {signal.position_size:.1%} do capital\n\n"
            
            # Adiciona análise resumida
            pattern_match = comparison_result.historical_pattern_match
            trend_sim = comparison_result.trend_similarity
            
            message += f"**Análise Histórica:**\n"
            message += f"• Padrão: {pattern_match:.1%}\n"
            message += f"• Tendência: {trend_sim:.1%}\n"
            message += f"• Risco: {comparison_result.risk_assessment.get('risk_level', 'médio')}\n\n"
            
            message += f"**Motivo:** {signal.reasoning[:200]}..."
            
            await self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {str(e)}")
    
    async def execute_signal_if_enabled(self, signal: TradingSignal) -> bool:
        """
        Executa o sinal se trading automático estiver habilitado
        
        Args:
            signal: Sinal para executar
            
        Returns:
            True se executado com sucesso, False caso contrário
        """
        if not self.config['enable_auto_trading']:
            logger.info(f"Trading automático desabilitado. Sinal {signal.action} para {signal.symbol} não executado")
            return False
        
        try:
            logger.info(f"Executando sinal automático: {signal.action} {signal.symbol}")
            
            # Aqui você integraria com seu sistema de execução de trades
            # Por exemplo:
            # if signal.action == "BUY":
            #     return await self._execute_buy_order(signal)
            # elif signal.action == "SELL":
            #     return await self._execute_sell_order(signal)
            
            # Por enquanto, apenas simula
            logger.info(f"[SIMULAÇÃO] Executaria {signal.action} {signal.symbol} por ${signal.entry_price}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar sinal: {str(e)}")
            return False
    
    async def run_continuous_analysis(self, interval_minutes: int = 5) -> None:
        """
        Executa análise contínua em loop
        
        Args:
            interval_minutes: Intervalo entre análises em minutos
        """
        logger.info(f"Iniciando análise histórica contínua (intervalo: {interval_minutes}min)")
        
        while True:
            try:
                # Executa análise
                signals = await self.analyze_market_with_history()
                
                # Executa sinais se habilitado
                for symbol, signal in signals.items():
                    await self.execute_signal_if_enabled(signal)
                
                # Aguarda próximo ciclo
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("Análise contínua cancelada")
                break
            except Exception as e:
                logger.error(f"Erro na análise contínua: {str(e)}")
                await asyncio.sleep(30)  # Aguarda 30s antes de tentar novamente
    
    def get_active_signals(self) -> Dict[str, TradingSignal]:
        """Retorna sinais ativos"""
        # Filtra sinais das últimas 4 horas
        cutoff_time = datetime.now() - timedelta(hours=4)
        active_signals = {
            symbol: signal for symbol, signal in self.active_signals.items()
            if signal.timestamp > cutoff_time
        }
        return active_signals
    
    async def get_historical_performance(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtém performance histórica dos sinais
        
        Args:
            symbol: Símbolo para analisar
            days: Número de dias para análise
            
        Returns:
            Estatísticas de performance
        """
        try:
            # Busca sinais históricos do banco
            start_date = datetime.now() - timedelta(days=days)
            
            signals = self.postgres_db.get_trading_signals(
                symbol=symbol,
                executed=True
            )
            
            if not signals:
                return {'error': 'Nenhum sinal histórico encontrado'}
            
            # Analisa performance (implementação simplificada)
            total_signals = len(signals)
            positive_signals = sum(1 for s in signals if s.get('confidence', 0) > 0.7)
            
            performance = {
                'symbol': symbol,
                'period_days': days,
                'total_signals': total_signals,
                'high_confidence_signals': positive_signals,
                'success_rate': positive_signals / total_signals if total_signals > 0 else 0,
                'avg_confidence': sum(s.get('confidence', 0) for s in signals) / total_signals if total_signals > 0 else 0
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Erro ao obter performance histórica: {str(e)}")
            return {'error': str(e)}


# Função de conveniência para usar o sistema
async def start_historical_trading_analysis(
    symbols: List[str] = None,
    interval_minutes: int = 5,
    enable_auto_trading: bool = False
) -> None:
    """
    Inicia sistema de análise histórica para trading
    
    Args:
        symbols: Símbolos para monitorar
        interval_minutes: Intervalo entre análises
        enable_auto_trading: Se deve executar trades automaticamente
    """
    integration = HistoricalTradingIntegration()
    integration.config['enable_auto_trading'] = enable_auto_trading
    
    if symbols:
        integration.config['symbols_to_monitor'] = symbols
    
    await integration.run_continuous_analysis(interval_minutes)
