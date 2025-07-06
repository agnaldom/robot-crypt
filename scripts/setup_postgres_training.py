#!/usr/bin/env python3
"""
Script de Setup Completo - PostgreSQL Training Pipeline

Este script executa todo o pipeline de migração e treinamento:
1. Migração de dados SQLite para PostgreSQL
2. Treinamento inicial do modelo
3. Geração de sinais
4. Verificação da configuração
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
import logging
import os

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

from ml.postgres_training_system import PostgresTradingTrainer
from database.postgres_manager import PostgresManager
from utils.logging_config import setup_logging

# Importar o script de migração
sys.path.append(str(Path(__file__).parent))
from migrate_to_postgres import SQLiteToPostgresMigrator


class PostgresTrainingPipeline:
    """Pipeline completo para setup do sistema PostgreSQL"""
    
    def __init__(self, config_path: str = "config/training_config.yaml"):
        self.config_path = config_path
        self.logger = None
        self.postgres_manager = None
        self.trainer = None
        self.migrator = None
        
    def setup_logging(self):
        """Configura logging do sistema"""
        try:
            self.logger = setup_logging("postgres_pipeline", log_to_file=True)
            self.logger.info("Sistema de logging inicializado")
        except Exception as e:
            # Fallback para logging básico
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Fallback para logging básico: {e}")
    
    async def initialize_components(self):
        """Inicializa todos os componentes"""
        try:
            self.logger.info("Inicializando componentes...")
            
            # Inicializar PostgresManager
            self.postgres_manager = PostgresManager()
            self.postgres_manager.connect()
            self.logger.info("PostgresManager inicializado")
            
            # Inicializar Trainer
            self.trainer = PostgresTradingTrainer(self.config_path)
            await self.trainer.initialize()
            self.logger.info("Trainer inicializado")
            
            # Inicializar Migrator
            self.migrator = SQLiteToPostgresMigrator(
                sqlite_path="",  # Será definido quando necessário
                config_path=self.config_path
            )
            self.logger.info("Migrator inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar componentes: {e}")
            raise
    
    async def check_database_status(self):
        """Verifica o status do banco de dados"""
        try:
            self.logger.info("=== VERIFICANDO STATUS DO BANCO ===")
            
            # Verificar conexão
            self.postgres_manager.connect()
            self.logger.info("✓ Conexão com PostgreSQL estabelecida")
            
            # Verificar tabelas
            tables = [
                'market_data', 'training_features', 'trading_signals',
                'trading_logs', 'model_performance', 'technical_indicators'
            ]
            
            for table in tables:
                try:
                    query = f"SELECT COUNT(*) FROM {table}"
                    result = self.postgres_manager.fetch_one(query)
                    count = result[0] if result else 0
                    self.logger.info(f"✓ Tabela {table}: {count} registros")
                except Exception as e:
                    self.logger.warning(f"✗ Tabela {table}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar banco: {e}")
            return False
    
    async def migrate_data(self, sqlite_path: str = None):
        """Executa migração de dados SQLite para PostgreSQL"""
        try:
            self.logger.info("=== INICIANDO MIGRAÇÃO DE DADOS ===")
            
            if not sqlite_path:
                # Procurar arquivo SQLite padrão
                possible_paths = [
                    "data/trading_data.db",
                    "trading_data.db",
                    "ml_training.db"
                ]
                
                for path in possible_paths:
                    if Path(path).exists():
                        sqlite_path = path
                        break
                
                if not sqlite_path:
                    self.logger.warning("Arquivo SQLite não encontrado. Pulando migração.")
                    return False
            
            self.logger.info(f"Migrando dados de: {sqlite_path}")
            
            # Definir o caminho do SQLite no migrator
            self.migrator.sqlite_path = sqlite_path
            
            # Executar migração completa
            await self.migrator.run_full_migration()
            success = True
            
            if success:
                self.logger.info("✓ Migração concluída com sucesso")
                return True
            else:
                self.logger.error("✗ Migração falhou")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante migração: {e}")
            return False
    
    async def run_initial_training(self, symbols: list = None, days: int = 30):
        """Executa treinamento inicial"""
        try:
            self.logger.info("=== INICIANDO TREINAMENTO INICIAL ===")
            
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            self.logger.info(f"Símbolos: {symbols}")
            self.logger.info(f"Dias de histórico: {days}")
            
            # Executar treinamento
            metrics = await self.trainer.train_model(symbols, days)
            
            # Exibir resultados
            self.logger.info("=== MÉTRICAS DO TREINAMENTO ===")
            for metric_name, value in metrics.items():
                self.logger.info(f"{metric_name}: {value}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro durante treinamento inicial: {e}")
            raise
    
    async def generate_initial_signals(self, symbols: list = None):
        """Gera sinais iniciais"""
        try:
            self.logger.info("=== GERANDO SINAIS INICIAIS ===")
            
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            # Gerar sinais
            signals = await self.trainer.generate_signals(symbols)
            
            # Exibir sinais
            self.logger.info(f"Sinais gerados: {len(signals)}")
            for signal in signals:
                self.logger.info(
                    f"  {signal.symbol}: {signal.signal_type} "
                    f"(Confiança: {signal.confidence:.2f})"
                )
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais iniciais: {e}")
            raise
    
    async def run_health_check(self):
        """Executa verificação de saúde do sistema"""
        try:
            self.logger.info("=== VERIFICAÇÃO DE SAÚDE ===")
            
            # Verificar modelo
            if not self.trainer.model.model:
                self.logger.warning("✗ Modelo não está treinado")
                return False
            else:
                self.logger.info("✓ Modelo está carregado")
            
            # Verificar dados de treinamento
            features_count = self.trainer.data_processor.get_features_count()
            signals_count = self.trainer.data_processor.get_signals_count()
            
            self.logger.info(f"✓ Features de treinamento: {features_count}")
            self.logger.info(f"✓ Sinais gerados: {signals_count}")
            
            # Verificar últimos dados
            try:
                last_training = self.trainer.data_processor.get_last_training_log()
                if last_training and "Nenhum" not in last_training:
                    self.logger.info(f"✓ Último treinamento: {last_training}")
                else:
                    self.logger.warning(f"✗ {last_training}")
            except Exception as e:
                self.logger.warning(f"✗ Erro ao verificar histórico: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de saúde: {e}")
            return False
    
    async def cleanup(self):
        """Limpa recursos"""
        try:
            if self.postgres_manager:
                self.postgres_manager.disconnect()
            self.logger.info("Recursos limpos com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos: {e}")


async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Setup Completo - PostgreSQL Training Pipeline')
    parser.add_argument('--config', default='config/training_config.yaml',
                       help='Caminho para arquivo de configuração')
    parser.add_argument('--sqlite-path', 
                       help='Caminho para arquivo SQLite (opcional)')
    parser.add_argument('--symbols', nargs='+', 
                       help='Símbolos para treinar (ex: BTC/USDT ETH/USDT)')
    parser.add_argument('--days', type=int, default=30,
                       help='Dias de histórico para treinamento')
    parser.add_argument('--skip-migration', action='store_true',
                       help='Pula a migração de dados')
    parser.add_argument('--skip-training', action='store_true',
                       help='Pula o treinamento inicial')
    parser.add_argument('--check-only', action='store_true',
                       help='Apenas verifica o status do sistema')
    
    args = parser.parse_args()
    
    # Inicializar pipeline
    pipeline = PostgresTrainingPipeline(args.config)
    pipeline.setup_logging()
    
    try:
        # Inicializar componentes
        await pipeline.initialize_components()
        
        # Verificar status inicial
        db_status = await pipeline.check_database_status()
        
        if args.check_only:
            # Apenas verificar e sair
            await pipeline.run_health_check()
            return
        
        # Migração de dados (se necessário)
        if not args.skip_migration:
            migration_success = await pipeline.migrate_data(args.sqlite_path)
            if migration_success:
                pipeline.logger.info("Migração concluída com sucesso")
            else:
                pipeline.logger.warning("Migração não foi executada ou falhou")
        
        # Treinamento inicial
        if not args.skip_training:
            await pipeline.run_initial_training(args.symbols, args.days)
            
            # Gerar sinais iniciais
            await pipeline.generate_initial_signals(args.symbols)
        
        # Verificação final
        health_ok = await pipeline.run_health_check()
        
        if health_ok:
            pipeline.logger.info("✓ Sistema configurado com sucesso!")
            pipeline.logger.info("✓ Pronto para uso!")
            
            # Instruções de uso
            pipeline.logger.info("\n=== PRÓXIMOS PASSOS ===")
            pipeline.logger.info("1. Para treinar o modelo:")
            pipeline.logger.info("   python scripts/train_model_postgres.py")
            pipeline.logger.info("2. Para treinamento contínuo:")
            pipeline.logger.info("   python scripts/train_model_postgres.py --continuous")
            pipeline.logger.info("3. Para gerar apenas sinais:")
            pipeline.logger.info("   python scripts/train_model_postgres.py --signals-only")
            pipeline.logger.info("4. Para verificar informações do modelo:")
            pipeline.logger.info("   python scripts/train_model_postgres.py --info")
        else:
            pipeline.logger.error("✗ Sistema não está funcionando corretamente")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")
    except Exception as e:
        print(f"Erro durante execução: {e}")
        sys.exit(1)
    finally:
        await pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
