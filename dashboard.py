#!/usr/bin/env python3
"""
Módulo para dashboard visual de monitoramento do Robot-Crypt
Implementa interface gráfica com métricas em tempo real usando Plotly e Dash
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import threading
import socket
import flask

from config import Config
from db_manager import DBManager
from utils import setup_logger


class RobotCryptDashboard:
    """
    Dashboard para monitoramento em tempo real do Robot-Crypt
    Fornece visualizações gráficas de desempenho, operações e configurações
    """

    def __init__(self, db_manager, config=None, port=8050, debug=False, external_data=None):
        """
        Inicializa o dashboard do Robot-Crypt
        
        Args:
            db_manager: Instância do DBManager para acessar dados históricos
            config: Configuração do bot (opcional)
            port: Porta para o servidor web do dashboard
            debug: Modo de debug para o Dash
            external_data: Analisador de dados externos (opcional)
        """
        self.db_manager = db_manager
        self.config = config if config else Config()
        self.logger = logging.getLogger("robot-crypt")
        self.port = self._find_available_port(port)
        self.debug = debug
        self.external_data = external_data
        
        # Estado do robô
        self.robot_state = {'running': False, 'last_update': None}
        self.capital_history = []
        self.operations_history = []
        self.risk_metrics = {}
        
        # Configuração do tema
        self.colors = {
            'background': '#0e1726',
            'text': '#e0e0e0',
            'gain': '#26a69a',
            'loss': '#ef5350',
            'neutral': '#9e9e9e',
            'card_bg': '#1a273e',
            'border': '#2c3958',
            'panel_bg': '#131f39',
            'header': '#2196f3'
        }
        
        # Intervalo de atualização
        self.update_interval_seconds = 30
        
        # Inicialização da aplicação Dash
        self.app = self._setup_dash_app()
        
        # Servidor está rodando
        self.is_running = False
        self.server_thread = None
        
        # Diretório para cache de dados
        self.cache_dir = Path(__file__).parent / "data"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.dashboard_cache = self.cache_dir / "dashboard_cache.json"
        
        # Última vez que os dados foram atualizados
        self.last_data_update = datetime.now() - timedelta(minutes=10)

    def _find_available_port(self, start_port):
        """
        Encontra uma porta disponível para o dashboard
        
        Args:
            start_port: Porta inicial a verificar
            
        Returns:
            int: Porta disponível
        """
        port = start_port
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                # Tenta criar um socket na porta
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    # Porta está disponível
                    return port
            except socket.error:
                # Porta já está em uso, tenta a próxima
                self.logger.info(f"Porta {port} já está em uso, tentando a próxima")
                port += 1
        
        # Se não encontrar porta disponível, usa a original
        self.logger.warning(f"Não foi possível encontrar porta disponível após {max_attempts} tentativas")
        return start_port

    def _setup_dash_app(self):
        """
        Configura a aplicação Dash com layout e callbacks
        
        Returns:
            dash.Dash: Aplicação Dash configurada
        """
        # Meta tags para responsividade
        meta_tags = [
            {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
        ]
        
        # Instanciar aplicação Dash
        app = dash.Dash(
            __name__, 
            meta_tags=meta_tags,
            assets_folder=os.path.join(os.path.dirname(__file__), 'assets'),
            title="Robot-Crypt Dashboard"
        )
        
        # Configurar layout
        app.layout = self._create_layout()
        
        # Configurar callbacks
        self._setup_callbacks(app)
        
        return app
        
    def _create_layout(self):
        """
        Cria o layout do dashboard
        
        Returns:
            html.Div: Layout completo do dashboard
        """
        return html.Div(
            style={
                'backgroundColor': self.colors['background'],
                'color': self.colors['text'],
                'minHeight': '100vh',
                'fontFamily': 'Roboto, Arial, sans-serif'
            },
            children=[
                # Header
                html.Div(
                    style={
                        'backgroundColor': self.colors['panel_bg'],
                        'padding': '10px 15px',
                        'borderBottom': f'1px solid {self.colors["border"]}',
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center'
                    },
                    children=[
                        html.H1("Robot-Crypt Dashboard", style={'margin': '0', 'fontSize': '24px'}),
                        html.Div([
                            html.Span("Status: ", style={'marginRight': '5px'}),
                            html.Span(
                                id='robot-status',
                                children="Verificando...",
                                style={
                                    'backgroundColor': '#FFB74D',
                                    'color': '#000',
                                    'padding': '3px 8px',
                                    'borderRadius': '4px',
                                    'fontWeight': 'bold'
                                }
                            )
                        ])
                    ]
                ),
                
                # Main content container
                html.Div(
                    style={'padding': '20px'},
                    children=[
                        # Top KPI Cards Row
                        html.Div(
                            style={
                                'display': 'grid', 
                                'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 
                                'gap': '15px',
                                'marginBottom': '20px'
                            },
                            children=[
                                # Capital atual
                                self._create_kpi_card('Capital Atual', 'current-capital', 'R$ 0.00'),
                                # Lucro total
                                self._create_kpi_card('Lucro Total', 'total-profit', 'R$ 0.00', is_profit=True),
                                # Taxa de acerto
                                self._create_kpi_card('Taxa de Acerto', 'win-rate', '0%'),
                                # Trades hoje
                                self._create_kpi_card('Trades Hoje', 'trades-today', '0'),
                                # Risco atual
                                self._create_kpi_card('Nível de Risco', 'risk-level', 'Normal')
                            ]
                        ),
                        
                        # Gráficos principais
                        html.Div(
                            style={
                                'display': 'grid',
                                'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
                                'gap': '20px',
                                'marginBottom': '20px'
                            },
                            children=[
                                # Gráfico de evolução do capital
                                self._create_panel(
                                    "Evolução do Capital",
                                    dcc.Graph(id='capital-chart', style={'height': '350px'})
                                ),
                                
                                # Gráfico de operações
                                self._create_panel(
                                    "Operações Recentes",
                                    dcc.Graph(id='operations-chart', style={'height': '350px'})
                                )
                            ]
                        ),
                        
                        # Terceira linha - Fatores externos e métricas de risco
                        html.Div(
                            style={
                                'display': 'grid',
                                'gridTemplateColumns': 'repeat(auto-fit, minmax(400px, 1fr))',
                                'gap': '20px',
                                'marginBottom': '20px'
                            },
                            children=[
                                # Fatores externos
                                self._create_panel(
                                    "Fatores Externos",
                                    dcc.Graph(id='external-factors-chart', style={'height': '300px'})
                                ),
                                
                                # Métricas de risco
                                self._create_panel(
                                    "Métricas de Risco",
                                    dcc.Graph(id='risk-metrics-chart', style={'height': '300px'})
                                )
                            ]
                        ),
                        
                        # Quarta linha - Tabela de operações e notícias
                        html.Div(
                            style={
                                'display': 'grid',
                                'gridTemplateColumns': 'repeat(auto-fit, minmax(450px, 1fr))',
                                'gap': '20px'
                            },
                            children=[
                                # Tabela de operações
                                self._create_panel(
                                    "Últimas Operações",
                                    html.Div(id='operations-table', style={'overflowX': 'auto'})
                                ),
                                
                                # Eventos e notícias
                                self._create_panel(
                                    "Notícias Relevantes",
                                    html.Div(id='news-feed')
                                )
                            ]
                        ),
                        
                        # Seção de dados contextuais externos
                        self._create_external_data_section(),
                        
                        # Análise adaptativa de risco
                        self._create_risk_analysis_section(),
                        
                        # Armazenar dados em intervalos
                        dcc.Interval(
                            id='interval-component',
                            interval=self.update_interval_seconds * 1000,  # milissegundos
                            n_intervals=0
                        )
                    ]
                )
            ]
        )

    def _create_kpi_card(self, title, id_prefix, default_value, is_profit=False):
        """
        Cria um card de KPI para o dashboard
        
        Args:
            title (str): Título do card
            id_prefix (str): Prefixo para o ID dos elementos
            default_value (str): Valor padrão
            is_profit (bool): Se é um indicador de lucro
            
        Returns:
            html.Div: Card de KPI
        """
        return html.Div(
            style={
                'backgroundColor': self.colors['card_bg'],
                'borderRadius': '8px',
                'padding': '15px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'border': f'1px solid {self.colors["border"]}'
            },
            children=[
                html.H3(
                    title,
                    style={'margin': '0 0 10px 0', 'fontSize': '16px', 'color': self.colors['text']}
                ),
                html.Div(
                    default_value,
                    id=id_prefix,
                    style={
                        'fontSize': '24px',
                        'fontWeight': 'bold',
                        'color': self.colors['text']
                    }
                ),
                html.Div(
                    id=f"{id_prefix}-change",
                    style={
                        'fontSize': '12px',
                        'marginTop': '5px',
                        'display': 'none' if not is_profit else 'block'
                    }
                )
            ]
        )

    def _create_panel(self, title, content):
        """
        Cria um painel para conteúdo do dashboard
        
        Args:
            title (str): Título do painel
            content: Conteúdo do painel
            
        Returns:
            html.Div: Painel completo
        """
        return html.Div(
            style={
                'backgroundColor': self.colors['panel_bg'],
                'borderRadius': '8px',
                'border': f'1px solid {self.colors["border"]}',
                'overflow': 'hidden'
            },
            children=[
                html.Div(
                    title,
                    style={
                        'backgroundColor': self.colors['card_bg'],
                        'padding': '12px 15px',
                        'borderBottom': f'1px solid {self.colors["border"]}',
                        'fontWeight': 'bold',
                        'fontSize': '16px'
                    }
                ),
                html.Div(
                    content,
                    style={'padding': '15px'}
                )
            ]
        )

    def _create_external_data_section(self):
        """
        Cria a seção de dados contextuais externos no dashboard
        
        Returns:
            html.Div: Componente Dash com visualização de dados contextuais
        """
        return html.Div([
            html.H3("Dados Contextuais Externos", className="dashboard-section-title"),
            html.Div([
                html.Div([
                    html.H4("Sentimento de Mercado", className="card-title"),
                    html.Div(id="market-sentiment-gauge", className="sentiment-gauge"),
                    html.Div(id="sentiment-score-value", className="sentiment-value")
                ], className="dashboard-card"),
                
                html.Div([
                    html.H4("Notícias Recentes de Impacto", className="card-title"),
                    html.Div(id="impact-news-container", className="news-container"),
                ], className="dashboard-card"),
                
                html.Div([
                    html.H4("Eventos Macroeconômicos", className="card-title"),
                    html.Div(id="macro-events-container", className="events-container"),
                ], className="dashboard-card")
            ], className="card-container")
        ], className="dashboard-section")

    def _create_risk_analysis_section(self):
        """
        Cria a seção de análise adaptativa de risco no dashboard
        
        Returns:
            html.Div: Componente Dash com visualização de análise de risco
        """
        return html.Div([
            html.H3("Análise Adaptativa de Risco", className="dashboard-section-title"),
            html.Div([
                html.Div([
                    html.H4("Ajuste Dinâmico de Parâmetros", className="card-title"),
                    dcc.Graph(id="risk-params-chart", config={"displayModeBar": False}),
                ], className="dashboard-card"),
                
                html.Div([
                    html.H4("Risco x Retorno", className="card-title"),
                    dcc.Graph(id="risk-reward-chart", config={"displayModeBar": False}),
                ], className="dashboard-card"),
                
                html.Div([
                    html.H4("Volatilidade do Mercado", className="card-title"),
                    dcc.Graph(id="market-volatility-chart", config={"displayModeBar": False}),
                ], className="dashboard-card")
            ], className="card-container")
        ], className="dashboard-section")

    def _setup_callbacks(self, app):
        """
        Configura os callbacks da aplicação Dash
        
        Args:
            app: Aplicação Dash
        """
        # Callback para atualizar dados periodicamente
        @app.callback(
            [
                Output('current-capital', 'children'),
                Output('total-profit', 'children'),
                Output('total-profit-change', 'children'),
                Output('total-profit-change', 'style'),
                Output('win-rate', 'children'),
                Output('trades-today', 'children'),
                Output('risk-level', 'children'),
                Output('risk-level', 'style'),
                Output('robot-status', 'children'),
                Output('robot-status', 'style'),
                Output('capital-chart', 'figure'),
                Output('operations-chart', 'figure'),
                Output('operations-table', 'children'),
                Output('news-feed', 'children'),
                Output('external-factors-chart', 'figure'),
                Output('risk-metrics-chart', 'figure')
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n_intervals):
            """Atualiza todos os componentes do dashboard"""
            # Verificar se é necessário atualizar os dados
            current_time = datetime.now()
            if (current_time - self.last_data_update).total_seconds() > self.update_interval_seconds or n_intervals == 0:
                self._update_dashboard_data()
                self.last_data_update = current_time
            
            # Capital atual
            capital = self._get_current_capital()
            capital_formatted = f"R$ {capital:.2f}"
            
            # Lucro total
            initial_capital = self.config.initial_capital if hasattr(self.config, 'initial_capital') else 100.0
            profit = capital - initial_capital
            profit_formatted = f"R$ {profit:.2f}"
            
            # Mudança percentual
            if initial_capital > 0:
                profit_percentage = (profit / initial_capital) * 100
                profit_change = f"{profit_percentage:+.2f}%"
                profit_color = self.colors['gain'] if profit >= 0 else self.colors['loss']
            else:
                profit_change = "N/A"
                profit_color = self.colors['neutral']
            
            # Taxa de acerto
            win_rate = self._calculate_win_rate()
            win_rate_formatted = f"{win_rate:.1f}%"
            
            # Trades hoje
            trades_today = self._get_trades_today()
            
            # Nível de risco
            risk_level, risk_style = self._get_risk_level()
            
            # Status do robô
            status, status_style = self._get_robot_status()
            
            # Gráficos e tabelas
            capital_chart = self._create_capital_chart()
            operations_chart = self._create_operations_chart()
            operations_table = self._create_operations_table()
            news_feed = self._create_news_feed()
            external_factors_chart = self._create_external_factors_chart()
            risk_metrics_chart = self._create_risk_metrics_chart()
            
            return (
                capital_formatted,
                profit_formatted,
                profit_change,
                {'fontSize': '12px', 'marginTop': '5px', 'color': profit_color},
                win_rate_formatted,
                f"{trades_today}",
                risk_level,
                {'fontSize': '24px', 'fontWeight': 'bold', 'color': risk_style},
                status,
                status_style,
                capital_chart,
                operations_chart,
                operations_table,
                news_feed,
                external_factors_chart,
                risk_metrics_chart
            )

    def _update_dashboard_data(self):
        """Atualiza os dados para o dashboard"""
        try:
            self.logger.info("Atualizando dados do dashboard...")
            
            # Atualizar histórico de capital
            self._update_capital_history()
            
            # Atualizar histórico de operações
            self._update_operations_history()
            
            # Atualizar métricas de risco
            self._update_risk_metrics()
            
            # Salvar cache
            self._save_dashboard_cache()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar dados do dashboard: {str(e)}")

    def _update_capital_history(self):
        """Atualiza histórico de capital"""
        try:
            # Buscar dados do banco de dados
            stats = self.db_manager.get_stats_history(30)  # últimos 30 dias
            
            if stats:
                self.capital_history = [
                    {
                        'date': datetime.strptime(stat['date'], '%Y-%m-%d') if isinstance(stat['date'], str) else stat['date'],
                        'capital': stat['final_capital'],
                        'initial_capital': stat['initial_capital']
                    }
                    for stat in stats
                ]
                
            else:
                # Se não houver dados, usar valores simulados
                self.logger.warning("Sem dados de capital no banco de dados, usando valores iniciais")
                today = datetime.now().date()
                initial_capital = self.config.initial_capital if hasattr(self.config, 'initial_capital') else 100.0
                
                self.capital_history = [
                    {
                        'date': today - timedelta(days=0),
                        'capital': initial_capital,
                        'initial_capital': initial_capital
                    }
                ]
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar histórico de capital: {str(e)}")

    def _update_operations_history(self):
        """Atualiza histórico de operações"""
        try:
            # Buscar operações recentes
            operations = self.db_manager.get_recent_operations(50)  # últimas 50 operações
            
            if operations:
                self.operations_history = operations
            else:
                self.logger.warning("Sem operações no banco de dados")
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar histórico de operações: {str(e)}")

    def _update_risk_metrics(self):
        """Atualiza métricas de risco"""
        try:
            # Aqui você pode incluir métricas do seu gerenciador de risco adaptativo
            # Por enquanto, usamos métricas simuladas
            
            self.risk_metrics = {
                'current_risk_level': 'Moderado',
                'risk_adjustment': 0.9,
                'volatility': 5.8,
                'consecutive_losses': 0,
                'market_conditions': 'Normal',
                'external_sentiment': 0.2  # -1 a 1
            }
            
            # Se houver dados externos disponíveis
            if self.external_data:
                try:
                    # Obter dados de contexto do mercado para BTC (representativo)
                    context = self.external_data.calculate_market_context_score("BTC")
                    
                    if context:
                        self.risk_metrics['external_sentiment'] = context.get('market_context_score', 0)
                        self.risk_metrics['market_conditions'] = context.get('alert_level', 'Normal').capitalize()
                        
                        # Ajustar nível de risco baseado no contexto externo
                        sentiment = context.get('market_context_score', 0)
                        if sentiment < -0.5:
                            self.risk_metrics['current_risk_level'] = 'Alto'
                        elif sentiment < -0.2:
                            self.risk_metrics['current_risk_level'] = 'Elevado'
                        elif sentiment > 0.5:
                            self.risk_metrics['current_risk_level'] = 'Baixo'
                        elif sentiment > 0.2:
                            self.risk_metrics['current_risk_level'] = 'Reduzido'
                        
                except Exception as ex:
                    self.logger.error(f"Erro ao obter dados externos: {str(ex)}")
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar métricas de risco: {str(e)}")

    def _get_current_capital(self):
        """Obtém o capital atual"""
        if self.capital_history:
            # Ordenar por data e pegar o mais recente
            sorted_history = sorted(self.capital_history, key=lambda x: x['date'], reverse=True)
            return sorted_history[0]['capital']
        
        # Valor padrão
        return self.config.initial_capital if hasattr(self.config, 'initial_capital') else 100.0

    def _calculate_win_rate(self):
        """Calcula a taxa de acerto"""
        if not self.operations_history:
            return 0.0
            
        # Filtrar apenas operações de venda
        sells = [op for op in self.operations_history if op['operation_type'] == 'sell']
        
        if not sells:
            return 0.0
            
        # Contar operações lucrativas
        profitable = len([op for op in sells if op.get('profit_percent', 0) > 0])
        
        # Calcular taxa
        win_rate = (profitable / len(sells)) * 100
        
        return win_rate

    def _get_trades_today(self):
        """Obtém número de trades realizados hoje"""
        if not self.operations_history:
            return 0
            
        # Obter data de hoje
        today = datetime.now().date()
        
        # Contar operações de hoje
        today_operations = [
            op for op in self.operations_history 
            if isinstance(op.get('timestamp'), datetime) and op.get('timestamp').date() == today
        ]
        
        return len(today_operations)

    def _get_risk_level(self):
        """Obtém nível de risco atual e estilo correspondente"""
        risk_level = self.risk_metrics.get('current_risk_level', 'Moderado')
        
        # Definir cor com base no nível
        if risk_level in ['Alto', 'Elevado']:
            color = self.colors['loss']
        elif risk_level in ['Baixo', 'Reduzido']:
            color = self.colors['gain']
        else:
            color = self.colors['neutral']
            
        return risk_level, color

    def _get_robot_status(self):
        """Obtém status atual do robô"""
        # Verificar último ciclo
        last_state_timestamp = self.db_manager.get_last_app_state_timestamp()
        
        if last_state_timestamp:
            # Converter para datetime se for string
            if isinstance(last_state_timestamp, str):
                last_state_timestamp = datetime.fromisoformat(last_state_timestamp)
                
            time_diff = datetime.now() - last_state_timestamp
            
            if time_diff < timedelta(minutes=15):
                status = "Ativo"
                style = {
                    'backgroundColor': '#66BB6A',
                    'color': '#000',
                    'padding': '3px 8px',
                    'borderRadius': '4px',
                    'fontWeight': 'bold'
                }
            else:
                status = "Inativo"
                style = {
                    'backgroundColor': '#EF5350',
                    'color': '#000',
                    'padding': '3px 8px',
                    'borderRadius': '4px',
                    'fontWeight': 'bold'
                }
        else:
            status = "Desconhecido"
            style = {
                'backgroundColor': '#FFB74D',
                'color': '#000',
                'padding': '3px 8px',
                'borderRadius': '4px',
                'fontWeight': 'bold'
            }
            
        return status, style

    def _create_capital_chart(self):
        """Cria gráfico de evolução do capital"""
        if not self.capital_history or len(self.capital_history) < 1:
            # Retornar gráfico vazio
            return go.Figure().update_layout(
                title="Sem dados de capital suficientes",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
        # Ordenar por data
        df = pd.DataFrame(self.capital_history).sort_values('date')
        
        # Calcular mudança percentual
        if len(df) > 1:
            first_capital = df['capital'].iloc[0]
            df['change_pct'] = ((df['capital'] - first_capital) / first_capital) * 100
        else:
            df['change_pct'] = 0
        
        # Criar subplots com dois eixos Y
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adicionar linha de capital
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['capital'],
                mode='lines+markers',
                name='Capital (R$)',
                line=dict(color='#2196f3', width=3),
                marker=dict(size=6)
            ),
            secondary_y=False
        )
        
        # Adicionar linha de mudança percentual
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['change_pct'],
                mode='lines',
                name='% de Mudança',
                line=dict(color='#4CAF50', width=2, dash='dot')
            ),
            secondary_y=True
        )
        
        # Atualizar layout
        fig.update_layout(
            plot_bgcolor=self.colors['panel_bg'],
            paper_bgcolor=self.colors['panel_bg'],
            font=dict(color=self.colors['text']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=10, r=10, t=30, b=10),
            hovermode="x unified"
        )
        
        # Atualizar eixos
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='%d/%m'
        )
        
        fig.update_yaxes(
            title_text="Capital (R$)",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            secondary_y=False
        )
        
        fig.update_yaxes(
            title_text="% de Mudança",
            showgrid=False,
            secondary_y=True,
            ticksuffix="%"
        )
        
        return fig

    def _create_operations_chart(self):
        """Cria gráfico de operações recentes"""
        if not self.operations_history or len(self.operations_history) < 1:
            # Retornar gráfico vazio
            return go.Figure().update_layout(
                title="Sem operações registradas",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )
        
        # Filtrar vendas (que têm lucro/perda)
        sells = [op for op in self.operations_history if op['operation_type'] == 'sell']
        
        if not sells:
            # Retornar gráfico vazio
            return go.Figure().update_layout(
                title="Sem vendas registradas",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )
        
        # Converter para DataFrame
        df = pd.DataFrame(sells)
        
        # Certificar-se que timestamp é datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        # Definir cores baseadas no lucro
        colors = []
        for profit in df['profit_percent']:
            if profit > 0:
                colors.append(self.colors['gain'])
            else:
                colors.append(self.colors['loss'])
        
        # Criar gráfico
        fig = go.Figure()
        
        # Adicionar barras de lucro/perda
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['profit_percent'] * 100 if 'profit_percent' in df.columns else [0] * len(df),
                marker_color=colors,
                name='Lucro/Perda (%)',
                text=df['symbol'],
                hovertemplate='<b>%{text}</b><br>Data: %{x}<br>Lucro: %{y:.2f}%<extra></extra>'
            )
        )
        
        # Adicionar linha de lucro acumulado
        if 'profit_percent' in df.columns and len(df) > 1:
            cumulative = (1 + df['profit_percent']).cumprod() - 1
            cumulative = cumulative * 100  # Converter para percentual
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=cumulative,
                    mode='lines',
                    name='Lucro Acumulado (%)',
                    line=dict(color='#FFEB3B', width=2)
                )
            )
        
        # Atualizar layout
        fig.update_layout(
            plot_bgcolor=self.colors['panel_bg'],
            paper_bgcolor=self.colors['panel_bg'],
            font=dict(color=self.colors['text']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=10, r=10, t=30, b=10),
            barmode='relative'
        )
        
        # Atualizar eixos
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            tickformat='%d/%m %H:%M'
        )
        
        fig.update_yaxes(
            title_text="Lucro/Perda (%)",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            ticksuffix="%"
        )
        
        return fig

    def _create_operations_table(self):
        """Cria tabela de operações recentes"""
        if not self.operations_history or len(self.operations_history) < 1:
            return html.Div("Sem operações registradas")
        
        # Preparar dados para a tabela
        rows = []
        
        # Ordenar operações por timestamp, mais recentes primeiro
        sorted_ops = sorted(
            self.operations_history,
            key=lambda x: x.get('timestamp', datetime.now()),
            reverse=True
        )
        
        # Limitar a 10 operações
        for op in sorted_ops[:10]:
            # Formatar timestamp
            timestamp = op.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = None
            
            formatted_time = timestamp.strftime('%d/%m/%Y %H:%M') if timestamp else 'N/A'
            
            # Formatar lucro/perda
            profit_percent = op.get('profit_percent', None)
            if profit_percent is not None:
                profit_style = {
                    'color': self.colors['gain'] if profit_percent > 0 else self.colors['loss'],
                    'fontWeight': 'bold'
                }
                profit_text = f"{profit_percent * 100:+.2f}%"
            else:
                profit_style = {}
                profit_text = 'N/A'
            
            # Criar linha
            row = html.Tr([
                html.Td(formatted_time, style={'padding': '8px'}),
                html.Td(op.get('symbol', 'N/A'), style={'padding': '8px'}),
                html.Td(op.get('operation_type', 'N/A').capitalize(), style={'padding': '8px'}),
                html.Td(f"R$ {op.get('price', 0):.2f}", style={'padding': '8px'}),
                html.Td(profit_text, style={**{'padding': '8px'}, **profit_style})
            ])
            
            rows.append(row)
        
        # Criar tabela
        table = html.Table(
            [
                html.Thead(
                    html.Tr([
                        html.Th("Data/Hora", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': f'1px solid {self.colors["border"]}'}),
                        html.Th("Par", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': f'1px solid {self.colors["border"]}'}),
                        html.Th("Tipo", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': f'1px solid {self.colors["border"]}'}),
                        html.Th("Preço", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': f'1px solid {self.colors["border"]}'}),
                        html.Th("Lucro", style={'textAlign': 'left', 'padding': '8px', 'borderBottom': f'1px solid {self.colors["border"]}'})
                    ])
                ),
                html.Tbody(rows)
            ],
            style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'color': self.colors['text']
            }
        )
        
        return table

    def _create_news_feed(self):
        """Cria feed de notícias relevantes"""
        # Verificar se temos dados externos
        if not hasattr(self, 'external_data') or not self.external_data:
            return html.Div(
                "Feed de notícias não disponível - Módulo de dados externos não configurado.",
                style={'fontStyle': 'italic', 'color': self.colors['neutral']}
            )
            
        try:
            # Tentar obter notícias
            news = self.external_data.fetch_economic_news(days=1)
            
            if not news:
                return html.Div(
                    "Sem notícias recentes disponíveis.",
                    style={'fontStyle': 'italic', 'color': self.colors['neutral']}
                )
            
            # Limitar a 5 notícias
            news = news[:5]
            
            # Criar lista de notícias
            news_items = []
            for n in news:
                # Definir cor baseada no sentimento
                sentiment = n.get('sentiment', 0)
                if sentiment > 0.3:
                    sentiment_color = self.colors['gain']
                    sentiment_icon = "▲"
                elif sentiment < -0.3:
                    sentiment_color = self.colors['loss']
                    sentiment_icon = "▼"
                else:
                    sentiment_color = self.colors['neutral']
                    sentiment_icon = "■"
                
                # Formatando data
                pub_date = n.get('published_at', '')
                if pub_date:
                    try:
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        formatted_date = pub_date.strftime('%d/%m %H:%M')
                    except:
                        formatted_date = pub_date
                else:
                    formatted_date = "N/A"
                
                news_items.append(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        sentiment_icon,
                                        style={
                                            'color': sentiment_color,
                                            'marginRight': '8px',
                                            'fontWeight': 'bold'
                                        }
                                    ),
                                    html.Span(
                                        formatted_date,
                                        style={
                                            'color': self.colors['neutral'],
                                            'fontSize': '12px'
                                        }
                                    )
                                ],
                                style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'marginBottom': '5px'
                                }
                            ),
                            html.A(
                                n.get('title', 'Sem título'),
                                href=n.get('url', '#'),
                                target="_blank",
                                style={
                                    'color': self.colors['text'],
                                    'textDecoration': 'none',
                                    'fontWeight': 'bold',
                                    'display': 'block',
                                    'marginBottom': '5px'
                                }
                            ),
                            html.Div(
                                n.get('source', 'Fonte desconhecida'),
                                style={
                                    'fontSize': '12px',
                                    'color': self.colors['neutral'],
                                    'marginBottom': '5px'
                                }
                            )
                        ],
                        style={
                            'marginBottom': '15px',
                            'paddingBottom': '15px',
                            'borderBottom': f'1px solid {self.colors["border"]}',
                        }
                    )
                )
            
            return html.Div(news_items)
        
        except Exception as e:
            self.logger.error(f"Erro ao criar feed de notícias: {str(e)}")
            return html.Div(
                f"Erro ao carregar notícias: {str(e)}",
                style={'fontStyle': 'italic', 'color': self.colors['loss']}
            )

    def _create_external_factors_chart(self):
        """Cria gráfico de fatores externos"""
        # Verificar se temos dados externos
        if not hasattr(self, 'external_data') or not self.external_data:
            return go.Figure().update_layout(
                title="Módulo de dados externos não configurado",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
        try:
            # Tentar obter dados de contexto para BTC (como referência)
            context = self.external_data.calculate_market_context_score("BTC")
            
            if not context or 'economic_indicators' not in context:
                return go.Figure().update_layout(
                    title="Sem dados de fatores externos disponíveis",
                    plot_bgcolor=self.colors['panel_bg'],
                    paper_bgcolor=self.colors['panel_bg'],
                    font=dict(color=self.colors['text']),
                    margin=dict(l=10, r=10, t=30, b=10)
                )
            
            # Extrair indicadores
            indicators = context['economic_indicators']
            
            # Preparar dados para o gráfico
            labels = [
                'Sentimento',
                'Inflação',
                'Taxa de Juros',
                'Volatilidade',
                'Crescimento'
            ]
            
            values = [
                context['sentiment_score'],
                indicators['inflation_impact'],
                indicators['interest_rate_impact'],
                indicators['market_volatility_impact'],
                indicators['economic_growth_impact']
            ]
            
            # Cores baseadas no impacto (positivo ou negativo)
            colors = []
            for value in values:
                if value > 0:
                    colors.append(self.colors['gain'])
                elif value < 0:
                    colors.append(self.colors['loss'])
                else:
                    colors.append(self.colors['neutral'])
            
            # Criar figura
            fig = go.Figure()
            
            # Adicionar barras
            fig.add_trace(
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color=colors,
                    text=[f"{v:.2f}" for v in values],
                    textposition='auto',
                    hovertemplate='%{x}: %{y:.2f}<extra></extra>'
                )
            )
            
            # Adicionar linha de pontuação geral
            fig.add_shape(
                type="line",
                x0=-0.5,
                x1=4.5,
                y0=0,
                y1=0,
                line=dict(
                    color="white",
                    width=1,
                    dash="dot",
                )
            )
            
            # Atualizar layout
            fig.update_layout(
                title=f"Score de Contexto: {context['market_context_score']:.2f} ({context['alert_level'].capitalize()})",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title="",
                yaxis_title="Impacto (-1 a +1)",
                yaxis=dict(
                    range=[-1, 1]
                )
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Erro ao criar gráfico de fatores externos: {str(e)}")
            return go.Figure().update_layout(
                title=f"Erro ao carregar fatores externos: {str(e)}",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )

    def _create_risk_metrics_chart(self):
        """Cria gráfico de métricas de risco"""
        # Verificar se temos métricas de risco
        if not self.risk_metrics:
            return go.Figure().update_layout(
                title="Sem dados de risco disponíveis",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
        try:
            # Criar gráfico de gauge para nível de risco
            fig = go.Figure()
            
            # Determinar valor para o gauge baseado no nível de risco
            risk_level = self.risk_metrics.get('current_risk_level', 'Moderado')
            risk_value_map = {
                'Baixo': 0.2,
                'Reduzido': 0.35,
                'Moderado': 0.5,
                'Elevado': 0.65,
                'Alto': 0.8
            }
            risk_value = risk_value_map.get(risk_level, 0.5)
            
            # Adicionar gauge
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=risk_value * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': self.colors['text']},
                        'bar': {'color': "#4CAF50" if risk_value < 0.4 else "#FFB74D" if risk_value < 0.6 else "#EF5350"},
                        'bgcolor': 'rgba(255,255,255,0.1)',
                        'borderwidth': 0,
                        'steps': [
                            {'range': [0, 40], 'color': "rgba(76, 175, 80, 0.3)"},
                            {'range': [40, 60], 'color': "rgba(255, 183, 77, 0.3)"},
                            {'range': [60, 100], 'color': "rgba(239, 83, 80, 0.3)"}
                        ]
                    },
                    title={
                        'text': "Nível de Risco",
                        'font': {'color': self.colors['text']}
                    },
                    delta={
                        'reference': 50,
                        'increasing': {'color': "#EF5350"},
                        'decreasing': {'color': "#4CAF50"}
                    },
                    number={
                        'suffix': "%",
                        'font': {'color': self.colors['text']}
                    }
                )
            )
            
            # Atualizar layout
            fig.update_layout(
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10),
                height=250
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Erro ao criar gráfico de métricas de risco: {str(e)}")
            return go.Figure().update_layout(
                title=f"Erro ao carregar métricas de risco: {str(e)}",
                plot_bgcolor=self.colors['panel_bg'],
                paper_bgcolor=self.colors['panel_bg'],
                font=dict(color=self.colors['text']),
                margin=dict(l=10, r=10, t=30, b=10)
            )

    def _save_dashboard_cache(self):
        """Salva cache de dados do dashboard"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'capital_history': [
                    {
                        'date': cap['date'].isoformat() if isinstance(cap['date'], datetime) else cap['date'],
                        'capital': cap['capital'],
                        'initial_capital': cap.get('initial_capital', 100.0)
                    } for cap in self.capital_history
                ],
                'risk_metrics': self.risk_metrics
            }
            
            with open(self.dashboard_cache, 'w') as f:
                json.dump(cache, f, indent=2)
            
            self.logger.info("Cache do dashboard salvo com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache do dashboard: {str(e)}")

    def _load_dashboard_cache(self):
        """Carrega cache de dados do dashboard"""
        try:
            if os.path.exists(self.dashboard_cache):
                with open(self.dashboard_cache, 'r') as f:
                    cache = json.load(f)
                    
                # Converter datas de string para datetime
                for cap in cache.get('capital_history', []):
                    if isinstance(cap.get('date'), str):
                        cap['date'] = datetime.fromisoformat(cap['date'])
                
                self.capital_history = cache.get('capital_history', [])
                self.risk_metrics = cache.get('risk_metrics', {})
                
                self.logger.info("Cache do dashboard carregado com sucesso")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache do dashboard: {str(e)}")
            return False

    def start(self):
        """Inicia o servidor do dashboard"""
        if self.is_running:
            self.logger.warning("Dashboard já está em execução")
            return False
            
        # Carregar cache, se existir
        self._load_dashboard_cache()
        
        # Atualizar dados iniciais
        self._update_dashboard_data()
        
        # Iniciar servidor em thread separada
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.is_running = True
        self.logger.info(f"Dashboard iniciado em http://localhost:{self.port}")
        
        return True

    def _run_server(self):
        """Executa o servidor Dash"""
        try:
            self.app.run_server(
                debug=self.debug,
                port=self.port,
                host='0.0.0.0'  # Permite acesso externo
            )
        except Exception as e:
            self.logger.error(f"Erro ao executar servidor do dashboard: {str(e)}")
            self.is_running = False

    def stop(self):
        """Para o servidor do dashboard"""
        # O Flask/Dash não tem um método clean de parar o servidor
        # Ao definir is_running como False, prevenimos que novos starts aconteçam
        self.is_running = False
        self.logger.info("Dashboard marcado para parar. O servidor será encerrado quando o processo principal terminar.")


# Teste simples como programa principal
if __name__ == "__main__":
    # Configurar logger
    logger = setup_logger()
    
    # Inicializar gerenciador de BD
    from db_manager import DBManager
    db = DBManager()
    
    # Tentar importar analisador externo
    try:
        from external_data_analyzer import ExternalDataAnalyzer
        external_data = ExternalDataAnalyzer()
        logger.info("Analisador de dados externos inicializado com sucesso")
    except ImportError:
        external_data = None
        logger.warning("Analisador de dados externos não disponível")
    
    # Inicializar dashboard
    dashboard = RobotCryptDashboard(db, external_data=external_data, debug=True)
    
    # Iniciar
    dashboard.start()
    
    # Manter rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando dashboard...")
        dashboard.stop()
