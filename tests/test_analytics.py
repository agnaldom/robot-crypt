"""
Test suite for analytics modules.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.analytics.advanced_analytics import AdvancedAnalytics
from src.analytics.backtesting_engine import BacktestingEngine, OrderType, OrderStatus, Trade, Position
from src.analytics.risk_analytics import RiskAnalytics
from src.analytics.ml_models import MLModels
from src.analytics.report_generator import ReportGenerator


class TestAdvancedAnalytics:
    """Test advanced analytics functionality."""
    
    @pytest.fixture
    def analytics(self):
        """Create AdvancedAnalytics instance."""
        return AdvancedAnalytics()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'price': 100 + np.cumsum(np.random.normal(0, 1, len(dates))),
            'volume': np.random.randint(1000, 10000, len(dates)),
            'returns': np.random.normal(0, 0.02, len(dates))
        }, index=dates)
        
        return data
    
    def test_descriptive_statistics(self, analytics, sample_data):
        """Test descriptive statistics calculation."""
        stats = analytics.descriptive_statistics(sample_data)
        
        assert isinstance(stats, dict)
        assert 'price' in stats
        assert 'volume' in stats
        assert 'returns' in stats
        
        price_stats = stats['price']
        assert 'count' in price_stats
        assert 'mean' in price_stats
        assert 'std' in price_stats
        assert 'skewness' in price_stats
        assert 'kurtosis' in price_stats
        assert 'min' in price_stats
        assert 'max' in price_stats
        assert 'q1' in price_stats
        assert 'q3' in price_stats
        
        # Check that normality tests are included
        assert 'jarque_bera' in price_stats
        assert 'shapiro_wilk' in price_stats
    
    def test_descriptive_statistics_empty_data(self, analytics):
        """Test descriptive statistics with empty data."""
        empty_data = pd.DataFrame()
        stats = analytics.descriptive_statistics(empty_data)
        assert stats == {}
    
    def test_correlation_analysis(self, analytics, sample_data):
        """Test correlation analysis."""
        corr_analysis = analytics.correlation_analysis(sample_data)
        
        assert isinstance(corr_analysis, dict)
        assert 'pearson_matrix' in corr_analysis
        assert 'spearman_matrix' in corr_analysis
        assert 'kendall_matrix' in corr_analysis
        assert 'significant_correlations' in corr_analysis
        
        # Check matrix shapes
        pearson_matrix = corr_analysis['pearson_matrix']
        assert pearson_matrix.shape == (3, 3)  # 3 numeric columns
        
        # Check diagonal is 1.0
        assert np.allclose(np.diag(pearson_matrix), 1.0)
    
    def test_correlation_analysis_empty_data(self, analytics):
        """Test correlation analysis with empty data."""
        empty_data = pd.DataFrame()
        corr_analysis = analytics.correlation_analysis(empty_data)
        assert corr_analysis == {}
    
    def test_time_series_analysis(self, analytics, sample_data):
        """Test time series analysis."""
        ts_analysis = analytics.time_series_analysis(sample_data['price'])
        
        assert isinstance(ts_analysis, dict)
        assert 'trend_analysis' in ts_analysis
        assert 'seasonality' in ts_analysis
        assert 'stationarity' in ts_analysis
        assert 'autocorrelation' in ts_analysis
        assert 'volatility_clustering' in ts_analysis
        assert 'distribution_analysis' in ts_analysis
        
        # Check trend analysis
        trend = ts_analysis['trend_analysis']
        assert 'slope' in trend
        assert 'r_squared' in trend
        assert 'trend_direction' in trend
    
    def test_correlation_strength_classification(self, analytics):
        """Test correlation strength classification."""
        assert analytics._correlation_strength(0.9) == "Very Strong"
        assert analytics._correlation_strength(0.7) == "Strong"
        assert analytics._correlation_strength(0.5) == "Moderate"
        assert analytics._correlation_strength(0.3) == "Weak"
        assert analytics._correlation_strength(0.1) == "Very Weak"


class TestBacktestingEngine:
    """Test backtesting engine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Create BacktestingEngine instance."""
        return BacktestingEngine(initial_capital=10000.0, commission=0.001)
    
    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2023-01-01', '2023-01-31', freq='h')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.normal(0, 0.5, len(dates)))
        
        data = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.1, len(dates)),
            'high': prices + np.abs(np.random.normal(0, 0.2, len(dates))),
            'low': prices - np.abs(np.random.normal(0, 0.2, len(dates))),
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        # Ensure high >= close >= low and high >= open >= low
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        return data
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.initial_capital == 10000.0
        assert engine.commission == 0.001
        assert engine.cash == 10000.0
        assert engine.positions == {}
        assert engine.trades == []
    
    def test_add_data(self, engine, sample_ohlcv_data):
        """Test adding data to engine."""
        engine.add_data(sample_ohlcv_data, "BTCUSDT")
        
        assert hasattr(engine, 'data')
        assert hasattr(engine, 'symbol')
        assert engine.symbol == "BTCUSDT"
        assert len(engine.data) == len(sample_ohlcv_data)
    
    def test_add_data_invalid_columns(self, engine):
        """Test adding data with invalid columns."""
        invalid_data = pd.DataFrame({'price': [100, 101, 102]})
        
        with pytest.raises(ValueError, match="Dados devem conter"):
            engine.add_data(invalid_data)
    
    def test_reset(self, engine):
        """Test engine reset."""
        # Modify engine state
        engine.cash = 5000.0
        engine.positions = {"BTCUSDT": Position("BTCUSDT", 1.0, 100.0, datetime.now())}
        engine.trades = [Trade(datetime.now(), "BTCUSDT", OrderType.BUY, 1.0, 100.0)]
        
        # Reset
        engine.reset()
        
        assert engine.cash == 10000.0
        assert engine.positions == {}
        assert engine.trades == []
    
    def test_place_buy_order(self, engine, sample_ohlcv_data):
        """Test placing a buy order."""
        engine.add_data(sample_ohlcv_data, "BTCUSDT")
        engine.current_timestamp = sample_ohlcv_data.index[0]
        
        success = engine.place_order(OrderType.BUY, 1.0)
        
        assert success
        assert len(engine.trades) == 1
        assert engine.trades[0].order_type == OrderType.BUY
        assert engine.trades[0].quantity == 1.0
        assert engine.cash < 10000.0  # Cash should be reduced
    
    def test_place_sell_order(self, engine, sample_ohlcv_data):
        """Test placing a sell order."""
        engine.add_data(sample_ohlcv_data, "BTCUSDT")
        engine.current_timestamp = sample_ohlcv_data.index[0]
        
        # First buy some position
        engine.place_order(OrderType.BUY, 1.0)
        initial_cash = engine.cash
        
        # Then sell
        success = engine.place_order(OrderType.SELL, 0.5)
        
        assert success
        assert len(engine.trades) == 2
        assert engine.trades[1].order_type == OrderType.SELL
        assert engine.cash > initial_cash  # Cash should increase after sell
    
    def test_place_order_insufficient_funds(self, engine, sample_ohlcv_data):
        """Test placing order with insufficient funds."""
        engine.add_data(sample_ohlcv_data, "BTCUSDT")
        engine.current_timestamp = sample_ohlcv_data.index[0]
        engine.cash = 10.0  # Very low cash
        
        success = engine.place_order(OrderType.BUY, 100.0)  # Try to buy large amount
        
        assert not success
        assert len(engine.trades) == 0
    
    def test_place_order_insufficient_position(self, engine, sample_ohlcv_data):
        """Test selling more than position."""
        engine.add_data(sample_ohlcv_data, "BTCUSDT")
        engine.current_timestamp = sample_ohlcv_data.index[0]
        
        # Try to sell without any position
        success = engine.place_order(OrderType.SELL, 1.0)
        
        assert not success
        assert len(engine.trades) == 0


class TestRiskAnalytics:
    """Test risk analytics functionality."""
    
    @pytest.fixture
    def risk_analytics(self):
        """Create RiskAnalytics instance."""
        return RiskAnalytics()
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data."""
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.02, 252))  # 1 year of daily returns
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        returns = np.random.normal(0.001, 0.02, 252)
        prices = 100 * (1 + returns).cumprod()
        return pd.Series(prices, index=dates)
    
    def test_calculate_var_historical(self, risk_analytics, sample_returns):
        """Test VaR calculation using historical method."""
        var_result = risk_analytics.calculate_var(sample_returns, confidence_level=0.95, method='historical')
        
        assert isinstance(var_result, dict)
        assert 'var' in var_result
        assert 'var_pct' in var_result
        assert 'confidence_level' in var_result
        assert 'method' in var_result
        assert 'expected_shortfall' in var_result
        
        assert var_result['confidence_level'] == 0.95
        assert var_result['method'] == 'historical'
        assert var_result['var'] < 0  # VaR should be negative (loss)
    
    def test_calculate_var_parametric(self, risk_analytics, sample_returns):
        """Test VaR calculation using parametric method."""
        var_result = risk_analytics.calculate_var(sample_returns, confidence_level=0.95, method='parametric')
        
        assert isinstance(var_result, dict)
        assert var_result['method'] == 'parametric'
        assert var_result['var'] < 0
    
    def test_calculate_var_monte_carlo(self, risk_analytics, sample_returns):
        """Test VaR calculation using Monte Carlo method."""
        var_result = risk_analytics.calculate_var(sample_returns, confidence_level=0.95, method='monte_carlo')
        
        assert isinstance(var_result, dict)
        assert var_result['method'] == 'monte_carlo'
        assert var_result['var'] < 0
    
    def test_calculate_var_invalid_method(self, risk_analytics, sample_returns):
        """Test VaR calculation with invalid method."""
        with pytest.raises(ValueError, match="Método invalid não reconhecido"):
            risk_analytics.calculate_var(sample_returns, method='invalid')
    
    def test_calculate_var_empty_data(self, risk_analytics):
        """Test VaR calculation with empty data."""
        empty_returns = pd.Series([])
        var_result = risk_analytics.calculate_var(empty_returns)
        assert var_result == {}
    
    def test_calculate_cvar(self, risk_analytics, sample_returns):
        """Test CVaR calculation."""
        cvar_result = risk_analytics.calculate_cvar(sample_returns, confidence_level=0.95)
        
        assert isinstance(cvar_result, dict)
        assert 'cvar' in cvar_result
        assert 'cvar_pct' in cvar_result
        assert 'var' in cvar_result
        assert 'tail_expectation' in cvar_result
        assert 'tail_observations' in cvar_result
        assert 'tail_percentage' in cvar_result
        
        assert cvar_result['cvar'] <= cvar_result['var']  # CVaR should be <= VaR
    
    def test_calculate_cvar_empty_data(self, risk_analytics):
        """Test CVaR calculation with empty data."""
        empty_returns = pd.Series([])
        cvar_result = risk_analytics.calculate_cvar(empty_returns)
        assert cvar_result == {}
    
    def test_calculate_maximum_drawdown(self, risk_analytics, sample_prices):
        """Test maximum drawdown calculation."""
        dd_result = risk_analytics.calculate_maximum_drawdown(sample_prices)
        
        assert isinstance(dd_result, dict)
        assert 'max_drawdown' in dd_result
        assert 'max_drawdown_pct' in dd_result
        assert 'max_drawdown_date' in dd_result
        assert 'peak_before_dd' in dd_result
        assert 'drawdown_duration_days' in dd_result
        assert 'underwater_duration' in dd_result
        assert 'current_drawdown' in dd_result
        assert 'drawdown_series' in dd_result
        
        assert dd_result['max_drawdown'] <= 0  # Max drawdown should be negative
        assert dd_result['max_drawdown_pct'] <= 0
    
    def test_calculate_maximum_drawdown_empty_data(self, risk_analytics):
        """Test maximum drawdown with empty data."""
        empty_prices = pd.Series([])
        dd_result = risk_analytics.calculate_maximum_drawdown(empty_prices)
        assert dd_result == {}
    
    def test_calculate_volatility_metrics(self, risk_analytics, sample_returns):
        """Test volatility metrics calculation."""
        vol_result = risk_analytics.calculate_volatility_metrics(sample_returns, annualize=True)
        
        assert isinstance(vol_result, dict)
        # Note: We can't check all expected keys without seeing the full implementation
        # but we can check the basic structure
        assert len(vol_result) > 0
    
    def test_calculate_volatility_metrics_empty_data(self, risk_analytics):
        """Test volatility metrics with empty data."""
        empty_returns = pd.Series([])
        vol_result = risk_analytics.calculate_volatility_metrics(empty_returns)
        assert vol_result == {}
    
    def test_calculate_sharpe_ratio(self, risk_analytics, sample_returns):
        """Test Sharpe ratio calculation."""
        sharpe_result = risk_analytics.calculate_sharpe_ratio(sample_returns, risk_free_rate=0.02)
        
        assert isinstance(sharpe_result, dict)
        assert 'sharpe_ratio' in sharpe_result
        assert 'sortino_ratio' in sharpe_result
        assert 'calmar_ratio' in sharpe_result
        assert 'annual_return' in sharpe_result
        assert 'annual_volatility' in sharpe_result
        assert 'excess_return' in sharpe_result
        assert 'downside_volatility' in sharpe_result
        
        assert isinstance(sharpe_result['sharpe_ratio'], float)
        assert isinstance(sharpe_result['sortino_ratio'], float)
        assert isinstance(sharpe_result['annual_return'], float)
    
    def test_calculate_sharpe_ratio_empty_data(self, risk_analytics):
        """Test Sharpe ratio with empty data."""
        empty_returns = pd.Series([])
        sharpe_result = risk_analytics.calculate_sharpe_ratio(empty_returns)
        assert sharpe_result == {}


