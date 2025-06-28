#!/usr/bin/env python3
"""
Módulo de utilidades para Robot-Crypt
"""
import os
import logging
import random
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

def setup_logger(log_level=logging.INFO):
    """Configura e retorna logger com formatação apropriada"""
    # Cria diretório de logs se não existir
    log_dir = Path.home() / ".robot-crypt" / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Nome do arquivo de log com timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"robot-crypt-{timestamp}.log"
    
    # Configura logger
    logger = logging.getLogger("robot-crypt")
    logger.setLevel(log_level)
    
    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers = []
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formato dos logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def calculate_fees(value, fee_rate=0.001):
    """Calcula taxas da Binance para um valor"""
    return value * fee_rate
    
def calculate_profit(entry_price, exit_price, quantity, fee_rate=0.001):
    """Calcula o lucro líquido de uma operação após taxas"""
    # Valor bruto de entrada e saída
    entry_value = entry_price * quantity
    exit_value = exit_price * quantity
    
    # Cálculo de taxas (entrada e saída)
    entry_fee = calculate_fees(entry_value, fee_rate)
    exit_fee = calculate_fees(exit_value, fee_rate)
    total_fees = entry_fee + exit_fee
    
    # Lucro bruto e líquido
    gross_profit = exit_value - entry_value
    net_profit = gross_profit - total_fees
    
    # Percentual de lucro após taxas
    profit_percentage = net_profit / entry_value
    
    return {
        'entry_value': entry_value,
        'exit_value': exit_value,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'total_fees': total_fees,
        'profit_percentage': profit_percentage
    }

def track_portfolio_performance(trades_history, initial_capital=100.0):
    """Acompanha performance do portfólio ao longo do tempo"""
    capital = initial_capital
    performance = []
    
    # Ordena trades por data
    sorted_trades = sorted(trades_history, key=lambda x: x['timestamp'])
    
    for trade in sorted_trades:
        # Atualiza capital após cada trade
        capital += trade['net_profit']
        
        # Registra desempenho
        performance.append({
            'timestamp': trade['timestamp'],
            'symbol': trade['symbol'],
            'action': trade['action'],
            'profit': trade['net_profit'],
            'capital': capital,
            'growth': (capital / initial_capital - 1) * 100  # Crescimento percentual
        })
    
    return performance

def calculate_profit(entry_price, exit_price, quantity, fee_rate=0.001):
    """Calcula o lucro real de uma operação considerando taxas
    
    Parameters:
    -----------
    entry_price : float
        Preço de compra
    exit_price : float
        Preço de venda
    quantity : float
        Quantidade negociada
    fee_rate : float
        Taxa por operação (padrão: 0.1%)
        
    Returns:
    --------
    dict
        Dicionário com valores de lucro bruto, taxas e lucro líquido
    """
    # Valor total da compra e venda
    entry_value = entry_price * quantity
    exit_value = exit_price * quantity
    
    # Lucro bruto
    gross_profit = exit_value - entry_value
    
    # Cálculo das taxas
    entry_fee = entry_value * fee_rate
    exit_fee = exit_value * fee_rate
    total_fees = entry_fee + exit_fee
    
    # Lucro líquido
    net_profit = gross_profit - total_fees
    
    # Porcentagem de lucro
    profit_percent = (net_profit / entry_value) * 100
    
    return {
        'entry_value': entry_value,
        'exit_value': exit_value,
        'gross_profit': gross_profit,
        'total_fees': total_fees,
        'net_profit': net_profit,
        'profit_percent': profit_percent
    }

