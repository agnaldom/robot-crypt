#!/usr/bin/env python3
"""
Testes para corrigir erros identificados nos logs - Enhanced Strategy
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.enhanced_strategy import EnhancedTradingStrategy, EnhancedScalpingStrategy
from src.core.config import Config


class TestEnhancedTradingStrategyErrors:
    """Testes para corrigir erros identificados na Enhanced Strategy"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_config = Mock(spec=Config)
        self.mock_binance_api = Mock()
        
        # Mock das configurações necessárias
        self.mock_config.scalping = {'risk_per_trade': 0.02}
        
        # Patches para evitar inicialização de componentes reais
        with patch('src.strategies.enhanced_strategy.get_llm_client'):
            with patch('src.strategies.enhanced_strategy.NewsIntegrator'):
                self.strategy = EnhancedTradingStrategy(self.mock_config, self.mock_binance_api)
    
    def test_combine_traditional_and_ai_analysis_handles_empty_signals(self):
        """Testa se _combine_traditional_and_ai_analysis trata lista vazia de sinais (Erro 5)"""
        traditional_result = (True, "buy", 50000.0)
        ai_signals = []  # Lista vazia
        risk_assessment = {"overall_risk": "medium", "risk_score": 0.5}
        ai_analysis = {"signals": []}
        
        result = self.strategy._combine_traditional_and_ai_analysis(
            traditional_result, ai_signals, risk_assessment, ai_analysis, "BTC/USDT"
        )
        
        # Deve retornar análise tradicional
        assert result == traditional_result
    
    def test_combine_traditional_and_ai_analysis_handles_invalid_signal_format(self):
        """Testa se _combine_traditional_and_ai_analysis trata formato inválido de sinais (Erro 3)"""
        traditional_result = (True, "buy", 50000.0)
        
        # Sinais com formato inválido (strings ao invés de dicts)
        invalid_signals = [
            "invalid_signal",
            {"signal_type": "buy", "confidence": 0.8, "reasoning": "Valid signal"}
        ]
        
        risk_assessment = {"overall_risk": "medium", "risk_score": 0.5}
        ai_analysis = {"signals": invalid_signals}
        
        # Mock para simular o comportamento do extract_ai_signals
        with patch.object(self.strategy, 'extract_ai_signals') as mock_extract:
            mock_extract.return_value = []  # Retorna lista vazia devido ao formato inválido
            
            result = self.strategy._combine_traditional_and_ai_analysis(
                traditional_result, [], risk_assessment, ai_analysis, "BTC/USDT"
            )
            
            # Deve retornar análise tradicional
            assert result == traditional_result
    
    def test_combine_traditional_and_ai_analysis_handles_dict_signals(self):
        """Testa se _combine_traditional_and_ai_analysis trata sinais dict corretamente (Erro 3)"""
        traditional_result = (True, "buy", 50000.0)
        
        # Sinais válidos no formato dict
        valid_signals = [
            {"signal_type": "buy", "confidence": 0.8, "reasoning": "Strong bullish signal"}
        ]
        
        risk_assessment = {"overall_risk": "low", "risk_score": 0.3}
        ai_analysis = {"signals": valid_signals}
        
        result = self.strategy._combine_traditional_and_ai_analysis(
            traditional_result, valid_signals, risk_assessment, ai_analysis, "BTC/USDT"
        )
        
        # Deve retornar decisão baseada na concordância
        assert result[0] == True  # should_trade
        assert result[1] == "buy"  # action
        assert result[2] == 50000.0  # price
    
    def test_combine_traditional_and_ai_analysis_handles_conflicting_signals(self):
        """Testa se _combine_traditional_and_ai_analysis trata sinais conflitantes"""
        traditional_result = (True, "buy", 50000.0)
        
        # Sinal IA conflitante (sell vs buy tradicional)
        conflicting_signals = [
            {"signal_type": "sell", "confidence": 0.7, "reasoning": "Bearish signal"}
        ]
        
        risk_assessment = {"overall_risk": "medium", "risk_score": 0.5}
        ai_analysis = {"signals": conflicting_signals}
        
        result = self.strategy._combine_traditional_and_ai_analysis(
            traditional_result, conflicting_signals, risk_assessment, ai_analysis, "BTC/USDT"
        )
        
        # Com confiança moderada (0.7 < 0.85), deve não executar trade
        assert result[0] == False  # should_trade
        assert result[1] == None  # action
        assert result[2] == None  # price
    
    def test_combine_traditional_and_ai_analysis_handles_high_confidence_conflict(self):
        """Testa se _combine_traditional_and_ai_analysis trata conflito com alta confiança"""
        traditional_result = (True, "buy", 50000.0)
        
        # Sinal IA com alta confiança
        high_confidence_signals = [
            {"signal_type": "sell", "confidence": 0.9, "reasoning": "Very strong bearish signal"}
        ]
        
        risk_assessment = {"overall_risk": "medium", "risk_score": 0.5}
        ai_analysis = {"signals": high_confidence_signals}
        
        result = self.strategy._combine_traditional_and_ai_analysis(
            traditional_result, high_confidence_signals, risk_assessment, ai_analysis, "BTC/USDT"
        )
        
        # Com confiança alta (0.9 > 0.85), deve seguir IA
        assert result[0] == True  # should_trade
        assert result[1] == "sell"  # action (IA)
        assert result[2] == 50000.0  # price
    
    def test_combine_traditional_and_ai_analysis_handles_high_risk(self):
        """Testa se _combine_traditional_and_ai_analysis trata alto risco"""
        traditional_result = (True, "buy", 50000.0)
        
        # Sinais válidos mas com alto risco
        valid_signals = [
            {"signal_type": "buy", "confidence": 0.8, "reasoning": "Bullish signal"}
        ]
        
        risk_assessment = {"overall_risk": "high", "risk_score": 0.9}
        ai_analysis = {"signals": valid_signals}
        
        result = self.strategy._combine_traditional_and_ai_analysis(
            traditional_result, valid_signals, risk_assessment, ai_analysis, "BTC/USDT"
        )
        
        # Deve executar mas com cautela (reduzirá posição no execute_buy/sell)
        assert result[0] == True  # should_trade
        assert result[1] == "buy"  # action
        assert result[2] == 50000.0  # price
    
    def test_combine_traditional_and_ai_analysis_handles_exception(self):
        """Testa se _combine_traditional_and_ai_analysis trata exceções"""
        traditional_result = (True, "buy", 50000.0)
        
        # Simula exceção durante processamento
        with patch.object(self.strategy, 'logger') as mock_logger:
            # Force uma exceção modificando o ai_signals para um tipo inválido
            ai_signals = None  # Tipo inválido que causará exceção
            risk_assessment = {"overall_risk": "medium", "risk_score": 0.5}
            ai_analysis = {"signals": []}
            
            result = self.strategy._combine_traditional_and_ai_analysis(
                traditional_result, ai_signals, risk_assessment, ai_analysis, "BTC/USDT"
            )
            
            # Deve retornar análise tradicional como fallback
            assert result == traditional_result
            # Deve logar erro
            mock_logger.error.assert_called_once()
    
    def test_get_decision_reasoning_handles_empty_ai_signals(self):
        """Testa se _get_decision_reasoning trata sinais IA vazios"""
        traditional_result = (True, "buy", 50000.0)
        ai_signals = []
        risk_assessment = {"overall_risk": "medium"}
        final_decision = (True, "buy", 50000.0)
        
        reasoning = self.strategy._get_decision_reasoning(
            traditional_result, ai_signals, risk_assessment, final_decision
        )
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "não encontrou sinais" in reasoning.lower()
    
    def test_get_decision_reasoning_handles_concordance(self):
        """Testa se _get_decision_reasoning identifica concordância"""
        traditional_result = (True, "buy", 50000.0)
        ai_signals = [{"signal_type": "buy", "confidence": 0.8}]
        risk_assessment = {"overall_risk": "medium"}
        final_decision = (True, "buy", 50000.0)
        
        reasoning = self.strategy._get_decision_reasoning(
            traditional_result, ai_signals, risk_assessment, final_decision
        )
        
        assert isinstance(reasoning, str)
        assert "concordância" in reasoning.lower()
        assert "0.8" in reasoning or "80%" in reasoning
    
    def test_get_decision_reasoning_handles_exception(self):
        """Testa se _get_decision_reasoning trata exceções"""
        traditional_result = None  # Valor inválido que causará exceção
        ai_signals = []
        risk_assessment = {}
        final_decision = (False, None, None)
        
        reasoning = self.strategy._get_decision_reasoning(
            traditional_result, ai_signals, risk_assessment, final_decision
        )
        
        assert isinstance(reasoning, str)
        assert "análise combinada" in reasoning.lower()
    
    def test_validate_analysis_data_handles_none_input(self):
        """Testa se _validate_analysis_data trata entrada None (Erro 2)"""
        result = self.strategy._validate_analysis_data(None, "BTC/USDT")
        
        assert isinstance(result, dict)
        assert 'signals' in result
        assert 'analysis_duration' in result
        assert 'traditional_analysis' in result
        assert 'ai_analysis' in result
        assert 'risk_assessment' in result
        assert 'market_sentiment' in result
        assert 'final_decision' in result
    
    def test_validate_analysis_data_handles_invalid_type(self):
        """Testa se _validate_analysis_data trata tipo inválido (Erro 2)"""
        result = self.strategy._validate_analysis_data("invalid_string", "BTC/USDT")
        
        assert isinstance(result, dict)
        assert 'signals' in result
        assert result['signals'] == []
    
    def test_validate_analysis_data_handles_missing_fields(self):
        """Testa se _validate_analysis_data preenche campos ausentes"""
        incomplete_data = {
            'signals': ['some_signal'],
            # Faltam outros campos
        }
        
        result = self.strategy._validate_analysis_data(incomplete_data, "BTC/USDT")
        
        assert isinstance(result, dict)
        assert 'analysis_duration' in result
        assert 'traditional_analysis' in result
        assert 'ai_analysis' in result
        assert 'risk_assessment' in result
        assert 'market_sentiment' in result
        assert 'final_decision' in result
        assert result['analysis_duration'] == 0.0
    
    def test_validate_analysis_data_preserves_valid_data(self):
        """Testa se _validate_analysis_data preserva dados válidos"""
        valid_data = {
            'signals': [{'signal_type': 'buy', 'confidence': 0.8}],
            'analysis_duration': 2.5,
            'traditional_analysis': {'should_trade': True, 'action': 'buy'},
            'ai_analysis': {'signals': [], 'best_signal': None},
            'risk_assessment': {'overall_risk': 'low'},
            'market_sentiment': {'sentiment_score': 0.5},
            'final_decision': {'should_trade': True, 'action': 'buy'}
        }
        
        result = self.strategy._validate_analysis_data(valid_data, "BTC/USDT")
        
        assert result['signals'] == valid_data['signals']
        assert result['analysis_duration'] == valid_data['analysis_duration']
        assert result['traditional_analysis'] == valid_data['traditional_analysis']
    
    def test_create_fallback_analysis_data_structure(self):
        """Testa se _create_fallback_analysis_data retorna estrutura correta"""
        result = self.strategy._create_fallback_analysis_data("BTC/USDT")
        
        assert isinstance(result, dict)
        assert result['signals'] == []
        assert result['analysis_duration'] == 0.0
        assert isinstance(result['traditional_analysis'], dict)
        assert isinstance(result['ai_analysis'], dict)
        assert isinstance(result['risk_assessment'], dict)
        assert isinstance(result['market_sentiment'], dict)
        assert isinstance(result['final_decision'], dict)
        assert "BTC/USDT" in result['final_decision']['reasoning']
    
    def test_adjust_position_size_for_risk_basic_cases(self):
        """Testa se adjust_position_size_for_risk funciona com casos básicos"""
        base_size = 1000.0
        
        # Teste com risco baixo
        low_risk = {"overall_risk": "low", "risk_score": 0.2}
        result = self.strategy.adjust_position_size_for_risk(base_size, low_risk)
        assert result > base_size  # Deve aumentar posição
        
        # Teste com risco médio
        medium_risk = {"overall_risk": "medium", "risk_score": 0.5}
        result = self.strategy.adjust_position_size_for_risk(base_size, medium_risk)
        assert result == base_size  # Deve manter posição
        
        # Teste com risco alto
        high_risk = {"overall_risk": "high", "risk_score": 0.8}
        result = self.strategy.adjust_position_size_for_risk(base_size, high_risk)
        assert result < base_size  # Deve reduzir posição
    
    def test_adjust_position_size_for_risk_handles_exception(self):
        """Testa se adjust_position_size_for_risk trata exceções"""
        base_size = 1000.0
        invalid_risk = None  # Tipo inválido que causará exceção
        
        with patch.object(self.strategy, 'logger') as mock_logger:
            result = self.strategy.adjust_position_size_for_risk(base_size, invalid_risk)
            
            # Deve retornar tamanho original
            assert result == base_size
            # Deve logar erro
            mock_logger.error.assert_called_once()
    
    def test_adjust_position_size_for_risk_disabled(self):
        """Testa se adjust_position_size_for_risk respeita configuração desabilitada"""
        # Desabilita ajuste de risco
        self.strategy.analysis_config['risk_adjustment'] = False
        
        base_size = 1000.0
        high_risk = {"overall_risk": "high", "risk_score": 0.9}
        
        result = self.strategy.adjust_position_size_for_risk(base_size, high_risk)
        
        # Deve retornar tamanho original (sem ajuste)
        assert result == base_size


