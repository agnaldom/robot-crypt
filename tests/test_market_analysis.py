#!/usr/bin/env python3
"""
Testes unitários para o módulo de análise de mercado do Robot-Crypt
"""
import unittest
import sys
import os
import json
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações do Robot-Crypt
from config import Config
from binance_api import BinanceAPI
from strategy import ScalpingStrategy, SwingTradingStrategy
from binance_simulator import BinanceSimulator

class MarketAnalysisTest(unittest.TestCase):
    """Testes para a funcionalidade de análise de mercado"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial executada uma vez antes de todos os testes"""
        cls.config = Config()
        
        # Usa o simulador para testes independentes de API externa
        cls.binance = BinanceSimulator()
        
        # Inicializa as estratégias
        cls.scalping = ScalpingStrategy(cls.config, cls.binance)
        cls.swing = SwingTradingStrategy(cls.config, cls.binance)
        
        # Lista de pares para teste
        cls.test_pairs = ["BTC/USDT", "ETH/USDT", "DOGE/USDT"]
    
    def test_strategy_instantiation(self):
        """Testa se as estratégias foram inicializadas corretamente"""
        self.assertIsInstance(self.scalping, ScalpingStrategy)
        self.assertIsInstance(self.swing, SwingTradingStrategy)
    
    def test_market_data_fetch(self):
        """Testa se os dados de mercado podem ser obtidos"""
        for pair in self.test_pairs:
            with self.subTest(pair=pair):
                ticker = self.binance.fetch_ticker(pair)
                self.assertIsNotNone(ticker)
                self.assertIn('last', ticker)
                self.assertIsInstance(ticker['last'], (int, float))
    
    def test_scalping_analysis(self):
        """Testa a análise de mercado na estratégia de Scalping"""
        for pair in self.test_pairs:
            with self.subTest(pair=pair):
                start_time = datetime.now()
                should_trade, action, price = self.scalping.analyze_market(pair)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Verifica o formato da resposta
                self.assertIsInstance(should_trade, bool)
                self.assertIn(action, ['buy', 'sell', 'hold', ''])
                self.assertIsInstance(price, (int, float, type(None)))
                
                # Verifica o tempo de execução
                self.assertLess(duration, 5.0, f"Análise para {pair} demorou muito: {duration:.2f}s")
    
    def test_swing_analysis(self):
        """Testa a análise de mercado na estratégia de Swing Trading"""
        for pair in self.test_pairs:
            with self.subTest(pair=pair):
                start_time = datetime.now()
                should_trade, action, price = self.swing.analyze_market(pair)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Verifica o formato da resposta
                self.assertIsInstance(should_trade, bool)
                self.assertIn(action, ['buy', 'sell', 'hold', ''])
                self.assertIsInstance(price, (int, float, type(None)))
                
                # Verifica o tempo de execução
                self.assertLess(duration, 5.0, f"Análise para {pair} demorou muito: {duration:.2f}s")
    
    def test_multiple_analyses(self):
        """Testa múltiplas análises consecutivas para verificar estabilidade"""
        pair = "BTC/USDT"  # Usa apenas um par para este teste
        durations = []
        
        for i in range(5):
            start_time = datetime.now()
            should_trade, _, _ = self.swing.analyze_market(pair)
            duration = (datetime.now() - start_time).total_seconds()
            durations.append(duration)
            
            # Pequena pausa entre análises
            import time
            time.sleep(0.1)
        
        # Verifica se o tempo de análise não aumenta significativamente
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        print(f"\nTempos de análise para {pair}: {durations}")
        print(f"Média: {avg_duration:.3f}s, Máximo: {max_duration:.3f}s")
        
        # Verifica se não há variação excessiva (mais de 100% acima da média)
        for duration in durations:
            self.assertLess(duration, avg_duration * 2.0, 
                           f"Variação excessiva no tempo de análise: {duration:.3f}s vs média {avg_duration:.3f}s")

    def test_memory_usage(self):
        """Testa o uso de memória durante análises repetidas"""
        try:
            import psutil
            import gc
            
            process = psutil.Process(os.getpid())
            
            # Força coleta de lixo antes do teste
            gc.collect()
            
            # Mede uso inicial de memória
            initial_memory = process.memory_info().rss / (1024 * 1024)  # Em MB
            
            # Executa várias análises
            for _ in range(10):
                for pair in self.test_pairs:
                    self.swing.analyze_market(pair)
            
            # Força coleta de lixo novamente
            gc.collect()
            
            # Mede uso final de memória
            final_memory = process.memory_info().rss / (1024 * 1024)  # Em MB
            
            # Calcula aumento de memória
            memory_increase = final_memory - initial_memory
            
            print(f"\nUso de memória: Inicial {initial_memory:.2f} MB, Final {final_memory:.2f} MB")
            print(f"Aumento: {memory_increase:.2f} MB")
            
            # Verifica se não há vazamento significativo de memória
            self.assertLess(memory_increase, 50.0, f"Possível vazamento de memória: {memory_increase:.2f} MB")
            
        except ImportError:
            print("Módulo psutil não instalado, pulando teste de memória")
            self.skipTest("psutil não disponível")

if __name__ == '__main__':
    unittest.main()
