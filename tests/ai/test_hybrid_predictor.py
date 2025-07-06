"""Test suite for AI hybrid predictor module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np

from src.ai.hybrid_predictor import HybridPricePredictor


class TestHybridPricePredictor:
    """Test cases for HybridPricePredictor class."""
    
    def setup_method(self):
        """Set up test predictor."""
        with patch('src.ai.hybrid_predictor.get_llm_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            self.predictor = HybridPricePredictor()
            self.mock_llm_client = mock_client
    
    def create_sample_technical_data(self):
        """Create sample technical data for testing."""
        return {
            'rsi_14': 65.5,
            'macd': 150.0,
            'macd_signal': 140.0,
            'macd_hist': 10.0,
            'sma_20': 49500.0,
            'sma_50': 48000.0,
            'ema_12': 50100.0,
            'ema_26': 49900.0,
            'bb_upper': 51000.0,
            'bb_lower': 48000.0,
            'bb_middle': 49500.0,
            'volume': 1000000.0,
            'volatility': 0.025,
            'price_change_24h': 2.5
        }
    
    def test_hybrid_predictor_initialization(self):
        """Test HybridPricePredictor initialization."""
        assert self.predictor is not None
        assert hasattr(self.predictor, 'traditional_model')
        assert hasattr(self.predictor, 'llm_client')
        assert self.predictor.llm_client is not None
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_success(self):
        """Test successful price movement prediction."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = "Bitcoin shows strong institutional adoption with major ETF approvals"
        
        # Mock LLM response
        mock_llm_response = {
            "expected_direction": "bullish",
            "confidence": 0.75,
            "recommended_strategy": "buy",
            "risk_assessment": "medium",
            "reasoning": "Strong technical indicators combined with positive news sentiment"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert isinstance(result, dict)
        assert "direction" in result
        assert "confidence" in result
        assert "strategy" in result
        assert "reasoning" in result
        
        assert result["direction"] == "bullish"
        assert result["confidence"] == 0.75
        assert result["strategy"] == "buy"
        assert "Strong technical indicators" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_llm_error(self):
        """Test price movement prediction with LLM error."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = "Test news data"
        
        # Mock LLM error
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM API error"))
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert isinstance(result, dict)
        assert result["prediction"] == "uncertain"
        assert result["confidence"] == 0.5
        assert result["strategy"] == "hold"
        assert "Error in prediction process" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_with_different_symbols(self):
        """Test price movement prediction with different symbols."""
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        technical_data = self.create_sample_technical_data()
        news_data = "General crypto market positive sentiment"
        
        mock_llm_response = {
            "expected_direction": "neutral",
            "confidence": 0.6,
            "recommended_strategy": "hold",
            "risk_assessment": "low",
            "reasoning": "Mixed signals from technical and fundamental analysis"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        for symbol in symbols:
            result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
            
            assert isinstance(result, dict)
            assert result["direction"] == "neutral"
            assert result["confidence"] == 0.6
            assert result["strategy"] == "hold"
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_with_minimal_data(self):
        """Test price movement prediction with minimal technical data."""
        symbol = "BTC/USDT"
        technical_data = {"rsi_14": 50.0, "price": 50000.0}
        news_data = "Minimal news data"
        
        mock_llm_response = {
            "expected_direction": "uncertain",
            "confidence": 0.4,
            "recommended_strategy": "wait",
            "risk_assessment": "high",
            "reasoning": "Insufficient data for reliable prediction"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert isinstance(result, dict)
        assert result["direction"] == "uncertain"
        assert result["confidence"] == 0.4
        assert result["strategy"] == "wait"
    
    def test_predict_with_traditional_model(self):
        """Test traditional ML model prediction."""
        technical_data = self.create_sample_technical_data()
        
        result = self.predictor._predict_with_traditional_model(technical_data)
        
        assert isinstance(result, dict)
        assert "prediction" in result
        assert "probability" in result
        
        # Check that it returns reasonable values
        assert result["prediction"] in ["buy", "sell", "hold"]
        assert 0 <= result["probability"] <= 1
    
    def test_construct_contextual_prompt(self):
        """Test contextual prompt construction."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_text = "Bitcoin price surges amid institutional interest"
        
        prompt = self.predictor._construct_contextual_prompt(symbol, technical_data, news_text)
        
        assert isinstance(prompt, str)
        assert symbol in prompt
        assert str(technical_data["rsi_14"]) in prompt
        assert news_text in prompt
        assert "Technical analysis" in prompt
        assert "News sentiment" in prompt
        assert "Market conditions" in prompt
    
    def test_get_expected_llm_schema(self):
        """Test LLM schema structure."""
        schema = self.predictor._get_expected_llm_schema()
        
        assert isinstance(schema, dict)
        assert "expected_direction" in schema
        assert "confidence" in schema
        assert "recommended_strategy" in schema
        assert "risk_assessment" in schema
        assert "reasoning" in schema
        
        # Check data types
        assert schema["expected_direction"] == "string"
        assert schema["confidence"] == "number"
        assert schema["recommended_strategy"] == "string"
        assert schema["risk_assessment"] == "string"
        assert schema["reasoning"] == "string"
    
    def test_combine_predictions_balanced(self):
        """Test prediction combination with balanced inputs."""
        tech_result = {
            "prediction": "buy",
            "probability": 0.7
        }
        
        llm_result = {
            "expected_direction": "bullish",
            "confidence": 0.8,
            "recommended_strategy": "accumulate",
            "risk_assessment": "medium",
            "reasoning": "Strong technical and fundamental signals"
        }
        
        combined = self.predictor._combine_predictions(tech_result, llm_result)
        
        assert isinstance(combined, dict)
        assert combined["direction"] == "bullish"
        assert combined["confidence"] == 0.8
        assert combined["strategy"] == "accumulate"
        assert combined["reasoning"] == "Strong technical and fundamental signals"
    
    def test_combine_predictions_missing_llm_data(self):
        """Test prediction combination with missing LLM data."""
        tech_result = {
            "prediction": "sell",
            "probability": 0.6
        }
        
        llm_result = {}  # Empty LLM result
        
        combined = self.predictor._combine_predictions(tech_result, llm_result)
        
        assert isinstance(combined, dict)
        assert combined["direction"] == "sell"  # Fallback to tech result
        assert combined["confidence"] == 0.6
        assert combined["strategy"] == "hold"  # Default strategy
        assert combined["reasoning"] == "Default reasoning"
    
    def test_combine_predictions_conflicting_signals(self):
        """Test prediction combination with conflicting signals."""
        tech_result = {
            "prediction": "buy",
            "probability": 0.8
        }
        
        llm_result = {
            "expected_direction": "bearish",
            "confidence": 0.7,
            "recommended_strategy": "sell",
            "risk_assessment": "high",
            "reasoning": "Negative news sentiment overrides technical signals"
        }
        
        combined = self.predictor._combine_predictions(tech_result, llm_result)
        
        assert isinstance(combined, dict)
        # LLM result should take precedence
        assert combined["direction"] == "bearish"
        assert combined["confidence"] == 0.7
        assert combined["strategy"] == "sell"
        assert "Negative news sentiment" in combined["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_various_directions(self):
        """Test price movement prediction with various direction outputs."""
        symbol = "ETH/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = "Ethereum network upgrade completed successfully"
        
        directions = ["bullish", "bearish", "neutral", "uncertain"]
        
        for direction in directions:
            mock_llm_response = {
                "expected_direction": direction,
                "confidence": 0.65,
                "recommended_strategy": "monitor",
                "risk_assessment": "medium",
                "reasoning": f"Analysis indicates {direction} outlook"
            }
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
            
            assert result["direction"] == direction
            assert result["confidence"] == 0.65
            assert direction in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_confidence_levels(self):
        """Test price movement prediction with various confidence levels."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = "Market analysis shows mixed signals"
        
        confidence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for confidence in confidence_levels:
            mock_llm_response = {
                "expected_direction": "neutral",
                "confidence": confidence,
                "recommended_strategy": "hold",
                "risk_assessment": "medium",
                "reasoning": f"Confidence level at {confidence}"
            }
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
            
            assert result["confidence"] == confidence
            assert str(confidence) in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_with_complex_technical_data(self):
        """Test price movement prediction with complex technical indicators."""
        symbol = "BTC/USDT"
        
        # Complex technical data with many indicators
        technical_data = {
            'rsi_14': 75.0,  # Overbought
            'rsi_7': 80.0,
            'macd': -50.0,   # Bearish
            'macd_signal': -40.0,
            'macd_hist': -10.0,
            'sma_20': 49500.0,
            'sma_50': 50000.0,  # Price below SMA
            'sma_200': 48000.0,
            'ema_12': 49800.0,
            'ema_26': 50100.0,
            'bb_upper': 52000.0,
            'bb_lower': 47000.0,
            'bb_middle': 49500.0,
            'stoch_k': 85.0,  # Overbought
            'stoch_d': 80.0,
            'cci': 120.0,     # Overbought
            'williams_r': -15.0,  # Overbought
            'atr': 500.0,
            'volume': 1500000.0,
            'volatility': 0.035,
            'price_change_24h': -3.2,
            'volume_change_24h': 25.0
        }
        
        news_data = "Mixed market sentiment with regulatory concerns"
        
        mock_llm_response = {
            "expected_direction": "bearish",
            "confidence": 0.72,
            "recommended_strategy": "reduce_position",
            "risk_assessment": "high",
            "reasoning": "Multiple overbought indicators with bearish MACD suggest downward pressure"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert result["direction"] == "bearish"
        assert result["confidence"] == 0.72
        assert result["strategy"] == "reduce_position"
        assert "overbought" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_empty_news(self):
        """Test price movement prediction with empty news data."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = ""
        
        mock_llm_response = {
            "expected_direction": "neutral",
            "confidence": 0.5,
            "recommended_strategy": "wait",
            "risk_assessment": "medium",
            "reasoning": "Technical analysis only - no news sentiment available"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert result["direction"] == "neutral"
        assert result["confidence"] == 0.5
        assert result["strategy"] == "wait"
        assert "Technical analysis only" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_long_news(self):
        """Test price movement prediction with long news data."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        
        # Long news data
        news_data = """
        Bitcoin has experienced significant volatility over the past week as institutional investors 
        continue to show interest in cryptocurrency markets. Major financial institutions have 
        announced plans to integrate Bitcoin into their portfolios, while regulatory concerns 
        persist in various jurisdictions. The Federal Reserve's recent statements on monetary 
        policy have also influenced crypto market sentiment. Technical analysis shows mixed 
        signals with some indicators suggesting bullish momentum while others point to potential 
        resistance levels. Trading volume has increased substantially, indicating heightened 
        market participation and interest from both retail and institutional investors.
        """
        
        mock_llm_response = {
            "expected_direction": "bullish",
            "confidence": 0.68,
            "recommended_strategy": "accumulate_gradually",
            "risk_assessment": "medium",
            "reasoning": "Institutional interest and increased volume support bullish outlook despite regulatory uncertainty"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert result["direction"] == "bullish"
        assert result["confidence"] == 0.68
        assert result["strategy"] == "accumulate_gradually"
        assert "Institutional interest" in result["reasoning"]
    
    def test_train_model_placeholder(self):
        """Test the train model placeholder method."""
        # This is a placeholder method, so we just test it doesn't crash
        try:
            self.predictor._train_model("dummy_data")
            assert True  # If no exception, test passes
        except Exception as e:
            pytest.fail(f"_train_model raised an exception: {e}")
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_invalid_technical_data(self):
        """Test price movement prediction with invalid technical data."""
        symbol = "BTC/USDT"
        technical_data = None  # Invalid data
        news_data = "Test news"
        
        # Should handle gracefully
        mock_llm_response = {
            "expected_direction": "uncertain",
            "confidence": 0.3,
            "recommended_strategy": "wait",
            "risk_assessment": "high",
            "reasoning": "Insufficient technical data for analysis"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert result["direction"] == "uncertain"
        assert result["confidence"] == 0.3
        assert result["strategy"] == "wait"
    
    @pytest.mark.asyncio
    async def test_predict_price_movement_llm_timeout(self):
        """Test price movement prediction with LLM timeout."""
        symbol = "BTC/USDT"
        technical_data = self.create_sample_technical_data()
        news_data = "Test news data"
        
        # Mock timeout error
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))
        
        result = await self.predictor.predict_price_movement(symbol, technical_data, news_data)
        
        assert isinstance(result, dict)
        assert result["prediction"] == "uncertain"
        assert result["confidence"] == 0.5
        assert result["strategy"] == "hold"
        assert "Error in prediction process" in result["reasoning"]


if __name__ == '__main__':
    pytest.main([__file__])
