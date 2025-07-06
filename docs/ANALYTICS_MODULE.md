# Módulo de Analytics e Reporting

## Visão Geral

O módulo de Analytics é um sistema completo de análise quantitativa e geração de relatórios para trading de criptomoedas. Ele fornece ferramentas avançadas para análise estatística, machine learning, backtesting, análise de risco e geração automática de relatórios.

## Componentes Principais

### 1. Advanced Analytics
- **Localização:** `src/analytics/advanced_analytics.py`
- **Funcionalidade:** Análises estatísticas avançadas

#### Recursos:
- Estatísticas descritivas completas (média, mediana, desvio padrão, skewness, kurtosis)
- Testes de normalidade (Jarque-Bera, Shapiro-Wilk)
- Análise de correlação (Pearson, Spearman, Kendall)
- Análise de séries temporais
- Análise de Componentes Principais (PCA)
- Clustering (K-means)
- Visualizações interativas

#### Exemplo de Uso:
```python
from analytics import AdvancedAnalytics

analytics = AdvancedAnalytics()

# Estatísticas descritivas
stats = analytics.descriptive_statistics(data)

# Análise de correlação
corr_analysis = analytics.correlation_analysis(data)

# PCA
pca_results = analytics.principal_component_analysis(data)
```

### 2. Risk Analytics
- **Localização:** `src/analytics/risk_analytics.py`
- **Funcionalidade:** Métricas avançadas de risco

#### Recursos:
- **VaR (Value at Risk):** Histórico, Paramétrico, Monte Carlo
- **CVaR (Conditional VaR):** Expected Shortfall
- **Maximum Drawdown:** Análise completa de drawdown
- **Métricas de Volatilidade:** GARCH, downside deviation
- **Ratios de Performance:** Sharpe, Sortino, Calmar
- **Stress Testing:** Cenários de stress
- **Simulação Monte Carlo:** Projeções probabilísticas
- **Risk Parity:** Otimização de pesos por risco

#### Exemplo de Uso:
```python
from analytics import RiskAnalytics

risk = RiskAnalytics()

# Value at Risk
var_95 = risk.calculate_var(returns, confidence_level=0.95)

# Conditional VaR
cvar_95 = risk.calculate_cvar(returns, confidence_level=0.95)

# Maximum Drawdown
dd_analysis = risk.calculate_maximum_drawdown(prices)

# Monte Carlo
mc_results = risk.monte_carlo_simulation(returns, num_simulations=1000)
```

### 3. Backtesting Engine
- **Localização:** `src/analytics/backtesting_engine.py`
- **Funcionalidade:** Sistema robusto de backtesting

#### Recursos:
- **Simulação de Trading:** Ordens de compra/venda
- **Gestão de Portfolio:** Cálculo de valor, posições
- **Comissões:** Simulação realista de custos
- **Métricas de Performance:** Retorno, Sharpe, drawdown
- **Estratégias Incluídas:** Média Móvel, RSI
- **Visualizações:** Gráficos de performance
- **Export de Resultados:** CSV, JSON

#### Exemplo de Uso:
```python
from analytics import BacktestingEngine
from analytics.backtesting_engine import simple_ma_strategy

engine = BacktestingEngine(initial_capital=10000, commission=0.001)
engine.add_data(data, "BTCUSDT")

results = engine.run_backtest(
    strategy=simple_ma_strategy,
    short_window=10,
    long_window=30
)

print(f"Retorno Total: {results['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.4f}")
```

### 4. Machine Learning Models
- **Localização:** `src/analytics/ml_models.py`
- **Funcionalidade:** Modelos preditivos treinados

#### Recursos:
- **Preparação de Features:** Lags, médias móveis, ratios
- **Modelos Disponíveis:** 
  - Linear Regression, Ridge, Lasso, Elastic Net
  - Random Forest, Gradient Boosting, XGBoost
  - Support Vector Regression, Neural Networks
- **Feature Selection:** Seleção automática de features
- **Hyperparameter Tuning:** Grid Search
- **Cross-Validation:** Validação cruzada
- **Ensemble Models:** Combinação de modelos
- **Predições com Confiança:** Intervalos de confiança

