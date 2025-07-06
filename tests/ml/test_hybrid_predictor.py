"""Test suite for hybrid_predictor module."""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from src.ml.hybrid_predictor import HybridPredictor


class TestHybridPredictor:
    """Test cases for HybridPredictor class."""

    def test_hybrid_predictor_initialization(self):
        """Test HybridPredictor can be instantiated."""
        predictor = HybridPredictor()
        assert predictor is not None
        assert hasattr(predictor, 'traditional_models')
        assert hasattr(predictor, 'llm_client')

    def test_train_models_with_valid_data(self):
        """Test training models with valid data."""
        predictor = HybridPredictor()
        
        # Mock data
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
            'open': np.random.rand(100) * 100,
            'high': np.random.rand(100) * 100,
            'low': np.random.rand(100) * 100,
            'close': np.random.rand(100) * 100,
            'volume': np.random.rand(100) * 1000
        })
        
        # This should not raise an exception
        try:
            predictor.train_models(mock_data)
            assert True
        except Exception as e:
            pytest.fail(f"train_models raised an exception: {e}")

    def test_make_prediction_returns_dict(self):
        """Test that make_prediction returns a dictionary."""
        predictor = HybridPredictor()
        
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
            'open': np.random.rand(10) * 100,
            'high': np.random.rand(10) * 100,
            'low': np.random.rand(10) * 100,
            'close': np.random.rand(10) * 100,
            'volume': np.random.rand(10) * 1000
        })
        
        with patch.object(predictor, '_get_traditional_predictions') as mock_trad, \
             patch.object(predictor, '_get_llm_predictions') as mock_llm:
            
            mock_trad.return_value = {'price': 100.0, 'confidence': 0.8}
            mock_llm.return_value = {'price': 102.0, 'confidence': 0.7}
            
            result = predictor.make_prediction(mock_data)
            
            assert isinstance(result, dict)
            assert 'price' in result
            assert 'confidence' in result
            assert 'traditional_prediction' in result
            assert 'llm_prediction' in result

    def test_combine_predictions_with_different_weights(self):
        """Test prediction combination with different weights."""
        predictor = HybridPredictor()
        
        traditional_pred = {'price': 100.0, 'confidence': 0.8}
        llm_pred = {'price': 110.0, 'confidence': 0.6}
        
        # Test with equal weights
        result = predictor._combine_predictions(traditional_pred, llm_pred)
        assert isinstance(result, dict)
        assert 'price' in result
        assert 'confidence' in result
        
        # Price should be between the two predictions
        assert 100.0 <= result['price'] <= 110.0

    def test_feature_engineering_returns_dataframe(self):
        """Test that feature engineering returns a DataFrame."""
        predictor = HybridPredictor()
        
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=50, freq='H'),
            'open': np.random.rand(50) * 100,
            'high': np.random.rand(50) * 100,
            'low': np.random.rand(50) * 100,
            'close': np.random.rand(50) * 100,
            'volume': np.random.rand(50) * 1000
        })
        
        result = predictor._engineer_features(mock_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= len(mock_data)  # May be shorter due to technical indicators

    def test_get_model_performance_metrics(self):
        """Test getting model performance metrics."""
        predictor = HybridPredictor()
        
        metrics = predictor.get_model_performance()
        assert isinstance(metrics, dict)
        # Should contain metrics for both traditional and LLM models
        assert 'traditional_models' in metrics
        assert 'llm_model' in metrics

    @patch('src.ml.hybrid_predictor.LLMClient')
    def test_predictor_with_mocked_llm_client(self, mock_llm_client):
        """Test HybridPredictor with mocked LLM client."""
        mock_client = Mock()
        mock_llm_client.return_value = mock_client
        
        predictor = HybridPredictor()
        assert predictor.llm_client is not None

    def test_error_handling_with_invalid_data(self):
        """Test error handling with invalid data."""
        predictor = HybridPredictor()
        
        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        
        with pytest.raises(Exception):
            predictor.train_models(empty_data)

    def test_prediction_without_training(self):
        """Test making prediction without training models first."""
        predictor = HybridPredictor()
        
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
            'close': np.random.rand(10) * 100
        })
        
        # This should handle the case gracefully
        result = predictor.make_prediction(mock_data)
        assert isinstance(result, dict)
