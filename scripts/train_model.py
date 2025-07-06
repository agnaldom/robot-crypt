#!/usr/bin/env python3
"""
Script para treinamento do modelo de trading
Uso: python scripts/train_model.py [--symbols BTC/USDT,ETH/USDT] [--continuous]
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import List

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.training_system import TradingTrainer
from src.core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradingModelTrainer:
    """Interface para treinamento do modelo de trading."""
    
    def __init__(self):
        self.trainer = TradingTrainer()
    
    async def train_single_session(self, symbols: List[str]) -> dict:
        """Executa uma sessão única de treinamento."""
        try:
            logger.info(f"Iniciando treinamento para símbolos: {symbols}")
            
            # Treinar modelo
            training_result = await self.trainer.train_model_with_latest_data(symbols)
            
            if "error" in training_result:
                logger.error(f"Erro no treinamento: {training_result['error']}")
                return training_result
            
            # Exibir resultados
            report = training_result.get('training_report', {})
            accuracy = report.get('accuracy', 'N/A')
            features_count = training_result.get('features_created', 0)
            
            logger.info(f"Treinamento concluído com sucesso!")
            logger.info(f"Acurácia: {accuracy}")
            logger.info(f"Features criadas: {features_count}")
            
            # Gerar sinais
            logger.info("Gerando sinais de trading...")
            signals = await self.trainer.generate_trading_signals(symbols)
            
            # Exibir sinais
            logger.info(f"Sinais gerados ({len(signals)}):")
            for signal in signals:
                logger.info(f"  {signal.symbol}: {signal.signal} "
                          f"(confiança: {signal.confidence:.2f}) "
                          f"- Preço: ${signal.price:.2f}")
            
            return {
                "success": True,
                "training_result": training_result,
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Erro durante o treinamento: {e}")
            return {"success": False, "error": str(e)}
    
    async def train_continuous(self, symbols: List[str], interval_hours: int = 24):
        """Executa treinamento contínuo."""
        logger.info(f"Iniciando treinamento contínuo a cada {interval_hours} horas")
        logger.info("Pressione Ctrl+C para interromper")
        
        try:
            await self.trainer.run_continuous_training(symbols, interval_hours)
        except KeyboardInterrupt:
            logger.info("Treinamento contínuo interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no treinamento contínuo: {e}")
    
    async def generate_signals_only(self, symbols: List[str]) -> List:
        """Gera apenas sinais de trading sem treinar."""
        logger.info(f"Gerando sinais para: {symbols}")
        
        try:
            signals = await self.trainer.generate_trading_signals(symbols)
            
            logger.info(f"Sinais gerados ({len(signals)}):")
            for signal in signals:
                logger.info(f"  {signal.symbol}: {signal.signal} "
                          f"(confiança: {signal.confidence:.2f}) "
                          f"- ${signal.price:.2f}")
                logger.info(f"    Razão: {signal.reasoning}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao gerar sinais: {e}")
            return []
    
    def print_model_info(self):
        """Exibe informações sobre o modelo."""
        model_path = self.trainer.model.model_path
        
        if os.path.exists(model_path):
            mod_time = os.path.getmtime(model_path)
            from datetime import datetime
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Modelo encontrado: {model_path}")
            logger.info(f"Última modificação: {mod_time_str}")
            
            # Tentar carregar e exibir informações do modelo
            try:
                self.trainer.model.load_model()
                if self.trainer.model.is_trained:
                    logger.info("Modelo carregado com sucesso")
                    logger.info(f"Features: {len(self.trainer.model.feature_columns)}")
                else:
                    logger.warning("Modelo não pôde ser carregado")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}")
        else:
            logger.info("Nenhum modelo treinado encontrado")


def parse_arguments():
    """Analisa argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Treinamento do modelo de trading")
    
    parser.add_argument(
        '--symbols', 
        type=str, 
        default='BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,SOL/USDT',
        help='Símbolos para análise (separados por vírgula)'
    )
    
    parser.add_argument(
        '--continuous', 
        action='store_true',
        help='Executar treinamento contínuo'
    )
    
    parser.add_argument(
        '--interval', 
        type=int, 
        default=24,
        help='Intervalo em horas para treinamento contínuo (padrão: 24)'
    )
    
    parser.add_argument(
        '--signals-only', 
        action='store_true',
        help='Gerar apenas sinais de trading (sem treinar)'
    )
    
    parser.add_argument(
        '--info', 
        action='store_true',
        help='Exibir informações sobre o modelo atual'
    )
    
    return parser.parse_args()


async def main():
    """Função principal."""
    args = parse_arguments()
    
    # Criar diretórios necessários
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Processar símbolos
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Inicializar trainer
    trainer = TradingModelTrainer()
    
    print("=== Sistema de Treinamento do Robô de Trading ===\n")
    
    # Verificar configuração
    if not any([
        settings.BINANCE_API_KEY,
        settings.COINMARKETCAP_API_KEY,
        settings.CRYPTOPANIC_API_KEY,
        settings.NEWS_API_KEY
    ]):
        print("⚠️  Atenção: Nenhuma chave de API configurada!")
        print("Configure pelo menos uma API no arquivo .env para obter dados reais.\n")
    
    # Exibir informações do modelo
    if args.info:
        trainer.print_model_info()
        return
    
    # Gerar apenas sinais
    if args.signals_only:
        await trainer.generate_signals_only(symbols)
        return
    
    # Treinamento contínuo
    if args.continuous:
        await trainer.train_continuous(symbols, args.interval)
        return
    
    # Treinamento único
    result = await trainer.train_single_session(symbols)
    
    if result.get("success"):
        print("\n✅ Treinamento concluído com sucesso!")
        
        # Salvar relatório
        report_file = "reports/training_report.json"
        os.makedirs('reports', exist_ok=True)
        
        import json
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"📊 Relatório salvo em: {report_file}")
    else:
        print(f"\n❌ Falha no treinamento: {result.get('error', 'Erro desconhecido')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