#### Exemplo de Uso:
```python
from analytics import MLModels

ml_models = MLModels()

# Preparar features
X, y = ml_models.prepare_features(
    data, 
    target_column='close',
    lag_features=5
)

# Treinar modelo
performance = ml_models.train_model(
    X, y,
    model_name='random_forest',
    hyperparameter_tuning=True
)

# Fazer predições
predictions = ml_models.predict(performance['model_id'], X_new)
```

### 5. Report Generator
- **Localização:** `src/analytics/report_generator.py`
- **Funcionalidade:** Geração automática de relatórios

#### Recursos:
- **Formatos:** HTML, JSON, Markdown
- **Seções do Relatório:**
  - Resumo Executivo
  - Análises Descritivas
  - Análise de Risco
  - Análise Técnica
  - Métricas de Performance
  - Recomendações
- **Visualizações:** Gráficos interativos Plotly
- **Templates:** HTML e Markdown customizáveis
- **Insights Automáticos:** Geração de insights baseada em dados

#### Exemplo de Uso:
```python
from analytics import ReportGenerator

report_gen = ReportGenerator()

report = report_gen.generate_comprehensive_report(
    data=data,
    returns_column='returns',
    price_column='close',
    title='Relatório de Trading',
    format_type='html'
)

print(f"Relatório gerado: {report['report_path']}")
```

## API FastAPI

### Endpoints Disponíveis

#### Análises Estatísticas
- `POST /analytics/descriptive-statistics` - Estatísticas descritivas
- `POST /analytics/correlation-analysis` - Análise de correlação

#### Análise de Risco
- `POST /analytics/risk-analysis` - Análise completa de risco
- `POST /analytics/monte-carlo` - Simulação Monte Carlo

#### Backtesting
- `POST /analytics/backtest` - Executar backtesting

#### Machine Learning
- `POST /analytics/ml-models/train` - Treinar modelo
- `GET /analytics/ml-models/list` - Listar modelos
- `POST /analytics/ml-models/{model_id}/predict` - Fazer predições

#### Relatórios
- `POST /analytics/reports/generate` - Gerar relatório
- `GET /analytics/reports/{report_id}` - Download de relatório

### Exemplo de Uso da API
```python
import requests

# Configuração de dados
data_config = {
    "source": "sample",  # ou "database", "csv"
    "symbol": "BTCUSDT",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
}

# Análise de risco
response = requests.post(
    "http://localhost:8000/analytics/risk-analysis",
    json={
        "data_config": data_config,
        "confidence_levels": [0.90, 0.95, 0.99]
    }
)

risk_metrics = response.json()
```

## Configuração e Instalação

### Dependências
```bash
pip install scipy statsmodels xgboost joblib jinja2 matplotlib seaborn
```

### Estrutura de Arquivos
```
src/analytics/
├── __init__.py
├── advanced_analytics.py
├── ml_models.py
├── backtesting_engine.py
├── risk_analytics.py
└── report_generator.py

src/api/routers/
└── analytics.py

tests/
└── test_analytics.py

scripts/
└── demo_analytics.py
```

## Testes

Execute os testes com:
```bash
pytest tests/test_analytics.py -v
```

**Cobertura de Testes:**
- ✅ 36 testes passando
- ✅ Cobertura completa de todos os módulos
- ✅ Testes de integração entre componentes

## Script de Demonstração

Execute a demonstração completa:
```bash
python scripts/demo_analytics.py
```

**O que a demonstração inclui:**
- Geração de dados sintéticos
- Análises estatísticas completas
- Análise de risco abrangente
- Backtesting de estratégias
- Treinamento de modelos ML
- Geração de relatórios
- Criação de visualizações

## Resultados e Performance

### Métricas de Exemplo (Demo)

#### Advanced Analytics
- Análises estatísticas em 500 dias de dados
- PCA: 2 componentes explicam 95% da variância
- Clustering: 3 clusters com Silhouette Score 0.366

