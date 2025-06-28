#!/usr/bin/env python3
"""
Módulo de simulação da API da Binance para testes sem conexão real
"""
import logging
import random
import time
from datetime import datetime

class BinanceSimulator:
    """Classe para simular a API da Binance para testes"""
    
    def __init__(self):
        """Inicializa o simulador"""
        self.logger = logging.getLogger("robot-crypt")
        self.logger.info("Inicializando simulador da Binance")
        
        # Dados simulados
        self.simulated_balance = {"USDT": 100.0, "BTC": 0.001, "ETH": 0.01, "BRL": 500.0}
        self.orders = {}
        self.next_order_id = 1000
        self.base_prices = {
            "BTCBRL": 150000.0, "ETHBRL": 8500.0, "SHIBUSDT": 0.00001,
            "FLOKIUSDT": 0.00002, "BTCUSDT": 30000.0, "ETHUSDT": 1700.0
        }
    
    def test_connection(self):
        """Simula teste de conexão"""
        self.logger.info("Simulação: Teste de conexão bem-sucedido")
        return True
        
    def get_account_info(self):
        """Retorna informações simuladas da conta"""
        self.logger.info("Simulação: Obtendo informações da conta")
        balances = []
        for asset, amount in self.simulated_balance.items():
            balances.append({
                "asset": asset,
                "free": str(amount * 0.8),  # 80% livre
                "locked": str(amount * 0.2)  # 20% em ordens
            })
        
        return {"balances": balances, "updateTime": int(time.time() * 1000)}
        
    def get_ticker_price(self, symbol):
        """Retorna preço simulado para um par"""
        clean_symbol = symbol.replace('/', '')
        base_price = self.base_prices.get(clean_symbol, 100.0)
        variation = random.uniform(-0.02, 0.02)
        price = base_price * (1 + variation)
        
        self.logger.info(f"Simulação: Preço de {symbol}: {price:.2f}")
        return {"symbol": clean_symbol, "price": str(price)}
    
    def get_klines(self, symbol, interval, limit=500):
        """Gera dados de candlestick simulados"""
        self.logger.info(f"Simulação: Obtendo {limit} candles para {symbol}")
        klines = []
        for i in range(limit):
            klines.append([
                int(time.time() * 1000) - (limit - i) * 60000,  # tempo
                "100.0",  # open
                "105.0",  # high
                "95.0",   # low
                "102.0",  # close
                "1000.0", # volume
                int(time.time() * 1000) - (limit - i - 1) * 60000,  # tempo de fechamento
                "102000.0",  # volume em quote
                100,          # número de trades
                "500.0",      # volume de compra
                "51000.0",    # volume de compra em quote
                "0"           # ignore
            ])
        return klines
    
    def create_order(self, symbol, side, type, quantity=None, price=None, time_in_force=None):
        """Simula a criação de uma ordem"""
        order_id = self.next_order_id
        self.next_order_id += 1
        
        self.logger.info(f"Simulação: Criando ordem {side} para {symbol} - {quantity}@{price}")
        
        order = {
            "orderId": order_id,
            "symbol": symbol.replace('/', ''),
            "status": "FILLED",
            "price": str(price) if price else "0.0",
            "origQty": str(quantity) if quantity else "0.0",
            "side": side.upper(),
            "type": type.upper()
        }
        
        self.orders[order_id] = order
        return order
    
    def get_order(self, symbol, order_id):
        """Retorna informações sobre uma ordem simulada"""
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            raise ValueError(f"Ordem {order_id} não encontrada")
    
    def get_exchange_info(self):
        """Retorna informações simuladas sobre a exchange"""
        return {"serverTime": int(time.time() * 1000)}
    
    def get_server_time(self):
        """Retorna o tempo simulado do servidor"""
        return {"serverTime": int(time.time() * 1000)}