class TestEnhancedScalpingStrategyErrors:
    """Testes específicos para Enhanced Scalping Strategy"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_config = Mock(spec=Config)
        self.mock_binance_api = Mock()
        
        # Mock das configurações necessárias
        self.mock_config.scalping = {'risk_per_trade': 0.02}
        
        # Patches para evitar inicialização de componentes reais
        with patch('src.strategies.enhanced_strategy.get_llm_client'):
            with patch('src.strategies.enhanced_strategy.NewsIntegrator'):
                with patch('src.strategies.strategy.ScalpingStrategy.__init__'):
                    self.strategy = EnhancedScalpingStrategy(self.mock_config, self.mock_binance_api)
    
    def test_analyze_market_with_disabled_ai(self):
        """Testa se analyze_market funciona com IA desabilitada"""
        self.strategy.analysis_enabled = False
        
        # Mock do método pai
        with patch('src.strategies.strategy.ScalpingStrategy.analyze_market') as mock_super:
            mock_super.return_value = (True, "buy", 50000.0)
            
            # Mock do notifier
            mock_notifier = Mock()
            mock_notifier.notify_analysis_report = Mock()
            
            result = self.strategy.analyze_market("BTC/USDT", mock_notifier)
            
            # Deve chamar análise tradicional
            mock_super.assert_called_once()
            assert result == (True, "buy", 50000.0)
    
    def test_analyze_market_with_no_ai_analysis(self):
        """Testa se analyze_market funciona quando análise IA não está disponível"""
        self.strategy.analysis_enabled = True
        
        # Mock do método pai
        with patch('src.strategies.strategy.ScalpingStrategy.analyze_market') as mock_super:
            mock_super.return_value = (True, "buy", 50000.0)
            
            # Mock da análise IA retornando None
            with patch.object(self.strategy, 'get_ai_analysis') as mock_ai:
                mock_ai.return_value = None
                
                mock_notifier = Mock()
                mock_notifier.notify_analysis_report = Mock()
                
                result = self.strategy.analyze_market("BTC/USDT", mock_notifier)
                
                # Deve usar análise tradicional
                mock_super.assert_called_once()
                assert result == (True, "buy", 50000.0)
    
    def test_analyze_market_handles_notification_error(self):
        """Testa se analyze_market trata erro de notificação (Erro 2)"""
        self.strategy.analysis_enabled = False
        
        # Mock do método pai
        with patch('src.strategies.strategy.ScalpingStrategy.analyze_market') as mock_super:
            mock_super.return_value = (True, "buy", 50000.0)
            
            # Mock do notifier que gera exceção
            mock_notifier = Mock()
            mock_notifier.notify_analysis_report = Mock(side_effect=Exception("Notification error"))
            
            with patch.object(self.strategy, 'logger') as mock_logger:
                result = self.strategy.analyze_market("BTC/USDT", mock_notifier)
                
                # Deve funcionar normalmente apesar do erro de notificação
                assert result == (True, "buy", 50000.0)
                # Deve logar erro
                mock_logger.error.assert_called()
    
    def test_execute_buy_with_risk_adjustment(self):
        """Testa se execute_buy aplica ajuste de risco"""
        # Mock da análise IA
        mock_ai_analysis = {
            'risk_analysis': {
                'overall_risk': 'high',
                'risk_score': 0.8
            }
        }
        
        # Mock do método pai
        with patch('src.strategies.strategy.ScalpingStrategy.execute_buy') as mock_super:
            mock_super.return_value = (True, {"quantity": 0.001})
            
            with patch.object(self.strategy, 'get_ai_analysis') as mock_ai:
                mock_ai.return_value = mock_ai_analysis
                
                # Mock das configurações
                self.mock_binance_api.get_account_info.return_value = {"balances": []}
                self.mock_config.get_balance.return_value = 1000.0
                
                result = self.strategy.execute_buy("BTC/USDT", 50000.0)
                
                # Deve executar compra
                mock_super.assert_called_once()
                assert result[0] == True
    
    def test_execute_buy_handles_exception(self):
        """Testa se execute_buy trata exceções"""
        # Mock que gera exceção
        with patch.object(self.strategy, 'get_ai_analysis') as mock_ai:
            mock_ai.side_effect = Exception("AI analysis error")
            
            # Mock do método pai
            with patch('src.strategies.strategy.ScalpingStrategy.execute_buy') as mock_super:
                mock_super.return_value = (True, {"quantity": 0.001})
                
                with patch.object(self.strategy, 'logger') as mock_logger:
                    result = self.strategy.execute_buy("BTC/USDT", 50000.0)
                    
                    # Deve usar método tradicional como fallback
                    mock_super.assert_called_once()
                    assert result[0] == True
                    # Deve logar erro
                    mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
