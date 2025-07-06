# 🚀 Prompt para Criação do Dashboard Frontend - Robot-Crypt

Crie um **dashboard frontend moderno e responsivo** para o sistema Robot-Crypt de trading de criptomoedas, com **4 páginas principais** conectando-se a uma API FastAPI robusta.

## 📋 Especificações Técnicas

### **Stack Tecnológico Recomendado**
- **Frontend**: React 18+ com TypeScript
- **UI Framework**: Tailwind CSS + Shadcn/ui (ou Material-UI)
- **Gráficos**: Recharts ou Chart.js
- **Estado Global**: Zustand ou Redux Toolkit
- **HTTP Client**: Axios ou React Query
- **Autenticação**: JWT com refresh tokens
- **Build Tool**: Vite
- **Deploy**: Vercel ou Netlify

### **Conectividade**
- **API Base URL**: `http://localhost:8000` (desenvolvimento)
- **Banco de Dados**: PostgreSQL (via API FastAPI)
- **WebSockets**: Suporte para dados em tempo real
- **Autenticação**: JWT Bearer tokens

## 🎨 Design System

### **Paleta de Cores**
```css
/* Tema Principal */
--primary: #10B981 (Verde - Lucros)
--danger: #EF4444 (Vermelho - Perdas)  
--warning: #F59E0B (Amarelo - Alertas)
--info: #3B82F6 (Azul - Informações)
--dark: #1F2937 (Fundo escuro)
--gray: #6B7280 (Texto secundário)
--light: #F9FAFB (Fundo claro)
```

### **Tipografia**
- **Fonte Principal**: Inter ou Poppins
- **Dados Numéricos**: JetBrains Mono (monospace)

## 📱 Estrutura das Páginas

## 1. 🏠 **PÁGINA DASHBOARD** 
*Visão geral e métricas principais*

### **Layout**
```
+─────────────────────────────────────────────────────+
│ Header: Logo, User Menu, Notifications              │
├─────────────────────────────────────────────────────┤
│ Sidebar: Navigation Menu                            │
├─────────────────────────────────────────────────────┤
│ CARDS DE MÉTRICAS (Grid 4 colunas)                 │
│ ┌─────────┬─────────┬─────────┬─────────┐          │
│ │ Balance │ P&L 24h │ Trades  │ Win Rate│          │
│ │ Total   │ +2.45%  │ Today   │ 68.5%   │          │
│ └─────────┴─────────┴─────────┴─────────┘          │
├─────────────────────────────────────────────────────┤
│ GRÁFICO PRINCIPAL: Portfolio Evolution (7 dias)     │
│ [Gráfico de linha com valor total USDT/BRL]        │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ TRADES RECENTES │ TOP PERFORMING ASSETS           ││
│ │ [Lista últimos  │ [Cards com % de ganho]         ││
│ │ 5 trades]       │                                 ││
│ └─────────────────┴─────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│ ALERTAS E NOTIFICAÇÕES                              │
│ [Lista de alertas importantes]                       │
└─────────────────────────────────────────────────────┘
```

### **Componentes Principais**
1. **MetricCard** - Cards de métricas com valor, percentual e ícone
2. **PortfolioChart** - Gráfico de evolução do portfólio
3. **RecentTrades** - Lista de trades recentes com status
4. **TopAssets** - Cards dos melhores ativos
5. **AlertsFeed** - Feed de notificações e alertas

### **APIs Utilizadas**
```typescript
GET /users/me                    // Dados do usuário
GET /trades/performance          // Métricas de performance
GET /assets/portfolio           // Saldos atuais dos ativos
GET /trades/?limit=5            // Últimos trades
GET /alerts/?limit=10           // Alertas recentes
```

## 2. 📊 **PÁGINA MARKET ANALYSIS**
*Análise técnica e fundamental do mercado*

### **Layout**
```
+─────────────────────────────────────────────────────+
│ FILTROS E CONTROLES                                 │
│ [Seletor de Par] [Timeframe] [Indicadores]         │
├─────────────────────────────────────────────────────┤
│ GRÁFICO PRINCIPAL DE PREÇOS + INDICADORES           │
│ [TradingView-style chart com candlesticks]         │
│ [Sobreposições: MA, EMA, Bollinger Bands]          │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ INDICADORES     │ MARKET SENTIMENT                ││
│ │ RSI: 45.2       │ Fear & Greed: 32 (Fear)        ││
│ │ MACD: Bullish   │ Volume 24h: +15%               ││
│ │ Volume: High    │ Trend: Sideways                ││
│ └─────────────────┴─────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│ NEWS FEED & ECONOMIC EVENTS                         │
│ [Lista de notícias relevantes com impacto]         │
└─────────────────────────────────────────────────────┘
```

