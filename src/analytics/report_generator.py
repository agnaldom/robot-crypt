"""
Report Generator - Gerador de relatórios completos de analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import warnings
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from jinja2 import Template

from .advanced_analytics import AdvancedAnalytics
from .ml_models import MLModels
from .backtesting_engine import BacktestingEngine
from .risk_analytics import RiskAnalytics

warnings.filterwarnings('ignore')


class ReportGenerator:
    """
    Gerador de relatórios completos de analytics e performance
    """
    
    def __init__(self, output_dir: str = "reports/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Inicializar módulos de analytics
        self.advanced_analytics = AdvancedAnalytics()
        self.ml_models = MLModels()
        self.risk_analytics = RiskAnalytics()
        
        # Templates de relatório
        self.templates = {
            'html': self._get_html_template(),
            'markdown': self._get_markdown_template()
        }
    
    def generate_comprehensive_report(self, data: pd.DataFrame,
                                    returns_column: str = 'returns',
                                    price_column: str = 'close',
                                    title: str = "Relatório de Analytics",
                                    format_type: str = 'html') -> Dict[str, Any]:
        """
        Gera relatório completo de analytics
        
        Args:
            data: DataFrame com dados de trading
            returns_column: Nome da coluna de retornos
            price_column: Nome da coluna de preço
            title: Título do relatório
            format_type: Formato ('html', 'json', 'markdown')
            
        Returns:
            Dict com informações do relatório gerado
        """
        print(f"Gerando relatório: {title}")
        
        # Preparar dados
        if returns_column in data.columns:
            returns = data[returns_column]
        else:
            # Calcular retornos se não existir
            if price_column in data.columns:
                prices = data[price_column]
                returns = prices.pct_change().dropna()
            else:
                raise ValueError("Nem coluna de retornos nem de preços encontrada")
        
        # Seções do relatório
        report_data = {
            'metadata': self._generate_metadata(data, title),
            'executive_summary': self._generate_executive_summary(data, returns),
            'descriptive_analytics': self._generate_descriptive_section(data),
            'risk_analytics': self._generate_risk_section(returns, data.get(price_column) if price_column in data.columns else None),
            'technical_analysis': self._generate_technical_section(data),
            'performance_metrics': self._generate_performance_section(returns),
            'visualizations': self._generate_visualizations(data, returns),
            'recommendations': self._generate_recommendations(data, returns)
        }
        
        # Gerar arquivo de relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{title.replace(' ', '_').lower()}_{timestamp}"
        
        if format_type == 'html':
            report_path = self._generate_html_report(report_data, filename)
        elif format_type == 'json':
            report_path = self._generate_json_report(report_data, filename)
        elif format_type == 'markdown':
            report_path = self._generate_markdown_report(report_data, filename)
        else:
            raise ValueError(f"Formato {format_type} não suportado")
        
        return {
            'report_path': report_path,
            'report_data': report_data,
            'timestamp': datetime.now().isoformat(),
            'format': format_type
        }
    
    def _generate_metadata(self, data: pd.DataFrame, title: str) -> Dict[str, Any]:
        """Gera metadados do relatório"""
        return {
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'data_period': {
                'start': data.index[0] if len(data) > 0 else None,
                'end': data.index[-1] if len(data) > 0 else None,
                'total_observations': len(data),
                'frequency': self._infer_frequency(data.index) if len(data) > 1 else 'Unknown'
            },
            'columns_analyzed': data.columns.tolist(),
            'missing_data': data.isnull().sum().to_dict()
        }
    
    def _infer_frequency(self, index) -> str:
        """Infere frequência dos dados"""
        if len(index) < 2:
            return 'Unknown'
        
        diff = index[1] - index[0]
        if diff.total_seconds() <= 60:
            return 'Minute'
        elif diff.total_seconds() <= 3600:
            return 'Hourly'
        elif diff.days == 1:
            return 'Daily'
        elif diff.days == 7:
            return 'Weekly'
        elif diff.days >= 28 and diff.days <= 31:
            return 'Monthly'
        else:
            return 'Irregular'
    
    def _generate_executive_summary(self, data: pd.DataFrame, returns: pd.Series) -> Dict[str, Any]:
        """Gera resumo executivo"""
        if len(returns) == 0:
            return {'message': 'Dados insuficientes para análise'}
        
        # Métricas principais
        total_return = (1 + returns).cumprod().iloc[-1] - 1 if len(returns) > 0 else 0
        volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        sharpe = self.risk_analytics.calculate_sharpe_ratio(returns).get('sharpe_ratio', 0)
        max_dd = self.risk_analytics.calculate_maximum_drawdown((1 + returns).cumprod()).get('max_drawdown_pct', 0)
        
        # Classificação de performance
        performance_score = self._calculate_performance_score(total_return, volatility, sharpe, max_dd)
        
        return {
            'period_return_pct': total_return * 100,
            'annualized_volatility_pct': volatility * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd,
            'performance_score': performance_score,
            'risk_level': self._classify_risk_level(volatility),
            'return_classification': self._classify_returns(total_return),
            'key_insights': self._generate_key_insights(data, returns)
        }
    
    def _calculate_performance_score(self, returns: float, volatility: float, 
                                   sharpe: float, max_dd: float) -> float:
        """Calcula score de performance (0-100)"""
        # Componentes do score
        return_score = min(max(returns * 100, -50), 50) + 50  # -50% to 50% -> 0 to 100
        volatility_score = max(0, 100 - volatility * 100)  # Lower vol = higher score
        sharpe_score = min(max(sharpe * 20, -20), 80) + 20  # -1 to 4 Sharpe -> 0 to 100
        dd_score = max(0, 100 + max_dd)  # Less DD = higher score
        
        # Peso igual para cada componente
        total_score = (return_score + volatility_score + sharpe_score + dd_score) / 4
        return round(total_score, 1)
    
    def _classify_risk_level(self, volatility: float) -> str:
        """Classifica nível de risco"""
        if volatility < 0.1:
            return "Muito Baixo"
        elif volatility < 0.2:
            return "Baixo"
        elif volatility < 0.3:
            return "Moderado"
        elif volatility < 0.5:
            return "Alto"
        else:
            return "Muito Alto"
    
    def _classify_returns(self, returns: float) -> str:
        """Classifica retornos"""
        if returns > 0.3:
            return "Excelente"
        elif returns > 0.1:
            return "Bom"
        elif returns > 0:
            return "Positivo"
        elif returns > -0.1:
            return "Levemente Negativo"
        else:
            return "Negativo"
    
    def _generate_key_insights(self, data: pd.DataFrame, returns: pd.Series) -> List[str]:
        """Gera insights principais"""
        insights = []
        
        if len(returns) == 0:
            return ["Dados insuficientes para gerar insights"]
        
        # Insight sobre consistência
        positive_days = (returns > 0).sum()
        total_days = len(returns)
        win_rate = positive_days / total_days * 100
        
        if win_rate > 60:
            insights.append(f"Alta consistência: {win_rate:.1f}% dos períodos foram positivos")
        elif win_rate < 40:
            insights.append(f"Baixa consistência: apenas {win_rate:.1f}% dos períodos foram positivos")
        
        # Insight sobre volatilidade
        recent_vol = returns.tail(30).std() * np.sqrt(252)
        overall_vol = returns.std() * np.sqrt(252)
        
        if recent_vol > overall_vol * 1.2:
            insights.append("Volatilidade recente está acima da média histórica")
        elif recent_vol < overall_vol * 0.8:
            insights.append("Volatilidade recente está abaixo da média histórica")
        
        # Insight sobre tendência
        recent_returns = returns.tail(30).mean() * 252
        if recent_returns > 0.1:
            insights.append("Tendência recente é positiva")
        elif recent_returns < -0.1:
            insights.append("Tendência recente é negativa")
        
        return insights
    
    def _generate_descriptive_section(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Gera seção de análise descritiva"""
        return {
            'summary_statistics': self.advanced_analytics.descriptive_statistics(data),
            'correlation_analysis': self.advanced_analytics.correlation_analysis(data),
            'distribution_analysis': self._analyze_distributions(data)
        }
    
    def _analyze_distributions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Análise de distribuições"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        distributions = {}
        
        for col in numeric_cols[:5]:  # Limitar a 5 colunas
            series = data[col].dropna()
            if len(series) > 0:
                distributions[col] = {
                    'normality_test': self._test_normality(series),
                    'outliers_count': self._count_outliers(series),
                    'distribution_type': self._classify_distribution(series)
                }
        
        return distributions
    
    def _test_normality(self, series: pd.Series) -> Dict[str, Any]:
        """Teste de normalidade"""
        try:
            from scipy.stats import jarque_bera, shapiro
            jb_stat, jb_p = jarque_bera(series)
            return {
                'jarque_bera_p_value': jb_p,
                'is_normal_jb': jb_p > 0.05,
                'test_statistic': jb_stat
            }
        except:
            return {'error': 'Não foi possível realizar teste de normalidade'}
    
    def _count_outliers(self, series: pd.Series) -> int:
        """Conta outliers usando IQR"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return len(outliers)
    
    def _classify_distribution(self, series: pd.Series) -> str:
        """Classifica tipo de distribuição"""
        skew = series.skew()
        kurt = series.kurtosis()
        
        if abs(skew) < 0.5 and abs(kurt) < 3:
            return "Aproximadamente Normal"
        elif skew > 0.5:
            return "Assimétrica à Direita"
        elif skew < -0.5:
            return "Assimétrica à Esquerda"
        elif kurt > 3:
            return "Leptocúrtica (caudas pesadas)"
        elif kurt < -1:
            return "Platicúrtica (caudas leves)"
        else:
            return "Distribuição Irregular"
    
    def _generate_risk_section(self, returns: pd.Series, prices: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Gera seção de análise de risco"""
        if len(returns) == 0:
            return {'message': 'Dados insuficientes para análise de risco'}
        
        return {
            'var_analysis': self._generate_var_analysis(returns),
            'volatility_metrics': self.risk_analytics.calculate_volatility_metrics(returns),
            'drawdown_analysis': self.risk_analytics.calculate_maximum_drawdown(prices) if prices is not None else {},
            'performance_ratios': self.risk_analytics.calculate_sharpe_ratio(returns),
            'stress_tests': self.risk_analytics.stress_testing(returns, {}),
            'risk_summary': self._generate_risk_summary(returns)
        }
    
    def _generate_var_analysis(self, returns: pd.Series) -> Dict[str, Any]:
        """Análise detalhada de VaR"""
        var_results = {}
        confidence_levels = [0.90, 0.95, 0.99]
        methods = ['historical', 'parametric']
        
        for confidence in confidence_levels:
            for method in methods:
                key = f"{method}_{int(confidence*100)}"
                var_results[key] = self.risk_analytics.calculate_var(returns, confidence, method)
        
        return var_results
    
    def _generate_risk_summary(self, returns: pd.Series) -> Dict[str, Any]:
        """Resumo de risco"""
        vol = returns.std() * np.sqrt(252)
        var_95 = self.risk_analytics.calculate_var(returns, 0.95).get('var_pct', 0)
        
        return {
            'risk_level': self._classify_risk_level(vol),
            'volatility_percentile': self._calculate_volatility_percentile(vol),
            'var_interpretation': self._interpret_var(var_95),
            'risk_recommendations': self._generate_risk_recommendations(vol, var_95)
        }
    
    def _calculate_volatility_percentile(self, volatility: float) -> str:
        """Calcula percentil de volatilidade"""
        # Benchmarks típicos de volatilidade
        if volatility < 0.05:
            return "5% inferior (muito baixa)"
        elif volatility < 0.15:
            return "25% inferior (baixa)"
        elif volatility < 0.25:
            return "50% (mediana)"
        elif volatility < 0.35:
            return "75% superior (alta)"
        else:
            return "95% superior (muito alta)"
    
    def _interpret_var(self, var_pct: float) -> str:
        """Interpreta VaR"""
        var_abs = abs(var_pct)
        if var_abs < 1:
            return "Risco muito baixo - perdas diárias raramente excedem 1%"
        elif var_abs < 3:
            return "Risco baixo - perdas diárias raramente excedem 3%"
        elif var_abs < 5:
            return "Risco moderado - perdas diárias podem chegar a 5%"
        elif var_abs < 10:
            return "Risco alto - perdas diárias podem chegar a 10%"
        else:
            return "Risco muito alto - perdas diárias podem exceder 10%"
    
    def _generate_risk_recommendations(self, volatility: float, var_pct: float) -> List[str]:
        """Gera recomendações de risco"""
        recommendations = []
        
        if volatility > 0.3:
            recommendations.append("Considere reduzir posições ou implementar stop-loss mais rigoroso")
        
        if abs(var_pct) > 5:
            recommendations.append("VaR elevado - considere diversificação ou hedging")
        
        if volatility < 0.1:
            recommendations.append("Volatilidade baixa pode indicar oportunidade para aumentar exposição")
        
        return recommendations
    
    def _generate_technical_section(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Gera seção de análise técnica"""
        technical_analysis = {}
        
        # Verificar se há dados de preço
        price_columns = ['close', 'price', 'value']
        price_col = None
        
        for col in price_columns:
            if col in data.columns:
                price_col = col
                break
        
        if price_col:
            prices = data[price_col]
            technical_analysis['moving_averages'] = self._calculate_moving_averages(prices)
            technical_analysis['momentum_indicators'] = self._calculate_momentum_indicators(prices)
            technical_analysis['trend_analysis'] = self._analyze_trend(prices)
        
        return technical_analysis
    
    def _calculate_moving_averages(self, prices: pd.Series) -> Dict[str, Any]:
        """Calcula médias móveis"""
        ma_periods = [10, 20, 50]
        mas = {}
        
        for period in ma_periods:
            if len(prices) >= period:
                ma = prices.rolling(window=period).mean()
                current_price = prices.iloc[-1]
                current_ma = ma.iloc[-1]
                
                mas[f'MA_{period}'] = {
                    'current_value': current_ma,
                    'signal': 'Bullish' if current_price > current_ma else 'Bearish',
                    'distance_pct': ((current_price - current_ma) / current_ma * 100) if current_ma != 0 else 0
                }
        
        return mas
    
    def _calculate_momentum_indicators(self, prices: pd.Series) -> Dict[str, Any]:
        """Calcula indicadores de momentum"""
        momentum = {}
        
        # RSI
        if len(prices) >= 14:
            rsi = self._calculate_rsi(prices, 14)
            current_rsi = rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50
            
            momentum['RSI'] = {
                'current_value': current_rsi,
                'signal': 'Oversold' if current_rsi < 30 else 'Overbought' if current_rsi > 70 else 'Neutral',
                'interpretation': self._interpret_rsi(current_rsi)
            }
        
        # Momentum simples
        if len(prices) >= 10:
            momentum_10 = (prices.iloc[-1] / prices.iloc[-10] - 1) * 100
            momentum['Momentum_10d'] = {
                'value_pct': momentum_10,
                'signal': 'Positive' if momentum_10 > 0 else 'Negative'
            }
        
        return momentum
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _interpret_rsi(self, rsi: float) -> str:
        """Interpreta RSI"""
        if rsi < 20:
            return "Extremamente sobrevendido"
        elif rsi < 30:
            return "Sobrevendido"
        elif rsi < 50:
            return "Bearish"
        elif rsi < 70:
            return "Bullish"
        elif rsi < 80:
            return "Sobrecomprado"
        else:
            return "Extremamente sobrecomprado"
    
    def _analyze_trend(self, prices: pd.Series) -> Dict[str, Any]:
        """Análise de tendência"""
        if len(prices) < 20:
            return {}
        
        # Tendência de curto prazo (10 dias)
        short_trend = (prices.iloc[-1] / prices.iloc[-10] - 1) * 100
        
        # Tendência de médio prazo (30 dias se disponível)
        medium_trend = (prices.iloc[-1] / prices.iloc[-min(30, len(prices))] - 1) * 100
        
        return {
            'short_term_trend_pct': short_trend,
            'medium_term_trend_pct': medium_trend,
            'short_term_direction': 'Upward' if short_trend > 0 else 'Downward',
            'medium_term_direction': 'Upward' if medium_trend > 0 else 'Downward',
            'trend_strength': self._classify_trend_strength(abs(short_trend))
        }
    
    def _classify_trend_strength(self, trend_magnitude: float) -> str:
        """Classifica força da tendência"""
        if trend_magnitude < 2:
            return "Fraca"
        elif trend_magnitude < 5:
            return "Moderada"
        elif trend_magnitude < 10:
            return "Forte"
        else:
            return "Muito Forte"
    
    def _generate_performance_section(self, returns: pd.Series) -> Dict[str, Any]:
        """Gera seção de performance"""
        if len(returns) == 0:
            return {}
        
        # Métricas de performance
        cumulative_returns = (1 + returns).cumprod()
        
        # Performance por períodos
        performance_periods = {}
        periods = {'1M': 30, '3M': 90, '6M': 180, '1Y': 252}
        
        for period_name, days in periods.items():
            if len(returns) >= days:
                period_return = (cumulative_returns.iloc[-1] / cumulative_returns.iloc[-days] - 1) * 100
                performance_periods[period_name] = period_return
        
        # Análise de performance mensal
        monthly_analysis = self._analyze_monthly_performance(returns)
        
        return {
            'cumulative_return_pct': (cumulative_returns.iloc[-1] - 1) * 100,
            'period_performance': performance_periods,
            'monthly_analysis': monthly_analysis,
            'consistency_metrics': self._calculate_consistency_metrics(returns),
            'rolling_performance': self._calculate_rolling_performance(returns)
        }
    
    def _analyze_monthly_performance(self, returns: pd.Series) -> Dict[str, Any]:
        """Análise de performance mensal"""
        if len(returns) < 30:
            return {}
        
        # Agrupar por mês
        monthly_returns = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
        
        return {
            'best_month_pct': monthly_returns.max() * 100,
            'worst_month_pct': monthly_returns.min() * 100,
            'positive_months': (monthly_returns > 0).sum(),
            'total_months': len(monthly_returns),
            'average_monthly_return_pct': monthly_returns.mean() * 100
        }
    
    def _calculate_consistency_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """Calcula métricas de consistência"""
        positive_periods = (returns > 0).sum()
        total_periods = len(returns)
        
        # Rolling win rate
        rolling_win_rate = returns.rolling(30).apply(lambda x: (x > 0).mean() * 100)
        
        return {
            'win_rate_pct': (positive_periods / total_periods * 100) if total_periods > 0 else 0,
            'current_rolling_win_rate_pct': rolling_win_rate.iloc[-1] if len(rolling_win_rate) > 0 else 0,
            'consistency_score': self._calculate_consistency_score(returns)
        }
    
    def _calculate_consistency_score(self, returns: pd.Series) -> float:
        """Calcula score de consistência (0-100)"""
        if len(returns) == 0:
            return 0
        
        # Baseado na estabilidade dos retornos
        volatility = returns.std()
        mean_return = returns.mean()
        
        # Score baseado em Sharpe ratio modificado
        if volatility > 0:
            consistency = min(100, max(0, (mean_return / volatility + 2) * 25))
        else:
            consistency = 100 if mean_return >= 0 else 0
        
        return round(consistency, 1)
    
    def _calculate_rolling_performance(self, returns: pd.Series) -> Dict[str, Any]:
        """Calcula performance rolling"""
        if len(returns) < 30:
            return {}
        
        rolling_30d = returns.rolling(30).apply(lambda x: (1 + x).prod() - 1) * 100
        
        return {
            'current_30d_return_pct': rolling_30d.iloc[-1],
            'best_30d_return_pct': rolling_30d.max(),
            'worst_30d_return_pct': rolling_30d.min(),
            'avg_30d_return_pct': rolling_30d.mean()
        }
    
    def _generate_visualizations(self, data: pd.DataFrame, returns: pd.Series) -> Dict[str, str]:
        """Gera visualizações e salva como HTML"""
        visualizations = {}
        
        try:
            # 1. Performance Chart
            perf_fig = self._create_performance_chart(returns)
            perf_path = self.output_dir / "performance_chart.html"
            pio.write_html(perf_fig, str(perf_path))
            visualizations['performance_chart'] = str(perf_path)
            
            # 2. Risk Analytics
            risk_fig = self.risk_analytics.create_risk_visualization(returns)
            risk_path = self.output_dir / "risk_analytics.html"
            pio.write_html(risk_fig, str(risk_path))
            visualizations['risk_analytics'] = str(risk_path)
            
            # 3. Advanced Analytics
            analytics_fig = self.advanced_analytics.create_visualization(data, "overview")
            analytics_path = self.output_dir / "advanced_analytics.html"
            pio.write_html(analytics_fig, str(analytics_path))
            visualizations['advanced_analytics'] = str(analytics_path)
            
        except Exception as e:
            print(f"Erro ao gerar visualizações: {e}")
        
        return visualizations
    
    def _create_performance_chart(self, returns: pd.Series) -> go.Figure:
        """Cria gráfico de performance"""
        cumulative_returns = (1 + returns).cumprod()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Retorno Cumulativo', 'Retornos Diários', 'Rolling Sharpe', 'Drawdown'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Retorno cumulativo
        fig.add_trace(
            go.Scatter(x=cumulative_returns.index, y=cumulative_returns, 
                      mode='lines', name='Retorno Cumulativo'),
            row=1, col=1
        )
        
        # Retornos diários
        fig.add_trace(
            go.Scatter(x=returns.index, y=returns * 100, 
                      mode='lines', name='Retornos Diários (%)'),
            row=1, col=2
        )
        
        # Rolling Sharpe (30 dias)
        if len(returns) >= 30:
            rolling_sharpe = returns.rolling(30).mean() / returns.rolling(30).std() * np.sqrt(252)
            fig.add_trace(
                go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe, 
                          mode='lines', name='Rolling Sharpe 30d'),
                row=2, col=1
            )
        
        # Drawdown
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max * 100
        fig.add_trace(
            go.Scatter(x=drawdown.index, y=drawdown, 
                      mode='lines', name='Drawdown (%)', fill='tonexty'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, title="Análise de Performance")
        return fig
    
    def _generate_recommendations(self, data: pd.DataFrame, returns: pd.Series) -> Dict[str, Any]:
        """Gera recomendações"""
        recommendations = {
            'strategic': [],
            'tactical': [],
            'risk_management': [],
            'overall_assessment': ''
        }
        
        if len(returns) == 0:
            recommendations['overall_assessment'] = 'Dados insuficientes para análise'
            return recommendations
        
        # Análise de performance
        total_return = (1 + returns).cumprod().iloc[-1] - 1
        sharpe = self.risk_analytics.calculate_sharpe_ratio(returns).get('sharpe_ratio', 0)
        volatility = returns.std() * np.sqrt(252)
        
        # Recomendações estratégicas
        if sharpe > 1.5:
            recommendations['strategic'].append("Excelente relação risco-retorno - considere manter estratégia")
        elif sharpe < 0.5:
            recommendations['strategic'].append("Baixa relação risco-retorno - revisão estratégica necessária")
        
        if total_return > 0.2:
            recommendations['strategic'].append("Performance forte - considere aumento gradual de exposição")
        elif total_return < -0.1:
            recommendations['strategic'].append("Performance negativa - considere redução de exposição")
        
        # Recomendações táticas
        recent_vol = returns.tail(30).std() * np.sqrt(252)
        if recent_vol > volatility * 1.3:
            recommendations['tactical'].append("Volatilidade recente elevada - considere reduzir posições")
        
        win_rate = (returns > 0).mean()
        if win_rate < 0.4:
            recommendations['tactical'].append("Baixa taxa de acerto - revisar sinais de entrada/saída")
        
        # Gestão de risco
        var_95 = abs(self.risk_analytics.calculate_var(returns, 0.95).get('var_pct', 0))
        if var_95 > 5:
            recommendations['risk_management'].append("VaR elevado - implementar stop-loss mais rigoroso")
        
        max_dd = abs(self.risk_analytics.calculate_maximum_drawdown((1 + returns).cumprod()).get('max_drawdown_pct', 0))
        if max_dd > 20:
            recommendations['risk_management'].append("Drawdown máximo alto - diversificação recomendada")
        
        # Avaliação geral
        score = self._calculate_performance_score(total_return, volatility, sharpe, max_dd)
        if score >= 80:
            recommendations['overall_assessment'] = "Estratégia excelente com performance consistente"
        elif score >= 60:
            recommendations['overall_assessment'] = "Estratégia boa com potencial de melhoria"
        elif score >= 40:
            recommendations['overall_assessment'] = "Estratégia moderada - necessita ajustes"
        else:
            recommendations['overall_assessment'] = "Estratégia precisa de revisão significativa"
        
        return recommendations
    
    def _generate_html_report(self, report_data: Dict[str, Any], filename: str) -> str:
        """Gera relatório em HTML"""
        template = Template(self.templates['html'])
        html_content = template.render(**report_data)
        
        html_path = self.output_dir / f"{filename}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _generate_json_report(self, report_data: Dict[str, Any], filename: str) -> str:
        """Gera relatório em JSON"""
        # Converter objetos não serializáveis
        json_data = self._make_serializable(report_data)
        
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(json_path)
    
    def _generate_markdown_report(self, report_data: Dict[str, Any], filename: str) -> str:
        """Gera relatório em Markdown"""
        template = Template(self.templates['markdown'])
        md_content = template.render(**report_data)
        
        md_path = self.output_dir / f"{filename}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(md_path)
    
    def _make_serializable(self, obj: Any) -> Any:
        """Torna objetos serializáveis para JSON"""
        if isinstance(obj, dict):
            return {str(k): self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, pd.DataFrame):
            # Convert DataFrame index to string to avoid timestamp issues
            df_dict = obj.reset_index().to_dict('records')
            return df_dict
        elif isinstance(obj, pd.Series):
            # Convert Series index to string to avoid timestamp issues
            return {str(k): v for k, v in obj.to_dict().items()}
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def _get_html_template(self) -> str:
        """Template HTML para relatório"""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ metadata.title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px; }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .recommendation { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 5px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ metadata.title }}</h1>
        <p>Gerado em: {{ metadata.generated_at }}</p>
        <p>Período: {{ metadata.data_period.start }} a {{ metadata.data_period.end }}</p>
    </div>

    <div class="section">
        <h2>Resumo Executivo</h2>
        <div class="metric">
            <strong>Retorno do Período:</strong> 
            <span class="{% if executive_summary.period_return_pct > 0 %}positive{% else %}negative{% endif %}">
                {{ "%.2f"|format(executive_summary.period_return_pct) }}%
            </span>
        </div>
        <div class="metric">
            <strong>Sharpe Ratio:</strong> {{ "%.2f"|format(executive_summary.sharpe_ratio) }}
        </div>
        <div class="metric">
            <strong>Score de Performance:</strong> {{ executive_summary.performance_score }}/100
        </div>
        <div class="metric">
            <strong>Nível de Risco:</strong> {{ executive_summary.risk_level }}
        </div>
        
        <h3>Insights Principais:</h3>
        <ul>
        {% for insight in executive_summary.key_insights %}
            <li>{{ insight }}</li>
        {% endfor %}
        </ul>
    </div>

    <div class="section">
        <h2>Análise de Risco</h2>
        <div class="metric">
            <strong>Volatilidade Anualizada:</strong> {{ "%.2f"|format(risk_analytics.volatility_metrics.volatility_pct) }}%
        </div>
        <div class="metric">
            <strong>VaR 95% (1 dia):</strong> {{ "%.2f"|format(risk_analytics.var_analysis.historical_95.var_pct) }}%
        </div>
        <div class="metric">
            <strong>Drawdown Máximo:</strong> {{ "%.2f"|format(risk_analytics.drawdown_analysis.max_drawdown_pct) }}%
        </div>
    </div>

    <div class="section">
        <h2>Recomendações</h2>
        <p><strong>Avaliação Geral:</strong> {{ recommendations.overall_assessment }}</p>
        
        <h3>Estratégicas:</h3>
        {% for rec in recommendations.strategic %}
            <div class="recommendation">{{ rec }}</div>
        {% endfor %}
        
        <h3>Gestão de Risco:</h3>
        {% for rec in recommendations.risk_management %}
            <div class="recommendation">{{ rec }}</div>
        {% endfor %}
    </div>
</body>
</html>
        """
    
    def _get_markdown_template(self) -> str:
        """Template Markdown para relatório"""
        return """
# {{ metadata.title }}

**Gerado em:** {{ metadata.generated_at }}
**Período:** {{ metadata.data_period.start }} a {{ metadata.data_period.end }}

## Resumo Executivo

- **Retorno do Período:** {{ "%.2f"|format(executive_summary.period_return_pct) }}%
- **Sharpe Ratio:** {{ "%.2f"|format(executive_summary.sharpe_ratio) }}
- **Score de Performance:** {{ executive_summary.performance_score }}/100
- **Nível de Risco:** {{ executive_summary.risk_level }}

### Insights Principais:
{% for insight in executive_summary.key_insights %}
- {{ insight }}
{% endfor %}

## Análise de Risco

- **Volatilidade Anualizada:** {{ "%.2f"|format(risk_analytics.volatility_metrics.volatility_pct) }}%
- **VaR 95% (1 dia):** {{ "%.2f"|format(risk_analytics.var_analysis.historical_95.var_pct) }}%
- **Drawdown Máximo:** {{ "%.2f"|format(risk_analytics.drawdown_analysis.max_drawdown_pct) }}%

## Recomendações

**Avaliação Geral:** {{ recommendations.overall_assessment }}

### Estratégicas:
{% for rec in recommendations.strategic %}
- {{ rec }}
{% endfor %}

### Gestão de Risco:
{% for rec in recommendations.risk_management %}
- {{ rec }}
{% endfor %}
        """