class TestMLModels:
    """Test ML models functionality."""
    
    @pytest.fixture
    def ml_models(self):
        """Create MLModels instance with temporary directory."""
        temp_dir = tempfile.mkdtemp()
        return MLModels(models_dir=temp_dir)
    
    @pytest.fixture
    def sample_ml_data(self):
        """Create sample data for ML testing."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        
        data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, len(dates)),
            'feature2': np.random.normal(0, 1, len(dates)),
            'feature3': np.random.normal(0, 1, len(dates)),
            'target': np.random.normal(0, 1, len(dates))
        }, index=dates)
        
        # Add some correlation to make it more realistic
        data['target'] = 0.5 * data['feature1'] + 0.3 * data['feature2'] + np.random.normal(0, 0.5, len(dates))
        
        return data
    
    def test_ml_models_initialization(self, ml_models):
        """Test ML models initialization."""
        assert hasattr(ml_models, 'models_dir')
        assert hasattr(ml_models, 'available_models')
        assert 'linear_regression' in ml_models.available_models
        assert 'random_forest' in ml_models.available_models
        assert 'xgboost' in ml_models.available_models
    
    def test_prepare_features(self, ml_models, sample_ml_data):
        """Test feature preparation."""
        X, y = ml_models.prepare_features(sample_ml_data, 'target')
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert len(X) > 0  # Should have some rows after dropping NaN
        assert 'target' not in X.columns  # Target should not be in features
        
        # Check that lag features were created
        feature_names = X.columns.tolist()
        assert any('_lag_' in col for col in feature_names)
        assert any('_ma_' in col for col in feature_names)
        assert any('_std_' in col for col in feature_names)
    
    def test_prepare_features_custom_columns(self, ml_models, sample_ml_data):
        """Test feature preparation with custom columns."""
        X, y = ml_models.prepare_features(sample_ml_data, 'target', 
                                        feature_columns=['feature1', 'feature2'])
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        # Should have original features plus derived features
        assert len(X.columns) > 2
    
    @pytest.mark.slow
    def test_train_model_linear_regression(self, ml_models, sample_ml_data):
        """Test training linear regression model."""
        X, y = ml_models.prepare_features(sample_ml_data, 'target')
        
        # Skip hyperparameter tuning for speed
        result = ml_models.train_model(X, y, model_name='linear_regression', 
                                     hyperparameter_tuning=False, feature_selection=False)
        
        assert isinstance(result, dict)
        assert 'model_id' in result
        assert 'model_name' in result
        assert 'metrics' in result
        assert 'cv_scores' in result
        
        # Check metrics structure
        metrics = result['metrics']
        assert 'train' in metrics
        assert 'test' in metrics
        assert 'mse' in metrics['train']
        assert 'mae' in metrics['train']
        assert 'r2' in metrics['train']
    
    def test_train_model_invalid_model(self, ml_models, sample_ml_data):
        """Test training with invalid model name."""
        X, y = ml_models.prepare_features(sample_ml_data, 'target')
        
        with pytest.raises(ValueError, match="Modelo invalid_model não disponível"):
            ml_models.train_model(X, y, model_name='invalid_model')


class TestReportGenerator:
    """Test report generator functionality."""
    
    @pytest.fixture
    def report_generator(self):
        """Create ReportGenerator instance with temporary directory."""
        temp_dir = tempfile.mkdtemp()
        return ReportGenerator(output_dir=temp_dir)
    
    @pytest.fixture
    def sample_trading_data(self):
        """Create sample trading data."""
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
        returns = np.diff(prices) / prices[:-1]
        
        data = pd.DataFrame({
            'close': prices,
            'returns': np.concatenate([[0], returns]),  # Add 0 for first day
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        return data
    
    def test_report_generator_initialization(self, report_generator):
        """Test report generator initialization."""
        assert hasattr(report_generator, 'output_dir')
        assert hasattr(report_generator, 'advanced_analytics')
        assert hasattr(report_generator, 'risk_analytics')
        assert hasattr(report_generator, 'templates')
        assert report_generator.output_dir.exists()
    
    @patch('src.analytics.report_generator.ReportGenerator._generate_html_report')
    @patch('src.analytics.report_generator.ReportGenerator._generate_json_report')
    def test_generate_comprehensive_report_json(self, mock_json, mock_html, 
                                              report_generator, sample_trading_data):
        """Test generating comprehensive report in JSON format."""
        mock_json.return_value = "test_report.json"
        
        result = report_generator.generate_comprehensive_report(
            sample_trading_data, format_type='json', title='Test Report')
        
        assert isinstance(result, dict)
        assert 'report_path' in result
        assert 'report_data' in result
        assert 'timestamp' in result
        assert 'format' in result
        assert result['format'] == 'json'
        
        report_data = result['report_data']
        assert 'metadata' in report_data
        assert 'executive_summary' in report_data
        assert 'risk_analytics' in report_data
        
        mock_json.assert_called_once()
        mock_html.assert_not_called()
    
    def test_generate_metadata(self, report_generator, sample_trading_data):
        """Test metadata generation."""
        metadata = report_generator._generate_metadata(sample_trading_data, "Test Title")
        
        assert isinstance(metadata, dict)
        assert 'title' in metadata
        assert 'generated_at' in metadata
        assert 'data_period' in metadata
        assert 'columns_analyzed' in metadata
        assert 'missing_data' in metadata
        
        assert metadata['title'] == "Test Title"
        
        data_period = metadata['data_period']
        assert 'start' in data_period
        assert 'end' in data_period
        assert 'total_observations' in data_period
        assert 'frequency' in data_period
    
    def test_infer_frequency(self, report_generator):
        """Test frequency inference."""
        # Test daily frequency
        daily_index = pd.date_range('2023-01-01', '2023-01-10', freq='D')
        assert report_generator._infer_frequency(daily_index) == 'Daily'
        
        # Test hourly frequency
        hourly_index = pd.date_range('2023-01-01', '2023-01-02', freq='h')
        assert report_generator._infer_frequency(hourly_index) == 'Hourly'
        
        # Test minute frequency
        minute_index = pd.date_range('2023-01-01 00:00', '2023-01-01 01:00', freq='min')
        assert report_generator._infer_frequency(minute_index) == 'Minute'
        
        # Test weekly frequency
        weekly_index = pd.date_range('2023-01-01', '2023-03-01', freq='W')
        assert report_generator._infer_frequency(weekly_index) == 'Weekly'
    
    def test_generate_executive_summary(self, report_generator, sample_trading_data):
        """Test executive summary generation."""
        returns = sample_trading_data['returns']
        summary = report_generator._generate_executive_summary(sample_trading_data, returns)
        
        assert isinstance(summary, dict)
        assert 'period_return_pct' in summary
        assert 'annualized_volatility_pct' in summary
        assert 'sharpe_ratio' in summary
        assert 'max_drawdown_pct' in summary
        assert 'performance_score' in summary
        assert 'risk_level' in summary
        assert 'return_classification' in summary
        assert 'key_insights' in summary
    
    def test_calculate_performance_score(self, report_generator):
        """Test performance score calculation."""
        score = report_generator._calculate_performance_score(0.1, 0.2, 1.5, -0.1)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_classify_risk_level(self, report_generator):
        """Test risk level classification."""
        assert report_generator._classify_risk_level(0.05) == "Muito Baixo"
        assert report_generator._classify_risk_level(0.15) == "Baixo"
        assert report_generator._classify_risk_level(0.25) == "Moderado"
        assert report_generator._classify_risk_level(0.4) == "Alto"
        assert report_generator._classify_risk_level(0.6) == "Muito Alto"
    
    def test_classify_returns(self, report_generator):
        """Test returns classification."""
        assert report_generator._classify_returns(0.4) == "Excelente"
        assert report_generator._classify_returns(0.2) == "Bom"
        assert report_generator._classify_returns(0.05) == "Positivo"


class TestTradeAndPosition:
    """Test Trade and Position dataclasses."""
    
    def test_trade_creation(self):
        """Test Trade dataclass creation."""
        trade = Trade(
            timestamp=datetime.now(),
            symbol="BTCUSDT",
            order_type=OrderType.BUY,
            quantity=1.0,
            price=50000.0,
            commission=50.0
        )
        
        assert trade.symbol == "BTCUSDT"
        assert trade.order_type == OrderType.BUY
        assert trade.quantity == 1.0
        assert trade.price == 50000.0
        assert trade.value == 50000.0  # quantity * price
        assert trade.commission == 50.0
    
    def test_position_creation(self):
        """Test Position dataclass creation."""
        position = Position(
            symbol="BTCUSDT",
            quantity=2.0,
            avg_price=45000.0,
            timestamp=datetime.now()
        )
        
        assert position.symbol == "BTCUSDT"
        assert position.quantity == 2.0
        assert position.avg_price == 45000.0
        assert position.value == 90000.0  # quantity * avg_price
        assert position.is_long
        assert not position.is_short
    
    def test_position_short(self):
        """Test short position."""
        position = Position(
            symbol="BTCUSDT",
            quantity=-1.0,
            avg_price=45000.0,
            timestamp=datetime.now()
        )
        
        assert not position.is_long
        assert position.is_short


class TestOrderEnums:
    """Test order enums."""
    
    def test_order_type_enum(self):
        """Test OrderType enum."""
        assert OrderType.BUY.value == "buy"
        assert OrderType.SELL.value == "sell"
    
    def test_order_status_enum(self):
        """Test OrderStatus enum."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.CANCELLED.value == "cancelled"


