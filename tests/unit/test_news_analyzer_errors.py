#!/usr/bin/env python3
"""
Testes para corrigir erros identificados nos logs - News Analyzer
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ai.news_analyzer import LLMNewsAnalyzer, NewsAnalysis, CryptoNewsItem


class TestLLMNewsAnalyzerErrors:
    """Testes para corrigir erros identificados no LLMNewsAnalyzer"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.analyzer = LLMNewsAnalyzer()
        self.sample_news_items = [
            CryptoNewsItem(
                title="Bitcoin alcança novo recorde",
                content="Bitcoin atingiu um novo recorde de preço hoje...",
                source="CryptoNews",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["BTC"]
            ),
            CryptoNewsItem(
                title="Ethereum atualização importante",
                content="A rede Ethereum recebeu uma atualização importante...",
                source="ETHNews",
                published_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["ETH"]
            )
        ]
    
    def test_analyze_crypto_news_method_exists(self):
        """Testa se o método analyze_crypto_news existe (Erro 1)"""
        # Verifica se o método existe
        assert hasattr(self.analyzer, 'analyze_crypto_news')
        assert callable(getattr(self.analyzer, 'analyze_crypto_news'))
    
    @pytest.mark.asyncio
    async def test_analyze_crypto_news_returns_news_analysis(self):
        """Testa se analyze_crypto_news retorna NewsAnalysis (Erro 1)"""
        # Mock do LLM client para evitar chamadas reais
        mock_response = {
            "sentiment_score": 0.7,
            "sentiment_label": "bullish",
            "confidence": 0.8,
            "impact_level": "medium",
            "key_events": ["Bitcoin record"],
            "price_prediction": "short_term_up",
            "reasoning": "Positive market sentiment"
        }
        
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(return_value=mock_response)
            
            with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                mock_guard.sanitize_ai_input.return_value = "safe input"
                mock_guard.validate_ai_output.return_value = (True, None)
                
                with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                    mock_optimizer.optimize_prompt.return_value = Mock(
                        optimized_prompt="optimized prompt",
                        safety_score=0.9,
                        modifications=[]
                    )
                    
                    result = await self.analyzer.analyze_crypto_news(self.sample_news_items, "BTC")
                    
                    # Verifica se retorna NewsAnalysis
                    assert isinstance(result, NewsAnalysis)
                    assert result.sentiment_score == 0.7
                    assert result.sentiment_label == "bullish"
                    assert result.confidence == 0.8
    
    def test_generate_cache_key_method_exists(self):
        """Testa se o método _generate_cache_key existe (Erro 1)"""
        assert hasattr(self.analyzer, '_generate_cache_key')
        assert callable(getattr(self.analyzer, '_generate_cache_key'))
    
    def test_generate_cache_key_returns_string(self):
        """Testa se _generate_cache_key retorna uma string válida (Erro 1)"""
        cache_key = self.analyzer._generate_cache_key(self.sample_news_items, "BTC")
        
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        assert "BTC" in cache_key
        assert "news_analysis" in cache_key
    
    def test_combine_news_for_analysis_method_exists(self):
        """Testa se o método _combine_news_for_analysis existe (Erro 1)"""
        assert hasattr(self.analyzer, '_combine_news_for_analysis')
        assert callable(getattr(self.analyzer, '_combine_news_for_analysis'))
    
    def test_combine_news_for_analysis_limits_size(self):
        """Testa se _combine_news_for_analysis limita o tamanho (Erro 1)"""
        # Cria muitas notícias para testar o limite
        many_news = []
        for i in range(10):
            news = CryptoNewsItem(
                title=f"Very long title number {i} " * 20,  # Título muito longo
                content=f"Very long content number {i} " * 50,  # Conteúdo muito longo
                source="TestSource",
                published_at=datetime.now() - timedelta(hours=i),
                symbols_mentioned=["BTC"]
            )
            many_news.append(news)
        
        combined_text = self.analyzer._combine_news_for_analysis(many_news)
        
        # Verifica se o texto foi limitado
        assert isinstance(combined_text, str)
        assert len(combined_text) <= 1520  # Limite definido no código + margem para "..."
        
        # Verifica se apenas as primeiras 5 notícias foram incluídas
        lines = combined_text.split('\n')
        numbered_lines = [line for line in lines if line.startswith(('1.', '2.', '3.', '4.', '5.'))]
        assert len(numbered_lines) <= 5
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_handles_none_response(self):
        """Testa se analyze_sentiment trata resposta None do LLM (Erro 4)"""
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(return_value=None)
            
            with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                mock_guard.sanitize_ai_input.return_value = "safe input"
                mock_guard.validate_ai_output.return_value = (True, None)
                
                with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                    mock_optimizer.optimize_prompt.return_value = Mock(
                        optimized_prompt="optimized prompt",
                        safety_score=0.9,
                        modifications=[]
                    )
                    
                    result = await self.analyzer.analyze_sentiment(self.sample_news_items, "BTC")
                    
                    # Deve retornar análise neutra
                    assert isinstance(result, NewsAnalysis)
                    assert result.sentiment_score == 0.0
                    assert result.sentiment_label == "neutral"
                    assert result.confidence == 0.1
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_handles_timeout(self):
        """Testa se analyze_sentiment trata timeout corretamente (Erro 4)"""
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(side_effect=asyncio.TimeoutError())
            
            with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                mock_guard.sanitize_ai_input.return_value = "safe input"
                
                with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                    mock_optimizer.optimize_prompt.return_value = Mock(
                        optimized_prompt="optimized prompt",
                        safety_score=0.9,
                        modifications=[]
                    )
                    
                    result = await self.analyzer.analyze_sentiment(self.sample_news_items, "BTC")
                    
                    # Deve retornar análise neutra com razão de timeout
                    assert isinstance(result, NewsAnalysis)
                    assert result.sentiment_score == 0.0
                    assert result.sentiment_label == "neutral"
                    assert "timed out" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_handles_blocked_by_safety_filters(self):
        """Testa se analyze_sentiment trata bloqueio por filtros de segurança (Erro 4)"""
        blocked_response = {"error": "blocked_by_safety_filters"}
        
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(return_value=blocked_response)
            
            with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                mock_guard.sanitize_ai_input.return_value = "safe input"
                
                with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                    mock_optimizer.optimize_prompt.return_value = Mock(
                        optimized_prompt="optimized prompt",
                        safety_score=0.9,
                        modifications=[]
                    )
                    
                    result = await self.analyzer.analyze_sentiment(self.sample_news_items, "BTC")
                    
                    # Deve retornar análise neutra com razão de bloqueio
                    assert isinstance(result, NewsAnalysis)
                    assert result.sentiment_score == 0.0
                    assert result.sentiment_label == "neutral"
                    assert "blocked by" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_handles_json_parsing_failed(self):
        """Testa se analyze_sentiment trata erro de parsing JSON (Erro 4)"""
        json_error_response = {"error": "json_parsing_failed"}
        
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(return_value=json_error_response)
            
            with patch.object(self.analyzer, '_create_fallback_analysis') as mock_fallback:
                mock_fallback.return_value = self.analyzer._create_neutral_analysis(
                    2, "Fallback analysis due to JSON parsing failure"
                )
                
                with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                    mock_guard.sanitize_ai_input.return_value = "safe input"
                    
                    with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                        mock_optimizer.optimize_prompt.return_value = Mock(
                            optimized_prompt="optimized prompt",
                            safety_score=0.9,
                            modifications=[]
                        )
                        
                        result = await self.analyzer.analyze_sentiment(self.sample_news_items, "BTC")
                        
                        # Deve chamar análise de fallback
                        mock_fallback.assert_called_once()
                        assert isinstance(result, NewsAnalysis)
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_handles_empty_news_items(self):
        """Testa se analyze_sentiment trata lista vazia de notícias (Erro 5)"""
        result = await self.analyzer.analyze_sentiment([], "BTC")
        
        # Deve retornar análise neutra
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.0
        assert result.sentiment_label == "neutral"
        assert result.confidence == 0.1
        assert result.article_count == 0
        assert "no news items" in result.reasoning.lower()
    
    def test_create_neutral_analysis_structure(self):
        """Testa se _create_neutral_analysis retorna estrutura correta"""
        result = self.analyzer._create_neutral_analysis(5, "Test reason")
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score == 0.0
        assert result.sentiment_label == "neutral"
        assert result.confidence == 0.1
        assert result.impact_level == "low"
        assert result.key_events == []
        assert result.price_prediction == "neutral"
        assert result.reasoning == "Test reason"
        assert result.article_count == 5
        assert isinstance(result.timestamp, datetime)
    
    def test_create_fallback_analysis_with_keywords(self):
        """Testa se _create_fallback_analysis usa heurísticas de palavras-chave"""
        # Cria notícias com palavras-chave positivas
        positive_news = [
            CryptoNewsItem(
                title="Bitcoin surge to new highs, bullish momentum continues",
                content="Bitcoin shows strong bullish signals with massive gains and positive outlook",
                source="TestSource",
                published_at=datetime.now(),
                symbols_mentioned=["BTC"]
            )
        ]
        
        result = self.analyzer._create_fallback_analysis(positive_news, "BTC")
        
        assert isinstance(result, NewsAnalysis)
        assert result.sentiment_score > 0  # Deve ser positivo devido às palavras-chave
        assert result.sentiment_label == "bullish"
        assert result.confidence == 0.3  # Confiança reduzida para análise heurística
        assert "fallback heuristic" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_market_events_handles_empty_news(self):
        """Testa se detect_market_events trata lista vazia de notícias"""
        result = await self.analyzer.detect_market_events([])
        
        # Deve retornar lista vazia
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_detect_market_events_handles_exception(self):
        """Testa se detect_market_events trata exceções corretamente"""
        with patch.object(self.analyzer, 'llm_client') as mock_llm:
            mock_llm.analyze_json = AsyncMock(side_effect=Exception("Test error"))
            
            with patch('src.ai_security.prompt_protection.ai_security_guard') as mock_guard:
                mock_guard.sanitize_ai_input.return_value = "safe input"
                
                with patch('src.ai.prompt_optimizer.prompt_optimizer') as mock_optimizer:
                    mock_optimizer.optimize_prompt.return_value = Mock(
                        optimized_prompt="optimized prompt",
                        safety_score=0.9,
                        modifications=[]
                    )
                    
                    result = await self.analyzer.detect_market_events(self.sample_news_items)
                    
                    # Deve retornar lista vazia em caso de erro
                    assert isinstance(result, list)
                    assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