### **Componentes Principais**
1. **TradingChart** - Gráfico de candlesticks com indicadores
2. **MarketFilters** - Controles para timeframe e pares
3. **TechnicalIndicators** - Painel com RSI, MACD, etc.
4. **MarketSentiment** - Medidores de sentimento
5. **NewsFeed** - Feed de notícias crypto
6. **EconomicCalendar** - Eventos econômicos

### **APIs Utilizadas**
```typescript
GET /assets/{symbol}/ohlcv      // Dados de preço OHLCV
GET /indicators/technical       // Indicadores técnicos calculados
GET /indicators/macro          // Indicadores macroeconômicos
GET /market/sentiment          // Dados de sentimento
GET /market/news               // Notícias de mercado
```

## 3. 💼 **PÁGINA PORTFOLIO**
*Gestão completa do portfólio*

### **Layout**
```
+─────────────────────────────────────────────────────+
│ PORTFOLIO OVERVIEW                                  │
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ Total Value     │ Asset Allocation (Pie Chart)   ││
│ │ $12,543.21      │ [Gráfico pizza com %]          ││
│ │ +$543 (4.5%)    │                                ││
│ └─────────────────┴─────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│ ASSETS TABLE                                        │
│ ┌─────┬─────────┬─────────┬─────────┬─────────┐    │
│ │Asset│ Amount  │ Value   │ %Port   │ 24h P&L │    │
│ ├─────┼─────────┼─────────┼─────────┼─────────┤    │
│ │ BTC │ 0.3234  │ $8,234  │ 65.7%   │ +2.3%   │    │
│ │ ETH │ 5.644   │ $2,543  │ 20.3%   │ -1.2%   │    │
│ │USDT │ 1,234   │ $1,234  │ 9.8%    │ 0.0%    │    │
│ └─────┴─────────┴─────────┴─────────┴─────────┘    │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ P&L EVOLUTION   │ PERFORMANCE METRICS             ││
│ │ [Gráfico linha  │ Total Return: +15.4%           ││
│ │ últimos 30d]    │ Max Drawdown: -8.2%            ││
│ │                 │ Sharpe Ratio: 1.45             ││
│ │                 │ Win Rate: 68.5%                ││
│ └─────────────────┴─────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### **Componentes Principais**
1. **PortfolioValue** - Valor total com variação
2. **AssetAllocation** - Gráfico pizza da distribuição
3. **AssetsTable** - Tabela detalhada dos ativos
4. **PnLChart** - Evolução do P&L no tempo
5. **PerformanceMetrics** - Métricas de performance
6. **RiskMetrics** - Métricas de risco

### **APIs Utilizadas**
```typescript
GET /assets/portfolio           // Saldos completos dos ativos
GET /trades/performance         // Métricas de performance
GET /portfolio/evolution        // Evolução histórica
GET /portfolio/allocation       // Distribuição por ativo
GET /portfolio/metrics          // Métricas de risco/retorno
```

## 4. 📈 **PÁGINA TRADING**
*Execução e monitoramento de trades*

### **Layout**
```
+─────────────────────────────────────────────────────+
│ TRADING PANEL                                       │
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ ORDER FORM      │ QUICK ACTIONS                   ││
│ │ [Buy/Sell]      │ [Stop All] [Emergency]         ││
│ │ Amount: ___     │ Status: ACTIVE                  ││
│ │ Price: ___      │ Bot Mode: AUTO                  ││
│ │ [PLACE ORDER]   │                                ││
│ └─────────────────┴─────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│ ACTIVE POSITIONS                                    │
│ ┌─────┬─────┬─────────┬─────────┬─────────┬───────┐ │
│ │Pair │Side │ Entry   │ Current │ P&L     │Actions│ │
│ ├─────┼─────┼─────────┼─────────┼─────────┼───────┤ │
│ │BTC  │LONG │ 42,000  │ 43,500  │ +3.6%   │[CLOSE]│ │
│ │ETH  │SHORT│ 2,400   │ 2,350   │ +2.1%   │[CLOSE]│ │
│ └─────┴─────┴─────────┴─────────┴─────────┴───────┘ │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┬─────────────────────────────────┐│
│ │ TRADE HISTORY   │ BOT PERFORMANCE                 ││
│ │ [Lista últimos  │ Today: +$234 (2.1%)           ││
│ │ 10 trades]      │ This Week: +$1,234 (12.4%)    ││
│ │                 │ Success Rate: 68%               ││
│ │                 │ Active Strategies: 3            ││
│ └─────────────────┴─────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│ TRADING LOGS & ALERTS                               │
│ [Real-time logs dos trades e alertas]              │
└─────────────────────────────────────────────────────┘
```

### **Componentes Principais**
1. **OrderForm** - Formulário para executar trades
2. **QuickActions** - Ações rápidas (stop, emergency)
3. **ActivePositions** - Posições abertas atuais
4. **TradeHistory** - Histórico de trades
5. **BotStatus** - Status e performance do bot
6. **TradingLogs** - Logs em tempo real
7. **RiskControls** - Controles de risco

### **APIs Utilizadas**
```typescript
GET /trades/active              // Posições abertas
POST /trades/                   // Executar trade
DELETE /trades/{id}             // Fechar posição
GET /trades/?limit=20           // Histórico de trades
GET /trading-sessions/status    // Status do bot
GET /alerts/trading             // Alertas de trading
WebSocket /ws/trading           // Updates em tempo real
```

## 🔐 Sistema de Autenticação

### **Fluxo de Login**
```typescript
// Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}

