#!/usr/bin/env python3
"""
Módulo para gerenciar a conexão e operações com o PostgreSQL
"""
import logging
import os
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, DictCursor

class PostgresManager:
    """Classe para gerenciar conexão e operações com o PostgreSQL"""
    
    def __init__(self, connection_string=None, max_retries=3, retry_delay=1):
        """
        Inicializa o gerenciador de PostgreSQL
        
        Args:
            connection_string (str): String de conexão com o PostgreSQL.
                                   Se None, tentará usar variáveis de ambiente.
            max_retries (int): Número máximo de tentativas de reconexão
            retry_delay (int): Tempo inicial de espera entre tentativas (segundos)
        """
        self.logger = logging.getLogger("robot-crypt")
        self.conn = None
        self.cursor = None
        self.connection_string = connection_string
        self.max_retries = max_retries  # Número máximo de tentativas de reconexão
        self.retry_delay = retry_delay  # Tempo inicial de espera entre tentativas (segundos)
        
        # Se não foi fornecida string de conexão, tenta obter das variáveis de ambiente
        if not self.connection_string:
            self.connection_string = self._get_connection_string_from_env()
        
        try:
            self._setup_tables()
            self.logger.info("PostgresManager inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar PostgresManager: {str(e)}")
            self.logger.error("O armazenamento em PostgreSQL não estará disponível")
    
    def _get_connection_string_from_env(self):
        """
        Obtém a string de conexão das variáveis de ambiente
        
        Formato esperado:
        - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
        - ou POSTGRES_URL para uma string de conexão completa
        """
        if os.environ.get("POSTGRES_URL"):
            return os.environ.get("POSTGRES_URL")
            
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "robot_crypt")
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASSWORD", "")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def connect(self):
        """Conecta ao PostgreSQL com retentativas"""
        import time
        
        retries = 0
        last_exception = None
        
        while retries < self.max_retries:
            try:
                if not self.conn or self.conn.closed:
                    self.conn = psycopg2.connect(self.connection_string)
                    self.cursor = self.conn.cursor(cursor_factory=DictCursor)
                    self.logger.info("Conexão com PostgreSQL estabelecida")
                return True
            except Exception as e:
                last_exception = e
                retries += 1
                wait_time = self.retry_delay * (2 ** (retries - 1))  # Backoff exponencial
                self.logger.warning(f"Tentativa {retries}/{self.max_retries} falhou. Tentando novamente em {wait_time}s. Erro: {str(e)}")
                time.sleep(wait_time)
        
        # Se chegou aqui, todas as tentativas falharam
        self.logger.error(f"Erro ao conectar ao PostgreSQL após {self.max_retries} tentativas: {str(last_exception)}")
        return False
    
    def disconnect(self):
        """Desconecta do PostgreSQL"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("Conexão com PostgreSQL encerrada")
    
    def _setup_tables(self):
        """Configura as tabelas necessárias no banco de dados"""
        if not self.connect():
            return False
        
        try:
            # Tabela para armazenar notificações
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    telegram_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para armazenar análises de mercado
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_analysis (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    analysis_type VARCHAR(50) NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para armazenar operações de trading (histórico de transações)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_history (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    operation_type VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(18, 8) NOT NULL,
                    exit_price DECIMAL(18, 8),
                    quantity DECIMAL(18, 8) NOT NULL,
                    volume DECIMAL(18, 8) NOT NULL,
                    profit_loss DECIMAL(18, 8),
                    profit_loss_percentage DECIMAL(8, 4),
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    duration_minutes INTEGER,
                    strategy_used VARCHAR(50) NOT NULL,
                    strategy_type VARCHAR(20),  -- 'Scalping' ou 'Swing Trading'
                    stop_loss DECIMAL(18, 8),
                    take_profit DECIMAL(18, 8),
                    fees DECIMAL(18, 8),
                    balance_before DECIMAL(18, 8),
                    balance_after DECIMAL(18, 8),
                    trade_notes TEXT,
                    risk_percentage DECIMAL(5, 2),
                    market_condition VARCHAR(50),
                    indicators_at_entry JSONB,
                    indicators_at_exit JSONB,
                    additional_data JSONB
                )
            """)
            
            # Tabela para armazenar operações de trading (compatibilidade com código existente)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    operation_type VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(18, 8) NOT NULL,
                    exit_price DECIMAL(18, 8),
                    quantity DECIMAL(18, 8) NOT NULL,
                    profit_loss DECIMAL(18, 8),
                    profit_loss_percentage DECIMAL(8, 4),
                    status VARCHAR(20) DEFAULT 'open',
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    strategy_used VARCHAR(50),
                    stop_loss DECIMAL(18, 8),
                    take_profit DECIMAL(18, 8),
                    additional_data JSONB
                )
            """)
            
            # Tabela para histórico de preços com dados adicionais
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    open_price DECIMAL(18, 8) NOT NULL,
                    high_price DECIMAL(18, 8) NOT NULL,
                    low_price DECIMAL(18, 8) NOT NULL,
                    close_price DECIMAL(18, 8) NOT NULL,
                    volume DECIMAL(24, 8) NOT NULL,
                    quote_asset_volume DECIMAL(24, 8),
                    number_of_trades INTEGER,
                    taker_buy_base_volume DECIMAL(24, 8),
                    taker_buy_quote_volume DECIMAL(24, 8),
                    timestamp TIMESTAMP NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    UNIQUE(symbol, timestamp, interval)
                )
            """)
            
            # Tabela para métricas de desempenho diárias
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_performance (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    starting_balance DECIMAL(18, 2) NOT NULL,
                    ending_balance DECIMAL(18, 2) NOT NULL,
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    winning_trades INTEGER NOT NULL DEFAULT 0,
                    losing_trades INTEGER NOT NULL DEFAULT 0,
                    profit_loss DECIMAL(18, 2) NOT NULL DEFAULT 0,
                    profit_loss_percentage DECIMAL(8, 4) NOT NULL DEFAULT 0,
                    largest_win DECIMAL(18, 2),
                    largest_loss DECIMAL(18, 2),
                    avg_win DECIMAL(18, 2),
                    avg_loss DECIMAL(18, 2),
                    win_rate DECIMAL(5, 2),
                    avg_profit_per_trade DECIMAL(8, 4),
                    avg_loss_per_trade DECIMAL(8, 4),
                    drawdown DECIMAL(8, 4),
                    metrics_data JSONB
                )
            """)
            
            # Tabela para estatísticas semanais, mensais, etc.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    winning_trades INTEGER NOT NULL DEFAULT 0,
                    losing_trades INTEGER NOT NULL DEFAULT 0,
                    win_rate DECIMAL(5, 2),
                    initial_capital DECIMAL(18, 2) NOT NULL,
                    final_capital DECIMAL(18, 2) NOT NULL,
                    profit_loss DECIMAL(18, 2) NOT NULL,
                    profit_loss_percentage DECIMAL(8, 4) NOT NULL,
                    avg_profit_per_trade DECIMAL(8, 4),
                    avg_loss_per_trade DECIMAL(8, 4),
                    profit_factor DECIMAL(8, 4),  -- relação ganhos/perdas
                    max_consecutive_wins INTEGER,
                    max_consecutive_losses INTEGER,
                    max_drawdown DECIMAL(8, 4),
                    max_drawdown_percentage DECIMAL(8, 4),
                    recovery_factor DECIMAL(8, 4),
                    sharpe_ratio DECIMAL(8, 4),
                    sortino_ratio DECIMAL(8, 4),
                    calmar_ratio DECIMAL(8, 4),
                    avg_trade_duration DECIMAL(10, 2),  -- em minutos
                    best_symbol VARCHAR(20),
                    worst_symbol VARCHAR(20),
                    UNIQUE(period_type, start_date, end_date)
                )
            """)
            
            # Tabela para estados da aplicação (melhorada)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    state_data JSONB NOT NULL,
                    strategy_type VARCHAR(50),
                    active_pairs JSONB,
                    open_positions JSONB,
                    config_settings JSONB,
                    last_check_timestamp TIMESTAMP,
                    stats JSONB
                )
            """)
            
            # Tabela para capital ao longo do tempo
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS capital_history (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    balance DECIMAL(18, 8) NOT NULL,
                    change_amount DECIMAL(18, 8),
                    change_percentage DECIMAL(8, 4),
                    trade_id INTEGER,
                    event_type VARCHAR(50),  -- 'trade', 'deposit', 'withdrawal', 'fee', etc.
                    notes TEXT
                )
            """)
            
            # Tabela para indicadores técnicos (expandida)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    indicator_type VARCHAR(50) NOT NULL,
                    values JSONB NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    interval VARCHAR(10) NOT NULL,
                    parameters JSONB,  -- parâmetros do indicador (períodos, etc.)
                    calculation_method VARCHAR(50),  -- fórmula ou método usado
                    UNIQUE(symbol, indicator_type, timestamp, interval)
                )
            """)
            
            # Tabela para sinais de trading (expandida)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    signal_type VARCHAR(10) NOT NULL,  -- 'buy', 'sell', 'hold'
                    strength DECIMAL(5, 2) NOT NULL,  -- 0 a 1
                    price DECIMAL(18, 8) NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) NOT NULL,  -- 'technical', 'fundamental', 'sentiment', etc.
                    executed BOOLEAN DEFAULT FALSE,
                    execution_time TIMESTAMP,
                    execution_price DECIMAL(18, 8),
                    execution_success BOOLEAN,
                    reasoning TEXT,
                    indicators_data JSONB,
                    confidence_score DECIMAL(5, 2)  -- 0 a 1
                )
            """)
            
            # Tabela para métricas periódicas
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS periodic_stats (
                    id SERIAL PRIMARY KEY,
                    period_type VARCHAR(10) NOT NULL,  -- 'weekly', 'monthly', 'quarterly', 'yearly'
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    starting_balance DECIMAL(18, 2) NOT NULL,
                    ending_balance DECIMAL(18, 2) NOT NULL,
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    winning_trades INTEGER NOT NULL DEFAULT 0,
                    losing_trades INTEGER NOT NULL DEFAULT 0,
                    profit_loss DECIMAL(18, 2) NOT NULL DEFAULT 0,
                    profit_loss_percentage DECIMAL(8, 4) NOT NULL DEFAULT 0,
                    win_rate DECIMAL(5, 2),
                    max_drawdown DECIMAL(8, 4),
                    sharpe_ratio DECIMAL(8, 4),
                    additional_metrics JSONB,
                    UNIQUE(period_type, period_start)
                )
            """)
            
            # Tabela para drawdowns (expandida)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS drawdowns (
                    id SERIAL PRIMARY KEY,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP,
                    starting_balance DECIMAL(18, 2) NOT NULL,
                    lowest_balance DECIMAL(18, 2) NOT NULL,
                    recovery_balance DECIMAL(18, 2),
                    drawdown_amount DECIMAL(18, 2) NOT NULL,
                    drawdown_percentage DECIMAL(8, 4) NOT NULL,
                    duration_minutes INTEGER,
                    duration_days INTEGER,
                    recovery_date TIMESTAMP,
                    recovery_duration_minutes INTEGER,
                    recovery_duration_days INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    trades_during_drawdown JSONB,
                    market_conditions JSONB
                )
            """)
            
            # Tabela para monitoramento de saúde do sistema
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage DECIMAL(5, 2) NOT NULL,
                    memory_usage DECIMAL(5, 2) NOT NULL,
                    disk_usage DECIMAL(5, 2) NOT NULL,
                    api_latency INTEGER,
                    active_processes INTEGER,
                    errors_count INTEGER DEFAULT 0,
                    additional_metrics JSONB
                )
            """) 
            
            # Tabela melhorada para saldos de ativos (substituindo user_wallet)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_balances (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    asset VARCHAR(20) NOT NULL,
                    free DECIMAL(24, 8) NOT NULL DEFAULT 0,
                    locked DECIMAL(24, 8) NOT NULL DEFAULT 0,
                    total DECIMAL(24, 8) NOT NULL DEFAULT 0,
                    usdt_value DECIMAL(24, 8) DEFAULT 0,
                    brl_value DECIMAL(24, 8) DEFAULT 0,
                    total_balance_usdt DECIMAL(24, 8) DEFAULT 0,
                    total_balance_brl DECIMAL(24, 8) DEFAULT 0,
                    percentage_of_portfolio DECIMAL(8, 4) DEFAULT 0,
                    avg_cost_usdt DECIMAL(24, 8) DEFAULT 0,
                    unrealized_pnl DECIMAL(24, 8) DEFAULT 0,
                    unrealized_pnl_percentage DECIMAL(8, 4) DEFAULT 0,
                    market_price_usdt DECIMAL(24, 8) DEFAULT 0,
                    last_price_update TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    source VARCHAR(50) DEFAULT 'binance',
                    metadata JSONB DEFAULT '{}',
                    UNIQUE(user_id, asset, snapshot_date)
                )
            """)
            
            # Índices para asset_balances
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_asset_balances_user_asset 
                ON asset_balances(user_id, asset)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_asset_balances_snapshot_date 
                ON asset_balances(snapshot_date)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_asset_balances_updated_at 
                ON asset_balances(updated_at)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_asset_balances_usdt_value 
                ON asset_balances(usdt_value DESC)
            """)
            
            self.conn.commit()
            self.logger.info("Tabelas verificadas/criadas com sucesso no PostgreSQL")
            return True
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao configurar tabelas no PostgreSQL: {str(e)}")
            return False
    
    def save_notification(self, notification_type, title, message, telegram_sent=False):
        """
        Salva uma notificação no banco de dados
        
        Args:
            notification_type (str): Tipo da notificação (status, trade, error, etc.)
            title (str): Título da notificação
            message (str): Conteúdo da mensagem
            telegram_sent (bool): Se a mensagem foi enviada com sucesso pelo Telegram
        
        Returns:
            int: ID da notificação inserida ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                INSERT INTO notifications (type, title, message, telegram_sent)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            self.cursor.execute(query, (notification_type, title, message, telegram_sent))
            notification_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Notificação salva no PostgreSQL (ID: {notification_id})")
            return notification_id
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar notificação no PostgreSQL: {str(e)}")
            return None
    
    def save_analysis(self, symbol, analysis_type, data):
        """
        Salva uma análise de mercado no banco de dados
        
        Args:
            symbol (str): Símbolo da criptomoeda (ex: BTC/USDT)
            analysis_type (str): Tipo da análise (sentiment, technical, etc.)
            data (dict): Dados da análise
        
        Returns:
            int: ID da análise inserida ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                INSERT INTO market_analysis (symbol, analysis_type, data)
                VALUES (%s, %s, %s)
                RETURNING id
            """
            self.cursor.execute(query, (symbol, analysis_type, Json(data)))
            analysis_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Análise de {symbol} salva no PostgreSQL (ID: {analysis_id})")
            return analysis_id
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar análise no PostgreSQL: {str(e)}")
            return None
    
    def save_trade(self, symbol, operation_type, entry_price, quantity, 
                 stop_loss=None, take_profit=None, strategy=None, additional_data=None):
        """
        Salva uma nova operação de trade no banco de dados
        
        Args:
            symbol (str): Símbolo da criptomoeda
            operation_type (str): Tipo da operação (buy, sell)
            entry_price (float): Preço de entrada
            quantity (float): Quantidade
            stop_loss (float, opcional): Stop loss configurado
            take_profit (float, opcional): Take profit configurado
            strategy (str, opcional): Estratégia usada
            additional_data (dict, opcional): Dados adicionais
        
        Returns:
            int: ID do trade inserido ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                INSERT INTO trades 
                (symbol, operation_type, entry_price, quantity, stop_loss, take_profit, strategy_used, additional_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            self.cursor.execute(
                query, 
                (symbol, operation_type, entry_price, quantity, stop_loss, 
                take_profit, strategy, Json(additional_data) if additional_data else None)
            )
            
            trade_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Trade de {symbol} salvo no PostgreSQL (ID: {trade_id})")
            return trade_id
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar trade no PostgreSQL: {str(e)}")
            return None
    
    def update_trade_exit(self, trade_id, exit_price, profit_loss, profit_loss_percentage):
        """
        Atualiza uma operação de trade com os dados de saída
        
        Args:
            trade_id (int): ID do trade a ser atualizado
            exit_price (float): Preço de saída
            profit_loss (float): Lucro/prejuízo absoluto
            profit_loss_percentage (float): Lucro/prejuízo percentual
        
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            query = """
                UPDATE trades
                SET exit_price = %s,
                    profit_loss = %s,
                    profit_loss_percentage = %s,
                    exit_time = CURRENT_TIMESTAMP,
                    status = 'closed'
                WHERE id = %s
            """
            
            self.cursor.execute(query, (exit_price, profit_loss, profit_loss_percentage, trade_id))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                self.logger.info(f"Trade ID {trade_id} atualizado com dados de saída")
                return True
            else:
                self.logger.warning(f"Trade ID {trade_id} não encontrado para atualização")
                return False
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao atualizar trade no PostgreSQL: {str(e)}")
            return False
    
    def get_recent_notifications(self, limit=10):
        """
        Obtém as notificações mais recentes
        
        Args:
            limit (int): Número máximo de notificações a retornar
        
        Returns:
            list: Lista de notificações ou lista vazia em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                SELECT id, type, title, message, telegram_sent, created_at
                FROM notifications
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            self.cursor.execute(query, (limit,))
            result = self.cursor.fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            self.logger.error(f"Erro ao obter notificações: {str(e)}")
            return []
    
    def get_recent_analysis(self, symbol=None, analysis_type=None, limit=10):
        """
        Obtém as análises mais recentes, opcionalmente filtradas por símbolo ou tipo
        
        Args:
            symbol (str, opcional): Símbolo para filtrar
            analysis_type (str, opcional): Tipo de análise para filtrar
            limit (int): Número máximo de análises a retornar
        
        Returns:
            list: Lista de análises ou lista vazia em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            where_clauses = []
            params = []
            
            if symbol:
                where_clauses.append("symbol = %s")
                params.append(symbol)
            
            if analysis_type:
                where_clauses.append("analysis_type = %s")
                params.append(analysis_type)
            
            where_sql = " AND ".join(where_clauses)
            if where_sql:
                where_sql = "WHERE " + where_sql
            
            query = f"""
                SELECT id, symbol, analysis_type, data, created_at
                FROM market_analysis
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            params.append(limit)
            self.cursor.execute(query, tuple(params))
            result = self.cursor.fetchall()
            
            # Convertendo dados JSON para dicionário Python
            formatted_results = []
            for row in result:
                row_dict = dict(row)
                formatted_results.append(row_dict)
            
            return formatted_results
        except Exception as e:
            self.logger.error(f"Erro ao obter análises: {str(e)}")
            return []
    
    def get_open_trades(self):
        """
        Obtém as operações de trade abertas
        
        Returns:
            list: Lista de operações abertas ou lista vazia em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                SELECT *
                FROM trades
                WHERE status = 'open'
                ORDER BY entry_time DESC
            """
            
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            self.logger.error(f"Erro ao obter operações abertas: {str(e)}")
            return []
    
    def get_closed_trades(self, limit=50, symbol=None):
        """
        Obtém as operações de trade fechadas
        
        Args:
            limit (int): Número máximo de operações a retornar
            symbol (str, opcional): Filtrar por símbolo
        
        Returns:
            list: Lista de operações fechadas ou lista vazia em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            where_clause = "WHERE status = 'closed'"
            params = []
            
            if symbol:
                where_clause += " AND symbol = %s"
                params.append(symbol)
            
            query = f"""
                SELECT *
                FROM trades
                {where_clause}
                ORDER BY exit_time DESC
                LIMIT %s
            """
            
            params.append(limit)
            self.cursor.execute(query, tuple(params))
            result = self.cursor.fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            self.logger.error(f"Erro ao obter operações fechadas: {str(e)}")
            return []
    
    def save_price_history(self, symbol, ohlcv_data, interval="1h"):
        """
        Salva dados de preço histórico OHLCV (Open, High, Low, Close, Volume)
        
        Args:
            symbol (str): O par de moedas (ex: 'BTCUSDT')
            ohlcv_data (dict): Dados de preço no formato {
                'open_time': timestamp,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': float
            }
            interval (str): Intervalo do candle (ex: '1h', '15m', '1d')
            
        Returns:
            bool: True se o dado foi salvo com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            # Converte timestamp para datetime se necessário
            if isinstance(ohlcv_data['open_time'], int):
                timestamp = datetime.fromtimestamp(ohlcv_data['open_time'] / 1000)
            else:
                timestamp = ohlcv_data['open_time']
                
            # Verifica se já existe esse registro para evitar duplicatas
            self.cursor.execute("""
                SELECT id FROM price_history
                WHERE symbol = %s AND timestamp = %s AND interval = %s
            """, (symbol, timestamp, interval))
            
            existing_record = self.cursor.fetchone()
            
            if existing_record:
                # Atualiza o registro existente
                self.cursor.execute("""
                    UPDATE price_history
                    SET open_price = %s,
                        high_price = %s,
                        low_price = %s,
                        close_price = %s,
                        volume = %s
                    WHERE id = %s
                """, (
                    ohlcv_data['open'],
                    ohlcv_data['high'],
                    ohlcv_data['low'],
                    ohlcv_data['close'],
                    ohlcv_data['volume'],
                    existing_record['id']
                ))
            else:
                # Insere novo registro
                self.cursor.execute("""
                    INSERT INTO price_history (symbol, open_price, high_price, low_price, close_price, volume, timestamp, interval)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    symbol,
                    ohlcv_data['open'],
                    ohlcv_data['high'],
                    ohlcv_data['low'],
                    ohlcv_data['close'],
                    ohlcv_data['volume'],
                    timestamp,
                    interval
                ))
                
            self.conn.commit()
            self.logger.debug(f"Dados de preço salvos para {symbol} em {timestamp}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar dados de preço para {symbol}: {str(e)}")
            return False
    
    def save_price_history_batch(self, symbol, ohlcv_data_list, interval="1h"):
        """
        Salva múltiplos pontos de dados de preço histórico OHLCV em lote
        
        Args:
            symbol (str): O par de moedas (ex: 'BTCUSDT')
            ohlcv_data_list (list): Lista de dicionários com dados OHLCV
            interval (str): Intervalo do candle (ex: '1h', '15m', '1d')
            
        Returns:
            int: Número de registros salvos com sucesso
        """
        self._check_and_reconnect()
        
        if not ohlcv_data_list:
            return 0
            
        try:
            count = 0
            # Usar transação para inserções em lote
            for ohlcv_data in ohlcv_data_list:
                if self.save_price_history(symbol, ohlcv_data, interval):
                    count += 1
                    
            self.logger.info(f"Salvos {count}/{len(ohlcv_data_list)} dados de preço para {symbol}")
            return count
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar lote de dados de preço: {str(e)}")
            return 0
            
    def get_price_history(self, symbol, interval="1h", limit=100, start_time=None, end_time=None):
        """
        Obtém dados de preço histórico
        
        Args:
            symbol (str): O par de moedas (ex: 'BTCUSDT')
            interval (str): Intervalo do candle (ex: '1h', '15m', '1d')
            limit (int): Número máximo de registros a retornar
            start_time (datetime): Timestamp inicial para filtrar
            end_time (datetime): Timestamp final para filtrar
            
        Returns:
            list: Lista de dicionários com dados OHLCV
        """
        self._check_and_reconnect()
        
        try:
            # Constrói a consulta SQL com base nos parâmetros
            query_parts = [
                "SELECT * FROM price_history WHERE symbol = %s AND interval = %s"
            ]
            query_params = [symbol, interval]
            
            if start_time:
                query_parts.append("AND timestamp >= %s")
                query_params.append(start_time)
                
            if end_time:
                query_parts.append("AND timestamp <= %s")
                query_params.append(end_time)
                
            query_parts.append("ORDER BY timestamp DESC LIMIT %s")
            query_params.append(limit)
            
            # Executa a consulta
            query = " ".join(query_parts)
            self.cursor.execute(query, tuple(query_params))
            
            results = self.cursor.fetchall()
            
            # Formata os resultados para o formato esperado por outras partes da aplicação
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row['id'],
                    'symbol': row['symbol'],
                    'open_time': row['timestamp'],
                    'open': float(row['open_price']),
                    'high': float(row['high_price']),
                    'low': float(row['low_price']),
                    'close': float(row['close_price']),
                    'volume': float(row['volume']),
                    'interval': row['interval']
                })
            
            self.logger.debug(f"Recuperados {len(formatted_results)} registros de preço para {symbol}")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados de preço para {symbol}: {str(e)}")
            return []
    
    def save_technical_indicator(self, symbol, indicator_type, values, interval="1h", timestamp=None):
        """
        Salva dados de indicadores técnicos
        
        Args:
            symbol (str): O par de moedas (ex: 'BTCUSDT')
            indicator_type (str): Tipo do indicador (ex: 'RSI', 'MACD', 'EMA')
            values (dict): Valores do indicador
            interval (str): Intervalo temporal do indicador
            timestamp (datetime): Timestamp do cálculo do indicador (se None, usa o timestamp atual)
            
        Returns:
            bool: True se o indicador foi salvo com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            if timestamp is None:
                timestamp = datetime.now()
                
            # Verificar se já existe um registro com o mesmo timestamp
            self.cursor.execute("""
                SELECT id FROM technical_indicators
                WHERE symbol = %s AND indicator_type = %s AND timestamp = %s AND interval = %s
            """, (symbol, indicator_type, timestamp, interval))
            
            existing_record = self.cursor.fetchone()
            
            if existing_record:
                # Atualiza o registro existente
                self.cursor.execute("""
                    UPDATE technical_indicators
                    SET values = %s
                    WHERE id = %s
                """, (Json(values), existing_record['id']))
            else:
                # Insere novo registro
                self.cursor.execute("""
                    INSERT INTO technical_indicators (symbol, indicator_type, values, timestamp, interval)
                    VALUES (%s, %s, %s, %s, %s)
                """, (symbol, indicator_type, Json(values), timestamp, interval))
                
            self.conn.commit()
            self.logger.debug(f"Indicador {indicator_type} salvo para {symbol}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar indicador {indicator_type} para {symbol}: {str(e)}")
            return False
    
    def get_technical_indicators(self, symbol=None, indicator_type=None, interval="1h", limit=100):
        """
        Obtém dados de indicadores técnicos
        
        Args:
            symbol (str, opcional): Filtrar por par de moedas
            indicator_type (str, opcional): Filtrar por tipo de indicador
            interval (str): Intervalo temporal dos indicadores
            limit (int): Número máximo de registros a retornar
            
        Returns:
            list: Lista de indicadores técnicos
        """
        self._check_and_reconnect()
        
        try:
            # Constrói consulta com base nos filtros fornecidos
            query_parts = ["SELECT * FROM technical_indicators"]
            query_params = []
            where_clauses = []
            
            if symbol:
                where_clauses.append("symbol = %s")
                query_params.append(symbol)
                
            if indicator_type:
                where_clauses.append("indicator_type = %s")
                query_params.append(indicator_type)
                
            if interval:
                where_clauses.append("interval = %s")
                query_params.append(interval)
                
            # Monta a cláusula WHERE
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))
                
            # Adiciona ordenação e limite
            query_parts.append("ORDER BY timestamp DESC LIMIT %s")
            query_params.append(limit)
            
            # Executa a consulta
            query = " ".join(query_parts)
            self.cursor.execute(query, tuple(query_params))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter indicadores técnicos: {str(e)}")
            return []
    
    def save_trading_signal(self, symbol, signal_type, strength, price, source, reasoning=None, indicators_data=None):
        """
        Salva um sinal de trading gerado
        
        Args:
            symbol (str): O par de moedas (ex: 'BTCUSDT')
            signal_type (str): Tipo do sinal ('buy', 'sell', 'hold')
            strength (float): Força do sinal (0.0 a 1.0)
            price (float): Preço quando o sinal foi gerado
            source (str): Fonte do sinal (ex: 'technical', 'sentiment', 'risk')
            reasoning (str, opcional): Explicação do motivo do sinal
            indicators_data (dict, opcional): Dados de indicadores usados para gerar o sinal
            
        Returns:
            int: ID do sinal inserido ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            self.cursor.execute("""
                INSERT INTO trading_signals (
                    symbol, signal_type, strength, price, source, reasoning, indicators_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                symbol, 
                signal_type, 
                strength, 
                price, 
                source, 
                reasoning,
                Json(indicators_data) if indicators_data else None
            ))
            
            signal_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Sinal de {signal_type.upper()} para {symbol} salvo (ID: {signal_id})")
            return signal_id
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar sinal de trading para {symbol}: {str(e)}")
            return None
            
    def update_signal_executed(self, signal_id):
        """
        Marca um sinal de trading como executado
        
        Args:
            signal_id (int): ID do sinal a ser atualizado
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            self.cursor.execute("""
                UPDATE trading_signals
                SET executed = TRUE
                WHERE id = %s
            """, (signal_id,))
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                self.logger.info(f"Sinal ID {signal_id} marcado como executado")
                return True
            else:
                self.logger.warning(f"Sinal ID {signal_id} não encontrado")
                return False
                
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao atualizar sinal {signal_id}: {str(e)}")
            return False
    
    def get_trading_signals(self, symbol=None, signal_type=None, executed=None, limit=50):
        """
        Obtém sinais de trading
        
        Args:
            symbol (str, opcional): Filtrar por par de moedas
            signal_type (str, opcional): Filtrar por tipo de sinal ('buy', 'sell', 'hold')
            executed (bool, opcional): Filtrar por sinais executados ou não
            limit (int): Número máximo de sinais a retornar
            
        Returns:
            list: Lista de sinais de trading
        """
        self._check_and_reconnect()
        
        try:
            # Constrói consulta com base nos filtros fornecidos
            query_parts = ["SELECT * FROM trading_signals"]
            query_params = []
            where_clauses = []
            
            if symbol:
                where_clauses.append("symbol = %s")
                query_params.append(symbol)
                
            if signal_type:
                where_clauses.append("signal_type = %s")
                query_params.append(signal_type)
                
            if executed is not None:
                where_clauses.append("executed = %s")
                query_params.append(executed)
                
            # Monta a cláusula WHERE
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))
                
            # Adiciona ordenação e limite
            query_parts.append("ORDER BY timestamp DESC LIMIT %s")
            query_params.append(limit)
            
            # Executa a consulta
            query = " ".join(query_parts)
            self.cursor.execute(query, tuple(query_params))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter sinais de trading: {str(e)}")
            return []
    
    def save_app_state(self, state_data):
        """
        Salva o estado da aplicação no PostgreSQL
        
        Args:
            state_data (dict): Dicionário com o estado da aplicação
        
        Returns:
            int: ID do estado salvo ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            # Extrair informações importantes do estado
            strategy_type = state_data.get('strategy_type')
            active_pairs = state_data.get('pairs', [])
            open_positions = state_data.get('open_positions', {})
            last_check_timestamp = state_data.get('last_check_time')
            stats = state_data.get('stats', {})
            
            # Converter timestamp string para datetime se necessário
            if isinstance(last_check_timestamp, str):
                try:
                    last_check_timestamp = datetime.fromisoformat(last_check_timestamp.replace('Z', '+00:00'))
                except:
                    last_check_timestamp = datetime.now()
            elif last_check_timestamp is None:
                last_check_timestamp = datetime.now()

            # Inserir o estado na tabela
            query = """
                INSERT INTO app_state (
                    state_data, strategy_type, active_pairs, open_positions, 
                    last_check_timestamp, stats
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            self.cursor.execute(query, (
                Json(state_data),
                strategy_type,
                Json(active_pairs),
                Json(open_positions),
                last_check_timestamp,
                Json(stats)
            ))
            
            state_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            # Manter apenas os 50 estados mais recentes
            self.cursor.execute("""
                DELETE FROM app_state 
                WHERE id NOT IN (
                    SELECT id FROM app_state ORDER BY timestamp DESC LIMIT 50
                )
            """)
            self.conn.commit()
            
            self.logger.info(f"Estado da aplicação salvo no PostgreSQL (ID: {state_id})")
            # Registra operação bem-sucedida
            self.register_success()
            return state_id
            
        except psycopg2.OperationalError as e:
            # Tratamento específico para erros de conexão
            self.logger.error(f"Erro de conexão ao salvar estado: {str(e)}")
            try:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
            except Exception as rollback_error:
                self.logger.error(f"Erro no rollback: {str(rollback_error)}")
            
            # Tenta reconectar para a próxima operação
            self._check_and_reconnect()
            # Registra a falha para rastrear problemas persistentes
            self.register_failure()
            return None
            
        except Exception as e:
            # Outros erros gerais
            self.logger.error(f"Erro ao salvar estado da aplicação no PostgreSQL: {str(e)}")
            try:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
            except Exception as rollback_error:
                self.logger.error(f"Erro no rollback: {str(rollback_error)}")
            
            # Registra a falha para rastrear problemas persistentes
            self.register_failure()
            return None
    
    def update_daily_stats(self, stats):
        """
        Atualiza ou insere estatísticas diárias
        
        Args:
            stats (dict): Dicionário com estatísticas atualizadas
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            # Data atual para registro
            today = datetime.now().date().isoformat()
            
            # Verifica se já existe uma entrada para hoje
            self.cursor.execute("SELECT id FROM daily_performance WHERE date = %s", (today,))
            result = self.cursor.fetchone()
            
            # Extrai os dados necessários do dicionário stats
            # Usamos .get() com valores padrão para evitar KeyError
            current_capital = float(stats.get('current_capital', 0.0))
            initial_capital = float(stats.get('initial_capital', current_capital))
            total_trades = int(stats.get('total_trades', 0))
            winning_trades = int(stats.get('winning_trades', 0))
            losing_trades = int(stats.get('losing_trades', 0))
            best_trade_profit = float(stats.get('best_trade_profit', 0.0))
            worst_trade_loss = float(stats.get('worst_trade_loss', 0.0))
            
            # Calcular métricas adicionais
            profit_loss = current_capital - initial_capital
            profit_loss_percentage = (profit_loss / initial_capital * 100) if initial_capital > 0 else 0
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            if result:
                # Atualiza entrada existente
                query = """
                    UPDATE daily_performance SET
                    ending_balance = %s,
                    total_trades = %s,
                    winning_trades = %s,
                    losing_trades = %s,
                    profit_loss = %s,
                    profit_loss_percentage = %s,
                    largest_win = %s,
                    largest_loss = %s,
                    win_rate = %s
                    WHERE id = %s
                """
                
                self.cursor.execute(query, (
                    current_capital,
                    total_trades,
                    winning_trades,
                    losing_trades,
                    profit_loss,
                    profit_loss_percentage,
                    best_trade_profit,
                    worst_trade_loss,
                    win_rate,
                    result['id']
                ))
                
                self.logger.info(f"Estatísticas diárias atualizadas para {today}")
            else:
                # Insere nova entrada
                query = """
                    INSERT INTO daily_performance (
                        date, starting_balance, ending_balance, total_trades,
                        winning_trades, losing_trades, profit_loss, profit_loss_percentage,
                        largest_win, largest_loss, win_rate
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                self.cursor.execute(query, (
                    today,
                    initial_capital,
                    current_capital,
                    total_trades,
                    winning_trades,
                    losing_trades,
                    profit_loss,
                    profit_loss_percentage,
                    best_trade_profit,
                    worst_trade_loss,
                    win_rate
                ))
                
                daily_id = self.cursor.fetchone()[0]
                self.logger.info(f"Novas estatísticas diárias inseridas para {today} (ID: {daily_id})")
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao atualizar estatísticas diárias: {str(e)}")
            return False
    
    # =============================================
    # Funções para histórico detalhado de transações
    # =============================================
    
    def record_transaction(self, transaction_data):
        """
        Registra uma transação completa no histórico
        
        Args:
            transaction_data (dict): Dicionário com dados da transação contendo:
                - symbol: Par de trading
                - operation_type: Tipo de operação ('buy' ou 'sell')
                - entry_price: Preço de entrada
                - exit_price: Preço de saída (apenas para vendas)
                - quantity: Quantidade negociada
                - volume: Volume total (preço x quantidade)
                - profit_loss: Lucro/prejuízo absoluto (apenas para vendas)
                - profit_loss_percentage: Percentual de lucro/prejuízo (apenas para vendas)
                - entry_time: Timestamp da entrada
                - exit_time: Timestamp da saída (apenas para vendas)
                - strategy_used: Estratégia utilizada
                - strategy_type: Tipo da estratégia ('Scalping' ou 'Swing Trading')
                - fees: Taxas pagas
                - balance_before: Saldo antes da operação
                - balance_after: Saldo após a operação
                - indicators_at_entry: Indicadores no momento da entrada (opcional)
                - indicators_at_exit: Indicadores no momento da saída (opcional)
                
        Returns:
            int: ID da transação registrada ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            # Verificar se temos todos os campos necessários
            required_fields = ['symbol', 'operation_type', 'entry_price', 'quantity', 'entry_time', 'strategy_used']
            for field in required_fields:
                if field not in transaction_data:
                    self.logger.error(f"Campo obrigatório '{field}' não encontrado nos dados da transação")
                    return None
            
            # Verificar se temos os campos para operações de venda
            if transaction_data['operation_type'] == 'sell':
                required_sell_fields = ['exit_price', 'exit_time', 'profit_loss_percentage']
                for field in required_sell_fields:
                    if field not in transaction_data:
                        self.logger.warning(f"Campo '{field}' não encontrado em uma operação de venda")
            
            # Calcular o volume se não estiver presente
            if 'volume' not in transaction_data:
                transaction_data['volume'] = float(transaction_data['entry_price']) * float(transaction_data['quantity'])
            
            # Calcular a duração em minutos para operações de venda
            duration_minutes = None
            if transaction_data['operation_type'] == 'sell' and 'entry_time' in transaction_data and 'exit_time' in transaction_data:
                entry_time = transaction_data['entry_time']
                exit_time = transaction_data['exit_time']
                
                # Converter para datetime se necessário
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                    
                duration_minutes = (exit_time - entry_time).total_seconds() / 60
            
            # Construir a consulta SQL com base nos campos disponíveis
            fields = []
            values = []
            placeholders = []
            
            # Mapear campos do dicionário para colunas do banco
            field_mapping = {
                'symbol': 'symbol',
                'operation_type': 'operation_type',
                'entry_price': 'entry_price',
                'exit_price': 'exit_price',
                'quantity': 'quantity',
                'volume': 'volume',
                'profit_loss': 'profit_loss',
                'profit_loss_percentage': 'profit_loss_percentage',
                'entry_time': 'entry_time',
                'exit_time': 'exit_time',
                'duration_minutes': 'duration_minutes',
                'strategy_used': 'strategy_used',
                'strategy_type': 'strategy_type',
                'stop_loss': 'stop_loss',
                'take_profit': 'take_profit',
                'fees': 'fees',
                'balance_before': 'balance_before',
                'balance_after': 'balance_after',
                'trade_notes': 'trade_notes',
                'risk_percentage': 'risk_percentage',
                'market_condition': 'market_condition'
            }
            
            # Adicionar campos que estão presentes nos dados
            for key, column in field_mapping.items():
                if key in transaction_data:
                    fields.append(column)
                    values.append(transaction_data[key])
                    placeholders.append('%s')
            
            # Adicionar campos JSONB se presentes
            if 'indicators_at_entry' in transaction_data:
                fields.append('indicators_at_entry')
                values.append(Json(transaction_data['indicators_at_entry']))
                placeholders.append('%s')
                
            if 'indicators_at_exit' in transaction_data:
                fields.append('indicators_at_exit')
                values.append(Json(transaction_data['indicators_at_exit']))
                placeholders.append('%s')
                
            if 'additional_data' in transaction_data:
                fields.append('additional_data')
                values.append(Json(transaction_data['additional_data']))
                placeholders.append('%s')
            
            # Adicionar duração calculada se disponível
            if duration_minutes is not None and 'duration_minutes' not in transaction_data:
                fields.append('duration_minutes')
                values.append(duration_minutes)
                placeholders.append('%s')
            
            # Construir e executar a consulta SQL
            fields_str = ', '.join(fields)
            placeholders_str = ', '.join(placeholders)
            
            query = f"""
                INSERT INTO transaction_history ({fields_str})
                VALUES ({placeholders_str})
                RETURNING id
            """
            
            self.cursor.execute(query, tuple(values))
            transaction_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Transação de {transaction_data['operation_type']} para {transaction_data['symbol']} registrada (ID: {transaction_id})")
            return transaction_id
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao registrar transação: {str(e)}")
            return None
    
    def get_transaction_history(self, symbol=None, start_date=None, end_date=None, operation_type=None, limit=100):
        """
        Obtém o histórico de transações, opcionalmente filtrado
        
        Args:
            symbol (str, opcional): Filtrar por par de moedas
            start_date (datetime, opcional): Data inicial para filtro
            end_date (datetime, opcional): Data final para filtro
            operation_type (str, opcional): Tipo de operação ('buy' ou 'sell')
            limit (int): Número máximo de transações a retornar
            
        Returns:
            list: Lista de transações
        """
        self._check_and_reconnect()
        
        try:
            # Constrói consulta com base nos filtros fornecidos
            query_parts = ["SELECT * FROM transaction_history"]
            query_params = []
            where_clauses = []
            
            if symbol:
                where_clauses.append("symbol = %s")
                query_params.append(symbol)
                
            if operation_type:
                where_clauses.append("operation_type = %s")
                query_params.append(operation_type)
                
            if start_date:
                where_clauses.append("entry_time >= %s")
                query_params.append(start_date)
                
            if end_date:
                where_clauses.append("entry_time <= %s")
                query_params.append(end_date)
                
            # Monta a cláusula WHERE
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))
                
            # Adiciona ordenação e limite
            query_parts.append("ORDER BY entry_time DESC LIMIT %s")
            query_params.append(limit)
            
            # Executa a consulta
            query = " ".join(query_parts)
            self.cursor.execute(query, tuple(query_params))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de transações: {str(e)}")
            return []
    
    def calculate_performance_metrics(self, period_type, start_date, end_date):
        """
        Calcula métricas de performance para um período específico
        
        Args:
            period_type (str): Tipo do período ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
            start_date (date): Data de início do período
            end_date (date): Data de fim do período
            
        Returns:
            dict: Métricas de performance calculadas ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            # Obter todas as transações no período
            self.cursor.execute("""
                SELECT * FROM transaction_history
                WHERE operation_type = 'sell'  -- Apenas transações completadas
                AND exit_time BETWEEN %s AND %s
                ORDER BY exit_time
            """, (start_date, end_date))
            
            transactions = self.cursor.fetchall()
            
            if not transactions:
                self.logger.info(f"Nenhuma transação encontrada para o período {start_date} a {end_date}")
                return None
            
            # Inicializa métricas básicas
            total_trades = len(transactions)
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            total_loss = 0.0
            profits = []
            losses = []
            durations = []
            symbols = {}
            
            # Obter saldo inicial (do primeiro trade) e final (do último trade)
            initial_capital = float(transactions[0]['balance_before']) if 'balance_before' in transactions[0] else None
            final_capital = float(transactions[-1]['balance_after']) if 'balance_after' in transactions[-1] else None
            
            # Se não temos os saldos, tentar buscar do histórico de capital
            if initial_capital is None or final_capital is None:
                self.cursor.execute("""
                    SELECT balance FROM capital_history
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY timestamp ASC LIMIT 1
                """, (start_date, end_date))
                
                initial_result = self.cursor.fetchone()
                if initial_result:
                    initial_capital = float(initial_result['balance'])
                
                self.cursor.execute("""
                    SELECT balance FROM capital_history
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (start_date, end_date))
                
                final_result = self.cursor.fetchone()
                if final_result:
                    final_capital = float(final_result['balance'])
            
            # Se ainda não temos os valores, usar valores padrão
            if initial_capital is None:
                initial_capital = 100.0
            if final_capital is None:
                final_capital = initial_capital
            
            # Analisar cada transação
            consecutive_wins = 0
            consecutive_losses = 0
            max_consecutive_wins = 0
            max_consecutive_losses = 0
            current_streak = 0
            
            for tx in transactions:
                profit_percentage = float(tx['profit_loss_percentage']) if tx['profit_loss_percentage'] is not None else 0.0
                profit_amount = float(tx['profit_loss']) if tx['profit_loss'] is not None else 0.0
                
                # Registrar duração se disponível
                if tx['duration_minutes'] is not None:
                    durations.append(float(tx['duration_minutes']))
                
                # Registrar estatísticas por símbolo
                symbol = tx['symbol']
                if symbol not in symbols:
                    symbols[symbol] = {'trades': 0, 'wins': 0, 'losses': 0, 'profit': 0.0}
                
                symbols[symbol]['trades'] += 1
                
                # Classificar como ganho ou perda
                if profit_percentage > 0:
                    winning_trades += 1
                    total_profit += profit_amount
                    profits.append(profit_percentage)
                    symbols[symbol]['wins'] += 1
                    symbols[symbol]['profit'] += profit_amount
                    
                    # Atualizar sequências de vitórias
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                    
                    max_consecutive_wins = max(max_consecutive_wins, current_streak)
                else:
                    losing_trades += 1
                    total_loss += abs(profit_amount)
                    losses.append(profit_percentage)
                    symbols[symbol]['losses'] += 1
                    symbols[symbol]['profit'] += profit_amount
                    
                    # Atualizar sequências de derrotas
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                    
                    max_consecutive_losses = max(max_consecutive_losses, abs(current_streak))
            
            # Calcular médias e estatísticas
            avg_profit_per_trade = total_profit / winning_trades if winning_trades > 0 else 0
            avg_loss_per_trade = total_loss / losing_trades if losing_trades > 0 else 0
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            avg_trade_duration = sum(durations) / len(durations) if durations else 0
            
            # Identificar melhor e pior símbolo
            best_symbol = None
            worst_symbol = None
            best_profit = float('-inf')
            worst_profit = float('inf')
            
            for symbol, stats in symbols.items():
                profit_per_trade = stats['profit'] / stats['trades'] if stats['trades'] > 0 else 0
                if profit_per_trade > best_profit:
                    best_profit = profit_per_trade
                    best_symbol = symbol
                if profit_per_trade < worst_profit:
                    worst_profit = profit_per_trade
                    worst_symbol = symbol
            
            # Calcular drawdown (através da tabela de drawdowns ou capital_history)
            max_drawdown = 0.0
            max_drawdown_percentage = 0.0
            
            self.cursor.execute("""
                SELECT * FROM drawdowns
                WHERE start_date BETWEEN %s AND %s
                ORDER BY drawdown_percentage DESC
                LIMIT 1
            """, (start_date, end_date))
            
            drawdown_record = self.cursor.fetchone()
            if drawdown_record:
                max_drawdown = float(drawdown_record['drawdown_amount'])
                max_drawdown_percentage = float(drawdown_record['drawdown_percentage'])
            
            # Calcular valor total de lucro/prejuízo e percentual
            profit_loss = final_capital - initial_capital
            profit_loss_percentage = (profit_loss / initial_capital) * 100 if initial_capital > 0 else 0
            
            # Preparar dados para inserção
            metrics = {
                'period_type': period_type,
                'start_date': start_date,
                'end_date': end_date,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'profit_loss': profit_loss,
                'profit_loss_percentage': profit_loss_percentage,
                'avg_profit_per_trade': avg_profit_per_trade,
                'avg_loss_per_trade': avg_loss_per_trade,
                'profit_factor': profit_factor,
                'max_consecutive_wins': max_consecutive_wins,
                'max_consecutive_losses': max_consecutive_losses,
                'max_drawdown': max_drawdown,
                'max_drawdown_percentage': max_drawdown_percentage,
                'avg_trade_duration': avg_trade_duration,
                'best_symbol': best_symbol,
                'worst_symbol': worst_symbol
            }
            
            # Verificar se já existe registro para esse período
            self.cursor.execute("""
                SELECT id FROM performance_metrics
                WHERE period_type = %s AND start_date = %s AND end_date = %s
            """, (period_type, start_date, end_date))
            
            existing_record = self.cursor.fetchone()
            
            if existing_record:
                # Atualizar registro existente
                update_fields = []
                update_values = []
                
                for key, value in metrics.items():
                    if key not in ('period_type', 'start_date', 'end_date'):
                        update_fields.append(f"{key} = %s")
                        update_values.append(value)
                
                update_values.append(existing_record['id'])
                
                query = f"""
                    UPDATE performance_metrics
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                
                self.cursor.execute(query, tuple(update_values))
                self.conn.commit()
                
                self.logger.info(f"Métricas de performance para {period_type} ({start_date} a {end_date}) atualizadas")
                return metrics
            else:
                # Inserir novo registro
                fields = list(metrics.keys())
                values = list(metrics.values())
                placeholders = ['%s'] * len(fields)
                
                query = f"""
                    INSERT INTO performance_metrics ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING id
                """
                
                self.cursor.execute(query, tuple(values))
                metrics_id = self.cursor.fetchone()[0]
                self.conn.commit()
                
                self.logger.info(f"Métricas de performance para {period_type} ({start_date} a {end_date}) inseridas (ID: {metrics_id})")
                return metrics
                
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao calcular métricas de performance: {str(e)}")
            return None
    
    def save_capital_update(self, balance, change_amount=None, change_percentage=None, trade_id=None, event_type='trade', notes=None):
        """
        Registra uma atualização no capital do bot
        
        Args:
            balance (float): Saldo atual após a atualização
            change_amount (float, opcional): Alteração no valor absoluto
            change_percentage (float, opcional): Alteração percentual
            trade_id (int, opcional): ID da transação relacionada, se houver
            event_type (str): Tipo do evento ('trade', 'deposit', 'withdrawal', 'fee', etc.)
            notes (str, opcional): Observações sobre a atualização
            
        Returns:
            int: ID do registro ou None em caso de erro
        """
        self._check_and_reconnect()
        
        try:
            query = """
                INSERT INTO capital_history (balance, change_amount, change_percentage, trade_id, event_type, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            self.cursor.execute(query, (balance, change_amount, change_percentage, trade_id, event_type, notes))
            record_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            self.logger.info(f"Atualização de capital registrada: {balance:.2f} ({change_percentage:+.2f}% se disponível) - ID: {record_id}")
            return record_id
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao registrar atualização de capital: {str(e)}")
            return None
            
    def get_capital_history(self, start_date=None, end_date=None, limit=100):
        """
        Obtém o histórico de capital
        
        Args:
            start_date (datetime, opcional): Data inicial para filtro
            end_date (datetime, opcional): Data final para filtro
            limit (int): Número máximo de registros a retornar
            
        Returns:
            list: Lista de registros de capital
        """
        self._check_and_reconnect()
        
        try:
            # Constrói consulta com base nos filtros fornecidos
            query_parts = ["SELECT * FROM capital_history"]
            query_params = []
            where_clauses = []
            
            if start_date:
                where_clauses.append("timestamp >= %s")
                query_params.append(start_date)
                
            if end_date:
                where_clauses.append("timestamp <= %s")
                query_params.append(end_date)
                
            # Monta a cláusula WHERE
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))
                
            # Adiciona ordenação e limite
            query_parts.append("ORDER BY timestamp DESC LIMIT %s")
            query_params.append(limit)
            
            # Executa a consulta
            query = " ".join(query_parts)
            self.cursor.execute(query, tuple(query_params))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de capital: {str(e)}")
            return []
    
    def ensure_connection(self):
        """Garante que a conexão com o banco está ativa ou reconecta"""
        if not self._is_connection_alive():
            self.logger.info("Reconectando ao PostgreSQL...")
            # Fecha conexões anteriores que possam estar em estado inválido
            self.disconnect()
            # Tenta estabelecer uma nova conexão
            return self.connect()
        return True
    
    def _is_connection_alive(self):
        """Verifica se a conexão está ativa e utilizável"""
        if not self.conn or self.conn.closed:
            return False
        
        try:
            # Executa uma consulta simples para verificar se a conexão funciona
            with self.conn.cursor() as check_cursor:
                check_cursor.execute("SELECT 1")
                return True
        except Exception:
            self.logger.warning("Conexão com PostgreSQL perdida ou inativa")
            return False
            
    def _check_and_reconnect(self):
        """
        Verifica se a conexão com o banco de dados está ativa e tenta reconectar se necessário
        Usa backoff exponencial para tentativas repetidas
        """
        import time
        
        if self._is_connection_alive():
            return True
        
        # Se chegou aqui, a conexão está inativa, vamos tentar reconectar
        self.logger.warning("Conexão com o banco de dados está fechada. Tentando reconectar...")
        
        # Limpa recursos anteriores
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn and not self.conn.closed:
                self.conn.close()
        except Exception:
            pass  # Ignora erros ao fechar conexões inválidas
        
        # Tenta reconectar com backoff exponencial
        for attempt in range(1, self.max_retries + 1):
            try:
                self.conn = psycopg2.connect(self.connection_string)
                self.cursor = self.conn.cursor(cursor_factory=DictCursor)
                self.logger.info(f"Reconexão bem-sucedida na tentativa {attempt}")
                return True
            except Exception as e:
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                if attempt < self.max_retries:
                    self.logger.warning(f"Tentativa {attempt}/{self.max_retries} falhou. Tentando novamente em {wait_time}s. Erro: {str(e)}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Todas as {self.max_retries} tentativas de reconexão falharam. Último erro: {str(e)}")
        
        return False
    
    def should_use_fallback(self):
        """
        Verifica se devemos usar o fallback SQLite
        Retorna True se houver problemas persistentes com PostgreSQL
        """
        if not hasattr(self, '_failure_count'):
            self._failure_count = 0
            self._last_failure_time = None
            
        if self._failure_count >= 5:  # 5 falhas seguidas sugerem problema persistente
            self.logger.warning("PostgreSQL com problemas persistentes. Recomendando uso de fallback SQLite.")
            return True
            
        return False
        
    def register_failure(self):
        """Registra uma falha de operação para rastrear problemas persistentes"""
        if not hasattr(self, '_failure_count'):
            self._failure_count = 0
            self._last_failure_time = None
            
        import time
        current_time = time.time()
        
        # Se a última falha foi há mais de 5 minutos, resetamos o contador
        if self._last_failure_time and (current_time - self._last_failure_time) > 300:
            self._failure_count = 0
            
        self._failure_count += 1
        self._last_failure_time = current_time
        
        if self._failure_count >= 3:
            self.logger.warning(f"PostgreSQL com {self._failure_count} falhas consecutivas")
            
    def register_success(self):
        """Registra uma operação bem-sucedida"""
        if hasattr(self, '_failure_count'):
            self._failure_count = 0
    
    def load_last_app_state(self):
        """
        Loads the last application state from the PostgreSQL database
        
        Returns:
            dict: The latest application state as a Python dictionary, or None if not found/error
        """
        try:
            if not self.connect():
                return None
            
            self.cursor.execute('SELECT state_data FROM app_state ORDER BY timestamp DESC LIMIT 1')
            result = self.cursor.fetchone()
            if result:
                return json.loads(result['state_data']) if isinstance(result['state_data'], str) else result['state_data']
            return None
        except Exception as e:
            self.logger.error(f"Error loading the last application state: {str(e)}")
            return None
    
    # =============================================
    # Métodos para Asset Balances
    # =============================================
    
    def save_asset_balances(self, user_id, balances_data, total_balance_usdt=0, total_balance_brl=0):
        """
        Salva os saldos de ativos do usuário
        
        Args:
            user_id (str): ID do usuário
            balances_data (list): Lista de dicionários com dados dos ativos
            total_balance_usdt (float): Valor total da carteira em USDT
            total_balance_brl (float): Valor total da carteira em BRL
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        self._check_and_reconnect()
        
        try:
            today = datetime.now().date()
            
            # Remove dados antigos do mesmo dia para este usuário
            self.cursor.execute("""
                DELETE FROM asset_balances 
                WHERE user_id = %s AND snapshot_date = %s
            """, (user_id, today))
            
            # Insere novos dados
            for balance in balances_data:
                # Calcula percentual do portfólio
                percentage = 0
                if total_balance_usdt > 0 and balance.get('usdt_value', 0) > 0:
                    percentage = (balance['usdt_value'] / total_balance_usdt) * 100
                
                self.cursor.execute("""
                    INSERT INTO asset_balances (
                        user_id, asset, free, locked, total, usdt_value, brl_value,
                        total_balance_usdt, total_balance_brl, percentage_of_portfolio,
                        market_price_usdt, last_price_update, snapshot_date, source, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    balance['asset'],
                    balance.get('free', 0),
                    balance.get('locked', 0),
                    balance.get('total', 0),
                    balance.get('usdt_value', 0),
                    balance.get('brl_value', 0),
                    total_balance_usdt,
                    total_balance_brl,
                    percentage,
                    balance.get('market_price', 0),
                    datetime.now(),
                    today,
                    balance.get('source', 'binance'),
                    Json(balance.get('metadata', {}))
                ))
            
            self.conn.commit()
            self.logger.info(f"Saldos de {len(balances_data)} ativos salvos para usuário {user_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar saldos de ativos: {str(e)}")
            return False
    
    def get_user_asset_balances(self, user_id, snapshot_date=None, active_only=True):
        """
        Obtém os saldos de ativos de um usuário
        
        Args:
            user_id (str): ID do usuário
            snapshot_date (date, opcional): Data específica do snapshot
            active_only (bool): Se True, retorna apenas ativos ativos
            
        Returns:
            list: Lista de saldos de ativos
        """
        self._check_and_reconnect()
        
        try:
            where_clauses = ["user_id = %s"]
            params = [user_id]
            
            if snapshot_date:
                where_clauses.append("snapshot_date = %s")
                params.append(snapshot_date)
            else:
                # Pega a data mais recente
                where_clauses.append("snapshot_date = (SELECT MAX(snapshot_date) FROM asset_balances WHERE user_id = %s)")
                params.append(user_id)
            
            if active_only:
                where_clauses.append("is_active = TRUE")
            
            query = f"""
                SELECT * FROM asset_balances
                WHERE {' AND '.join(where_clauses)}
                ORDER BY usdt_value DESC
            """
            
            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter saldos de ativos: {str(e)}")
            return []
    
    def get_user_total_balance(self, user_id, snapshot_date=None):
        """
        Obtém o saldo total da carteira do usuário
        
        Args:
            user_id (str): ID do usuário
            snapshot_date (date, opcional): Data específica do snapshot
            
        Returns:
            dict: Saldo total em USDT e BRL
        """
        self._check_and_reconnect()
        
        try:
            where_clause = "user_id = %s"
            params = [user_id]
            
            if snapshot_date:
                where_clause += " AND snapshot_date = %s"
                params.append(snapshot_date)
            else:
                where_clause += " AND snapshot_date = (SELECT MAX(snapshot_date) FROM asset_balances WHERE user_id = %s)"
                params.append(user_id)
            
            query = f"""
                SELECT DISTINCT total_balance_usdt, total_balance_brl, snapshot_date
                FROM asset_balances
                WHERE {where_clause}
                LIMIT 1
            """
            
            self.cursor.execute(query, tuple(params))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'total_balance_usdt': float(result['total_balance_usdt']),
                    'total_balance_brl': float(result['total_balance_brl']),
                    'snapshot_date': result['snapshot_date']
                }
            
            return {'total_balance_usdt': 0.0, 'total_balance_brl': 0.0, 'snapshot_date': None}
            
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo total: {str(e)}")
            return {'total_balance_usdt': 0.0, 'total_balance_brl': 0.0, 'snapshot_date': None}
    
    def get_portfolio_evolution(self, user_id, days=30):
        """
        Obtém a evolução do portfólio do usuário nos últimos dias
        
        Args:
            user_id (str): ID do usuário
            days (int): Número de dias para análise
            
        Returns:
            list: Evolução diária do portfólio
        """
        self._check_and_reconnect()
        
        try:
            query = """
                SELECT 
                    snapshot_date,
                    total_balance_usdt,
                    total_balance_brl,
                    COUNT(CASE WHEN total > 0 THEN 1 END) as active_assets
                FROM asset_balances
                WHERE user_id = %s 
                    AND snapshot_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY snapshot_date, total_balance_usdt, total_balance_brl
                ORDER BY snapshot_date DESC
            """
            
            self.cursor.execute(query, (user_id, days))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter evolução do portfólio: {str(e)}")
            return []
    
    def get_top_assets_by_value(self, user_id, limit=10, snapshot_date=None):
        """
        Obtém os ativos com maior valor na carteira
        
        Args:
            user_id (str): ID do usuário
            limit (int): Número máximo de ativos a retornar
            snapshot_date (date, opcional): Data específica do snapshot
            
        Returns:
            list: Lista dos principais ativos por valor
        """
        self._check_and_reconnect()
        
        try:
            where_clause = "user_id = %s AND total > 0"
            params = [user_id]
            
            if snapshot_date:
                where_clause += " AND snapshot_date = %s"
                params.append(snapshot_date)
            else:
                where_clause += " AND snapshot_date = (SELECT MAX(snapshot_date) FROM asset_balances WHERE user_id = %s)"
                params.append(user_id)
            
            query = f"""
                SELECT asset, total, usdt_value, brl_value, percentage_of_portfolio
                FROM asset_balances
                WHERE {where_clause}
                ORDER BY usdt_value DESC
                LIMIT %s
            """
            
            params.append(limit)
            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter principais ativos: {str(e)}")
            return []
