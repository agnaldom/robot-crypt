#!/usr/bin/env python3
"""
Simulador robusto da API Binance para desenvolvimento e testes
"""
import random
import time
import logging
from datetime import datetime, timedelta

class BinanceSimulator:
    """Simulador da API Binance que não faz requisições reais"""
    
    def __init__(self):
        self.logger = logging.getLogger("robot-crypt")
        self.logger.info("Inicializando Simulador Binance (sem requisições reais)")
        
        # Preços simulados para pares comuns
        self.simulated_prices = {
            "BTCUSDT": 45000 + random.uniform(-5000, 5000),
            "ETHUSDT": 3000 + random.uniform(-500, 500),
            "BNBUSDT": 300 + random.uniform(-50, 50),
            "ADAUSDT": 0.5 + random.uniform(-0.1, 0.1),
            "DOGEUSDT": 0.08 + random.uniform(-0.02, 0.02),
            "SHIBUSDT": 0.000025 + random.uniform(-0.000005, 0.000005),
            "DOTUSDT": 20 + random.uniform(-5, 5),
            "LINKUSDT": 15 + random.uniform(-3, 3),
            "LTCUSDT": 180 + random.uniform(-30, 30),
            "XRPUSDT": 0.6 + random.uniform(-0.1, 0.1),
            "UNIUSDT": 25 + random.uniform(-5, 5),
            "SOLUSDT": 100 + random.uniform(-20, 20),
            "MATICUSDT": 1.2 + random.uniform(-0.3, 0.3),
            "AVAXUSDT": 80 + random.uniform(-15, 15),
            "ATOMUSDT": 12 + random.uniform(-3, 3),
        }
        
        # Saldos simulados
        self.simulated_balances = [
            {"asset": "USDT", "free": "100.00000000", "locked": "0.00000000"},
            {"asset": "BTC", "free": "0.00100000", "locked": "0.00000000"},
            {"asset": "ETH", "free": "0.01000000", "locked": "0.00000000"},
            {"asset": "BNB", "free": "0.50000000", "locked": "0.00000000"},
        ]
    
    def test_connection(self):
        """Simula teste de conexão sempre bem-sucedido"""
        self.logger.info("Simulador: Teste de conexão bem-sucedido")
        return True
    
    def get_account_info(self):
        """Simula informações da conta"""
        self.logger.info("Simulador: Obtendo informações da conta")
        return {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "balances": self.simulated_balances
        }
    
    def get_ticker_price(self, symbol):
        """Simula preço de ticker"""
        # Remove a barra se existir (BTC/USDT -> BTCUSDT)
        clean_symbol = symbol.replace("/", "")
        
        if clean_symbol in self.simulated_prices:
            # Adiciona pequena variação aleatória para simular movimento de preço
            base_price = self.simulated_prices[clean_symbol]
            variation = random.uniform(-0.02, 0.02)  # ±2% de variação
            current_price = base_price * (1 + variation)
            
            self.logger.debug(f"Simulador: Preço de {symbol} = {current_price:.8f}")
            return {"symbol": clean_symbol, "price": f"{current_price:.8f}"}
        else:
            self.logger.warning(f"Simulador: Par {symbol} não disponível em modo simulação")
            return None
    
    def get_klines(self, symbol, interval, limit=500):
        """Simula dados de candlestick"""
        self.logger.debug(f"Simulador: Gerando {limit} candles para {symbol}")
        
        # Remove a barra se existir
        clean_symbol = symbol.replace("/", "")
        
        # Preço base ou aleatório se não existir
        if clean_symbol in self.simulated_prices:
            base_price = self.simulated_prices[clean_symbol]
        else:
            base_price = random.uniform(0.001, 50000)
        
        klines = []
        current_time = int(time.time() * 1000)
        
        # Intervalo em milissegundos
        interval_ms = {
            "1m": 60000,
            "5m": 300000,
            "15m": 900000,
            "1h": 3600000,
            "4h": 14400000,
            "1d": 86400000
        }.get(interval, 3600000)
        
        for i in range(limit):
            timestamp = current_time - (limit - i) * interval_ms
            
            # Simula variação de preço
            price_change = random.uniform(-0.05, 0.05)  # ±5%
            open_price = base_price * (1 + price_change)
            close_price = open_price * (1 + random.uniform(-0.03, 0.03))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.uniform(1000, 100000)
            
            kline = [
                timestamp,                    # Open time
                f"{open_price:.8f}",         # Open price
                f"{high_price:.8f}",         # High price
                f"{low_price:.8f}",          # Low price
                f"{close_price:.8f}",        # Close price
                f"{volume:.8f}",             # Volume
                timestamp + interval_ms - 1, # Close time
                f"{volume * close_price:.8f}", # Quote asset volume
                random.randint(100, 1000),   # Number of trades
                f"{volume * 0.6:.8f}",       # Taker buy base asset volume
                f"{volume * close_price * 0.6:.8f}", # Taker buy quote asset volume
                "0"                          # Ignore
            ]
            klines.append(kline)
            
            # Atualiza preço base para próxima iteração
            base_price = close_price
        
        return klines
    
    def create_order(self, symbol, side, type, quantity=None, price=None, time_in_force=None):
        """Simula criação de ordem"""
        order_id = random.randint(1000000, 9999999)
        self.logger.info(f"Simulador: Ordem {side} {type} criada para {symbol} (ID: {order_id})")
        
        return {
            "symbol": symbol.replace("/", ""),
            "orderId": order_id,
            "orderListId": -1,
            "clientOrderId": f"sim_{int(time.time())}",
            "transactTime": int(time.time() * 1000),
            "price": str(price) if price else "0.00000000",
            "origQty": str(quantity) if quantity else "0.00000000",
            "executedQty": str(quantity) if quantity else "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "FILLED",
            "timeInForce": time_in_force or "GTC",
            "type": type.upper(),
            "side": side.upper(),
            "fills": []
        }
    
    def get_exchange_info(self):
        """Simula informações de exchange"""
        symbols = []
        for symbol in self.simulated_prices.keys():
            symbols.append({
                "symbol": symbol,
                "status": "TRADING",
                "baseAsset": symbol[:-4],  # Remove USDT
                "quoteAsset": "USDT",
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": True
            })
        
        return {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "symbols": symbols
        }
    
    def validate_trading_pairs(self, pairs):
        """Valida pares de trading simulados"""
        valid_pairs = []
        for pair in pairs:
            clean_pair = pair.replace("/", "") + "USDT"
            if clean_pair.replace("USDT", "") + "USDT" in self.simulated_prices:
                valid_pairs.append(pair)
            else:
                self.logger.warning(f"Simulador: Par {pair} não disponível")
        return valid_pairs
