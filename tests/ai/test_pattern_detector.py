"""Test suite for AI pattern detector module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.ai.pattern_detector import AdvancedPatternDetector


class TestAdvancedPatternDetector:
    """Test cases for AdvancedPatternDetector class."""
    
    def setup_method(self):
        """Set up test pattern detector."""
        with patch('src.ai.pattern_detector.get_llm_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            self.detector = AdvancedPatternDetector()
            self.mock_llm_client = mock_client
    
    def create_sample_price_data(self, num_points=50):
        """Create sample price data for testing."""
        base_price = 50000.0
        data = []
        
        for i in range(num_points):
            price = base_price + (i * 100) + ((-1) ** i * 50)  # Zigzag pattern
            data.append({
                'timestamp': (datetime.now() - timedelta(hours=num_points-i)).isoformat(),
                'open': price - 10,
                'high': price + 20,
                'low': price - 20,
                'close': price,
                'volume': 1000000 + (i * 10000)
            })
        
        return data
    
    def create_sample_volume_data(self, num_points=50):
        """Create sample volume data for testing."""
        data = []
        
        for i in range(num_points):
            volume = 1000000 + (i * 10000)
            data.append({
                'timestamp': (datetime.now() - timedelta(hours=num_points-i)).isoformat(),
                'volume': volume
            })
        
        return data
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_success(self):
        """Test successful complex pattern detection."""
        price_data = self.create_sample_price_data(30)
        volume_data = self.create_sample_volume_data(30)
        
        # Mock LLM response
        mock_llm_response = {
            "patterns": [
                {
                    "name": "Ascending Triangle",
                    "description": "Bullish continuation pattern with rising lows and horizontal resistance",
                    "confidence": 85,
                    "direction": "bullish",
                    "target_levels": [52000, 53000],
                    "invalidation_level": 49000,
                    "time_horizon": "short-term",
                    "volume_confirmation": True
                },
                {
                    "name": "Bull Flag",
                    "description": "Short-term consolidation after strong upward move",
                    "confidence": 70,
                    "direction": "bullish",
                    "target_levels": [54000],
                    "invalidation_level": 48500,
                    "time_horizon": "very short-term",
                    "volume_confirmation": False
                }
            ],
            "overall_assessment": "Bullish outlook with multiple confirmation signals",
            "key_levels": {
                "support": [49000, 49500],
                "resistance": [52000, 53000]
            },
            "risk_factors": ["Volume declining on recent moves"]
        }
        
        with patch('src.ai.pattern_detector.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized chart description"
            mock_security.validate_ai_output.return_value = (True, "Valid")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            patterns = await self.detector.detect_complex_patterns(price_data, volume_data)
            
            assert isinstance(patterns, list)
            assert len(patterns) == 2  # Both patterns have confidence >= 50%
            
            # Check first pattern
            assert patterns[0]["name"] == "Ascending Triangle"
            assert patterns[0]["confidence"] == 85
            assert patterns[0]["direction"] == "bullish"
            assert len(patterns[0]["target_levels"]) == 2
            
            # Check second pattern
            assert patterns[1]["name"] == "Bull Flag"
            assert patterns[1]["confidence"] == 70
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_insufficient_data(self):
        """Test pattern detection with insufficient data."""
        price_data = self.create_sample_price_data(10)  # Less than 20 points
        volume_data = self.create_sample_volume_data(10)
        
        patterns = await self.detector.detect_complex_patterns(price_data, volume_data)
        
        assert isinstance(patterns, list)
        assert len(patterns) == 0
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_empty_data(self):
        """Test pattern detection with empty data."""
        patterns = await self.detector.detect_complex_patterns([], [])
        
        assert isinstance(patterns, list)
        assert len(patterns) == 0
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_security_rejection(self):
        """Test pattern detection when security guard rejects input."""
        price_data = self.create_sample_price_data(30)
        volume_data = self.create_sample_volume_data(30)
        
        with patch('src.ai.pattern_detector.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.side_effect = ValueError("Malicious content detected")
            
            patterns = await self.detector.detect_complex_patterns(price_data, volume_data)
            
            assert isinstance(patterns, list)
            assert len(patterns) == 0
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_validation_failure(self):
        """Test pattern detection when output validation fails."""
        price_data = self.create_sample_price_data(30)
        volume_data = self.create_sample_volume_data(30)
        
        mock_llm_response = {
            "patterns": [
                {
                    "name": "Invalid Pattern",
                    "confidence": 150,  # Invalid confidence > 100
                    "direction": "invalid_direction"
                }
            ]
        }
        
        with patch('src.ai.pattern_detector.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (False, "Invalid confidence score")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            patterns = await self.detector.detect_complex_patterns(price_data, volume_data)
            
            assert isinstance(patterns, list)
            assert len(patterns) == 0
    
    @pytest.mark.asyncio
    async def test_detect_complex_patterns_caching(self):
        """Test pattern detection caching functionality."""
        price_data = self.create_sample_price_data(30)
        volume_data = self.create_sample_volume_data(30)
        
        mock_llm_response = {
            "patterns": [
                {
                    "name": "Test Pattern",
                    "confidence": 75,
                    "direction": "bullish",
                    "target_levels": [55000],
                    "invalidation_level": 48000,
                    "time_horizon": "short-term",
                    "volume_confirmation": True
                }
            ],
            "overall_assessment": "Test assessment",
            "key_levels": {"support": [49000], "resistance": [55000]},
            "risk_factors": []
        }
        
        with patch('src.ai.pattern_detector.ai_security_guard') as mock_security:
            mock_security.sanitize_ai_input.return_value = "sanitized input"
            mock_security.validate_ai_output.return_value = (True, "Valid")
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            # First call should hit LLM
            patterns1 = await self.detector.detect_complex_patterns(price_data, volume_data)
            self.mock_llm_client.analyze_json.assert_called_once()
            
            # Second call with same data should use cache
            self.mock_llm_client.analyze_json.reset_mock()
            patterns2 = await self.detector.detect_complex_patterns(price_data, volume_data)
            
            # Should be cached result (LLM not called again)
            self.mock_llm_client.analyze_json.assert_not_called()
            assert len(patterns2) == len(patterns1)
    
    @pytest.mark.asyncio
    async def test_analyze_breakout_probability_success(self):
        """Test successful breakout probability analysis."""
        price_data = self.create_sample_price_data(50)
        
        mock_response = {
            "breakout_probability": 0.75,
            "direction": "up",
            "confidence": 0.85,
            "key_levels": [50000, 51000, 52000],
            "risk_factors": ["High volatility", "Low volume"],
            "reasoning": "Strong technical indicators suggest upward breakout"
        }
        
        self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_response)
        
        result = await self.detector.analyze_breakout_probability(price_data, "BTC/USDT")
        
        assert isinstance(result, dict)
        assert result["breakout_probability"] == 0.75
        assert result["direction"] == "up"
        assert result["confidence"] == 0.85
        assert len(result["key_levels"]) == 3
        assert len(result["risk_factors"]) == 2
        assert "reasoning" in result
    
    @pytest.mark.asyncio
    async def test_analyze_breakout_probability_insufficient_data(self):
        """Test breakout analysis with insufficient data."""
        price_data = self.create_sample_price_data(20)  # Less than 30 points
        
        result = await self.detector.analyze_breakout_probability(price_data, "BTC/USDT")
        
        assert isinstance(result, dict)
        assert result["probability"] == 0.5
        assert result["direction"] == "uncertain"
        assert result["confidence"] == 0.1
    
    @pytest.mark.asyncio
    async def test_analyze_breakout_probability_error_handling(self):
        """Test breakout analysis error handling."""
        price_data = self.create_sample_price_data(50)
        
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM error"))
        
        result = await self.detector.analyze_breakout_probability(price_data, "BTC/USDT")
        
        assert isinstance(result, dict)
        assert result["breakout_probability"] == 0.5
        assert result["direction"] == "uncertain"
        assert result["confidence"] == 0.1
        assert "Analysis failed" in result["risk_factors"]
        assert "Error: LLM error" in result["reasoning"]
    
    def test_generate_chart_description(self):
        """Test chart description generation."""
        price_data = self.create_sample_price_data(30)
        volume_data = self.create_sample_volume_data(30)
        
        description = self.detector._generate_chart_description(price_data, volume_data)
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "Price movement over" in description
        assert "Recent range:" in description
        assert "Volume:" in description
        assert "Recent trend:" in description
    
    def test_generate_chart_description_minimal_data(self):
        """Test chart description with minimal data."""
        price_data = self.create_sample_price_data(5)
        volume_data = self.create_sample_volume_data(5)
        
        description = self.detector._generate_chart_description(price_data, volume_data)
        
        assert isinstance(description, str)
        assert "insufficient data" in description or len(description) > 0
    
    def test_generate_chart_description_error_handling(self):
        """Test chart description error handling."""
        # Invalid data structure
        price_data = [{"invalid": "data"}]
        volume_data = []
        
        description = self.detector._generate_chart_description(price_data, volume_data)
        
        assert isinstance(description, str)
        assert "Unable to generate chart description" in description
    
    def test_describe_trend_uptrend(self):
        """Test trend description for uptrend."""
        prices = [100, 102, 104, 106, 108, 110]
        
        trend = self.detector._describe_trend(prices)
        
        assert "uptrend" in trend
        assert "+" in trend
    
    def test_describe_trend_downtrend(self):
        """Test trend description for downtrend."""
        prices = [110, 108, 106, 104, 102, 100]
        
        trend = self.detector._describe_trend(prices)
        
        assert "downtrend" in trend
        assert "-" in trend
    
    def test_describe_trend_sideways(self):
        """Test trend description for sideways movement."""
        prices = [100, 101, 99, 100.5, 99.5, 100]
        
        trend = self.detector._describe_trend(prices)
        
        assert "sideways" in trend
    
    def test_describe_trend_insufficient_data(self):
        """Test trend description with insufficient data."""
        prices = [100, 101]
        
        trend = self.detector._describe_trend(prices)
        
        assert trend == "insufficient data"
    
    def test_find_reversal_points(self):
        """Test reversal point detection."""
        # Create data with clear peaks and valleys
        prices = [100, 105, 110, 105, 100, 95, 100, 105, 100, 95, 100]
        
        reversal_points = self.detector._find_reversal_points(prices)
        
        assert isinstance(reversal_points, list)
        assert len(reversal_points) > 0
        
        # Should find some peaks and valleys
        for point in reversal_points:
            assert "peak" in point or "valley" in point
    
    def test_find_reversal_points_insufficient_data(self):
        """Test reversal point detection with insufficient data."""
        prices = [100, 101, 102]
        
        reversal_points = self.detector._find_reversal_points(prices)
        
        assert isinstance(reversal_points, list)
        assert len(reversal_points) == 0
    
    def test_calculate_trend_rising(self):
        """Test trend calculation for rising prices."""
        prices = [100, 102, 105]
        
        trend = self.detector._calculate_trend(prices)
        
        assert trend == "rising"
    
    def test_calculate_trend_falling(self):
        """Test trend calculation for falling prices."""
        prices = [105, 102, 100]
        
        trend = self.detector._calculate_trend(prices)
        
        assert trend == "falling"
    
    def test_calculate_trend_flat(self):
        """Test trend calculation for flat prices."""
        prices = [100, 100.5, 100]
        
        trend = self.detector._calculate_trend(prices)
        
        assert trend == "flat"
    
    def test_calculate_trend_insufficient_data(self):
        """Test trend calculation with insufficient data."""
        prices = [100]
        
        trend = self.detector._calculate_trend(prices)
        
        assert trend == "flat"
    
    def test_calculate_volatility(self):
        """Test volatility calculation."""
        prices = [100, 105, 95, 110, 90]
        
        volatility = self.detector._calculate_volatility(prices)
        
        assert isinstance(volatility, float)
        assert volatility > 0
    
    def test_calculate_volatility_insufficient_data(self):
        """Test volatility calculation with insufficient data."""
        prices = [100]
        
        volatility = self.detector._calculate_volatility(prices)
        
        assert volatility == 0.0
    
    def test_create_pattern_analysis_prompt(self):
        """Test pattern analysis prompt creation."""
        chart_description = "Test chart description with price movements"
        
        prompt = self.detector._create_pattern_analysis_prompt(chart_description)
        
        assert isinstance(prompt, str)
        assert chart_description in prompt
        assert "Chart patterns" in prompt
        assert "Head & Shoulders" in prompt
        assert "Support and resistance" in prompt
    
    def test_get_pattern_system_prompt(self):
        """Test pattern system prompt."""
        system_prompt = self.detector._get_pattern_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert "technical analyst" in system_prompt
        assert "pattern recognition" in system_prompt
        assert "Conservative" in system_prompt
    
    def test_get_pattern_schema(self):
        """Test pattern schema structure."""
        schema = self.detector._get_pattern_schema()
        
        assert isinstance(schema, dict)
        assert "patterns" in schema
        assert "overall_assessment" in schema
        assert "key_levels" in schema
        assert "risk_factors" in schema
        
        # Check pattern structure
        pattern_schema = schema["patterns"][0]
        assert "name" in pattern_schema
        assert "confidence" in pattern_schema
        assert "direction" in pattern_schema
        assert "target_levels" in pattern_schema
        assert "invalidation_level" in pattern_schema
    
    def test_process_detected_patterns_filtering(self):
        """Test processing and filtering of detected patterns."""
        response = {
            "patterns": [
                {"name": "High Confidence Pattern", "confidence": 85},
                {"name": "Medium Confidence Pattern", "confidence": 60},
                {"name": "Low Confidence Pattern", "confidence": 40},  # Should be filtered
                {"name": "Another High Pattern", "confidence": 90}
            ]
        }
        
        patterns = self.detector._process_detected_patterns(response)
        
        assert len(patterns) == 3  # One filtered out (confidence < 50%)
        
        # Should be sorted by confidence (highest first)
        assert patterns[0]["confidence"] == 90
        assert patterns[1]["confidence"] == 85
        assert patterns[2]["confidence"] == 60
    
    def test_process_detected_patterns_empty_response(self):
        """Test processing empty patterns response."""
        response = {"patterns": []}
        
        patterns = self.detector._process_detected_patterns(response)
        
        assert isinstance(patterns, list)
        assert len(patterns) == 0
    
    def test_create_cache_key(self):
        """Test cache key creation."""
        price_data = self.create_sample_price_data(10)
        
        cache_key = self.detector._create_cache_key(price_data)
        
        assert isinstance(cache_key, str)
        assert cache_key.startswith("patterns_")
        
        # Same data should produce same key
        cache_key2 = self.detector._create_cache_key(price_data)
        assert cache_key == cache_key2
    
    def test_create_cache_key_empty_data(self):
        """Test cache key creation with empty data."""
        cache_key = self.detector._create_cache_key([])
        
        assert cache_key == "empty_data"
    
    def test_get_cached_patterns_none(self):
        """Test getting cached patterns when none exist."""
        patterns = self.detector._get_cached_patterns("nonexistent_key")
        
        assert patterns is None
    
    def test_cache_patterns_and_retrieve(self):
        """Test caching and retrieving patterns."""
        patterns = [{"name": "Test Pattern", "confidence": 80}]
        cache_key = "test_key"
        
        # Cache patterns
        self.detector._cache_patterns(cache_key, patterns)
        
        # Retrieve from cache
        cached_patterns = self.detector._get_cached_patterns(cache_key)
        
        assert cached_patterns == patterns
    
    def test_cache_patterns_expiry(self):
        """Test cache pattern expiry."""
        patterns = [{"name": "Test Pattern", "confidence": 80}]
        cache_key = "test_key"
        
        # Mock expired cache
        self.detector.pattern_cache[cache_key] = {
            "patterns": patterns,
            "timestamp": datetime.now() - timedelta(hours=1)  # Expired
        }
        
        # Should return None for expired cache
        cached_patterns = self.detector._get_cached_patterns(cache_key)
        
        assert cached_patterns is None


if __name__ == '__main__':
    pytest.main([__file__])
