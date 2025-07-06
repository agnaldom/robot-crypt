"""Test suite for AI strategy generator module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.ai.strategy_generator import AIStrategyGenerator


class TestAIStrategyGenerator:
    """Test cases for AIStrategyGenerator class."""
    
    def setup_method(self):
        """Set up test strategy generator."""
        with patch('src.ai.strategy_generator.get_llm_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            self.generator = AIStrategyGenerator()
            self.mock_llm_client = mock_client
    
    def create_sample_market_conditions(self):
        """Create sample market conditions for testing."""
        return {
            'volatility': 35.0,
            'trend': 'upward',
            'volume': 'high',
            'market_sentiment': 'positive'
        }
    
    def create_sample_user_preferences(self):
        """Create sample user preferences for testing."""
        return {
            'risk_tolerance': 'medium',
            'capital': 10000.0,
            'timeframe': 'daily'
        }
    
    def test_strategy_generator_initialization(self):
        """Test AIStrategyGenerator initialization."""
        assert self.generator is not None
        assert hasattr(self.generator, 'llm_client')
        assert self.generator.llm_client is not None
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_success(self):
        """Test successful strategy generation."""
        market_conditions = self.create_sample_market_conditions()
        user_preferences = self.create_sample_user_preferences()
        
        # Mock LLM response
        mock_llm_response = {
            "dynamic_stop_loss": "Set stop-loss at 2% below support",
            "adaptive_take_profit": "Adjust take-profit targets to previous highs",
            "position_sizing": "Allocate 5% of capital per trade",
            "entry_signals": ["Breakout above resistance", "Bullish MACD crossover"],
            "exit_signals": ["Price falls below 20-day MA", "Bearish MACD reversal"]
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.generator.generate_custom_strategy(market_conditions, user_preferences)
        
        assert isinstance(result, dict)
        assert "dynamic_stop_loss" in result
        assert "adaptive_take_profit" in result
        assert "position_sizing" in result
        assert len(result["entry_signals"]) == 2
        assert len(result["exit_signals"]) == 2
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_error_handling(self):
        """Test strategy generation error handling."""
        market_conditions = self.create_sample_market_conditions()
        user_preferences = self.create_sample_user_preferences()
        
        # Mock LLM error
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM API error"))
        
        result = await self.generator.generate_custom_strategy(market_conditions, user_preferences)
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Failed to generate strategy"
        assert "LLM API error" in result["reason"]
    
    def test_construct_strategy_prompt(self):
        """Test strategy prompt construction."""
        market_conditions = self.create_sample_market_conditions()
        user_preferences = self.create_sample_user_preferences()
        
        prompt = self.generator._construct_strategy_prompt(market_conditions, user_preferences)
        
        assert isinstance(prompt, str)
        assert "Based on the current market conditions and user preferences" in prompt
        assert "Volatility: 35.0%" in prompt
        assert "Trend: upward" in prompt
        assert "Risk Tolerance: medium" in prompt
        assert "Available Capital: 10000.0" in prompt
    
    def test_get_system_prompt(self):
        """Test system prompt structure."""
        system_prompt = self.generator._get_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert "AI specializing in virtual asset trading strategies" in system_prompt
        assert "Generate logical, efficient, and realistic strategies" in system_prompt
    
    def test_get_expected_schema(self):
        """Test expected schema structure."""
        schema = self.generator._get_expected_schema()
        
        assert isinstance(schema, dict)
        assert "dynamic_stop_loss" in schema
        assert "adaptive_take_profit" in schema
        assert "position_sizing" in schema
        assert "entry_signals" in schema
        assert "exit_signals" in schema


if __name__ == '__main__':
    pytest.main([__file__])

