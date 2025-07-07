#!/usr/bin/env python3
"""
Estratégias de trading aprimoradas com integração do Sistema de Análise Inteligente
"""
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Imports com paths absolutos para evitar problemas de import relativo
import sys
from pathlib import Path

# Adiciona src ao path se necessário
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.utils import format_symbol
from src.analysis.symbol_analyzer import SymbolAnalyzer, analyze_symbol
from src.strategies.strategy import TradingStrategy, ScalpingStrategy, SwingTradingStrategy
from src.ai import LLMNewsAnalyzer, HybridPricePredictor, AdvancedPatternDetector

logger = logging.getLogger("robot-crypt")


class EnhancedTradingStrategy(TradingStrategy):
    """
    Estratégia base aprimorada com integração do Sistema de Análise Inteligente
    """
    
    def __init__(self, config, binance_api):
        """Inicializa a estratégia aprimorada"""
        super().__init__(config, binance_api)
        
        # Inicializa o analisador de símbolos
        try:
            self.symbol_analyzer = SymbolAnalyzer()
            self.analysis_enabled = True
            self.logger.info("Sistema de Análise Inteligente inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar Sistema de Análise: {str(e)}")
            self.symbol_analyzer = None
            self.analysis_enabled = False
        
        # Inicializa módulos de IA
        try:
            self.news_analyzer = LLMNewsAnalyzer()
            self.price_predictor = HybridPricePredictor()
            self.pattern_detector = AdvancedPatternDetector()
            # Importa NewsIntegrator
            from src.ai.news_integrator import NewsIntegrator
            self.news_integrator = NewsIntegrator()
            self.ai_enabled = True
            self.logger.info("Módulos de IA LLM inicializados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar módulos de IA: {str(e)}")
            self.news_analyzer = None
            self.price_predictor = None
            self.pattern_detector = None
            self.news_integrator = None
            self.ai_enabled = False
        
        # Configurações de análise
        self.analysis_config = {
            'min_confidence_threshold': 0.6,  # Confiança mínima para sinais (reduzido de 0.7)
            'timeframe': '1h',                # Timeframe padrão para análise
            'analysis_limit': 100,            # Número de candles para análise
            'use_ai_signals': True,           # Se deve usar sinais da IA
            'combine_with_traditional': True, # Se deve combinar com análise tradicional
            'risk_adjustment': True           # Se deve ajustar risco baseado na análise
        }
    
    def get_ai_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtém análise inteligente para o símbolo
        
        Args:
            symbol: Símbolo do par de trading
            
        Returns:
            Análise completa do símbolo ou None se erro
        """
        if not self.analysis_enabled or not self.symbol_analyzer:
            return None
        
        try:
            self.logger.info(f"Executando análise inteligente para {symbol}")
            
            # Executa análise completa
            analysis = self.symbol_analyzer.analyze_symbol(
                symbol=symbol,
                timeframe=self.analysis_config['timeframe'],
                limit=self.analysis_config['analysis_limit']
            )
            
            if analysis:
                self.logger.info(f"Análise de {symbol} concluída - {len(analysis.get('signals', []))} sinais encontrados")
                return analysis
            else:
                self.logger.warning(f"Análise de {symbol} retornou resultado vazio")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro na análise inteligente de {symbol}: {str(e)}")
            return None
    
    def extract_ai_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrai sinais relevantes da análise IA
        
        Args:
            analysis: Resultado da análise inteligente
            
        Returns:
            Lista de sinais filtrados por confiança
        """
        if not analysis or 'signals' not in analysis:
            return []
        
        try:
            signals = analysis['signals']
            
            # Filtra sinais por confiança mínima
            filtered_signals = [
                signal for signal in signals 
                if signal.get('confidence', 0) >= self.analysis_config['min_confidence_threshold']
            ]
            
            # Ordena por confiança (maior primeiro)
            filtered_signals.sort(key=lambda s: s.get('confidence', 0), reverse=True)
            
            return filtered_signals
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair sinais da análise: {str(e)}")
            return []
    
    def get_risk_assessment(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtém avaliação de risco da análise IA
        
        Args:
            analysis: Resultado da análise inteligente
            
        Returns:
            Avaliação de risco com recomendações
        """
        default_risk = {
            'overall_risk': 'medium',
            'risk_score': 0.5,
            'recommendations': ['Use gerenciamento de risco padrão']
        }
        
        if not analysis or 'risk_analysis' not in analysis:
            return default_risk
        
        try:
            return analysis['risk_analysis']
        except Exception as e:
            self.logger.error(f"Erro ao obter avaliação de risco: {str(e)}")
            return default_risk
    
    async def get_market_sentiment_context(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém contexto de sentimento do mercado para o símbolo
        
        Args:
            symbol: Símbolo para análise
            
        Returns:
            Contexto de sentimento do mercado
        """
        if not self.ai_enabled or not self.news_integrator:
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'confidence': 0.1}
        
        try:
            # Remove suffix if present (e.g., "BTCUSDT" -> "BTC")
            clean_symbol = symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
            if not clean_symbol:
                clean_symbol = symbol[:3]  # Fallback
            
            sentiment = await self.news_integrator.get_symbol_sentiment(clean_symbol)
            self.logger.info(f"Sentimento de mercado para {symbol}: {sentiment['sentiment_label']} "
                           f"(score: {sentiment['sentiment_score']:.2f}, confiaça: {sentiment['confidence']:.2f})")
            return sentiment
            
        except Exception as e:
            self.logger.error(f"Erro ao obter sentimento para {symbol}: {str(e)}")
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'confidence': 0.1}
    
    def adjust_position_size_for_risk(self, base_position_size: float, 
                                    risk_assessment: Dict[str, Any]) -> float:
        """
        Ajusta tamanho da posição baseado na avaliação de risco IA
        
        Args:
            base_position_size: Tamanho base da posição
            risk_assessment: Avaliação de risco da IA
            
        Returns:
            Tamanho ajustado da posição
        """
        if not self.analysis_config['risk_adjustment']:
            return base_position_size
        
        try:
            risk_score = risk_assessment.get('risk_score', 0.5)
            risk_level = risk_assessment.get('overall_risk', 'medium')
            
            # Fatores de ajuste baseados no risco
            risk_multipliers = {
                'low': 1.2,      # Aumenta posição em 20% para baixo risco
                'medium': 1.0,   # Mantém posição padrão
                'high': 0.6,     # Reduz posição em 40% para alto risco
                'unknown': 0.8   # Reduz posição em 20% para risco desconhecido
            }
            
            multiplier = risk_multipliers.get(risk_level, 1.0)
            
            # Ajuste adicional baseado no score numérico
            if risk_score > 0.8:
                multiplier *= 0.7  # Redução adicional para score muito alto
            elif risk_score < 0.3:
                multiplier *= 1.1  # Aumento adicional para score muito baixo
            
            adjusted_size = base_position_size * multiplier
            
            self.logger.info(f"Ajuste de posição: {base_position_size:.2f} -> {adjusted_size:.2f} "
                           f"(risco: {risk_level}, score: {risk_score:.2f}, mult: {multiplier:.2f})")
            
            return adjusted_size
            
        except Exception as e:
            self.logger.error(f"Erro ao ajustar posição para risco: {str(e)}")
            return base_position_size


