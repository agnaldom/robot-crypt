#!/usr/bin/env python3
"""
Script de teste para verificar conexão e configuração BingX
"""

import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adiciona o diretório src ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api.bingx.futures_client import BingXFuturesClient
from src.api.bingx.harmonic_patterns import HarmonicPatternDetector
from config.bingx_config import BingXConfig
from src.core.logging_setup import logger


def test_config():
    """Teste básico de configuração"""
    logger.info("🔧 Testando configuração...")
    
    errors = BingXConfig.validate_config()
    if errors:
        logger.error("❌ Erros de configuração:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("✅ Configuração OK")
    return True


def test_connection():
    """Teste de conexão com BingX"""
    logger.info("🌐 Testando conexão...")
    
    try:
        client = BingXFuturesClient(
            api_key=BingXConfig.API_KEY,
            api_secret=BingXConfig.API_SECRET,
            testnet=BingXConfig.USE_TESTNET
        )
        
        # Testar tempo do servidor
        server_time = client.get_server_time()
        logger.info(f"⏰ Server Time: {server_time}")
        
        # Testar informações da exchange
        exchange_info = client.get_exchange_info()
        logger.info(f"📊 Exchange Info: {len(exchange_info.get('data', {}).get('symbols', []))} símbolos disponíveis")
        
        logger.info("✅ Conexão OK")
        return client
        
    except Exception as e:
        logger.error(f"❌ Erro de conexão: {str(e)}")
        return None


def test_account_info(client: BingXFuturesClient):
    """Teste de informações da conta"""
    logger.info("👤 Testando informações da conta...")
    
    try:
        account = client.get_account()
        if account and account.get('data'):
            balance_data = account['data']['balance']
            if balance_data:
                balance = float(balance_data[0]['balance'])
                logger.info(f"💰 Saldo: {balance} USDT")
            else:
                logger.warning("⚠️ Nenhum saldo encontrado")
        else:
            logger.warning("⚠️ Dados da conta não encontrados")
            
        logger.info("✅ Informações da conta OK")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter informações da conta: {str(e)}")
        return False


def test_market_data(client: BingXFuturesClient):
    """Teste de dados de mercado"""
    logger.info("📈 Testando dados de mercado...")
    
    try:
        symbol = 'BTC-USDT'
        
        # Testar preço
        ticker = client.get_ticker_price(symbol)
        if ticker and ticker.get('data'):
            price = float(ticker['data']['price'])
            logger.info(f"💲 Preço {symbol}: {price}")
        
        # Testar klines
        klines = client.get_klines(symbol, '1h', limit=10)
        if klines:
            logger.info(f"📊 Klines {symbol}: {len(klines)} candles obtidos")
        
        # Testar order book
        depth = client.get_depth(symbol, limit=5)
        if depth and depth.get('data'):
            bids = depth['data']['bids']
            asks = depth['data']['asks']
            logger.info(f"📚 Order Book {symbol}: {len(bids)} bids, {len(asks)} asks")
        
        logger.info("✅ Dados de mercado OK")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter dados de mercado: {str(e)}")
        return False


def test_pattern_detection():
    """Teste de detecção de padrões"""
    logger.info("🔍 Testando detecção de padrões...")
    
    try:
        detector = HarmonicPatternDetector()
        
        # Dados de exemplo (mock)
        mock_klines = [
            [1, 50000, 51000, 49000, 50500, 100],  # timestamp, open, high, low, close, volume
            [2, 50500, 52000, 50000, 51500, 120],
            [3, 51500, 53000, 51000, 52000, 110],
            [4, 52000, 52500, 50500, 51000, 130],
            [5, 51000, 51500, 49500, 50000, 140],
        ]
        
        patterns = detector.detect_butterfly_pattern(mock_klines)
        logger.info(f"🦋 Padrões detectados: {len(patterns)}")
        
        # Testar cálculo de ratios
        test_points = [50000, 51000, 50500, 51500, 50000]
        ratios = detector.calculate_fibonacci_ratios(test_points)
        logger.info(f"📐 Ratios calculados: {ratios}")
        
        logger.info("✅ Detecção de padrões OK")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na detecção de padrões: {str(e)}")
        return False


def main():
    """Função principal de teste"""
    logger.info("🚀 Iniciando testes do BingX Bot...")
    
    tests_passed = 0
    total_tests = 5
    
    # Teste 1: Configuração
    if test_config():
        tests_passed += 1
    
    # Teste 2: Conexão
    client = test_connection()
    if client:
        tests_passed += 1
        
        # Teste 3: Informações da conta
        if test_account_info(client):
            tests_passed += 1
        
        # Teste 4: Dados de mercado
        if test_market_data(client):
            tests_passed += 1
    
    # Teste 5: Detecção de padrões
    if test_pattern_detection():
        tests_passed += 1
    
    # Resultado final
    logger.info(f"📊 Resultado dos testes: {tests_passed}/{total_tests} passaram")
    
    if tests_passed == total_tests:
        logger.info("🎉 Todos os testes passaram! O bot está pronto para uso.")
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} teste(s) falharam. Verifique a configuração.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
