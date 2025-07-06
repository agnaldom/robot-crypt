"""Test suite for training_system module."""

import pytest
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import sqlite3
import tempfile
import os

from src.ml.training_system import (
    TradingDataProcessor,
    TradingModel,
    TradingTrainer,
    TrainingFeature,
    TradingSignal
)


class TestTrainingFeature:
    """Test cases for TrainingFeature dataclass."""
    
    def test_training_feature_creation(self):
        """Test TrainingFeature can be created with required fields."""
        feature = TrainingFeature(
            symbol="BTC/USDT",
            timestamp="2023-01-01T00:00:00",
            price=50000.0,
            volume_24h=1000000.0,
            price_change_24h=1000.0,
            price_change_percentage_24h=2.0,
            high_24h=51000.0,
            low_24h=49000.0,
            rsi=50.0,
            macd=100.0,
            macd_signal=90.0,
            bb_upper=52000.0,
            bb_middle=50000.0,
            bb_lower=48000.0,
            sma_20=49500.0,
            ema_12=50200.0,
            ema_26=49800.0,
            news_sentiment_score=0.2,
            news_count=5,
            overall_sentiment="positive",
            upcoming_events_count=2,
            high_importance_events=1
        )
        
        assert feature.symbol == "BTC/USDT"
        assert feature.price == 50000.0
        assert feature.overall_sentiment == "positive"
        assert feature.target is None  # Default value


class TestTradingSignal:
    """Test cases for TradingSignal dataclass."""
    
    def test_trading_signal_creation(self):
        """Test TradingSignal can be created with required fields."""
        signal = TradingSignal(
            symbol="ETH/USDT",
            timestamp="2023-01-01T01:00:00",
            signal="BUY",
            confidence=0.85,
            price=2000.0,
            reasoning="Strong technical indicators",
            features_used={"rsi": 30, "macd": 50}
        )
        
        assert signal.symbol == "ETH/USDT"
        assert signal.signal == "BUY"
        assert signal.confidence == 0.85
        assert "rsi" in signal.features_used


