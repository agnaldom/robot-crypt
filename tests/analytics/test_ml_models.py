"""Test suite for analytics ml_models module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from sklearn.datasets import make_regression
from sklearn.metrics import mean_squared_error

from src.analytics.ml_models import MLModels


class TestMLModels:
    """Test cases for MLModels class."""
    
    def setup_method(self):
        """Set up test MLModels instance."""
        self.temp_models_dir = tempfile.mkdtemp()
        self.ml_models = MLModels(models_dir=self.temp_models_dir)
    
    def teardown_method(self):
        """Clean up test directory."""
        import shutil
        if os.path.exists(self.temp_models_dir):
            shutil.rmtree(self.temp_models_dir)
    
    def test_initialization(self):
        """Test MLModels initialization."""
        assert self.ml_models.models_dir == self.temp_models_dir
        assert isinstance(self.ml_models.models, dict)
        assert isinstance(self.ml_models.scalers, dict)
        assert isinstance(self.ml_models.available_models, dict)
        assert os.path.exists(self.temp_models_dir)
        
        # Check that all expected models are available
        expected_models = [
            'linear_regression', 'ridge', 'lasso', 'elastic_net',
            'random_forest', 'gradient_boosting', 'xgboost', 'svr', 'mlp'
        ]
        for model_name in expected_models:
            assert model_name in self.ml_models.available_models
    
    def test_prepare_features_basic(self):
        """Test basic feature preparation."""
        # Create sample data
        data = pd.DataFrame({
            'price': [100, 105, 110, 108, 112],
            'volume': [1000, 1100, 950, 1200, 1050],
            'target': [105, 110, 108, 112, 115]
        })
        
        X, y = self.ml_models.prepare_features(data, 'target', ['price', 'volume'], lag_features=2)
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert len(X) < len(data)  # Should be smaller due to lag features and rolling stats
        
        # Check that lag features were created
        assert any('_lag_1' in col for col in X.columns)
        assert any('_lag_2' in col for col in X.columns)
        
        # Check that rolling features were created
        assert any('_ma_5' in col for col in X.columns)
        assert any('_std_5' in col for col in X.columns)
        
        # Check that difference features were created
        assert any('_diff_1' in col for col in X.columns)
        assert any('_diff_pct' in col for col in X.columns)
    
    def test_prepare_features_auto_column_selection(self):
        """Test automatic feature column selection."""
        data = pd.DataFrame({
            'price': [100, 105, 110, 108, 112],
            'volume': [1000, 1100, 950, 1200, 1050],
            'rsi': [50, 55, 45, 60, 58],
            'macd': [0.5, 0.8, 0.3, 1.0, 0.7],
            'target': [105, 110, 108, 112, 115],
            'text_column': ['a', 'b', 'c', 'd', 'e']  # Non-numeric column
        })
        
        X, y = self.ml_models.prepare_features(data, 'target', lag_features=1)
        
        # Should automatically select numeric columns except target
        assert 'price' in str(X.columns)
        assert 'volume' in str(X.columns)
        assert 'rsi' in str(X.columns)
        assert 'macd' in str(X.columns)
        assert 'target' not in str(X.columns)
        assert 'text_column' not in str(X.columns)
    
    def test_train_model_linear_regression(self):
        """Test training linear regression model."""
        # Create sample regression data
        X, y = make_regression(n_samples=100, n_features=5, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series, 
            model_name='linear_regression',
            test_size=0.2,
            cv_folds=3,
            feature_selection=False,
            hyperparameter_tuning=False
        )
        
        assert isinstance(result, dict)
        assert 'model_id' in result
        assert 'model_name' in result
        assert 'metrics' in result
        assert 'cv_scores' in result
        assert 'selected_features' in result
        
        # Check metrics structure
        assert 'train' in result['metrics']
        assert 'test' in result['metrics']
        assert 'mse' in result['metrics']['train']
        assert 'rmse' in result['metrics']['train']
        assert 'mae' in result['metrics']['train']
        assert 'r2' in result['metrics']['train']
        
        # Model should be stored
        model_id = result['model_id']
        assert model_id in self.ml_models.models
        assert model_id in self.ml_models.scalers
    
    def test_train_model_random_forest(self):
        """Test training random forest model."""
        X, y = make_regression(n_samples=50, n_features=3, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series,
            model_name='random_forest',
            test_size=0.3,
            cv_folds=3,
            feature_selection=True,
            hyperparameter_tuning=False
        )
        
        assert result['model_name'] == 'random_forest'
        assert 'feature_importance' in result
        assert result['feature_importance'] is not None
        
        # Random forest should have feature importance
        assert isinstance(result['feature_importance'], dict)
        assert len(result['feature_importance']) > 0
    
    @patch('src.analytics.ml_models.GridSearchCV')
    def test_hyperparameter_tuning(self, mock_grid_search):
        """Test hyperparameter tuning functionality."""
        # Mock GridSearchCV
        mock_grid_instance = Mock()
        mock_grid_instance.best_estimator_ = self.ml_models.available_models['ridge']
        mock_grid_search.return_value = mock_grid_instance
        
        X, y = make_regression(n_samples=30, n_features=2, random_state=42)
        X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1'])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series,
            model_name='ridge',
            hyperparameter_tuning=True,
            cv_folds=3
        )
        
        # Should have called GridSearchCV
        mock_grid_search.assert_called_once()
        assert result['model_name'] == 'ridge'
    
    def test_predict(self):
        """Test model prediction functionality."""
        # Train a simple model first
        X, y = make_regression(n_samples=50, n_features=3, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series,
            model_name='linear_regression',
            hyperparameter_tuning=False
        )
        
        model_id = result['model_id']
        
        # Test prediction
        test_X = X_df.iloc[:5]
        predictions = self.ml_models.predict(model_id, test_X)
        
        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == 5
        assert all(isinstance(pred, (int, float, np.number)) for pred in predictions)
    
    def test_predict_nonexistent_model(self):
        """Test prediction with non-existent model."""
        X = pd.DataFrame({'feature_0': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Modelo .* não encontrado"):
            self.ml_models.predict("nonexistent_model", X)
    
    def test_predict_with_confidence(self):
        """Test prediction with confidence intervals."""
        # Train a random forest model (has estimators for confidence)
        X, y = make_regression(n_samples=50, n_features=3, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series,
            model_name='random_forest',
            hyperparameter_tuning=False
        )
        
        model_id = result['model_id']
        
        # Test prediction with confidence
        test_X = X_df.iloc[:3]
        pred_result = self.ml_models.predict_with_confidence(model_id, test_X, confidence_level=0.95)
        
        assert isinstance(pred_result, dict)
        assert 'predictions' in pred_result
        assert 'lower_bound' in pred_result
        assert 'upper_bound' in pred_result
        assert 'std' in pred_result
        
        assert len(pred_result['predictions']) == 3
        assert len(pred_result['lower_bound']) == 3
        assert len(pred_result['upper_bound']) == 3
    
    def test_evaluate_model(self):
        """Test model evaluation functionality."""
        # Train a model
        X, y = make_regression(n_samples=50, n_features=3, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(
            X_df, y_series,
            model_name='linear_regression',
            test_size=0.4  # Use more data for testing
        )
        
        model_id = result['model_id']
        
        # Evaluate on test data
        test_X = X_df.iloc[-10:]
        test_y = y_series.iloc[-10:]
        
        eval_result = self.ml_models.evaluate_model(model_id, test_X, test_y)
        
        assert isinstance(eval_result, dict)
        assert 'model_id' in eval_result
        assert 'test_metrics' in eval_result
        assert 'predictions' in eval_result
        assert 'actuals' in eval_result
        
        # Check test metrics
        test_metrics = eval_result['test_metrics']
        assert 'mse' in test_metrics
        assert 'rmse' in test_metrics
        assert 'mae' in test_metrics
        assert 'r2' in test_metrics
        assert 'mape' in test_metrics
    
    def test_compare_models(self):
        """Test model comparison functionality."""
        # Create data for comparison
        X, y = make_regression(n_samples=80, n_features=4, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        models_to_compare = ['linear_regression', 'ridge', 'random_forest']
        
        comparison_df = self.ml_models.compare_models(X_df, y_series, models_to_compare)
        
        assert isinstance(comparison_df, pd.DataFrame)
        assert len(comparison_df) <= len(models_to_compare)  # Some models might fail
        
        if len(comparison_df) > 0:
            expected_columns = ['model', 'train_rmse', 'test_rmse', 'train_r2', 'test_r2', 'cv_rmse_mean', 'cv_rmse_std']
            for col in expected_columns:
                assert col in comparison_df.columns
            
            # Should be sorted by test_rmse
            assert comparison_df['test_rmse'].is_monotonic_increasing
    
    def test_create_ensemble_model(self):
        """Test ensemble model creation."""
        # Train multiple models first
        X, y = make_regression(n_samples=50, n_features=3, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        # Train two models
        result1 = self.ml_models.train_model(X_df, y_series, model_name='linear_regression')
        result2 = self.ml_models.train_model(X_df, y_series, model_name='ridge')
        
        model_ids = [result1['model_id'], result2['model_id']]
        weights = [0.6, 0.4]
        
        ensemble_id = self.ml_models.create_ensemble_model(model_ids, weights)
        
        assert isinstance(ensemble_id, str)
        assert ensemble_id.startswith('ensemble_')
        assert ensemble_id in self.ml_models.models
        
        # Test ensemble prediction
        test_X = X_df.iloc[:3]
        ensemble_predictions = self.ml_models.predict(ensemble_id, test_X)
        
        assert isinstance(ensemble_predictions, np.ndarray)
        assert len(ensemble_predictions) == 3
    
    def test_list_models(self):
        """Test listing trained models."""
        # Initially should be empty
        models_df = self.ml_models.list_models()
        assert isinstance(models_df, pd.DataFrame)
        
        if len(models_df) == 0:
            # Train a model and test again
            X, y = make_regression(n_samples=30, n_features=2, random_state=42)
            X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1'])
            y_series = pd.Series(y)
            
            result = self.ml_models.train_model(X_df, y_series, model_name='linear_regression')
            
            models_df = self.ml_models.list_models()
            assert len(models_df) == 1
            
            expected_columns = ['model_id', 'model_name', 'test_rmse', 'test_r2', 'cv_rmse', 'n_features']
            for col in expected_columns:
                assert col in models_df.columns
    
    def test_get_model_info(self):
        """Test getting detailed model information."""
        # Train a model
        X, y = make_regression(n_samples=30, n_features=2, random_state=42)
        X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1'])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(X_df, y_series, model_name='linear_regression')
        model_id = result['model_id']
        
        model_info = self.ml_models.get_model_info(model_id)
        
        assert isinstance(model_info, dict)
        assert model_info['model_id'] == model_id
        assert model_info['model_name'] == 'linear_regression'
        assert 'metrics' in model_info
        assert 'selected_features' in model_info
    
    def test_get_model_info_nonexistent(self):
        """Test getting info for non-existent model."""
        with pytest.raises(ValueError, match="Modelo .* não encontrado"):
            self.ml_models.get_model_info("nonexistent_model")
    
    def test_delete_model(self):
        """Test model deletion."""
        # Train a model
        X, y = make_regression(n_samples=30, n_features=2, random_state=42)
        X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1'])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(X_df, y_series, model_name='linear_regression')
        model_id = result['model_id']
        
        # Verify model exists
        assert model_id in self.ml_models.models
        assert model_id in self.ml_models.scalers
        assert model_id in self.ml_models.model_performance
        
        # Delete model
        self.ml_models.delete_model(model_id)
        
        # Verify model is deleted
        assert model_id not in self.ml_models.models
        assert model_id not in self.ml_models.scalers
        assert model_id not in self.ml_models.model_performance
    
    def test_save_and_load_model(self):
        """Test model saving and loading functionality."""
        # Train a model
        X, y = make_regression(n_samples=30, n_features=2, random_state=42)
        X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1'])
        y_series = pd.Series(y)
        
        result = self.ml_models.train_model(X_df, y_series, model_name='linear_regression')
        model_id = result['model_id']
        
        # Make prediction before save
        test_X = X_df.iloc[:3]
        original_predictions = self.ml_models.predict(model_id, test_X)
        
        # Create new MLModels instance and load model
        new_ml_models = MLModels(models_dir=self.temp_models_dir)
        new_ml_models.load_model(model_id)
        
        # Test that loaded model makes same predictions
        loaded_predictions = new_ml_models.predict(model_id, test_X)
        
        np.testing.assert_array_almost_equal(original_predictions, loaded_predictions, decimal=5)
    
    def test_load_nonexistent_model(self):
        """Test loading non-existent model file."""
        with pytest.raises(FileNotFoundError):
            self.ml_models.load_model("nonexistent_model")
    
    def test_feature_importance_extraction(self):
        """Test feature importance extraction for different models."""
        X, y = make_regression(n_samples=30, n_features=3, random_state=42)
        X_df = pd.DataFrame(X, columns=['feature_0', 'feature_1', 'feature_2'])
        
        # Test with Random Forest (has feature_importances_)
        mock_rf_model = Mock()
        mock_rf_model.feature_importances_ = np.array([0.5, 0.3, 0.2])
        
        importance = self.ml_models._get_feature_importance(mock_rf_model, ['feature_0', 'feature_1', 'feature_2'])
        
        assert isinstance(importance, dict)
        assert len(importance) == 3
        assert importance['feature_0'] == 0.5
        
        # Test with Linear model (has coef_)
        mock_linear_model = Mock()
        mock_linear_model.feature_importances_ = None
        mock_linear_model.coef_ = np.array([1.5, -0.8, 2.1])
        delattr(mock_linear_model, 'feature_importances_')  # Remove the attribute
        
        importance = self.ml_models._get_feature_importance(mock_linear_model, ['feature_0', 'feature_1', 'feature_2'])
        
        assert isinstance(importance, dict)
        assert importance['feature_0'] == 1.5
        assert importance['feature_1'] == 0.8  # Should be absolute value
        assert importance['feature_2'] == 2.1
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        y_true = np.array([100, 105, 110, 108, 112])
        y_pred = np.array([98, 107, 109, 110, 114])
        
        metrics = self.ml_models._calculate_metrics(y_true, y_pred)
        
        assert isinstance(metrics, dict)
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert 'mape' in metrics
        
        # Verify MSE calculation
        expected_mse = mean_squared_error(y_true, y_pred)
        assert abs(metrics['mse'] - expected_mse) < 1e-6
        
        # Verify RMSE
        assert abs(metrics['rmse'] - np.sqrt(expected_mse)) < 1e-6
        
        # All metrics should be reasonable values
        assert metrics['mse'] >= 0
        assert metrics['rmse'] >= 0
        assert metrics['mae'] >= 0
        assert -1 <= metrics['r2'] <= 1  # R² can be negative for bad models


if __name__ == '__main__':
    pytest.main([__file__])
