#!/usr/bin/env python3
"""
Teste de Execução para Robot-Crypt
Este script verifica a funcionalidade básica do sistema e simula um ciclo de análise
para diagnosticar problemas de desempenho e execução.
"""
import os
import sys
import time
import logging
import json
import requests
from datetime import datetime, timedelta
import traceback
import gc

# Importações do Robot-Crypt
from config import Config
from binance_api import BinanceAPI
from utils import setup_logger
from strategy import ScalpingStrategy, SwingTradingStrategy

# Configuração do logger específico para testes
logger = setup_logger('robot-crypt-test')

def test_imports():
    """Testa se todas as importações necessárias funcionam"""
    logger.info("Testando importações dos módulos necessários...")
    
    try:
        import pandas as pd
        import numpy as np
        logger.info("✅ Módulos de análise de dados (pandas, numpy) importados com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulos de análise de dados: {str(e)}")
        logger.error("Execute 'pip install -r requirements.txt' para instalar dependências")
        return False
    
    try:
        from health_monitor import check_system_health, log_process_tree
        logger.info("✅ Módulo de monitoramento de saúde importado com sucesso")
    except ImportError as e:
        logger.warning(f"⚠️ Módulo de monitoramento de saúde não encontrado: {str(e)}")
        logger.warning("O monitoramento avançado não estará disponível")
    
    try:
        from db_manager import DBManager
        logger.info("✅ Módulo de banco de dados importado com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulo de banco de dados: {str(e)}")
        return False
    
    return True

def test_config():
    """Testa se a configuração está correta"""
    logger.info("Testando configuração...")
    
    try:
        config = Config()
        logger.info(f"✅ Configuração carregada com sucesso")
        
        # Verifica os parâmetros mais importantes
        logger.info(f"Modo TestNet: {'✅ Ativado' if config.use_testnet else '❌ Desativado'}")
        logger.info(f"Modo Simulação: {'✅ Ativado' if config.simulation_mode else '❌ Desativado'}")
        logger.info(f"Intervalo de verificação: {config.check_interval} segundos")
        logger.info(f"API Key disponível: {'✅ Sim' if config.api_key else '❌ Não'}")
        logger.info(f"API Secret disponível: {'✅ Sim' if config.api_secret else '❌ Não'}")
        
        if not config.simulation_mode and not (config.api_key and config.api_secret):
            logger.warning("⚠️ Modo de simulação desativado mas credenciais API ausentes")
            
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {str(e)}")
        logger.exception("Detalhes do erro:")
        return None

def test_api_connection(config):
    """Testa a conexão com a API da Binance"""
    logger.info("Testando conexão com a API da Binance...")
    
    if config.simulation_mode:
        logger.info("✅ Modo de simulação ativado, pulando teste de API")
        from binance_simulator import BinanceSimulator
        return BinanceSimulator()
        
    try:
        start_time = datetime.now()
        binance = BinanceAPI(
            api_key=config.api_key, 
            api_secret=config.api_secret,
            testnet=config.use_testnet
        )
        
        logger.info("Testando conexão...")
        connection_status = binance.test_connection()
        
        if connection_status:
            connection_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Conexão estabelecida com sucesso em {connection_time:.2f} segundos")
            return binance
        else:
            logger.error("❌ Falha no teste de conexão")
            return None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com a API: {str(e)}")
        logger.exception("Detalhes do erro:")
        return None

def test_market_data_fetch(binance, symbol="BTC/USDT"):
    """Testa a obtenção de dados de mercado para um símbolo"""
    logger.info(f"Testando obtenção de dados de mercado para {symbol}...")
    
    try:
        start_time = datetime.now()
        ticker = binance.fetch_ticker(symbol)
        
        if ticker and 'last' in ticker:
            fetch_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Dados obtidos com sucesso em {fetch_time:.3f} segundos")
            logger.info(f"Preço atual de {symbol}: {ticker['last']}")
            return ticker
        else:
            logger.error(f"❌ Dados de mercado incompletos ou inválidos")
            return None
    except Exception as e:
        logger.error(f"❌ Erro ao obter dados de mercado: {str(e)}")
        logger.exception("Detalhes do erro:")
        return None

def test_strategy_analysis(config, binance, symbol="BTC/USDT"):
    """Testa a análise de mercado pela estratégia"""
    logger.info(f"Testando análise de estratégia para {symbol}...")
    
    try:
        # Teste com ambas as estratégias para diagnóstico
        strategies = [
            ("Scalping", ScalpingStrategy(config, binance)),
            ("Swing Trading", SwingTradingStrategy(config, binance))
        ]
        
        for strategy_name, strategy in strategies:
            start_time = datetime.now()
            logger.info(f"Executando análise com estratégia {strategy_name}...")
            
            should_trade, action, price = strategy.analyze_market(symbol)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Análise concluída em {analysis_time:.3f} segundos")
            logger.info(f"Resultado: {'Sinal de ' + action.upper() if should_trade else 'Sem ação recomendada'}")
            
            if analysis_time > 5.0:
                logger.warning(f"⚠️ Análise levou mais de 5 segundos ({analysis_time:.2f}s), possível problema de desempenho")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao executar análise de mercado: {str(e)}")
        logger.exception("Detalhes do erro:")
        return False

