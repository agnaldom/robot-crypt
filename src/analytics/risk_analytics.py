"""
Risk Analytics - Métricas avançadas de risco (VaR, CVaR, etc.)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import warnings
from scipy import stats
from scipy.optimize import minimize
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')


class RiskAnalytics:
    """
    Classe para análise de risco avançada
    """
    
    def __init__(self):
        self.confidence_levels = [0.90, 0.95, 0.99]
        self.risk_metrics = {}
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95, 
                     method: str = 'historical') -> Dict[str, float]:
        """
        Calcula Value at Risk (VaR)
        
        Args:
            returns: Série de retornos
            confidence_level: Nível de confiança
            method: Método ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            Dict com métricas de VaR
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        alpha = 1 - confidence_level
        
        if method == 'historical':
            var = np.percentile(clean_returns, alpha * 100)
            
        elif method == 'parametric':
            # Assumindo distribuição normal
            mean = clean_returns.mean()
            std = clean_returns.std()
            var = stats.norm.ppf(alpha, mean, std)
            
        elif method == 'monte_carlo':
            # Simulação Monte Carlo
            mean = clean_returns.mean()
            std = clean_returns.std()
            simulations = np.random.normal(mean, std, 10000)
            var = np.percentile(simulations, alpha * 100)
            
        else:
            raise ValueError(f"Método {method} não reconhecido")
        
        return {
            'var': var,
            'var_pct': var * 100,
            'confidence_level': confidence_level,
            'method': method,
            'expected_shortfall': self._calculate_expected_shortfall(clean_returns, var),
            'relative_var': abs(var / clean_returns.mean()) if clean_returns.mean() != 0 else 0
        }
    
    def _calculate_expected_shortfall(self, returns: pd.Series, var: float) -> float:
        """Calcula Expected Shortfall (CVaR)"""
        tail_returns = returns[returns <= var]
        return tail_returns.mean() if len(tail_returns) > 0 else var
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calcula Conditional Value at Risk (CVaR) ou Expected Shortfall
        
        Args:
            returns: Série de retornos
            confidence_level: Nível de confiança
            
        Returns:
            Dict com métricas de CVaR
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        alpha = 1 - confidence_level
        var = np.percentile(clean_returns, alpha * 100)
        
        # CVaR é a média dos retornos que são menores ou iguais ao VaR
        tail_returns = clean_returns[clean_returns <= var]
        cvar = tail_returns.mean() if len(tail_returns) > 0 else var
        
        return {
            'cvar': cvar,
            'cvar_pct': cvar * 100,
            'var': var,
            'tail_expectation': cvar,
            'tail_observations': len(tail_returns),
            'tail_percentage': len(tail_returns) / len(clean_returns) * 100
        }
    
    def calculate_maximum_drawdown(self, prices: pd.Series) -> Dict[str, Any]:
        """
        Calcula Maximum Drawdown e métricas relacionadas
        
        Args:
            prices: Série de preços ou valores do portfolio
            
        Returns:
            Dict com métricas de drawdown
        """
        if len(prices) == 0:
            return {}
        
        # Calcular drawdown
        running_max = prices.expanding().max()
        drawdown = (prices - running_max) / running_max
        
        # Maximum Drawdown
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Período de drawdown máximo
        peak_before = running_max.loc[:max_dd_date].idxmax()
        
        # Recovery (se aplicável)
        recovery_date = None
        if max_dd_date < prices.index[-1]:
            post_dd_prices = prices.loc[max_dd_date:]
            peak_value = running_max.loc[max_dd_date]
            recovery_prices = post_dd_prices[post_dd_prices >= peak_value]
            if len(recovery_prices) > 0:
                recovery_date = recovery_prices.index[0]
        
        # Duração do drawdown
        if peak_before is not None and max_dd_date is not None:
            try:
                # Try datetime calculation first
                dd_duration = (max_dd_date - peak_before).days
            except AttributeError:
                # Handle non-datetime indices (e.g., integer indices)
                dd_duration = abs(max_dd_date - peak_before)
        else:
            dd_duration = 0
        
        # Tempo de recuperação
        if recovery_date is not None and max_dd_date is not None:
            try:
                # Try datetime calculation first
                recovery_duration = (recovery_date - max_dd_date).days
            except AttributeError:
                # Handle non-datetime indices (e.g., integer indices)
                recovery_duration = abs(recovery_date - max_dd_date)
        else:
            recovery_duration = None
        
        # Underwater duration (tempo total em drawdown)
        underwater_periods = drawdown[drawdown < 0]
        underwater_duration = len(underwater_periods)
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd * 100,
            'max_drawdown_date': max_dd_date,
            'peak_before_dd': peak_before,
            'drawdown_duration_days': dd_duration,
            'recovery_date': recovery_date,
            'recovery_duration_days': recovery_duration,
            'underwater_duration': underwater_duration,
            'underwater_percentage': underwater_duration / len(prices) * 100,
            'current_drawdown': drawdown.iloc[-1],
            'current_drawdown_pct': drawdown.iloc[-1] * 100,
            'drawdown_series': drawdown
        }
    
    def calculate_volatility_metrics(self, returns: pd.Series, 
                                   annualize: bool = True) -> Dict[str, float]:
        """
        Calcula métricas de volatilidade
        
        Args:
            returns: Série de retornos
            annualize: Se deve anualizar as métricas
            
        Returns:
            Dict com métricas de volatilidade
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        # Volatilidade histórica
        volatility = clean_returns.std()
        if annualize:
            volatility *= np.sqrt(252)  # Assumindo 252 dias de trading
        
        # Volatilidade realizada (rolling)
        rolling_vol = clean_returns.rolling(window=30).std()
        if annualize:
            rolling_vol *= np.sqrt(252)
        
        # Volatilidade GARCH (simplificada)
        garch_vol = self._estimate_garch_volatility(clean_returns)
        if annualize:
            garch_vol *= np.sqrt(252)
        
        # Downside deviation
        negative_returns = clean_returns[clean_returns < 0]
        downside_deviation = negative_returns.std() if len(negative_returns) > 0 else 0
        if annualize:
            downside_deviation *= np.sqrt(252)
        
        # Upside deviation
        positive_returns = clean_returns[clean_returns > 0]
        upside_deviation = positive_returns.std() if len(positive_returns) > 0 else 0
        if annualize:
            upside_deviation *= np.sqrt(252)
        
        return {
            'volatility': volatility,
            'volatility_pct': volatility * 100,
            'rolling_volatility_mean': rolling_vol.mean(),
            'rolling_volatility_std': rolling_vol.std(),
            'garch_volatility': garch_vol,
            'downside_deviation': downside_deviation,
            'upside_deviation': upside_deviation,
            'volatility_ratio': upside_deviation / downside_deviation if downside_deviation > 0 else 0,
            'volatility_skew': clean_returns.skew(),
            'volatility_kurtosis': clean_returns.kurtosis()
        }
    
    
    def _estimate_garch_volatility(self, returns: pd.Series, 
                                  alpha: float = 0.1, beta: float = 0.8) -> float:
        """
        Estimativa simples de volatilidade GARCH(1,1)
        
        Args:
            returns: Série de retornos
            alpha: Parâmetro alpha do GARCH
            beta: Parâmetro beta do GARCH
            
        Returns:
            Volatilidade GARCH estimada
        """
        # Implementação simplificada do GARCH(1,1)
        omega = 0.000001  # Termo constante
        volatilities = []
        
        # Volatilidade inicial
        vol_init = returns.std()
        volatilities.append(vol_init)
        
        for i in range(1, len(returns)):
            # GARCH(1,1): σ²(t) = ω + α*ε²(t-1) + β*σ²(t-1)
            prev_return_sq = returns.iloc[i-1] ** 2
            prev_vol_sq = volatilities[i-1] ** 2
            
            vol_sq = omega + alpha * prev_return_sq + beta * prev_vol_sq
            vol = np.sqrt(max(vol_sq, 0))
            volatilities.append(vol)
        
        return np.mean(volatilities)
    
    def calculate_beta(self, asset_returns: pd.Series, 
                      market_returns: pd.Series) -> Dict[str, float]:
        """
        Calcula Beta e métricas relacionadas
        
        Args:
            asset_returns: Retornos do ativo
            market_returns: Retornos do mercado
            
        Returns:
            Dict com métricas de Beta
        """
        # Alinhar séries
        aligned_data = pd.DataFrame({
            'asset': asset_returns,
            'market': market_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return {}
        
        asset_clean = aligned_data['asset']
        market_clean = aligned_data['market']
        
        # Beta
        covariance = np.cov(asset_clean, market_clean)[0, 1]
        market_variance = np.var(market_clean)
        beta = covariance / market_variance if market_variance > 0 else 0
        
        # Alpha (CAPM)
        risk_free_rate = 0.02 / 252  # Assumindo 2% ao ano
        market_return = market_clean.mean()
        asset_return = asset_clean.mean()
        alpha = asset_return - (risk_free_rate + beta * (market_return - risk_free_rate))
        
        # Correlação
        correlation = np.corrcoef(asset_clean, market_clean)[0, 1]
        
        # R-squared
        r_squared = correlation ** 2
        
        # Tracking error
        excess_returns = asset_clean - market_clean
        tracking_error = excess_returns.std()
        
        # Information ratio
        information_ratio = excess_returns.mean() / tracking_error if tracking_error > 0 else 0
        
        return {
            'beta': beta,
            'alpha': alpha,
            'alpha_annualized': alpha * 252,
            'correlation': correlation,
            'r_squared': r_squared,
            'tracking_error': tracking_error,
            'tracking_error_annualized': tracking_error * np.sqrt(252),
            'information_ratio': information_ratio,
            'systematic_risk': beta * np.var(market_clean),
            'idiosyncratic_risk': np.var(asset_clean) - beta * covariance
        }
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                              risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        Calcula Sharpe Ratio e variações
        
        Args:
            returns: Série de retornos
            risk_free_rate: Taxa livre de risco (anualizada)
            
        Returns:
            Dict com métricas de Sharpe
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        # Anualizar retornos
        annual_return = clean_returns.mean() * 252
        annual_volatility = clean_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0
        
        # Sortino Ratio
        negative_returns = clean_returns[clean_returns < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
        
        # Calmar Ratio
        max_dd = self.calculate_maximum_drawdown(
            (1 + clean_returns).cumprod()
        ).get('max_drawdown', 0)
        calmar_ratio = annual_return / abs(max_dd) if max_dd != 0 else 0
        
        # Modified Sharpe (ajustado para skewness e kurtosis)
        skew = clean_returns.skew()
        kurt = clean_returns.kurtosis()
        modified_sharpe = sharpe_ratio * (1 + (skew/6)*sharpe_ratio - ((kurt-3)/24)*sharpe_ratio**2)
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'modified_sharpe': modified_sharpe,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'excess_return': excess_return,
            'downside_volatility': downside_volatility
        }
    
    def calculate_portfolio_risk(self, returns: pd.DataFrame, 
                               weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calcula métricas de risco para portfolio
        
        Args:
            returns: DataFrame com retornos dos ativos
            weights: Pesos do portfolio (equal weight se None)
            
        Returns:
            Dict com métricas de risco do portfolio
        """
        if weights is None:
            weights = [1.0 / len(returns.columns)] * len(returns.columns)
        
        weights = np.array(weights)
        
        # Retornos do portfolio
        portfolio_returns = (returns * weights).sum(axis=1)
        
        # Matriz de covariância
        cov_matrix = returns.cov() * 252  # Anualizada
        
        # Volatilidade do portfolio
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Contribuição de risco por ativo
        marginal_contrib = np.dot(cov_matrix, weights)
        risk_contrib = weights * marginal_contrib / portfolio_vol
        
        # Diversification ratio
        individual_vols = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = np.dot(weights, individual_vols)
        diversification_ratio = weighted_avg_vol / portfolio_vol
        
        # VaR do portfolio
        portfolio_var = self.calculate_var(portfolio_returns)
        
        # Maximum Drawdown do portfolio
        portfolio_cumret = (1 + portfolio_returns).cumprod()
        portfolio_dd = self.calculate_maximum_drawdown(portfolio_cumret)
        
        return {
            'portfolio_volatility': portfolio_vol,
            'portfolio_volatility_pct': portfolio_vol * 100,
            'risk_contributions': dict(zip(returns.columns, risk_contrib)),
            'marginal_contributions': dict(zip(returns.columns, marginal_contrib)),
            'diversification_ratio': diversification_ratio,
            'portfolio_var': portfolio_var,
            'portfolio_drawdown': portfolio_dd,
            'correlation_matrix': returns.corr(),
            'covariance_matrix': cov_matrix
        }
    
    def calculate_risk_parity_weights(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula pesos de Risk Parity
        
        Args:
            returns: DataFrame com retornos dos ativos
            
        Returns:
            Dict com pesos e métricas
        """
        cov_matrix = returns.cov() * 252
        n_assets = len(returns.columns)
        
        def risk_budget_objective(weights, cov_matrix):
            """Função objetivo para risk parity"""
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol
            target_contrib = 1.0 / n_assets
            return sum((risk_contrib - target_contrib) ** 2)
        
        # Otimização
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        result = minimize(
            risk_budget_objective,
            initial_weights,
            args=(cov_matrix,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        
        # Calcular métricas com pesos otimizados
        portfolio_risk = self.calculate_portfolio_risk(returns, optimal_weights)
        
        return {
            'weights': dict(zip(returns.columns, optimal_weights)),
            'optimization_success': result.success,
            'portfolio_metrics': portfolio_risk
        }
    
    def stress_testing(self, returns: pd.Series, scenarios: Dict[str, float]) -> Dict[str, Any]:
        """
        Realiza stress testing
        
        Args:
            returns: Série de retornos
            scenarios: Dict com cenários de stress
            
        Returns:
            Dict com resultados dos stress tests
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        results = {}
        
        # Cenários padrão se não fornecidos
        if not scenarios:
            scenarios = {
                'mild_stress': -0.05,      # -5%
                'moderate_stress': -0.10,   # -10%
                'severe_stress': -0.20,     # -20%
                'extreme_stress': -0.30     # -30%
            }
        
        for scenario_name, shock in scenarios.items():
            # Aplicar shock
            stressed_returns = clean_returns + shock
            
            # Calcular métricas sob stress
            stressed_vol = stressed_returns.std() * np.sqrt(252)
            stressed_var = self.calculate_var(stressed_returns)
            stressed_cvar = self.calculate_cvar(stressed_returns)
            
            # Portfolio value under stress
            cumulative_return = (1 + stressed_returns).cumprod()
            final_value = cumulative_return.iloc[-1]
            
            results[scenario_name] = {
                'shock_magnitude': shock,
                'stressed_volatility': stressed_vol,
                'stressed_var': stressed_var,
                'stressed_cvar': stressed_cvar,
                'final_portfolio_value': final_value,
                'total_loss': (final_value - 1) * 100,
                'max_drawdown': self.calculate_maximum_drawdown(cumulative_return)
            }
        
        return results
    
    def monte_carlo_simulation(self, returns: pd.Series, 
                             num_simulations: int = 1000,
                             time_horizon: int = 252) -> Dict[str, Any]:
        """
        Simulação Monte Carlo
        
        Args:
            returns: Série de retornos históricos
            num_simulations: Número de simulações
            time_horizon: Horizonte temporal (dias)
            
        Returns:
            Dict com resultados da simulação
        """
        clean_returns = returns.dropna()
        
        if len(clean_returns) == 0:
            return {}
        
        # Parâmetros históricos
        mean_return = clean_returns.mean()
        volatility = clean_returns.std()
        
        # Simulações
        simulations = []
        
        for _ in range(num_simulations):
            # Gerar retornos aleatórios
            random_returns = np.random.normal(mean_return, volatility, time_horizon)
            
            # Calcular valor cumulativo
            cumulative_value = (1 + random_returns).cumprod()
            simulations.append(cumulative_value)
        
        simulations = np.array(simulations)
        
        # Análise dos resultados
        final_values = simulations[:, -1]
        
        # Percentis
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        percentile_values = np.percentile(final_values, percentiles)
        
        # Probabilidade de perda
        loss_probability = np.mean(final_values < 1) * 100
        
        # Expected value
        expected_value = np.mean(final_values)
        
        # VaR da simulação
        var_95 = np.percentile(final_values, 5)
        var_99 = np.percentile(final_values, 1)
        
        return {
            'num_simulations': num_simulations,
            'time_horizon_days': time_horizon,
            'expected_final_value': expected_value,
            'expected_return_pct': (expected_value - 1) * 100,
            'loss_probability_pct': loss_probability,
            'var_95_pct': (var_95 - 1) * 100,
            'var_99_pct': (var_99 - 1) * 100,
            'percentiles': dict(zip(percentiles, percentile_values)),
            'simulation_paths': simulations,
            'final_values': final_values
        }
    
    def generate_risk_report(self, returns: pd.Series, 
                           prices: Optional[pd.Series] = None,
                           market_returns: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Gera relatório completo de risco
        
        Args:
            returns: Série de retornos
            prices: Série de preços (opcional)
            market_returns: Retornos do mercado (opcional)
            
        Returns:
            Dict com relatório completo
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_period': {
                'start': returns.index[0] if len(returns) > 0 else None,
                'end': returns.index[-1] if len(returns) > 0 else None,
                'observations': len(returns)
            }
        }
        
        # VaR para diferentes níveis de confiança
        report['var_analysis'] = {}
        for confidence in self.confidence_levels:
            for method in ['historical', 'parametric']:
                key = f"{method}_{int(confidence*100)}"
                report['var_analysis'][key] = self.calculate_var(returns, confidence, method)
        
        # CVaR
        report['cvar_analysis'] = {}
        for confidence in self.confidence_levels:
            key = f"cvar_{int(confidence*100)}"
            report['cvar_analysis'][key] = self.calculate_cvar(returns, confidence)
        
        # Volatilidade
        report['volatility_metrics'] = self.calculate_volatility_metrics(returns)
        
        # Sharpe e ratios
        report['performance_ratios'] = self.calculate_sharpe_ratio(returns)
        
        # Maximum Drawdown
        if prices is not None:
            report['drawdown_analysis'] = self.calculate_maximum_drawdown(prices)
        
        # Beta (se market returns disponível)
        if market_returns is not None:
            report['market_risk_metrics'] = self.calculate_beta(returns, market_returns)
        
        # Stress testing
        report['stress_tests'] = self.stress_testing(returns)
        
        # Monte Carlo (amostra menor para performance)
        report['monte_carlo'] = self.monte_carlo_simulation(returns, num_simulations=100)
        
        return report
    
    def create_risk_visualization(self, returns: pd.Series, 
                                prices: Optional[pd.Series] = None) -> go.Figure:
        """
        Cria visualização de risco
        
        Args:
            returns: Série de retornos
            prices: Série de preços
            
        Returns:
            Figura Plotly
        """
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Distribuição de Retornos', 'VaR Histórico',
                'Rolling Volatility', 'Drawdown',
                'Q-Q Plot', 'Risk Metrics'
            ]
        )
        
        clean_returns = returns.dropna()
        
        # 1. Distribuição de Retornos
        fig.add_trace(
            go.Histogram(x=clean_returns * 100, name='Returns Distribution', nbinsx=50),
            row=1, col=1
        )
        
        # VaR lines
        var_95 = np.percentile(clean_returns, 5) * 100
        var_99 = np.percentile(clean_returns, 1) * 100
        fig.add_vline(x=var_95, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_vline(x=var_99, line_dash="dash", line_color="darkred", row=1, col=1)
        
        # 2. VaR Histórico (rolling)
        rolling_var = clean_returns.rolling(30).quantile(0.05) * 100
        fig.add_trace(
            go.Scatter(x=rolling_var.index, y=rolling_var, name='Rolling VaR 95%'),
            row=1, col=2
        )
        
        # 3. Rolling Volatility
        rolling_vol = clean_returns.rolling(30).std() * np.sqrt(252) * 100
        fig.add_trace(
            go.Scatter(x=rolling_vol.index, y=rolling_vol, name='Rolling Volatility'),
            row=2, col=1
        )
        
        # 4. Drawdown
        if prices is not None:
            running_max = prices.expanding().max()
            drawdown = (prices - running_max) / running_max * 100
            fig.add_trace(
                go.Scatter(x=drawdown.index, y=drawdown, name='Drawdown %', fill='tonexty'),
                row=2, col=2
            )
        
        # 5. Q-Q Plot
        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(clean_returns)))
        sample_quantiles = np.sort(clean_returns)
        fig.add_trace(
            go.Scatter(x=theoretical_quantiles, y=sample_quantiles, mode='markers', name='Q-Q Plot'),
            row=3, col=1
        )
        
        # Linha de referência normal
        fig.add_trace(
            go.Scatter(x=theoretical_quantiles, y=theoretical_quantiles, 
                      mode='lines', name='Normal Reference', line=dict(dash='dash')),
            row=3, col=1
        )
        
        # 6. Risk Metrics Summary (como texto)
        var_metrics = self.calculate_var(clean_returns)
        vol_metrics = self.calculate_volatility_metrics(clean_returns)
        
        risk_text = f"""
        VaR 95%: {var_metrics.get('var_pct', 0):.2f}%
        Volatility: {vol_metrics.get('volatility_pct', 0):.2f}%
        Skewness: {clean_returns.skew():.2f}
        Kurtosis: {clean_returns.kurtosis():.2f}
        """
        
        fig.add_annotation(
            text=risk_text,
            xref="x6", yref="y6",
            x=0.5, y=0.5,
            showarrow=False,
            row=3, col=2
        )
        
        fig.update_layout(height=900, title="Risk Analytics Dashboard")
        
        return fig
