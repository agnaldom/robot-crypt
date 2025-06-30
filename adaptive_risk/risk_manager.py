import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

class AdaptiveRiskManager:
    """Gerenciador de risco adaptativo que ajusta parâmetros com base nos dados históricos"""
    
    def __init__(self, initial_stop_loss=0.05, initial_take_profit=0.1, 
                 initial_position_size=0.1, max_position_size=0.3, 
                 min_stop_loss=0.01, max_stop_loss=0.15):
        """
        Inicializa o gerenciador de risco adaptativo
        
        Args:
            initial_stop_loss: Porcentagem inicial de stop loss (default: 5%)
            initial_take_profit: Porcentagem inicial de take profit (default: 10%)
            initial_position_size: Tamanho inicial da posição como fração do capital (default: 10%)
            max_position_size: Tamanho máximo da posição como fração do capital (default: 30%)
            min_stop_loss: Valor mínimo permitido para stop loss (default: 1%)
            max_stop_loss: Valor máximo permitido para stop loss (default: 15%)
        """
        self.stop_loss = initial_stop_loss
        self.take_profit = initial_take_profit
        self.position_size = initial_position_size
        self.max_position_size = max_position_size
        self.min_stop_loss = min_stop_loss
        self.max_stop_loss = max_stop_loss
        self.trade_history = []
        self.market_volatility = 0
        self.consecutive_losses = 0
        self.consecutive_wins = 0
    
    def add_trade_result(self, entry_price, exit_price, timestamp, trade_volume, 
                        stop_loss_used, take_profit_used, position_size_used):
        """
        Adiciona um resultado de trade ao histórico
        
        Args:
            entry_price: Preço de entrada do trade
            exit_price: Preço de saída do trade
            timestamp: Timestamp da conclusão do trade
            trade_volume: Volume do trade
            stop_loss_used: Stop loss utilizado neste trade
            take_profit_used: Take profit utilizado neste trade
            position_size_used: Tamanho da posição utilizado neste trade
        """
        profit_pct = (exit_price - entry_price) / entry_price
        is_profit = profit_pct > 0
        
        trade_info = {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_pct': profit_pct,
            'is_profit': is_profit,
            'timestamp': timestamp,
            'trade_volume': trade_volume,
            'stop_loss_used': stop_loss_used,
            'take_profit_used': take_profit_used,
            'position_size_used': position_size_used
        }
        
        self.trade_history.append(trade_info)
        
        # Atualiza contadores de sequências
        if is_profit:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        
        # Adapta os parâmetros após cada trade
        self._adapt_parameters()
        
        return trade_info
    
    def update_market_volatility(self, recent_prices, window=24):
        """
        Atualiza a volatilidade do mercado com base nos preços recentes
        
        Args:
            recent_prices: Lista ou array de preços recentes
            window: Janela de tempo para cálculo (default: 24 horas)
        """
        if len(recent_prices) < window:
            logger.warning("Dados insuficientes para calcular a volatilidade")
            return
            
        # Calcula os retornos percentuais
        prices = np.array(recent_prices[-window:])
        returns = np.diff(prices) / prices[:-1]
        
        # Atualiza a volatilidade (desvio padrão dos retornos)
        self.market_volatility = np.std(returns)
        logger.info(f"Volatilidade atualizada: {self.market_volatility:.4f}")
    
    def get_trade_parameters(self, asset=None, context_data=None):
        """
        Obtém os parâmetros de negociação atuais, ajustados para o ativo específico
        
        Args:
            asset: Ativo para o qual os parâmetros serão ajustados (opcional)
            context_data: Dados contextuais para ajustes adicionais (opcional)
            
        Returns:
            dict: Parâmetros de negociação
        """
        params = {
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size
        }
        
        # Ajustes específicos do ativo, se fornecido
        if asset:
            # Aqui poderia haver lógica para ajustar parâmetros específicos por ativo
            pass
            
        # Ajustes baseados em dados contextuais (notícias, eventos, etc)
        if context_data:
            alert_level = context_data.get('alert_level', 'baixo')
            
            # Ajusta parâmetros com base no nível de alerta
            if alert_level == 'crítico':
                params['position_size'] *= 0.5  # Reduz pela metade o tamanho da posição
                params['stop_loss'] *= 0.8      # Aperta o stop loss em 20%
            elif alert_level == 'alto':
                params['position_size'] *= 0.7  # Reduz o tamanho da posição em 30%
                params['stop_loss'] *= 0.9      # Aperta o stop loss em 10%
            elif alert_level == 'médio':
                params['position_size'] *= 0.9  # Reduz o tamanho da posição em 10%
            
        return params
    
    def _adapt_parameters(self):
        """
        Adapta os parâmetros de negociação com base no histórico de trades e volatilidade
        """
        # Ignora se não houver histórico suficiente
        if len(self.trade_history) < 5:
            return
            
        # Ajusta com base em perdas consecutivas
        if self.consecutive_losses >= 3:
            # Reduz tamanho da posição após perdas consecutivas
            self.position_size *= 0.8
            # Aumenta a proporção take_profit/stop_loss para buscar trades mais seguros
            self.take_profit = max(self.take_profit, self.stop_loss * 2.5)
            
        # Ajusta com base em ganhos consecutivos
        if self.consecutive_wins >= 3:
            # Aumenta gradualmente o tamanho da posição
            self.position_size = min(self.position_size * 1.1, self.max_position_size)
            
        # Ajusta com base na volatilidade do mercado
        if self.market_volatility > 0:
            # Em mercados mais voláteis, aumenta o stop loss
            volatility_factor = min(max(self.market_volatility * 10, 1), 3)
            new_stop_loss = self.stop_loss * volatility_factor
            self.stop_loss = max(min(new_stop_loss, self.max_stop_loss), self.min_stop_loss)
            
            # Ajusta take profit para manter proporção com stop loss
            self.take_profit = max(self.stop_loss * 1.5, self.take_profit)
        
        # Usa regressão para prever melhores parâmetros baseados no histórico
        self._optimize_parameters_with_ml()
        
        logger.info(f"Parâmetros adaptados: SL={self.stop_loss:.4f}, TP={self.take_profit:.4f}, " 
                   f"Tamanho da posição={self.position_size:.4f}")
    
    def _optimize_parameters_with_ml(self):
        """
        Usa aprendizado de máquina para otimizar parâmetros com base no histórico
        """
        # Precisamos de pelo menos 20 trades para fazer uma regressão significativa
        if len(self.trade_history) < 20:
            return
            
        # Prepara os dados para ML
        df = pd.DataFrame(self.trade_history)
        
        # Features: stop_loss, take_profit, position_size, market_volatility
        X = df[['stop_loss_used', 'take_profit_used', 'position_size_used']].values
        
        # Target: profit_pct
        y = df['profit_pct'].values
        
        # Treina um modelo simples de regressão
        model = LinearRegression()
        try:
            model.fit(X, y)
            
            # Gera possíveis combinações de parâmetros dentro de limites razoáveis
            stop_loss_options = np.linspace(self.min_stop_loss, self.max_stop_loss, 5)
            take_profit_options = np.linspace(self.stop_loss * 1.5, self.stop_loss * 3, 5)
            position_size_options = np.linspace(0.05, self.max_position_size, 5)
            
            best_profit = -float('inf')
            best_params = None
            
            # Encontra a melhor combinação de parâmetros
            for sl in stop_loss_options:
                for tp in take_profit_options:
                    for ps in position_size_options:
                        params = np.array([[sl, tp, ps]])
                        predicted_profit = model.predict(params)[0]
                        
                        if predicted_profit > best_profit:
                            best_profit = predicted_profit
                            best_params = (sl, tp, ps)
            
            # Atualiza gradualmente os parâmetros em direção aos melhores previstos
            if best_params:
                weight = 0.3  # Peso da adaptação (30% em direção aos valores ótimos)
                self.stop_loss = (1 - weight) * self.stop_loss + weight * best_params[0]
                self.take_profit = (1 - weight) * self.take_profit + weight * best_params[1]
                self.position_size = (1 - weight) * self.position_size + weight * best_params[2]
                
                logger.info(f"Parâmetros otimizados por ML: SL={self.stop_loss:.4f}, "
                           f"TP={self.take_profit:.4f}, Posição={self.position_size:.4f}")
                
        except Exception as e:
            logger.error(f"Erro na otimização por ML: {str(e)}")