def test_system_health():
    """Testa o monitoramento de saúde do sistema se disponível"""
    logger.info("Testando monitoramento de saúde do sistema...")
    
    try:
        from health_monitor import check_system_health
        
        health_metrics = check_system_health()
        if health_metrics:
            logger.info(f"✅ Métricas de saúde: {json.dumps(health_metrics, indent=2)}")
            
            # Verifica problemas de recursos
            if health_metrics.get('memory_percent', 0) > 80:
                logger.warning(f"⚠️ Uso de memória elevado: {health_metrics['memory_percent']}%")
            if health_metrics.get('cpu_percent', 0) > 80:
                logger.warning(f"⚠️ Uso de CPU elevado: {health_metrics['cpu_percent']}%")
                
            return health_metrics
        else:
            logger.warning("⚠️ Não foi possível obter métricas de saúde")
            return None
    except ImportError:
        logger.warning("⚠️ Módulo de monitoramento de saúde não disponível")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao verificar saúde do sistema: {str(e)}")
        logger.exception("Detalhes do erro:")
        return None

def simulate_analysis_cycle(config, binance, pairs=None):
    """Simula um ciclo completo de análise de mercado"""
    if pairs is None:
        pairs = ["BTC/USDT", "ETH/USDT", "DOGE/USDT"]
    
    logger.info("=" * 50)
    logger.info("Iniciando simulação de ciclo completo de análise")
    logger.info(f"Pares a analisar: {', '.join(pairs)}")
    logger.info("=" * 50)
    
    start_time = datetime.now()
    strategy = SwingTradingStrategy(config, binance)
    
    total_analysis_time = 0
    pair_times = []
    
    for pair in pairs:
        pair_start = datetime.now()
        logger.info(f"Analisando par {pair}...")
        
        try:
            should_trade, action, price = strategy.analyze_market(pair)
            
            pair_time = (datetime.now() - pair_start).total_seconds()
            pair_times.append(pair_time)
            total_analysis_time += pair_time
            
            logger.info(f"✅ Análise de {pair} concluída em {pair_time:.3f}s - Resultado: {action if should_trade else 'sem ação'}")
            
            # Força coleção de lixo para simular comportamento real
            gc.collect()
            
            # Pequena pausa entre análises
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar {pair}: {str(e)}")
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info("=" * 50)
    logger.info(f"Ciclo de análise completo em {total_time:.3f} segundos")
    logger.info(f"Tempo médio por par: {sum(pair_times)/len(pair_times):.3f} segundos")
    logger.info(f"Tempo de análise pura: {total_analysis_time:.3f} segundos")
    logger.info(f"Sobrecarga adicional: {total_time - total_analysis_time:.3f} segundos")
    
    # Extrapolação para intervalo de verificação padrão
    if config.check_interval > 0:
        idle_percentage = 100 * (1 - (total_time / config.check_interval))
        logger.info(f"Com intervalo de {config.check_interval}s, sistema fica {idle_percentage:.1f}% do tempo ocioso")
    
    logger.info("=" * 50)
    
    return {
        "total_time": total_time,
        "analysis_time": total_analysis_time,
        "overhead": total_time - total_analysis_time,
        "average_pair_time": sum(pair_times)/len(pair_times) if pair_times else 0,
        "pair_times": {pair: time for pair, time in zip(pairs, pair_times)}
    }

def run_full_test():
    """Executa todos os testes em sequência"""
    logger.info("=" * 80)
    logger.info(f"INICIANDO TESTE COMPLETO DE EXECUÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 80)
    
    # Teste de importações
    if not test_imports():
        logger.error("❌ Teste de importações falhou. Corrigir antes de continuar.")
        return False
    
    # Teste de configuração
    config = test_config()
    if not config:
        logger.error("❌ Teste de configuração falhou. Corrigir antes de continuar.")
        return False
    
    # Teste de conexão com a API
    binance = test_api_connection(config)
    if not binance:
        logger.error("❌ Teste de conexão com a API falhou. Corrigir antes de continuar.")
        return False
    
    # Teste de obtenção de dados de mercado
    market_data = test_market_data_fetch(binance)
    if not market_data:
        logger.error("❌ Teste de obtenção de dados de mercado falhou. Corrigir antes de continuar.")
        return False
    
    # Teste de análise de estratégia
    if not test_strategy_analysis(config, binance):
        logger.error("❌ Teste de análise de estratégia falhou.")
        return False
    
    # Teste de saúde do sistema
    test_system_health()
    
    # Simulação de ciclo completo
    cycle_stats = simulate_analysis_cycle(config, binance)
    
    logger.info("=" * 80)
    logger.info("TESTE COMPLETO FINALIZADO COM SUCESSO")
    logger.info("=" * 80)
    
    # Recomendações baseadas nos resultados
    if cycle_stats["average_pair_time"] > 2.0:
        logger.warning("⚠️ RECOMENDAÇÃO: O tempo médio de análise por par está elevado.")
        logger.warning("   Considere reduzir o número de pares ou otimizar a estratégia.")
    
    if cycle_stats["overhead"] > cycle_stats["analysis_time"] * 0.5:
        logger.warning("⚠️ RECOMENDAÇÃO: Sobrecarga do sistema está alta em relação ao tempo de análise.")
        logger.warning("   Verifique recursos do sistema e processos concorrentes.")
    
    return True

if __name__ == "__main__":
    try:
        if run_full_test():
            logger.info("✅ Teste de execução concluído com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Teste de execução falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Erro não tratado durante o teste: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(2)
