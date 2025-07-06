# APIs de Dados Reais de Mercado - Documentação

## 📋 Visão Geral

O Robot-Crypt agora está integrado com **5 APIs reais** para fornecer dados abrangentes de mercado, notícias, eventos e análise de sentimento:

### 🔗 APIs Integradas

1. **🟡 Binance API** (Gratuita) - Dados de preços em tempo real
2. **🔵 CoinMarketCap API** (Freemium) - Rankings e dados de mercado
3. **🟠 CoinMarketCal API** (Freemium) - Eventos de criptomoedas
4. **🟣 CryptoPanic API** (Freemium) - Notícias com análise de sentimento
5. **🔴 NewsAPI** (Freemium) - Notícias gerais e financeiras

## 🔧 Configuração

### 1. Variáveis de Ambiente

Adicione as seguintes chaves no seu arquivo `.env`:

```env
# Binance API (não requer chave para dados públicos)
# Automático

# CoinMarketCap API
COINMARKETCAP_API_KEY=your_coinmarketcap_api_key_here

# CoinMarketCal API  
COINMARKETCAL_API_KEY=your_coinmarketcal_api_key_here

# CryptoPanic API
CRYPTOPANIC_API_KEY=your_cryptopanic_api_key_here

# NewsAPI
NEWS_API_KEY=your_newsapi_key_here
```

### 2. Como Obter as Chaves de API

#### **Binance API**
- ✅ **Não requer chave** para dados públicos de mercado
- Automaticamente habilitada

