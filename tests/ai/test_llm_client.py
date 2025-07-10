#!/usr/bin/env python3
"""
Tests for LLM Client functionality
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.ai.llm_client import LLMClient, LLMResponse, get_llm_client, reset_llm_client


class TestLLMClient:
    """Test LLM Client functionality"""
    
    def setup_method(self):
        """Reset global client for each test"""
        reset_llm_client()
    
    def test_llm_client_initialization(self):
        """Test LLM client initialization with different providers"""
        # Test auto provider
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="auto")
            assert client.provider in ["openai", "gemini", "deepseek", "auto"]
    
    def test_llm_client_no_providers(self):
        """Test initialization when no providers are available"""
        with patch.dict('os.environ', {}, clear=True):
            with patch('src.ai.llm_client.OPENAI_AVAILABLE', False):
                with patch('src.ai.llm_client.GEMINI_AVAILABLE', False):
                    with patch('src.ai.llm_client.DEEPSEEK_AVAILABLE', False):
                        with pytest.raises(ValueError, match="No LLM providers available"):
                            LLMClient(provider="auto")
    
    @pytest.mark.asyncio
    async def test_openai_chat_success(self):
        """Test successful OpenAI chat completion"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            response = await client.chat("Test message")
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.provider == "openai"
            assert response.tokens_used == 100
            assert response.cost_estimate > 0
    
    @pytest.mark.asyncio
    async def test_gemini_chat_success(self):
        """Test successful Gemini chat completion"""
        mock_response = MagicMock()
        mock_response.text = "Test response from Gemini"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].finish_reason = 1  # STOP
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = "Test response from Gemini"
        
        mock_gemini_client = MagicMock()
        
        with patch.dict('os.environ', {'GOOGLE_AI_API_KEY': 'test-key'}):
            with patch('src.ai.llm_client.genai.GenerativeModel') as mock_genai:
                mock_genai.return_value = mock_gemini_client
                
                client = LLMClient(provider="gemini")
                client.gemini_client = mock_gemini_client
                
                with patch('asyncio.to_thread') as mock_to_thread:
                    mock_to_thread.return_value = mock_response
                    
                    response = await client.chat("Test message")
                    
                    assert isinstance(response, LLMResponse)
                    assert response.content == "Test response from Gemini"
                    assert response.provider == "gemini"
                    assert response.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        """Test chat with system prompt"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "System-guided response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 120
        mock_response.usage.prompt_tokens = 70
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            response = await client.chat(
                "User message",
                system_prompt="You are a helpful assistant"
            )
            
            assert response.content == "System-guided response"
            
            # Check that system prompt was included
            call_args = mock_openai_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == "You are a helpful assistant"
    
    @pytest.mark.asyncio
    async def test_analyze_json_success(self):
        """Test successful JSON analysis"""
        json_response = {
            "sentiment": "positive",
            "confidence": 0.8,
            "reasoning": "Test reasoning"
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 150
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            result = await client.analyze_json("Analyze this text")
            
            assert result == json_response
    
    @pytest.mark.asyncio
    async def test_analyze_json_with_schema(self):
        """Test JSON analysis with schema validation"""
        schema = {
            "sentiment": "string",
            "confidence": "number",
            "reasoning": "string"
        }
        
        json_response = {
            "sentiment": "positive",
            "confidence": 0.8,
            "reasoning": "Test reasoning"
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 150
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            result = await client.analyze_json(
                "Analyze this text",
                schema=schema
            )
            
            assert result == json_response
    
    @pytest.mark.asyncio
    async def test_analyze_json_malformed(self):
        """Test JSON analysis with malformed JSON"""
        malformed_json = '{"sentiment": "positive", "confidence": 0.8, "reasoning": "Test'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = malformed_json
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 150
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            result = await client.analyze_json("Analyze this text")
            
            # Should return a fallback response
            assert "error" in result
            assert result["error"] == "json_parsing_failed"
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when client is healthy"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 10
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            status = await client.health_check()
            
            assert status["status"] == "healthy"
            assert status["provider"] == "openai"
            assert status["openai_available"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when client is unhealthy"""
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            client.openai_client = mock_openai_client
            
            status = await client.health_check()
            
            assert status["status"] == "unhealthy"
            assert "error" in status
    
    def test_get_available_models(self):
        """Test getting available models"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(provider="openai")
            
            models = client.get_available_models()
            
            assert isinstance(models, list)
            assert len(models) > 0
            assert "gpt-4" in models or "gpt-3.5-turbo" in models
    
    def test_cost_calculation(self):
        """Test cost calculation for different providers"""
        client = LLMClient.__new__(LLMClient)  # Create without calling __init__
        client.model = "gpt-4"
        client.costs = {
            "gpt-4": {"input": 0.03, "output": 0.06}
        }
        
        cost = client._calculate_cost("openai", 1000, 500)
        expected = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert cost == expected
    
    def test_token_estimation(self):
        """Test token estimation"""
        client = LLMClient.__new__(LLMClient)
        client.token_counter = None
        
        # Test without token counter (fallback)
        tokens = client._estimate_tokens("This is a test message")
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_convert_messages_to_gemini_prompt(self):
        """Test converting OpenAI messages to Gemini format"""
        client = LLMClient.__new__(LLMClient)
        
        # Test single user message
        messages = [{"role": "user", "content": "Hello"}]
        prompt = client._convert_messages_to_gemini_prompt(messages)
        assert prompt == "Hello"
        
        # Test conversation
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        prompt = client._convert_messages_to_gemini_prompt(messages)
        assert "System: You are helpful" in prompt
        assert "User: Hello" in prompt
        assert "Assistant: Hi there!" in prompt
    
    def test_fix_json_formatting(self):
        """Test JSON formatting fixes"""
        client = LLMClient.__new__(LLMClient)
        
        # Test fixing unquoted properties
        malformed = '{sentiment: "positive", confidence: 0.8}'
        fixed = client._fix_json_formatting(malformed)
        assert '"sentiment":' in fixed
        assert '"confidence":' in fixed
        
        # Test fixing trailing commas
        malformed = '{"sentiment": "positive", "confidence": 0.8,}'
        fixed = client._fix_json_formatting(malformed)
        assert not fixed.endswith(',}')
    
    def test_create_fallback_sentiment_response(self):
        """Test creating fallback sentiment response"""
        client = LLMClient.__new__(LLMClient)
        client.logger = MagicMock()
        
        malformed_json = '{"sentiment_score": 0.7, "sentiment_label": "positive"'
        
        response = client._create_fallback_sentiment_response(malformed_json)
        
        assert response["sentiment_score"] == 0.7
        assert response["sentiment_label"] == "positive"
        assert response["confidence"] > 0
    
    def test_global_client_management(self):
        """Test global client management"""
        # Test getting client
        with patch.dict('os.environ', {'GOOGLE_AI_API_KEY': 'test-key'}):
            client1 = get_llm_client()
            client2 = get_llm_client()
            
            assert client1 is client2  # Should be same instance
        
        # Test resetting client
        reset_llm_client()
        with patch.dict('os.environ', {'GOOGLE_AI_API_KEY': 'test-key'}):
            client3 = get_llm_client()
            assert client3 is not client1  # Should be new instance


class TestLLMResponse:
    """Test LLMResponse dataclass"""
    
    def test_llm_response_creation(self):
        """Test creating LLMResponse"""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            tokens_used=100,
            cost_estimate=0.01,
            timestamp=datetime.now()
        )
        
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 100
        assert response.cost_estimate == 0.01
        assert isinstance(response.timestamp, datetime)
    
    def test_llm_response_with_metadata(self):
        """Test LLMResponse with metadata"""
        metadata = {
            "input_tokens": 50,
            "output_tokens": 50,
            "finish_reason": "stop"
        }
        
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            tokens_used=100,
            cost_estimate=0.01,
            timestamp=datetime.now(),
            confidence=0.9,
            metadata=metadata
        )
        
        assert response.confidence == 0.9
        assert response.metadata == metadata
        assert response.metadata["finish_reason"] == "stop"


class TestLLMProviderSelection:
    """Test LLM provider selection logic"""
    
    def test_provider_selection_openai_priority(self):
        """Test OpenAI gets priority in auto selection"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'GOOGLE_AI_API_KEY': 'test-key'
        }):
            client = LLMClient(provider="auto")
            assert client.provider == "openai"
    
    def test_provider_selection_fallback_to_gemini(self):
        """Test fallback to Gemini when OpenAI unavailable"""
        with patch.dict('os.environ', {
            'GOOGLE_AI_API_KEY': 'test-key'
        }):
            with patch('src.ai.llm_client.OPENAI_AVAILABLE', False):
                client = LLMClient(provider="auto")
                assert client.provider == "gemini"
    
    def test_provider_selection_deepseek(self):
        """Test DeepSeek selection"""
        with patch.dict('os.environ', {
            'DEEPSEEK_API_KEY': 'test-key'
        }):
            with patch('src.ai.llm_client.OPENAI_AVAILABLE', False):
                with patch('src.ai.llm_client.GEMINI_AVAILABLE', False):
                    client = LLMClient(provider="auto")
                    assert client.provider == "deepseek"