class EnhancedScalpingStrategy(EnhancedTradingStrategy, ScalpingStrategy):
    """
    Estratégia de Scalping aprimorada com Sistema de Análise Inteligente
    
    Combina a estratégia tradicional de scalping com sinais da IA para:
    - Melhor timing de entrada e saída
    - Ajuste dinâmico de risco
    - Confirmação de sinais técnicos
    """
    
    def __init__(self, config, binance_api):
        """Inicializa estratégia de scalping aprimorada"""
        # Inicializa ambas as classes pai
        EnhancedTradingStrategy.__init__(self, config, binance_api)
        ScalpingStrategy.__init__(self, config, binance_api)
        
        # Configurações específicas do scalping com IA
        self.analysis_config.update({
            'timeframe': '15m',           # Timeframe mais curto para scalping
            'min_confidence_threshold': 0.65,  # Reduzido de 0.75 para 0.65
            'use_volume_analysis': True,  # Importante para scalping
            'use_volatility_analysis': True
        })
    
    def analyze_market(self, symbol, notifier=None):
        """
        Análise de mercado aprimorada combinando IA e análise tradicional
        
        Args:
            symbol: Símbolo do par de trading
            notifier: Notificador Telegram opcional
            
        Returns:
            Tuple: (should_trade, action, price)
        """
        try:
            # Executa análise tradicional primeiro
            traditional_result = super().analyze_market(symbol, notifier)
            should_trade_traditional, action_traditional, price_traditional = traditional_result
            
            # Se análise IA não estiver habilitada, usa apenas tradicional
            if not self.analysis_enabled:
                return traditional_result
            
            # Executa análise inteligente
            ai_analysis = self.get_ai_analysis(symbol)
            if not ai_analysis:
                self.logger.warning(f"Análise IA não disponível para {symbol}, usando apenas análise tradicional")
                return traditional_result
            
            # Extrai sinais da IA
            ai_signals = self.extract_ai_signals(ai_analysis)
            risk_assessment = self.get_risk_assessment(ai_analysis)
            
            # Combina resultados da análise tradicional e IA
            final_decision = self._combine_traditional_and_ai_analysis(
                traditional_result=traditional_result,
                ai_signals=ai_signals,
                risk_assessment=risk_assessment,
                ai_analysis=ai_analysis,
                symbol=symbol
            )
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Erro na análise de mercado aprimorada para {symbol}: {str(e)}")
            # Em caso de erro, retorna análise tradicional como fallback
            return super().analyze_market(symbol, notifier)
    
    def _combine_traditional_and_ai_analysis(self, traditional_result: Tuple, 
                                           ai_signals: List[Dict], 
                                           risk_assessment: Dict,
                                           ai_analysis: Dict,
                                           symbol: str) -> Tuple:
        """
        Combina análise tradicional com sinais da IA
        
        Args:
            traditional_result: Resultado da análise tradicional
            ai_signals: Sinais da análise IA
            risk_assessment: Avaliação de risco da IA
            symbol: Símbolo analisado
            
        Returns:
            Decisão final combinada
        """
        should_trade_traditional, action_traditional, price_traditional = traditional_result
        
        try:
            # Se não há sinais da IA, usa análise tradicional
            if not ai_signals:
                self.logger.info(f"[{symbol}]: Sem sinais IA válidos, usando análise tradicional")
                # Diagnóstico: vamos verificar se há sinais com confiança menor
                all_signals = ai_analysis.get('signals', [])
                if all_signals:
                    low_confidence_signals = [s for s in all_signals if s.confidence < self.analysis_config['min_confidence_threshold']]
                    if low_confidence_signals:
                        best_low = max(low_confidence_signals, key=lambda s: s.confidence)
                        self.logger.info(f"[{symbol}]: Melhor sinal de baixa confiança: {best_low.signal_type} ({best_low.confidence:.2%}) - {best_low.reasoning}")
                    else:
                        self.logger.info(f"[{symbol}]: Nenhum sinal gerado pela análise IA")
                else:
                    self.logger.info(f"[{symbol}]: Lista de sinais IA está vazia")
                return traditional_result
            
            # Pega o sinal de maior confiança da IA
            best_ai_signal = ai_signals[0]
            ai_action = best_ai_signal.get('signal_type', 'hold')
            ai_confidence = best_ai_signal.get('confidence', 0)
            ai_reasoning = best_ai_signal.get('reasoning', 'Não especificado')
            
            self.logger.info(f"{symbol}: Melhor sinal IA - {ai_action.upper()} "
                           f"(confiança: {ai_confidence:.2%}) - {ai_reasoning}")
            
            # Lógica de combinação
            if should_trade_traditional and ai_action != 'hold':
                # Ambos sugerem trading
                if action_traditional == ai_action:
                    # Concordam na direção - FORTE SINAL
                    self.logger.info(f"{symbol}: CONCORDÂNCIA - Tradicional e IA sugerem {ai_action.upper()}")
                    
                    # Verifica risco antes de confirmar
                    risk_level = risk_assessment.get('overall_risk', 'medium')
                    if risk_level == 'high':
                        self.logger.warning(f"{symbol}: Alto risco detectado, reduzindo confiança no sinal")
                        # Ainda executa, mas com menor posição (será ajustada no execute_buy/sell)
                    
                    return True, ai_action, price_traditional
                else:
                    # Discordam na direção - SINAL CONFLITANTE
                    self.logger.warning(f"{symbol}: CONFLITO - Tradicional sugere {action_traditional}, "
                                      f"IA sugere {ai_action}")
                    
                    # Decide baseado na confiança da IA
                    if ai_confidence > 0.85:
                        self.logger.info(f"{symbol}: IA tem alta confiança ({ai_confidence:.2%}), "
                                       f"seguindo sinal IA: {ai_action}")
                        return True, ai_action, price_traditional
                    else:
                        self.logger.info(f"{symbol}: Confiança IA moderada, não executando trade devido ao conflito")
                        return False, None, None
            
            elif should_trade_traditional and ai_action == 'hold':
                # Tradicional sugere trade, IA sugere aguardar
                self.logger.warning(f"{symbol}: Tradicional sugere {action_traditional}, mas IA sugere HOLD")
                
                # Verifica se é um risco muito alto
                if risk_assessment.get('overall_risk') == 'high':
                    self.logger.info(f"{symbol}: Alto risco confirmado pela IA, cancelando trade tradicional")
                    return False, None, None
                else:
                    # Risco baixo/médio - executa com posição reduzida
                    self.logger.info(f"{symbol}: Executando trade tradicional com cautela")
                    return True, action_traditional, price_traditional
            
            elif not should_trade_traditional and ai_action != 'hold':
                # Tradicional não sugere trade, mas IA sugere
                self.logger.info(f"{symbol}: IA sugere {ai_action} mas análise tradicional não confirma")
                
                # Só executa se IA tem confiança muito alta E risco é baixo
                if ai_confidence > 0.9 and risk_assessment.get('overall_risk') == 'low':
                    self.logger.info(f"{symbol}: IA tem confiança muito alta ({ai_confidence:.2%}) "
                                   f"e risco baixo, executando sinal IA")
                    return True, ai_action, price_traditional
                else:
                    self.logger.info(f"{symbol}: Confiança/risco insuficiente para sinal IA isolado")
                    return False, None, None
            
            else:
                # Ambos não sugerem trade
                return False, None, None
            
        except Exception as e:
            self.logger.error(f"Erro ao combinar análises para {symbol}: {str(e)}")
            return traditional_result
    
    def execute_buy(self, symbol, price):
        """
        Executa compra com ajuste de risco baseado na análise IA
        """
        try:
            # Obtém análise IA para ajuste de risco
            ai_analysis = self.get_ai_analysis(symbol)
            if ai_analysis:
                risk_assessment = self.get_risk_assessment(ai_analysis)
                
                # Calcula posição base usando método tradicional
                account_info = self.binance.get_account_info()
                capital = self.config.get_balance(account_info)
                risk_per_trade = self.config.scalping['risk_per_trade']
                base_position_value = capital * risk_per_trade
                
                # Ajusta posição baseado no risco IA
                adjusted_position_value = self.adjust_position_size_for_risk(
                    base_position_value, risk_assessment
                )
                
                # Substitui temporariamente a configuração de risco
                original_risk = self.config.scalping['risk_per_trade']
                self.config.scalping['risk_per_trade'] = adjusted_position_value / capital
                
                try:
                    # Executa compra com risco ajustado
                    result = super().execute_buy(symbol, price)
                    
                    # Log do ajuste aplicado
                    if result[0]:  # Se sucesso
                        adjustment_ratio = adjusted_position_value / base_position_value
                        self.logger.info(f"Compra de {symbol} executada com ajuste de risco IA: "
                                       f"{adjustment_ratio:.2f}x da posição base")
                    
                    return result
                finally:
                    # Restaura configuração original
                    self.config.scalping['risk_per_trade'] = original_risk
            else:
                # Sem análise IA, executa compra tradicional
                return super().execute_buy(symbol, price)
                
        except Exception as e:
            self.logger.error(f"Erro na execução de compra aprimorada para {symbol}: {str(e)}")
            return super().execute_buy(symbol, price)


