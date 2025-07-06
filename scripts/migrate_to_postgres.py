#!/usr/bin/env python3
"""
Script de Migração: SQLite para PostgreSQL

Este script migra dados do sistema de treinamento SQLite existente
para o novo sistema PostgreSQL integrado.
"""

import asyncio
import sqlite3
import logging
import sys
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    # Se python-dotenv não estiver instalado, tenta carregar manualmente
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database.postgres_manager import PostgresManager
from ml.postgres_training_system import PostgresTradingDataProcessor, TrainingFeatures, TrainingSignal


class SQLiteToPostgresMigrator:
    """Migra dados do sistema SQLite para PostgreSQL"""
    
    def __init__(self, sqlite_path: str, config_path: str = "config/training_config.yaml"):
        self.sqlite_path = sqlite_path
        self.config_path = config_path
        self.postgres_manager = None
        self.data_processor = None
        self.logger = logging.getLogger(__name__)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self) -> Dict:
        """Carrega configuração do PostgreSQL"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return {}
    
    async def initialize_postgres(self):
        """Inicializa conexão PostgreSQL"""
        try:
            # Usar variáveis de ambiente do .env
            self.postgres_manager = PostgresManager()
            self.postgres_manager.connect()
            self.data_processor = PostgresTradingDataProcessor(self.postgres_manager)
            
            self.logger.info("Conexão PostgreSQL inicializada com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar PostgreSQL: {e}")
            raise
    
    def connect_sqlite(self) -> sqlite3.Connection:
        """Conecta ao banco SQLite"""
        try:
            if not Path(self.sqlite_path).exists():
                raise FileNotFoundError(f"Banco SQLite não encontrado: {self.sqlite_path}")
            
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            
            self.logger.info(f"Conectado ao SQLite: {self.sqlite_path}")
            return conn
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar SQLite: {e}")
            raise
    
    def get_sqlite_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Lista tabelas do SQLite"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.logger.info(f"Tabelas encontradas no SQLite: {tables}")
            return tables
            
        except Exception as e:
            self.logger.error(f"Erro ao listar tabelas SQLite: {e}")
            return []
    
    async def migrate_market_data(self, conn: sqlite3.Connection):
        """Migra dados de mercado"""
        try:
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_data'")
            if not cursor.fetchone():
                self.logger.warning("Tabela 'market_data' não encontrada no SQLite")
                return
            
            # Buscar dados de mercado
            cursor.execute("""
                SELECT symbol, timestamp, open, high, low, close, volume
                FROM market_data
                ORDER BY timestamp
            """)
            
            rows = cursor.fetchall()
            migrated_count = 0
            
            for row in rows:
                try:
                    # Converter timestamp se necessário
                    timestamp = row['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    
                    # Salvar no PostgreSQL
                    await self.postgres_manager.save_market_data(
                        symbol=row['symbol'],
                        price=float(row['close']),
                        volume=float(row['volume']),
                        high=float(row['high']),
                        low=float(row['low']),
                        open_price=float(row['open']),
                        timestamp=timestamp
                    )
                    
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        self.logger.info(f"Migrados {migrated_count} registros de market_data")
                
                except Exception as e:
                    self.logger.error(f"Erro ao migrar registro de market_data: {e}")
                    continue
            
            self.logger.info(f"Migração de market_data concluída: {migrated_count} registros")
            
        except Exception as e:
            self.logger.error(f"Erro na migração de market_data: {e}")
    
    async def migrate_training_features(self, conn: sqlite3.Connection):
        """Migra features de treinamento"""
        try:
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_features'")
            if not cursor.fetchone():
                self.logger.warning("Tabela 'training_features' não encontrada no SQLite")
                return
            
            # Buscar schema da tabela
            cursor.execute("PRAGMA table_info(training_features)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Buscar dados
            cursor.execute("SELECT * FROM training_features ORDER BY timestamp")
            rows = cursor.fetchall()
            migrated_count = 0
            
            for row in rows:
                try:
                    # Converter dados para TrainingFeatures
                    row_dict = dict(row)
                    
                    # Converter timestamp
                    timestamp = row_dict.get('timestamp')
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    
                    # Criar objeto TrainingFeatures
                    features = TrainingFeatures(
                        symbol=row_dict.get('symbol', ''),
                        timestamp=timestamp,
                        price=float(row_dict.get('price', 0)),
                        volume=float(row_dict.get('volume', 0)),
                        price_change_1h=float(row_dict.get('price_change_1h', 0)),
                        price_change_4h=float(row_dict.get('price_change_4h', 0)),
                        price_change_24h=float(row_dict.get('price_change_24h', 0)),
                        volume_change_24h=float(row_dict.get('volume_change_24h', 0)),
                        volatility_24h=float(row_dict.get('volatility_24h', 0)),
                        sma_10=float(row_dict.get('sma_10', 0)),
                        sma_20=float(row_dict.get('sma_20', 0)),
                        sma_50=float(row_dict.get('sma_50', 0)),
                        ema_12=float(row_dict.get('ema_12', 0)),
                        ema_26=float(row_dict.get('ema_26', 0)),
                        rsi_14=float(row_dict.get('rsi_14', 0)),
                        macd=float(row_dict.get('macd', 0)),
                        macd_signal=float(row_dict.get('macd_signal', 0)),
                        macd_hist=float(row_dict.get('macd_hist', 0)),
                        bb_upper=float(row_dict.get('bb_upper', 0)),
                        bb_lower=float(row_dict.get('bb_lower', 0)),
                        bb_middle=float(row_dict.get('bb_middle', 0)),
                        stoch_k=float(row_dict.get('stoch_k', 0)),
                        stoch_d=float(row_dict.get('stoch_d', 0)),
                        cci=float(row_dict.get('cci', 0)),
                        williams_r=float(row_dict.get('williams_r', 0)),
                        atr=float(row_dict.get('atr', 0)),
                        volume_sma=float(row_dict.get('volume_sma', 0)),
                        news_sentiment=float(row_dict.get('news_sentiment', 0)),
                        social_sentiment=float(row_dict.get('social_sentiment', 0)),
                        fear_greed_index=float(row_dict.get('fear_greed_index', 0)),
                        upcoming_events=int(row_dict.get('upcoming_events', 0)),
                        event_impact=float(row_dict.get('event_impact', 0))
                    )
                    
                    # Salvar no PostgreSQL
                    await self.data_processor.save_training_features(features)
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        self.logger.info(f"Migrados {migrated_count} registros de training_features")
                
                except Exception as e:
                    self.logger.error(f"Erro ao migrar registro de training_features: {e}")
                    continue
            
            self.logger.info(f"Migração de training_features concluída: {migrated_count} registros")
            
        except Exception as e:
            self.logger.error(f"Erro na migração de training_features: {e}")
    
    async def migrate_training_signals(self, conn: sqlite3.Connection):
        """Migra sinais de treinamento"""
        try:
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_signals'")
            if not cursor.fetchone():
                self.logger.warning("Tabela 'training_signals' não encontrada no SQLite")
                return
            
            # Buscar dados
            cursor.execute("SELECT * FROM training_signals ORDER BY timestamp")
            rows = cursor.fetchall()
            migrated_count = 0
            
            for row in rows:
                try:
                    row_dict = dict(row)
                    
                    # Converter timestamp
                    timestamp = row_dict.get('timestamp')
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    
                    # Criar objeto TrainingSignal
                    signal = TrainingSignal(
                        symbol=row_dict.get('symbol', ''),
                        timestamp=timestamp,
                        signal_type=row_dict.get('signal_type', 'HOLD'),
                        confidence=float(row_dict.get('confidence', 0.5)),
                        price_target=float(row_dict.get('price_target')) if row_dict.get('price_target') else None,
                        stop_loss=float(row_dict.get('stop_loss')) if row_dict.get('stop_loss') else None,
                        take_profit=float(row_dict.get('take_profit')) if row_dict.get('take_profit') else None,
                        reasoning=row_dict.get('reasoning')
                    )
                    
                    # Salvar no PostgreSQL
                    await self.data_processor.save_training_signal(signal)
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        self.logger.info(f"Migrados {migrated_count} registros de training_signals")
                
                except Exception as e:
                    self.logger.error(f"Erro ao migrar registro de training_signals: {e}")
                    continue
            
            self.logger.info(f"Migração de training_signals concluída: {migrated_count} registros")
            
        except Exception as e:
            self.logger.error(f"Erro na migração de training_signals: {e}")
    
    async def migrate_training_logs(self, conn: sqlite3.Connection):
        """Migra logs de treinamento"""
        try:
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_logs'")
            if not cursor.fetchone():
                self.logger.warning("Tabela 'training_logs' não encontrada no SQLite")
                return
            
            # Buscar dados
            cursor.execute("SELECT * FROM training_logs ORDER BY timestamp")
            rows = cursor.fetchall()
            migrated_count = 0
            
            for row in rows:
                try:
                    row_dict = dict(row)
                    
                    # Converter timestamp
                    timestamp = row_dict.get('timestamp')
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    
                    # Salvar log no PostgreSQL
                    await self.postgres_manager.save_log(
                        log_type='training_migration',
                        message=row_dict.get('message', 'Migração de log de treinamento'),
                        details=str(row_dict.get('details', {})),
                        timestamp=timestamp
                    )
                    
                    migrated_count += 1
                    
                    if migrated_count % 50 == 0:
                        self.logger.info(f"Migrados {migrated_count} registros de training_logs")
                
                except Exception as e:
                    self.logger.error(f"Erro ao migrar registro de training_logs: {e}")
                    continue
            
            self.logger.info(f"Migração de training_logs concluída: {migrated_count} registros")
            
        except Exception as e:
            self.logger.error(f"Erro na migração de training_logs: {e}")
    
    async def verify_migration(self):
        """Verifica a migração comparando contagens"""
        try:
            self.logger.info("Verificando migração...")
            
            # Conectar ao SQLite para contagem
            sqlite_conn = self.connect_sqlite()
            cursor = sqlite_conn.cursor()
            
            # Verificar tabelas e contar registros
            tables_to_check = ['market_data', 'training_features', 'training_signals', 'training_logs']
            
            for table in tables_to_check:
                try:
                    # Contar no SQLite
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    sqlite_count = cursor.fetchone()[0]
                    
                    # Contar no PostgreSQL (adaptando nomes das tabelas)
                    if table == 'training_logs':
                        pg_query = "SELECT COUNT(*) FROM trading_logs WHERE log_type = 'training_migration'"
                    else:
                        pg_query = f"SELECT COUNT(*) FROM {table}"
                    
                    pg_result = await self.postgres_manager.fetch_one(pg_query)
                    pg_count = pg_result[0] if pg_result else 0
                    
                    self.logger.info(f"Tabela {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                    
                    if sqlite_count != pg_count and table != 'training_logs':
                        self.logger.warning(f"Divergência na tabela {table}!")
                
                except Exception as e:
                    self.logger.error(f"Erro ao verificar tabela {table}: {e}")
            
            sqlite_conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de migração: {e}")
    
    async def run_full_migration(self):
        """Executa migração completa"""
        try:
            self.logger.info("Iniciando migração completa SQLite -> PostgreSQL")
            
            # Inicializar PostgreSQL
            await self.initialize_postgres()
            
            # Conectar SQLite
            sqlite_conn = self.connect_sqlite()
            
            # Listar tabelas disponíveis
            tables = self.get_sqlite_tables(sqlite_conn)
            
            # Migrar dados por categoria
            await self.migrate_market_data(sqlite_conn)
            await self.migrate_training_features(sqlite_conn)
            await self.migrate_training_signals(sqlite_conn)
            await self.migrate_training_logs(sqlite_conn)
            
            # Verificar migração
            await self.verify_migration()
            
            # Fechar conexões
            sqlite_conn.close()
            
            self.logger.info("Migração concluída com sucesso!")
            
        except Exception as e:
            self.logger.error(f"Erro na migração: {e}")
            raise
        finally:
            if self.postgres_manager:
                await self.postgres_manager.disconnect()


async def main():
    """Função principal do script de migração"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migra dados de SQLite para PostgreSQL')
    parser.add_argument('sqlite_path', help='Caminho para o arquivo SQLite')
    parser.add_argument('--config', default='config/training_config.yaml', 
                       help='Caminho para arquivo de configuração')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Apenas verificar migração existente')
    
    args = parser.parse_args()
    
    migrator = SQLiteToPostgresMigrator(args.sqlite_path, args.config)
    
    try:
        if args.verify_only:
            await migrator.initialize_postgres()
            await migrator.verify_migration()
        else:
            await migrator.run_full_migration()
            
    except KeyboardInterrupt:
        print("\nMigração interrompida pelo usuário")
    except Exception as e:
        print(f"Erro durante migração: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
