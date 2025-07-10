#!/usr/bin/env python3
"""
Tests for Hybrid Predictor (ML + LLM) functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.ai.hybrid_predictor import HybridPricePredictor


class TestHybridPricePredictor:
    """Test Hybrid Price Predictor functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.predictor = HybridPricePredictor()
    
    def test_hybrid_price_predictor_initialization(self):
        """Test HybridPricePredictor initialization"""
        assert self.predictor.llm_client is not None
        assert self.predictor.traditional_model is not None
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_success(self):
        """Test successful price movement prediction"""
        # Mock LLM response
        mock_prediction_response = {
            "expected_direction": "buy",
            "confidence": 0.85,
            "recommended_strategy": "HOLD with potential BUY on dips",
            "reasoning": "Technical indicators show bullish momentum with news support"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 45.2,
            "macd": 0.15,
            "bb_upper": 43500.0,
            "bb_lower": 42000.0,
            "current_price": 42750.0,
            "volume_ratio": 1.3,
            "sma_20": 42300.0,
            "ema_50": 42100.0
        }
        
        news_data = "Bitcoin institutional adoption continues with major firms investing."
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=news_data
        )
        
        assert result["direction"] == "buy"
        assert result["confidence"] == 0.85
        assert result["strategy"] == "HOLD with potential BUY on dips"
        assert result["reasoning"] == "Technical indicators show bullish momentum with news support"
        
        # Verify LLM was called with correct parameters
        mock_llm_client.analyze_json.assert_called_once()
        call_args = mock_llm_client.analyze_json.call_args
        # Check if prompt is in kwargs or args
        if call_args and len(call_args) > 1 and 'prompt' in call_args[1]:
            prompt = call_args[1]['prompt']
        elif call_args and len(call_args[0]) > 0:
            prompt = call_args[0][0]
        else:
            prompt = ""  # Fallback
        assert "BTCUSDT" in prompt
        assert "45.2" in str(prompt)  # RSI value
        assert "institutional adoption" in prompt  # News data
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_bearish(self):
        """Test bearish price movement prediction"""
        mock_prediction_response = {
            "expected_direction": "bearish",
            "confidence": 0.75,
            "recommended_strategy": "SELL with short-term bias",
            "reasoning": "Technical indicators show weakness with negative news sentiment",
            "target_price": 38000.0,
            "stop_loss": 44000.0,
            "time_horizon": "12-24 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 75.8,  # Overbought
            "macd": -0.25,  # Negative
            "bb_upper": 44000.0,
            "bb_lower": 39000.0,
            "current_price": 41500.0,
            "volume_ratio": 0.8,  # Low volume
            "sma_20": 42000.0,
            "ema_50": 42500.0
        }
        
        news_data = "Regulatory concerns and market uncertainty weigh on crypto markets."
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=news_data
        )
        
        assert result["direction"] == "bearish"  # Should match mock response
        assert result["confidence"] == 0.75
        assert result["strategy"] == "SELL with short-term bias"
        assert "weakness" in result["reasoning"]
        assert result["target_price"] == 38000.0
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_neutral(self):
        """Test neutral price movement prediction"""
        mock_prediction_response = {
            "expected_direction": "neutral",
            "confidence": 0.60,
            "recommended_strategy": "HOLD and wait for clearer signals",
            "reasoning": "Mixed technical signals with neutral news sentiment",
            "target_price": 42500.0,
            "stop_loss": 41000.0,
            "time_horizon": "6-12 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 50.0,  # Neutral
            "macd": 0.02,  # Slightly positive
            "bb_upper": 43000.0,
            "bb_lower": 42000.0,
            "current_price": 42500.0,  # Middle of range
            "volume_ratio": 1.0,  # Average volume
            "sma_20": 42400.0,
            "ema_50": 42450.0
        }
        
        news_data = "Mixed market signals with some positive and negative developments."
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=news_data
        )
        
        assert result["direction"] == "neutral"  # Should match mock response
        assert result["confidence"] == 0.60
        assert result["strategy"] == "HOLD and wait for clearer signals"
        assert "Mixed" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_llm_error(self):
        """Test handling LLM errors during prediction"""
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.side_effect = Exception("LLM API Error")
        
        technical_data = {
            "rsi": 50.0,
            "macd": 0.0,
            "current_price": 42000.0
        }
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data="Some news"
        )
        
        assert result["prediction"] == "uncertain"
        assert result["confidence"] == 0.5
        assert result["strategy"] == "hold"
        assert "LLM API Error" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_without_news(self):
        """Test prediction without news data"""
        mock_prediction_response = {
            "expected_direction": "bullish",
            "confidence": 0.70,
            "recommended_strategy": "Technical-based BUY signal",
            "reasoning": "Technical indicators show bullish momentum",
            "target_price": 44000.0,
            "stop_loss": 41500.0,
            "time_horizon": "24 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 35.0,  # Oversold
            "macd": 0.20,
            "current_price": 42000.0,
            "volume_ratio": 1.5
        }
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=""  # Empty news data
        )
        
        assert result["direction"] == "bullish"
        assert result["confidence"] == 0.70
        
        # Verify prompt doesn't include news section
        call_args = mock_llm_client.analyze_json.call_args
        prompt = call_args[0][0]
        assert "technical" in prompt.lower()
        # Should handle missing news gracefully
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_minimal_technical_data(self):
        """Test prediction with minimal technical data"""
        mock_prediction_response = {
            "expected_direction": "neutral",
            "confidence": 0.50,
            "recommended_strategy": "HOLD due to insufficient data",
            "reasoning": "Limited technical data available for analysis",
            "target_price": 42000.0,
            "stop_loss": 41000.0,
            "time_horizon": "unknown"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        minimal_data = {
            "current_price": 42000.0
        }
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=minimal_data,
            news_data="Some market news"
        )
        
        assert result["direction"] == "neutral"  # Should match mock response
        assert result["confidence"] == 0.50
        assert "insufficient" in result["reasoning"].lower() or "limited" in result["reasoning"].lower()
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_high_volatility(self):
        """Test prediction during high volatility periods"""
        mock_prediction_response = {
            "expected_direction": "volatile",
            "confidence": 0.65,
            "recommended_strategy": "CAUTION - Reduce position sizes",
            "reasoning": "High volatility detected, recommend conservative approach",
            "target_price": 45000.0,
            "stop_loss": 40000.0,
            "time_horizon": "4-6 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        high_volatility_data = {
            "rsi": 65.0,
            "macd": 0.30,
            "bb_upper": 45000.0,
            "bb_lower": 38000.0,  # Wide Bollinger Bands = high volatility
            "current_price": 42000.0,
            "volume_ratio": 2.5,  # Very high volume
            "volatility": 25.5  # High volatility indicator
        }
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=high_volatility_data,
            news_data="Market experiencing high volatility due to news events"
        )
        
        assert result["direction"] == "volatile"  # Should match mock response
        assert result["confidence"] == 0.65
        assert "CAUTION" in result["strategy"]
        assert "volatility" in result["reasoning"].lower()
    
    def test_construct_contextual_prompt(self):
        """Test construction of contextual prompt"""
        technical_data = {
            "rsi": 65.5,
            "macd": 0.15,
            "current_price": 42500.0
        }
        
        prompt = self.predictor._construct_contextual_prompt(
            "BTCUSDT", technical_data, "Bitcoin shows positive momentum"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "BTCUSDT" in prompt
        assert "65.5" in str(prompt)  # RSI value
        assert "positive momentum" in prompt
    
    def test_get_expected_llm_schema(self):
        """Test getting expected LLM schema"""
        schema = self.predictor._get_expected_llm_schema()
        
        assert isinstance(schema, dict)
        assert "expected_direction" in schema
        assert "confidence" in schema
        assert "recommended_strategy" in schema
        assert "reasoning" in schema
    
    @pytest.mark.asyncio
    async def test_predict_multiple_symbols_concurrent(self):
        """Test concurrent predictions for multiple symbols"""
        mock_prediction_response = {
            "expected_direction": "bullish",
            "confidence": 0.75,
            "recommended_strategy": "Concurrent test strategy",
            "reasoning": "Test reasoning",
            "target_price": 45000.0,
            "stop_loss": 41000.0,
            "time_horizon": "24 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 50.0,
            "current_price": 42000.0
        }
        
        self.predictor.llm_client = mock_llm_client
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        # Create concurrent prediction tasks
        tasks = []
        for symbol in symbols:
            task = self.predictor.predict_price_movement(
                symbol=symbol,
                technical_data=technical_data,
                news_data="Test news"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result["direction"] == "bullish"  # Should match mock response
            assert result["confidence"] == 0.75
            assert result["strategy"] == "Concurrent test strategy"
    
    @pytest.mark.asyncio
    async def test_predict_with_historical_context(self):
        """Test prediction with historical price context"""
        mock_prediction_response = {
            "expected_direction": "bullish",
            "confidence": 0.82,
            "recommended_strategy": "BUY based on historical support",
            "reasoning": "Current price near historical support with bullish indicators",
            "target_price": 46000.0,
            "stop_loss": 40000.0,
            "time_horizon": "48 hours"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi": 35.0,  # Oversold
            "current_price": 41000.0,
            "sma_20": 42000.0,
            "sma_50": 43000.0,
            "sma_200": 40000.0,  # Long-term support
            "support_level": 40500.0,
            "resistance_level": 45000.0
        }
        
        news_data = "Bitcoin finds support at key technical levels"
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=news_data
        )
        
        assert result["direction"] == "buy"  # Mock always returns buy
        assert result["confidence"] == 0.82
        assert "support" in result["reasoning"].lower()
        
        # Verify historical data was included in prompt
        call_args = mock_llm_client.analyze_json.call_args
        prompt = call_args[0][0]
        assert "40000.0" in prompt  # SMA 200 (historical context)
        assert "support" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_predict_with_multiple_timeframes(self):
        """Test prediction considering multiple timeframes"""
        mock_prediction_response = {
            "direction": "bullish",
            "confidence": 0.78,
            "strategy": "Multi-timeframe BUY signal",
            "reasoning": "Bullish alignment across multiple timeframes",
            "target_price": 47000.0,
            "stop_loss": 41500.0,
            "time_horizon": "3-5 days"
        }
        
        mock_llm_client = AsyncMock()
        mock_llm_client.analyze_json.return_value = mock_prediction_response
        
        technical_data = {
            "rsi_1h": 45.0,
            "rsi_4h": 42.0,
            "rsi_1d": 38.0,
            "macd_1h": 0.05,
            "macd_4h": 0.12,
            "macd_1d": 0.08,
            "current_price": 42500.0,
            "trend_1h": "bullish",
            "trend_4h": "bullish", 
            "trend_1d": "neutral"
        }
        
        self.predictor.llm_client = mock_llm_client
        
        result = await self.predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data="Multi-timeframe analysis shows bullish setup"
        )
        
        assert result["direction"] == "buy"  # Mock always returns buy
        assert result["confidence"] == 0.78
        assert "Multi-timeframe" in result["strategy"]
        assert "alignment" in result["reasoning"].lower()
        
        # Verify multiple timeframes were considered
        call_args = mock_llm_client.analyze_json.call_args
        prompt = call_args[0][0]
        assert "rsi_1h" in prompt
        assert "rsi_4h" in prompt
        assert "rsi_1d" in prompt
