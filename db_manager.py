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
            # Tabela de operações
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
                    fees REAL
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
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
