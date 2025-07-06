#!/usr/bin/env python3
"""
Sistema de Análise Inteligente de Símbolos
Implementa análise de dados de mercado, geração de sinais e predições usando ML
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
from dataclasses import dataclass, asdict

from src.database.postgres_manager import PostgresManager
from src.analysis.technical_indicators import TechnicalIndicators
# from src.api.external.binance_client import BinanceClient

logger = logging.getLogger("robot-crypt")


class BinanceClient:
    """Cliente simples da Binance para buscar dados de mercado"""
    
    def __init__(self):
        self.logger = logging.getLogger("robot-crypt.binance_client")
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """
        Simula busca de dados de klines da Binance
        Em uma implementação real, faria chamada para a API
        """
        self.logger.warning(f"BinanceClient mock - dados não disponíveis para {symbol}")
        return []


@dataclass
class TradingSignal:
    """Estrutura de dados para sinais de trading"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 a 1.0
    confidence: float  # 0.0 a 1.0
    price: float
    timestamp: datetime
    reasoning: str
    indicators_data: Dict[str, Any]
    source: str = 'symbol_analyzer'


@dataclass
class MarketAnalysis:
    """Estrutura de dados para análise de mercado"""
    symbol: str
    analysis_type: str
    trend: str
    trend_strength: float
    volatility: float
    volume_profile: Dict[str, Any]
    support_levels: List[float]
    resistance_levels: List[float]
    risk_score: float
    opportunity_score: float
    timestamp: datetime
    additional_data: Dict[str, Any]


