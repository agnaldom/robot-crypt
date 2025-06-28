#!/usr/bin/env python3
"""
Script para executar todos os testes do Robot-Crypt
"""
import sys
import unittest
import os

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Execute todos os testes do projeto"""
    print("=" * 70)
    print("               TESTES AUTOMATIZADOS ROBOT-CRYPT                  ")
    print("=" * 70)
    
    # Descobre e executa todos os testes nas subpastas
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # Retorna 0 se todos os testes passaram, ou 1 se algum falhou
    return 0 if test_result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
