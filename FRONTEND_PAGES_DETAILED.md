# 📄 Prompts Detalhados por Página - Robot-Crypt Dashboard

## 🏠 PÁGINA DASHBOARD - Prompt Específico

### **Objetivo**
Criar uma página de dashboard principal que forneça uma visão geral rápida e intuitiva do estado atual do sistema de trading.

### **Componentes Específicos**

#### 1. **MetricCard Component**
```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  loading?: boolean;
}

// Exemplos de uso:
<MetricCard 
  title="Total Balance" 
  value="$12,543.21" 
  change={4.5} 
  changeType="positive"
  icon={<DollarSignIcon />}
/>
```

#### 2. **PortfolioChart Component**
```typescript
interface PortfolioChartProps {
  data: Array<{
    date: string;
    value_usdt: number;
    value_brl: number;
  }>;
  timeRange: '24h' | '7d' | '30d' | '90d';
  onTimeRangeChange: (range: string) => void;
}
```

#### 3. **RecentTrades Component**
```typescript
interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  profit_loss: number;
  timestamp: string;
  status: 'completed' | 'pending' | 'failed';
}

interface RecentTradesProps {
  trades: Trade[];
  onViewAll: () => void;
}
```

### **Layout Responsivo**
```css
/* Desktop: Grid 4 colunas */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

/* Tablet: Grid 2 colunas */
@media (max-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile: 1 coluna */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
```

### **Dados Mock para Desenvolvimento**
```typescript
const mockDashboardData = {
  metrics: {
    totalBalance: { value: 12543.21, change: 4.5 },
    dailyPnL: { value: 234.56, change: 2.1 },
    totalTrades: { value: 127, change: 8 },
    winRate: { value: 68.5, change: -1.2 }
  },
  portfolioHistory: [
    { date: '2024-01-01', value_usdt: 12000, value_brl: 60000 },
    { date: '2024-01-02', value_usdt: 12200, value_brl: 61000 },
    // ... mais dados
  ],
  recentTrades: [
    {
      id: '1',
      symbol: 'BTC/USDT',
      side: 'buy',
      amount: 0.01,
      price: 43500,
      profit_loss: 45.50,
      timestamp: '2024-01-15T10:30:00Z',
      status: 'completed'
    }
  ]
};
```

---

## 📊 PÁGINA MARKET ANALYSIS - Prompt Específico

### **Objetivo**
Criar uma página de análise de mercado avançada com gráficos interativos e indicadores técnicos.

### **Componentes Específicos**

#### 1. **TradingChart Component**
```typescript
interface CandlestickData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradingChartProps {
  data: CandlestickData[];
  symbol: string;
  interval: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
  indicators: {
    ma?: { period: number; type: 'sma' | 'ema' };
    rsi?: { period: number };
    macd?: { fast: number; slow: number; signal: number };
    bollinger?: { period: number; stdDev: number };
  };
  onIntervalChange: (interval: string) => void;
}

// Usar biblioteca como Recharts ou Chart.js
// Exemplo com Recharts:
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
```

#### 2. **TechnicalIndicators Panel**
```typescript
interface IndicatorValue {
  name: string;
  value: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  description: string;
}

interface TechnicalIndicatorsProps {
  indicators: {
    rsi: IndicatorValue;
    macd: IndicatorValue;
    stochastic: IndicatorValue;
    williams_r: IndicatorValue;
  };
  symbol: string;
}

// Exemplo de renderização:
const IndicatorItem = ({ indicator }: { indicator: IndicatorValue }) => (
  <div className={`p-4 border rounded-lg ${
    indicator.signal === 'bullish' ? 'border-green-500' : 
    indicator.signal === 'bearish' ? 'border-red-500' : 
    'border-gray-300'
  }`}>
    <div className="flex justify-between items-center">
      <span className="font-medium">{indicator.name}</span>
      <span className="text-lg font-mono">{indicator.value.toFixed(2)}</span>
    </div>
    <p className="text-sm text-gray-600 mt-1">{indicator.description}</p>
  </div>
);
```

#### 3. **MarketSentiment Component**
```typescript
interface SentimentData {
  fear_greed_index: number;
  volume_24h_change: number;
  market_trend: 'bullish' | 'bearish' | 'sideways';
  volatility: number;
  social_sentiment: number;
}

// Gauge chart para Fear & Greed Index
const FearGreedGauge = ({ value }: { value: number }) => {
  const getColor = (val: number) => {
    if (val <= 20) return '#EF4444'; // Extreme Fear
    if (val <= 40) return '#F59E0B'; // Fear
    if (val <= 60) return '#6B7280'; // Neutral
    if (val <= 80) return '#84CC16'; // Greed
    return '#10B981'; // Extreme Greed
  };

  return (
    <div className="relative w-32 h-32">
      {/* Implementar gauge visual */}
    </div>
  );
};
```

