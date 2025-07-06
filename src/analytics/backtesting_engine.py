"""
Backtesting Engine - Sistema de backtesting robusto
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
import warnings
from dataclasses import dataclass
from enum import Enum
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')


class OrderType(Enum):
    """Tipos de ordem"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Status da ordem"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """Representa uma operação"""
    timestamp: datetime
    symbol: str
    order_type: OrderType
    quantity: float
    price: float
    commission: float = 0.0
    order_id: str = ""
    
    @property
    def value(self) -> float:
        """Valor total da operação"""
        return self.quantity * self.price


@dataclass
class Position:
    """Representa uma posição"""
    symbol: str
    quantity: float
    avg_price: float
    timestamp: datetime
    
    @property
    def value(self) -> float:
        """Valor total da posição"""
        return self.quantity * self.avg_price
    
    @property
    def is_long(self) -> bool:
        """Se a posição é long"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Se a posição é short"""
        return self.quantity < 0


class BacktestingEngine:
    """
    Engine de backtesting para estratégias de trading
    """
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
    
    def reset(self):
        """Reset do engine"""
        self.cash = self.initial_capital
        self.positions = {}  # symbol -> Position
        self.trades = []     # Lista de trades
        self.portfolio_history = []  # Histórico do portfolio
        self.current_timestamp = None
        self.results = {}
    
    def add_data(self, data: pd.DataFrame, symbol: str = "BTCUSDT"):
        """
        Adiciona dados para backtesting
        
        Args:
            data: DataFrame com dados OHLCV
            symbol: Símbolo do ativo
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Dados devem conter: {required_columns}")
        
        self.data = data.copy()
        self.symbol = symbol
        
        # Ensure timestamp index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                self.data.set_index('timestamp', inplace=True)
            else:
                self.data.index = pd.date_range(start='2023-01-01', periods=len(data), freq='1H')
    
    def place_order(self, order_type: OrderType, quantity: float, 
                   price: Optional[float] = None, symbol: Optional[str] = None) -> bool:
        """
        Coloca uma ordem
        
        Args:
            order_type: Tipo da ordem (BUY/SELL)
            quantity: Quantidade
            price: Preço (None para preço de mercado)
            symbol: Símbolo do ativo
            
        Returns:
            True se a ordem foi executada
        """
        if symbol is None:
            symbol = self.symbol
        
        if price is None:
            # Usar preço atual de mercado
            if self.current_timestamp is None:
                return False
            
            current_data = self.data.loc[self.current_timestamp]
            price = current_data['close']
        
        # Calcular comissão
        trade_value = quantity * price
        commission_cost = trade_value * self.commission
        
        # Verificar se há capital suficiente para compra
        if order_type == OrderType.BUY:
            total_cost = trade_value + commission_cost
            if total_cost > self.cash:
                return False  # Não há capital suficiente
        
        # Verificar se há posição suficiente para venda
        elif order_type == OrderType.SELL:
            current_position = self.positions.get(symbol, Position(symbol, 0, 0, self.current_timestamp))
            if quantity > current_position.quantity:
                return False  # Não há posição suficiente
        
        # Executar a ordem
        trade = Trade(
            timestamp=self.current_timestamp,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
            commission=commission_cost,
            order_id=f"{len(self.trades)+1:06d}"
        )
        
        self.trades.append(trade)
        
        # Atualizar posição
        self._update_position(trade)
        
        # Atualizar cash
        if order_type == OrderType.BUY:
            self.cash -= (trade_value + commission_cost)
        else:
            self.cash += (trade_value - commission_cost)
        
        return True
    
    def _update_position(self, trade: Trade):
        """Atualiza posição após trade"""
        symbol = trade.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, 0, 0, trade.timestamp)
        
        position = self.positions[symbol]
        
        if trade.order_type == OrderType.BUY:
            # Calcular novo preço médio
            total_value = position.value + trade.value
            new_quantity = position.quantity + trade.quantity
            new_avg_price = total_value / new_quantity if new_quantity > 0 else 0
            
            position.quantity = new_quantity
            position.avg_price = new_avg_price
            position.timestamp = trade.timestamp
            
        elif trade.order_type == OrderType.SELL:
            position.quantity -= trade.quantity
            
            # Se zerou a posição, reset avg_price
            if position.quantity <= 0:
                position.quantity = 0
                position.avg_price = 0
    
    def get_portfolio_value(self, timestamp: Optional[datetime] = None) -> float:
        """
        Calcula valor total do portfolio
        
        Args:
            timestamp: Timestamp para cálculo (usar atual se None)
            
        Returns:
            Valor total do portfolio
        """
        if timestamp is None:
            timestamp = self.current_timestamp
        
        if timestamp is None or timestamp not in self.data.index:
            return self.cash
        
        current_prices = self.data.loc[timestamp]
        portfolio_value = self.cash
        
        for symbol, position in self.positions.items():
            if position.quantity > 0:
                if symbol == self.symbol:
                    current_price = current_prices['close']
                    portfolio_value += position.quantity * current_price
        
        return portfolio_value
    
    def run_backtest(self, strategy: Callable, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None, **strategy_params) -> Dict[str, Any]:
        """
        Executa backtesting
        
        Args:
            strategy: Função de estratégia
            start_date: Data de início
            end_date: Data de fim
            **strategy_params: Parâmetros da estratégia
            
        Returns:
            Resultados do backtesting
        """
        # Reset do engine
        self.reset()
        
        # Filtrar dados por período
        data_subset = self.data.copy()
        if start_date:
            data_subset = data_subset[data_subset.index >= start_date]
        if end_date:
            data_subset = data_subset[data_subset.index <= end_date]
        
        # Executar estratégia para cada timestamp
        for timestamp in data_subset.index:
            self.current_timestamp = timestamp
            current_data = data_subset.loc[timestamp]
            
            # Executar estratégia
            try:
                strategy(self, current_data, **strategy_params)
            except Exception as e:
                print(f"Erro na estratégia em {timestamp}: {e}")
                continue
            
            # Registrar valor do portfolio
            portfolio_value = self.get_portfolio_value(timestamp)
            self.portfolio_history.append({
                'timestamp': timestamp,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions_value': portfolio_value - self.cash,
                'returns': (portfolio_value / self.initial_capital - 1) * 100
            })
        
        # Calcular métricas de performance
        self.results = self._calculate_performance_metrics()
        
        return self.results
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de performance"""
        if not self.portfolio_history:
            return {}
        
        df = pd.DataFrame(self.portfolio_history)
        df.set_index('timestamp', inplace=True)
        
        # Retornos
        df['daily_returns'] = df['portfolio_value'].pct_change()
        
        # Métricas básicas
        final_value = df['portfolio_value'].iloc[-1]
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # Número de trades
        num_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t.order_type == OrderType.BUY])
        sell_trades = len([t for t in self.trades if t.order_type == OrderType.SELL])
        
        # Comissões totais
        total_commission = sum(t.commission for t in self.trades)
        
        # Drawdown
        running_max = df['portfolio_value'].expanding().max()
        drawdown = (df['portfolio_value'] - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Métricas de retorno
        daily_returns = df['daily_returns'].dropna()
        
        if len(daily_returns) > 0:
            avg_daily_return = daily_returns.mean()
            volatility = daily_returns.std()
            sharpe_ratio = avg_daily_return / volatility * np.sqrt(252) if volatility > 0 else 0
            
            # Sortino Ratio
            negative_returns = daily_returns[daily_returns < 0]
            downside_volatility = negative_returns.std() if len(negative_returns) > 0 else 0
            sortino_ratio = avg_daily_return / downside_volatility * np.sqrt(252) if downside_volatility > 0 else 0
            
            # Calmar Ratio
            annualized_return = (final_value / self.initial_capital) ** (252 / len(daily_returns)) - 1
            calmar_ratio = annualized_return / abs(max_drawdown / 100) if max_drawdown != 0 else 0
        else:
            avg_daily_return = 0
            volatility = 0
            sharpe_ratio = 0
            sortino_ratio = 0
            annualized_return = 0
            calmar_ratio = 0
        
        # Win Rate
        profitable_trades = self._calculate_trade_pnl()
        if profitable_trades:
            wins = len([pnl for pnl in profitable_trades if pnl > 0])
            win_rate = wins / len(profitable_trades) * 100 if profitable_trades else 0
            avg_win = np.mean([pnl for pnl in profitable_trades if pnl > 0]) if wins > 0 else 0
            avg_loss = np.mean([pnl for pnl in profitable_trades if pnl < 0]) if (len(profitable_trades) - wins) > 0 else 0
            profit_factor = abs(avg_win * wins / (avg_loss * (len(profitable_trades) - wins))) if avg_loss != 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        # Período de teste
        start_date = df.index[0]
        end_date = df.index[-1]
        duration = (end_date - start_date).days
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return * 100,
            'max_drawdown_pct': max_drawdown,
            'volatility_pct': volatility * 100 * np.sqrt(252),
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'num_trades': num_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_commission': total_commission,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration,
            'portfolio_history': df,
            'trades': self.trades
        }
    
    def _calculate_trade_pnl(self) -> List[float]:
        """Calcula P&L de cada trade fechado"""
        pnl_list = []
        
        # Agrupar trades por símbolo
        symbol_trades = {}
        for trade in self.trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        # Calcular P&L para cada símbolo
        for symbol, trades in symbol_trades.items():
            position_qty = 0
            position_cost = 0
            
            for trade in trades:
                if trade.order_type == OrderType.BUY:
                    position_qty += trade.quantity
                    position_cost += trade.value + trade.commission
                
                elif trade.order_type == OrderType.SELL:
                    if position_qty > 0:
                        # Calcular P&L da venda
                        avg_cost = position_cost / position_qty
                        pnl = (trade.price - avg_cost) * trade.quantity - trade.commission
                        pnl_list.append(pnl)
                        
                        # Atualizar posição
                        position_qty -= trade.quantity
                        position_cost = avg_cost * position_qty if position_qty > 0 else 0
        
        return pnl_list
    
    def create_performance_report(self) -> go.Figure:
        """
        Cria relatório visual de performance
        
        Returns:
            Figura Plotly com gráficos
        """
        if not self.results or 'portfolio_history' not in self.results:
            return go.Figure()
        
        df = self.results['portfolio_history']
        
        # Criar subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Evolução do Portfolio', 'Retornos Diários',
                'Drawdown', 'Distribuição de Retornos',
                'Trades', 'Posições'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Evolução do Portfolio
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['portfolio_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        # Linha de capital inicial
        fig.add_hline(
            y=self.initial_capital,
            line_dash="dash",
            line_color="gray",
            row=1, col=1
        )
        
        # 2. Retornos Diários
        daily_returns = df['daily_returns'].dropna() * 100
        fig.add_trace(
            go.Scatter(
                x=daily_returns.index,
                y=daily_returns,
                mode='lines',
                name='Daily Returns (%)',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        # 3. Drawdown
        running_max = df['portfolio_value'].expanding().max()
        drawdown = (df['portfolio_value'] - running_max) / running_max * 100
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=drawdown,
                mode='lines',
                name='Drawdown (%)',
                fill='tonexty',
                line=dict(color='red')
            ),
            row=2, col=1
        )
        
        # 4. Distribuição de Retornos
        fig.add_trace(
            go.Histogram(
                x=daily_returns,
                name='Returns Distribution',
                nbinsx=30
            ),
            row=2, col=2
        )
        
        # 5. Trades (Buy/Sell points)
        buy_trades = [t for t in self.trades if t.order_type == OrderType.BUY]
        sell_trades = [t for t in self.trades if t.order_type == OrderType.SELL]
        
        if buy_trades:
            fig.add_trace(
                go.Scatter(
                    x=[t.timestamp for t in buy_trades],
                    y=[t.price for t in buy_trades],
                    mode='markers',
                    name='Buy Orders',
                    marker=dict(color='green', symbol='triangle-up', size=8)
                ),
                row=3, col=1
            )
        
        if sell_trades:
            fig.add_trace(
                go.Scatter(
                    x=[t.timestamp for t in sell_trades],
                    y=[t.price for t in sell_trades],
                    mode='markers',
                    name='Sell Orders',
                    marker=dict(color='red', symbol='triangle-down', size=8)
                ),
                row=3, col=1
            )
        
        # Adicionar linha de preço
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['close'],
                mode='lines',
                name='Price',
                line=dict(color='black', width=1)
            ),
            row=3, col=1
        )
        
        # 6. Posições
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['positions_value'],
                mode='lines',
                name='Positions Value',
                line=dict(color='orange')
            ),
            row=3, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['cash'],
                mode='lines',
                name='Cash',
                line=dict(color='purple')
            ),
            row=3, col=2
        )
        
        # Atualizar layout
        fig.update_layout(
            height=900,
            title=f"Backtest Results - Total Return: {self.results['total_return_pct']:.2f}%",
            showlegend=True
        )
        
        return fig
    
    def export_results(self, filename: str):
        """
        Exporta resultados para arquivo
        
        Args:
            filename: Nome do arquivo
        """
        if not self.results:
            print("Nenhum resultado para exportar")
            return
        
        # Preparar dados para export
        export_data = {
            'summary': {k: v for k, v in self.results.items() 
                       if not isinstance(v, (pd.DataFrame, list))},
            'trades': [
                {
                    'timestamp': t.timestamp.isoformat(),
                    'symbol': t.symbol,
                    'order_type': t.order_type.value,
                    'quantity': t.quantity,
                    'price': t.price,
                    'commission': t.commission,
                    'order_id': t.order_id
                }
                for t in self.trades
            ]
        }
        
        # Exportar portfolio history
        if 'portfolio_history' in self.results:
            df = self.results['portfolio_history']
            df.to_csv(f"{filename}_portfolio_history.csv")
        
        # Exportar summary
        import json
        with open(f"{filename}_summary.json", 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Resultados exportados para {filename}")


# Estratégias de exemplo
def simple_ma_strategy(engine: BacktestingEngine, current_data: pd.Series, 
                      short_window: int = 10, long_window: int = 30):
    """
    Estratégia simples de média móvel
    
    Args:
        engine: Engine de backtesting
        current_data: Dados atuais
        short_window: Janela da média móvel curta
        long_window: Janela da média móvel longa
    """
    # Obter dados históricos até o momento atual
    current_idx = engine.data.index.get_loc(engine.current_timestamp)
    
    if current_idx < long_window:
        return  # Não há dados suficientes
    
    # Calcular médias móveis
    historical_data = engine.data.iloc[max(0, current_idx - long_window + 1):current_idx + 1]
    short_ma = historical_data['close'].tail(short_window).mean()
    long_ma = historical_data['close'].tail(long_window).mean()
    
    current_price = current_data['close']
    current_position = engine.positions.get(engine.symbol, Position(engine.symbol, 0, 0, engine.current_timestamp))
    
    # Sinais de trading
    if short_ma > long_ma and current_position.quantity == 0:
        # Sinal de compra - média curta cruzou acima da longa
        buy_quantity = engine.cash * 0.95 / current_price  # Usar 95% do cash disponível
        engine.place_order(OrderType.BUY, buy_quantity)
    
    elif short_ma < long_ma and current_position.quantity > 0:
        # Sinal de venda - média curta cruzou abaixo da longa
        engine.place_order(OrderType.SELL, current_position.quantity)


def rsi_strategy(engine: BacktestingEngine, current_data: pd.Series, 
                rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
    """
    Estratégia baseada no RSI
    
    Args:
        engine: Engine de backtesting
        current_data: Dados atuais
        rsi_period: Período do RSI
        oversold: Nível de sobrevenda
        overbought: Nível de sobrecompra
    """
    current_idx = engine.data.index.get_loc(engine.current_timestamp)
    
    if current_idx < rsi_period:
        return
    
    # Calcular RSI
    historical_data = engine.data.iloc[max(0, current_idx - rsi_period):current_idx + 1]
    closes = historical_data['close']
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    current_price = current_data['close']
    current_position = engine.positions.get(engine.symbol, Position(engine.symbol, 0, 0, engine.current_timestamp))
    
    # Sinais de trading
    if current_rsi < oversold and current_position.quantity == 0:
        # Sinal de compra - RSI em sobrevenda
        buy_quantity = engine.cash * 0.95 / current_price
        engine.place_order(OrderType.BUY, buy_quantity)
    
    elif current_rsi > overbought and current_position.quantity > 0:
        # Sinal de venda - RSI em sobrecompra
        engine.place_order(OrderType.SELL, current_position.quantity)
