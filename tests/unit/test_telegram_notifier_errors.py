#!/usr/bin/env python3
"""
Testes para corrigir erros identificados nos logs - Telegram Notifier
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any, Optional

import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.notifications.telegram_notifier import TelegramNotifier


class TestTelegramNotifierErrors:
    """Testes para corrigir erros identificados no TelegramNotifier"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.token = "test_token"
        self.chat_id = "test_chat_id"
        self.notifier = TelegramNotifier(self.token, self.chat_id)
    
    def test_notify_analysis_report_handles_none_data(self):
        """Testa se notify_analysis_report trata dados None (Erro 2)"""
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            # Testa com dados None
            result = self.notifier.notify_analysis_report("BTC/USDT", None)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica se foi criada estrutura de fallback
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "0 sinais encontrados" in call_args
    
    def test_notify_analysis_report_handles_invalid_type_data(self):
        """Testa se notify_analysis_report trata dados com tipo inválido (Erro 2)"""
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            # Testa com dados de tipo inválido
            result = self.notifier.notify_analysis_report("BTC/USDT", "invalid_string")
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica se foi criada estrutura de fallback
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "0 sinais encontrados" in call_args
    
    def test_notify_analysis_report_handles_complete_data(self):
        """Testa se notify_analysis_report funciona com dados completos"""
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'buy',
                    'confidence': 0.8,
                    'reasoning': 'Strong bullish signal'
                }
            ],
            'analysis_duration': 2.5,
            'traditional_analysis': {
                'should_trade': True,
                'action': 'buy',
                'price': 50000.0
            },
            'ai_analysis': {
                'signals': [{'signal_type': 'buy'}],
                'best_signal': {'signal_type': 'buy', 'confidence': 0.8},
                'total_signals': 1,
                'valid_signals': 1
            },
            'risk_assessment': {
                'overall_risk': 'low',
                'risk_score': 0.3
            },
            'market_sentiment': {
                'sentiment_score': 0.6,
                'sentiment_label': 'bullish',
                'confidence': 0.7
            },
            'final_decision': {
                'should_trade': True,
                'action': 'buy',
                'reasoning': 'Strong bullish signals from both analyses'
            }
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "1 sinais encontrados" in call_args
            assert "BUY" in call_args
            # Verifica se a confiança está presente na mensagem (pode estar em formato diferente)
            assert "80%" in call_args or "0.8" in call_args or "80." in call_args
            assert "Strong bullish signal" in call_args
    
    def test_notify_analysis_report_handles_empty_signals(self):
        """Testa se notify_analysis_report trata lista vazia de sinais (Erro 5)"""
        analysis_data = {
            'signals': [],  # Lista vazia
            'analysis_duration': 1.0,
            'traditional_analysis': {
                'should_trade': False,
                'action': 'hold',
                'price': 50000.0
            },
            'ai_analysis': {
                'signals': [],
                'best_signal': None,
                'total_signals': 0,
                'valid_signals': 0
            },
            'risk_assessment': {
                'overall_risk': 'medium',
                'risk_score': 0.5
            },
            'market_sentiment': {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.1
            },
            'final_decision': {
                'should_trade': False,
                'action': 'hold',
                'reasoning': 'No clear opportunities found'
            }
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "0 sinais encontrados" in call_args
            assert "NENHUM SINAL DETECTADO" in call_args or "sem oportunidades" in call_args.lower()
            assert "consolidação" in call_args.lower()
    
    def test_notify_analysis_report_handles_multiple_signals(self):
        """Testa se notify_analysis_report trata múltiplos sinais corretamente"""
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'buy',
                    'confidence': 0.9,
                    'reasoning': 'Very strong bullish signal'
                },
                {
                    'signal_type': 'buy',
                    'confidence': 0.7,
                    'reasoning': 'Moderate bullish signal'
                },
                {
                    'signal_type': 'sell',
                    'confidence': 0.6,
                    'reasoning': 'Weak bearish signal'
                },
                {
                    'signal_type': 'buy',
                    'confidence': 0.8,
                    'reasoning': 'Strong bullish signal'
                }
            ],
            'analysis_duration': 3.0,
            'traditional_analysis': {
                'should_trade': True,
                'action': 'buy',
                'price': 50000.0
            },
            'ai_analysis': {
                'signals': [],
                'best_signal': {'signal_type': 'buy', 'confidence': 0.9},
                'total_signals': 4,
                'valid_signals': 4
            },
            'risk_assessment': {
                'overall_risk': 'low',
                'risk_score': 0.2
            },
            'market_sentiment': {
                'sentiment_score': 0.8,
                'sentiment_label': 'bullish',
                'confidence': 0.9
            },
            'final_decision': {
                'should_trade': True,
                'action': 'buy',
                'reasoning': 'Multiple strong bullish signals'
            }
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "4 sinais encontrados" in call_args
            
            # Deve mostrar apenas os primeiros 3 sinais
            assert "Sinal 1:" in call_args
            assert "Sinal 2:" in call_args
            assert "Sinal 3:" in call_args
            assert "... e mais 1 sinais" in call_args
    
    def test_notify_analysis_report_handles_missing_signal_fields(self):
        """Testa se notify_analysis_report trata campos ausentes nos sinais"""
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'buy',
                    'confidence': 0.8,
                    # Falta 'reasoning'
                },
                {
                    'confidence': 0.7,
                    'reasoning': 'Signal without type'
                    # Falta 'signal_type'
                },
                {
                    'signal_type': 'sell',
                    'reasoning': 'Signal without confidence'
                    # Falta 'confidence'
                }
            ],
            'analysis_duration': 2.0,
            'traditional_analysis': {},
            'ai_analysis': {},
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message sem gerar erro
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT" in call_args
            assert "3 sinais encontrados" in call_args
            
            # Verifica se campos ausentes são tratados com valores padrão
            assert "HOLD" in call_args  # signal_type padrão
            assert "0%" in call_args     # confidence padrão
            assert "Não especificado" in call_args  # reasoning padrão
    
    def test_notify_analysis_report_handles_confidence_visual_bars(self):
        """Testa se notify_analysis_report cria barras visuais de confiança corretamente"""
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'buy',
                    'confidence': 0.0,  # 0% - 0 barras verdes
                    'reasoning': 'No confidence'
                },
                {
                    'signal_type': 'buy',
                    'confidence': 0.5,  # 50% - 5 barras verdes
                    'reasoning': 'Moderate confidence'
                },
                {
                    'signal_type': 'buy',
                    'confidence': 1.0,  # 100% - 10 barras verdes
                    'reasoning': 'Full confidence'
                }
            ],
            'analysis_duration': 2.0,
            'traditional_analysis': {},
            'ai_analysis': {},
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            
            # Verifica barras visuais
            assert "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜" in call_args  # 0% - todas vazias
            assert "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜" in call_args  # 50% - 5 verdes, 5 vazias
            assert "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩" in call_args  # 100% - todas verdes
    
    def test_notify_analysis_report_handles_traditional_vs_ai_comparison(self):
        """Testa se notify_analysis_report mostra comparação entre análises"""
        analysis_data = {
            'signals': [],
            'analysis_duration': 2.0,
            'traditional_analysis': {
                'should_trade': True,
                'action': 'buy',
                'price': 50000.0
            },
            'ai_analysis': {
                'signals': [{'signal_type': 'sell'}],
                'best_signal': {'signal_type': 'sell', 'confidence': 0.8},
                'total_signals': 1,
                'valid_signals': 1
            },
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            
            # Verifica comparação entre análises
            assert "COMPARAÇÃO DE ANÁLISES" in call_args
            assert "Tradicional:" in call_args
            assert "BUY" in call_args
            assert "IA:" in call_args
            assert "SELL" in call_args
            assert "Divergência:" in call_args
    
    def test_notify_analysis_report_handles_concordance_between_analyses(self):
        """Testa se notify_analysis_report identifica concordância entre análises"""
        analysis_data = {
            'signals': [],
            'analysis_duration': 2.0,
            'traditional_analysis': {
                'should_trade': True,
                'action': 'buy',
                'price': 50000.0
            },
            'ai_analysis': {
                'signals': [{'signal_type': 'buy'}],
                'best_signal': {'signal_type': 'buy', 'confidence': 0.8},
                'total_signals': 1,
                'valid_signals': 1
            },
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica conteúdo da mensagem
            call_args = mock_send.call_args[0][0]
            
            # Verifica concordância entre análises
            assert "COMPARAÇÃO DE ANÁLISES" in call_args
            assert "Tradicional:" in call_args
            assert "IA:" in call_args
            assert "Concordância:" in call_args
            assert "BUY" in call_args
    
    def test_notify_analysis_report_handles_exception_in_formatting(self):
        """Testa se notify_analysis_report trata exceções durante formatação"""
        # Dados que podem causar exceção
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'buy',
                    'confidence': 'invalid_confidence',  # Tipo inválido
                    'reasoning': 'Test signal'
                }
            ],
            'analysis_duration': 'invalid_duration',  # Tipo inválido
            'traditional_analysis': {},
            'ai_analysis': {},
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            with patch.object(self.notifier, 'logger') as mock_logger:
                result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
                
                # Deve chamar send_message mesmo com dados inválidos
                mock_send.assert_called_once()
    
    def test_notify_analysis_report_handles_timeframe_parameter(self):
        """Testa se notify_analysis_report inclui timeframe na mensagem"""
        analysis_data = {
            'signals': [],
            'analysis_duration': 2.0,
            'traditional_analysis': {},
            'ai_analysis': {},
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data, "1h")
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica se timeframe foi incluído
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT (1h)" in call_args
    
    def test_notify_analysis_report_handles_no_timeframe(self):
        """Testa se notify_analysis_report funciona sem timeframe"""
        analysis_data = {
            'signals': [],
            'analysis_duration': 2.0,
            'traditional_analysis': {},
            'ai_analysis': {},
            'risk_assessment': {},
            'market_sentiment': {},
            'final_decision': {}
        }
        
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            result = self.notifier.notify_analysis_report("BTC/USDT", analysis_data)
            
            # Deve chamar send_message
            mock_send.assert_called_once()
            
            # Verifica se não há timeframe na mensagem
            call_args = mock_send.call_args[0][0]
            assert "BTC/USDT CONCLUÍDA" in call_args
            assert "(" not in call_args or ")" not in call_args  # Não deve ter parênteses de timeframe


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
