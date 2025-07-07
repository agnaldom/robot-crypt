#!/usr/bin/env python3
"""
Script de Treinamento do Modelo - Versão PostgreSQL

Este script utiliza o novo sistema de treinamento integrado com PostgreSQL
para treinar o modelo de ML do robô de trading.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from ml.postgres_training_system import PostgresTradingTrainer
from src.utils.logging_config import setup_logging


class PostgresTrainingCLI:
    """Interface de linha de comando para treinamento PostgreSQL"""
    
    def __init__(self, config_path: str = "config/training_config.yaml"):
        self.config_path = config_path
        self.trainer = None
        self.logger = None
        
    def setup_logging(self):
        """Configura logging do sistema"""
        try:
            self.logger = setup_logging("training_cli", log_to_file=True)
            self.logger.info("Sistema de logging inicializado")
        except Exception as e:
            # Fallback para logging básico
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Fallback para logging básico: {e}")
    
    async def initialize_trainer(self):
        """Inicializa o trainer"""
        try:
            self.trainer = PostgresTradingTrainer(self.config_path)
            await self.trainer.initialize()
            self.logger.info("Trainer inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar trainer: {e}")
            raise
    
    async def train_model(self, symbols: list = None, days: int = 30):
        """Treina o modelo"""
        try:
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            self.logger.info(f"Iniciando treinamento para {symbols} com {days} dias de histórico")
            
            # Executar treinamento
            metrics = await self.trainer.train_model(symbols, days)
            
            # Exibir métricas
            self.logger.info("=== MÉTRICAS DO TREINAMENTO ===")
            for metric_name, value in metrics.items():
                self.logger.info(f"{metric_name}: {value}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro durante treinamento: {e}")
            raise
    
    async def generate_signals(self, symbols: list = None):
        """Gera sinais de trading"""
        try:
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            self.logger.info(f"Gerando sinais para {symbols}")
            
            # Gerar sinais
            signals = await self.trainer.generate_signals(symbols)
            
            # Exibir sinais
            self.logger.info("=== SINAIS GERADOS ===")
            for signal in signals:
                self.logger.info(
                    f"{signal.symbol}: {signal.signal_type} "
                    f"(Confiança: {signal.confidence:.2f})"
                )
                if signal.reasoning:
                    self.logger.info(f"  Razão: {signal.reasoning}")
                if signal.price_target:
                    self.logger.info(f"  Alvo: {signal.price_target}")
                if signal.stop_loss:
                    self.logger.info(f"  Stop Loss: {signal.stop_loss}")
                if signal.take_profit:
                    self.logger.info(f"  Take Profit: {signal.take_profit}")
                self.logger.info("-" * 50)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinais: {e}")
            raise
    
    async def show_model_info(self):
        """Exibe informações do modelo"""
        try:
            self.logger.info("=== INFORMAÇÕES DO MODELO ===")
            
            # Verificar se modelo existe
            if not self.trainer.model.model:
                self.logger.info("Modelo não está treinado")
                return
            
            # Informações básicas
            model_type = type(self.trainer.model.model).__name__
            self.logger.info(f"Tipo do modelo: {model_type}")
            
            # Últimos dados de treinamento
            try:
                last_training = await self.trainer.data_processor.get_last_training_log()
                if last_training:
                    self.logger.info(f"Último treinamento: {last_training}")
                else:
                    self.logger.info("Nenhum histórico de treinamento encontrado")
            except Exception as e:
                self.logger.warning(f"Erro ao buscar histórico: {e}")
            
            # Estatísticas de features
            try:
                features_count = await self.trainer.data_processor.get_features_count()
                self.logger.info(f"Total de features armazenadas: {features_count}")
            except Exception as e:
                self.logger.warning(f"Erro ao buscar contagem de features: {e}")
            
            # Estatísticas de sinais
            try:
                signals_count = await self.trainer.data_processor.get_signals_count()
                self.logger.info(f"Total de sinais gerados: {signals_count}")
            except Exception as e:
                self.logger.warning(f"Erro ao buscar contagem de sinais: {e}")
            
        except Exception as e:
            self.logger.error(f"Erro ao exibir informações: {e}")
            raise
    
    async def continuous_training(self, symbols: list = None, interval_hours: int = 6):
        """Executa treinamento contínuo"""
        try:
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            self.logger.info(f"Iniciando treinamento contínuo a cada {interval_hours} horas")
            self.logger.info(f"Símbolos: {symbols}")
            self.logger.info("Pressione Ctrl+C para parar")
            
            cycle_count = 0
            
            while True:
                try:
                    cycle_count += 1
                    self.logger.info(f"=== CICLO {cycle_count} ===")
                    
                    # Treinar modelo
                    await self.train_model(symbols, days=7)  # Usar menos dias para treinos frequentes
                    
                    # Gerar sinais
                    await self.generate_signals(symbols)
                    
                    # Aguardar próximo ciclo
                    next_run = datetime.now() + timedelta(hours=interval_hours)
                    self.logger.info(f"Próximo treinamento em: {next_run}")
                    
                    await asyncio.sleep(interval_hours * 3600)  # Converter para segundos
                    
                except KeyboardInterrupt:
                    self.logger.info("Treinamento contínuo interrompido pelo usuário")
                    break
                except Exception as e:
                    self.logger.error(f"Erro no ciclo {cycle_count}: {e}")
                    # Aguardar 10 minutos antes de tentar novamente
                    self.logger.info("Aguardando 10 minutos antes de tentar novamente...")
                    await asyncio.sleep(600)
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro no treinamento contínuo: {e}")
            raise
    
    async def cleanup(self):
        """Limpa recursos"""
        try:
            if self.trainer:
                await self.trainer.cleanup()
                self.logger.info("Recursos limpos com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos: {e}")


async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Treinamento do Modelo - PostgreSQL')
    parser.add_argument('--config', default='config/training_config.yaml',
                       help='Caminho para arquivo de configuração')
    parser.add_argument('--symbols', nargs='+', 
                       help='Símbolos para treinar (ex: BTC/USDT ETH/USDT)')
    parser.add_argument('--days', type=int, default=30,
                       help='Dias de histórico para treinamento')
    parser.add_argument('--continuous', action='store_true',
                       help='Executa treinamento contínuo')
    parser.add_argument('--interval', type=int, default=6,
                       help='Intervalo em horas para treinamento contínuo')
    parser.add_argument('--signals-only', action='store_true',
                       help='Apenas gera sinais sem treinar')
    parser.add_argument('--info', action='store_true',
                       help='Exibe informações do modelo')
    
    args = parser.parse_args()
    
    # Inicializar CLI
    cli = PostgresTrainingCLI(args.config)
    cli.setup_logging()
    
    try:
        # Inicializar trainer
        await cli.initialize_trainer()
        
        # Executar ação solicitada
        if args.info:
            await cli.show_model_info()
        elif args.signals_only:
            await cli.generate_signals(args.symbols)
        elif args.continuous:
            await cli.continuous_training(args.symbols, args.interval)
        else:
            # Treinamento single-shot
            await cli.train_model(args.symbols, args.days)
            
            # Gerar sinais após treinamento
            await cli.generate_signals(args.symbols)
    
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")
    except Exception as e:
        print(f"Erro durante execução: {e}")
        sys.exit(1)
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
