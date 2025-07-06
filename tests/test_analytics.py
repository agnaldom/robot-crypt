"""
Testes para o módulo de Analytics
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analytics import (
    AdvancedAnalytics,
    MLModels,
    BacktestingEngine,
    RiskAnalytics,
    ReportGenerator
)
from analytics.backtesting_engine import OrderType, simple_ma_strategy, rsi_strategy


@pytest.fixture
def sample_data():
    """Fixture para dados de teste"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Gerar preços simulados
    returns = np.random.normal(0.001, 0.02, 100)
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'close': prices,
        'open': prices * (1 + np.random.normal(0, 0.001, 100)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
        'volume': np.random.lognormal(10, 0.5, 100),
        'returns': returns  # Usar returns diretamente
    }, index=dates)
    
    return data


@pytest.fixture
def returns_data():
    """Fixture para dados de retornos"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    returns = np.random.normal(0.001, 0.02, 100)
    return pd.Series(returns, index=dates)


class TestAdvancedAnalytics:
    """Testes para AdvancedAnalytics"""
    
    def test_init(self):
        """Teste de inicialização"""
        analytics = AdvancedAnalytics()
        assert hasattr(analytics, 'scaler')
        assert hasattr(analytics, 'pca')
    
    def test_descriptive_statistics(self, sample_data):
        """Teste de estatísticas descritivas"""
        analytics = AdvancedAnalytics()
        stats = analytics.descriptive_statistics(sample_data)
        
        assert isinstance(stats, dict)
        assert 'close' in stats
        assert 'mean' in stats['close']
        assert 'std' in stats['close']
        assert 'skewness' in stats['close']
        assert 'kurtosis' in stats['close']
        
        # Verificar valores razoáveis
        assert stats['close']['count'] > 0
        assert stats['close']['std'] > 0
    
    def test_descriptive_statistics_empty_data(self):
        """Teste com dados vazios"""
        analytics = AdvancedAnalytics()
        empty_data = pd.DataFrame()
        stats = analytics.descriptive_statistics(empty_data)
        
        assert isinstance(stats, dict)
        assert len(stats) == 0
    
    def test_correlation_analysis(self, sample_data):
        """Teste de análise de correlação"""
        analytics = AdvancedAnalytics()
        corr_data = sample_data[['close', 'volume', 'returns']]
        corr_analysis = analytics.correlation_analysis(corr_data)
        
        assert isinstance(corr_analysis, dict)
        assert 'pearson_matrix' in corr_analysis
        assert 'spearman_matrix' in corr_analysis
        assert 'kendall_matrix' in corr_analysis
        assert 'significant_correlations' in corr_analysis
        
        # Verificar matriz de correlação
        pearson_matrix = corr_analysis['pearson_matrix']
        assert pearson_matrix.shape == (3, 3)
        assert all(np.diag(pearson_matrix.values) == 1.0)  # Diagonal deve ser 1
    
    def test_time_series_analysis(self, returns_data):
        """Teste de análise de séries temporais"""
        analytics = AdvancedAnalytics()
        ts_analysis = analytics.time_series_analysis(returns_data)
        
        assert isinstance(ts_analysis, dict)
        assert 'trend_analysis' in ts_analysis
        assert 'seasonality' in ts_analysis
        assert 'stationarity' in ts_analysis
        assert 'autocorrelation' in ts_analysis
        assert 'volatility_clustering' in ts_analysis
        
        # Verificar trend analysis
        trend = ts_analysis['trend_analysis']
        assert 'slope' in trend
        assert 'r_squared' in trend
        assert 'trend_direction' in trend
    
    def test_principal_component_analysis(self, sample_data):
        """Teste de PCA"""
        analytics = AdvancedAnalytics()
        numeric_data = sample_data[['close', 'volume', 'high', 'low']]
        pca_analysis = analytics.principal_component_analysis(numeric_data)
        
        assert isinstance(pca_analysis, dict)
        assert 'principal_components' in pca_analysis
        assert 'explained_variance_ratio' in pca_analysis
        assert 'components' in pca_analysis
        
        # Verificar dimensões
        pc_df = pca_analysis['principal_components']
        assert pc_df.shape[1] <= 4  # Máximo 4 componentes
        assert len(pca_analysis['explained_variance_ratio']) <= 4
    
    def test_cluster_analysis(self, sample_data):
        """Teste de clustering"""
        analytics = AdvancedAnalytics()
        cluster_data = sample_data[['returns', 'volume']]
        cluster_analysis = analytics.cluster_analysis(cluster_data)
        
        assert isinstance(cluster_analysis, dict)
        assert 'clustered_data' in cluster_analysis
        assert 'cluster_centers' in cluster_analysis
        assert 'cluster_stats' in cluster_analysis
        assert 'silhouette_score' in cluster_analysis
        
        # Verificar clusters
        clustered_data = cluster_analysis['clustered_data']
        assert 'cluster' in clustered_data.columns
        assert clustered_data['cluster'].nunique() == 3  # 3 clusters por padrão


class TestRiskAnalytics:
    """Testes para RiskAnalytics"""
    
    def test_init(self):
        """Teste de inicialização"""
        risk = RiskAnalytics()
        assert hasattr(risk, 'confidence_levels')
        assert 0.95 in risk.confidence_levels
    
    def test_calculate_var(self, returns_data):
        """Teste de cálculo de VaR"""
        risk = RiskAnalytics()
        
        # Teste VaR histórico
        var_hist = risk.calculate_var(returns_data, 0.95, 'historical')
        assert isinstance(var_hist, dict)
        assert 'var' in var_hist
        assert 'var_pct' in var_hist
        assert 'confidence_level' in var_hist
        assert var_hist['confidence_level'] == 0.95
        
        # Teste VaR paramétrico
        var_param = risk.calculate_var(returns_data, 0.95, 'parametric')
        assert isinstance(var_param, dict)
        assert 'var' in var_param
        assert var_param['method'] == 'parametric'
        
        # Teste VaR Monte Carlo
        var_mc = risk.calculate_var(returns_data, 0.95, 'monte_carlo')
        assert isinstance(var_mc, dict)
        assert 'var' in var_mc
        assert var_mc['method'] == 'monte_carlo'
    
    def test_calculate_var_invalid_method(self, returns_data):
        """Teste com método inválido"""
        risk = RiskAnalytics()
        
        with pytest.raises(ValueError):
            risk.calculate_var(returns_data, 0.95, 'invalid_method')
    
    def test_calculate_cvar(self, returns_data):
        """Teste de CVaR"""
        risk = RiskAnalytics()
        cvar = risk.calculate_cvar(returns_data, 0.95)
        
        assert isinstance(cvar, dict)
        assert 'cvar' in cvar
        assert 'cvar_pct' in cvar
        assert 'var' in cvar
        assert 'tail_expectation' in cvar
        assert 'tail_observations' in cvar
    
    def test_calculate_maximum_drawdown(self, sample_data):
        """Teste de Maximum Drawdown"""
        risk = RiskAnalytics()
        prices = sample_data['close']
        dd_analysis = risk.calculate_maximum_drawdown(prices)
        
        assert isinstance(dd_analysis, dict)
        assert 'max_drawdown' in dd_analysis
        assert 'max_drawdown_pct' in dd_analysis
        assert 'max_drawdown_date' in dd_analysis
        assert 'drawdown_duration_days' in dd_analysis
        assert 'underwater_duration' in dd_analysis
        
        # Drawdown deve ser negativo ou zero
        assert dd_analysis['max_drawdown'] <= 0
    
    def test_calculate_volatility_metrics(self, returns_data):
        """Teste de métricas de volatilidade"""
        risk = RiskAnalytics()
        vol_metrics = risk.calculate_volatility_metrics(returns_data)
        
        assert isinstance(vol_metrics, dict)
        assert 'volatility' in vol_metrics
        assert 'volatility_pct' in vol_metrics
        assert 'garch_volatility' in vol_metrics
        assert 'downside_deviation' in vol_metrics
        assert 'upside_deviation' in vol_metrics
        
        # Volatilidade deve ser positiva
        assert vol_metrics['volatility'] > 0
    
    def test_calculate_sharpe_ratio(self, returns_data):
        """Teste de Sharpe Ratio"""
        risk = RiskAnalytics()
        ratios = risk.calculate_sharpe_ratio(returns_data)
        
        assert isinstance(ratios, dict)
        assert 'sharpe_ratio' in ratios
        assert 'sortino_ratio' in ratios
        assert 'calmar_ratio' in ratios
        assert 'annual_return' in ratios
        assert 'annual_volatility' in ratios
    
    def test_monte_carlo_simulation(self, returns_data):
        """Teste de simulação Monte Carlo"""
        risk = RiskAnalytics()
        mc_results = risk.monte_carlo_simulation(returns_data, num_simulations=100, time_horizon=50)
        
        assert isinstance(mc_results, dict)
        assert 'num_simulations' in mc_results
        assert 'time_horizon_days' in mc_results
        assert 'expected_final_value' in mc_results
        assert 'loss_probability_pct' in mc_results
        assert 'simulation_paths' in mc_results
        assert 'final_values' in mc_results
        
        # Verificar dimensões
        assert mc_results['num_simulations'] == 100
        assert mc_results['time_horizon_days'] == 50
        assert len(mc_results['final_values']) == 100
    
    def test_stress_testing(self, returns_data):
        """Teste de stress testing"""
        risk = RiskAnalytics()
        stress_results = risk.stress_testing(returns_data, {})
        
        assert isinstance(stress_results, dict)
        assert len(stress_results) > 0  # Deve ter cenários padrão
        
        for scenario_name, results in stress_results.items():
            assert 'shock_magnitude' in results
            assert 'stressed_volatility' in results
            assert 'final_portfolio_value' in results


class TestBacktestingEngine:
    """Testes para BacktestingEngine"""
    
    def test_init(self):
        """Teste de inicialização"""
        engine = BacktestingEngine(initial_capital=10000, commission=0.001)
        assert engine.initial_capital == 10000
        assert engine.commission == 0.001
        assert engine.cash == 10000
    
    def test_add_data(self, sample_data):
        """Teste de adição de dados"""
        engine = BacktestingEngine()
        engine.add_data(sample_data, "BTCUSDT")
        
        assert hasattr(engine, 'data')
        assert hasattr(engine, 'symbol')
        assert engine.symbol == "BTCUSDT"
        assert len(engine.data) > 0
    
    def test_add_data_invalid_columns(self):
        """Teste com colunas inválidas"""
        engine = BacktestingEngine()
        invalid_data = pd.DataFrame({'price': [100, 101, 102]})
        
        with pytest.raises(ValueError):
            engine.add_data(invalid_data, "BTCUSDT")
    
    def test_place_order_buy(self, sample_data):
        """Teste de ordem de compra"""
        engine = BacktestingEngine(initial_capital=10000)
        engine.add_data(sample_data, "BTCUSDT")
        engine.current_timestamp = sample_data.index[0]
        
        # Ordem de compra
        success = engine.place_order(OrderType.BUY, 1.0)
        assert success
        assert len(engine.trades) == 1
        assert engine.cash < 10000  # Cash deve ter diminuído
    
    def test_place_order_sell_without_position(self, sample_data):
        """Teste de venda sem posição"""
        engine = BacktestingEngine()
        engine.add_data(sample_data, "BTCUSDT")
        engine.current_timestamp = sample_data.index[0]
        
        # Tentar vender sem posição
        success = engine.place_order(OrderType.SELL, 1.0)
        assert not success  # Deve falhar
        assert len(engine.trades) == 0
    
    def test_place_order_insufficient_cash(self, sample_data):
        """Teste com cash insuficiente"""
        engine = BacktestingEngine(initial_capital=100)  # Capital baixo
        engine.add_data(sample_data, "BTCUSDT")
        engine.current_timestamp = sample_data.index[0]
        
        current_price = sample_data.loc[sample_data.index[0], 'close']
        large_quantity = 10.0  # Quantidade que excede o capital
        
        success = engine.place_order(OrderType.BUY, large_quantity)
        assert not success  # Deve falhar por falta de capital
    
    def test_run_backtest_simple_strategy(self, sample_data):
        """Teste de backtest com estratégia simples"""
        engine = BacktestingEngine(initial_capital=10000)
        engine.add_data(sample_data, "BTCUSDT")
        
        results = engine.run_backtest(simple_ma_strategy, short_window=5, long_window=10)
        
        assert isinstance(results, dict)
        assert 'initial_capital' in results
        assert 'final_value' in results
        assert 'total_return_pct' in results
        assert 'num_trades' in results
        assert 'portfolio_history' in results
        
        assert results['initial_capital'] == 10000
    
    def test_get_portfolio_value(self, sample_data):
        """Teste de cálculo do valor do portfolio"""
        engine = BacktestingEngine(initial_capital=10000)
        engine.add_data(sample_data, "BTCUSDT")
        engine.current_timestamp = sample_data.index[0]
        
        # Valor inicial deve ser igual ao cash
        initial_value = engine.get_portfolio_value()
        assert initial_value == 10000
        
        # Comprar e verificar valor
        engine.place_order(OrderType.BUY, 1.0)
        portfolio_value = engine.get_portfolio_value()
        assert portfolio_value != 10000  # Deve ter mudado


class TestMLModels:
    """Testes para MLModels"""
    
    def test_init(self):
        """Teste de inicialização"""
        ml_models = MLModels()
        assert hasattr(ml_models, 'models')
        assert hasattr(ml_models, 'scalers')
        assert hasattr(ml_models, 'available_models')
        assert 'random_forest' in ml_models.available_models
    
    def test_prepare_features(self, sample_data):
        """Teste de preparação de features"""
        ml_models = MLModels()
        X, y = ml_models.prepare_features(
            sample_data, 
            target_column='close',
            feature_columns=['close', 'volume'],
            lag_features=3
        )
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert len(X) > 0
        
        # Verificar se features de lag foram criadas
        feature_names = X.columns.tolist()
        assert any('lag' in name for name in feature_names)
        assert any('ma' in name for name in feature_names)  # Moving averages
    
    def test_train_model(self, sample_data):
        """Teste de treinamento de modelo"""
        ml_models = MLModels()
        X, y = ml_models.prepare_features(sample_data, 'close', lag_features=2)
        
        performance = ml_models.train_model(
            X, y,
            model_name='linear_regression',
            hyperparameter_tuning=False
        )
        
        assert isinstance(performance, dict)
        assert 'model_id' in performance
        assert 'model_name' in performance
        assert 'metrics' in performance
        assert 'train' in performance['metrics']
        assert 'test' in performance['metrics']
        
        # Verificar métricas
        train_metrics = performance['metrics']['train']
        assert 'rmse' in train_metrics
        assert 'r2' in train_metrics
        assert train_metrics['rmse'] > 0
    
    def test_predict(self, sample_data):
        """Teste de predição"""
        ml_models = MLModels()
        X, y = ml_models.prepare_features(sample_data, 'close', lag_features=2)
        
        # Treinar modelo
        performance = ml_models.train_model(X, y, 'linear_regression', hyperparameter_tuning=False)
        model_id = performance['model_id']
        
        # Fazer predições
        predictions = ml_models.predict(model_id, X.head(5))
        
        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == 5
        assert all(np.isfinite(predictions))  # Verificar se não há NaN/inf
    
    def test_predict_nonexistent_model(self, sample_data):
        """Teste de predição com modelo inexistente"""
        ml_models = MLModels()
        X, y = ml_models.prepare_features(sample_data, 'close', lag_features=2)
        
        with pytest.raises(ValueError):
            ml_models.predict('nonexistent_model', X.head(5))
    
    def test_compare_models(self, sample_data):
        """Teste de comparação de modelos"""
        ml_models = MLModels()
        X, y = ml_models.prepare_features(sample_data, 'close', lag_features=2)
        
        comparison = ml_models.compare_models(
            X, y, 
            models_to_compare=['linear_regression', 'ridge']
        )
        
        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 2
        assert 'model' in comparison.columns
        assert 'test_rmse' in comparison.columns
        assert 'test_r2' in comparison.columns


class TestReportGenerator:
    """Testes para ReportGenerator"""
    
    def test_init(self):
        """Teste de inicialização"""
        report_gen = ReportGenerator()
        assert hasattr(report_gen, 'output_dir')
        assert hasattr(report_gen, 'advanced_analytics')
        assert hasattr(report_gen, 'risk_analytics')
    
    def test_generate_comprehensive_report(self, sample_data):
        """Teste de geração de relatório"""
        report_gen = ReportGenerator()
        
        report_info = report_gen.generate_comprehensive_report(
            data=sample_data,
            returns_column='returns',
            price_column='close',
            title='Test Report',
            format_type='json'  # JSON para testes
        )
        
        assert isinstance(report_info, dict)
        assert 'report_path' in report_info
        assert 'report_data' in report_info
        assert 'timestamp' in report_info
        assert 'format' in report_info
        
        # Verificar estrutura do relatório
        report_data = report_info['report_data']
        assert 'metadata' in report_data
        assert 'executive_summary' in report_data
        assert 'risk_analytics' in report_data
        assert 'recommendations' in report_data
    
    def test_generate_report_invalid_format(self, sample_data):
        """Teste com formato inválido"""
        report_gen = ReportGenerator()
        
        with pytest.raises(ValueError):
            report_gen.generate_comprehensive_report(
                data=sample_data,
                format_type='invalid_format'
            )
    
    def test_generate_report_no_data(self):
        """Teste com dados vazios"""
        report_gen = ReportGenerator()
        empty_data = pd.DataFrame()
        
        with pytest.raises(ValueError):
            report_gen.generate_comprehensive_report(
                data=empty_data,
                returns_column='returns',
                price_column='close'
            )


class TestIntegration:
    """Testes de integração entre módulos"""
    
    def test_full_analytics_pipeline(self, sample_data):
        """Teste do pipeline completo de analytics"""
        # 1. Advanced Analytics
        analytics = AdvancedAnalytics()
        stats = analytics.descriptive_statistics(sample_data)
        assert len(stats) > 0
        
        # 2. Risk Analytics
        risk = RiskAnalytics()
        returns = sample_data['returns'].dropna()
        var_analysis = risk.calculate_var(returns, 0.95)
        assert 'var' in var_analysis
        
        # 3. Backtesting
        engine = BacktestingEngine(initial_capital=10000)
        engine.add_data(sample_data, "BTCUSDT")
        backtest_results = engine.run_backtest(simple_ma_strategy, short_window=5, long_window=10)
        assert 'total_return_pct' in backtest_results
        
        # 4. Machine Learning
        ml_models = MLModels()
        X, y = ml_models.prepare_features(sample_data, 'close', lag_features=2)
        model_performance = ml_models.train_model(X, y, 'linear_regression', hyperparameter_tuning=False)
        assert 'model_id' in model_performance
        
        # 5. Report Generation
        report_gen = ReportGenerator()
        report = report_gen.generate_comprehensive_report(
            data=sample_data,
            returns_column='returns',
            price_column='close',
            format_type='json'
        )
        assert 'report_data' in report
    
    def test_data_flow_consistency(self, sample_data):
        """Teste de consistência no fluxo de dados"""
        # Verificar se os dados passam consistentemente entre módulos
        
        # Preparar dados
        returns = sample_data['returns'].dropna()
        prices = sample_data['close']
        
        # Risk Analytics
        risk = RiskAnalytics()
        var_result = risk.calculate_var(returns, 0.95)
        dd_result = risk.calculate_maximum_drawdown(prices)
        
        # Advanced Analytics
        analytics = AdvancedAnalytics()
        ts_result = analytics.time_series_analysis(returns)
        
        # Verificar consistência de dados
        assert len(returns) > 0
        assert not returns.isna().all()
        assert 'var' in var_result
        assert 'max_drawdown' in dd_result
        assert 'trend_analysis' in ts_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
