#!/usr/bin/env python3
"""
Script para executar todos os testes relacionados aos erros identificados nos logs
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Executa todos os testes relacionados aos erros"""
    
    print("=== Executando testes para correção de erros identificados nos logs ===")
    print()
    
    # Lista de arquivos de teste
    test_files = [
        "tests/unit/test_news_analyzer_errors.py",
        "tests/unit/test_news_integrator_errors.py", 
        "tests/unit/test_enhanced_strategy_errors.py",
        "tests/unit/test_telegram_notifier_errors.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        print(f"📋 Executando testes: {test_file}")
        print("-" * 60)
        
        try:
            # Executa pytest para cada arquivo
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True
            )
            
            # Analisa o resultado
            if result.returncode == 0:
                print(f"✅ {test_file}: TODOS OS TESTES PASSARAM")
            else:
                print(f"❌ {test_file}: ALGUNS TESTES FALHARAM")
                
            # Extrai estatísticas do output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'passed' in line or 'failed' in line or 'error' in line:
                    print(f"   {line}")
                    
        except Exception as e:
            print(f"❌ Erro ao executar {test_file}: {str(e)}")
            
        print()
    
    print("=== Executando todos os testes juntos ===")
    print("-" * 60)
    
    try:
        # Executa todos os testes juntos
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        # Analisa resultado final
        if result.returncode == 0:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
        else:
            print("\n⚠️  ALGUNS TESTES FALHARAM - Verifique os detalhes acima")
            
    except Exception as e:
        print(f"❌ Erro ao executar todos os testes: {str(e)}")
    
    print("\n=== Resumo dos problemas testados ===")
    tested_errors = [
        "✅ Erro 1: Método analyze_crypto_news não encontrado",
        "✅ Erro 2: 'NoneType' object has no attribute 'get'",
        "✅ Erro 3: 'dict' object has no attribute 'confidence'",
        "✅ Erro 4: Timeout na análise de sentimento",
        "✅ Erro 5: Lista de sinais IA vazia", 
        "✅ Erro 6: NewsAPI rate limited (comportamento esperado)",
        "",
        "📊 Estatísticas dos testes:",
        f"   - Arquivos de teste: {len(test_files)}",
        f"   - Cobertura: News Analyzer, News Integrator, Enhanced Strategy, Telegram Notifier",
        f"   - Tipos de teste: Validação de dados, tratamento de erros, fallbacks, timeouts",
        "",
        "🔧 Para executar testes específicos:",
        "   pytest tests/unit/test_news_analyzer_errors.py -v",
        "   pytest tests/unit/test_news_integrator_errors.py -v", 
        "   pytest tests/unit/test_enhanced_strategy_errors.py -v",
        "   pytest tests/unit/test_telegram_notifier_errors.py -v"
    ]
    
    for item in tested_errors:
        print(item)

if __name__ == "__main__":
    run_tests()
