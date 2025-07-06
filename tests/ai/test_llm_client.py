"""Test suite for AI LLM client module."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import os

from src.ai.llm_client import (
    LLMClient,
    LLMResponse,
    get_llm_client
)


class TestLLMResponse:
    """Test cases for LLMResponse dataclass."""
    
    def test_llm_response_creation(self):
        """Test LLMResponse can be created with all fields."""
        response = LLMResponse(
            content="Test response content",
            model="gpt-4",
            provider="openai",
            tokens_used=150,
            cost_estimate=0.003,
            timestamp=datetime.now(),
            confidence=0.85,
            metadata={"input_tokens": 100, "output_tokens": 50}
        )
        
        assert response.content == "Test response content"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 150
        assert response.confidence == 0.85
        assert "input_tokens" in response.metadata


class TestLLMClient:
    """Test cases for LLMClient class."""
    
    def setup_method(self):
        """Set up test client."""
        # Clear any existing environment variables for clean testing
        self.original_env = {}
        for key in ["AI_PROVIDER", "AI_MODEL", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY"]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]
    
    def teardown_method(self):
        """Restore environment variables."""
        for key, value in self.original_env.items():
            os.environ[key] = value
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('src.ai.llm_client.openai.AsyncOpenAI')
    @patch('src.ai.llm_client.tiktoken.encoding_for_model')
    def test_initialization_openai(self, mock_tiktoken, mock_openai_client):
        """Test LLMClient initialization with OpenAI."""
        # Set up environment
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["AI_PROVIDER"] = "openai"
        
        # Mock tiktoken
        mock_encoding = Mock()
        mock_tiktoken.return_value = mock_encoding
        
        # Mock OpenAI client
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        
        client = LLMClient(provider="openai")
        
        assert client.provider == "openai"
        assert client.model == "gpt-4-turbo"
        assert client.openai_client is not None
        assert client.token_counter is not None
        mock_openai_client.assert_called_once_with(api_key="test-key")
    
    @patch('src.ai.llm_client.GEMINI_AVAILABLE', True)
    @patch('src.ai.llm_client.genai.configure')
    @patch('src.ai.llm_client.genai.GenerativeModel')
    def test_initialization_gemini(self, mock_generative_model, mock_configure):
        """Test LLMClient initialization with Gemini."""
        # Set up environment
        os.environ["GOOGLE_AI_API_KEY"] = "test-key"
        os.environ["AI_PROVIDER"] = "gemini"
        
        # Mock Gemini client
        mock_model_instance = Mock()
        mock_generative_model.return_value = mock_model_instance
        
        client = LLMClient(provider="gemini")
        
        assert client.provider == "gemini"
        assert client.model == "gemini-pro"
        assert client.gemini_client is not None
        mock_configure.assert_called_once_with(api_key="test-key")
        mock_generative_model.assert_called_once_with('gemini-pro')
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', False)
    @patch('src.ai.llm_client.GEMINI_AVAILABLE', False)
    def test_initialization_no_providers(self):
        """Test LLMClient initialization with no available providers."""
        with pytest.raises(ValueError, match="No LLM providers available"):
            LLMClient(provider="auto")
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('src.ai.llm_client.openai.AsyncOpenAI')
    def test_auto_provider_selection(self, mock_openai_client):
        """Test automatic provider selection."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        
        client = LLMClient(provider="auto")
        
        assert client.provider == "openai"
        assert client.model == "gpt-4-turbo"
    
    @pytest.mark.asyncio
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    async def test_chat_openai(self):
        """Test chat functionality with OpenAI."""
        # Setup mock client
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150  # Add total_tokens to match what the code expects
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"

        response = await client.chat("Test message", system_prompt="Test system prompt")

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 150
        assert response.metadata["input_tokens"] == 100
        assert response.metadata["output_tokens"] == 50
    
    @pytest.mark.asyncio
    @patch('src.ai.llm_client.GEMINI_AVAILABLE', True)
    @patch('src.ai.llm_client.asyncio.to_thread')
    async def test_chat_gemini(self, mock_to_thread):
        """Test chat functionality with Gemini."""
        # Setup mock client
        mock_gemini_client = Mock()
        mock_response = Mock()
        mock_response.text = "Test response"
        
        mock_to_thread.return_value = mock_response
        
        client = LLMClient(provider="gemini")
        client.gemini_client = mock_gemini_client
        client.model = "gemini-pro"
        
        response = await client.chat("Test message", system_prompt="Test system prompt")
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gemini-pro"
        assert response.provider == "gemini"
        mock_to_thread.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_with_messages_list(self):
        """Test chat with list of messages."""
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        response = await client.chat(messages)
        
        assert response.content == "Test response"
        # Verify that the messages were passed correctly
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["messages"] == messages
    
    @pytest.mark.asyncio
    async def test_analyze_json(self):
        """Test JSON analysis functionality."""
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"result": "success", "confidence": 0.85}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        schema = {"result": "string", "confidence": "number"}
        response = await client.analyze_json(
            "Analyze this data", 
            system_prompt="You are an analyst",
            schema=schema
        )
        
        assert isinstance(response, dict)
        assert response["result"] == "success"
        assert response["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_analyze_json_with_code_blocks(self):
        """Test JSON analysis with code block formatting."""
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '```json\n{"status": "ok"}\n```'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 70
        mock_usage.completion_tokens = 30
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        response = await client.analyze_json("Test prompt")
        
        assert isinstance(response, dict)
        assert response["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_analyze_json_invalid_response(self):
        """Test JSON analysis with invalid JSON response."""
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "This is not valid JSON"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 70
        mock_usage.completion_tokens = 30
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        with pytest.raises(json.JSONDecodeError):
            await client.analyze_json("Test prompt")
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('os.getenv')
    def test_convert_messages_to_gemini_prompt(self, mock_getenv):
        """Test message conversion for Gemini."""
        mock_getenv.return_value = "test_api_key"
        client = LLMClient(provider="openai")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = client._convert_messages_to_gemini_prompt(messages)
        
        expected_prompt = (
            "System: You are a helpful assistant\n\n"
            "User: Hello\n\n"
            "Assistant: Hi there!\n\n"
            "User: How are you?"
        )
        
        assert prompt == expected_prompt
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('os.getenv')
    def test_estimate_tokens(self, mock_getenv):
        """Test token estimation."""
        mock_getenv.return_value = "test_api_key"
        client = LLMClient(provider="openai")
        
        # Test with mock token counter
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        client.token_counter = mock_encoder
        
        token_count = client._estimate_tokens("Hello world")
        assert token_count == 5
        
        # Test without token counter (fallback)
        client.token_counter = None
        token_count = client._estimate_tokens("Hello world test")  # 17 characters
        assert token_count == 17 // 4  # Should be approximately 4 tokens
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('os.getenv')
    def test_calculate_cost(self, mock_getenv):
        """Test cost calculation."""
        mock_getenv.return_value = "test_api_key"
        client = LLMClient(provider="openai")
        client.model = "gpt-4"
        
        # Test OpenAI cost calculation
        cost = client._calculate_cost("openai", 1000, 500)
        
        # gpt-4 costs: input=$0.03/1k, output=$0.06/1k
        expected_cost = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert abs(cost - expected_cost) < 0.001
        
        # Test Gemini cost calculation
        client.model = "gemini-pro"
        cost = client._calculate_cost("gemini", 1000, 500)
        
        # gemini-pro costs: input=$0.00025/1k, output=$0.0005/1k
        expected_cost = (1000 / 1000) * 0.00025 + (500 / 1000) * 0.0005
        assert abs(cost - expected_cost) < 0.0001
    
    @patch('src.ai.llm_client.OPENAI_AVAILABLE', True)
    @patch('os.getenv')
    def test_get_available_models(self, mock_getenv):
        """Test getting available models."""
        mock_getenv.return_value = "test_api_key"
        client = LLMClient(provider="openai")
        
        # Mock both clients as available
        client.openai_client = Mock()
        client.gemini_client = Mock()
        
        models = client.get_available_models()
        
        assert isinstance(models, list)
        assert "gpt-4" in models
        assert "gpt-4-turbo" in models
        assert "gpt-3.5-turbo" in models
        assert "gemini-pro" in models
        assert "gemini-pro-vision" in models
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check with healthy client."""
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "OK"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 5
        mock_response.usage = mock_usage
        mock_choice.finish_reason = "stop"
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        health_status = await client.health_check()
        
        assert health_status["provider"] == "openai"
        assert health_status["model"] == "gpt-4"
        assert health_status["status"] == "healthy"
        assert health_status["openai_available"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check with unhealthy client."""
        mock_openai_client = Mock()
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        client.model = "gpt-4"
        
        health_status = await client.health_check()
        
        assert health_status["status"] == "unhealthy"
        assert "error" in health_status
        assert "Connection failed" in health_status["error"]
    
    @pytest.mark.asyncio
    async def test_chat_error_handling(self):
        """Test chat error handling."""
        mock_openai_client = Mock()
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        client = LLMClient(provider="openai")
        client.openai_client = mock_openai_client
        
        with pytest.raises(Exception, match="API Error"):
            await client.chat("Test message")
    
    def test_invalid_provider(self):
        """Test initialization with invalid provider."""
        with pytest.raises(ValueError, match="Provider invalid_provider not available"):
            client = LLMClient(provider="invalid_provider")
            # Force provider check by trying to use it
            client.provider = "invalid_provider"
            client.openai_client = None
            client.gemini_client = None
            asyncio.run(client.chat("test"))


class TestGetLLMClient:
    """Test cases for get_llm_client function."""
    
    def setup_method(self):
        """Reset global client."""
        import src.ai.llm_client
        src.ai.llm_client.llm_client = None
    
    @patch('src.ai.llm_client.LLMClient')
    def test_get_llm_client_singleton(self, mock_llm_client):
        """Test that get_llm_client returns singleton instance."""
        mock_client_instance = Mock()
        mock_llm_client.return_value = mock_client_instance
        
        # First call should create new instance
        client1 = get_llm_client()
        assert client1 == mock_client_instance
        mock_llm_client.assert_called_once()
        
        # Second call should return same instance
        client2 = get_llm_client()
        assert client2 == mock_client_instance
        assert client1 == client2
        # Should not create new instance
        mock_llm_client.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
