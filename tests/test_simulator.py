#!/usr/bin/env python3
"""
Testes para o simulador da Binance
"""
import sys
import os
import unittest
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_simulator import BinanceSimulator

class TestBinanceSimulator(unittest.TestCase):
    """Testes para o simulador da Binance"""
    
    def setUp(self):
        """Inicializa o simulador antes de cada teste"""
        self.simulator = BinanceSimulator()
    
    def test_test_connection(self):
        """Testa se a conexão simulada funciona"""
        self.assertTrue(self.simulator.test_connection())
    
    def test_get_account_info(self):
        """Testa se o simulador retorna informações da conta"""
        account_info = self.simulator.get_account_info()
        self.assertIn('balances', account_info)
        self.assertIn('updateTime', account_info)
        
        # Verifica se temos os ativos esperados no saldo
        assets = [balance['asset'] for balance in account_info['balances']]
        expected_assets = ['USDT', 'BTC', 'ETH', 'BRL']
        for asset in expected_assets:
            self.assertIn(asset, assets)
    
    def test_get_ticker_price(self):
        """Testa se o simulador retorna preços de ticker"""
        ticker = self.simulator.get_ticker_price("BTC/BRL")
        self.assertIn('symbol', ticker)
        self.assertIn('price', ticker)
        self.assertEqual(ticker['symbol'], 'BTCBRL')
        
        # Verifica se o preço é um valor numérico
        price = float(ticker['price'])
        self.assertTrue(135000 <= price <= 165000)  # Esperamos variação de ±10% do preço base
    
    def test_get_klines(self):
        """Testa se o simulador retorna dados de klines (candles)"""
        klines = self.simulator.get_klines("BTC/BRL", "1h", 10)
        self.assertEqual(len(klines), 10)
        
        # Verifica estrutura de um kline
        kline = klines[0]
        self.assertEqual(len(kline), 12)  # 12 campos esperados
        
        # Verifica se timestamps fazem sentido
        self.assertTrue(kline[0] < kline[6])  # openTime < closeTime
    
    def test_create_order(self):
        """Testa criação de ordens simuladas"""
        order = self.simulator.create_order(
            symbol="BTC/BRL",
            side="buy",
            type="limit",
            quantity=0.01,
            price=150000
        )
        
        self.assertIn('orderId', order)
        self.assertEqual(order['symbol'], 'BTCBRL')
        self.assertEqual(order['side'], 'BUY')
        self.assertEqual(order['type'], 'LIMIT')
        self.assertEqual(float(order['origQty']), 0.01)
        self.assertEqual(float(order['price']), 150000)
        
        # Verifica se o order_id foi salvo
        order_id = order['orderId']
        self.assertIn(order_id, self.simulator.orders)
    
    def test_get_order(self):
        """Testa recuperação de ordens simuladas"""
        # Primeiro cria uma ordem
        order = self.simulator.create_order(
            symbol="ETH/BRL",
            side="sell",
            type="limit",
            quantity=0.1,
            price=8500
        )
        
        order_id = order['orderId']
        
        # Recupera a ordem
        retrieved_order = self.simulator.get_order("ETH/BRL", order_id)
        
        # Verifica se os dados são os mesmos
        self.assertEqual(retrieved_order['orderId'], order_id)
        self.assertEqual(retrieved_order['symbol'], 'ETHBRL')
        self.assertEqual(retrieved_order['side'], 'SELL')
    
    def test_order_not_found(self):
        """Testa erro ao buscar ordem inexistente"""
        with self.assertRaises(ValueError):
            self.simulator.get_order("BTC/BRL", 999999)

if __name__ == '__main__':
    unittest.main()