class TestTradingDataProcessor:
    """Test cases for TradingDataProcessor class."""
    
    def setup_method(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.processor = TradingDataProcessor(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database and tables are created properly."""
        # Check that database file exists
        assert os.path.exists(self.temp_db.name)
        
        # Check that tables exist
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['historical_data', 'training_features', 'trading_signals']
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_save_market_data(self):
        """Test saving market data to database."""
        market_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': '2023-01-01T00:00:00',
                'price': 50000.0,
                'volume_24h': 1000000.0,
                'high_24h': 51000.0,
                'low_24h': 49000.0,
                'price_change_24h': 1000.0,
                'price_change_percentage_24h': 2.0,
                'market_cap': 1000000000.0,
                'source': 'test'
            }
        ]
        
        self.processor.save_market_data(market_data)
        
        # Verify data was saved
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historical_data")
        count = cursor.fetchone()[0]
        assert count == 1
        
        cursor.execute("SELECT symbol, price FROM historical_data")
        row = cursor.fetchone()
        assert row[0] == 'BTC/USDT'
        assert row[1] == 50000.0
        
        conn.close()
    
    def test_get_historical_data(self):
        """Test retrieving historical data."""
        # First save some data
        market_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': '2023-01-01T00:00:00',
                'price': 50000.0,
                'volume_24h': 1000000.0,
                'high_24h': 51000.0,
                'low_24h': 49000.0,
                'price_change_24h': 1000.0,
                'price_change_percentage_24h': 2.0,
                'market_cap': 1000000000.0,
                'source': 'test'
            }
        ]
        self.processor.save_market_data(market_data)
        
        # Retrieve data
        df = self.processor.get_historical_data('BTC/USDT', days=30)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['symbol'] == 'BTC/USDT'
        assert df.iloc[0]['price'] == 50000.0
    
    def test_calculate_technical_indicators(self):
        """Test calculation of technical indicators."""
        # Create sample data with enough points for indicators
        data = []
        base_price = 50000
        for i in range(30):
            price = base_price + np.random.normal(0, 100)
            data.append({
                'price': price,
                'high_24h': price + 50,
                'low_24h': price - 50,
                'volume_24h': 1000000
            })
        
        df = pd.DataFrame(data)
        result_df = self.processor.calculate_technical_indicators(df)
        
        # Check that technical indicators were added
        expected_columns = ['rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_middle', 'bb_lower', 'sma_20', 'ema_12', 'ema_26']
        for col in expected_columns:
            assert col in result_df.columns
        
        # Check that some values are not NaN (at least in the later rows)
        assert not result_df['rsi'].iloc[-1:].isna().all()
    
    def test_calculate_technical_indicators_insufficient_data(self):
        """Test technical indicators calculation with insufficient data."""
        # Create data with too few points
        data = [{'price': 50000, 'high_24h': 50050, 'low_24h': 49950, 'volume_24h': 1000000} for _ in range(5)]
        df = pd.DataFrame(data)
        
        result_df = self.processor.calculate_technical_indicators(df)
        
        # Should return original dataframe
        assert len(result_df) == 5
        assert 'price' in result_df.columns


class TestTradingModel:
    """Test cases for TradingModel class."""
    
    def setup_method(self):
        """Set up test model."""
        self.temp_model_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        self.temp_model_file.close()
        self.model = TradingModel(self.temp_model_file.name)
    
    def teardown_method(self):
        """Clean up test files."""
        if os.path.exists(self.temp_model_file.name):
            os.unlink(self.temp_model_file.name)
    
    def test_model_initialization(self):
        """Test TradingModel initialization."""
        assert self.model.model_path == self.temp_model_file.name
        assert self.model.model is None
        assert self.model.scaler is None
        assert self.model.feature_columns is None
        assert not self.model.is_trained
    
    def test_create_features_from_data(self):
        """Test feature creation from market data."""
        market_data = {
            'market_data': [
                {
                    'symbol': 'BTC/USDT',
                    'timestamp': '2023-01-01T00:00:00',
                    'price': 50000.0,
                    'volume_24h': 1000000.0,
                    'price_change_24h': 1000.0,
                    'price_change_percentage_24h': 2.0,
                    'high_24h': 51000.0,
                    'low_24h': 49000.0
                }
            ],
            'news': [
                {
                    'currencies': ['BTC'],
                    'sentiment_score': 0.5
                }
            ],
            'events': [
                {
                    'currencies': ['BTC'],
                    'importance': 'high'
                }
            ]
        }
        
        features = self.model.create_features_from_data(market_data)
        
        assert len(features) == 1
        assert isinstance(features[0], TrainingFeature)
        assert features[0].symbol == 'BTC/USDT'
        assert features[0].price == 50000.0
        assert features[0].news_sentiment_score == 0.5
        assert features[0].high_importance_events == 1
    
    def test_create_training_targets(self):
        """Test creation of training targets."""
        features = [
            TrainingFeature(
                symbol="BTC/USDT",
                timestamp="2023-01-01T00:00:00",
                price=50000.0,
                volume_24h=1000000.0,
                price_change_24h=1000.0,
                price_change_percentage_24h=2.0,
                high_24h=51000.0,
                low_24h=49000.0,
                rsi=30.0,  # Oversold
                macd=100.0,
                macd_signal=90.0,
                bb_upper=52000.0,
                bb_middle=50000.0,
                bb_lower=48000.0,
                sma_20=49500.0,
                ema_12=50200.0,
                ema_26=49800.0,
                news_sentiment_score=0.2,
                news_count=5,
                overall_sentiment="positive",
                upcoming_events_count=2,
                high_importance_events=1
            )
        ]
        
        features_with_targets = self.model.create_training_targets(features)
        
        assert len(features_with_targets) == 1
        assert features_with_targets[0].target is not None
        # With RSI = 30 (oversold), should be BUY
        assert features_with_targets[0].target == "BUY"
    
    def test_prepare_training_data(self):
        """Test preparation of training data."""
        features = [
            TrainingFeature(
                symbol="BTC/USDT",
                timestamp="2023-01-01T00:00:00",
                price=50000.0,
                volume_24h=1000000.0,
                price_change_24h=1000.0,
                price_change_percentage_24h=2.0,
                high_24h=51000.0,
                low_24h=49000.0,
                rsi=50.0,
                macd=100.0,
                macd_signal=90.0,
                bb_upper=52000.0,
                bb_middle=50000.0,
                bb_lower=48000.0,
                sma_20=49500.0,
                ema_12=50200.0,
                ema_26=49800.0,
                news_sentiment_score=0.2,
                news_count=5,
                overall_sentiment="positive",
                upcoming_events_count=2,
                high_importance_events=1,
                target="BUY"
            )
        ]
        
        X, y = self.model.prepare_training_data(features)
        
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(X) == 1
        assert len(y) == 1
        assert y[0] == "BUY"
        assert self.model.feature_columns is not None
    
    def test_train_model(self):
        """Test model training."""
        # Create sample training data
        X = np.random.rand(100, 10)
        y = np.random.choice(['BUY', 'SELL', 'HOLD'], 100)
        
        training_report = self.model.train_model(X, y)
        
        assert isinstance(training_report, dict)
        assert 'accuracy' in training_report
        assert 'classification_report' in training_report
        assert 'feature_importance' in training_report
        assert self.model.is_trained
        assert self.model.model is not None
        assert self.model.scaler is not None
    
    @patch('src.ml.training_system.TradingModel._predict_with_rules')
    def test_predict_signal_without_trained_model(self, mock_predict_rules):
        """Test prediction when model is not trained."""
        mock_predict_rules.return_value = [Mock(spec=TradingSignal)]
        
        features = [Mock(spec=TrainingFeature)]
        signals = self.model.predict_signal(features)
        
        mock_predict_rules.assert_called_once_with(features)
    
    def test_predict_with_rules(self):
        """Test fallback prediction with rules."""
        features = [
            TrainingFeature(
                symbol="BTC/USDT",
                timestamp="2023-01-01T00:00:00",
                price=50000.0,
                volume_24h=1000000.0,
                price_change_24h=1000.0,
                price_change_percentage_24h=6.0,  # Strong positive momentum
                high_24h=51000.0,
                low_24h=49000.0,
                rsi=50.0,
                macd=100.0,
                macd_signal=90.0,
                bb_upper=52000.0,
                bb_middle=50000.0,
                bb_lower=48000.0,
                sma_20=49500.0,
                ema_12=50200.0,
                ema_26=49800.0,
                news_sentiment_score=0.3,  # Good sentiment
                news_count=5,
                overall_sentiment="positive",
                upcoming_events_count=2,
                high_importance_events=1
            )
        ]
        
        signals = self.model._predict_with_rules(features)
        
        assert len(signals) == 1
        assert isinstance(signals[0], TradingSignal)
        assert signals[0].symbol == "BTC/USDT"
        assert signals[0].signal == "BUY"  # Should be BUY due to strong positive momentum and sentiment


class TestTradingTrainer:
    """Test cases for TradingTrainer class."""
    
    @patch('src.ml.training_system.MarketDataAggregator')
    def setup_method(self, mock_aggregator):
        """Set up test trainer."""
        self.trainer = TradingTrainer()
    
    @pytest.mark.asyncio
    @patch('src.ml.training_system.MarketDataAggregator')
    async def test_collect_and_store_data(self, mock_aggregator):
        """Test data collection and storage."""
        mock_aggregator_instance = Mock()
        mock_aggregator.return_value.__aenter__.return_value = mock_aggregator_instance
        mock_aggregator_instance.get_comprehensive_market_analysis = AsyncMock(return_value={
            'market_data': [
                {
                    'symbol': 'BTC/USDT',
                    'timestamp': '2023-01-01T00:00:00',
                    'price': 50000.0,
                    'volume_24h': 1000000.0,
                    'price_change_24h': 1000.0,
                    'price_change_percentage_24h': 2.0,
                    'high_24h': 51000.0,
                    'low_24h': 49000.0,
                    'source': 'test'
                }
            ],
            'summary': {'total_symbols': 1}
        })
        
        symbols = ['BTC/USDT']
        result = await self.trainer.collect_and_store_data(symbols)
        
        assert 'market_data' in result
        assert len(result['market_data']) == 1
        assert result['market_data'][0]['symbol'] == 'BTC/USDT'
    
    @pytest.mark.asyncio
    @patch('src.ml.training_system.TradingTrainer.collect_and_store_data')
    async def test_train_model_with_latest_data(self, mock_collect):
        """Test model training with latest data."""
        mock_collect.return_value = {
            'market_data': [
                {
                    'symbol': 'BTC/USDT',
                    'timestamp': '2023-01-01T00:00:00',
                    'price': 50000.0,
                    'volume_24h': 1000000.0,
                    'price_change_24h': 1000.0,
                    'price_change_percentage_24h': 2.0,
                    'high_24h': 51000.0,
                    'low_24h': 49000.0
                }
            ],
            'summary': {'total_symbols': 1}
        }
        
        symbols = ['BTC/USDT']
        
        with patch.object(self.trainer.model, 'train_model') as mock_train:
            mock_train.return_value = {'accuracy': 0.75, 'precision': 0.8}
            
            result = await self.trainer.train_model_with_latest_data(symbols)
            
            assert 'training_report' in result
            assert 'features_created' in result
            assert result['symbols_analyzed'] == symbols
    
    @pytest.mark.asyncio
    @patch('src.ml.training_system.TradingTrainer.collect_and_store_data')
    async def test_generate_trading_signals(self, mock_collect):
        """Test trading signal generation."""
        mock_collect.return_value = {
            'market_data': [
                {
                    'symbol': 'BTC/USDT',
                    'timestamp': '2023-01-01T00:00:00',
                    'price': 50000.0,
                    'volume_24h': 1000000.0,
                    'price_change_24h': 1000.0,
                    'price_change_percentage_24h': 2.0,
                    'high_24h': 51000.0,
                    'low_24h': 49000.0
                }
            ]
        }
        
        symbols = ['BTC/USDT']
        
        with patch.object(self.trainer.model, 'predict_signal') as mock_predict:
            mock_predict.return_value = [
                TradingSignal(
                    symbol="BTC/USDT",
                    timestamp="2023-01-01T00:00:00",
                    signal="BUY",
                    confidence=0.75,
                    price=50000.0,
                    reasoning="Test signal",
                    features_used={}
                )
            ]
            
            signals = await self.trainer.generate_trading_signals(symbols)
            
            assert len(signals) == 1
            assert signals[0].symbol == "BTC/USDT"
            assert signals[0].signal == "BUY"
    
    @pytest.mark.asyncio
    async def test_train_model_with_insufficient_data(self):
        """Test training with insufficient data."""
        with patch.object(self.trainer, 'collect_and_store_data') as mock_collect:
            mock_collect.return_value = {'market_data': []}
            
            result = await self.trainer.train_model_with_latest_data(['BTC/USDT'])
            
            assert 'error' in result
            assert result['error'] == "Insufficient data for training"


if __name__ == '__main__':
    pytest.main([__file__])
