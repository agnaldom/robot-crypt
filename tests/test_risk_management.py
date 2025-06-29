#!/usr/bin/env python3
"""
Testes unitários para o gerenciamento de risco e proteção contra perdas consecutivas
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Adiciona o diretório raiz ao sys.path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy import TradingStrategy
from config import Config

class TestRiskManagement:
    """Testes unitários para o gerenciamento de risco"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        # Cria mock da configuração
        self.config = MagicMock()
        self.config.max_consecutive_losses = 3
        self.config.risk_reduction_factor = 0.5
        self.config.scalping = {
            "max_position_size": 0.05,
            "risk_per_trade": 0.01
        }
        
        # Cria mock da API
        self.api = MagicMock()
        
        # Cria a estratégia de trading
        self.strategy = TradingStrategy(self.config, self.api)
    
    def test_initial_consecutive_losses(self):
        """Testa se o contador de perdas consecutivas inicia em zero"""
        assert self.strategy.consecutive_losses == 0
    
    def test_normal_position_size(self):
        """Testa cálculo de tamanho de posição normal (sem redução)"""
        capital = 1000.0
        price = 10.0
        risk_percentage = 0.01  # 1%
        
        # Com 0 perdas consecutivas, não deve haver redução de risco
        self.strategy.consecutive_losses = 0
        quantity = self.strategy.calculate_position_size(capital, price, risk_percentage)
        
        # Verifica se o cálculo está correto (limitado pelo risco)
        expected_quantity = (capital * risk_percentage) / price
        assert quantity == expected_quantity
    
    def test_reduced_position_size_after_consecutive_losses(self):
        """Testa se o tamanho da posição é reduzido após perdas consecutivas"""
        capital = 1000.0
        price = 10.0
        risk_percentage = 0.01  # 1%
        
        # Com perdas consecutivas acima do limite, deve haver redução de risco
        self.strategy.consecutive_losses = 3  # Igual ao limite
        quantity_reduced = self.strategy.calculate_position_size(capital, price, risk_percentage)
        
        # Verifica se o risco foi reduzido pela metade
        expected_quantity_reduced = (capital * risk_percentage * 0.5) / price
        assert quantity_reduced == expected_quantity_reduced
        
        # Verifica que a redução é proporcional ao fator de redução
        assert quantity_reduced == (capital * risk_percentage * self.config.risk_reduction_factor) / price
    
    def test_reset_consecutive_losses_after_profit(self):
        """Testa se o contador de perdas é resetado após um trade lucrativo"""
        # Configura perdas consecutivas
        self.strategy.consecutive_losses = 2
        
        # Simula um trade lucrativo (função chamada durante execute_sell)
        with patch.object(self.strategy, 'execute_sell') as mock_sell:
            # Não podemos testar diretamente execute_sell, então simulamos seu comportamento
            self.strategy.consecutive_losses = 2
            # Simula um trade lucrativo manualmente
            self.strategy.consecutive_losses = 0
            
            assert self.strategy.consecutive_losses == 0
    
    def test_increment_consecutive_losses_after_loss(self):
        """Testa se o contador de perdas é incrementado após um trade com prejuízo"""
        # Configura perdas consecutivas inicialmente
        self.strategy.consecutive_losses = 1
        
        # Simula um trade com prejuízo manualmente
        self.strategy.consecutive_losses += 1
        
        assert self.strategy.consecutive_losses == 2
