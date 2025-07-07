#!/usr/bin/env python3
"""
Módulo de gestão de risco adaptativa para Robot-Crypt
Implementa algoritmos de aprendizado contínuo para ajuste dinâmico de parâmetros de trading
"""
import os
import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from src.core.config import Config
from src.utils.utils import setup_logger

# Importar analisador de contexto avançado se disponível
try:
    from contextual_analysis.advanced_context_analyzer import AdvancedContextAnalyzer
    advanced_context_available = True
except ImportError:
    advanced_context_available = False

class AdaptiveRiskManager:
    """
    Gerenciador de risco adaptativo que ajusta dinamicamente parâmetros como
    stop loss, take profit e alocação de capital baseado em:
    
    1. Histórico de negociações
    2. Volatilidade recente do mercado
    3. Desempenho de cada par de trading
    4. Condições de mercado variáveis
    """
    
    def __init__(self, db_manager, config=None, context_analyzer=None, news_analyzer=None):
        """Inicializa o gerenciador de risco adaptativo
        
        Args:
            db_manager: Instância do DBManager para acessar dados históricos
            config: Configuração do bot (opcional)
            context_analyzer: Analisador de contexto externo (opcional)
            news_analyzer: Analisador de notícias (opcional)
        """
        self.db_manager = db_manager
        self.config = config if config else Config()
        self.logger = logging.getLogger("robot-crypt")
        
        # Inicializa o analisador de contexto avançado se não for fornecido
        self.context_analyzer = context_analyzer
        self.news_analyzer = news_analyzer
        
        # Se não foi fornecido um analisador de contexto, tenta criar um novo
        if advanced_context_available and not self.context_analyzer:
            try:
                self.context_analyzer = AdvancedContextAnalyzer(config=config, news_analyzer=news_analyzer)
                self.logger.info("Analisador de contexto avançado inicializado com sucesso")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar analisador de contexto: {str(e)}")
                self.context_analyzer = None
        
        # Parâmetros de controle
        self.min_history_entries = 5  # Mínimo de operações históricas necessárias
        self.volatility_lookback_days = 14  # Janela para cálculo de volatilidade
        self.consecutive_loss_threshold = 3  # Quantidade de perdas consecutivas para trigger
        self.profit_target_volatility_factor = 1.5  # Fator para ajuste de alvos baseado em volatilidade
        
        # Carrega histórico de operações
        self.trade_history = {}  # Será preenchido sob demanda
        
        # Diretório para armazenar modelos e dados
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.models_file = self.data_dir / "risk_models.json"
        
        # Inicializa/carrega modelos de risco
        self.risk_models = self._load_risk_models()
        
        # Limites de ajuste para evitar parâmetros extremos
        self.adjustment_limits = {
            'stop_loss': {'min': 0.5, 'max': 2.0},  # Fatores multiplicadores
            'take_profit': {'min': 0.5, 'max': 2.0},
            'position_size': {'min': 0.3, 'max': 1.5},
            'max_hold_time': {'min': 0.5, 'max': 2.0}
        }

    def _load_risk_models(self):
        """Carrega modelos de risco do arquivo
        
        Returns:
            dict: Modelos de risco por símbolo
        """
        try:
            if os.path.exists(self.models_file):
                with open(self.models_file, 'r') as f:
                    models = json.load(f)
                    self.logger.info(f"Modelos de risco carregados: {len(models)} símbolos")
                    return models
            else:
                self.logger.info("Arquivo de modelos não encontrado. Criando novo.")
                return {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelos de risco: {str(e)}")
            return {}

    def _save_risk_models(self):
        """Salva modelos de risco em arquivo"""
        try:
            with open(self.models_file, 'w') as f:
                json.dump(self.risk_models, f, indent=2)
            self.logger.info("Modelos de risco salvos com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelos de risco: {str(e)}")
            return False

    def _get_trade_history(self, symbol, days=30):
        """Obtém histórico de operações para um símbolo
        
        Args:
            symbol (str): Símbolo do par de trading
            days (int): Número de dias do histórico
            
        Returns:
            list: Lista de operações
        """
        # Verificar se já temos em cache
        cache_key = f"{symbol}_{days}"
        if cache_key in self.trade_history:
            return self.trade_history[cache_key]
            
        # Buscar do banco de dados
        history = self.db_manager.get_operations_by_symbol(symbol, days)
        
        # Armazenar em cache
        self.trade_history[cache_key] = history
        
        return history

    def calculate_market_volatility(self, symbol, klines=None):
        """Calcula a volatilidade recente do mercado para um símbolo
        
        Args:
            symbol (str): Símbolo do par de trading
            klines (list, optional): Dados de velas, se já disponíveis
            
        Returns:
            float: Percentual de volatilidade diária média
        """
        try:
            # Se não foram fornecidos dados de velas, precisa obter da API
            # (Neste caso, assumimos que o chamador fornecerá os dados)
            if not klines or len(klines) < 10:
                self.logger.warning(f"Dados insuficientes para calcular volatilidade de {symbol}")
                return 0.05  # Valor padrão de volatilidade (5%)
            
            # Extrair preços de fechamento
            closes = [float(k[4]) for k in klines]
            
            # Calcular retornos diários
            returns = []
            for i in range(1, len(closes)):
                daily_return = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(daily_return)
            
            # Calcular desvio padrão dos retornos (volatilidade)
            if not returns:
                return 0.05
                
            volatility = np.std(returns)
            
            # Converter para percentual diário
            daily_volatility = volatility * 100
            
            # Limitar a faixa (1% a 30%)
            daily_volatility = max(1.0, min(30.0, daily_volatility))
            
            return daily_volatility
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular volatilidade: {str(e)}")
            return 0.05  # Valor padrão em caso de erro

    def analyze_performance(self, symbol):
        """Analisa o desempenho histórico de um par de trading
        
        Args:
            symbol (str): Símbolo do par de trading
            
        Returns:
            dict: Métricas de desempenho
        """
        try:
            # Obter histórico de operações
            history = self._get_trade_history(symbol, days=60)
            
            # Verificar se há dados suficientes
            if len(history) < self.min_history_entries:
                self.logger.info(f"Histórico insuficiente para {symbol}. Usando configurações padrão.")
                return {
                    'symbol': symbol,
                    'success_rate': 0.5,  # 50% taxa de sucesso padrão
                    'avg_profit': 0.02,  # 2% lucro médio padrão
                    'avg_loss': 0.01,    # 1% perda média padrão
                    'risk_reward_ratio': 2.0,  # Razão de 2:1 padrão
                    'volatility_score': 1.0,  # Score normal
                    'consecutive_losses': 0,
                    'confidence': 0.5  # Confiança média (pela falta de dados)
                }
                
            # Separar operações de compra e venda
            buys = [op for op in history if op['operation_type'] == 'buy']
            sells = [op for op in history if op['operation_type'] == 'sell']
            
            # Contar operações com lucro e prejuízo
            profitable_trades = [op for op in sells if op.get('profit_percent', 0) > 0]
            loss_trades = [op for op in sells if op.get('profit_percent', 0) <= 0]
            
            # Calcular taxa de sucesso
            total_completed_trades = len(profitable_trades) + len(loss_trades)
            success_rate = len(profitable_trades) / total_completed_trades if total_completed_trades > 0 else 0.5
            
            # Calcular lucro/perda média
            avg_profit = sum([op.get('profit_percent', 0) for op in profitable_trades]) / len(profitable_trades) if profitable_trades else 0.02
            avg_loss = abs(sum([op.get('profit_percent', 0) for op in loss_trades]) / len(loss_trades)) if loss_trades else 0.01
            
            # Calcular razão risco/recompensa
            risk_reward_ratio = avg_profit / avg_loss if avg_loss > 0 else 2.0
            
            # Detectar perdas consecutivas
            consecutive_losses = 0
            sorted_sells = sorted(sells, key=lambda x: x.get('timestamp'), reverse=True)
            
            for sell in sorted_sells:
                if sell.get('profit_percent', 0) <= 0:
                    consecutive_losses += 1
                else:
                    break
                    
            # Calcular nível de confiança baseado no volume de dados
            confidence = min(1.0, total_completed_trades / 20.0)  # Máximo com 20 trades
            
            # Retornar métricas
            return {
                'symbol': symbol,
                'success_rate': success_rate,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'risk_reward_ratio': risk_reward_ratio,
                'volatility_score': 1.0,  # Será definido posteriormente
                'consecutive_losses': consecutive_losses,
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de desempenho para {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'success_rate': 0.5,
                'avg_profit': 0.02,
                'avg_loss': 0.01,
                'risk_reward_ratio': 2.0,
                'volatility_score': 1.0,
                'consecutive_losses': 0,
                'confidence': 0.5
            }

    def update_symbol_risk_model(self, symbol, klines=None, external_factors=None):
        """Atualiza o modelo de risco para um símbolo específico
        
        Args:
            symbol (str): Símbolo do par de trading
            klines (list, optional): Dados de velas, se já disponíveis
            external_factors (dict, optional): Fatores externos, se disponíveis
            
        Returns:
            dict: Modelo de risco atualizado
        """
        try:
            # Verificar se já existe modelo para este símbolo
            if symbol not in self.risk_models:
                # Criar novo modelo com configurações padrão
                self.risk_models[symbol] = {
                    'symbol': symbol,
                    'base_stop_loss': self.config.scalping.get("stop_loss", 0.005),
                    'base_take_profit': self.config.scalping.get("take_profit", 0.015),
                    'base_position_size': self.config.scalping.get("max_position_size", 0.1),
                    'base_max_hold_time': 24,  # Horas
                    'adjustments': {
                        'stop_loss_factor': 1.0,
                        'take_profit_factor': 1.0,
                        'position_size_factor': 1.0,
                        'max_hold_time_factor': 1.0
                    },
                    'last_updated': datetime.now().isoformat(),
                    'market_conditions': 'normal'
                }
            
            # Obter modelo atual
            model = self.risk_models[symbol]
            
            # Calcular volatilidade do mercado
            volatility = self.calculate_market_volatility(symbol, klines)
            
            # Analisar desempenho histórico
            performance = self.analyze_performance(symbol)
            
            # Definir score de volatilidade relativa (comparado ao normal)
            # - Acima de 1.0: Mais volátil que o normal
            # - Abaixo de 1.0: Menos volátil que o normal
            normal_volatility = 5.0  # 5% é considerado normal
            volatility_score = volatility / normal_volatility
            performance['volatility_score'] = volatility_score
            
            # Calcular fatores de ajuste baseados no desempenho e volatilidade
            adjustments = self._calculate_adjustment_factors(performance, external_factors)
            
            # Atualizar modelo
            model['adjustments'] = adjustments
            model['last_updated'] = datetime.now().isoformat()
            model['volatility'] = volatility
            model['performance'] = {
                'success_rate': performance['success_rate'],
                'avg_profit': performance['avg_profit'],
                'avg_loss': performance['avg_loss'],
                'consecutive_losses': performance['consecutive_losses']
            }
            
            # Determinar condições de mercado
            if volatility_score > 1.5:
                model['market_conditions'] = 'highly_volatile'
            elif volatility_score > 1.2:
                model['market_conditions'] = 'volatile'
            elif volatility_score < 0.8:
                model['market_conditions'] = 'low_volatility'
            else:
                model['market_conditions'] = 'normal'
                
            # Atualizar modelo em memoria
            self.risk_models[symbol] = model
            
            # Salvar todos os modelos em arquivo
            self._save_risk_models()
            
            return model
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar modelo de risco para {symbol}: {str(e)}")
            # Retornar modelo padrão em caso de erro
            return {
                'symbol': symbol,
                'adjustments': {
                    'stop_loss_factor': 1.0,
                    'take_profit_factor': 1.0,
                    'position_size_factor': 1.0,
                    'max_hold_time_factor': 1.0
                },
                'market_conditions': 'normal'
            }

    def _calculate_adjustment_factors(self, performance, external_factors=None):
        """Calcula fatores de ajuste baseados no desempenho e outros fatores
        
        Args:
            performance (dict): Métricas de desempenho
            external_factors (dict, optional): Fatores externos
            
        Returns:
            dict: Fatores de ajuste para parâmetros de trading
        """
        # Valores iniciais
        stop_loss_factor = 1.0
        take_profit_factor = 1.0
        position_size_factor = 1.0
        max_hold_time_factor = 1.0
        
        # Ajustar com base na taxa de sucesso
        success_rate = performance['success_rate']
        if success_rate > 0.7:  # Taxa de sucesso alta
            position_size_factor *= 1.2
            take_profit_factor *= 1.1
        elif success_rate < 0.4:  # Taxa de sucesso baixa
            position_size_factor *= 0.8
            stop_loss_factor *= 0.9  # Stop loss mais restrito
        
        # Ajustar com base na volatilidade
        volatility_score = performance['volatility_score']
        if volatility_score > 1.5:  # Muito volátil
            stop_loss_factor *= 1.2  # Stop loss mais flexível
            take_profit_factor *= 1.3  # Take profit mais alto
            position_size_factor *= 0.7  # Reduzir tamanho da posição
            max_hold_time_factor *= 0.8  # Reduzir tempo de retenção
        elif volatility_score < 0.7:  # Pouco volátil
            stop_loss_factor *= 0.9  # Stop loss mais restrito
            take_profit_factor *= 0.9  # Take profit mais baixo
            position_size_factor *= 1.1  # Aumentar tamanho da posição
            max_hold_time_factor *= 1.2  # Aumentar tempo de retenção
        
        # Ajustar com base em perdas consecutivas
        consecutive_losses = performance['consecutive_losses']
        if consecutive_losses >= self.consecutive_loss_threshold:
            reduction_factor = 1.0 - (0.1 * min(consecutive_losses, 5))  # Até 50% de redução
            position_size_factor *= reduction_factor
            max_hold_time_factor *= reduction_factor
        
        # Incorporar fatores externos, se disponíveis
        if external_factors and 'market_context_score' in external_factors:
            context_score = external_factors['market_context_score']
            
            # Contexto negativo
            if context_score < -0.3:
                position_size_factor *= (1.0 + context_score)  # Reduzir tamanho
                max_hold_time_factor *= (1.0 + context_score * 0.5)  # Reduzir tempo
                
            # Contexto positivo
            elif context_score > 0.3:
                position_size_factor *= (1.0 + context_score * 0.3)  # Aumentar tamanho
                take_profit_factor *= (1.0 + context_score * 0.2)  # Aumentar take profit
        
        # Aplicar limites para evitar valores extremos
        stop_loss_factor = self._apply_limits(stop_loss_factor, 'stop_loss')
        take_profit_factor = self._apply_limits(take_profit_factor, 'take_profit')
        position_size_factor = self._apply_limits(position_size_factor, 'position_size')
        max_hold_time_factor = self._apply_limits(max_hold_time_factor, 'max_hold_time')
        
        # Pesar os ajustes conforme a confiança na análise
        confidence = performance['confidence']
        
        # Quanto menos confiança, mais próximo de 1.0 (neutro)
        for factor_name in ['stop_loss_factor', 'take_profit_factor', 'position_size_factor', 'max_hold_time_factor']:
            locals()[factor_name] = 1.0 + (locals()[factor_name] - 1.0) * confidence
        
        return {
            'stop_loss_factor': round(stop_loss_factor, 2),
            'take_profit_factor': round(take_profit_factor, 2),
            'position_size_factor': round(position_size_factor, 2),
            'max_hold_time_factor': round(max_hold_time_factor, 2)
        }

    def _apply_limits(self, value, parameter):
        """Aplica limites ao valor para evitar ajustes extremos
        
        Args:
            value (float): Valor a ser limitado
            parameter (str): Nome do parâmetro
            
        Returns:
            float: Valor limitado
        """
        limits = self.adjustment_limits.get(parameter, {'min': 0.5, 'max': 2.0})
        return max(limits['min'], min(limits['max'], value))

    def get_adjusted_parameters(self, symbol, base_params, external_factors=None):
        """Obtém parâmetros de trading ajustados para um símbolo
        
        Args:
            symbol (str): Símbolo do par de trading
            base_params (dict): Parâmetros base
            external_factors (dict, optional): Fatores externos
            
        Returns:
            dict: Parâmetros ajustados
        """
        # Se temos o analisador de contexto avançado, vamos usar
        context_data = None
        if self.context_analyzer:
            try:
                # Extrai símbolo base da criptomoeda, se for um par como BTC/USDT
                crypto_symbol = symbol.split('/')[0] if '/' in symbol else symbol
                # Obter análise contextual e ajustes recomendados
                risk_base = base_params.get('stop_loss', 0.005)  # Usar stop_loss como base de risco
                context_data = self.context_analyzer.get_trading_adjustments(crypto_symbol, risk_base)
                self.logger.info(f"Análise contextual obtida para {crypto_symbol}: {context_data['context_score']:.2f}")
                
                # Atualizar/complementar fatores externos
                if external_factors is None:
                    external_factors = {}
                external_factors.update({
                    'market_context_score': context_data['context_score'],
                    'market_impact': context_data['market_impact'],
                    'alert_level': context_data['alert_level']
                })
            except Exception as e:
                self.logger.error(f"Erro ao obter dados contextuais para {symbol}: {str(e)}")
        
        # Verificar se temos modelo para este símbolo
        if symbol not in self.risk_models:
            # Criar um modelo básico
            self.update_symbol_risk_model(symbol, external_factors=external_factors)
        
        # Obter modelo e ajustes
        model = self.risk_models[symbol]
        adjustments = model['adjustments']
        
        # Se temos dados contextuais, aplicar ajustes adicionais
        context_adjustments = {}
        if context_data and 'adjustments' in context_data:
            context_adjustments = context_data['adjustments']
            self.logger.info(f"Aplicando ajustes contextuais para {symbol}: {context_adjustments}")
        
        # Obter parâmetros base
        stop_loss = base_params.get('stop_loss', model.get('base_stop_loss', 0.005))
        take_profit = base_params.get('take_profit', model.get('base_take_profit', 0.015))
        position_size = base_params.get('position_size', model.get('base_position_size', 0.1))
        max_hold_time = base_params.get('max_hold_time', model.get('base_max_hold_time', 24))
        
        # Aplicar ajustes do modelo de risco
        adjusted_params = {
            'stop_loss': round(stop_loss * adjustments['stop_loss_factor'], 4),
            'take_profit': round(take_profit * adjustments['take_profit_factor'], 4),
            'position_size': round(position_size * adjustments['position_size_factor'], 4),
            'max_hold_time': round(max_hold_time * adjustments['max_hold_time_factor'], 1)
        }
        
        # Se temos ajustes contextuais, aplicar como uma camada adicional
        if context_adjustments:
            # Aplicar fator de ajuste contextual para stop loss
            if 'stop_loss_factor' in context_adjustments:
                adjusted_params['stop_loss'] = round(adjusted_params['stop_loss'] * context_adjustments['stop_loss_factor'], 4)
            
            # Aplicar fator de ajuste contextual para take profit
            if 'take_profit_factor' in context_adjustments:
                adjusted_params['take_profit'] = round(adjusted_params['take_profit'] * context_adjustments['take_profit_factor'], 4)
            
            # Aplicar fator de ajuste contextual para tamanho da posição
            if 'position_size_factor' in context_adjustments:
                adjusted_params['position_size'] = round(adjusted_params['position_size'] * context_adjustments['position_size_factor'], 4)
            
            # Aplicar fator de ajuste contextual para tempo máximo de retenção
            if 'hold_time_factor' in context_adjustments:
                adjusted_params['max_hold_time'] = round(adjusted_params['max_hold_time'] * context_adjustments['hold_time_factor'], 1)
        
        # Adicionar justificativas para cada ajuste
        justifications = {
            'stop_loss': self._get_adjustment_explanation(adjustments['stop_loss_factor'], 'stop loss'),
            'take_profit': self._get_adjustment_explanation(adjustments['take_profit_factor'], 'objetivo de lucro'),
            'position_size': self._get_adjustment_explanation(adjustments['position_size_factor'], 'tamanho da posição'),
            'max_hold_time': self._get_adjustment_explanation(adjustments['max_hold_time_factor'], 'tempo máximo de retenção')
        }
        
        # Adicionar dados de contexto
        result = {
            'symbol': symbol,
            'base_parameters': base_params,
            'adjusted_parameters': adjusted_params,
            'adjustments': adjustments,
            'justifications': justifications,
            'market_conditions': model['market_conditions'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar métricas de desempenho se disponíveis
        if 'performance' in model:
            result['performance'] = model['performance']
            
        return result

    def _get_adjustment_explanation(self, factor, parameter_name):
        """Gera explicação para um ajuste específico
        
        Args:
            factor (float): Fator de ajuste
            parameter_name (str): Nome do parâmetro
            
        Returns:
            str: Explicação do ajuste
        """
        if abs(factor - 1.0) < 0.05:
            return f"{parameter_name.capitalize()} mantido no nível normal"
        
        change_percent = abs(factor - 1.0) * 100
        
        if factor > 1.0:
            return f"{parameter_name.capitalize()} aumentado em {change_percent:.1f}% devido às condições de mercado"
        else:
            return f"{parameter_name.capitalize()} reduzido em {change_percent:.1f}% devido às condições de mercado"


# Teste simples como programa principal
if __name__ == "__main__":
    # Configurar logger
    logger = setup_logger()
    
    # Para teste, importar aqui
    from db_manager import DBManager
    
    # Inicializar gerenciador de BD
    db = DBManager()
    
    # Inicializar gerenciador de risco
    risk_manager = AdaptiveRiskManager(db)
    
    # Testar para BTC/USDT
    symbol = "BTC/USDT"
    
    # Parâmetros base
    base_params = {
        'stop_loss': 0.005,  # 0.5%
        'take_profit': 0.015,  # 1.5%
        'position_size': 0.1,  # 10% do capital
        'max_hold_time': 24  # 24 horas
    }
    
    # Obter parâmetros ajustados
    adjusted = risk_manager.get_adjusted_parameters(symbol, base_params)
    print(json.dumps(adjusted, indent=2))
