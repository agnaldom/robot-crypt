"""
Machine Learning Models - Modelos preditivos treinados
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import warnings
import joblib
import os
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
from sklearn.neural_network import MLPRegressor
from sklearn.feature_selection import SelectKBest, f_regression, RFE

warnings.filterwarnings('ignore')


class MLModels:
    """
    Classe para modelos de Machine Learning preditivos
    """
    
    def __init__(self, models_dir: str = "models/"):
        self.models_dir = models_dir
        self.models = {}
        self.scalers = {}
        self.feature_selectors = {}
        self.model_performance = {}
        
        # Criar diretório de modelos se não existir
        os.makedirs(models_dir, exist_ok=True)
        
        # Modelos disponíveis
        self.available_models = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0),
            'elastic_net': ElasticNet(alpha=1.0, l1_ratio=0.5),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42),
            'svr': SVR(kernel='rbf'),
            'mlp': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
        }
    
    def prepare_features(self, data: pd.DataFrame, target_column: str, 
                        feature_columns: Optional[List[str]] = None,
                        lag_features: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara features para modelagem
        
        Args:
            data: DataFrame com dados
            target_column: Nome da coluna target
            feature_columns: Lista de colunas de features
            lag_features: Número de lags para criar
            
        Returns:
            Tuple com features e target
        """
        df = data.copy()
        
        # Selecionar colunas de features
        if feature_columns is None:
            # Selecionar apenas colunas numéricas, excluindo target
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_columns = [col for col in numeric_columns if col != target_column]
        
        # Criar features de lag
        for lag in range(1, lag_features + 1):
            for col in feature_columns:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        # Criar features de rolling statistics
        for window in [5, 10, 20]:
            for col in feature_columns:
                df[f'{col}_ma_{window}'] = df[col].rolling(window=window).mean()
                df[f'{col}_std_{window}'] = df[col].rolling(window=window).std()
                df[f'{col}_min_{window}'] = df[col].rolling(window=window).min()
                df[f'{col}_max_{window}'] = df[col].rolling(window=window).max()
        
        # Criar features de diferenças
        for col in feature_columns:
            df[f'{col}_diff_1'] = df[col].diff(1)
            df[f'{col}_diff_pct'] = df[col].pct_change()
        
        # Criar features de ratios
        if len(feature_columns) > 1:
            for i, col1 in enumerate(feature_columns):
                for col2 in feature_columns[i+1:]:
                    df[f'{col1}_{col2}_ratio'] = df[col1] / (df[col2] + 1e-8)
        
        # Remover NaN values
        df = df.dropna()
        
        # Separar features e target
        # Manter apenas colunas numéricas nas features finais
        feature_cols = [col for col in df.columns if col != target_column]
        numeric_feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        X = df[numeric_feature_cols]
        y = df[target_column]
        
        return X, y
    
    def train_model(self, X: pd.DataFrame, y: pd.Series, 
                   model_name: str = 'random_forest',
                   test_size: float = 0.2,
                   cv_folds: int = 5,
                   feature_selection: bool = True,
                   hyperparameter_tuning: bool = True) -> Dict[str, Any]:
        """
        Treina um modelo de ML
        
        Args:
            X: Features
            y: Target
            model_name: Nome do modelo
            test_size: Proporção do conjunto de teste
            cv_folds: Número de folds para cross-validation
            feature_selection: Se deve aplicar seleção de features
            hyperparameter_tuning: Se deve fazer tuning de hiperparâmetros
            
        Returns:
            Dict com resultados do treinamento
        """
        if model_name not in self.available_models:
            raise ValueError(f"Modelo {model_name} não disponível")
        
        # Split dos dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )
        
        # Scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Feature Selection
        if feature_selection:
            selector = SelectKBest(score_func=f_regression, k=min(20, X_train.shape[1]))
            X_train_selected = selector.fit_transform(X_train_scaled, y_train)
            X_test_selected = selector.transform(X_test_scaled)
            selected_features = X.columns[selector.get_support()].tolist()
        else:
            X_train_selected = X_train_scaled
            X_test_selected = X_test_scaled
            selected_features = X.columns.tolist()
            selector = None
        
        # Modelo base
        model = self.available_models[model_name]
        
        # Hyperparameter Tuning
        if hyperparameter_tuning:
            model = self._tune_hyperparameters(model, model_name, X_train_selected, y_train, cv_folds)
        
        # Treinar modelo final
        model.fit(X_train_selected, y_train)
        
        # Predições
        y_train_pred = model.predict(X_train_selected)
        y_test_pred = model.predict(X_test_selected)
        
        # Métricas
        metrics = {
            'train': self._calculate_metrics(y_train, y_train_pred),
            'test': self._calculate_metrics(y_test, y_test_pred)
        }
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_selected, y_train, 
                                   cv=cv_folds, scoring='neg_mean_squared_error')
        
        # Salvar modelo e componentes
        model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.models[model_id] = model
        self.scalers[model_id] = scaler
        if selector:
            self.feature_selectors[model_id] = selector
        
        # Performance do modelo
        performance = {
            'model_id': model_id,
            'model_name': model_name,
            'metrics': metrics,
            'cv_scores': {
                'mean': -cv_scores.mean(),
                'std': cv_scores.std(),
                'scores': -cv_scores
            },
            'selected_features': selected_features,
            'feature_importance': self._get_feature_importance(model, selected_features),
            'training_data_shape': X_train.shape,
            'test_data_shape': X_test.shape
        }
        
        self.model_performance[model_id] = performance
        
        # Salvar modelo
        self._save_model(model_id)
        
        return performance
    
    def _tune_hyperparameters(self, model, model_name: str, X: np.ndarray, y: np.ndarray, cv_folds: int):
        """Tuning de hiperparâmetros"""
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'ridge': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            'lasso': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            'elastic_net': {
                'alpha': [0.1, 1.0, 10.0],
                'l1_ratio': [0.1, 0.5, 0.9]
            },
            'svr': {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto', 0.001, 0.01]
            },
            'mlp': {
                'hidden_layer_sizes': [(50,), (100,), (100, 50)],
                'alpha': [0.0001, 0.001, 0.01]
            }
        }
        
        if model_name in param_grids:
            grid_search = GridSearchCV(
                model, param_grids[model_name], 
                cv=cv_folds, scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            grid_search.fit(X, y)
            return grid_search.best_estimator_
        
        return model
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calcula métricas de performance"""
        return {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
        }
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Optional[Dict[str, float]]:
        """Extrai importância das features"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_)
            else:
                return None
            
            return dict(zip(feature_names, importance))
        except:
            return None
    
    def predict(self, model_id: str, X: pd.DataFrame) -> np.ndarray:
        """
        Faz predições com modelo treinado
        
        Args:
            model_id: ID do modelo
            X: Features para predição
            
        Returns:
            Array com predições
        """
        if model_id not in self.models:
            raise ValueError(f"Modelo {model_id} não encontrado")
        
        # Aplicar scaling
        X_scaled = self.scalers[model_id].transform(X)
        
        # Aplicar feature selection se disponível
        if model_id in self.feature_selectors:
            X_selected = self.feature_selectors[model_id].transform(X_scaled)
        else:
            X_selected = X_scaled
        
        # Predição
        predictions = self.models[model_id].predict(X_selected)
        
        return predictions
    
    def predict_with_confidence(self, model_id: str, X: pd.DataFrame, 
                              confidence_level: float = 0.95) -> Dict[str, np.ndarray]:
        """
        Predições com intervalos de confiança
        
        Args:
            model_id: ID do modelo
            X: Features
            confidence_level: Nível de confiança
            
        Returns:
            Dict com predições e intervalos
        """
        predictions = self.predict(model_id, X)
        
        # Estimar incerteza usando bootstrap se o modelo suportar
        if hasattr(self.models[model_id], 'estimators_'):
            # Para modelos ensemble
            estimator_predictions = []
            for estimator in self.models[model_id].estimators_:
                X_scaled = self.scalers[model_id].transform(X)
                if model_id in self.feature_selectors:
                    X_selected = self.feature_selectors[model_id].transform(X_scaled)
                else:
                    X_selected = X_scaled
                pred = estimator.predict(X_selected)
                estimator_predictions.append(pred)
            
            estimator_predictions = np.array(estimator_predictions)
            prediction_std = np.std(estimator_predictions, axis=0)
            
            # Intervalo de confiança assumindo distribuição normal
            alpha = 1 - confidence_level
            z_score = 1.96  # Para 95% de confiança
            
            lower_bound = predictions - z_score * prediction_std
            upper_bound = predictions + z_score * prediction_std
            
            return {
                'predictions': predictions,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'std': prediction_std
            }
        else:
            # Para modelos não-ensemble, retornar apenas predições
            return {
                'predictions': predictions,
                'lower_bound': predictions,
                'upper_bound': predictions,
                'std': np.zeros_like(predictions)
            }
    
    def evaluate_model(self, model_id: str, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """
        Avalia modelo em dados de teste
        
        Args:
            model_id: ID do modelo
            X_test: Features de teste
            y_test: Target de teste
            
        Returns:
            Dict com métricas de avaliação
        """
        predictions = self.predict(model_id, X_test)
        metrics = self._calculate_metrics(y_test.values, predictions)
        
        return {
            'model_id': model_id,
            'test_metrics': metrics,
            'predictions': predictions,
            'actuals': y_test.values
        }
    
    def compare_models(self, X: pd.DataFrame, y: pd.Series, 
                      models_to_compare: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compara performance de múltiplos modelos
        
        Args:
            X: Features
            y: Target
            models_to_compare: Lista de modelos para comparar
            
        Returns:
            DataFrame com comparação
        """
        if models_to_compare is None:
            models_to_compare = ['linear_regression', 'ridge', 'random_forest', 'xgboost']
        
        results = []
        
        for model_name in models_to_compare:
            if model_name in self.available_models:
                try:
                    performance = self.train_model(X, y, model_name, 
                                                 hyperparameter_tuning=False)
                    results.append({
                        'model': model_name,
                        'train_rmse': performance['metrics']['train']['rmse'],
                        'test_rmse': performance['metrics']['test']['rmse'],
                        'train_r2': performance['metrics']['train']['r2'],
                        'test_r2': performance['metrics']['test']['r2'],
                        'cv_rmse_mean': performance['cv_scores']['mean'],
                        'cv_rmse_std': performance['cv_scores']['std']
                    })
                except Exception as e:
                    print(f"Erro ao treinar {model_name}: {e}")
        
        return pd.DataFrame(results).sort_values('test_rmse')
    
    def create_ensemble_model(self, model_ids: List[str], weights: Optional[List[float]] = None) -> str:
        """
        Cria modelo ensemble
        
        Args:
            model_ids: Lista de IDs de modelos
            weights: Pesos para cada modelo
            
        Returns:
            ID do modelo ensemble
        """
        if weights is None:
            weights = [1.0 / len(model_ids)] * len(model_ids)
        
        ensemble_id = f"ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        def ensemble_predict(X):
            predictions = []
            for model_id, weight in zip(model_ids, weights):
                pred = self.predict(model_id, X)
                predictions.append(pred * weight)
            return np.sum(predictions, axis=0)
        
        # Criar um objeto simulando modelo sklearn
        class EnsembleModel:
            def __init__(self, predict_func):
                self.predict = predict_func
        
        self.models[ensemble_id] = EnsembleModel(ensemble_predict)
        
        return ensemble_id
    
    def _save_model(self, model_id: str):
        """Salva modelo e componentes"""
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        
        model_data = {
            'model': self.models[model_id],
            'scaler': self.scalers[model_id],
            'feature_selector': self.feature_selectors.get(model_id),
            'performance': self.model_performance[model_id]
        }
        
        joblib.dump(model_data, model_path)
    
    def load_model(self, model_id: str):
        """Carrega modelo salvo"""
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            
            self.models[model_id] = model_data['model']
            self.scalers[model_id] = model_data['scaler']
            if model_data['feature_selector']:
                self.feature_selectors[model_id] = model_data['feature_selector']
            self.model_performance[model_id] = model_data['performance']
        else:
            raise FileNotFoundError(f"Modelo {model_id} não encontrado")
    
    def list_models(self) -> pd.DataFrame:
        """Lista todos os modelos treinados"""
        if not self.model_performance:
            return pd.DataFrame()
        
        models_info = []
        for model_id, performance in self.model_performance.items():
            models_info.append({
                'model_id': model_id,
                'model_name': performance['model_name'],
                'test_rmse': performance['metrics']['test']['rmse'],
                'test_r2': performance['metrics']['test']['r2'],
                'cv_rmse': performance['cv_scores']['mean'],
                'n_features': len(performance['selected_features'])
            })
        
        return pd.DataFrame(models_info)
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Retorna informações detalhadas do modelo"""
        if model_id not in self.model_performance:
            raise ValueError(f"Modelo {model_id} não encontrado")
        
        return self.model_performance[model_id]
    
    def delete_model(self, model_id: str):
        """Remove modelo"""
        if model_id in self.models:
            del self.models[model_id]
        if model_id in self.scalers:
            del self.scalers[model_id]
        if model_id in self.feature_selectors:
            del self.feature_selectors[model_id]
        if model_id in self.model_performance:
            del self.model_performance[model_id]
        
        # Remover arquivo
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        if os.path.exists(model_path):
            os.remove(model_path)
