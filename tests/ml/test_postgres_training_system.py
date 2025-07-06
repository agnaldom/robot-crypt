"""Test suite for postgres_training_system module."""

import pytest
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import tempfile
import os
from dataclasses import asdict

from src.ml.postgres_training_system import (
    PostgresTradingDataProcessor,
    PostgresMLModel,
    PostgresTradingTrainer,
    TrainingFeatures,
    TrainingSignal
)


class TestTrainingFeatures:
    """Test cases for TrainingFeatures dataclass."""
    
    def test_training_features_creation(self):
        """Test TrainingFeatures can be created with all fields."""
        features = TrainingFeatures(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            price=50000.0,
            volume=1000000.0,
            price_change_1h=1.5,
            price_change_4h=3.2,
            price_change_24h=5.1,
            volume_change_24h=2.3,
            volatility_24h=0.15,
            sma_10=49800.0,
            sma_20=49500.0,
            sma_50=48000.0,
            ema_12=50100.0,
            ema_26=49900.0,
            rsi_14=65.5,
            macd=150.0,
            macd_signal=140.0,
            macd_hist=10.0,
            bb_upper=51000.0,
            bb_lower=48000.0,
            bb_middle=49500.0,
            stoch_k=75.2,
            stoch_d=73.1,
            cci=120.5,
            williams_r=-25.3,
            atr=500.0,
            volume_sma=950000.0,
            news_sentiment=0.3,
            social_sentiment=0.2,
            fear_greed_index=0.6,
            upcoming_events=2,
            event_impact=0.4
        )
        
        assert features.symbol == "BTC/USDT"
        assert features.price == 50000.0
        assert features.rsi_14 == 65.5
        assert features.news_sentiment == 0.3
        
        # Test conversion to dict
        feature_dict = asdict(features)
        assert isinstance(feature_dict, dict)
        assert feature_dict['symbol'] == "BTC/USDT"


class TestTrainingSignal:
    """Test cases for TrainingSignal dataclass."""
    
    def test_training_signal_creation(self):
        """Test TrainingSignal can be created with all fields."""
        signal = TrainingSignal(
            symbol="ETH/USDT",
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.85,
            price_target=2100.0,
            stop_loss=1950.0,
            take_profit=2200.0,
            reasoning="Strong technical breakout"
        )
        
        assert signal.symbol == "ETH/USDT"
        assert signal.signal_type == "BUY"
        assert signal.confidence == 0.85
        assert signal.price_target == 2100.0


