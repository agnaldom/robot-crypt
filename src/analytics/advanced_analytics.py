"""
Advanced Analytics - Análises estatísticas avançadas
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import warnings
from scipy import stats
from scipy.stats import jarque_bera, shapiro, anderson
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')


class AdvancedAnalytics:
    """
    Classe para análises estatísticas avançadas de dados de trading
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA()
        
    def descriptive_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula estatísticas descritivas avançadas
        
        Args:
            data: DataFrame com dados de trading
            
        Returns:
            Dict com estatísticas descritivas
        """
        stats_dict = {}
        
        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column].dropna()
            
            if len(series) > 0:
                stats_dict[column] = {
                    'count': len(series),
                    'mean': series.mean(),
                    'median': series.median(),
                    'std': series.std(),
                    'variance': series.var(),
                    'skewness': series.skew(),
                    'kurtosis': series.kurtosis(),
                    'min': series.min(),
                    'max': series.max(),
                    'range': series.max() - series.min(),
                    'q1': series.quantile(0.25),
                    'q3': series.quantile(0.75),
                    'iqr': series.quantile(0.75) - series.quantile(0.25),
                    'mad': series.sub(series.mean()).abs().mean(),  # Mean Absolute Deviation
                    'cv': series.std() / series.mean() if series.mean() != 0 else 0,  # Coefficient of Variation
                    'percentile_95': series.quantile(0.95),
                    'percentile_5': series.quantile(0.05),
                }
                
                # Testes de normalidade
                if len(series) >= 8:
                    try:
                        jb_stat, jb_p = jarque_bera(series)
                        stats_dict[column]['jarque_bera'] = {
                            'statistic': jb_stat,
                            'p_value': jb_p,
                            'is_normal': jb_p > 0.05
                        }
                    except:
                        stats_dict[column]['jarque_bera'] = None
                        
                if len(series) >= 3:
                    try:
                        sw_stat, sw_p = shapiro(series)
                        stats_dict[column]['shapiro_wilk'] = {
                            'statistic': sw_stat,
                            'p_value': sw_p,
                            'is_normal': sw_p > 0.05
                        }
                    except:
                        stats_dict[column]['shapiro_wilk'] = None
        
        return stats_dict
    
    def correlation_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Análise de correlação avançada
        
        Args:
            data: DataFrame com dados numéricos
            
        Returns:
            Dict com análises de correlação
        """
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            return {}
        
        # Matriz de correlação Pearson
        pearson_corr = numeric_data.corr(method='pearson')
        
        # Matriz de correlação Spearman
        spearman_corr = numeric_data.corr(method='spearman')
        
        # Matriz de correlação Kendall
        kendall_corr = numeric_data.corr(method='kendall')
        
        # Identificar correlações significativas
        significant_correlations = []
        for i in range(len(pearson_corr.columns)):
            for j in range(i+1, len(pearson_corr.columns)):
                col1, col2 = pearson_corr.columns[i], pearson_corr.columns[j]
                pearson_val = pearson_corr.iloc[i, j]
                spearman_val = spearman_corr.iloc[i, j]
                kendall_val = kendall_corr.iloc[i, j]
                
                if abs(pearson_val) > 0.3:  # Threshold para correlação significativa
                    significant_correlations.append({
                        'pair': (col1, col2),
                        'pearson': pearson_val,
                        'spearman': spearman_val,
                        'kendall': kendall_val,
                        'strength': self._correlation_strength(abs(pearson_val))
                    })
        
        return {
            'pearson_matrix': pearson_corr,
            'spearman_matrix': spearman_corr,
            'kendall_matrix': kendall_corr,
            'significant_correlations': significant_correlations
        }
    
    def _correlation_strength(self, corr_value: float) -> str:
        """Classifica a força da correlação"""
        if corr_value >= 0.8:
            return "Very Strong"
        elif corr_value >= 0.6:
            return "Strong"
        elif corr_value >= 0.4:
            return "Moderate"
        elif corr_value >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def time_series_analysis(self, data: pd.Series, timestamp_col: Optional[str] = None) -> Dict[str, Any]:
        """
        Análise de séries temporais avançada
        
        Args:
            data: Série temporal
            timestamp_col: Nome da coluna de timestamp (se aplicável)
            
        Returns:
            Dict com análises de série temporal
        """
        if timestamp_col and timestamp_col in data.index.names:
            ts_data = data.copy()
        else:
            ts_data = data.copy()
        
        # Estatísticas básicas da série temporal
        analysis = {
            'trend_analysis': self._analyze_trend(ts_data),
            'seasonality': self._detect_seasonality(ts_data),
            'stationarity': self._test_stationarity(ts_data),
            'autocorrelation': self._calculate_autocorrelation(ts_data),
            'volatility_clustering': self._analyze_volatility_clustering(ts_data),
            'distribution_analysis': self._analyze_distribution(ts_data)
        }
        
        return analysis
    
    def _analyze_trend(self, data: pd.Series) -> Dict[str, Any]:
        """Análise de tendência"""
        # Cálculo de tendência usando regressão linear
        x = np.arange(len(data))
        y = data.values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'std_error': std_err,
            'trend_direction': 'upward' if slope > 0 else 'downward' if slope < 0 else 'flat',
            'trend_strength': abs(r_value)
        }
    
    def _detect_seasonality(self, data: pd.Series) -> Dict[str, Any]:
        """Detecção de sazonalidade"""
        # Análise de sazonalidade usando FFT
        fft_values = np.fft.fft(data.values)
        frequencies = np.fft.fftfreq(len(data))
        
        # Identificar frequências dominantes
        magnitude = np.abs(fft_values)
        dominant_freq_idx = np.argsort(magnitude)[-5:]  # Top 5 frequências
        
        return {
            'dominant_frequencies': frequencies[dominant_freq_idx].tolist(),
            'magnitude': magnitude[dominant_freq_idx].tolist(),
            'has_seasonality': len(dominant_freq_idx) > 1
        }
    
    def _test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        """Teste de estacionariedade"""
        try:
            from statsmodels.tsa.stattools import adfuller
            
            result = adfuller(data.dropna())
            
            return {
                'adf_statistic': result[0],
                'p_value': result[1],
                'critical_values': result[4],
                'is_stationary': result[1] <= 0.05
            }
        except ImportError:
            # Teste simples de estacionariedade
            mean_first_half = data[:len(data)//2].mean()
            mean_second_half = data[len(data)//2:].mean()
            std_first_half = data[:len(data)//2].std()
            std_second_half = data[len(data)//2:].std()
            
            return {
                'mean_difference': abs(mean_first_half - mean_second_half),
                'std_difference': abs(std_first_half - std_second_half),
                'is_stationary': abs(mean_first_half - mean_second_half) < data.std() * 0.1
            }
    
    def _calculate_autocorrelation(self, data: pd.Series, max_lags: int = 20) -> Dict[str, Any]:
        """Cálculo de autocorrelação"""
        autocorr_values = []
        
        for lag in range(1, min(max_lags + 1, len(data) // 2)):
            if len(data) > lag:
                corr = data.autocorr(lag=lag)
                if not np.isnan(corr):
                    autocorr_values.append({'lag': lag, 'correlation': corr})
        
        return {
            'autocorrelations': autocorr_values,
            'significant_lags': [ac for ac in autocorr_values if abs(ac['correlation']) > 0.1]
        }
    
    def _analyze_volatility_clustering(self, data: pd.Series) -> Dict[str, Any]:
        """Análise de clustering de volatilidade"""
        # Calcular retornos se os dados são preços
        if data.min() > 0:  # Assumindo que são preços
            returns = data.pct_change().dropna()
        else:
            returns = data.copy()
        
        # Volatilidade realizada (rolling standard deviation)
        volatility = returns.rolling(window=20).std()
        
        # Detectar períodos de alta e baixa volatilidade
        vol_mean = volatility.mean()
        vol_std = volatility.std()
        
        high_vol_periods = volatility > (vol_mean + vol_std)
        low_vol_periods = volatility < (vol_mean - vol_std)
        
        return {
            'average_volatility': vol_mean,
            'volatility_std': vol_std,
            'high_volatility_periods': high_vol_periods.sum(),
            'low_volatility_periods': low_vol_periods.sum(),
            'volatility_clustering_detected': high_vol_periods.sum() > len(volatility) * 0.1
        }
    
    def _analyze_distribution(self, data: pd.Series) -> Dict[str, Any]:
        """Análise de distribuição"""
        clean_data = data.dropna()
        
        if len(clean_data) == 0:
            return {}
        
        # Momentos da distribuição
        moments = {
            'mean': clean_data.mean(),
            'variance': clean_data.var(),
            'skewness': clean_data.skew(),
            'kurtosis': clean_data.kurtosis(),
            'excess_kurtosis': clean_data.kurtosis() - 3
        }
        
        # Classificação da distribuição
        distribution_type = "normal"
        if abs(moments['skewness']) > 0.5:
            distribution_type = "skewed"
        if abs(moments['excess_kurtosis']) > 1:
            distribution_type = "heavy_tailed" if moments['excess_kurtosis'] > 0 else "light_tailed"
        
        return {
            'moments': moments,
            'distribution_type': distribution_type,
            'outliers_count': len(clean_data[(clean_data > clean_data.quantile(0.95)) | 
                                            (clean_data < clean_data.quantile(0.05))])
        }
    
    def principal_component_analysis(self, data: pd.DataFrame, n_components: Optional[int] = None) -> Dict[str, Any]:
        """
        Análise de Componentes Principais
        
        Args:
            data: DataFrame com dados numéricos
            n_components: Número de componentes principais
            
        Returns:
            Dict com resultados da PCA
        """
        numeric_data = data.select_dtypes(include=[np.number]).dropna()
        
        if numeric_data.empty:
            return {}
        
        # Padronizar os dados
        scaled_data = self.scaler.fit_transform(numeric_data)
        
        # Aplicar PCA
        if n_components is None:
            n_components = min(len(numeric_data.columns), len(numeric_data))
        
        self.pca = PCA(n_components=n_components)
        pca_result = self.pca.fit_transform(scaled_data)
        
        # Criar DataFrame com componentes principais
        pca_df = pd.DataFrame(
            pca_result,
            columns=[f'PC{i+1}' for i in range(n_components)]
        )
        
        return {
            'principal_components': pca_df,
            'explained_variance_ratio': self.pca.explained_variance_ratio_,
            'cumulative_variance_ratio': np.cumsum(self.pca.explained_variance_ratio_),
            'components': pd.DataFrame(
                self.pca.components_.T,
                columns=[f'PC{i+1}' for i in range(n_components)],
                index=numeric_data.columns
            ),
            'n_components_95_variance': np.argmax(np.cumsum(self.pca.explained_variance_ratio_) >= 0.95) + 1
        }
    
    def cluster_analysis(self, data: pd.DataFrame, n_clusters: int = 3) -> Dict[str, Any]:
        """
        Análise de clustering
        
        Args:
            data: DataFrame com dados numéricos
            n_clusters: Número de clusters
            
        Returns:
            Dict com resultados do clustering
        """
        numeric_data = data.select_dtypes(include=[np.number]).dropna()
        
        if numeric_data.empty:
            return {}
        
        # Padronizar os dados
        scaled_data = self.scaler.fit_transform(numeric_data)
        
        # Aplicar K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Adicionar clusters ao DataFrame original
        result_df = numeric_data.copy()
        result_df['cluster'] = clusters
        
        # Análise dos clusters
        cluster_stats = {}
        for cluster_id in range(n_clusters):
            cluster_data = result_df[result_df['cluster'] == cluster_id]
            cluster_stats[f'cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'percentage': len(cluster_data) / len(result_df) * 100,
                'centroid': cluster_data.drop('cluster', axis=1).mean().to_dict()
            }
        
        return {
            'clustered_data': result_df,
            'cluster_centers': kmeans.cluster_centers_,
            'cluster_stats': cluster_stats,
            'inertia': kmeans.inertia_,
            'silhouette_score': self._calculate_silhouette_score(scaled_data, clusters)
        }
    
    def _calculate_silhouette_score(self, data: np.ndarray, labels: np.ndarray) -> float:
        """Calcula o silhouette score"""
        try:
            from sklearn.metrics import silhouette_score
            return silhouette_score(data, labels)
        except ImportError:
            return 0.0
    
    def generate_analytics_report(self, data: pd.DataFrame, title: str = "Analytics Report") -> Dict[str, Any]:
        """
        Gera relatório completo de analytics
        
        Args:
            data: DataFrame com dados
            title: Título do relatório
            
        Returns:
            Dict com relatório completo
        """
        report = {
            'title': title,
            'timestamp': datetime.now().isoformat(),
            'data_info': {
                'shape': data.shape,
                'columns': data.columns.tolist(),
                'dtypes': data.dtypes.to_dict(),
                'null_values': data.isnull().sum().to_dict()
            },
            'descriptive_statistics': self.descriptive_statistics(data),
            'correlation_analysis': self.correlation_analysis(data)
        }
        
        # Análise de séries temporais para colunas numéricas
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            report['time_series_analysis'] = {}
            for col in numeric_columns[:3]:  # Limitar a 3 colunas para performance
                if data[col].notna().sum() > 10:  # Apenas se houver dados suficientes
                    report['time_series_analysis'][col] = self.time_series_analysis(data[col])
        
        # PCA se houver dados suficientes
        if len(numeric_columns) > 2 and len(data) > 10:
            report['pca_analysis'] = self.principal_component_analysis(data)
        
        # Clustering se houver dados suficientes
        if len(numeric_columns) > 1 and len(data) > 10:
            report['cluster_analysis'] = self.cluster_analysis(data)
        
        return report
    
    def create_visualization(self, data: pd.DataFrame, analysis_type: str = "overview") -> go.Figure:
        """
        Cria visualizações para análises
        
        Args:
            data: DataFrame com dados
            analysis_type: Tipo de análise ('overview', 'correlation', 'distribution', 'time_series')
            
        Returns:
            Figura Plotly
        """
        numeric_data = data.select_dtypes(include=[np.number])
        
        if analysis_type == "overview":
            return self._create_overview_plot(numeric_data)
        elif analysis_type == "correlation":
            return self._create_correlation_plot(numeric_data)
        elif analysis_type == "distribution":
            return self._create_distribution_plot(numeric_data)
        elif analysis_type == "time_series":
            return self._create_time_series_plot(numeric_data)
        else:
            return go.Figure()
    
    def _create_overview_plot(self, data: pd.DataFrame) -> go.Figure:
        """Cria plot de overview"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribuição', 'Correlação', 'Boxplot', 'Tendência'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        if len(data.columns) > 0:
            col = data.columns[0]
            
            # Histograma
            fig.add_trace(
                go.Histogram(x=data[col], name=f'Distribuição {col}'),
                row=1, col=1
            )
            
            # Boxplot
            fig.add_trace(
                go.Box(y=data[col], name=f'Boxplot {col}'),
                row=2, col=1
            )
            
            # Série temporal
            fig.add_trace(
                go.Scatter(y=data[col], mode='lines', name=f'Tendência {col}'),
                row=2, col=2
            )
        
        fig.update_layout(height=600, title_text="Overview Estatístico")
        return fig
    
    def _create_correlation_plot(self, data: pd.DataFrame) -> go.Figure:
        """Cria heatmap de correlação"""
        corr_matrix = data.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(title="Matriz de Correlação")
        return fig
    
    def _create_distribution_plot(self, data: pd.DataFrame) -> go.Figure:
        """Cria plots de distribuição"""
        fig = make_subplots(
            rows=len(data.columns), cols=1,
            subplot_titles=data.columns.tolist()
        )
        
        for i, col in enumerate(data.columns):
            fig.add_trace(
                go.Histogram(x=data[col], name=col),
                row=i+1, col=1
            )
        
        fig.update_layout(height=300 * len(data.columns), title_text="Distribuições")
        return fig
    
    def _create_time_series_plot(self, data: pd.DataFrame) -> go.Figure:
        """Cria plots de séries temporais"""
        fig = go.Figure()
        
        for col in data.columns:
            fig.add_trace(
                go.Scatter(
                    y=data[col],
                    mode='lines',
                    name=col
                )
            )
        
        fig.update_layout(title="Séries Temporais")
        return fig
