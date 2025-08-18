#!/usr/bin/env python3
"""
🚀 Executável Principal da Estratégia de Breakout Avançada

Este script executa a estratégia de breakout com análise de fluxo de ordens,
usando configurações do arquivo .env.breakout

Uso:
    python run_breakout_strategy.py

Configuração:
    1. Copie .env.breakout.example para .env.breakout
    2. Configure suas credenciais BingX
    3. Ajuste os parâmetros de risco conforme necessário
    4. Execute o script

Funcionalidades:
    - Detecção de breakout com confirmação de volume
    - Análise de desequilíbrio do livro de ordens
    - Execução automatizada com alavancagem isolada 20x
    - Gestão de risco com SL/TP dinâmicos
    - Monitoramento de posições com trailing stop
    - Notificações via Telegram/Email
"""

import asyncio
import os
import sys
import signal
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.strategies.advanced_breakout_strategy import (
    AdvancedBreakoutStrategy,
    RiskParameters
)
from config.breakout_strategy_config import BreakoutStrategyConfig
from src.core.logging_setup import logger


class BreakoutStrategyRunner:
    """
    Executor principal da estratégia de breakout
    """
    
    def __init__(self):
        self.strategy = None
        self.config = None
        self.running = False
        
        # Configurar handlers para sinais
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """
        Handler para sinais de interrupção
        """
        logger.info(f"🛑 Sinal recebido: {signum}. Encerrando estratégia...")
        self.running = False
    
    def load_environment(self):
        """
        Carrega variáveis de ambiente
        """
        env_files = [
            '.env.breakout',
            '.env.local',
            '.env'
        ]
        
        for env_file in env_files:
            env_path = project_root / env_file
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"📁 Carregado arquivo de ambiente: {env_file}")
                break
        else:
            logger.warning("⚠️ Nenhum arquivo de ambiente encontrado. Usando variáveis do sistema.")
    
    def initialize_strategy(self):
        """
        Inicializa a estratégia com configurações
        """
        try:
            # Carregar configurações
            self.config = BreakoutStrategyConfig()
            
            # Validar configurações
            errors = self.config.validate_config()
            if errors:
                logger.error("❌ Erros de configuração:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # Imprimir configuração
            logger.info("📊 Configuração carregada com sucesso")
            self.config.print_config()
            
            # Criar parâmetros de risco
            risk_params = RiskParameters(
                risk_per_trade=self.config.risk_management.risk_per_trade,
                leverage=self.config.risk_management.leverage,
                risk_reward_ratio=self.config.risk_management.risk_reward_ratio,
                max_position_size=self.config.risk_management.max_position_size
            )
            
            # Inicializar estratégia
            self.strategy = AdvancedBreakoutStrategy(
                api_key=self.config.bingx.api_key,
                api_secret=self.config.bingx.api_secret,
                testnet=self.config.bingx.testnet,
                risk_params=risk_params
            )
            
            # Aplicar configurações específicas
            self.strategy.min_volume_increase = self.config.breakout_detection.min_volume_increase
            self.strategy.lookback_periods = self.config.breakout_detection.lookback_periods
            self.strategy.min_confidence = self.config.breakout_detection.min_confidence
            
            logger.info("✅ Estratégia inicializada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar estratégia: {e}")
            return False
    
    def setup_logging(self):
        """
        Configura logging baseado nas configurações
        """
        try:
            import logging
            from logging.handlers import RotatingFileHandler
            
            # Criar diretório de logs se não existir
            log_dir = Path(self.config.logging.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar handler de arquivo
            file_handler = RotatingFileHandler(
                filename=self.config.logging.log_file,
                maxBytes=self.config.logging.max_log_size,
                backupCount=self.config.logging.backup_count
            )
            
            # Configurar formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Configurar nível de log
            log_level = getattr(logging, self.config.logging.log_level.upper())
            
            # Configurar logger principal
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            root_logger.addHandler(file_handler)
            
            logger.info(f"📝 Logging configurado: {self.config.logging.log_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar logging: {e}")
    
    async def run_strategy(self):
        """
        Executa a estratégia principal
        """
        try:
            self.running = True
            
            logger.info("🚀 Iniciando estratégia de breakout...")
            logger.info(f"📊 Símbolos: {self.config.trading.symbols}")
            logger.info(f"⏰ Intervalo de verificação: {self.config.trading.check_interval}s")
            logger.info(f"🎯 Modo: {'TESTNET' if self.config.bingx.testnet else 'PRODUCTION'}")
            
            # Executar estratégia
            await self.strategy.run_strategy(self.config.trading.symbols)
            
        except Exception as e:
            logger.error(f"❌ Erro na execução da estratégia: {e}")
            raise
        finally:
            self.running = False
            logger.info("🛑 Estratégia encerrada")
    
    def print_banner(self):
        """
        Imprime banner de inicialização
        """
        banner = """
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║                    🚀 ESTRATÉGIA DE BREAKOUT AVANÇADA 🚀                          ║
║                                                                                    ║
║                   Breakout + Fluxo de Ordens + Risco Controlado                   ║
║                                                                                    ║
║  Funcionalidades:                                                                  ║
║  • 🔓 Detecção de breakout com confirmação de volume                              ║
║  • 💡 Análise de desequilíbrio do livro de ordens                                ║
║  • 🎯 Execução automatizada com alavancagem isolada 20x                          ║
║  • 🛡️ Gestão de risco com SL/TP dinâmicos                                       ║
║  • 🛠️ Monitoramento de posições com trailing stop                               ║
║  • 🧮 Controle de risco de 1% por trade                                          ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    async def main(self):
        """
        Função principal
        """
        try:
            # Imprimir banner
            self.print_banner()
            
            # Carregar ambiente
            self.load_environment()
            
            # Inicializar estratégia
            if not self.initialize_strategy():
                return 1
            
            # Configurar logging
            self.setup_logging()
            
            # Verificar se é testnet
            if self.config.bingx.testnet:
                logger.info("🧪 EXECUTANDO EM MODO TESTNET")
                print("\n" + "="*50)
                print("🧪 ATENÇÃO: EXECUTANDO EM MODO TESTNET")
                print("="*50 + "\n")
            else:
                logger.warning("💰 EXECUTANDO EM MODO PRODUCTION")
                print("\n" + "="*50)
                print("💰 ATENÇÃO: EXECUTANDO EM MODO PRODUCTION")
                print("💰 TRADES REAIS SERÃO EXECUTADOS!")
                print("="*50 + "\n")
                
                # Confirmação para modo production
                confirm = input("Digite 'CONFIRMO' para continuar: ")
                if confirm != 'CONFIRMO':
                    print("❌ Operação cancelada")
                    return 1
            
            # Executar estratégia
            await self.run_strategy()
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
            return 0
        except Exception as e:
            logger.error(f"❌ Erro crítico: {e}")
            return 1


def main():
    """
    Ponto de entrada do script
    """
    runner = BreakoutStrategyRunner()
    
    try:
        # Executar estratégia
        exit_code = asyncio.run(runner.main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Programa interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