class TestPostgresTradingDataProcessor:
    """Test cases for PostgresTradingDataProcessor class."""
    
    def setup_method(self):
        """Set up test processor with mocked PostgresManager."""
        self.mock_postgres_manager = Mock()
        self.processor = PostgresTradingDataProcessor(self.mock_postgres_manager)
    
    @pytest.mark.asyncio
    async def test_save_training_features(self):
        """Test saving training features to PostgreSQL."""
        features = TrainingFeatures(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            price=50000.0,
            volume=1000000.0,
            price_change_1h=1.5,
            price_change_4h=3.2,
            price_change_24h=5.1,
            volume_change_24h=2.3,
            volatility_24h=0.15,
            sma_10=49800.0,
            sma_20=49500.0,
            sma_50=48000.0,
            ema_12=50100.0,
            ema_26=49900.0,
            rsi_14=65.5,
            macd=150.0,
            macd_signal=140.0,
            macd_hist=10.0,
            bb_upper=51000.0,
            bb_lower=48000.0,
            bb_middle=49500.0,
            stoch_k=75.2,
            stoch_d=73.1,
            cci=120.5,
            williams_r=-25.3,
            atr=500.0,
            volume_sma=950000.0,
            news_sentiment=0.3,
            social_sentiment=0.2,
            fear_greed_index=0.6,
            upcoming_events=2,
            event_impact=0.4
        )
        
        with patch.object(self.processor, '_create_features_table'):
            self.mock_postgres_manager.execute_query.return_value = None
            
            result = await self.processor.save_training_features(features)
            
            assert result is True
            self.mock_postgres_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_training_signal(self):
        """Test saving training signal to PostgreSQL."""
        signal = TrainingSignal(
            symbol="ETH/USDT",
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.85,
            price_target=2100.0,
            stop_loss=1950.0,
            take_profit=2200.0,
            reasoning="Strong technical breakout"
        )
        
        with patch.object(self.processor, '_create_signals_table'):
            self.mock_postgres_manager.execute_query.return_value = None
            
            result = await self.processor.save_training_signal(signal)
            
            assert result is True
            self.mock_postgres_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_training_data(self):
        """Test retrieving training data from PostgreSQL."""
        # Mock features data
        mock_features_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': datetime.now(),
                'price': 50000.0,
                'rsi_14': 65.5
            }
        ]
        
        # Mock signals data
        mock_signals_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': datetime.now(),
                'signal_type': 'BUY',
                'confidence': 0.85
            }
        ]
        
        # Setup mock to return different data for different queries
        self.mock_postgres_manager.fetch_all.side_effect = [
            mock_features_data,
            mock_signals_data
        ]
        
        features_df, signals_df = await self.processor.get_training_data('BTC/USDT', days=30)
        
        assert isinstance(features_df, pd.DataFrame)
        assert isinstance(signals_df, pd.DataFrame)
        assert len(features_df) == 1
        assert len(signals_df) == 1
        assert features_df.iloc[0]['symbol'] == 'BTC/USDT'
        assert signals_df.iloc[0]['signal_type'] == 'BUY'
    
    @pytest.mark.asyncio
    async def test_get_market_data(self):
        """Test retrieving market data from PostgreSQL."""
        mock_market_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': datetime.now(),
                'close': 50000.0,
                'volume': 1000000.0
            }
        ]
        
        self.mock_postgres_manager.fetch_all.return_value = mock_market_data
        
        df = await self.processor.get_market_data('BTC/USDT', days=30)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['symbol'] == 'BTC/USDT'
        assert df.iloc[0]['close'] == 50000.0
    
    @pytest.mark.asyncio
    async def test_save_training_log(self):
        """Test saving training log."""
        metrics = {'accuracy': 0.85, 'precision': 0.78}
        
        with patch.object(self.mock_postgres_manager, 'save_log', new_callable=AsyncMock) as mock_save_log:
            mock_save_log.return_value = True
            
            result = await self.processor.save_training_log(
                'random_forest', metrics, 'BTC/USDT', datetime.now()
            )
            
            assert result is True
            mock_save_log.assert_called_once()
    
    def test_get_features_count(self):
        """Test getting features count."""
        self.mock_postgres_manager.fetch_one.return_value = (150,)
        
        count = self.processor.get_features_count()
        
        assert count == 150
        self.mock_postgres_manager.fetch_one.assert_called_once()
    
    def test_get_signals_count(self):
        """Test getting signals count."""
        self.mock_postgres_manager.fetch_one.return_value = (75,)
        
        count = self.processor.get_signals_count()
        
        assert count == 75
        self.mock_postgres_manager.fetch_one.assert_called_once()


