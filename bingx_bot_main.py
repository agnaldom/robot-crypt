#!/usr/bin/env python3
"""
BingX Trading Bot Main Script
Bot de trading para BingX com estratégia Harmonic Butterfly Pattern
"""

import sys
import os
import time
from typing import Optional

# Adiciona o diretório src ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api.bingx.futures_client import BingXFuturesClient
from src.strategies.bingx_butterfly_strategy import BingXButterflyStrategy
from config.bingx_config import BingXConfig
from src.core.logging_setup import logger


def setup_environment():
    """
    Configurar ambiente e validar configurações.
    """
    logger.info("🚀 Iniciando BingX Trading Bot...")
    
    # Validar configuração
    config_errors = BingXConfig.validate_config()
    if config_errors:
        logger.error("❌ Erros de configuração encontrados:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("💡 Verifique suas variáveis de ambiente no arquivo .env")
        return False
    
    logger.info("✅ Configuração validada com sucesso")
    return True


def create_bingx_client() -> Optional[BingXFuturesClient]:
    """
    Criar cliente BingX com configurações.
    
    Returns:
        Optional[BingXFuturesClient]: Cliente BingX ou None se falhar
    """
    try:
        client = BingXFuturesClient(
            api_key=BingXConfig.API_KEY,
            api_secret=BingXConfig.API_SECRET,
            testnet=BingXConfig.USE_TESTNET
        )
        
        # Testar conexão
        server_time = client.get_server_time()
        logger.info(f"✅ Conectado ao BingX - Server Time: {server_time}")
        
        # Mostrar informações da conta
        account_info = client.get_account()
        if account_info and account_info.get('data'):
            balance_data = account_info['data']['balance']
            if balance_data:
                balance = float(balance_data[0]['balance'])
                logger.info(f"💰 Saldo da conta: {balance} USDT")
        
        return client
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com BingX: {str(e)}")
        return None


def create_strategy(client: BingXFuturesClient) -> Optional[BingXButterflyStrategy]:
    """
    Criar estratégia Butterfly com configurações.
    
    Args:
        client (BingXFuturesClient): Cliente BingX
        
    Returns:
        Optional[BingXButterflyStrategy]: Estratégia ou None se falhar
    """
    try:
        strategy_config = BingXConfig.get_strategy_config()
        
        strategy = BingXButterflyStrategy(
            client=client,
            **strategy_config
        )
        
        logger.info("✅ Estratégia Butterfly criada com sucesso")
        logger.info(f"📊 Configurações da estratégia:")
        logger.info(f"  - Símbolos: {strategy_config['symbols']}")
        logger.info(f"  - Timeframe: {strategy_config['timeframe']}")
        logger.info(f"  - Leverage: {strategy_config['leverage']}x")
        logger.info(f"  - Risco por trade: {strategy_config['risk_per_trade']*100}%")
        logger.info(f"  - Max posições: {strategy_config['max_positions']}")
        logger.info(f"  - Stop Loss: {strategy_config['stop_loss_ratio']*100}%")
        logger.info(f"  - Take Profit: {strategy_config['take_profit_ratio']*100}%")
        
        return strategy
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar estratégia: {str(e)}")
        return None


def show_strategy_status(strategy: BingXButterflyStrategy):
    """
    Mostrar status da estratégia.
    
    Args:
        strategy (BingXButterflyStrategy): Estratégia
    """
    status = strategy.get_strategy_status()
    logger.info("📈 Status da Estratégia:")
    logger.info(f"  - Posições ativas: {status['active_positions']}/{status['max_positions']}")
    logger.info(f"  - Símbolos monitorados: {len(status['symbols'])}")
    logger.info(f"  - Última análise: {len(status['last_analysis'])} símbolos")
    
    if status['positions']:
        logger.info("🎯 Posições Ativas:")
        for symbol, position in status['positions'].items():
            logger.info(f"  - {symbol}: {position['side']} - Size: {position['position_size']}")


def main():
    """
    Função principal do bot.
    """
    try:
        # Configurar ambiente
        if not setup_environment():
            return
        
        # Criar cliente BingX
        client = create_bingx_client()
        if not client:
            logger.error("❌ Falha ao criar cliente BingX")
            return
        
        # Criar estratégia
        strategy = create_strategy(client)
        if not strategy:
            logger.error("❌ Falha ao criar estratégia")
            return
        
        # Mostrar status inicial
        show_strategy_status(strategy)
        
        # Executar teste de análise inicial
        logger.info("🔍 Executando análise inicial...")
        for symbol in BingXConfig.SYMBOLS:
            analysis = strategy.analyze_market(symbol)
            if analysis:
                patterns_found = len(analysis.get('patterns', []))
                logger.info(f"  - {symbol}: {patterns_found} padrões encontrados")
        
        # Perguntar se deve executar em modo real
        if BingXConfig.USE_TESTNET:
            logger.info("⚠️  Executando em modo TESTNET")
            response = input("Deseja executar a estratégia? (s/n): ").lower().strip()
        else:
            logger.warning("⚠️  ATENÇÃO: Executando em modo REAL com dinheiro real!")
            response = input("TEM CERTEZA que deseja executar com dinheiro real? (sim/n): ").lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            logger.info("🚀 Iniciando execução da estratégia...")
            
            # Executar estratégia
            try:
                strategy.run_strategy()
            except KeyboardInterrupt:
                logger.info("⏹️  Estratégia interrompida pelo usuário")
            except Exception as e:
                logger.error(f"❌ Erro na execução da estratégia: {str(e)}")
        else:
            logger.info("⏹️  Execução cancelada pelo usuário")
            
    except Exception as e:
        logger.error(f"❌ Erro crítico: {str(e)}")
    finally:
        logger.info("👋 Bot finalizado")


if __name__ == "__main__":
    main()
