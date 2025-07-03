#!/usr/bin/env python3
"""
Módulo para gerenciar o banco de dados SQLite do Robot-Crypt
"""
import os
import sqlite3
import json
from datetime import datetime
import logging

class DBManager:
    """Gerencia o banco de dados SQLite do Robot-Crypt"""
    
    def __init__(self, db_path="data/robot_crypt.db"):
        """Inicializa o gerenciador de banco de dados"""
        self.logger = logging.getLogger("robot-crypt")
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.setup_tables()
    
    def connect(self):
        """Conecta ao banco de dados SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para obter resultados como dicionários
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            return False
    
    def setup_tables(self):
        """Configura as tabelas do banco de dados"""
        try:
            # Tabela de operações (versão aprimorada)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    profit_percent REAL,
                    net_profit REAL,
                    fees REAL,
                    entry_price REAL,
                    exit_price REAL,
                    volume REAL,
                    trade_duration INTEGER,
                    trade_strategy TEXT,
                    risk_percentage REAL,
                    position_size_percentage REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    balance_before REAL,
                    balance_after REAL
                )
            ''')
            
            # Tabela para estatísticas gerais
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    initial_capital REAL,
                    final_capital REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    best_trade_profit REAL,
                    worst_trade_loss REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela para o estado da aplicação
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Nova tabela para histórico de saldo
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Nova tabela para estatísticas de performance detalhadas
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_type TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    initial_capital REAL,
                    final_capital REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    avg_profit_per_trade REAL,
                    avg_loss_per_trade REAL,
                    profit_factor REAL,
                    max_consecutive_wins INTEGER,
                    max_consecutive_losses INTEGER,
                    max_drawdown REAL,
                    max_drawdown_percent REAL,
                    sharpe_ratio REAL,
                    avg_trade_duration REAL,  -- em minutos
                    best_symbol TEXT,
                    worst_symbol TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(period_type, start_date, end_date)
                )
            ''')
            
            # Nova tabela para dados de mercado
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,  -- '1m', '5m', '15m', '1h', '4h', '1d'
                    open_time DATETIME NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    quote_asset_volume REAL,
                    number_of_trades INTEGER,
                    taker_buy_base_volume REAL,
                    taker_buy_quote_volume REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, open_time)
                )
            ''')
            
            # Nova tabela para indicadores técnicos calculados
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    indicator_name TEXT NOT NULL,
                    indicator_value REAL,
                    timestamp DATETIME NOT NULL,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, indicator_name, timestamp)
                )
            ''')
            
            # Nova tabela para sinais de compra/venda identificados
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,  -- 'buy', 'sell', 'neutral'
                    signal_strength REAL,  -- 0.0 a 1.0
                    strategy TEXT NOT NULL,
                    indicator_values TEXT,  -- JSON com valores dos indicadores
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao configurar tabelas: {str(e)}")
            return False
    
    def register_operation(self, symbol, operation_type, quantity, price, profit_percent=None, net_profit=None, fees=None):
        """Registra uma operação no banco de dados"""
        try:
            self.cursor.execute('''
                INSERT INTO operations (symbol, operation_type, quantity, price, profit_percent, net_profit, fees)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, operation_type, quantity, price, profit_percent, net_profit, fees))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Erro ao registrar operação: {str(e)}")
            return None
    
    def update_daily_stats(self, stats):
        """Atualiza ou insere estatísticas diárias"""
        today = datetime.now().date().isoformat()
        try:
            # Garantir que temos todas as chaves necessárias com valores padrão
            # Isso evita KeyError quando algum campo estiver faltando
            default_stats = {
                'current_capital': 100.0,  # Valor padrão para capital
                'initial_capital': 100.0,  # Valor padrão para capital inicial
                'total_trades': 0,         # Valor padrão para total de trades
                'winning_trades': 0,       # Valor padrão para trades com lucro
                'losing_trades': 0,        # Valor padrão para trades com prejuízo
                'best_trade_profit': 0.0,  # Valor padrão para melhor trade
                'worst_trade_loss': 0.0    # Valor padrão para pior trade
            }
            
            # Atualiza os valores padrão com os valores reais, se existirem
            for key, default_value in default_stats.items():
                if key not in stats:
                    self.logger.warning(f"Estatística '{key}' não encontrada, usando valor padrão: {default_value}")
                    stats[key] = default_value
            
            # Verifica se já existe uma entrada para hoje
            self.cursor.execute('SELECT id FROM stats WHERE date = ?', (today,))
            result = self.cursor.fetchone()
            
            if result:
                # Atualiza estatísticas existentes
                self.cursor.execute('''
                    UPDATE stats SET
                    final_capital = ?,
                    total_trades = ?,
                    winning_trades = ?,
                    losing_trades = ?,
                    best_trade_profit = ?,
                    worst_trade_loss = ?
                    WHERE date = ?
                ''', (
                    stats['current_capital'],
                    stats['total_trades'],
                    stats['winning_trades'],
                    stats['losing_trades'],
                    stats['best_trade_profit'],
                    stats['worst_trade_loss'],
                    today
                ))
            else:
                # Insere novas estatísticas
                self.cursor.execute('''
                    INSERT INTO stats (date, initial_capital, final_capital, total_trades, 
                                     winning_trades, losing_trades, best_trade_profit, worst_trade_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today,
                    stats['initial_capital'],
                    stats['current_capital'],
                    stats['total_trades'],
                    stats['winning_trades'],
                    stats['losing_trades'],
                    stats['best_trade_profit'],
                    stats['worst_trade_loss']
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao atualizar estatísticas: {str(e)}")
            return False
    
    def save_app_state(self, state_data):
        """Salva o estado da aplicação"""
        try:
            json_data = json.dumps(state_data)
            self.cursor.execute('''
                INSERT INTO app_state (state_data)
                VALUES (?)
            ''', (json_data,))
            self.conn.commit()
            
            # Manter apenas os 10 estados mais recentes
            self.cursor.execute('''
                DELETE FROM app_state 
                WHERE id NOT IN (
                    SELECT id FROM app_state ORDER BY timestamp DESC LIMIT 10
                )
            ''')
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado da aplicação: {str(e)}")
            return False
    
    def load_last_app_state(self):
        """Carrega o último estado da aplicação"""
        try:
            self.cursor.execute('SELECT state_data FROM app_state ORDER BY timestamp DESC LIMIT 1')
            result = self.cursor.fetchone()
            if result:
                return json.loads(result['state_data'])
            return None
        except Exception as e:
            self.logger.error(f"Erro ao carregar estado da aplicação: {str(e)}")
            return None
    
    def get_operations_history(self, limit=100):
        """Obtém histórico de operações"""
        try:
            self.cursor.execute('''
                SELECT * FROM operations ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de operações: {str(e)}")
            return []
    
    def get_stats_history(self, days=30):
        """Obtém histórico de estatísticas"""
        try:
            self.cursor.execute('''
                SELECT * FROM stats ORDER BY date DESC LIMIT ?
            ''', (days,))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de estatísticas: {str(e)}")
            return []
    
    def migrate_db_stats(self):
        """Migra estatísticas do banco de dados para o novo formato de nomes de campo"""
        try:
            # Verifica se há alguma entrada na tabela stats
            self.cursor.execute('SELECT COUNT(*) as count FROM stats')
            result = self.cursor.fetchone()
            if result and result['count'] > 0:
                self.logger.info(f"Encontradas {result['count']} entradas na tabela stats para migração")
                
                # Verifica se as colunas antigas existem (isso pode ser uma operação complexa no SQLite)
                # Como alternativa, vamos tentar carregar dados de app_state e migrar para o banco
                
                # Carrega o último estado da aplicação
                last_state = self.load_last_app_state()
                if last_state and 'stats' in last_state:
                    stats = last_state['stats']
                    
                    # Mapeia chaves antigas para novas se necessário
                    key_mapping = {
                        'trades_total': 'total_trades',
                        'trades_win': 'winning_trades',
                        'trades_loss': 'losing_trades'
                    }
                    
                    # Verifica se precisamos migrar
                    needs_migration = False
                    for old_key, new_key in key_mapping.items():
                        if old_key in stats and new_key not in stats:
                            stats[new_key] = stats[old_key]
                            self.logger.info(f"Migrando {old_key} para {new_key} no estado do banco de dados")
                            needs_migration = True
                    
                    if needs_migration:
                        # Salva o estado migrado de volta no banco
                        self.save_app_state(last_state)
                        self.logger.info("Estado migrado salvo com sucesso no banco de dados")
                    else:
                        self.logger.info("Nenhuma migração necessária para o estado no banco de dados")
                return True
            else:
                self.logger.info("Nenhuma entrada na tabela stats para migrar")
                return True
        except Exception as e:
            self.logger.error(f"Erro ao migrar estatísticas do banco de dados: {str(e)}")
            return False
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