class TestPostgresMLModel:
    """Test cases for PostgresMLModel class."""
    
    def test_model_initialization_random_forest(self):
        """Test PostgresMLModel initialization with random forest."""
        model = PostgresMLModel(model_type="random_forest", n_estimators=50)
        
        assert model.model_type == "random_forest"
        assert model.model is not None
        assert hasattr(model, 'scaler')
        assert model.feature_columns == []
    
    def test_model_initialization_gradient_boosting(self):
        """Test PostgresMLModel initialization with gradient boosting."""
        model = PostgresMLModel(model_type="gradient_boosting", learning_rate=0.1)
        
        assert model.model_type == "gradient_boosting"
        assert model.model is not None
    
    def test_model_initialization_invalid_type(self):
        """Test PostgresMLModel initialization with invalid type."""
        with pytest.raises(ValueError):
            PostgresMLModel(model_type="invalid_model")
    
    def test_prepare_features(self):
        """Test feature preparation."""
        model = PostgresMLModel()
        
        # Create mock features DataFrame
        features_data = {
            'id': [1, 2, 3],
            'timestamp': [datetime.now()] * 3,
            'price': [50000.0, 51000.0, 49000.0],
            'volume': [1000000.0, 1100000.0, 900000.0],
            'rsi_14': [65.5, 70.2, 45.8]
        }
        features_df = pd.DataFrame(features_data)
        
        features_array = model.prepare_features(features_df)
        
        assert isinstance(features_array, np.ndarray)
        assert features_array.shape[0] == 3
        assert 'price' in model.feature_columns
        assert 'volume' in model.feature_columns
        assert 'rsi_14' in model.feature_columns
        assert 'id' not in model.feature_columns
        assert 'timestamp' not in model.feature_columns
    
    def test_prepare_targets(self):
        """Test target preparation."""
        model = PostgresMLModel()
        
        # Create mock signals DataFrame
        signals_data = {
            'signal_type': ['BUY', 'SELL', 'HOLD'],
            'confidence': [0.85, 0.75, 0.60]
        }
        signals_df = pd.DataFrame(signals_data)
        
        targets = model.prepare_targets(signals_df)
        
        assert isinstance(targets, np.ndarray)
        assert len(targets) == 3
        assert targets[0] == 1   # BUY
        assert targets[1] == -1  # SELL
        assert targets[2] == 0   # HOLD
    
    @pytest.mark.asyncio
    async def test_train_model(self):
        """Test model training."""
        model = PostgresMLModel(model_type="random_forest", n_estimators=10)
        
        # Create mock data
        features_data = {
            'price': np.random.rand(50) * 10000 + 45000,
            'volume': np.random.rand(50) * 1000000 + 500000,
            'rsi_14': np.random.rand(50) * 100
        }
        features_df = pd.DataFrame(features_data)
        
        signals_data = {
            'signal_type': np.random.choice(['BUY', 'SELL', 'HOLD'], 50)
        }
        signals_df = pd.DataFrame(signals_data)
        
        metrics = await model.train(features_df, signals_df)
        
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 0 <= metrics['accuracy'] <= 1
    
    @pytest.mark.asyncio
    async def test_predict(self):
        """Test model prediction."""
        model = PostgresMLModel(model_type="random_forest", n_estimators=10)
        
        # Train model first
        features_data = {
            'price': np.random.rand(50) * 10000 + 45000,
            'volume': np.random.rand(50) * 1000000 + 500000,
            'rsi_14': np.random.rand(50) * 100
        }
        features_df = pd.DataFrame(features_data)
        
        signals_data = {
            'signal_type': np.random.choice(['BUY', 'SELL', 'HOLD'], 50)
        }
        signals_df = pd.DataFrame(signals_data)
        
        await model.train(features_df, signals_df)
        
        # Test prediction
        test_features = features_df.iloc[:5].copy()
        test_features['symbol'] = 'BTC/USDT'
        test_features['timestamp'] = datetime.now()
        
        signals = await model.predict(test_features)
        
        assert isinstance(signals, list)
        # May be empty if confidence is too low
        for signal in signals:
            assert isinstance(signal, TrainingSignal)
            assert signal.signal_type in ['BUY', 'SELL', 'HOLD']
            assert 0 <= signal.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_save_and_load_model(self):
        """Test model save and load functionality."""
        model = PostgresMLModel(model_type="random_forest", n_estimators=10)
        
        # Train a simple model
        features_data = {
            'price': [50000.0, 51000.0, 49000.0],
            'volume': [1000000.0, 1100000.0, 900000.0]
        }
        features_df = pd.DataFrame(features_data)
        
        signals_data = {
            'signal_type': ['BUY', 'SELL', 'HOLD']
        }
        signals_df = pd.DataFrame(signals_data)
        
        await model.train(features_df, signals_df)
        
        # Save model
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            save_result = await model.save_model(tmp_path)
            assert save_result is True
            assert os.path.exists(tmp_path)
            
            # Load model
            new_model = PostgresMLModel()
            load_result = await new_model.load_model(tmp_path)
            assert load_result is True
            assert new_model.model is not None
            assert new_model.scaler is not None
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestPostgresTradingTrainer:
    """Test cases for PostgresTradingTrainer class."""
    
    def setup_method(self):
        """Set up test trainer."""
        with patch('src.ml.postgres_training_system.PostgresTradingTrainer._load_config') as mock_load_config:
            mock_load_config.return_value = {
                'model': {
                    'type': 'random_forest',
                    'random_forest': {'n_estimators': 10},
                    'model_path': 'test_model.pkl'
                },
                'data': {
                    'default_symbols': ['BTC/USDT', 'ETH/USDT'],
                    'historical_days': 30
                }
            }
            self.trainer = PostgresTradingTrainer()
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test trainer initialization."""
        with patch('src.ml.postgres_training_system.PostgresManager') as mock_pg_manager:
            mock_manager_instance = Mock()
            mock_pg_manager.return_value = mock_manager_instance
            mock_manager_instance.connect.return_value = None
            
            await self.trainer.initialize()
            
            assert self.trainer.postgres_manager is not None
            assert self.trainer.data_processor is not None
            assert self.trainer.model is not None
            mock_manager_instance.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_and_process_data(self):
        """Test data collection and processing."""
        # Mock dependencies
        self.trainer.data_processor = Mock()
        self.trainer.data_processor.get_market_data = AsyncMock(return_value=pd.DataFrame({
            'close': [50000.0, 51000.0, 49000.0],
            'volume': [1000000.0, 1100000.0, 900000.0],
            'timestamp': [datetime.now()] * 3
        }))
        self.trainer.data_processor.save_training_features = AsyncMock(return_value=True)
        self.trainer.data_processor.save_training_signal = AsyncMock(return_value=True)
        
        with patch.object(self.trainer, '_calculate_features') as mock_calc_features, \
             patch.object(self.trainer, '_generate_training_signals') as mock_gen_signals:
            
            mock_calc_features.return_value = [Mock(spec=TrainingFeatures)]
            mock_gen_signals.return_value = [Mock(spec=TrainingSignal)]
            
            await self.trainer.collect_and_process_data(['BTC/USDT'])
            
            self.trainer.data_processor.get_market_data.assert_called_once()
            mock_calc_features.assert_called_once()
            mock_gen_signals.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_train_model(self):
        """Test model training."""
        # Mock dependencies
        self.trainer.data_processor = Mock()
        self.trainer.model = Mock()
        
        mock_features_df = pd.DataFrame({
            'price': [50000.0, 51000.0],
            'volume': [1000000.0, 1100000.0]
        })
        mock_signals_df = pd.DataFrame({
            'signal_type': ['BUY', 'SELL']
        })
        
        self.trainer.data_processor.get_training_data = AsyncMock(
            return_value=(mock_features_df, mock_signals_df)
        )
        self.trainer.model.train = AsyncMock(return_value={'accuracy': 0.85})
        self.trainer.model.save_model = AsyncMock(return_value=True)
        self.trainer.data_processor.save_training_log = AsyncMock(return_value=True)
        
        metrics = await self.trainer.train_model(['BTC/USDT'], days=30)
        
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        self.trainer.model.train.assert_called_once()
        self.trainer.model.save_model.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_signals(self):
        """Test signal generation."""
        # Mock dependencies
        self.trainer.data_processor = Mock()
        self.trainer.model = Mock()
        
        mock_features_df = pd.DataFrame({
            'symbol': ['BTC/USDT'],
            'timestamp': [datetime.now()],
            'price': [50000.0]
        })
        
        mock_signal = TrainingSignal(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.85
        )
        
        self.trainer.data_processor.get_training_data = AsyncMock(
            return_value=(mock_features_df, pd.DataFrame())
        )
        self.trainer.model.predict = AsyncMock(return_value=[mock_signal])
        self.trainer.data_processor.save_training_signal = AsyncMock(return_value=True)
        
        signals = await self.trainer.generate_signals(['BTC/USDT'])
        
        assert len(signals) == 1
        assert signals[0].symbol == "BTC/USDT"
        assert signals[0].signal_type == "BUY"
    
    @pytest.mark.asyncio
    async def test_calculate_features(self):
        """Test feature calculation."""
        market_data = pd.DataFrame({
            'close': [50000.0, 51000.0, 49000.0],
            'volume': [1000000.0, 1100000.0, 900000.0],
            'timestamp': [datetime.now()] * 3
        })
        
        features_list = await self.trainer._calculate_features(market_data, 'BTC/USDT')
        
        assert isinstance(features_list, list)
        assert len(features_list) == 3
        for features in features_list:
            assert isinstance(features, TrainingFeatures)
            assert features.symbol == 'BTC/USDT'
    
    @pytest.mark.asyncio
    async def test_generate_training_signals(self):
        """Test training signal generation."""
        features_list = [
            TrainingFeatures(
                symbol="BTC/USDT",
                timestamp=datetime.now(),
                price=50000.0,
                volume=1000000.0,
                price_change_1h=0.0,
                price_change_4h=0.0,
                price_change_24h=0.0,
                volume_change_24h=0.0,
                volatility_24h=0.0,
                sma_10=0.0,
                sma_20=51000.0,  # Price below SMA20
                sma_50=0.0,
                ema_12=0.0,
                ema_26=0.0,
                rsi_14=25.0,  # Oversold
                macd=0.0,
                macd_signal=0.0,
                macd_hist=0.0,
                bb_upper=0.0,
                bb_lower=0.0,
                bb_middle=0.0,
                stoch_k=0.0,
                stoch_d=0.0,
                cci=0.0,
                williams_r=0.0,
                atr=0.0,
                volume_sma=0.0,
                news_sentiment=0.0,
                social_sentiment=0.0,
                fear_greed_index=0.0,
                upcoming_events=0,
                event_impact=0.0
            )
        ]
        
        signals = await self.trainer._generate_training_signals(features_list, 'BTC/USDT')
        
        assert len(signals) == 1
        assert isinstance(signals[0], TrainingSignal)
        assert signals[0].symbol == 'BTC/USDT'
        # Should be BUY due to RSI < 30 and price > SMA20
        assert signals[0].signal_type == 'BUY'
    
    @pytest.mark.asyncio
    async def test_run_training_pipeline(self):
        """Test complete training pipeline."""
        with patch.object(self.trainer, 'initialize') as mock_init, \
             patch.object(self.trainer, 'collect_and_process_data') as mock_collect, \
             patch.object(self.trainer, 'train_model') as mock_train, \
             patch.object(self.trainer, 'generate_signals') as mock_generate:
            
            mock_init.return_value = None
            mock_collect.return_value = None
            mock_train.return_value = {'accuracy': 0.85}
            mock_generate.return_value = [Mock(spec=TrainingSignal)]
            
            self.trainer.postgres_manager = Mock()
            self.trainer.postgres_manager.disconnect = AsyncMock()
            
            metrics, signals = await self.trainer.run_training_pipeline()
            
            assert metrics['accuracy'] == 0.85
            assert len(signals) == 1
            mock_init.assert_called_once()
            mock_collect.assert_called_once()
            mock_train.assert_called_once()
            mock_generate.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
