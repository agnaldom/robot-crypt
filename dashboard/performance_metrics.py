import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PerformanceMetrics:
    """Calcula métricas de desempenho com base no histórico de trades"""
    
    def __init__(self, trades_data):
        """
        Inicializa a classe com dados de trades
        
        Args:
            trades_data: Lista de dicionários contendo dados de trades
        """
        self.trades = trades_data
        self.trades_df = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()
    
    def get_win_rate(self):
        """
        Calcula a taxa de acerto (win rate)
        
        Returns:
            float: Taxa de acerto como fração (0-1)
        """
        if self.trades_df.empty:
            return 0
            
        return self.trades_df['is_profit'].mean()
    
    def get_average_profit(self):
        """
        Calcula o lucro médio por trade
        
        Returns:
            float: Lucro médio como fração (ex: 0.05 = 5%)
        """
        if self.trades_df.empty:
            return 0
            
        return self.trades_df['profit_pct'].mean()
    
    def get_profit_loss_ratio(self):
        """
        Calcula a relação entre lucro médio e prejuízo médio
        
        Returns:
            float: Relação lucro/prejuízo
        """
        if self.trades_df.empty:
            return 0
            
        # Separa trades com lucro e prejuízo
        profitable = self.trades_df[self.trades_df['profit_pct'] > 0]
        losing = self.trades_df[self.trades_df['profit_pct'] < 0]
        
        # Calcula a média de cada grupo
        if profitable.empty or losing.empty:
            return 0
            
        avg_profit = profitable['profit_pct'].mean()
        avg_loss = abs(losing['profit_pct'].mean())
        
        # Calcula a relação (evita divisão por zero)
        if avg_loss == 0:
            return float('inf')
            
        return avg_profit / avg_loss
    
    def get_drawdown(self):
        """
        Calcula o drawdown máximo
        
        Returns:
            float: Drawdown máximo como fração (ex: 0.15 = 15%)
        """
        if self.trades_df.empty:
            return 0
            
        # Ordena os trades por timestamp
        sorted_trades = self.trades_df.sort_values('timestamp')
        
        # Calcula o saldo acumulado
        sorted_trades['cumulative_profit'] = sorted_trades['profit_pct'].cumsum()
        
        # Calcula o drawdown
        running_max = sorted_trades['cumulative_profit'].cummax()
        drawdown = (running_max - sorted_trades['cumulative_profit']) / (1 + running_max)
        
        return drawdown.max()
    
    def get_sharpe_ratio(self, risk_free_rate=0.01):
        """
        Calcula o Sharpe Ratio (adaptado para trading)
        
        Args:
            risk_free_rate: Taxa livre de risco anualizada (default: 1%)
            
        Returns:
            float: Sharpe Ratio
        """
        if self.trades_df.empty:
            return 0
            
        # Calcula retornos e desvio padrão
        returns = self.trades_df['profit_pct']
        if len(returns) < 2:
            return 0
            
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0
            
        # Estima o número de trades por ano (assumindo trades diários para simplificar)
        daily_trades = len(returns) / 30  # Aproximação
        annual_factor = np.sqrt(365 / 30)
        
        # Ajusta o risk-free rate para o período de um trade
        rfr_per_trade = risk_free_rate / 365
        
        # Calcula o Sharpe Ratio
        sharpe = (mean_return - rfr_per_trade) / std_return * annual_factor
        
        return sharpe
    
    def get_expectancy(self):
        """
        Calcula a expectativa matemática por trade
        
        Returns:
            float: Expectativa por trade
        """
        if self.trades_df.empty:
            return 0
            
        win_rate = self.get_win_rate()
        win_avg = self.trades_df[self.trades_df['profit_pct'] > 0]['profit_pct'].mean() if win_rate > 0 else 0
        loss_avg = self.trades_df[self.trades_df['profit_pct'] < 0]['profit_pct'].mean() if win_rate < 1 else 0
        
        expectancy = (win_rate * win_avg) + ((1 - win_rate) * loss_avg)
        
        return expectancy
    
    def get_metrics_summary(self):
        """
        Obtém um resumo de todas as métricas importantes
        
        Returns:
            dict: Resumo das métricas
        """
        return {
            'win_rate': self.get_win_rate(),
            'avg_profit': self.get_average_profit(),
            'profit_loss_ratio': self.get_profit_loss_ratio(),
            'max_drawdown': self.get_drawdown(),
            'sharpe_ratio': self.get_sharpe_ratio(),
            'expectancy': self.get_expectancy(),
            'total_trades': len(self.trades_df),
            'profitable_trades': self.trades_df['is_profit'].sum() if not self.trades_df.empty else 0,
            'losing_trades': (~self.trades_df['is_profit']).sum() if not self.trades_df.empty else 0
        }