class BinanceSimulator:
    """Classe para simular a API da Binance para testes"""
    
    def __init__(self):
        """Inicializa o simulador"""
        self.logger = logging.getLogger("robot-crypt")
        self.logger.info("Inicializando simulador da Binance")
        
        # Dados simulados
        self.simulated_balance = {
            "USDT": 100.0,
            "BTC": 0.001,
            "ETH": 0.01,
            "BRL": 500.0,
        }
        
        # Armazena ordens simuladas
        self.orders = {}
        self.next_order_id = 1000
        
        # Preços base simulados
        self.base_prices = {
            "BTCBRL": 150000.0,
            "ETHBRL": 8500.0,
            "SHIBUSDT": 0.00001,
            "FLOKIUSDT": 0.00002,
            "BTCUSDT": 30000.0,
            "ETHUSDT": 1700.0,
        }
    
    def test_connection(self):
        """Simula teste de conexão"""
        self.logger.info("Simulando teste de conexão - sempre retorna sucesso")
        time.sleep(0.5)  # Simula latência da rede
        return True
    
    def get_account_info(self):
        """Retorna informações simuladas da conta"""
        self.logger.info("Retornando informações simuladas da conta")
        
        # Formata os dados no mesmo formato que a API da Binance
        balances = []
        for asset, amount in self.simulated_balance.items():
            balances.append({
                "asset": asset,
                "free": str(amount * 0.8),  # 80% livre
                "locked": str(amount * 0.2)  # 20% bloqueado (simulando ordens abertas)
            })
        
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": balances
        }
    
    def get_ticker_price(self, symbol):
        """Retorna preço simulado para um par"""
        # Remove a / se presente
        clean_symbol = symbol.replace('/', '')
        
        # Verifica se temos um preço base para este símbolo
        base_price = self.base_prices.get(clean_symbol, 100.0)
        
        # Adiciona uma variação aleatória (-2% a +2%)
        variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + variation)
        
        self.logger.info(f"Preço simulado para {symbol}: {current_price:.8f}")
        
        return {
            "symbol": clean_symbol,
            "price": str(current_price)
        }
    
    def get_klines(self, symbol, interval, limit=500):
        """Gera dados de candlestick (OHLCV) simulados"""
        clean_symbol = symbol.replace('/', '')
        base_price = self.base_prices.get(clean_symbol, 100.0)
        
        # Determina o tamanho dos candles baseado no intervalo
        if interval == "1m":
            candle_size = 0.001
        elif interval == "5m":
            candle_size = 0.003
        elif interval == "15m":
            candle_size = 0.005
        elif interval == "1h":
            candle_size = 0.01
        elif interval == "4h":
            candle_size = 0.02
        elif interval == "1d":
            candle_size = 0.05
        else:
            candle_size = 0.01
        
        # Gera dados simulados para o número de candles solicitado
        klines = []
        current_time = int(time.time() * 1000)
        
        # Determina o timeframe em milissegundos
        if interval == "1m":
            timeframe = 60 * 1000
        elif interval == "5m":
            timeframe = 5 * 60 * 1000
        elif interval == "15m":
            timeframe = 15 * 60 * 1000
        elif interval == "1h":
            timeframe = 60 * 60 * 1000
        elif interval == "4h":
            timeframe = 4 * 60 * 60 * 1000
        elif interval == "1d":
            timeframe = 24 * 60 * 60 * 1000
        else:
            timeframe = 60 * 60 * 1000  # Padrão: 1h
        
        # Gera candles históricos
        for i in range(limit):
            # Cada candle tem: [open_time, open, high, low, close, volume, ...]
            candle_time = current_time - ((limit - i) * timeframe)
            
            # Gera preços simulados com tendência (80% chance de seguir tendência anterior)
            if i > 0:
                prev_close = float(klines[i-1][4])
                if random.random() < 0.8:
                    # Segue a tendência (alta ou baixa)
                    trend = (prev_close - float(klines[i-1][1])) / float(klines[i-1][1])  # (close-open)/open
                    open_price = prev_close
                    close_price = open_price * (1 + trend + random.uniform(-0.5, 0.5) * candle_size)
                else:
                    # Inverte a tendência
                    trend = (prev_close - float(klines[i-1][1])) / float(klines[i-1][1])
                    open_price = prev_close
                    close_price = open_price * (1 - trend + random.uniform(-0.5, 0.5) * candle_size)