#### 4. **NewsFeed Component**
```typescript
interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  impact: 'high' | 'medium' | 'low';
  sentiment: 'positive' | 'negative' | 'neutral';
  related_symbols: string[];
}

interface NewsFeedProps {
  news: NewsItem[];
  onNewsClick: (newsId: string) => void;
}
```

### **Dados Mock para Market Analysis**
```typescript
const mockMarketData = {
  ohlcv: [
    { timestamp: 1640995200000, open: 42000, high: 43500, low: 41800, close: 43200, volume: 1234567 },
    // ... mais dados
  ],
  indicators: {
    rsi: { name: 'RSI (14)', value: 45.2, signal: 'neutral', description: 'Momentum neutro' },
    macd: { name: 'MACD', value: 0.025, signal: 'bullish', description: 'Sinal de alta' }
  },
  sentiment: {
    fear_greed_index: 32,
    volume_24h_change: 15.4,
    market_trend: 'sideways',
    volatility: 2.8,
    social_sentiment: 0.6
  }
};
```

---

## 💼 PÁGINA PORTFOLIO - Prompt Específico

### **Objetivo**
Criar uma página completa de gestão de portfólio com visão detalhada dos ativos e performance.

### **Componentes Específicos**

#### 1. **AssetAllocation Component (Pie Chart)**
```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface AllocationData {
  asset: string;
  value: number;
  percentage: number;
  color: string;
}

const AssetAllocation = ({ data }: { data: AllocationData[] }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={100}
          dataKey="percentage"
          label={({ asset, percentage }) => `${asset}: ${percentage.toFixed(1)}%`}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => [`${value.toFixed(2)}%`, 'Allocation']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};
```

#### 2. **AssetsTable Component**
```typescript
interface AssetHolding {
  asset: string;
  amount: number;
  value_usdt: number;
  value_brl: number;
  percentage: number;
  pnl_24h: number;
  pnl_24h_percent: number;
  avg_buy_price: number;
  current_price: number;
}

const AssetsTable = ({ assets }: { assets: AssetHolding[] }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Asset
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Amount
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Value (USDT)
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              % Portfolio
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              24h P&L
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {assets.map((asset) => (
            <tr key={asset.asset} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <img 
                    src={`/icons/${asset.asset.toLowerCase()}.png`} 
                    alt={asset.asset}
                    className="w-8 h-8 mr-3"
                  />
                  <span className="font-medium">{asset.asset}</span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap font-mono">
                {asset.amount.toFixed(6)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap font-mono">
                ${asset.value_usdt.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {asset.percentage.toFixed(1)}%
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`font-medium ${
                  asset.pnl_24h >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {asset.pnl_24h >= 0 ? '+' : ''}${asset.pnl_24h.toFixed(2)} 
                  ({asset.pnl_24h_percent >= 0 ? '+' : ''}{asset.pnl_24h_percent.toFixed(2)}%)
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### 3. **PerformanceMetrics Component**
```typescript
interface PerformanceData {
  total_return: number;
  total_return_percent: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
}

const PerformanceMetrics = ({ data }: { data: PerformanceData }) => {
  const metrics = [
    { label: 'Total Return', value: `$${data.total_return.toFixed(2)}`, subValue: `${data.total_return_percent.toFixed(2)}%` },
    { label: 'Max Drawdown', value: `$${data.max_drawdown.toFixed(2)}`, subValue: `${data.max_drawdown_percent.toFixed(2)}%` },
    { label: 'Sharpe Ratio', value: data.sharpe_ratio.toFixed(2), subValue: null },
    { label: 'Win Rate', value: `${data.win_rate.toFixed(1)}%`, subValue: null },
    { label: 'Profit Factor', value: data.profit_factor.toFixed(2), subValue: null },
    { label: 'Avg Win', value: `$${data.avg_win.toFixed(2)}`, subValue: null },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {metrics.map((metric) => (
        <div key={metric.label} className="p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-600">{metric.label}</h4>
          <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
          {metric.subValue && (
            <p className="text-sm text-gray-500">{metric.subValue}</p>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## 📈 PÁGINA TRADING - Prompt Específico

### **Objetivo**
Criar uma página de trading com interface para executar operações e monitorar posições ativas.

### **Componentes Específicos**

#### 1. **OrderForm Component**
```typescript
interface OrderFormProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  onOrderSubmit: (order: OrderData) => void;
  availableBalance: number;
  currentPrice: number;
}

interface OrderData {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  amount: number;
  price?: number;
  stopPrice?: number;
}

