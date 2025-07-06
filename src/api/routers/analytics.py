"""
Analytics API Router - Endpoints para módulo de analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import json
from pathlib import Path

from ...analytics import (
    AdvancedAnalytics, 
    MLModels, 
    BacktestingEngine, 
    RiskAnalytics, 
    ReportGenerator
)
from ...core.database import get_db_connection
from ...core.security import get_current_user
from ...schemas.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Instâncias dos módulos de analytics
advanced_analytics = AdvancedAnalytics()
ml_models = MLModels()
risk_analytics = RiskAnalytics()
report_generator = ReportGenerator()


@router.post("/descriptive-statistics")
async def calculate_descriptive_statistics(
    data_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Calcula estatísticas descritivas para dados
    """
    try:
        # Aqui você obteria os dados baseado na configuração
        # Por exemplo, de um banco de dados ou API externa
        data = await _get_data_from_config(data_config)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Calcular estatísticas
        stats = advanced_analytics.descriptive_statistics(data)
        
        return {
            "status": "success",
            "data": stats,
            "metadata": {
                "rows": len(data),
                "columns": len(data.columns),
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@router.post("/correlation-analysis")
async def calculate_correlation_analysis(
    data_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Análise de correlação avançada
    """
    try:
        data = await _get_data_from_config(data_config)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        correlation_analysis = advanced_analytics.correlation_analysis(data)
        
        # Converter DataFrames para dict para serialização JSON
        if 'pearson_matrix' in correlation_analysis:
            correlation_analysis['pearson_matrix'] = correlation_analysis['pearson_matrix'].to_dict()
        if 'spearman_matrix' in correlation_analysis:
            correlation_analysis['spearman_matrix'] = correlation_analysis['spearman_matrix'].to_dict()
        if 'kendall_matrix' in correlation_analysis:
            correlation_analysis['kendall_matrix'] = correlation_analysis['kendall_matrix'].to_dict()
        
        return {
            "status": "success",
            "data": correlation_analysis,
            "metadata": {
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de correlação: {str(e)}")


@router.post("/risk-analysis")
async def calculate_risk_analysis(
    data_config: Dict[str, Any],
    confidence_levels: List[float] = Query([0.95], description="Níveis de confiança para VaR"),
    current_user: User = Depends(get_current_user)
):
    """
    Análise completa de risco
    """
    try:
        data = await _get_data_from_config(data_config)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Identificar coluna de retornos
        returns_column = data_config.get('returns_column', 'returns')
        if returns_column not in data.columns:
            # Tentar calcular retornos de preços
            price_column = data_config.get('price_column', 'close')
            if price_column in data.columns:
                returns = data[price_column].pct_change().dropna()
            else:
                raise HTTPException(status_code=400, detail="Coluna de retornos não encontrada")
        else:
            returns = data[returns_column].dropna()
        
        # Calcular métricas de risco
        risk_metrics = {}
        
        # VaR para diferentes níveis
        for confidence in confidence_levels:
            for method in ['historical', 'parametric']:
                key = f"var_{method}_{int(confidence*100)}"
                risk_metrics[key] = risk_analytics.calculate_var(returns, confidence, method)
        
        # CVaR
        for confidence in confidence_levels:
            key = f"cvar_{int(confidence*100)}"
            risk_metrics[key] = risk_analytics.calculate_cvar(returns, confidence)
        
        # Outras métricas
        risk_metrics['volatility'] = risk_analytics.calculate_volatility_metrics(returns)
        risk_metrics['sharpe_ratios'] = risk_analytics.calculate_sharpe_ratio(returns)
        
        # Maximum Drawdown se houver preços
        price_column = data_config.get('price_column', 'close')
        if price_column in data.columns:
            prices = data[price_column]
            risk_metrics['drawdown'] = risk_analytics.calculate_maximum_drawdown(prices)
            # Converter Series para dict
            if 'drawdown_series' in risk_metrics['drawdown']:
                risk_metrics['drawdown']['drawdown_series'] = risk_metrics['drawdown']['drawdown_series'].to_dict()
        
        return {
            "status": "success",
            "data": risk_metrics,
            "metadata": {
                "confidence_levels": confidence_levels,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de risco: {str(e)}")


@router.post("/backtest")
async def run_backtest(
    backtest_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Executa backtesting de estratégia
    """
    try:
        # Obter dados
        data = await _get_data_from_config(backtest_config.get('data_config', {}))
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Configurar engine de backtesting
        initial_capital = backtest_config.get('initial_capital', 10000)
        commission = backtest_config.get('commission', 0.001)
        
        engine = BacktestingEngine(initial_capital=initial_capital, commission=commission)
        engine.add_data(data, backtest_config.get('symbol', 'BTCUSDT'))
        
        # Definir estratégia (exemplo com média móvel)
        strategy_type = backtest_config.get('strategy', 'simple_ma')
        strategy_params = backtest_config.get('strategy_params', {})
        
        if strategy_type == 'simple_ma':
            from ...analytics.backtesting_engine import simple_ma_strategy
            strategy = simple_ma_strategy
        elif strategy_type == 'rsi':
            from ...analytics.backtesting_engine import rsi_strategy
            strategy = strategy
        else:
            raise HTTPException(status_code=400, detail=f"Estratégia {strategy_type} não suportada")
        
        # Executar backtest
        results = engine.run_backtest(
            strategy=strategy,
            start_date=backtest_config.get('start_date'),
            end_date=backtest_config.get('end_date'),
            **strategy_params
        )
        
        # Converter DataFrames e objetos não serializáveis
        serializable_results = _make_serializable(results)
        
        return {
            "status": "success",
            "data": serializable_results,
            "metadata": {
                "strategy": strategy_type,
                "parameters": strategy_params,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no backtesting: {str(e)}")


@router.post("/ml-models/train")
async def train_ml_model(
    training_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Treina modelo de Machine Learning
    """
    try:
        # Obter dados
        data = await _get_data_from_config(training_config.get('data_config', {}))
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Preparar features
        target_column = training_config.get('target_column', 'close')
        feature_columns = training_config.get('feature_columns')
        lag_features = training_config.get('lag_features', 5)
        
        X, y = ml_models.prepare_features(
            data, 
            target_column, 
            feature_columns, 
            lag_features
        )
        
        if len(X) == 0:
            raise HTTPException(status_code=400, detail="Não foi possível preparar features")
        
        # Configurações de treinamento
        model_name = training_config.get('model_name', 'random_forest')
        test_size = training_config.get('test_size', 0.2)
        cv_folds = training_config.get('cv_folds', 5)
        feature_selection = training_config.get('feature_selection', True)
        hyperparameter_tuning = training_config.get('hyperparameter_tuning', True)
        
        # Treinar modelo
        def train_model_task():
            performance = ml_models.train_model(
                X, y,
                model_name=model_name,
                test_size=test_size,
                cv_folds=cv_folds,
                feature_selection=feature_selection,
                hyperparameter_tuning=hyperparameter_tuning
            )
            return performance
        
        # Executar treinamento em background se for demorado
        if hyperparameter_tuning:
            background_tasks.add_task(train_model_task)
            return {
                "status": "training_started",
                "message": "Treinamento iniciado em background",
                "model_name": model_name
            }
        else:
            performance = train_model_task()
            
            # Converter objetos não serializáveis
            serializable_performance = _make_serializable(performance)
            
            return {
                "status": "success",
                "data": serializable_performance,
                "metadata": {
                    "generated_at": datetime.now().isoformat()
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no treinamento: {str(e)}")


@router.get("/ml-models/list")
async def list_ml_models(current_user: User = Depends(get_current_user)):
    """
    Lista modelos treinados
    """
    try:
        models_df = ml_models.list_models()
        
        if models_df.empty:
            return {
                "status": "success",
                "data": [],
                "message": "Nenhum modelo encontrado"
            }
        
        return {
            "status": "success",
            "data": models_df.to_dict('records'),
            "metadata": {
                "total_models": len(models_df),
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")


@router.post("/ml-models/{model_id}/predict")
async def predict_with_model(
    model_id: str,
    prediction_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Faz predições com modelo treinado
    """
    try:
        # Obter dados
        data = await _get_data_from_config(prediction_config.get('data_config', {}))
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Preparar features (deve ser igual ao treinamento)
        target_column = prediction_config.get('target_column', 'close')
        feature_columns = prediction_config.get('feature_columns')
        lag_features = prediction_config.get('lag_features', 5)
        
        X, _ = ml_models.prepare_features(
            data, 
            target_column, 
            feature_columns, 
            lag_features
        )
        
        # Fazer predições
        predictions = ml_models.predict(model_id, X)
        
        # Predições com intervalo de confiança se solicitado
        with_confidence = prediction_config.get('with_confidence', False)
        if with_confidence:
            confidence_level = prediction_config.get('confidence_level', 0.95)
            pred_results = ml_models.predict_with_confidence(model_id, X, confidence_level)
        else:
            pred_results = {
                'predictions': predictions.tolist()
            }
        
        return {
            "status": "success",
            "data": pred_results,
            "metadata": {
                "model_id": model_id,
                "num_predictions": len(predictions),
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")


@router.post("/reports/generate")
async def generate_comprehensive_report(
    report_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Gera relatório completo de analytics
    """
    try:
        # Obter dados
        data = await _get_data_from_config(report_config.get('data_config', {}))
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Configurações do relatório
        title = report_config.get('title', 'Relatório de Analytics')
        format_type = report_config.get('format', 'html')
        returns_column = report_config.get('returns_column', 'returns')
        price_column = report_config.get('price_column', 'close')
        
        # Gerar relatório
        def generate_report_task():
            return report_generator.generate_comprehensive_report(
                data=data,
                returns_column=returns_column,
                price_column=price_column,
                title=title,
                format_type=format_type
            )
        
        # Executar geração em background para relatórios grandes
        if len(data) > 1000:
            background_tasks.add_task(generate_report_task)
            return {
                "status": "report_generation_started",
                "message": "Geração de relatório iniciada em background",
                "title": title
            }
        else:
            report_info = generate_report_task()
            
            return {
                "status": "success",
                "data": {
                    "report_path": report_info['report_path'],
                    "format": report_info['format'],
                    "timestamp": report_info['timestamp']
                },
                "metadata": {
                    "title": title,
                    "generated_at": datetime.now().isoformat()
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geração do relatório: {str(e)}")


@router.get("/reports/{report_id}")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download de relatório gerado
    """
    try:
        # Verificar se o arquivo existe
        reports_dir = Path("reports")
        
        # Procurar arquivo com o ID
        report_files = list(reports_dir.glob(f"*{report_id}*"))
        
        if not report_files:
            raise HTTPException(status_code=404, detail="Relatório não encontrado")
        
        report_file = report_files[0]
        
        return FileResponse(
            path=str(report_file),
            filename=report_file.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no download: {str(e)}")


@router.post("/monte-carlo")
async def run_monte_carlo_simulation(
    simulation_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Executa simulação Monte Carlo
    """
    try:
        # Obter dados
        data = await _get_data_from_config(simulation_config.get('data_config', {}))
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Preparar retornos
        returns_column = simulation_config.get('returns_column', 'returns')
        if returns_column not in data.columns:
            price_column = simulation_config.get('price_column', 'close')
            if price_column in data.columns:
                returns = data[price_column].pct_change().dropna()
            else:
                raise HTTPException(status_code=400, detail="Coluna de retornos não encontrada")
        else:
            returns = data[returns_column].dropna()
        
        # Parâmetros da simulação
        num_simulations = simulation_config.get('num_simulations', 1000)
        time_horizon = simulation_config.get('time_horizon', 252)
        
        # Executar simulação
        results = risk_analytics.monte_carlo_simulation(
            returns,
            num_simulations=num_simulations,
            time_horizon=time_horizon
        )
        
        # Converter arrays numpy para listas para serialização
        serializable_results = _make_serializable(results)
        
        return {
            "status": "success",
            "data": serializable_results,
            "metadata": {
                "num_simulations": num_simulations,
                "time_horizon": time_horizon,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na simulação Monte Carlo: {str(e)}")


# Funções auxiliares
async def _get_data_from_config(data_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Obtém dados baseado na configuração
    """
    data_source = data_config.get('source', 'database')
    
    if data_source == 'database':
        # Obter dados do banco de dados
        table_name = data_config.get('table', 'trades')
        start_date = data_config.get('start_date')
        end_date = data_config.get('end_date')
        symbol = data_config.get('symbol')
        
        # Implementar query baseada nos parâmetros
        # Por exemplo:
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        
        if start_date:
            query += f" AND timestamp >= '{start_date}'"
        if end_date:
            query += f" AND timestamp <= '{end_date}'"
        if symbol:
            query += f" AND symbol = '{symbol}'"
        
        query += " ORDER BY timestamp"
        
        # Aqui você executaria a query no banco
        # Por enquanto, retornar DataFrame vazio
        return pd.DataFrame()
        
    elif data_source == 'csv':
        # Carregar de arquivo CSV
        file_path = data_config.get('file_path')
        if not file_path or not Path(file_path).exists():
            return pd.DataFrame()
        
        return pd.read_csv(file_path, parse_dates=['timestamp'], index_col='timestamp')
        
    elif data_source == 'sample':
        # Gerar dados de exemplo
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
        returns = np.diff(np.log(prices))
        
        return pd.DataFrame({
            'close': prices[1:],
            'returns': returns,
            'volume': np.random.normal(1000000, 200000, len(returns))
        }, index=dates[1:])
    
    return pd.DataFrame()


def _make_serializable(obj):
    """
    Torna objetos serializáveis para JSON
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    else:
        return obj