#### Risk Analytics
- VaR 95%: -4.20% (histórico), -4.58% (paramétrico)
- Maximum Drawdown: -38.90%
- Sharpe Ratio: 0.6023
- Volatilidade Anualizada: 45.37%

#### Backtesting Results
- **Estratégia Média Móvel:** +18.23% retorno, Sharpe 0.54
- **Estratégia RSI:** +54.72% retorno, Sharpe 1.10
- 14 trades (MA) vs 10 trades (RSI)

#### Machine Learning
- **Melhor Modelo:** Linear Regression
- **R² Teste:** 0.9943
- **RMSE:** 357.31
- **Erro Médio:** < 1% nas predições

## Arquivos Gerados

### Relatórios
- HTML: Relatório interativo com visualizações
- JSON: Dados estruturados para integração
- Markdown: Documentação legível

### Visualizações
- Dashboard de Analytics (PNG)
- Matriz de Correlação (PNG)
- Gráficos Plotly Interativos (HTML)

## Casos de Uso

### 1. Análise de Portfolio
- Avaliação de risco de carteiras
- Otimização de alocação
- Métricas de performance

### 2. Desenvolvimento de Estratégias
- Backtesting de novas estratégias
- Análise de drawdown
- Otimização de parâmetros

### 3. Machine Learning Trading
- Predição de preços
- Classificação de sinais
- Feature engineering automatizado

### 4. Risk Management
- Monitoramento de VaR
- Stress testing
- Análise de correlações

### 5. Reporting Automatizado
- Relatórios diários/semanais
- Dashboards executivos
- Alertas de risco

## Personalização e Extensão

### Adicionando Novas Estratégias
```python
def my_custom_strategy(engine, current_data, **params):
    # Sua lógica de estratégia aqui
    current_price = current_data['close']
    
    # Exemplo: comprar se preço subiu 2%
    if some_condition:
        engine.place_order(OrderType.BUY, quantity)
    elif other_condition:
        engine.place_order(OrderType.SELL, quantity)
```

### Adicionando Novos Modelos
```python
from sklearn.ensemble import ExtraTreesRegressor

# Adicionar ao available_models
ml_models.available_models['extra_trees'] = ExtraTreesRegressor()
```

### Customizando Relatórios
```python
# Modificar templates HTML/Markdown
report_gen.templates['html'] = custom_html_template
```

## Melhores Práticas

### 1. Performance
- Use dados filtrados para análises longas
- Implemente cache para cálculos repetitivos
- Use paralelização para Monte Carlo

### 2. Qualidade dos Dados
- Sempre valide dados de entrada
- Trate valores ausentes adequadamente
- Normalize dados quando necessário

### 3. Risk Management
- Monitore métricas em tempo real
- Configure alertas automáticos
- Mantenha logs detalhados

### 4. Machine Learning
- Use validação temporal para séries temporais
- Evite look-ahead bias
- Regularmente retreine modelos

## Limitações e Considerações

### 1. Dados Históricos
- Backtesting não garante performance futura
- Considere regime changes no mercado
- Use dados de boa qualidade

### 2. Overfitting
- Cuidado com otimização excessiva
- Use cross-validation adequada
- Monitore performance out-of-sample

### 3. Latência
- Algumas análises são computacionalmente intensivas
- Use background tasks para processamento longo
- Considere aproximações para análises em tempo real

## Suporte e Contribuição

### Logs e Debug
- Logs detalhados em `logs/analytics.log`
- Use `logging.DEBUG` para troubleshooting
- Monitore métricas de performance

### Contribuindo
1. Fork o repositório
2. Crie feature branch
3. Adicione testes
4. Atualize documentação
5. Submeta pull request

## Conclusão

O módulo de Analytics fornece uma base sólida para análise quantitativa em trading de criptomoedas. Com componentes modulares e bem testados, oferece flexibilidade para diversos casos de uso, desde análises exploratórias até sistemas de produção.

Para mais informações, consulte os exemplos em `scripts/demo_analytics.py` e os testes em `tests/test_analytics.py`.
