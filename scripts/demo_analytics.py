#!/usr/bin/env python3
"""
Demo Analytics - Script de demonstração do módulo de analytics
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analytics import (
    AdvancedAnalytics,
    MLModels,
    BacktestingEngine,
    RiskAnalytics,
    ReportGenerator
)
from analytics.backtesting_engine import simple_ma_strategy, rsi_strategy


def generate_sample_data(days=365, symbol="BTCUSDT"):
    """
    Gera dados de exemplo para demonstração
    """
    print(f"Gerando dados de exemplo para {days} dias...")
    
    # Configurar seed para resultados reproduzíveis
    np.random.seed(42)
    
    # Gerar datas
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Gerar preços usando random walk com drift
    initial_price = 30000  # Preço inicial do Bitcoin
    drift = 0.0005  # 0.05% drift diário
    volatility = 0.03  # 3% volatilidade diária
    
    # Retornos log-normais
    returns = np.random.normal(drift, volatility, days)
    log_prices = np.cumsum(returns)
    prices = initial_price * np.exp(log_prices)
    
    # Gerar dados OHLCV
    data = pd.DataFrame(index=dates)
    data['close'] = prices
    data['open'] = data['close'].shift(1) * (1 + np.random.normal(0, 0.001, days))
    data['high'] = np.maximum(data['open'], data['close']) * (1 + np.abs(np.random.normal(0, 0.01, days)))
    data['low'] = np.minimum(data['open'], data['close']) * (1 - np.abs(np.random.normal(0, 0.01, days)))
    data['volume'] = np.random.lognormal(15, 0.5, days)  # Volume log-normal
    data['returns'] = data['close'].pct_change()
    
    # Remover valores NaN
    data = data.dropna()
    
    print(f"Dados gerados: {len(data)} registros de {data.index[0]} a {data.index[-1]}")
    return data


def demo_advanced_analytics():
    """
    Demonstração do módulo de Advanced Analytics
    """
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO: ADVANCED ANALYTICS")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(500)
    
    # Inicializar analytics
    analytics = AdvancedAnalytics()
    
    # 1. Estatísticas Descritivas
    print("\n1. Estatísticas Descritivas:")
    stats = analytics.descriptive_statistics(data)
    
    for column, column_stats in stats.items():
        if column in ['close', 'returns', 'volume']:
            print(f"\n{column.upper()}:")
            print(f"  Média: {column_stats['mean']:.4f}")
            print(f"  Desvio Padrão: {column_stats['std']:.4f}")
            print(f"  Skewness: {column_stats['skewness']:.4f}")
            print(f"  Kurtosis: {column_stats['kurtosis']:.4f}")
            
            if 'jarque_bera' in column_stats and column_stats['jarque_bera']:
                jb = column_stats['jarque_bera']
                print(f"  Teste Jarque-Bera: {'Normal' if jb['is_normal'] else 'Não Normal'} (p={jb['p_value']:.4f})")
    
    # 2. Análise de Correlação
    print("\n2. Análise de Correlação:")
    corr_analysis = analytics.correlation_analysis(data[['close', 'volume', 'returns']])
    
    print(f"Correlações significativas encontradas: {len(corr_analysis['significant_correlations'])}")
    for corr in corr_analysis['significant_correlations']:
        pair, pearson, strength = corr['pair'], corr['pearson'], corr['strength']
        print(f"  {pair[0]} vs {pair[1]}: {pearson:.4f} ({strength})")
    
    # 3. Análise de Séries Temporais
    print("\n3. Análise de Séries Temporais (Retornos):")
    ts_analysis = analytics.time_series_analysis(data['returns'])
    
    trend = ts_analysis['trend_analysis']
    print(f"  Tendência: {trend['trend_direction']} (R²={trend['r_squared']:.4f})")
    print(f"  Estacionariedade: {'Sim' if ts_analysis['stationarity']['is_stationary'] else 'Não'}")
    print(f"  Autocorrelações significativas: {len(ts_analysis['autocorrelation']['significant_lags'])}")
    
    # 4. PCA
    print("\n4. Análise de Componentes Principais:")
    pca_analysis = analytics.principal_component_analysis(data[['close', 'volume', 'high', 'low']])
    
    if pca_analysis:
        explained_var = pca_analysis['explained_variance_ratio']
        print(f"  Variância explicada pelos componentes: {explained_var[:3]}")
        print(f"  Componentes para 95% da variância: {pca_analysis['n_components_95_variance']}")
    
    # 5. Clustering
    print("\n5. Análise de Clustering:")
    cluster_analysis = analytics.cluster_analysis(data[['returns', 'volume']])
    
    if cluster_analysis:
        print(f"  Silhouette Score: {cluster_analysis['silhouette_score']:.4f}")
        for cluster_id, stats in cluster_analysis['cluster_stats'].items():
            print(f"  {cluster_id}: {stats['size']} observações ({stats['percentage']:.1f}%)")


def demo_risk_analytics():
    """
    Demonstração do módulo de Risk Analytics
    """
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO: RISK ANALYTICS")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(365)
    returns = data['returns'].dropna()
    prices = data['close']
    
    # Inicializar risk analytics
    risk = RiskAnalytics()
    
    # 1. Value at Risk (VaR)
    print("\n1. Value at Risk (VaR):")
    confidence_levels = [0.90, 0.95, 0.99]
    
    for confidence in confidence_levels:
        var_hist = risk.calculate_var(returns, confidence, 'historical')
        var_param = risk.calculate_var(returns, confidence, 'parametric')
        
        print(f"  VaR {int(confidence*100)}%:")
        print(f"    Histórico: {var_hist['var_pct']:.2f}%")
        print(f"    Paramétrico: {var_param['var_pct']:.2f}%")
    
    # 2. Conditional VaR (CVaR)
    print("\n2. Conditional Value at Risk (CVaR):")
    for confidence in confidence_levels:
        cvar = risk.calculate_cvar(returns, confidence)
        print(f"  CVaR {int(confidence*100)}%: {cvar['cvar_pct']:.2f}%")
    
    # 3. Maximum Drawdown
    print("\n3. Maximum Drawdown:")
    dd_analysis = risk.calculate_maximum_drawdown(prices)
    
    print(f"  Drawdown Máximo: {dd_analysis['max_drawdown_pct']:.2f}%")
    print(f"  Data do Drawdown: {dd_analysis['max_drawdown_date']}")
    print(f"  Duração: {dd_analysis['drawdown_duration_days']} dias")
    print(f"  Tempo submerso: {dd_analysis['underwater_percentage']:.1f}%")
    
    # 4. Métricas de Volatilidade
    print("\n4. Métricas de Volatilidade:")
    vol_metrics = risk.calculate_volatility_metrics(returns)
    
    print(f"  Volatilidade Anualizada: {vol_metrics['volatility_pct']:.2f}%")
    print(f"  Volatilidade GARCH: {vol_metrics['garch_volatility']*100:.2f}%")
    print(f"  Downside Deviation: {vol_metrics['downside_deviation']*100:.2f}%")
    print(f"  Skewness: {vol_metrics['volatility_skew']:.4f}")
    print(f"  Kurtosis: {vol_metrics['volatility_kurtosis']:.4f}")
    
    # 5. Sharpe e outros ratios
    print("\n5. Ratios de Performance:")
    ratios = risk.calculate_sharpe_ratio(returns)
    
    print(f"  Sharpe Ratio: {ratios['sharpe_ratio']:.4f}")
    print(f"  Sortino Ratio: {ratios['sortino_ratio']:.4f}")
    print(f"  Calmar Ratio: {ratios['calmar_ratio']:.4f}")
    print(f"  Retorno Anualizado: {ratios['annual_return']*100:.2f}%")
    
    # 6. Stress Testing
    print("\n6. Stress Testing:")
    stress_results = risk.stress_testing(returns, {})
    
    for scenario, results in stress_results.items():
        print(f"  {scenario.replace('_', ' ').title()}:")
        print(f"    Perda Total: {results['total_loss']:.2f}%")
        print(f"    Volatilidade Estressada: {results['stressed_volatility']*100:.2f}%")
    
    # 7. Monte Carlo
    print("\n7. Simulação Monte Carlo (100 simulações):")
    mc_results = risk.monte_carlo_simulation(returns, num_simulations=100, time_horizon=252)
    
    print(f"  Valor Final Esperado: {mc_results['expected_final_value']:.4f}")
    print(f"  Retorno Esperado: {mc_results['expected_return_pct']:.2f}%")
    print(f"  Probabilidade de Perda: {mc_results['loss_probability_pct']:.1f}%")
    print(f"  VaR 95% (1 ano): {mc_results['var_95_pct']:.2f}%")


def demo_backtesting():
    """
    Demonstração do módulo de Backtesting
    """
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO: BACKTESTING ENGINE")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(365)
    
    # Inicializar engine
    engine = BacktestingEngine(initial_capital=10000, commission=0.001)
    engine.add_data(data, "BTCUSDT")
    
    # 1. Backtest com estratégia de média móvel
    print("\n1. Backtesting - Estratégia Média Móvel Simples:")
    results_ma = engine.run_backtest(
        strategy=simple_ma_strategy,
        short_window=10,
        long_window=30
    )
    
    print(f"  Capital Inicial: ${results_ma['initial_capital']:,.2f}")
    print(f"  Valor Final: ${results_ma['final_value']:,.2f}")
    print(f"  Retorno Total: {results_ma['total_return_pct']:.2f}%")
    print(f"  Retorno Anualizado: {results_ma['annualized_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {results_ma['sharpe_ratio']:.4f}")
    print(f"  Drawdown Máximo: {results_ma['max_drawdown_pct']:.2f}%")
    print(f"  Número de Trades: {results_ma['num_trades']}")
    print(f"  Taxa de Acerto: {results_ma['win_rate_pct']:.1f}%")
    print(f"  Profit Factor: {results_ma['profit_factor']:.2f}")
    
    # 2. Backtest com estratégia RSI
    print("\n2. Backtesting - Estratégia RSI:")
    engine.reset()  # Reset para novo backtest
    engine.add_data(data, "BTCUSDT")
    
    results_rsi = engine.run_backtest(
        strategy=rsi_strategy,
        rsi_period=14,
        oversold=30,
        overbought=70
    )
    
    print(f"  Capital Inicial: ${results_rsi['initial_capital']:,.2f}")
    print(f"  Valor Final: ${results_rsi['final_value']:,.2f}")
    print(f"  Retorno Total: {results_rsi['total_return_pct']:.2f}%")
    print(f"  Retorno Anualizado: {results_rsi['annualized_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {results_rsi['sharpe_ratio']:.4f}")
    print(f"  Drawdown Máximo: {results_rsi['max_drawdown_pct']:.2f}%")
    print(f"  Número de Trades: {results_rsi['num_trades']}")
    print(f"  Taxa de Acerto: {results_rsi['win_rate_pct']:.1f}%")
    print(f"  Profit Factor: {results_rsi['profit_factor']:.2f}")
    
    # 3. Comparação de estratégias
    print("\n3. Comparação de Estratégias:")
    print(f"  Média Móvel vs RSI:")
    print(f"    Retorno: {results_ma['total_return_pct']:.2f}% vs {results_rsi['total_return_pct']:.2f}%")
    print(f"    Sharpe: {results_ma['sharpe_ratio']:.4f} vs {results_rsi['sharpe_ratio']:.4f}")
    print(f"    Drawdown: {results_ma['max_drawdown_pct']:.2f}% vs {results_rsi['max_drawdown_pct']:.2f}%")
    
    return results_ma, results_rsi


def demo_ml_models():
    """
    Demonstração do módulo de ML Models
    """
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO: MACHINE LEARNING MODELS")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(500)
    
    # Inicializar ML models
    ml_models = MLModels()
    
    # 1. Preparar features
    print("\n1. Preparação de Features:")
    X, y = ml_models.prepare_features(
        data, 
        target_column='close',
        feature_columns=['close', 'volume', 'high', 'low'],
        lag_features=5
    )
    
    print(f"  Shape das features: {X.shape}")
    print(f"  Shape do target: {y.shape}")
    print(f"  Colunas de features: {X.columns.tolist()[:10]}...")  # Mostrar apenas 10 primeiras
    
    # 2. Comparar modelos
    print("\n2. Comparação de Modelos:")
    comparison = ml_models.compare_models(
        X, y, 
        models_to_compare=['linear_regression', 'ridge', 'random_forest']
    )
    
    print("  Ranking por RMSE de teste:")
    for idx, row in comparison.iterrows():
        print(f"    {idx+1}. {row['model']}: RMSE={row['test_rmse']:.2f}, R²={row['test_r2']:.4f}")
    
    # 3. Treinar melhor modelo
    print("\n3. Treinamento do Melhor Modelo:")
    best_model = comparison.iloc[0]['model']
    
    performance = ml_models.train_model(
        X, y,
        model_name=best_model,
        hyperparameter_tuning=False  # Desabilitar para demo rápida
    )
    
    print(f"  Modelo: {performance['model_name']}")
    print(f"  Model ID: {performance['model_id']}")
    print(f"  RMSE Treino: {performance['metrics']['train']['rmse']:.2f}")
    print(f"  RMSE Teste: {performance['metrics']['test']['rmse']:.2f}")
    print(f"  R² Treino: {performance['metrics']['train']['r2']:.4f}")
    print(f"  R² Teste: {performance['metrics']['test']['r2']:.4f}")
    print(f"  Features Selecionadas: {len(performance['selected_features'])}")
    
    # 4. Fazer predições
    print("\n4. Predições:")
    predictions = ml_models.predict(performance['model_id'], X.tail(10))
    actual_values = y.tail(10).values
    
    print("  Últimas 10 predições vs valores reais:")
    for i in range(len(predictions)):
        error = abs(predictions[i] - actual_values[i]) / actual_values[i] * 100
        print(f"    Pred: {predictions[i]:.2f}, Real: {actual_values[i]:.2f}, Erro: {error:.1f}%")
    
    # 5. Predições com confiança
    print("\n5. Predições com Intervalo de Confiança:")
    pred_with_conf = ml_models.predict_with_confidence(
        performance['model_id'], 
        X.tail(5),
        confidence_level=0.95
    )
    
    for i in range(len(pred_with_conf['predictions'])):
        pred = pred_with_conf['predictions'][i]
        lower = pred_with_conf['lower_bound'][i]
        upper = pred_with_conf['upper_bound'][i]
        print(f"    Predição: {pred:.2f} [{lower:.2f}, {upper:.2f}]")
    
    return performance


def demo_report_generator():
    """
    Demonstração do gerador de relatórios
    """
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO: REPORT GENERATOR")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(365)
    
    # Inicializar gerador
    report_gen = ReportGenerator()
    
    # 1. Gerar relatório HTML
    print("\n1. Gerando Relatório HTML...")
    html_report = report_gen.generate_comprehensive_report(
        data=data,
        returns_column='returns',
        price_column='close',
        title='Relatório de Demonstração - Bitcoin',
        format_type='html'
    )
    
    print(f"  Relatório HTML gerado: {html_report['report_path']}")
    print(f"  Timestamp: {html_report['timestamp']}")
    
    # 2. Gerar relatório JSON
    print("\n2. Gerando Relatório JSON...")
    json_report = report_gen.generate_comprehensive_report(
        data=data,
        returns_column='returns',
        price_column='close',
        title='Relatório de Demonstração - Bitcoin',
        format_type='json'
    )
    
    print(f"  Relatório JSON gerado: {json_report['report_path']}")
    
    # 3. Gerar relatório Markdown
    print("\n3. Gerando Relatório Markdown...")
    md_report = report_gen.generate_comprehensive_report(
        data=data,
        returns_column='returns',
        price_column='close',
        title='Relatório de Demonstração - Bitcoin',
        format_type='markdown'
    )
    
    print(f"  Relatório Markdown gerado: {md_report['report_path']}")
    
    # 4. Mostrar resumo executivo
    print("\n4. Resumo Executivo do Relatório:")
    executive_summary = html_report['report_data']['executive_summary']
    
    print(f"  Retorno do Período: {executive_summary['period_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {executive_summary['sharpe_ratio']:.4f}")
    print(f"  Score de Performance: {executive_summary['performance_score']}/100")
    print(f"  Nível de Risco: {executive_summary['risk_level']}")
    print(f"  Classificação de Retorno: {executive_summary['return_classification']}")
    
    print("\n  Insights Principais:")
    for insight in executive_summary['key_insights']:
        print(f"    • {insight}")
    
    return html_report, json_report, md_report


def create_visualizations():
    """
    Criar visualizações dos resultados
    """
    print("\n" + "="*50)
    print("CRIANDO VISUALIZAÇÕES")
    print("="*50)
    
    # Gerar dados
    data = generate_sample_data(365)
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Dashboard de Analytics - Bitcoin', fontsize=16)
    
    # 1. Evolução do preço
    axes[0, 0].plot(data.index, data['close'], color='blue', linewidth=1)
    axes[0, 0].set_title('Evolução do Preço')
    axes[0, 0].set_ylabel('Preço (USD)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Distribuição de retornos
    axes[0, 1].hist(data['returns'].dropna(), bins=50, alpha=0.7, color='green', edgecolor='black')
    axes[0, 1].set_title('Distribuição de Retornos Diários')
    axes[0, 1].set_xlabel('Retorno')
    axes[0, 1].set_ylabel('Frequência')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Volatilidade rolling
    rolling_vol = data['returns'].rolling(30).std() * np.sqrt(252) * 100
    axes[1, 0].plot(data.index, rolling_vol, color='red', linewidth=1)
    axes[1, 0].set_title('Volatilidade Rolling (30 dias)')
    axes[1, 0].set_ylabel('Volatilidade (%)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Drawdown
    cumulative = (1 + data['returns']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max * 100
    
    axes[1, 1].fill_between(data.index, drawdown, 0, alpha=0.3, color='red')
    axes[1, 1].plot(data.index, drawdown, color='darkred', linewidth=1)
    axes[1, 1].set_title('Drawdown')
    axes[1, 1].set_ylabel('Drawdown (%)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Salvar visualização
    viz_path = 'reports/analytics_dashboard.png'
    os.makedirs('reports', exist_ok=True)
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    print(f"  Dashboard salvo: {viz_path}")
    
    # Criar visualização de correlação
    plt.figure(figsize=(10, 8))
    correlation_matrix = data[['close', 'volume', 'returns']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='RdBu_r', center=0, 
                square=True, linewidths=0.5)
    plt.title('Matriz de Correlação')
    
    corr_path = 'reports/correlation_matrix.png'
    plt.savefig(corr_path, dpi=300, bbox_inches='tight')
    print(f"  Matriz de correlação salva: {corr_path}")
    
    plt.show()


def main():
    """
    Função principal do demo
    """
    print("🚀 DEMONSTRAÇÃO COMPLETA DO MÓDULO DE ANALYTICS")
    print("="*60)
    
    try:
        # Executar todas as demonstrações
        demo_advanced_analytics()
        demo_risk_analytics()
        ma_results, rsi_results = demo_backtesting()
        ml_performance = demo_ml_models()
        html_report, json_report, md_report = demo_report_generator()
        
        # Criar visualizações
        create_visualizations()
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO DA DEMONSTRAÇÃO")
        print("="*60)
        
        print(f"\n✅ Advanced Analytics: Análises estatísticas completas")
        print(f"✅ Risk Analytics: VaR, CVaR, Drawdown, Stress Testing")
        print(f"✅ Backtesting: Estratégias MA e RSI testadas")
        print(f"✅ Machine Learning: {ml_performance['model_name']} treinado")
        print(f"✅ Relatórios: HTML, JSON e Markdown gerados")
        print(f"✅ Visualizações: Dashboard e gráficos criados")
        
        print(f"\n📁 Arquivos gerados:")
        print(f"  • {html_report['report_path']}")
        print(f"  • {json_report['report_path']}")
        print(f"  • {md_report['report_path']}")
        print(f"  • reports/analytics_dashboard.png")
        print(f"  • reports/correlation_matrix.png")
        
        print(f"\n🎯 Sistema de Analytics totalmente funcional!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