class EnhancedSwingTradingStrategy(EnhancedTradingStrategy, SwingTradingStrategy):
    """
    Estratégia de Swing Trading aprimorada com Sistema de Análise Inteligente
    
    Combina análise de volume e novas listagens com sinais avançados da IA:
    - Análise de padrões de preço
    - Avaliação de oportunidades
    - Timing otimizado de entrada/saída
    """
    
    def __init__(self, config, binance_api):
        """Inicializa estratégia de swing trading aprimorada"""
        # Inicializa ambas as classes pai
        EnhancedTradingStrategy.__init__(self, config, binance_api)
        SwingTradingStrategy.__init__(self, config, binance_api)
        
        # Configurações específicas do swing trading com IA
        self.analysis_config.update({
            'timeframe': '4h',            # Timeframe maior para swing trading
            'min_confidence_threshold': 0.65,  # Confiança moderada para swing
            'use_pattern_analysis': True, # Importante para swing trading
            'use_opportunity_analysis': True,
            'analysis_limit': 200        # Mais dados para análise de médio prazo
        })
    
    def analyze_market(self, symbol, notifier=None):
        """
        Análise de mercado aprimorada para swing trading
        
        Combina análise de volume tradicional com análise avançada da IA
        """
        try:
            # Executa análise tradicional
            traditional_result = super().analyze_market(symbol, notifier)
            should_trade_traditional, action_traditional, price_traditional = traditional_result
            
            # Se análise IA não estiver habilitada, usa apenas tradicional
            if not self.analysis_enabled:
                return traditional_result
            
            # Executa análise inteligente
            ai_analysis = self.get_ai_analysis(symbol)
            if not ai_analysis:
                return traditional_result
            
            # Extrai informações específicas para swing trading
            ai_signals = self.extract_ai_signals(ai_analysis)
            opportunity_analysis = ai_analysis.get('opportunity_analysis', {})
            risk_assessment = self.get_risk_assessment(ai_analysis)
            
            # Análise específica de padrões
            pattern_signals = self._analyze_ai_patterns(ai_analysis, symbol)
            
            # Combina todas as análises
            final_decision = self._combine_swing_analysis(
                traditional_result=traditional_result,
                ai_signals=ai_signals,
                opportunity_analysis=opportunity_analysis,
                risk_assessment=risk_assessment,
                pattern_signals=pattern_signals,
                symbol=symbol
            )
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Erro na análise swing aprimorada para {symbol}: {str(e)}")
            return super().analyze_market(symbol, notifier)
    
    def _analyze_ai_patterns(self, ai_analysis: Dict, symbol: str) -> List[Dict]:
        """
        Analisa padrões identificados pela IA
        
        Args:
            ai_analysis: Análise completa da IA
            symbol: Símbolo analisado
            
        Returns:
            Lista de sinais baseados em padrões
        """
        try:
            pattern_data = ai_analysis.get('market_data', {}).get('pattern_analysis', {})
            patterns = pattern_data.get('patterns', [])
            
            pattern_signals = []
            
            for pattern in patterns:
                if pattern.get('confidence', 0) >= 0.7:
                    signal_type = 'buy' if pattern.get('signal') == 'bullish' else 'sell' if pattern.get('signal') == 'bearish' else 'hold'
                    
                    pattern_signals.append({
                        'signal_type': signal_type,
                        'confidence': pattern.get('confidence', 0),
                        'source': 'pattern_analysis',
                        'reasoning': f"Padrão {pattern.get('name', 'desconhecido')}: {pattern.get('description', '')}"
                    })
            
            if pattern_signals:
                self.logger.info(f"{symbol}: {len(pattern_signals)} padrões identificados pela IA")
            
            return pattern_signals
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar padrões IA para {symbol}: {str(e)}")
            return []
    
    def _combine_swing_analysis(self, traditional_result: Tuple, ai_signals: List[Dict],
                              opportunity_analysis: Dict, risk_assessment: Dict,
                              pattern_signals: List[Dict], symbol: str) -> Tuple:
        """
        Combina todas as análises para swing trading
        """
        should_trade_traditional, action_traditional, price_traditional = traditional_result
        
        try:
            # Análise de oportunidade
            opportunity_score = opportunity_analysis.get('opportunity_score', 0.5)
            opportunity_level = opportunity_analysis.get('overall_opportunity', 'medium')
            
            self.logger.info(f"{symbol}: Oportunidade IA - {opportunity_level} "
                           f"(score: {opportunity_score:.2f})")
            
            # Se análise tradicional sugere trade
            if should_trade_traditional:
                # Verifica se IA confirma a oportunidade
                if opportunity_score >= 0.7:
                    self.logger.info(f"{symbol}: Alta oportunidade confirmada pela IA, "
                                   f"executando trade tradicional")
                    return traditional_result
                elif opportunity_score >= 0.4:
                    # Oportunidade moderada - verifica sinais adicionais
                    confirming_signals = [s for s in ai_signals if s.get('signal_type') == action_traditional]
                    if confirming_signals:
                        best_confirming = max(confirming_signals, key=lambda s: s.get('confidence', 0))
                        self.logger.info(f"{symbol}: Oportunidade moderada com confirmação IA "
                                       f"({best_confirming.get('confidence', 0):.2%})")
                        return traditional_result
                    else:
                        self.logger.warning(f"{symbol}: Oportunidade moderada sem confirmação IA")
                        return False, None, None
                else:
                    self.logger.warning(f"{symbol}: Baixa oportunidade detectada pela IA, "
                                      f"cancelando trade tradicional")
                    return False, None, None
            
            # Se análise tradicional não sugere trade, verifica se IA encontrou oportunidade
            else:
                if opportunity_score >= 0.8 and ai_signals:
                    best_ai_signal = max(ai_signals, key=lambda s: s.get('confidence', 0))
                    if best_ai_signal.get('confidence', 0) >= 0.8:
                        self.logger.info(f"{symbol}: Alta oportunidade e confiança IA, "
                                       f"executando sinal IA: {best_ai_signal.get('signal_type')}")
                        return True, best_ai_signal.get('signal_type'), price_traditional
                
                # Verifica padrões fortes
                strong_patterns = [p for p in pattern_signals if p.get('confidence', 0) >= 0.8]
                if strong_patterns and opportunity_score >= 0.6:
                    best_pattern = max(strong_patterns, key=lambda p: p.get('confidence', 0))
                    self.logger.info(f"{symbol}: Padrão forte detectado: {best_pattern.get('reasoning')}")
                    return True, best_pattern.get('signal_type'), price_traditional
            
            return False, None, None
            
        except Exception as e:
            self.logger.error(f"Erro ao combinar análises swing para {symbol}: {str(e)}")
            return traditional_result
    
    def execute_buy(self, symbol, price):
        """
        Executa compra para swing trading com ajuste IA
        """
        try:
            # Obtém análise IA para ajuste
            ai_analysis = self.get_ai_analysis(symbol)
            if ai_analysis:
                risk_assessment = self.get_risk_assessment(ai_analysis)
                opportunity_analysis = ai_analysis.get('opportunity_analysis', {})
                
                # Calcula posição base
                account_info = self.binance.get_account_info()
                capital = self.config.get_balance(account_info)
                base_position_value = capital * self.config.swing_trading['max_position_size']
                
                # Ajusta posição baseado em risco E oportunidade
                risk_adjusted_value = self.adjust_position_size_for_risk(
                    base_position_value, risk_assessment
                )
                
                # Ajuste adicional baseado na oportunidade
                opportunity_score = opportunity_analysis.get('opportunity_score', 0.5)
                opportunity_multiplier = 0.8 + (opportunity_score * 0.4)  # 0.8 a 1.2
                
                final_position_value = risk_adjusted_value * opportunity_multiplier
                
                # Substitui temporariamente a configuração
                original_size = self.config.swing_trading['max_position_size']
                self.config.swing_trading['max_position_size'] = final_position_value / capital
                
                try:
                    result = super().execute_buy(symbol, price)
                    
                    if result[0]:  # Se sucesso
                        total_adjustment = final_position_value / base_position_value
                        self.logger.info(f"Compra swing de {symbol} com ajuste IA total: "
                                       f"{total_adjustment:.2f}x (risco + oportunidade)")
                    
                    return result
                finally:
                    # Restaura configuração
                    self.config.swing_trading['max_position_size'] = original_size
            else:
                return super().execute_buy(symbol, price)
                
        except Exception as e:
            self.logger.error(f"Erro na execução swing aprimorada para {symbol}: {str(e)}")
            return super().execute_buy(symbol, price)


# Função factory para criar estratégias aprimoradas
def create_enhanced_strategy(strategy_type: str, config, binance_api):
    """
    Cria instância da estratégia aprimorada baseada no tipo
    
    Args:
        strategy_type: 'scalping' ou 'swing'
        config: Configuração do bot
        binance_api: API da Binance
        
    Returns:
        Instância da estratégia aprimorada
    """
    try:
        if strategy_type.lower() == 'scalping':
            return EnhancedScalpingStrategy(config, binance_api)
        elif strategy_type.lower() == 'swing':
            return EnhancedSwingTradingStrategy(config, binance_api)
        else:
            raise ValueError(f"Tipo de estratégia desconhecido: {strategy_type}")
    except Exception as e:
        logger.error(f"Erro ao criar estratégia aprimorada {strategy_type}: {str(e)}")
        # Fallback para estratégias tradicionais
        if strategy_type.lower() == 'scalping':
            return ScalpingStrategy(config, binance_api)
        else:
            return SwingTradingStrategy(config, binance_api)
