#!/usr/bin/env python3
"""
Testes para as estratégias de trading
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy import ScalpingStrategy, SwingTradingStrategy
from config import Config
from binance_simulator import BinanceSimulator

class MockConfig:
    """Configuração simulada para testes"""
    def __init__(self):
        self.scalping = {
            'risk_per_trade': 0.01,
            'profit_target': 0.02,
            'stop_loss': 0.01,
            'max_position_size': 0.05,
            'trade_amount': 100.0
        }
        self.swing_trading = {
            'min_volume_increase': 0.3,
            'profit_target': 0.08,
            'stop_loss': 0.03,
            'max_hold_time': 48,
            'max_position_size': 0.05,
            'entry_delay': 60
        }
        self.max_trades_per_day = 3
    
    def get_balance(self, account_info):
        """Retorna saldo simulado"""
        return 1000.0

class TestScalpingStrategy(unittest.TestCase):
    """Testes para a estratégia de Scalping"""
    
    def setUp(self):
        """Inicializa a estratégia antes de cada teste"""
        self.config = MockConfig()
        self.binance = BinanceSimulator()
        self.strategy = ScalpingStrategy(self.config, self.binance)
    
    def test_check_trade_limit(self):
        """Testa limite de trades diário"""
        # Inicialmente deve permitir trades
        self.assertTrue(self.strategy.check_trade_limit())
        
        # Simula que já fizemos 3 trades hoje
        self.strategy.trades_today = 3
        self.assertFalse(self.strategy.check_trade_limit())
        
        # Reset para próximo teste
        self.strategy.trades_today = 0
    
    def test_position_size_calculation(self):
        """Testa cálculo do tamanho da posição"""
        # Cenário: Capital = 1000, Preço = 100, Risco = 1%
        capital = 1000.0
        price = 100.0
        risk = 0.01
        
        # Capital * risco / preço = 1000 * 0.01 / 100 = 0.1
        expected_quantity = 0.1
        
        quantity = self.strategy.calculate_position_size(capital, price, risk)
        self.assertAlmostEqual(quantity, expected_quantity, delta=0.001)
        
        # Testa limite de tamanho máximo (5%)
        risk = 0.1  # Risco muito alto
        # Deveria limitar a 5% (config.scalping["max_position_size"])
        # Capital * max_size / preço = 1000 * 0.05 / 100 = 0.5
        expected_quantity = 0.5
        quantity = self.strategy.calculate_position_size(capital, price, risk)
        self.assertAlmostEqual(quantity, expected_quantity, delta=0.001)
    
    def test_is_near_support(self):
        """Testa detecção de proximidade do suporte"""
        # Preço atual = 100, Suporte = 98.5, muito próximo (1.5%)
        price_data = {
            'current_price': 100.0,
            'support': 98.5,
            'resistance': 110.0
        }
        
        self.assertTrue(self.strategy.is_near_support(price_data))
        
        # Preço atual = 100, Suporte = 95, longe demais (5%)
        price_data = {
            'current_price': 100.0,
            'support': 95.0,
            'resistance': 110.0
        }
        
        self.assertFalse(self.strategy.is_near_support(price_data))
        
        # Preço atual = 100, Suporte = 100.5, acima do suporte (nem perto)
        price_data = {
            'current_price': 100.0,
            'support': 100.5,
            'resistance': 110.0
        }
        
        self.assertFalse(self.strategy.is_near_support(price_data))

class TestSwingTradingStrategy(unittest.TestCase):
    """Testes para a estratégia de Swing Trading"""
    
    def setUp(self):
        """Inicializa a estratégia antes de cada teste"""
        self.config = MockConfig()
        self.binance = BinanceSimulator()
        self.strategy = SwingTradingStrategy(self.config, self.binance)
    
    def test_check_volume_increase(self):
        """Testa detecção de aumento de volume"""
        # Mock da função para simular dados de volume
        self.strategy.get_volume_data = MagicMock(return_value={
            'avg_volume': 100000,
            'current_volume': 140000  # 40% acima da média
        })
        
        # Deve detectar aumento de volume acima do threshold (30%)
        self.assertTrue(self.strategy.check_volume_increase("SHIB/BRL"))
        
        # Altera o mock para simular volume baixo
        self.strategy.get_volume_data = MagicMock(return_value={
            'avg_volume': 100000,
            'current_volume': 110000  # 10% acima da média
        })
        
        # Não deve detectar aumento significativo de volume
        self.assertFalse(self.strategy.check_volume_increase("SHIB/BRL"))

if __name__ == '__main__':
    unittest.main()
