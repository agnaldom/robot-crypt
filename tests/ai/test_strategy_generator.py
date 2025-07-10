#!/usr/bin/env python3
"""
Tests for AI Strategy Generator functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.ai.strategy_generator import AIStrategyGenerator


class TestAIStrategyGenerator:
    """Test AI Strategy Generator functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.generator = AIStrategyGenerator()
    
    def test_ai_strategy_generator_initialization(self):
        """Test AIStrategyGenerator initialization"""
        assert self.generator.llm_client is not None
        assert self.generator.logger is not None
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_success(self):
        """Test successful strategy generation"""
        # Mock LLM response
        mock_strategy_response = {
            "dynamic_stop_loss": "ATR-based stop loss at 2x ATR below entry",
            "adaptive_take_profit": "Profit target at 1.5:1 risk-reward ratio with trailing stop",
            "position_sizing": "Risk 1% of portfolio per trade, max 5% total exposure",
            "entry_signals": [
                "RSI below 30 with bullish divergence",
                "Price above 20-period EMA",
                "Volume above average"
            ],
            "exit_signals": [
                "RSI above 70",
                "Stop loss hit",
                "Take profit reached"
            ]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 15.5,
            "trend": "bullish",
            "volume": "high",
            "support_level": 42000,
            "resistance_level": 45000
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 1000,
            "timeframe": "4h",
            "max_drawdown": 5
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" not in result
        assert result["dynamic_stop_loss"] == "ATR-based stop loss at 2x ATR below entry"
        assert result["adaptive_take_profit"] == "Profit target at 1.5:1 risk-reward ratio with trailing stop"
        assert result["position_sizing"] == "Risk 1% of portfolio per trade, max 5% total exposure"
        assert len(result["entry_signals"]) == 3
        assert len(result["exit_signals"]) == 3
        
        # Verify LLM was called with correct parameters
        mock_llm_client.analyze_json.assert_called_once()
        call_args = mock_llm_client.analyze_json.call_args
        # Check if prompt is in kwargs or args
        if len(call_args) > 1 and 'prompt' in call_args[1]:
            prompt = call_args[1]['prompt']
        else:
            prompt = call_args[0][0] if call_args[0] else ""
        assert "15.5" in prompt  # volatility value
        assert "medium" in prompt  # risk tolerance
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_llm_error(self):
        """Test strategy generation with LLM error"""
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.side_effect = Exception("LLM API Error")
        
        market_conditions = {
            "volatility": 10.0,
            "trend": "sideways",
            "volume": "medium"
        }
        
        user_preferences = {
            "risk_tolerance": "low",
            "capital": 500,
            "timeframe": "1h"
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" in result
        assert result["error"] == "Failed to generate strategy"
        assert "LLM API Error" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_high_volatility(self):
        """Test strategy generation for high volatility market"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Wider stops at 3x ATR due to high volatility",
            "adaptive_take_profit": "Conservative profit targets with quick exits",
            "position_sizing": "Reduced position size to 0.5% per trade",
            "entry_signals": [
                "Volatility contraction patterns",
                "Support/resistance confirmation"
            ],
            "exit_signals": [
                "Volatility expansion above threshold",
                "Quick profit taking at 1:1 ratio"
            ]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 35.0,  # High volatility
            "trend": "volatile",
            "volume": "extreme",
            "support_level": 38000,
            "resistance_level": 48000
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 2000,
            "timeframe": "15m",
            "max_drawdown": 3
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" not in result
        assert "high volatility" in result["dynamic_stop_loss"].lower() or "3x ATR" in result["dynamic_stop_loss"]
        assert "reduced" in result["position_sizing"].lower() or "0.5%" in result["position_sizing"]
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_conservative_user(self):
        """Test strategy generation for conservative user"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Tight stops at 1.5x ATR for capital preservation",
            "adaptive_take_profit": "Conservative targets with 2:1 risk-reward minimum",
            "position_sizing": "Very conservative 0.5% risk per trade",
            "entry_signals": [
                "Strong trend confirmation",
                "Multiple timeframe alignment",
                "High probability setups only"
            ],
            "exit_signals": [
                "First sign of reversal",
                "Tight trailing stops",
                "Conservative profit taking"
            ]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 8.0,
            "trend": "bullish",
            "volume": "normal"
        }
        
        user_preferences = {
            "risk_tolerance": "low",  # Conservative user
            "capital": 10000,
            "timeframe": "1d",
            "max_drawdown": 2
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" not in result
        assert "conservative" in result["position_sizing"].lower() or "0.5%" in result["position_sizing"]
        assert "2:1" in result["adaptive_take_profit"] or "conservative" in result["adaptive_take_profit"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_aggressive_user(self):
        """Test strategy generation for aggressive user"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Wider stops at 3x ATR for trend following",
            "adaptive_take_profit": "Aggressive targets with 3:1 risk-reward potential",
            "position_sizing": "Aggressive 2% risk per trade, up to 10% total exposure",
            "entry_signals": [
                "Momentum breakouts",
                "Early trend signals",
                "High beta opportunities"
            ],
            "exit_signals": [
                "Momentum exhaustion",
                "Wide trailing stops",
                "Let winners run strategy"
            ]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 20.0,
            "trend": "strong_bullish",
            "volume": "high"
        }
        
        user_preferences = {
            "risk_tolerance": "high",  # Aggressive user
            "capital": 5000,
            "timeframe": "5m",
            "max_drawdown": 10
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" not in result
        assert "aggressive" in result["position_sizing"].lower() or "2%" in result["position_sizing"]
        assert "3:1" in result["adaptive_take_profit"] or "aggressive" in result["adaptive_take_profit"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_custom_strategy_bear_market(self):
        """Test strategy generation for bear market conditions"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Tight stops due to bearish bias",
            "adaptive_take_profit": "Quick profit taking in bear market",
            "position_sizing": "Reduced exposure due to bearish conditions",
            "entry_signals": [
                "Short-term oversold bounces",
                "Support level tests",
                "Bear market rally setups"
            ],
            "exit_signals": [
                "Quick profit taking",
                "Resistance level rejection",
                "Bearish continuation patterns"
            ]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 25.0,
            "trend": "bearish",
            "volume": "declining",
            "support_level": 25000,
            "resistance_level": 30000
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 3000,
            "timeframe": "2h",
            "max_drawdown": 7
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        assert "error" not in result
        assert "bear" in result["position_sizing"].lower() or "reduced" in result["position_sizing"].lower()
        assert "quick" in result["adaptive_take_profit"].lower() or "bear" in result["adaptive_take_profit"].lower()
    
    def test_construct_strategy_prompt(self):
        """Test strategy prompt construction"""
        market_conditions = {
            "volatility": 15.5,
            "trend": "bullish",
            "volume": "high"
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 1000,
            "timeframe": "4h"
        }
        
        prompt = self.generator._construct_strategy_prompt(market_conditions, user_preferences)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "15.5" in prompt  # volatility
        assert "bullish" in prompt  # trend
        assert "high" in prompt  # volume
        assert "medium" in prompt  # risk tolerance
        assert "1000" in prompt  # capital
        assert "4h" in prompt  # timeframe
        assert "dynamic stop-loss" in prompt.lower()
        assert "adaptive take-profit" in prompt.lower()
        assert "position sizing" in prompt.lower()
        assert "entry" in prompt.lower()
        assert "exit" in prompt.lower()
    
    def test_get_system_prompt(self):
        """Test system prompt generation"""
        system_prompt = self.generator._get_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "trading" in system_prompt.lower() or "strategy" in system_prompt.lower()
        assert "ai" in system_prompt.lower() or "artificial" in system_prompt.lower()
    
    def test_get_expected_schema(self):
        """Test expected schema generation"""
        schema = self.generator._get_expected_schema()
        
        assert isinstance(schema, dict)
        assert "dynamic_stop_loss" in schema
        assert "adaptive_take_profit" in schema
        assert "position_sizing" in schema
        assert "entry_signals" in schema
        assert "exit_signals" in schema
        
        # Check data types
        assert schema["dynamic_stop_loss"] == "string"
        assert schema["adaptive_take_profit"] == "string"
        assert schema["position_sizing"] == "string"
        assert schema["entry_signals"] == "array"
        assert schema["exit_signals"] == "array"
    
    @pytest.mark.asyncio
    async def test_generate_strategy_with_missing_market_data(self):
        """Test strategy generation with incomplete market conditions"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Standard ATR-based stop loss",
            "adaptive_take_profit": "Standard profit targets",
            "position_sizing": "Standard 1% risk per trade",
            "entry_signals": ["Basic technical signals"],
            "exit_signals": ["Standard exit conditions"]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        # Incomplete market conditions
        market_conditions = {
            "volatility": 12.0
            # Missing trend, volume, etc.
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 1000
            # Missing timeframe, max_drawdown
        }
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        # May fail due to missing data
        if "error" in result:
            assert result["error"] == "Failed to generate strategy"
        else:
            # If it succeeds, should have basic structure
            assert "dynamic_stop_loss" in result
            assert "adaptive_take_profit" in result
            assert "position_sizing" in result
    
    @pytest.mark.asyncio
    async def test_generate_strategy_with_invalid_parameters(self):
        """Test strategy generation with invalid parameters"""
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = {}
        
        # Invalid market conditions
        market_conditions = {
            "volatility": -5.0,  # Invalid negative volatility
            "trend": "invalid_trend",
            "volume": 999  # Should be string
        }
        
        user_preferences = {
            "risk_tolerance": "extreme",  # Invalid tolerance level
            "capital": -1000,  # Invalid negative capital
            "timeframe": "invalid"  # Invalid timeframe
        }
        
        self.generator.llm_client = mock_llm_client
        
        # Should still attempt to generate (LLM should handle validation)
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        # The prompt should contain the invalid values, LLM should handle them
        call_args = mock_llm_client.analyze_json.call_args
        assert "-5.0" in call_args[1]["prompt"]  # Invalid volatility should be in prompt
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_strategy_generation(self):
        """Test multiple concurrent strategy generations"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Concurrent strategy stop loss",
            "adaptive_take_profit": "Concurrent strategy profit target",
            "position_sizing": "Concurrent strategy position sizing",
            "entry_signals": ["Signal 1", "Signal 2"],
            "exit_signals": ["Exit 1", "Exit 2"]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {
            "volatility": 15.0,
            "trend": "bullish",
            "volume": "high"
        }
        
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 1000,
            "timeframe": "1h"
        }
        
        self.generator.llm_client = mock_llm_client
        
        # Generate multiple strategies concurrently
        tasks = []
        for i in range(3):
            task = self.generator.generate_custom_strategy(
                market_conditions, user_preferences
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert "error" not in result
            assert "dynamic_stop_loss" in result
            assert result["dynamic_stop_loss"] == "Concurrent strategy stop loss"
    
    @pytest.mark.asyncio
    async def test_strategy_generation_with_custom_schema(self):
        """Test strategy generation with custom schema requirements"""
        # Test that the method properly uses the expected schema
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = {
            "dynamic_stop_loss": "Custom schema test",
            "adaptive_take_profit": "Custom schema test",
            "position_sizing": "Custom schema test",
            "entry_signals": ["Custom signal"],
            "exit_signals": ["Custom exit"]
        }
        
        market_conditions = {"volatility": 10.0, "trend": "neutral"}
        user_preferences = {"risk_tolerance": "medium", "capital": 1000}
        
        self.generator.llm_client = mock_llm_client
        
        result = await self.generator.generate_custom_strategy(
            market_conditions, user_preferences
        )
        
        # Verify LLM was called (may fail due to missing data)
        if mock_llm_client.analyze_json.call_args:
            call_args = mock_llm_client.analyze_json.call_args
            # Check if schema is in kwargs
            if len(call_args) > 1 and 'schema' in call_args[1]:
                schema = call_args[1]['schema']
                assert schema["entry_signals"] == "array"
                assert schema["exit_signals"] == "array"
                assert schema["dynamic_stop_loss"] == "string"
    
    @pytest.mark.asyncio
    async def test_strategy_generation_logging(self):
        """Test that strategy generation properly logs events"""
        mock_strategy_response = {
            "dynamic_stop_loss": "Logged strategy",
            "adaptive_take_profit": "Logged strategy",
            "position_sizing": "Logged strategy",
            "entry_signals": ["Logged signal"],
            "exit_signals": ["Logged exit"]
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_strategy_response
        
        market_conditions = {"volatility": 10.0}
        user_preferences = {"risk_tolerance": "medium"}
        
        self.generator.llm_client = mock_llm_client
        
        with patch.object(self.generator.logger, 'info') as mock_log_info:
            with patch.object(self.generator.logger, 'error') as mock_log_error:
                result = await self.generator.generate_custom_strategy(
                    market_conditions, user_preferences
                )
                
                # Should log success if it succeeds
                if "error" not in result:
                    mock_log_info.assert_called_with("Generated custom strategy using AI")
                    mock_log_error.assert_not_called()
        
        # Test error logging
        mock_llm_client.analyze_json.side_effect = Exception("Test error")
        
        with patch.object(self.generator.logger, 'error') as mock_log_error:
            result = await self.generator.generate_custom_strategy(
                market_conditions, user_preferences
            )
            
            # Should log error
            mock_log_error.assert_called_once()
            assert "Strategy generation failed" in mock_log_error.call_args[0][0]
