import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Verificação de dependências
dashboard_available = True
missing_dependencies = []

try:
    import dash
except ImportError:
    dashboard_available = False
    missing_dependencies.append("dash")

try:
    from dash import dcc, html
    from dash.dependencies import Input, Output
except ImportError:
    dashboard_available = False
    missing_dependencies.append("dash components")

try:
    import plotly.graph_objs as go
    import plotly.express as px
except ImportError:
    dashboard_available = False
    missing_dependencies.append("plotly")

try:
    import pandas as pd
    import numpy as np
except ImportError:
    dashboard_available = False
    missing_dependencies.append("pandas/numpy")

if not dashboard_available:
    logger.warning(f"Dashboard não estará disponível. Dependências faltando: {', '.join(missing_dependencies)}")
    logger.warning("Instale as dependências com: pip install dash dash-core-components dash-html-components dash-table plotly pandas numpy")

from .performance_metrics import PerformanceMetrics

class RobotCryptDashboard:
    """
    Classe principal para o dashboard do Robot-Crypt que encapsula toda a 
    funcionalidade de visualização e monitoramento
    """
    
    def __init__(self, db=None, config=None, port=8050, host='0.0.0.0', external_data=None):
        """
        Inicializa o dashboard do Robot-Crypt
        
        Args:
            db: Instância do gerenciador de banco de dados
            config: Instância da configuração
            port: Porta onde o dashboard será servido (default: 8050)
            host: Host onde o dashboard será servido (default: '0.0.0.0')
            external_data: Instância do analisador de dados externos
        """
        self.port = port
        self.host = host
        self.db = db
        self.config = config
        self.external_data = external_data
        self.dashboard_thread = None
        self.available = dashboard_available
        
        if not dashboard_available:
            logger.warning(f"Dashboard não disponível. Dependências faltando: {', '.join(missing_dependencies)}")
            logger.warning("Para habilitar o dashboard, instale as dependências com: pip install dash plotly pandas numpy")
            return
            
        try:
            self.app = dash.Dash(
                __name__, 
                title='Robot-Crypt Dashboard',
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
                update_title=None
            )
            self._setup_layout()
            self._setup_callbacks()
            
            # Em vez de usar before_first_request (removido nas versões recentes do Flask)
            # vamos executar a configuração do servidor diretamente
            with self.app.server.app_context():
                self._setup_server()
            logger.info("Dashboard inicializado com sucesso")
        except Exception as e:
            self.available = False
            logger.error(f"Erro ao inicializar dashboard: {str(e)}")
            logger.exception("Detalhes do erro:")
    
    def _setup_layout(self):
        """Configura o layout do dashboard"""
        self.app.layout = html.Div([
            # Cabeçalho
            html.Div([
                html.H1('Robot-Crypt - Dashboard de Monitoramento', className='dashboard-title'),
                html.Div([
                    html.Span('Última atualização: ', className='update-label'),
                    html.Span(id='last-update-time', className='update-time')
                ], className='update-info')
            ], className='header'),
            
            # Avisos de contexto e alertas
            html.Div([
                html.Div(id='market-context-alert', className='market-context-alert')
            ], className='alert-container'),
            
            # Linha de métricas principais (KPIs)
            html.Div([
                html.Div([
                    html.H3('Saldo Total'),
                    html.H2(id='total-balance', children='$0.00'),
                    html.P(id='balance-change', children='0%')
                ], className='metric-card'),
                
                html.Div([
                    html.H3('Taxa de Acerto'),
                    html.H2(id='win-rate', children='0%'),
                    html.P(id='trades-count', children='0 trades')
                ], className='metric-card'),
                
                html.Div([
                    html.H3('Lucro Médio'),
                    html.H2(id='avg-profit', children='0%'),
                    html.P(id='profit-vs-loss', children='P/L: 0')
                ], className='metric-card'),
                
                html.Div([
                    html.H3('Nível de Risco'),
                    html.H2(id='risk-level', children='Baixo'),
                    html.P(id='risk-factors', children='Fatores: 0')
                ], className='metric-card')
            ], className='metrics-row'),
            
            # Gráficos principais
            html.Div([
                # Gráfico de desempenho
                html.Div([
                    html.H3('Desempenho do Robô'),
                    dcc.Graph(id='performance-chart'),
                    dcc.RadioItems(
                        id='timeframe-selector',
                        options=[
                            {'label': '24 horas', 'value': '1D'},
                            {'label': '7 dias', 'value': '7D'},
                            {'label': '30 dias', 'value': '30D'},
                            {'label': 'Todos', 'value': 'ALL'}
                        ],
                        value='7D',
                        className='radio-items'
                    )
                ], className='chart-container'),
                
                # Gráfico de operações
                html.Div([
                    html.H3('Operações Recentes'),
                    dcc.Graph(id='trades-chart')
                ], className='chart-container')
            ], className='charts-row'),
            
            # Segunda linha de gráficos
            html.Div([
                # Análise contextual
                html.Div([
                    html.H3('Análise Contextual'),
                    dcc.Graph(id='context-impact-chart'),
                    html.Div(id='news-alerts', className='alerts-container')
                ], className='chart-container'),
                
                # Ajustes de risco
                html.Div([
                    html.H3('Parâmetros Adaptativos'),
                    dcc.Graph(id='risk-params-chart')
                ], className='chart-container')
            ], className='charts-row'),
            
            # Atualização automática
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # atualiza a cada minuto (60 * 1000 milissegundos)
                n_intervals=0
            )
        ])
    
    def _setup_callbacks(self):
        """Configura os callbacks do dashboard"""
        @self.app.callback(
            [Output('last-update-time', 'children'),
             Output('total-balance', 'children'),
             Output('balance-change', 'children'),
             Output('win-rate', 'children'),
             Output('trades-count', 'children'),
             Output('avg-profit', 'children'),
             Output('profit-vs-loss', 'children'),
             Output('risk-level', 'children'),
             Output('risk-factors', 'children'),
             Output('performance-chart', 'figure'),
             Output('trades-chart', 'figure'),
             Output('context-impact-chart', 'figure'),
             Output('risk-params-chart', 'figure'),
             Output('news-alerts', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('timeframe-selector', 'value')]
        )
        def update_dashboard(n_intervals, timeframe):
            # Em produção, estes dados viriam da API do robô ou banco de dados
            data = self._load_sample_data()
            
            # Atualiza a hora
            last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Filtra os dados conforme o timeframe selecionado
            if timeframe == '1D':
                cutoff_date = datetime.now() - timedelta(days=1)
            elif timeframe == '7D':
                cutoff_date = datetime.now() - timedelta(days=7)
            elif timeframe == '30D':
                cutoff_date = datetime.now() - timedelta(days=30)
            else:  # ALL
                cutoff_date = datetime.min
            
            # Filtra os dados de balanço
            balance_df = data['balance_history']
            filtered_balance = balance_df[balance_df['timestamp'] >= cutoff_date]
            
            # Métricas de desempenho
            metrics = PerformanceMetrics(data['trades'])
            
            # Prepara os valores para exibição
            current_balance = filtered_balance['balance'].iloc[-1]
            balance_start = filtered_balance['balance'].iloc[0]
            balance_change_pct = ((current_balance - balance_start) / balance_start) * 100
            
            win_rate = metrics.get_win_rate() * 100
            trades_count = len(data['trades'])
            avg_profit = metrics.get_average_profit() * 100
            profit_loss_ratio = metrics.get_profit_loss_ratio()
            
            # Determina o nível de risco atual
            risk_level = 'Médio'  # Seria calculado com base em vários fatores
            risk_factors = 'Volatilidade, Notícias'  # Exemplo
            
            # Gráficos
            
            # 1. Gráfico de desempenho
            performance_fig = px.line(
                filtered_balance, 
                x='timestamp', 
                y='balance',
                title='Evolução do Saldo',
                labels={'timestamp': 'Data', 'balance': 'Saldo ($)'}
            )
            performance_fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="",
                yaxis_title=""
            )
            
            # 2. Gráfico de trades
            trades_df = pd.DataFrame(data['trades'])
            trades_df = trades_df[trades_df['timestamp'] >= cutoff_date]
            
            # Cria um gráfico de dispersão para os trades
            trades_fig = go.Figure()
            
            # Adiciona trades lucrativos (verde)
            profitable_trades = trades_df[trades_df['is_profit'] == True]
            if not profitable_trades.empty:
                trades_fig.add_trace(go.Scatter(
                    x=profitable_trades['timestamp'],
                    y=profitable_trades['profit_pct'] * 100,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color='green',
                        symbol='circle'
                    ),
                    name='Lucro'
                ))
            
            # Adiciona trades com prejuízo (vermelho)
            loss_trades = trades_df[trades_df['is_profit'] == False]
            if not loss_trades.empty:
                trades_fig.add_trace(go.Scatter(
                    x=loss_trades['timestamp'],
                    y=loss_trades['profit_pct'] * 100,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color='red',
                        symbol='circle'
                    ),
                    name='Prejuízo'
                ))
            
            trades_fig.update_layout(
                title='Resultados dos Trades',
                xaxis_title='Data',
                yaxis_title='Resultado (%)',
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 3. Gráfico de impacto contextual
            context_df = pd.DataFrame(data['context_history'])
            context_df = context_df[context_df['timestamp'] >= cutoff_date]
            
            context_fig = go.Figure()
            if not context_df.empty:
                context_fig.add_trace(go.Scatter(
                    x=context_df['timestamp'],
                    y=context_df['sentiment_score'],
                    mode='lines+markers',
                    name='Sentimento',
                    line=dict(color='purple')
                ))
            
            context_fig.update_layout(
                title='Análise de Sentimento do Mercado',
                xaxis_title='Data',
                yaxis_title='Score de Sentimento',
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 4. Gráfico de parâmetros adaptativos
            params_df = pd.DataFrame(data['params_history'])
            params_df = params_df[params_df['timestamp'] >= cutoff_date]
            
            params_fig = go.Figure()
            if not params_df.empty:
                params_fig.add_trace(go.Scatter(
                    x=params_df['timestamp'],
                    y=params_df['stop_loss'] * 100,
                    mode='lines',
                    name='Stop Loss (%)',
                    line=dict(color='red')
                ))
                params_fig.add_trace(go.Scatter(
                    x=params_df['timestamp'],
                    y=params_df['take_profit'] * 100,
                    mode='lines',
                    name='Take Profit (%)',
                    line=dict(color='green')
                ))
                params_fig.add_trace(go.Scatter(
                    x=params_df['timestamp'],
                    y=params_df['position_size'] * 100,
                    mode='lines',
                    name='Tamanho da Posição (%)',
                    line=dict(color='blue')
                ))
            
            params_fig.update_layout(
                title='Evolução dos Parâmetros Adaptativos',
                xaxis_title='Data',
                yaxis_title='Valor (%)',
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # Gera alertas de notícias
            news_alerts = []
            if not context_df.empty:
                for i, alert in enumerate(context_df.sort_values('timestamp', ascending=False).head(3).to_dict('records')):
                    alert_class = 'alert-' + alert['alert_level']
                    news_alerts.append(html.Div([
                        html.H4(f"Alerta de Notícias - {alert['alert_level'].capitalize()}"),
                        html.P(f"Sentimento: {alert['sentiment_score']:.2f}"),
                        html.P(f"Impacto no mercado: {alert['market_impact']}")
                    ], className=f'alert-box {alert_class}'))
            
            # Formata os valores para exibição
            formatted_balance = f"${current_balance:.2f}"
            formatted_balance_change = f"{'+' if balance_change_pct >= 0 else ''}{balance_change_pct:.2f}%"
            formatted_win_rate = f"{win_rate:.1f}%"
            formatted_trades_count = f"{trades_count} trades"
            formatted_avg_profit = f"{'+' if avg_profit >= 0 else ''}{avg_profit:.2f}%"
            formatted_pl_ratio = f"P/L: {profit_loss_ratio:.2f}"
            
            return (
                last_update,
                formatted_balance,
                formatted_balance_change,
                formatted_win_rate,
                formatted_trades_count,
                formatted_avg_profit,
                formatted_pl_ratio,
                risk_level,
                risk_factors,
                performance_fig,
                trades_fig,
                context_fig,
                params_fig,
                news_alerts
            )
    
    def _load_sample_data(self):
        """
        Carrega dados de exemplo para fins de demonstração
        
        Em produção, este método seria substituído por uma conexão com 
        API ou banco de dados para obter dados reais
        """
        # Simula 30 dias de dados históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Dados de saldo
        base_balance = 10000
        random_changes = np.cumsum(np.random.normal(0.001, 0.01, size=len(dates)))
        balance_data = base_balance * (1 + random_changes)
        
        # Dados de trades
        num_trades = 120
        trade_timestamps = sorted(np.random.choice(dates, size=num_trades, replace=False))
        entry_prices = np.random.uniform(30000, 60000, size=num_trades)
        exit_prices = entry_prices * np.random.normal(1.01, 0.05, size=num_trades)
        is_profit = exit_prices > entry_prices
        
        trades = []
        for i in range(num_trades):
            trades.append({
                'timestamp': trade_timestamps[i],
                'entry_price': entry_prices[i],
                'exit_price': exit_prices[i],
                'profit_pct': (exit_prices[i] - entry_prices[i]) / entry_prices[i],
                'is_profit': is_profit[i],
                'asset': np.random.choice(['BTC', 'ETH', 'BNB', 'ADA']),
                'position_size': np.random.uniform(0.05, 0.2),
                'stop_loss': np.random.uniform(0.02, 0.08),
                'take_profit': np.random.uniform(0.05, 0.15)
            })
        
        # Dados de parâmetros adaptativos
        params_data = []
        for i in range(len(dates)):
            params_data.append({
                'timestamp': dates[i],
                'stop_loss': 0.05 + 0.02 * np.sin(i/20),
                'take_profit': 0.1 + 0.03 * np.sin(i/18),
                'position_size': 0.1 + 0.05 * np.sin(i/25)
            })
        
        # Dados de impacto contextual
        context_data = []
        for i in range(len(dates)):
            if i % 24 == 0:  # Adiciona dados diários
                context_data.append({
                    'timestamp': dates[i],
                    'sentiment_score': np.random.normal(0, 0.5),
                    'market_impact': np.random.choice(['baixo', 'médio', 'alto']),
                    'alert_level': np.random.choice(['baixo', 'médio', 'alto', 'crítico'], 
                                                  p=[0.7, 0.2, 0.08, 0.02])
                })
        
        return {
            'balance_history': pd.DataFrame({
                'timestamp': dates,
                'balance': balance_data
            }),
            'trades': trades,
            'params_history': params_data,
            'context_history': context_data
        }
    
    def _setup_server(self):
        """Configura o servidor Flask sem usar before_first_request"""
        try:
            # Realize aqui as configurações que seriam feitas no before_first_request
            logger.info("Configuração do servidor realizada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar servidor: {str(e)}")
            logger.exception("Detalhes do erro:")
    
    def start(self, debug=False):
        """
        Inicia o servidor do dashboard
        
        Args:
            debug: Flag para ativar modo de depuração (default: False)
        """
        # Verifica se o dashboard está disponível
        if not self.available:
            logger.warning("Não foi possível iniciar o dashboard porque as dependências necessárias não estão instaladas")
            logger.warning("Para habilitar o dashboard, instale: pip install dash plotly pandas numpy")
            return
            
        # Inicia em uma thread separada para não bloquear a execução principal
        self.start_in_thread()
        logger.info(f"Dashboard iniciado em thread separada na porta {self.port}")
    
    def start_in_thread(self):
        """Inicia o dashboard em uma thread separada"""
        # Verifica se o dashboard está disponível
        if not self.available:
            logger.warning("Dashboard não disponível devido à falta de dependências")
            return
            
        # Verifica se já está em execução
        if self.dashboard_thread and self.dashboard_thread.is_alive():
            logger.warning("Dashboard já está em execução")
            return
        
        def run_dashboard():
            try:
                logger.info(f"Iniciando servidor dashboard na porta {self.port}")
                self.app.run_server(debug=False, host=self.host, port=self.port, use_reloader=False)
            except Exception as e:
                logger.error(f"Erro ao iniciar dashboard: {e}")
                logger.exception("Detalhes do erro:")
        
        self.dashboard_thread = threading.Thread(target=run_dashboard)
        self.dashboard_thread.daemon = True
        self.dashboard_thread.start()
        logger.info(f"Dashboard iniciado em thread separada (http://{self.host}:{self.port})")
        
        return self.dashboard_thread
    
    def stop(self):
        """Para o servidor do dashboard"""
        # Nota: O Dash não tem um método clean para parar o servidor
        # Esta função seria implementada se estivéssemos usando Flask diretamente
        logger.info("Função stop chamada, mas o Dash não oferece um método direto para parar o servidor")
        # Em uma implementação real, poderíamos considerar o uso de um servidor WSGI como gunicorn
        # que permite o controle mais granular do ciclo de vida da aplicação
