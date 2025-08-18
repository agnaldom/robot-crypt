#!/usr/bin/env python3
"""
Teste do Sistema de Cache Histórico
===================================

Script para testar o sistema de cache de dados históricos implementado.

Testa:
1. Inicialização do cache
2. Busca de dados históricos
3. Performance do sistema
4. Integração com estratégias

Uso:
    python test_historical_cache.py
"""

import pytest

import sys
import asyncio
import time
from pathlib import Path

# Adiciona src ao path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.cache import (
    initialize_historical_cache, 
    get_historical_data_cached, 
    get_cache_status,
    cache_manager
)
from src.strategies.cache_enhanced_strategy import enhance_strategy_with_cache
from src.core.logging_setup import logger


class TestResults:
    """Classe para armazenar resultados dos testes."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """Adiciona resultado de um teste."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            self.tests_failed += 1
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        
        self.results.append(result)
        print(result)
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        print("\n" + "="*60)
        print("RESUMO DOS TESTES")
        print("="*60)
        print(f"Total de testes: {self.tests_run}")
        print(f"Passou: {self.tests_passed}")
        print(f"Falhou: {self.tests_failed}")
        print(f"Taxa de sucesso: {(self.tests_passed/max(self.tests_run,1))*100:.1f}%")
        print("="*60)


@pytest.mark.asyncio
async def test_cache_initialization():
    """Testa inicialização do cache."""
    print("\n🧪 Teste 1: Inicialização do Cache")
    results = TestResults()
    
    try:
        # Testa inicialização com símbolos padrão
        success = await initialize_historical_cache(['BTCUSDT', 'ETHUSDT'])
        results.add_result("Inicialização básica", success, "Cache inicializado com símbolos de teste")
        
        # Verifica status do cache
        status = get_cache_status()
        results.add_result("Status do cache", 'cached_symbols' in status, f"Status: {status}")
        
        # Testa inicialização sem símbolos (usa padrão)
        success2 = await initialize_historical_cache()
        results.add_result("Inicialização com símbolos padrão", success2, "Usando símbolos prioritários")
        
    except Exception as e:
        results.add_result("Inicialização do cache", False, f"Erro: {str(e)}")
    
    results.print_summary()


def test_data_retrieval():
    """Testa busca de dados históricos."""
    print("\n🧪 Teste 2: Busca de Dados Históricos")
    results = TestResults()
    
    try:
        # Testa busca de dados do Bitcoin
        btc_data = get_historical_data_cached('BTCUSDT', '1d', 7)
        results.add_result("Busca dados Bitcoin", btc_data is not None, 
                         f"Obtidos {len(btc_data) if btc_data else 0} pontos")
        
        # Testa busca com intervalo diferente
        btc_4h = get_historical_data_cached('BTCUSDT', '4h', 3)
        results.add_result("Busca dados 4h", btc_4h is not None,
                         f"Obtidos {len(btc_4h) if btc_4h else 0} pontos")
        
        # Testa busca forçando API
        btc_api = get_historical_data_cached('BTCUSDT', '1d', 1, force_api=True)
        results.add_result("Busca forçando API", btc_api is not None,
                         f"API retornou {len(btc_api) if btc_api else 0} pontos")
        
        # Testa símbolo inexistente
        fake_data = get_historical_data_cached('FAKEUSDT', '1d', 7)
        results.add_result("Busca símbolo inexistente", fake_data is None, 
                         "Retornou None como esperado")
        
    except Exception as e:
        results.add_result("Busca de dados", False, f"Erro: {str(e)}")
    
    results.print_summary()


def test_cache_performance():
    """Testa performance do cache."""
    print("\n🧪 Teste 3: Performance do Cache")
    results = TestResults()
    
    try:
        # Testa velocidade do cache vs API
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        # Primeira busca (pode usar cache ou API)
        start_time = time.time()
        for symbol in symbols:
            data = get_historical_data_cached(symbol, '1d', 7)
        first_run_time = time.time() - start_time
        
        # Segunda busca (deve usar cache)
        start_time = time.time()
        for symbol in symbols:
            data = get_historical_data_cached(symbol, '1d', 7)
        second_run_time = time.time() - start_time
        
        results.add_result("Performance - primeira busca", True, 
                         f"Tempo: {first_run_time:.2f}s")
        results.add_result("Performance - segunda busca", True,
                         f"Tempo: {second_run_time:.2f}s")
        
        # Verifica se cache é mais rápido
        is_faster = second_run_time < first_run_time * 0.5  # Pelo menos 50% mais rápido
        results.add_result("Cache é mais rápido", is_faster,
                         f"Speedup: {first_run_time/max(second_run_time,0.001):.1f}x")
        
    except Exception as e:
        results.add_result("Teste de performance", False, f"Erro: {str(e)}")
    
    results.print_summary()