#### **CoinMarketCap API**
1. Acesse [https://coinmarketcap.com/api/](https://coinmarketcap.com/api/)
2. Crie uma conta gratuita
3. Obtenha sua chave da API na dashboard
4. **Plano Gratuito**: 10.000 requisições/mês

#### **CoinMarketCal API**
1. Acesse [https://developers.coinmarketcal.com/](https://developers.coinmarketcal.com/)
2. Registre-se para uma conta
3. Gere sua chave de API
4. **Plano Gratuito**: 1.000 requisições/mês

#### **CryptoPanic API**
1. Acesse [https://cryptopanic.com/developers/api/](https://cryptopanic.com/developers/api/)
2. Crie uma conta
3. Obtenha sua chave de API gratuita
4. **Plano Gratuito**: 200 requisições/mês

#### **NewsAPI**
1. Acesse [https://newsapi.org/](https://newsapi.org/)
2. Registre-se para uma conta gratuita
3. Obtenha sua chave de API
4. **Plano Gratuito**: 1.000 requisições/mês

## 📊 Endpoints da API

### 🔸 **Preço Atual**
```http
GET /market/price/{symbol}
```
**Exemplo**: `GET /market/price/BTC/USDT`

**Resposta**:
```json
{
  "symbol": "BTC/USDT",
  "name": "BTC",
  "price": 45000.50,
  "price_change_24h": 1200.30,
  "price_change_percentage_24h": 2.75,
  "volume_24h": 28500000000,
  "market_cap": 850000000000,
  "high_24h": 46000.00,
  "low_24h": 44200.00,
  "source": "binance",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 🔸 **Dados Históricos**
```http
GET /market/historical/{symbol}?days=30
```
**Parâmetros**:
- `days`: 1-365 dias de histórico

**Resposta**:
```json
{
  "symbol": "BTC/USDT",
  "days": 30,
  "data": [
    {
      "timestamp": "2024-01-15T00:00:00Z",
      "open": 44800.00,
      "high": 46000.00,
      "low": 44200.00,
      "close": 45000.50,
      "volume": 850000000
    }
  ],
  "count": 30
}
```

### 🔸 **Moedas em Tendência**
```http
GET /market/trending?limit=10
```

**Resposta**:
```json
{
  "trending_coins": [
    {
      "symbol": "BTC/USDT",
      "name": "Bitcoin",
      "price": 45000.50,
      "price_change_percentage_24h": 2.75,
      "volume_24h": 28500000000,
      "source": "binance"
    }
  ],
  "count": 10
}
```

### 🔸 **Resumo de Mercado**
```http
GET /market/market-summary?symbols=BTC/USDT,ETH/USDT,BNB/USDT
```

### 🔸 **Notícias**
```http
GET /market/news/{symbol}?limit=10
```

**Resposta**:
```json
{
  "symbol": "BTC/USDT",
  "coin": "BTC",
  "news": [
    {
      "title": "Bitcoin Reaches New Heights",
      "description": "Bitcoin price surge continues...",
      "url": "https://example.com/news/1",
      "source": "CryptoNews",
      "published_at": "2024-01-15T08:00:00Z",
      "sentiment": "positive",
      "sentiment_score": 0.75,
      "importance": "high",
      "currencies": ["BTC"],
      "source_type": "cryptopanic"
    }
  ],
  "count": 10
}
```

### 🔸 **Análise de Sentimento**
```http
GET /market/sentiment/{symbol}?days=7
```

**Resposta**:
```json
{
  "symbol": "BTC/USDT",
  "coin": "BTC",
  "sentiment": "positive",
  "sentiment_score": 0.65,
  "confidence": 0.85,
  "post_count": 142,
  "sentiment_distribution": {
    "positive": 85,
    "neutral": 42,
    "negative": 15
  },
  "analyzed_days": 7,
  "source": "cryptopanic"
}
```

### 🔸 **Eventos Futuros**
```http
GET /market/events?days_ahead=7&limit=20
```

**Resposta**:
```json
{
  "events": [
    {
      "title": "Bitcoin ETF Decision",
      "description": "SEC decision on Bitcoin ETF approval",
      "date_event": "2024-01-20T00:00:00Z",
      "source": "coinmarketcal",
      "importance": "high",
      "currencies": ["BTC"],
      "category": "Regulation",
      "votes": 245
    }
  ],
  "count": 15,
  "days_ahead": 7
}
```

### 🔸 **Análise Abrangente** ⭐
```http
GET /market/analysis?symbols=BTC/USDT,ETH/USDT&include_news=true&include_events=true&include_sentiment=true
```

**Resposta**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "symbols_analyzed": ["BTC/USDT", "ETH/USDT"],
  "api_status": {
    "binance": true,
    "coinmarketcap": true,
    "coinmarketcal": false,
    "cryptopanic": true,
    "news_api": true
  },
  "market_data": [...],
  "trending": [...],
  "news": [...],
  "events": [...],
  "sentiment": {...},
  "summary": {
    "market_summary": {
      "average_price_change_24h": 2.15,
      "positive_performers": 1,
      "negative_performers": 1,
      "total_symbols": 2
    },
    "news_summary": {
      "total_articles": 25,
      "overall_news_sentiment": "positive"
    },
    "events_summary": {
      "total_upcoming_events": 8,
      "high_importance_events": 3
    }
  }
}
```

### 🔸 **Health Check**
```http
GET /market/health
```

**Resposta**:
```json
{
  "status": "healthy",
  "api_connectivity": true,
  "api_status": {
    "binance": true,
    "coinmarketcap": true,
    "coinmarketcal": false,
    "cryptopanic": true,
    "news_api": true
  },
  "data_sources": {
    "binance": true,
    "coinmarketcap": true,
    "coinmarketcal": false,
    "cryptopanic": true,
    "news_api": true
  }
}
```

## 🎯 Funcionalidades Principais

### ✅ **Dados de Preços em Tempo Real**
- Preços atuais de centenas de criptomoedas
- Dados históricos (1 dia a 1 ano)
- Volume de negociação 24h
- Variação percentual
- Máximas e mínimas do dia

### ✅ **Análise de Sentimento**
- Análise automática de notícias
- Score de sentimento (-1 a +1)
- Distribuição de sentimentos
- Confiança da análise
- Múltiplas fontes de dados

### ✅ **Notícias Agregadas**
- Notícias específicas por criptomoeda
- Múltiplas fontes (CryptoPanic, NewsAPI)
- Classificação de importância
- Análise de sentimento automática
- Filtragem por moeda

### ✅ **Eventos de Mercado**
- Calendário de eventos importantes
- Classificação por importância
- Filtros por categoria
- Votação da comunidade
- Datas e descrições detalhadas

### ✅ **Moedas em Tendência**
- Top moedas por volume
- Gainers e losers do dia
- Dados de múltiplas exchanges
- Ranking por capitalização de mercado

## 🔄 Fallback e Resiliência

O sistema implementa **fallback automático**:

1. **Binance** (principal) → **CoinMarketCap** (backup)
2. **CryptoPanic** (principal) → **NewsAPI** (backup)
3. **Dados mock** como último recurso

## 📈 Exemplos de Uso

### 1. **Dashboard Principal**
```javascript
// Obter análise completa do mercado
const marketAnalysis = await fetch('/market/analysis?symbols=BTC/USDT,ETH/USDT,BNB/USDT');
const data = await marketAnalysis.json();

// Exibir dados
console.log(`Sentimento geral: ${data.summary.news_summary.overall_news_sentiment}`);
console.log(`Eventos importantes: ${data.summary.events_summary.high_importance_events}`);
```

### 2. **Página Específica de Moeda**
```javascript
// Dados detalhados do Bitcoin
const btcPrice = await fetch('/market/price/BTC/USDT');
const btcNews = await fetch('/market/news/BTC/USDT?limit=5');
const btcSentiment = await fetch('/market/sentiment/BTC/USDT?days=7');
const btcHistory = await fetch('/market/historical/BTC/USDT?days=30');
```

### 3. **Monitoramento de Status**
```javascript
// Verificar saúde das APIs
const health = await fetch('/market/health');
const status = await health.json();

if (status.api_status.binance) {
  console.log('✅ Binance API funcionando');
} else {
  console.log('❌ Binance API com problemas');
}
```

## ⚠️ Limitações e Considerações

### **Limites de Rate**
- **Binance**: 1200 req/min (grátis)
- **CoinMarketCap**: 10.000 req/mês (grátis)
- **CoinMarketCal**: 1.000 req/mês (grátis)
- **CryptoPanic**: 200 req/mês (grátis)
- **NewsAPI**: 1.000 req/mês (grátis)

### **Qualidade dos Dados**
- **Preços**: Dados em tempo real da Binance
- **Sentimento**: Análise baseada em palavras-chave
- **Notícias**: Agregação de múltiplas fontes
- **Eventos**: Dados da comunidade CoinMarketCal

### **APIs Opcionais**
- O sistema funciona mesmo se algumas APIs estiverem indisponíveis
- Fallback automático para fontes alternativas
- Graceful degradation quando APIs estão offline

## 🚀 Próximos Passos

### **Melhorias Planejadas**
1. **Cache Redis** para otimizar performance
2. **WebSockets** para dados em tempo real
3. **Machine Learning** para análise de sentimento avançada
4. **Alertas automáticos** baseados em eventos
5. **Dashboard interativo** com gráficos
6. **API de trading** para execução automática

### **Expansão de Fontes**
- **Fear & Greed Index**
- **On-chain metrics** (Glassnode)
- **Social media sentiment** (Twitter/Reddit)
- **Technical indicators** avançados

## 📞 Suporte

Para questões sobre as APIs:

1. **Logs**: Verifique os logs da aplicação
2. **Health Check**: Use `/market/health` para diagnosticar
3. **Fallback**: O sistema continua funcionando mesmo com APIs offline
4. **Documentação**: APIs individuais têm documentação específica

---

**✨ Agora o Robot-Crypt tem dados reais de mercado de múltiplas fontes confiáveis!**
