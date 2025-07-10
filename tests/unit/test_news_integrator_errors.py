#!/usr/bin/env python3
"""
Testes para corrigir erros identificados nos logs - News Integrator
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

from src.ai.news_integrator import NewsIntegrator
from src.ai.news_analyzer import CryptoNewsItem


class TestNewsIntegratorErrors:
    """Testes para corrigir erros identificados no NewsIntegrator"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.integrator = NewsIntegrator()
        self.sample_news_items = [
            CryptoNewsItem(
                title="Bitcoin reaches new record",
                content="Bitcoin hit a new price record today...",
                source="CryptoNews",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["BTC"]
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_handles_none_analysis(self):
        """Testa se get_market_sentiment trata análise None do LLM (Erro 2)"""
        with patch.object(self.integrator, 'news_analyzer') as mock_analyzer:
            mock_analyzer.analyze_crypto_news = AsyncMock(return_value=None)
            
            with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
                mock_fetch.return_value = self.sample_news_items
                
                result = await self.integrator.get_market_sentiment(['BTC'])
                
                # Deve retornar sentimento neutro
                assert isinstance(result, dict)
                assert result['sentiment_score'] == 0.0
                assert result['sentiment_label'] == 'neutral'
                assert result['confidence'] == 0.1
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_handles_invalid_type_analysis(self):
        """Testa se get_market_sentiment trata análise com tipo inválido (Erro 2)"""
        with patch.object(self.integrator, 'news_analyzer') as mock_analyzer:
            # Retorna string ao invés de dict
            mock_analyzer.analyze_crypto_news = AsyncMock(return_value="invalid_type")
            
            with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
                mock_fetch.return_value = self.sample_news_items
                
                result = await self.integrator.get_market_sentiment(['BTC'])
                
                # Deve retornar sentimento neutro
                assert isinstance(result, dict)
                assert result['sentiment_score'] == 0.0
                assert result['sentiment_label'] == 'neutral'
                assert result['confidence'] == 0.1
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_handles_dict_analysis(self):
        """Testa se get_market_sentiment trata análise dict corretamente (Erro 2)"""
        mock_analysis = {
            'sentiment_score': 0.7,
            'sentiment_label': 'bullish',
            'confidence': 0.8,
            'impact_level': 'medium',
            'key_events': ['Bitcoin record'],
            'price_prediction': 'short_term_up',
            'reasoning': 'Positive market sentiment',
            'article_count': 1
        }
        
        with patch.object(self.integrator, 'news_analyzer') as mock_analyzer:
            # Simula um objeto NewsAnalysis com atributos
            mock_news_analysis = Mock()
            mock_news_analysis.sentiment_score = 0.7
            mock_news_analysis.sentiment_label = 'bullish'
            mock_news_analysis.confidence = 0.8
            mock_news_analysis.impact_level = 'medium'
            mock_news_analysis.key_events = ['Bitcoin record']
            mock_news_analysis.price_prediction = 'short_term_up'
            mock_news_analysis.reasoning = 'Positive market sentiment'
            mock_news_analysis.article_count = 1
            
            mock_analyzer.analyze_crypto_news = AsyncMock(return_value=mock_news_analysis)
            
            with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
                mock_fetch.return_value = self.sample_news_items
                
                result = await self.integrator.get_market_sentiment(['BTC'])
                
                # Deve retornar dados do mock
                assert isinstance(result, dict)
                assert result['sentiment_score'] == 0.7
                assert result['sentiment_label'] == 'bullish'
                assert result['confidence'] == 0.8
                assert result['impact_level'] == 'medium'
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_handles_timeout(self):
        """Testa se get_market_sentiment trata timeout corretamente (Erro 4)"""
        with patch.object(self.integrator, 'news_analyzer') as mock_analyzer:
            mock_analyzer.analyze_crypto_news = AsyncMock(side_effect=asyncio.TimeoutError())
            
            with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
                mock_fetch.return_value = self.sample_news_items
                
                result = await self.integrator.get_market_sentiment(['BTC'])
                
                # Deve retornar sentimento neutro com timeout
                assert isinstance(result, dict)
                assert result['sentiment_score'] == 0.0
                assert result['sentiment_label'] == 'neutral'
                assert result['confidence'] == 0.1
                assert 'timeout' in result['reasoning'].lower()
    
    @pytest.mark.asyncio
    async def test_get_market_sentiment_handles_empty_news(self):
        """Testa se get_market_sentiment trata lista vazia de notícias (Erro 5)"""
        with patch.object(self.integrator, '_fetch_recent_news') as mock_fetch:
            mock_fetch.return_value = []  # Lista vazia
            
            result = await self.integrator.get_market_sentiment(['BTC'])
            
            # Deve retornar sentimento neutro
            assert isinstance(result, dict)
            assert result['sentiment_score'] == 0.0
            assert result['sentiment_label'] == 'neutral'
            assert result['confidence'] == 0.1
            assert 'no data available' in result['reasoning'].lower()
    
    @pytest.mark.asyncio
    async def test_get_symbol_sentiment_handles_timeout(self):
        """Testa se get_symbol_sentiment trata timeout corretamente (Erro 4)"""
        with patch.object(self.integrator, 'get_market_sentiment') as mock_get_sentiment:
            mock_get_sentiment.side_effect = asyncio.TimeoutError()
            
            result = await self.integrator.get_symbol_sentiment('BTC')
            
            # Deve retornar sentimento neutro com timeout
            assert isinstance(result, dict)
            assert result['sentiment_score'] == 0.0
            assert result['sentiment_label'] == 'neutral'
            assert result['confidence'] == 0.1
            assert 'timeout' in result['reasoning'].lower()
    
    @pytest.mark.asyncio
    async def test_get_symbol_sentiment_handles_exception(self):
        """Testa se get_symbol_sentiment trata exceções corretamente"""
        with patch.object(self.integrator, 'get_market_sentiment') as mock_get_sentiment:
            mock_get_sentiment.side_effect = Exception("Test error")
            
            result = await self.integrator.get_symbol_sentiment('BTC')
            
            # Deve retornar sentimento neutro
            assert isinstance(result, dict)
            assert result['sentiment_score'] == 0.0
            assert result['sentiment_label'] == 'neutral'
            assert result['confidence'] == 0.1
    
    def test_create_neutral_sentiment_structure(self):
        """Testa se _create_neutral_sentiment retorna estrutura correta"""
        result = self.integrator._create_neutral_sentiment()
        
        assert isinstance(result, dict)
        assert result['sentiment_score'] == 0.0
        assert result['sentiment_label'] == 'neutral'
        assert result['confidence'] == 0.1
        assert result['impact_level'] == 'low'
        assert result['key_events'] == []
        assert result['price_prediction'] == 'neutral'
        assert result['article_count'] == 0
        assert result['detected_events'] == []
        assert 'timestamp' in result
    
    def test_create_neutral_sentiment_with_timeout_structure(self):
        """Testa se _create_neutral_sentiment_with_timeout retorna estrutura correta"""
        result = self.integrator._create_neutral_sentiment_with_timeout(['BTC'])
        
        assert isinstance(result, dict)
        assert result['sentiment_score'] == 0.0
        assert result['sentiment_label'] == 'neutral'
        assert result['confidence'] == 0.1
        assert result['impact_level'] == 'low'
        assert result['key_events'] == []
        assert result['price_prediction'] == 'neutral'
        assert result['article_count'] == 0
        assert result['detected_events'] == []
        assert 'timeout' in result['reasoning'].lower()
        assert 'btc' in result['reasoning'].lower()
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_handles_no_sources(self):
        """Testa se _fetch_recent_news trata ausência de fontes (Erro 6)"""
        # Simula sources_available = False
        self.integrator.sources_available = False
        
        with patch.object(self.integrator, '_create_sample_news') as mock_sample:
            mock_sample.return_value = self.sample_news_items
            
            result = await self.integrator._fetch_recent_news(['BTC'])
            
            # Deve retornar notícias de exemplo
            mock_sample.assert_called_once()
            assert isinstance(result, list)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_handles_cache(self):
        """Testa se _fetch_recent_news usa cache corretamente"""
        # Configura cache
        cache_key = "news_BTC_24h"
        cached_news = self.sample_news_items
        self.integrator.news_cache[cache_key] = (datetime.now(), cached_news)
        
        result = await self.integrator._fetch_recent_news(['BTC'])
        
        # Deve retornar notícias do cache
        assert isinstance(result, list)
        assert len(result) == len(cached_news)
    
    @pytest.mark.asyncio
    async def test_fetch_recent_news_handles_expired_cache(self):
        """Testa se _fetch_recent_news trata cache expirado"""
        # Configura cache expirado
        cache_key = "news_BTC_24h"
        cached_news = self.sample_news_items
        expired_time = datetime.now() - timedelta(hours=1)  # Cache de 1 hora atrás
        self.integrator.news_cache[cache_key] = (expired_time, cached_news)
        
        # Mock para evitar chamadas reais de API
        with patch.object(self.integrator, '_fetch_news_api_news') as mock_news_api:
            mock_news_api.return_value = self.sample_news_items
            
            result = await self.integrator._fetch_recent_news(['BTC'])
            
            # Deve buscar notícias frescas, não usar cache
            mock_news_api.assert_called_once()
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_news_api_news_handles_exception(self):
        """Testa se _fetch_news_api_news trata exceções corretamente"""
        with patch.object(self.integrator, 'news_api_client') as mock_client:
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_crypto_news = AsyncMock(side_effect=Exception("API Error"))
            
            result = await self.integrator._fetch_news_api_news(['BTC'], 24)
            
            # Deve retornar lista vazia em caso de erro
            assert isinstance(result, list)
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_news_api_news_handles_no_articles(self):
        """Testa se _fetch_news_api_news trata ausência de artigos"""
        with patch.object(self.integrator, 'news_api_client') as mock_client:
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_crypto_news = AsyncMock(return_value=None)
            
            result = await self.integrator._fetch_news_api_news(['BTC'], 24)
            
            # Deve retornar lista vazia
            assert isinstance(result, list)
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_news_api_news_handles_invalid_article_format(self):
        """Testa se _fetch_news_api_news trata formato inválido de artigo"""
        invalid_articles = [
            "string_instead_of_dict",  # Formato inválido
            {"title": "Valid Article", "description": "Valid content"}  # Formato válido
        ]
        
        with patch.object(self.integrator, 'news_api_client') as mock_client:
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_crypto_news = AsyncMock(return_value=invalid_articles)
            
            result = await self.integrator._fetch_news_api_news(['BTC'], 24)
            
            # Deve retornar apenas artigos válidos
            assert isinstance(result, list)
            assert len(result) == 1  # Apenas o artigo válido
    
    def test_create_sample_news_returns_valid_structure(self):
        """Testa se _create_sample_news retorna estrutura válida"""
        result = self.integrator._create_sample_news()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        for item in result:
            assert isinstance(item, CryptoNewsItem)
            assert hasattr(item, 'title')
            assert hasattr(item, 'content')
            assert hasattr(item, 'source')
            assert hasattr(item, 'published_at')
            assert hasattr(item, 'symbols_mentioned')
            assert item.source == "Sample News"
    
    def test_extract_symbols_from_text_basic_cases(self):
        """Testa se _extract_symbols_from_text funciona com casos básicos"""
        test_cases = [
            ("Bitcoin reaches new high", ["BTC"]),
            ("Ethereum network upgrade", ["ETH"]),
            ("BNB token performs well", ["BNB"]),
            ("Bitcoin and Ethereum both rising", ["BTC", "ETH"]),
            ("No crypto symbols here", []),
            ("BITCOIN and ETHEREUM", ["BTC", "ETH"]),
        ]
        
        for text, expected_symbols in test_cases:
            result = self.integrator._extract_symbols_from_text(text)
            
            assert isinstance(result, list)
            for symbol in expected_symbols:
                assert symbol in result
    
    def test_extract_symbols_from_text_removes_duplicates(self):
        """Testa se _extract_symbols_from_text remove duplicatas"""
        text = "Bitcoin BTC bitcoin BITCOIN"
        result = self.integrator._extract_symbols_from_text(text)
        
        assert isinstance(result, list)
        assert result.count("BTC") == 1  # Deve haver apenas um BTC
    
    @pytest.mark.asyncio
    async def test_save_analysis_to_database_handles_timeout(self):
        """Testa se _save_analysis_to_database trata timeout corretamente"""
        with patch('src.database.database.get_safe_database_session') as mock_get_session:
            mock_get_session.side_effect = asyncio.TimeoutError()
            
            # Não deve gerar exceção
            await self.integrator._save_analysis_to_database(
                symbol="BTC",
                analysis_type="test",
                data={"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_save_analysis_to_database_handles_event_loop_error(self):
        """Testa se _save_analysis_to_database trata erro de event loop"""
        with patch('src.database.database.get_safe_database_session') as mock_get_session:
            mock_get_session.side_effect = Exception("got Future attached to a different loop")
            
            # Não deve gerar exceção
            await self.integrator._save_analysis_to_database(
                symbol="BTC",
                analysis_type="test",
                data={"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_cleanup_waits_for_background_tasks(self):
        """Testa se cleanup aguarda tarefas em segundo plano"""
        # Simula tarefas em segundo plano
        mock_task = AsyncMock()
        self.integrator.background_tasks.add(mock_task)
        
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = AsyncMock()
            
            await self.integrator.cleanup()
            
            # Deve chamar gather com as tarefas
            mock_gather.assert_called_once()
            # Verifica se o conjunto foi limpo
            assert len(self.integrator.background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_handles_exception(self):
        """Testa se cleanup trata exceções corretamente"""
        # Simula tarefas em segundo plano
        mock_task = AsyncMock()
        self.integrator.background_tasks.add(mock_task)
        
        with patch('asyncio.gather') as mock_gather:
            mock_gather.side_effect = Exception("Cleanup error")
            
            # Não deve gerar exceção
            await self.integrator.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
