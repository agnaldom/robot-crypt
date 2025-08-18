#!/usr/bin/env python3
"""
Teste do Sistema de Cache Histórico
====================================

Este script demonstra o funcionamento do novo sistema de cache histórico
que prioriza SEMPRE o banco de dados antes de consultar a API da Binance.

Para executar:
    python test_cache_system.py

Autor: Robot-Crypt Team
Data: 2024
"""

import pytest

import asyncio
import time
import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Importa funcionalidades do cache
from src.cache import (
    # Funções principais
    initialize_historical_cache,
    get_cache_status,
    
    # Interface simplificada
    get_market_data,
    get_latest_price,
    get_price_range,
    ensure_cache_ready,
    is_cache_healthy,
    maintain_cache_health,
    
    # Classes
    cache_manager,
    data_provider
)

print("🚀 TESTE DO SISTEMA DE CACHE HISTÓRICO")
print("="*60)


@pytest.mark.asyncio
async def test_cache_initialization():
    """Testa a inicialização do cache."""
    print("\n📊 TESTE 1: Inicialização do Cache")
    print("-" * 40)
    
    # Símbolos para teste
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    print(f"🎯 Inicializando cache para: {', '.join(test_symbols)}")
    
    start_time = time.time()
    success = await initialize_historical_cache(test_symbols)
    end_time = time.time()
    
    if success:
        print(f"✅ Cache inicializado com sucesso em {end_time - start_time:.2f} segundos")
        
        # Mostra status
        status = get_cache_status()
        print(f"📈 Símbolos em cache: {status['cached_symbols']}")
        print(f"🎯 Cobertura: {status['coverage_percentage']:.1f}%")
        print(f"📊 Dias de dados: {status['data_coverage_days']}")
        
        assert True
    else:
        print("❌ Falha ao inicializar cache")
        assert False


def test_cache_priority():
    """Testa se o cache tem prioridade sobre a API."""
    print("\n🔍 TESTE 2: Prioridade do Cache vs API")
    print("-" * 40)
    
    symbol = 'BTCUSDT'
    
    # Primeira busca (pode vir da API se não estiver em cache)
    print(f"🌐 Primeira busca para {symbol}...")
    start_time = time.time()
    data1 = get_market_data(symbol, '1d', 7)
    first_duration = time.time() - start_time
    
    if data1:
        print(f"✅ Primeira busca: {len(data1)} registros em {first_duration:.3f}s")
        
        # Segunda busca (DEVE vir do cache)
        print(f"💾 Segunda busca para {symbol} (deve usar cache)...")
        start_time = time.time()
        data2 = get_market_data(symbol, '1d', 7)
        second_duration = time.time() - start_time
        
        if data2:
            print(f"✅ Segunda busca: {len(data2)} registros em {second_duration:.3f}s")
            
            # Compara velocidades
            speedup = first_duration / second_duration if second_duration > 0 else float('inf')
            print(f"🚀 Cache {speedup:.1f}x mais rápido que API")
            
            # Verifica se os dados são consistentes
            if len(data1) == len(data2):
                print("✅ Dados consistentes entre cache e API")
                assert True
            else:
                print("⚠️ Dados inconsistentes")
                assert False
        else:
            print("❌ Segunda busca falhou")
            assert False
    else:
        print("❌ Primeira busca falhou")
        assert False


def test_convenience_functions():
    """Testa as funções convenientes da interface simplificada."""
    print("\n🛠️ TESTE 3: Funções Convenientes")
    print("-" * 40)
    
    symbol = 'BTCUSDT'
    
    # Testa preço mais recente
    print(f"💰 Buscando preço mais recente de {symbol}...")
    price = get_latest_price(symbol)
    if price:
        print(f"✅ Preço atual: ${price:.2f}")
    else:
        print("❌ Falha ao obter preço")
        assert False
    
    # Testa faixa de preços
    print(f"📊 Buscando faixa de preços de {symbol} (30 dias)...")
    price_range = get_price_range(symbol, 30)
    if price_range:
        print(f"✅ Faixa: ${price_range['min']:.2f} - ${price_range['max']:.2f}")
        print(f"📈 Média: ${price_range['avg']:.2f} | Atual: ${price_range['current']:.2f}")
        print(f"📊 {price_range['count']} pontos de dados")
    else:
        print("❌ Falha ao obter faixa de preços")
        assert False
    
    # Testa dados históricos com diferentes períodos
    print(f"📈 Testando diferentes períodos para {symbol}...")
    
    periods = ['1d', '1w', '1m', '3m']
    for period in periods:
        data = get_market_data(symbol, '1d', period)
        if data:
            print(f"✅ {period}: {len(data)} registros")
        else:
            print(f"❌ {period}: falha")


def test_multiple_symbols():
    """Testa busca de dados para múltiplos símbolos."""
    print("\n📊 TESTE 4: Múltiplos Símbolos")
    print("-" * 40)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
    
    print(f"🔍 Buscando dados para {len(symbols)} símbolos...")
    
    results = data_provider.get_multiple_symbols_data(symbols, '1d', 7)
    
    successful = 0
    failed = 0
    
    for symbol, data in results.items():
        if data:
            successful += 1
            print(f"✅ {symbol}: {len(data)} registros")
        else:
            failed += 1
            print(f"❌ {symbol}: falha")
    
    print(f"📈 Resultado: {successful} sucessos, {failed} falhas")
    assert successful > failed


