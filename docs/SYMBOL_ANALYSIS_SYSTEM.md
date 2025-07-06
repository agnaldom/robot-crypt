# Sistema de Análise Inteligente de Símbolos

## Visão Geral

O Sistema de Análise Inteligente de Símbolos é uma implementação completa que analisa dados de mercado de criptomoedas, calcula indicadores técnicos, identifica padrões e gera sinais de trading baseados em inteligência artificial e análise técnica avançada.

## Características Principais

### 🎯 Análise Técnica Avançada
- **Indicadores Técnicos**: RSI, MACD, Bandas de Bollinger, Médias Móveis (EMA/SMA), Estocástico, ATR
- **Análise de Padrões**: Identificação automática de padrões de candlestick
- **Análise de Volume**: Detecção de picos de volume e tendências
- **Análise de Volatilidade**: Classificação de níveis de volatilidade

### 🧠 Geração Inteligente de Sinais
- **Sinais Multi-fonte**: Combinação de indicadores técnicos, volume, volatilidade e padrões
- **Sistema de Confiança**: Cada sinal possui um score de confiança (0-100%)
- **Consolidação de Sinais**: Evita redundância agrupando sinais similares
- **Filtragem Inteligente**: Remove sinais com baixa confiança

### ⚠️ Análise de Risco e Oportunidade
- **Score de Risco**: Análise quantitativa de fatores de risco (0-100%)
- **Score de Oportunidade**: Identificação de oportunidades de trading (0-100%)
- **Recomendações Inteligentes**: Sugestões baseadas na análise combinada

### 💾 Persistência e Histórico
- **Banco PostgreSQL**: Armazenamento de dados de mercado, análises e sinais
- **Cache Inteligente**: Reutilização de dados para melhor performance
- **Histórico Completo**: Tracking de todas as análises e sinais gerados

## Arquitetura do Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dados de      │    │    Análise       │    │    Sinais       │
│   Mercado       │───▶│    Técnica       │───▶│   de Trading    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │ Indicadores &    │    │   Registro      │
│   Database      │    │ Padrões          │    │   no Banco      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Uso Básico

### 1. Análise Simples de um Símbolo

```python
from src.analysis.symbol_analyzer import analyze_symbol

# Análise completa de BTC/USDT
result = analyze_symbol('BTCUSDT', timeframe='1h', limit=100)

if result:
    print(f"Símbol: {result['symbol']}")
    print(f"Recomendação: {result['summary']['recommendation']}")
    print(f"Sinais encontrados: {len(result['signals'])}")
```

### 2. Uso da Classe Principal

```python
from src.analysis.symbol_analyzer import SymbolAnalyzer

# Criar instância do analisador
analyzer = SymbolAnalyzer()

# Análise passo a passo
market_data = analyzer.fetch_market_data('ETHUSDT', '15m', 200)
processed_data = analyzer.process_data(market_data)
signals = analyzer.generate_signals('ETHUSDT', processed_data)
risk_analysis = analyzer.analyze_risk('ETHUSDT', processed_data)
```

### 3. Análise de Múltiplos Símbolos

```python
symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']
results = {}

for symbol in symbols:
    result = analyze_symbol(symbol)
    if result:
        results[symbol] = result

# Processa resultados...
```

## Estrutura dos Dados Retornados

### Análise Completa
```python
{
    'symbol': 'BTCUSDT',
    'timeframe': '1h',
    'timestamp': '2025-01-06T12:00:00',
    'market_data': {
        'technical_indicators': {...},
        'volatility_analysis': {...},
        'volume_analysis': {...},
        'pattern_analysis': {...}
    },
    'signals': [...],
    'risk_analysis': {...},
    'opportunity_analysis': {...},
    'summary': {...}
}
```

### Estrutura de um Sinal
```python
{
    'symbol': 'BTCUSDT',
    'signal_type': 'buy',  # 'buy', 'sell', 'hold'
    'strength': 0.75,      # 0.0 a 1.0
    'confidence': 0.82,    # 0.0 a 1.0
    'price': 45000.0,
    'timestamp': '2025-01-06T12:00:00',
    'reasoning': 'RSI saindo de área de sobrevenda',
    'indicators_data': {...},
    'source': 'technical_rsi'
}
```

### Análise de Risco
```python
{
    'overall_risk': 'medium',  # 'low', 'medium', 'high'
    'risk_score': 0.45,        # 0.0 a 1.0
    'factors': [
        {
            'factor': 'high_volatility',
            'weight': 0.3,
            'description': 'Alta volatilidade detectada'
        }
    ],
    'recommendations': [...]
}
```

## Indicadores Técnicos Disponíveis

### RSI (Relative Strength Index)
- **Período padrão**: 14
- **Sinais**: Sobrecompra (>70), Sobrevenda (<30)
- **Cruzamentos**: Entrada/saída das zonas extremas

### MACD
- **Configuração**: 12, 26, 9
- **Sinais**: Cruzamentos da linha MACD com a linha de sinal
- **Histograma**: Força da tendência

### Bandas de Bollinger
- **Período**: 20
- **Desvio**: 2
- **Sinais**: Preço tocando bandas superior/inferior

### Médias Móveis
- **EMA 9 e 21**: Tendências de curto prazo
- **SMA 50 e 200**: Tendências de longo prazo
- **Golden/Death Cross**: Cruzamentos significativos