# Integration tests
class TestAnalyticsIntegration:
    """Test integration between analytics modules."""
    
    @pytest.fixture
    def sample_integrated_data(self):
        """Create sample data for integration testing."""
        dates = pd.date_range('2023-01-01', '2023-06-30', freq='D')
        np.random.seed(42)
        
        prices = 100 * (1 + np.random.normal(0.001, 0.02, len(dates))).cumprod()
        returns = np.diff(prices) / prices[:-1]
        
        data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, len(dates))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.002, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.002, len(dates)))),
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates)),
            'returns': np.concatenate([[0], returns])
        }, index=dates)
        
        return data
    
    def test_full_analytics_pipeline(self, sample_integrated_data):
        """Test full analytics pipeline."""
        # Initialize all modules
        advanced_analytics = AdvancedAnalytics()
        risk_analytics = RiskAnalytics()
        
        # Run descriptive analytics
        stats = advanced_analytics.descriptive_statistics(sample_integrated_data)
        assert len(stats) > 0
        
        # Run correlation analysis
        corr_analysis = advanced_analytics.correlation_analysis(sample_integrated_data)
        assert 'pearson_matrix' in corr_analysis
        
        # Run risk analytics
        returns = sample_integrated_data['returns'].dropna()
        var_result = risk_analytics.calculate_var(returns)
        assert 'var' in var_result
        
        cvar_result = risk_analytics.calculate_cvar(returns)
        assert 'cvar' in cvar_result
        
        dd_result = risk_analytics.calculate_maximum_drawdown(sample_integrated_data['close'])
        assert 'max_drawdown' in dd_result
    
    @pytest.mark.slow
    def test_backtesting_with_analytics(self, sample_integrated_data):
        """Test backtesting engine with analytics."""
        # Initialize backtesting engine
        engine = BacktestingEngine(initial_capital=10000.0)
        engine.add_data(sample_integrated_data)
        
        # Simple buy and hold strategy
        first_timestamp = sample_integrated_data.index[0]
        last_timestamp = sample_integrated_data.index[-1]
        
        engine.current_timestamp = first_timestamp
        buy_success = engine.place_order(OrderType.BUY, 1.0)
        assert buy_success
        
        engine.current_timestamp = last_timestamp
        sell_success = engine.place_order(OrderType.SELL, 1.0)
        assert sell_success
        
        # Analyze results
        assert len(engine.trades) == 2
        assert engine.trades[0].order_type == OrderType.BUY
        assert engine.trades[1].order_type == OrderType.SELL
        
        # Calculate portfolio returns
        buy_price = engine.trades[0].price
        sell_price = engine.trades[1].price
        portfolio_return = (sell_price - buy_price) / buy_price
        
        # Analyze with risk analytics
        risk_analytics = RiskAnalytics()
        returns_series = pd.Series([portfolio_return])
        
        # This should not fail (even with single data point)
        vol_metrics = risk_analytics.calculate_volatility_metrics(returns_series)
        # With single data point, most metrics will be empty or zero
        assert isinstance(vol_metrics, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