class SymbolAnalyzer:
    """
    Classe principal para análise inteligente de símbolos
    Integra análise técnica, machine learning e geração de sinais
    """

    def __init__(self, postgres_manager: PostgresManager = None, binance_client: BinanceClient = None):
        """
        Inicializa o analisador de símbolos
        
        Args:
            postgres_manager: Instância do gerenciador PostgreSQL
            binance_client: Cliente da API da Binance
        """
        self.logger = logging.getLogger("robot-crypt.symbol_analyzer")
        self.db = postgres_manager or PostgresManager()
        self.binance = binance_client or BinanceClient()
        self.technical = TechnicalIndicators()
        
        # Configurações de análise
        self.config = {
            'default_limit': 100,
            'min_confidence_threshold': 0.6,
            'signal_expiry_minutes': 15,
            'volatility_window': 20,
            'volume_threshold_multiplier': 1.5
        }

    def analyze_symbol(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict[str, Any]:
        """
        Função principal de análise de símbolo
        
        Args:
            symbol: Símbolo do par de trading (ex: 'BTCUSDT')
            timeframe: Timeframe para análise (ex: '1h', '15m', '1d')
            limit: Número de candles para análise
            
        Returns:
            Dict com análise completa do símbolo
        """
        try:
            self.logger.info(f"Iniciando análise completa para {symbol} ({timeframe})")
            
            # 1. Buscar dados de mercado
            market_data = self.fetch_market_data(symbol, timeframe, limit)
            if not market_data:
                self.logger.error(f"Não foi possível obter dados de mercado para {symbol}")
                return {}
            
            # 2. Processar dados e calcular indicadores
            processed_data = self.process_data(market_data)
            if not processed_data:
                self.logger.error(f"Erro no processamento de dados para {symbol}")
                return {}
            
            # 3. Gerar sinais de trading
            signals = self.generate_signals(symbol, processed_data)
            
            # 4. Realizar análise de risco
            risk_analysis = self.analyze_risk(symbol, processed_data)
            
            # 5. Calcular scores de oportunidade
            opportunity_analysis = self.analyze_opportunity(symbol, processed_data)
            
            # 6. Consolidar análise
            complete_analysis = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'market_data': processed_data,
                'signals': signals,
                'risk_analysis': risk_analysis,
                'opportunity_analysis': opportunity_analysis,
                'summary': self._create_analysis_summary(processed_data, signals, risk_analysis, opportunity_analysis)
            }
            
            # 7. Registrar análise no banco de dados
            self.record_analysis(symbol, complete_analysis)
            
            # 8. Registrar sinais no banco de dados
            for signal in signals:
                self.record_signals([signal])
            
            self.logger.info(f"Análise completa de {symbol} finalizada com {len(signals)} sinais gerados")
            return complete_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de {symbol}: {str(e)}")
            return {}

    def fetch_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Busca dados de mercado do banco de dados ou API
        
        Args:
            symbol: Símbolo do par
            timeframe: Timeframe dos dados
            limit: Quantidade de dados
            
        Returns:
            Lista de dados OHLCV
        """
        try:
            # Primeiro tenta buscar do banco de dados
            db_data = self.db.get_price_history(symbol, timeframe, limit)
            
            if db_data and len(db_data) >= limit * 0.8:  # Se temos pelo menos 80% dos dados
                self.logger.info(f"Dados obtidos do banco: {len(db_data)} registros para {symbol}")
                return db_data
            
            # Se não temos dados suficientes, busca da API
            self.logger.info(f"Buscando dados da API da Binance para {symbol}")
            api_data = self.binance.get_klines(symbol, timeframe, limit)
            
            if api_data:
                # Salva os dados no banco para uso futuro
                self.db.save_price_history_batch(symbol, api_data, timeframe)
                return api_data
            
            return []
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados de mercado para {symbol}: {str(e)}")
            return []

    def process_data(self, market_data: List[Dict]) -> Dict[str, Any]:
        """
        Processa dados de mercado e calcula indicadores técnicos
        
        Args:
            market_data: Lista de dados OHLCV
            
        Returns:
            Dados processados com indicadores
        """
        try:
            if not market_data:
                return {}
            
            # Converte dados para formato de klines para análise técnica
            klines = []
            for data in market_data:
                kline = [
                    int(data['open_time'].timestamp() * 1000) if hasattr(data['open_time'], 'timestamp') else data['open_time'],
                    str(data['open']),
                    str(data['high']),
                    str(data['low']),
                    str(data['close']),
                    str(data['volume'])
                ]
                klines.append(kline)
            
            # Calcula todos os indicadores técnicos
            technical_analysis = self.technical.calculate_all_indicators(klines)
            
            if not technical_analysis:
                self.logger.warning("Não foi possível calcular indicadores técnicos")
                return {}
            
            # Adiciona análises adicionais
            df = pd.DataFrame(market_data)
            
            # Análise de volatilidade
            volatility_analysis = self._analyze_volatility(df)
            
            # Análise de volume
            volume_analysis = self._analyze_volume(df)
            
            # Análise de padrões de preço
            pattern_analysis = self._analyze_price_patterns(df)
            
            processed_data = {
                'raw_data': market_data,
                'technical_indicators': technical_analysis,
                'volatility_analysis': volatility_analysis,
                'volume_analysis': volume_analysis,
                'pattern_analysis': pattern_analysis,
                'data_quality': {
                    'completeness': len(market_data) / self.config['default_limit'],
                    'latest_timestamp': market_data[-1]['open_time'] if market_data else None,
                    'data_span_hours': self._calculate_data_span(market_data)
                }
            }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de dados: {str(e)}")
            return {}

    def generate_signals(self, symbol: str, processed_data: Dict[str, Any]) -> List[TradingSignal]:
        """
        Gera sinais de trading baseados na análise
        
        Args:
            symbol: Símbolo do par
            processed_data: Dados processados com indicadores
            
        Returns:
            Lista de sinais de trading
        """
        try:
            signals = []
            
            if not processed_data or 'technical_indicators' not in processed_data:
                return signals
            
            tech_data = processed_data['technical_indicators']
            current_price = tech_data['price']['close']
            
            # Análise baseada em indicadores técnicos
            technical_signals = self._generate_technical_signals(symbol, tech_data, current_price)
            signals.extend(technical_signals)
            
            # Análise baseada em volume
            volume_signals = self._generate_volume_signals(symbol, processed_data, current_price)
            signals.extend(volume_signals)
            
            # Análise baseada em volatilidade
            volatility_signals = self._generate_volatility_signals(symbol, processed_data, current_price)
            signals.extend(volatility_signals)
            
            # Análise baseada em padrões
            pattern_signals = self._generate_pattern_signals(symbol, processed_data, current_price)
            signals.extend(pattern_signals)
            
            # Filtra sinais por confiança mínima
            filtered_signals = [s for s in signals if s.confidence >= self.config['min_confidence_threshold']]
            
            # Consolida sinais similares
            consolidated_signals = self._consolidate_signals(filtered_signals)
            
            return consolidated_signals
            
        except Exception as e:
            self.logger.error(f"Erro na geração de sinais para {symbol}: {str(e)}")
            return []

    def _generate_technical_signals(self, symbol: str, tech_data: Dict, current_price: float) -> List[TradingSignal]:
        """Gera sinais baseados em indicadores técnicos"""
        signals = []
        
        try:
            indicators = tech_data['indicators']
            tech_signals = tech_data['technical_signals']
            
            # Sinal baseado em RSI
            if indicators['rsi']['oversold'] and indicators['rsi']['crossed_up_30']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='buy',
                    strength=0.8,
                    confidence=0.75,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="RSI saindo de área de sobrevenda (< 30)",
                    indicators_data={'rsi': indicators['rsi']},
                    source='technical_rsi'
                )
                signals.append(signal)
            
            elif indicators['rsi']['overbought'] and indicators['rsi']['crossed_down_70']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='sell',
                    strength=0.8,
                    confidence=0.75,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="RSI saindo de área de sobrecompra (> 70)",
                    indicators_data={'rsi': indicators['rsi']},
                    source='technical_rsi'
                )
                signals.append(signal)
            
            # Sinal baseado em MACD
            if indicators['macd']['crossed_up']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='buy',
                    strength=0.7,
                    confidence=0.70,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="MACD cruzou acima da linha de sinal",
                    indicators_data={'macd': indicators['macd']},
                    source='technical_macd'
                )
                signals.append(signal)
            
            elif indicators['macd']['crossed_down']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='sell',
                    strength=0.7,
                    confidence=0.70,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="MACD cruzou abaixo da linha de sinal",
                    indicators_data={'macd': indicators['macd']},
                    source='technical_macd'
                )
                signals.append(signal)
            
            # Sinal baseado em Bandas de Bollinger
            if indicators['bollinger_bands']['below_lower']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='buy',
                    strength=0.6,
                    confidence=0.65,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="Preço abaixo da banda inferior de Bollinger",
                    indicators_data={'bollinger': indicators['bollinger_bands']},
                    source='technical_bollinger'
                )
                signals.append(signal)
            
            elif indicators['bollinger_bands']['above_upper']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='sell',
                    strength=0.6,
                    confidence=0.65,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="Preço acima da banda superior de Bollinger",
                    indicators_data={'bollinger': indicators['bollinger_bands']},
                    source='technical_bollinger'
                )
                signals.append(signal)
            
            # Sinal baseado em cruzamento de médias móveis
            if indicators['moving_averages']['ema_9_crossed_up_ema_21']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='buy',
                    strength=0.75,
                    confidence=0.70,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="EMA 9 cruzou acima da EMA 21",
                    indicators_data={'ma': indicators['moving_averages']},
                    source='technical_ma_cross'
                )
                signals.append(signal)
            
            elif indicators['moving_averages']['ema_9_crossed_down_ema_21']:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='sell',
                    strength=0.75,
                    confidence=0.70,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="EMA 9 cruzou abaixo da EMA 21",
                    indicators_data={'ma': indicators['moving_averages']},
                    source='technical_ma_cross'
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais técnicos: {str(e)}")
            return []

    def _generate_volume_signals(self, symbol: str, processed_data: Dict, current_price: float) -> List[TradingSignal]:
        """Gera sinais baseados em análise de volume"""
        signals = []
        
        try:
            volume_analysis = processed_data.get('volume_analysis', {})
            
            if volume_analysis.get('volume_spike', False):
                # Volume anormalmente alto pode indicar movimento forte
                signal_type = 'buy' if volume_analysis.get('price_trend', 'neutral') == 'up' else 'sell'
                
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=0.6,
                    confidence=0.65,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning=f"Pico de volume detectado com tendência {volume_analysis.get('price_trend', 'neutral')}",
                    indicators_data={'volume': volume_analysis},
                    source='volume_spike'
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais de volume: {str(e)}")
            return []

    def _generate_volatility_signals(self, symbol: str, processed_data: Dict, current_price: float) -> List[TradingSignal]:
        """Gera sinais baseados em análise de volatilidade"""
        signals = []
        
        try:
            volatility_analysis = processed_data.get('volatility_analysis', {})
            
            # Baixa volatilidade pode indicar movimento iminente
            if volatility_analysis.get('volatility_level', 'normal') == 'low':
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type='hold',
                    strength=0.5,
                    confidence=0.60,
                    price=current_price,
                    timestamp=datetime.now(),
                    reasoning="Baixa volatilidade detectada - aguardar breakout",
                    indicators_data={'volatility': volatility_analysis},
                    source='volatility_low'
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais de volatilidade: {str(e)}")
            return []

    def _generate_pattern_signals(self, symbol: str, processed_data: Dict, current_price: float) -> List[TradingSignal]:
        """Gera sinais baseados em padrões de preço"""
        signals = []
        
        try:
            pattern_analysis = processed_data.get('pattern_analysis', {})
            
            # Verifica padrões identificados
            for pattern in pattern_analysis.get('patterns', []):
                if pattern['confidence'] >= 0.7:
                    signal_type = 'buy' if pattern['signal'] == 'bullish' else 'sell'
                    
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=pattern['confidence'],
                        confidence=pattern['confidence'],
                        price=current_price,
                        timestamp=datetime.now(),
                        reasoning=f"Padrão {pattern['name']} detectado",
                        indicators_data={'pattern': pattern},
                        source='pattern_recognition'
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais de padrões: {str(e)}")
            return []

    def _consolidate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Consolida sinais similares para evitar redundância"""
        try:
            if not signals:
                return signals
            
            consolidated = []
            signal_groups = {'buy': [], 'sell': [], 'hold': []}
            
            # Agrupa sinais por tipo
            for signal in signals:
                signal_groups[signal.signal_type].append(signal)
            
            # Para cada tipo, consolida em um sinal mais forte
            for signal_type, group in signal_groups.items():
                if not group:
                    continue
                
                if len(group) == 1:
                    consolidated.append(group[0])
                else:
                    # Cria sinal consolidado com maior confiança
                    best_signal = max(group, key=lambda s: s.confidence)
                    avg_strength = sum(s.strength for s in group) / len(group)
                    avg_confidence = sum(s.confidence for s in group) / len(group)
                    
                    reasoning_parts = [s.reasoning for s in group]
                    combined_reasoning = f"Múltiplos sinais: {'; '.join(reasoning_parts)}"
                    
                    consolidated_signal = TradingSignal(
                        symbol=best_signal.symbol,
                        signal_type=signal_type,
                        strength=min(avg_strength, 1.0),
                        confidence=min(avg_confidence * 1.1, 1.0),  # Bônus por múltiplos sinais
                        price=best_signal.price,
                        timestamp=best_signal.timestamp,
                        reasoning=combined_reasoning,
                        indicators_data={'consolidated': [s.indicators_data for s in group]},
                        source='consolidated'
                    )
                    consolidated.append(consolidated_signal)
            
            return consolidated
            
        except Exception as e:
            self.logger.error(f"Erro ao consolidar sinais: {str(e)}")
            return signals

    def analyze_risk(self, symbol: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa riscos associados ao símbolo
        
        Args:
            symbol: Símbolo do par
            processed_data: Dados processados
            
        Returns:
            Análise de risco
        """
        try:
            risk_analysis = {
                'overall_risk': 'medium',
                'risk_score': 0.5,  # 0 = baixo risco, 1 = alto risco
                'factors': [],
                'recommendations': []
            }
            
            if not processed_data:
                risk_analysis['overall_risk'] = 'unknown'
                risk_analysis['risk_score'] = 0.8
                return risk_analysis
            
            risk_factors = []
            
            # Análise de volatilidade
            volatility = processed_data.get('volatility_analysis', {})
            if volatility.get('volatility_level') == 'high':
                risk_factors.append({
                    'factor': 'high_volatility',
                    'weight': 0.3,
                    'description': 'Alta volatilidade detectada'
                })
            
            # Análise de volume
            volume = processed_data.get('volume_analysis', {})
            if volume.get('volume_trend') == 'decreasing':
                risk_factors.append({
                    'factor': 'decreasing_volume',
                    'weight': 0.2,
                    'description': 'Volume em queda'
                })
            
            # Análise técnica
            tech_data = processed_data.get('technical_indicators', {})
            if tech_data:
                rsi = tech_data.get('indicators', {}).get('rsi', {})
                if rsi.get('overbought') or rsi.get('oversold'):
                    risk_factors.append({
                        'factor': 'extreme_rsi',
                        'weight': 0.25,
                        'description': 'RSI em zona extrema'
                    })
            
            # Calcula score de risco
            total_risk = sum(factor['weight'] for factor in risk_factors)
            risk_analysis['risk_score'] = min(total_risk, 1.0)
            risk_analysis['factors'] = risk_factors
            
            # Determina nível de risco
            if risk_analysis['risk_score'] < 0.3:
                risk_analysis['overall_risk'] = 'low'
                risk_analysis['recommendations'].append('Risco baixo - condições favoráveis para trading')
            elif risk_analysis['risk_score'] < 0.7:
                risk_analysis['overall_risk'] = 'medium'
                risk_analysis['recommendations'].append('Risco médio - usar stop-loss e take-profit')
            else:
                risk_analysis['overall_risk'] = 'high'
                risk_analysis['recommendations'].append('Risco alto - considere reduzir posição ou aguardar')
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de risco para {symbol}: {str(e)}")
            return {'overall_risk': 'unknown', 'risk_score': 0.8, 'factors': [], 'recommendations': []}

    def analyze_opportunity(self, symbol: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa oportunidades de trading
        
        Args:
            symbol: Símbolo do par
            processed_data: Dados processados
            
        Returns:
            Análise de oportunidades
        """
        try:
            opportunity_analysis = {
                'overall_opportunity': 'medium',
                'opportunity_score': 0.5,  # 0 = baixa oportunidade, 1 = alta oportunidade
                'factors': [],
                'entry_points': [],
                'target_levels': []
            }
            
            if not processed_data:
                return opportunity_analysis
            
            opportunity_factors = []
            
            # Verifica sinais técnicos positivos
            tech_data = processed_data.get('technical_indicators', {})
            if tech_data:
                signals = tech_data.get('technical_signals', {})
                buy_signals = len(signals.get('buy_signals', []))
                sell_signals = len(signals.get('sell_signals', []))
                
                if buy_signals > sell_signals:
                    opportunity_factors.append({
                        'factor': 'bullish_signals',
                        'weight': 0.4,
                        'description': f'{buy_signals} sinais de compra vs {sell_signals} de venda'
                    })
                
                # Verifica tendência forte
                trend_strength = abs(signals.get('trend_strength', 0))
                if trend_strength > 0.6:
                    opportunity_factors.append({
                        'factor': 'strong_trend',
                        'weight': 0.3,
                        'description': f'Tendência forte detectada ({trend_strength:.2f})'
                    })
            
            # Verifica padrões favoráveis
            patterns = processed_data.get('pattern_analysis', {}).get('patterns', [])
            high_confidence_patterns = [p for p in patterns if p.get('confidence', 0) > 0.7]
            if high_confidence_patterns:
                opportunity_factors.append({
                    'factor': 'favorable_patterns',
                    'weight': 0.3,
                    'description': f'{len(high_confidence_patterns)} padrões favoráveis'
                })
            
            # Calcula score de oportunidade
            total_opportunity = sum(factor['weight'] for factor in opportunity_factors)
            opportunity_analysis['opportunity_score'] = min(total_opportunity, 1.0)
            opportunity_analysis['factors'] = opportunity_factors
            
            # Determina nível de oportunidade
            if opportunity_analysis['opportunity_score'] > 0.7:
                opportunity_analysis['overall_opportunity'] = 'high'
            elif opportunity_analysis['opportunity_score'] > 0.4:
                opportunity_analysis['overall_opportunity'] = 'medium'
            else:
                opportunity_analysis['overall_opportunity'] = 'low'
            
            return opportunity_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de oportunidade para {symbol}: {str(e)}")
            return {'overall_opportunity': 'unknown', 'opportunity_score': 0.3, 'factors': [], 'entry_points': [], 'target_levels': []}

    def record_signals(self, signals: List[TradingSignal]) -> bool:
        """
        Registra sinais no banco de dados
        
        Args:
            signals: Lista de sinais para registrar
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if not signals:
                return True
            
            for signal in signals:
                # Converte TradingSignal para formato do banco
                indicators_data = signal.indicators_data.copy()
                indicators_data['strength'] = signal.strength
                indicators_data['source'] = signal.source
                
                signal_id = self.db.save_trading_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type,
                    strength=signal.strength,
                    price=signal.price,
                    source=signal.source,
                    reasoning=signal.reasoning,
                    indicators_data=indicators_data
                )
                
                if signal_id:
                    self.logger.debug(f"Sinal {signal.signal_type} para {signal.symbol} registrado (ID: {signal_id})")
                else:
                    self.logger.warning(f"Falha ao registrar sinal {signal.signal_type} para {signal.symbol}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar sinais: {str(e)}")
            return False

    def record_analysis(self, symbol: str, analysis: Dict[str, Any]) -> bool:
        """
        Registra análise completa no banco de dados
        
        Args:
            symbol: Símbolo analisado
            analysis: Dados da análise
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Converte datetime objects para strings para serialização
            def convert_datetime_to_string(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {key: convert_datetime_to_string(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime_to_string(item) for item in obj]
                else:
                    return obj
            
            serializable_analysis = convert_datetime_to_string(analysis)
            
            analysis_id = self.db.save_analysis(
                symbol=symbol,
                analysis_type='complete_technical_analysis',
                data=serializable_analysis
            )
            
            if analysis_id:
                self.logger.info(f"Análise de {symbol} registrada no banco (ID: {analysis_id})")
                return True
            else:
                self.logger.warning(f"Falha ao registrar análise de {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao registrar análise de {symbol}: {str(e)}")
            return False

    # Métodos auxiliares para análises específicas

    def _analyze_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa volatilidade dos dados"""
        try:
            if df.empty:
                return {}
            
            # Calcula retornos
            df['returns'] = df['close'].pct_change()
            
            # Volatilidade (desvio padrão dos retornos)
            volatility = df['returns'].std()
            volatility_window = df['returns'].rolling(self.config['volatility_window']).std()
            current_volatility = volatility_window.iloc[-1]
            avg_volatility = volatility_window.mean()
            
            # Classifica nível de volatilidade
            volatility_ratio = current_volatility / avg_volatility if avg_volatility > 0 else 1
            
            if volatility_ratio > 1.5:
                level = 'high'
            elif volatility_ratio < 0.7:
                level = 'low'
            else:
                level = 'normal'
            
            return {
                'current_volatility': float(current_volatility),
                'average_volatility': float(avg_volatility),
                'volatility_ratio': float(volatility_ratio),
                'volatility_level': level,
                'volatility_trend': 'increasing' if volatility_window.iloc[-1] > volatility_window.iloc[-5] else 'decreasing'
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de volatilidade: {str(e)}")
            return {}

    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa volume de negociação"""
        try:
            if df.empty:
                return {}
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Detecta picos de volume
            volume_spike = volume_ratio > self.config['volume_threshold_multiplier']
            
            # Tendência de preço com volume
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            price_trend = 'up' if price_change > 0.001 else 'down' if price_change < -0.001 else 'neutral'
            
            # Tendência de volume
            volume_ma_short = df['volume'].rolling(5).mean().iloc[-1]
            volume_ma_long = df['volume'].rolling(20).mean().iloc[-1]
            volume_trend = 'increasing' if volume_ma_short > volume_ma_long else 'decreasing'
            
            return {
                'current_volume': float(current_volume),
                'average_volume': float(avg_volume),
                'volume_ratio': float(volume_ratio),
                'volume_spike': volume_spike,
                'price_trend': price_trend,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de volume: {str(e)}")
            return {}

    def _analyze_price_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa padrões de preço"""
        try:
            if df.empty or len(df) < 20:
                return {'patterns': []}
            
            patterns = []
            
            # Padrão: Doji
            last_candle = df.iloc[-1]
            body_size = abs(last_candle['close'] - last_candle['open'])
            wick_size = last_candle['high'] - last_candle['low']
            
            if body_size < (wick_size * 0.1):  # Corpo muito pequeno
                patterns.append({
                    'name': 'Doji',
                    'signal': 'neutral',
                    'confidence': 0.6,
                    'description': 'Indecisão do mercado'
                })
            
            # Padrão: Martelo ou Shooting Star
            upper_wick = last_candle['high'] - max(last_candle['open'], last_candle['close'])
            lower_wick = min(last_candle['open'], last_candle['close']) - last_candle['low']
            
            if lower_wick > (body_size * 2) and upper_wick < (body_size * 0.5):
                patterns.append({
                    'name': 'Hammer',
                    'signal': 'bullish',
                    'confidence': 0.7,
                    'description': 'Possível reversão de alta'
                })
            elif upper_wick > (body_size * 2) and lower_wick < (body_size * 0.5):
                patterns.append({
                    'name': 'Shooting Star',
                    'signal': 'bearish',
                    'confidence': 0.7,
                    'description': 'Possível reversão de baixa'
                })
            
            # Padrão: Rompimento de máximas/mínimas
            recent_high = df['high'].rolling(20).max().iloc[-21]  # Máxima dos últimos 20 excluindo o atual
            recent_low = df['low'].rolling(20).min().iloc[-21]    # Mínima dos últimos 20 excluindo o atual
            
            if last_candle['high'] > recent_high:
                patterns.append({
                    'name': 'Breakout High',
                    'signal': 'bullish',
                    'confidence': 0.8,
                    'description': 'Rompimento de máximas recentes'
                })
            elif last_candle['low'] < recent_low:
                patterns.append({
                    'name': 'Breakdown Low',
                    'signal': 'bearish',
                    'confidence': 0.8,
                    'description': 'Rompimento de mínimas recentes'
                })
            
            return {'patterns': patterns}
            
        except Exception as e:
            self.logger.error(f"Erro na análise de padrões: {str(e)}")
            return {'patterns': []}

    def _calculate_data_span(self, market_data: List[Dict]) -> float:
        """Calcula o período de tempo coberto pelos dados em horas"""
        try:
            if len(market_data) < 2:
                return 0
            
            first_time = market_data[0]['open_time']
            last_time = market_data[-1]['open_time']
            
            if hasattr(first_time, 'timestamp'):
                time_diff = last_time.timestamp() - first_time.timestamp()
            else:
                time_diff = last_time - first_time
            
            return time_diff / 3600  # Converte para horas
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular período dos dados: {str(e)}")
            return 0

    def _create_analysis_summary(self, processed_data: Dict, signals: List[TradingSignal], 
                                risk_analysis: Dict, opportunity_analysis: Dict) -> Dict[str, Any]:
        """Cria resumo da análise"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'data_quality': processed_data.get('data_quality', {}),
                'signals_count': {
                    'total': len(signals),
                    'buy': len([s for s in signals if s.signal_type == 'buy']),
                    'sell': len([s for s in signals if s.signal_type == 'sell']),
                    'hold': len([s for s in signals if s.signal_type == 'hold'])
                },
                'highest_confidence_signal': None,
                'risk_level': risk_analysis.get('overall_risk', 'unknown'),
                'opportunity_level': opportunity_analysis.get('overall_opportunity', 'unknown'),
                'recommendation': 'hold'  # Padrão
            }
            
            # Encontra sinal com maior confiança
            if signals:
                best_signal = max(signals, key=lambda s: s.confidence)
                summary['highest_confidence_signal'] = {
                    'type': best_signal.signal_type,
                    'confidence': best_signal.confidence,
                    'strength': best_signal.strength,
                    'reasoning': best_signal.reasoning
                }
                summary['recommendation'] = best_signal.signal_type
            
            # Adiciona observações baseadas na análise
            observations = []
            
            if risk_analysis.get('risk_score', 0.5) > 0.7:
                observations.append("Alto risco detectado - use gerenciamento de risco rigoroso")
            
            if opportunity_analysis.get('opportunity_score', 0.5) > 0.7:
                observations.append("Alta oportunidade identificada")
            
            if len(signals) == 0:
                observations.append("Nenhum sinal forte identificado - aguarde melhores condições")
            
            summary['observations'] = observations
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao criar resumo da análise: {str(e)}")
            return {'timestamp': datetime.now().isoformat(), 'error': str(e)}


# Função principal para uso externo
def analyze_symbol(symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict[str, Any]:
    """
    Função principal para análise de símbolo
    
    Args:
        symbol: Símbolo do par de trading
        timeframe: Timeframe para análise
        limit: Número de candles para análise
        
    Returns:
        Análise completa do símbolo
    """
    try:
        analyzer = SymbolAnalyzer()
        return analyzer.analyze_symbol(symbol, timeframe, limit)
    except Exception as e:
        logger.error(f"Erro na análise de {symbol}: {str(e)}")
        return {}


# Funções auxiliares para integração
def fetch_market_data(symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
    """Busca dados de mercado para o símbolo"""
    analyzer = SymbolAnalyzer()
    return analyzer.fetch_market_data(symbol, timeframe, limit)


def process_data(market_data: List[Dict]) -> Dict[str, Any]:
    """Processa dados de mercado e calcula indicadores"""
    analyzer = SymbolAnalyzer()
    return analyzer.process_data(market_data)


def generate_signals(symbol: str, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Gera sinais de trading baseados nos dados processados"""
    analyzer = SymbolAnalyzer()
    signals = analyzer.generate_signals(symbol, processed_data)
    
    # Converte TradingSignal para dict para compatibilidade
    return [asdict(signal) for signal in signals]


def record_signals(signals: List[Dict[str, Any]]) -> bool:
    """Registra sinais no banco de dados"""
    try:
        analyzer = SymbolAnalyzer()
        
        # Converte dicts para TradingSignal se necessário
        trading_signals = []
        for signal in signals:
            if isinstance(signal, dict):
                trading_signal = TradingSignal(
                    symbol=signal['symbol'],
                    signal_type=signal['signal_type'],
                    strength=signal['strength'],
                    confidence=signal['confidence'],
                    price=signal['price'],
                    timestamp=datetime.fromisoformat(signal['timestamp']) if isinstance(signal['timestamp'], str) else signal['timestamp'],
                    reasoning=signal['reasoning'],
                    indicators_data=signal['indicators_data'],
                    source=signal['source']
                )
                trading_signals.append(trading_signal)
            else:
                trading_signals.append(signal)
        
        return analyzer.record_signals(trading_signals)
        
    except Exception as e:
        logger.error(f"Erro ao registrar sinais: {str(e)}")
        return False