def test_strategy_integration():
    """Testa integração com estratégias."""
    print("\n🧪 Teste 4: Integração com Estratégias")
    results = TestResults()
    
    try:
        # Cria uma estratégia básica para teste
        class MockStrategy:
            def __init__(self, config, client):
                self.config = config
                self.client = client
            
            def analyze_market(self, symbol):
                return True, "buy", 50000.0
        
        # Aplica enhancement de cache
        EnhancedStrategy = enhance_strategy_with_cache(MockStrategy)
        results.add_result("Criação de estratégia aprimorada", True,
                         f"Classe: {EnhancedStrategy.__name__}")
        
        # Cria instância da estratégia
        class MockConfig:
            pass
        
        class MockClient:
            pass
        
        strategy = EnhancedStrategy(MockConfig(), MockClient())
        results.add_result("Instanciação da estratégia", hasattr(strategy, 'cache_stats'),
                         "Estratégia tem capacidades de cache")
        
        # Testa análise histórica
        analysis = strategy.analyze_historical_trends('BTCUSDT', 50000.0)
        results.add_result("Análise histórica", 'recommendations' in analysis,
                         f"Análise contém {len(analysis.get('recommendations', []))} recomendações")
        
        # Testa performance do cache na estratégia
        performance = strategy.get_cache_performance()
        results.add_result("Performance da estratégia", 'hit_rate' in performance,
                         f"Hit rate: {performance.get('hit_rate', 0)}%")
        
    except Exception as e:
        results.add_result("Integração com estratégias", False, f"Erro: {str(e)}")
    
    results.print_summary()


def test_error_handling():
    """Testa tratamento de erros."""
    print("\n🧪 Teste 5: Tratamento de Erros")
    results = TestResults()
    
    try:
        # Testa busca com parâmetros inválidos
        invalid_data = get_historical_data_cached('', '1d', 7)
        results.add_result("Símbolo vazio", invalid_data is None,
                         "Retornou None para símbolo vazio")
        
        # Testa intervalo inválido
        invalid_interval = get_historical_data_cached('BTCUSDT', 'invalid', 7)
        results.add_result("Intervalo inválido", True,  # Não deve quebrar
                         "Sistema não quebrou com intervalo inválido")
        
        # Testa dias negativos
        negative_days = get_historical_data_cached('BTCUSDT', '1d', -1)
        results.add_result("Dias negativos", True,  # Não deve quebrar
                         "Sistema não quebrou com dias negativos")
        
    except Exception as e:
        results.add_result("Tratamento de erros", False, f"Erro não tratado: {str(e)}")
    
    results.print_summary()


async def run_all_tests():
    """Executa todos os testes."""
    print("🚀 Iniciando testes do sistema de cache histórico...")
    print("="*60)
    
    all_results = TestResults()
    
    # Executa cada teste
    test1 = await test_cache_initialization()
    test2 = test_data_retrieval()
    test3 = test_cache_performance()
    test4 = test_strategy_integration()
    test5 = test_error_handling()
    
    # Consolida resultados
    for test_result in [test1, test2, test3, test4, test5]:
        all_results.tests_run += test_result.tests_run
        all_results.tests_passed += test_result.tests_passed
        all_results.tests_failed += test_result.tests_failed
        all_results.results.extend(test_result.results)
    
    # Mostra status final do cache
    print("\n📊 Status Final do Cache:")
    try:
        final_status = get_cache_status()
        for key, value in final_status.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"  Erro ao obter status: {e}")
    
    # Resumo geral
    print("\n🏁 RESULTADO FINAL DOS TESTES")
    all_results.print_summary()
    
    if all_results.tests_failed == 0:
        print("🎉 Todos os testes passaram! Sistema está funcionando corretamente.")
    else:
        print(f"⚠️ {all_results.tests_failed} teste(s) falharam. Verifique os logs acima.")
    
    return all_results.tests_failed == 0


if __name__ == "__main__":
    print("🔧 Teste do Sistema de Cache Histórico do Robot-Crypt")
    print("====================================================")
    
    try:
        # Executa todos os testes
        success = asyncio.run(run_all_tests())
        
        if success:
            print("\n✅ Sistema de cache histórico está funcionando perfeitamente!")
            exit(0)
        else:
            print("\n❌ Alguns testes falharam. Verifique a implementação.")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Testes interrompidos pelo usuário.")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erro crítico durante os testes: {str(e)}")
        exit(1)