### Estocástico
- **Períodos**: %K=14, %D=3
- **Sinais**: Zonas de sobrecompra/sobrevenda

### ATR (Average True Range)
- **Período**: 14
- **Uso**: Medição de volatilidade

## Análise de Padrões

### Padrões de Candlestick
- **Doji**: Indecisão do mercado
- **Hammer**: Possível reversão de alta
- **Shooting Star**: Possível reversão de baixa

### Padrões de Preço
- **Breakout High**: Rompimento de máximas
- **Breakdown Low**: Rompimento de mínimas
- **Consolidação**: Períodos de baixa volatilidade

## Configuração e Instalação

### Dependências
```bash
pip install pandas numpy sqlalchemy psycopg2-binary
```

### Configuração do Banco de Dados

O sistema requer PostgreSQL configurado. As variáveis de ambiente necessárias:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=robot_crypt
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

### Inicialização das Tabelas

O sistema cria automaticamente as tabelas necessárias:
- `trading_signals`: Sinais gerados
- `market_analysis`: Análises completas
- `technical_indicators`: Indicadores calculados
- `price_history`: Dados OHLCV

## Script de Exemplo

Execute o script de exemplo para ver o sistema em ação:

```bash
cd scripts
python example_symbol_analysis.py
```

### Opções do Script
1. **Análise completa**: Analisa múltiplos símbolos
2. **Teste individual**: Testa funções separadamente
3. **Ambos**: Executa análise completa + testes

## Personalização

### Configurando Parâmetros

```python
analyzer = SymbolAnalyzer()

# Modificar configurações
analyzer.config['min_confidence_threshold'] = 0.7  # Confiança mínima
analyzer.config['volatility_window'] = 30          # Janela de volatilidade
analyzer.config['volume_threshold_multiplier'] = 2.0  # Multiplicador de volume
```

### Adicionando Novos Indicadores

```python
class CustomAnalyzer(SymbolAnalyzer):
    def _generate_custom_signals(self, symbol, processed_data, current_price):
        signals = []
        
        # Implementar lógica personalizada
        # ...
        
        return signals
```

## Integração com Trading Bot

### Usando Sinais para Trading
```python
def execute_trading_signals():
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    for symbol in symbols:
        analysis = analyze_symbol(symbol)
        
        if analysis:
            best_signal = analysis['summary'].get('highest_confidence_signal')
            
            if best_signal and best_signal['confidence'] > 0.8:
                signal_type = best_signal['type']
                
                if signal_type == 'buy':
                    # Executar ordem de compra
                    place_buy_order(symbol, best_signal['price'])
                elif signal_type == 'sell':
                    # Executar ordem de venda
                    place_sell_order(symbol, best_signal['price'])
```

## Monitoramento e Logs

### Logs Detalhados
O sistema gera logs detalhados para debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("robot-crypt.symbol_analyzer")
```

### Métricas de Performance
- Tempo de análise por símbolo
- Taxa de sucesso na geração de sinais
- Precisão dos sinais (a ser implementado)

## Limitações e Considerações

### Limitações Atuais
- **Dados**: Dependente da qualidade dos dados da API Binance
- **Latência**: Análise pode levar alguns segundos para símbolos complexos
- **Memória**: Uso de memória aumenta com histórico longo

### Considerações de Risco
- **Não é conselho financeiro**: Sistema para fins educacionais
- **Backtesting**: Recomendado testar estratégias antes do uso real
- **Gestão de risco**: Sempre usar stop-loss e take-profit

## Próximas Funcionalidades

### Em Desenvolvimento
- [ ] Machine Learning para predição de preços
- [ ] Análise de sentimento de notícias
- [ ] Backtesting automático
- [ ] API REST para integração externa
- [ ] Dashboard web para visualização

### Melhorias Planejadas
- [ ] Suporte a mais exchanges
- [ ] Indicadores técnicos adicionais
- [ ] Otimização de performance
- [ ] Alertas em tempo real
- [ ] Integração com Telegram

## Suporte e Contribuição

### Relatando Problemas
- Abra uma issue no repositório
- Inclua logs detalhados
- Descreva os passos para reproduzir

### Contribuindo
1. Fork do repositório
2. Crie uma branch para sua feature
3. Implemente testes
4. Abra um Pull Request

## Exemplos Avançados

### Análise Personalizada com Filtros
```python
def analyze_with_filters(symbol, min_volume=1000000):
    analyzer = SymbolAnalyzer()
    
    # Buscar dados
    market_data = analyzer.fetch_market_data(symbol, '1h', 100)
    
    # Filtrar por volume
    filtered_data = [d for d in market_data if d['volume'] > min_volume]
    
    if len(filtered_data) < 50:
        return None
    
    # Continuar análise...
    processed_data = analyzer.process_data(filtered_data)
    return analyzer.generate_signals(symbol, processed_data)
```

### Análise Multi-timeframe
```python
def multi_timeframe_analysis(symbol):
    timeframes = ['15m', '1h', '4h', '1d']
    results = {}
    
    for tf in timeframes:
        result = analyze_symbol(symbol, timeframe=tf)
        if result:
            results[tf] = result
    
    # Combinar sinais de diferentes timeframes
    return combine_timeframe_signals(results)
```

Este sistema fornece uma base sólida para análise técnica automatizada e pode ser expandido conforme suas necessidades específicas de trading.