// Headers para requests autenticados
Authorization: Bearer eyJ...
```

### **Componentes de Auth**
1. **LoginForm** - Formulário de login
2. **AuthGuard** - Proteção de rotas
3. **TokenRefresh** - Renovação automática de tokens

## 📊 Componentes de Dados

### **Formatação de Números**
```typescript
// Valores monetários
$12,543.21 USD
R$ 62,716.05 BRL

// Percentuais
+2.45% (verde)
-1.23% (vermelho)

// Criptomoedas
0.32145 BTC
1,234.56 USDT
```

### **Estados de Loading**
- **Skeleton loaders** para carregamento
- **Spinners** para ações
- **Toast notifications** para feedback

## 🌐 Conectividade Real-time

### **WebSockets**
```typescript
// Conexão WebSocket para dados em tempo real
const ws = new WebSocket('ws://localhost:8000/ws/trading');

// Eventos suportados
- price_update      // Atualizações de preço
- trade_executed    // Trade executado
- balance_changed   // Saldo alterado
- alert_triggered   // Alerta disparado
```

## 📱 Responsividade

### **Breakpoints**
- **Mobile**: < 768px (Stack vertical, sidebars collapse)
- **Tablet**: 768px - 1024px (Grid adaptativo)
- **Desktop**: > 1024px (Layout completo)

### **Mobile First**
- Navigation drawer para mobile
- Cards empilhados
- Tabelas com scroll horizontal
- Touch-friendly controls

## ⚡ Performance

### **Otimizações**
- **Code splitting** por página
- **Lazy loading** de componentes pesados
- **Memoização** de cálculos
- **Virtual scrolling** para listas grandes
- **Caching** de dados da API

## 🧪 Estrutura de Arquivos

```
src/
├── components/
│   ├── ui/                 # Componentes base (Button, Card, etc)
│   ├── charts/             # Componentes de gráficos
│   ├── forms/              # Formulários
│   └── layout/             # Layout components
├── pages/
│   ├── Dashboard.tsx
│   ├── MarketAnalysis.tsx
│   ├── Portfolio.tsx
│   └── Trading.tsx
├── hooks/                  # Custom hooks
├── services/              # API calls
├── store/                 # Estado global
├── types/                 # TypeScript types
├── utils/                 # Utilitários
└── constants/             # Constantes
```

## 🎯 Funcionalidades Especiais

### **Dashboard**
- Auto-refresh a cada 30 segundos
- Notificações push para alertas críticos
- Shortcuts de teclado para ações rápidas

### **Market Analysis**
- Drawings tools no gráfico
- Alertas de preço customizáveis
- Comparação entre múltiplos pares

### **Portfolio**
- Export de dados (CSV, PDF)
- Alerts para mudanças significativas
- Simulação de cenários

### **Trading**
- One-click trading
- Stop loss / Take profit automático
- Paper trading mode

## 📋 Checklist de Implementação

### **Fase 1: Setup & Estrutura**
- [ ] Configurar React + TypeScript + Vite
- [ ] Instalar dependências (UI lib, charts, HTTP client)
- [ ] Configurar roteamento
- [ ] Implementar sistema de autenticação
- [ ] Criar layout base com sidebar

### **Fase 2: Páginas Core**
- [ ] Dashboard com métricas principais
- [ ] Portfolio com tabela de ativos
- [ ] Trading com formulário de orders
- [ ] Market Analysis com gráficos básicos

### **Fase 3: Features Avançadas**
- [ ] WebSockets para dados real-time
- [ ] Charts interativos avançados
- [ ] Sistema de notificações
- [ ] Export de dados
- [ ] Mobile responsiveness

### **Fase 4: Polish & Deploy**
- [ ] Testes unitários
- [ ] Performance optimization
- [ ] Error handling robusto
- [ ] Deploy em produção

## 💡 Dicas de Implementação

1. **Inicie simples**: Comece com layouts básicos e adicione complexidade gradualmente
2. **Mock data**: Use dados mockados inicialmente para não depender da API
3. **Componentização**: Crie componentes reutilizáveis desde o início
4. **Type safety**: Use TypeScript rigorosamente para evitar bugs
5. **Real-time**: Implemente WebSockets apenas após ter a base funcionando

---

**🎯 Objetivo Final**: Um dashboard profissional, responsivo e funcional que permita monitorar e controlar completamente o sistema Robot-Crypt de trading de criptomoedas.