const OrderForm = ({ symbol, onOrderSubmit, availableBalance, currentPrice }: OrderFormProps) => {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [type, setType] = useState<'market' | 'limit'>('market');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>(currentPrice.toString());

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Place Order</h3>
      
      {/* Side Selector */}
      <div className="flex space-x-2 mb-4">
        <button
          onClick={() => setSide('buy')}
          className={`flex-1 py-2 px-4 rounded ${
            side === 'buy' ? 'bg-green-500 text-white' : 'bg-gray-200'
          }`}
        >
          Buy
        </button>
        <button
          onClick={() => setSide('sell')}
          className={`flex-1 py-2 px-4 rounded ${
            side === 'sell' ? 'bg-red-500 text-white' : 'bg-gray-200'
          }`}
        >
          Sell
        </button>
      </div>

      {/* Type Selector */}
      <div className="mb-4">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as 'market' | 'limit')}
          className="w-full p-2 border rounded"
        >
          <option value="market">Market</option>
          <option value="limit">Limit</option>
        </select>
      </div>

      {/* Amount Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Amount</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full p-2 border rounded"
          placeholder="0.00"
        />
        <p className="text-xs text-gray-500 mt-1">
          Available: {availableBalance.toFixed(2)} USDT
        </p>
      </div>

      {/* Price Input (for limit orders) */}
      {type === 'limit' && (
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Price</label>
          <input
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="0.00"
          />
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={() => onOrderSubmit({
          symbol,
          side,
          type,
          amount: parseFloat(amount),
          price: type === 'limit' ? parseFloat(price) : undefined
        })}
        className={`w-full py-3 px-4 rounded font-medium ${
          side === 'buy' 
            ? 'bg-green-500 hover:bg-green-600 text-white' 
            : 'bg-red-500 hover:bg-red-600 text-white'
        }`}
      >
        {side === 'buy' ? 'Buy' : 'Sell'} {symbol}
      </button>
    </div>
  );
};
```

#### 2. **ActivePositions Component**
```typescript
interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  amount: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  stop_loss?: number;
  take_profit?: number;
  timestamp: string;
}

const ActivePositions = ({ positions, onClosePosition }: {
  positions: Position[];
  onClosePosition: (positionId: string) => void;
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entry</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">P&L</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {positions.map((position) => (
            <tr key={position.id}>
              <td className="px-6 py-4 whitespace-nowrap font-medium">{position.symbol}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs rounded ${
                  position.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {position.side.toUpperCase()}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap font-mono">{position.amount}</td>
              <td className="px-6 py-4 whitespace-nowrap font-mono">${position.entry_price.toFixed(2)}</td>
              <td className="px-6 py-4 whitespace-nowrap font-mono">${position.current_price.toFixed(2)}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                  <br />
                  <span className="text-sm">
                    ({position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%)
                  </span>
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <button
                  onClick={() => onClosePosition(position.id)}
                  className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                >
                  Close
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### 3. **TradingLogs Component**
```typescript
interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  details?: any;
}

const TradingLogs = ({ logs }: { logs: LogEntry[] }) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-black text-green-400 p-4 rounded-lg h-64 overflow-y-auto font-mono text-sm">
      {logs.map((log) => (
        <div key={log.id} className="mb-1">
          <span className="text-gray-400">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
          <span className={`ml-2 ${getLevelColor(log.level)}`}>
            {log.level.toUpperCase()}
          </span>
          <span className="ml-2">{log.message}</span>
        </div>
      ))}
    </div>
  );
};
```

### **WebSocket Integration para Trading**
```typescript
// Hook para WebSocket de trading
const useTradingWebSocket = () => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/trading');
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Processar diferentes tipos de mensagens
      switch (data.type) {
        case 'price_update':
          // Atualizar preços
          break;
        case 'trade_executed':
          // Atualizar trades
          break;
        case 'position_update':
          // Atualizar posições
          break;
      }
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setSocket(null);
    };

    return () => {
      ws.close();
    };
  }, []);

  return { socket, connectionStatus };
};
```

## 🚀 Script de Inicialização

Aqui está um script bash para inicializar rapidamente o projeto:

```bash
#!/bin/bash
# setup-dashboard.sh

echo "🚀 Configurando Robot-Crypt Dashboard..."

# Criar projeto React com TypeScript
npx create-react-app robot-crypt-dashboard --template typescript
cd robot-crypt-dashboard

# Instalar dependências principais
npm install \
  @types/react @types/react-dom \
  tailwindcss autoprefixer postcss \
  @headlessui/react @heroicons/react \
  recharts \
  axios \
  react-router-dom \
  @types/react-router-dom \
  zustand \
  react-query \
  date-fns

# Instalar dependências de desenvolvimento
npm install -D \
  @types/node \
  prettier \
  eslint

# Configurar Tailwind CSS
npx tailwindcss init -p

echo "✅ Projeto configurado! Execute 'npm start' para iniciar."
```

---

Este prompt detalhado fornece tudo o que é necessário para implementar cada página do dashboard com componentes específicos, mock data, e estruturas TypeScript bem definidas.