def test_cache_health():
    """Testa verificação de saúde do cache."""
    print("\n🏥 TESTE 5: Saúde do Cache")
    print("-" * 40)
    
    print("🔍 Verificando saúde do cache...")
    healthy = is_cache_healthy()
    
    if healthy:
        print("✅ Cache está saudável")
    else:
        print("⚠️ Cache apresenta problemas")
    
    # Mostra estatísticas detalhadas
    status = get_cache_status()
    print(f"📊 Estatísticas detalhadas:")
    print(f"   Símbolos: {status['cached_symbols']}/{status['total_symbols']}")
    print(f"   Taxa de acerto: {status['hit_rate']:.1f}%")
    print(f"   Eficiência: {status['cache_efficiency']}")
    print(f"   Status: {status['status']}")
    print(f"   Última atualização: {status.get('last_update', 'N/A')}")


@pytest.mark.asyncio
async def test_cache_maintenance():
    """Testa manutenção do cache."""
    print("\n🔧 TESTE 6: Manutenção do Cache")
    print("-" * 40)
    
    print("🔧 Executando manutenção do cache...")
    
    try:
        await maintain_cache_health()
        print("✅ Manutenção executada com sucesso")
        
        # Verifica saúde após manutenção
        healthy = is_cache_healthy()
        print(f"🏥 Saúde pós-manutenção: {'OK' if healthy else 'PROBLEMAS'}")
        
        assert True
        
    except Exception as e:
        print(f"❌ Erro na manutenção: {str(e)}")
        assert False


def test_performance_comparison():
    """Compara performance do cache vs chamadas diretas."""
    print("\n⚡ TESTE 7: Comparação de Performance")
    print("-" * 40)
    
    symbol = 'BTCUSDT'
    num_requests = 5
    
    print(f"🔬 Fazendo {num_requests} requisições para {symbol}...")
    
    # Múltiplas requisições para medir cache hits
    total_time = 0
    successful_requests = 0
    
    for i in range(num_requests):
        start_time = time.time()
        data = get_market_data(symbol, '1d', 7)
        duration = time.time() - start_time
        
        if data:
            successful_requests += 1
            total_time += duration
            print(f"  Requisição {i+1}: {len(data)} registros em {duration:.3f}s")
        else:
            print(f"  Requisição {i+1}: FALHA")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"⚡ Tempo médio por requisição: {avg_time:.3f}s")
        
        # Mostra estatísticas do provider
        stats = data_provider.get_stats()
        print(f"📊 Estatísticas do provider:")
        print(f"   Total de requisições: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Taxa de acerto: {stats['hit_rate']:.1f}%")
        
        assert True
    else:
        print("❌ Todas as requisições falharam")
        assert False


async def run_comprehensive_test():
    """Executa todos os testes de forma sequencial."""
    print("🧪 INICIANDO TESTE ABRANGENTE DO SISTEMA DE CACHE")
    print("="*60)
    
    tests = [
        ("Inicialização do Cache", test_cache_initialization),
        ("Prioridade Cache vs API", test_cache_priority),
        ("Funções Convenientes", test_convenience_functions),
        ("Múltiplos Símbolos", test_multiple_symbols),
        ("Saúde do Cache", test_cache_health),
        ("Manutenção do Cache", test_cache_maintenance),
        ("Comparação de Performance", test_performance_comparison),
    ]
    
    results = []
    start_total = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🚀 Executando: {test_name}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"🎯 {test_name}: {status}")
            
        except Exception as e:
            print(f"❌ ERRO em {test_name}: {str(e)}")
            results.append((test_name, False))
    
    end_total = time.time()
    
    # Relatório final
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"⏱️ Tempo total: {end_total - start_total:.2f} segundos")
    print(f"📊 Testes: {passed}/{total} passaram ({(passed/total)*100:.1f}%)")
    print()
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status} {test_name}")
    
    # Status final do cache
    print(f"\n📈 STATUS FINAL DO CACHE:")
    try:
        status = get_cache_status()
        print(f"   Símbolos em cache: {status['cached_symbols']}")
        print(f"   Taxa de acerto: {status['hit_rate']:.1f}%")
        print(f"   Eficiência: {status['cache_efficiency']}")
        print(f"   Cobertura: {status['coverage_percentage']:.1f}%")
    except Exception as e:
        print(f"   Erro ao obter status: {str(e)}")
    
    if passed == total:
        print(f"\n🎉 TODOS OS TESTES PASSARAM! Sistema está funcionando perfeitamente.")
        return True
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam. Verifique os logs acima.")
        return False


if __name__ == "__main__":
    # Executa o teste abrangente
    try:
        success = asyncio.run(run_comprehensive_test())
        
        if success:
            print("\n✅ Sistema de cache está pronto para uso!")
            print("💡 Para usar nas estratégias, importe:")
            print("   from src.cache import get_market_data, get_latest_price")
            sys.exit(0)
        else:
            print("\n❌ Sistema apresentou falhas nos testes")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
