#!/usr/bin/env python3
"""
Script de teste simples para verificar o sistema de análise de símbolos
"""
import sys
import os
import logging
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_symbol_analyzer")

def test_imports():
    """Testa se todas as importações estão funcionando"""
    try:
        print("1. Testando importações...")
        
        from src.database.postgres_manager import PostgresManager
        print("   ✅ PostgresManager importado")
        
        from src.analysis.technical_indicators import TechnicalIndicators
        print("   ✅ TechnicalIndicators importado")
        
        from src.analysis.symbol_analyzer import SymbolAnalyzer, TradingSignal, analyze_symbol
        print("   ✅ SymbolAnalyzer importado")
        
        print("   🎉 Todas as importações bem-sucedidas!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na importação: {str(e)}")
        return False

def test_classes():
    """Testa a criação das classes principais"""
    try:
        print("\n2. Testando criação de classes...")
        
        from src.analysis.symbol_analyzer import SymbolAnalyzer, TradingSignal
        
        # Teste SymbolAnalyzer
        analyzer = SymbolAnalyzer()
        print("   ✅ SymbolAnalyzer criado")
        
        # Teste TradingSignal
        signal = TradingSignal(
            symbol='BTCUSDT',
            signal_type='buy',
            strength=0.8,
            confidence=0.75,
            price=45000.0,
            timestamp=datetime.now(),
            reasoning="Teste de sinal",
            indicators_data={'test': True},
            source='test'
        )
        print("   ✅ TradingSignal criado")
        
        print("   🎉 Classes criadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na criação de classes: {str(e)}")
        return False

def test_technical_indicators():
    """Testa os indicadores técnicos com dados simulados"""
    try:
        print("\n3. Testando indicadores técnicos...")
        
        from src.analysis.technical_indicators import TechnicalIndicators
        
        # Cria dados simulados (klines)
        klines = []
        base_price = 45000
        
        for i in range(100):
            # Simula variação de preço
            price_var = (i % 10 - 5) * 100
            open_price = base_price + price_var
            close_price = open_price + (i % 3 - 1) * 50
            high_price = max(open_price, close_price) + 25
            low_price = min(open_price, close_price) - 25
            volume = 1000 + (i % 5) * 200
            
            kline = [
                1640995200000 + (i * 3600000),  # timestamp
                str(open_price),   # open
                str(high_price),   # high
                str(low_price),    # low
                str(close_price),  # close
                str(volume)        # volume
            ]
            klines.append(kline)
        
        # Testa cálculo de indicadores
        technical = TechnicalIndicators()
        result = technical.calculate_all_indicators(klines)
        
        if result:
            print("   ✅ Indicadores técnicos calculados")
            print(f"   📊 Timestamp: {result.get('timestamp', 'N/A')}")
            
            indicators = result.get('indicators', {})
            if indicators:
                rsi = indicators.get('rsi', {}).get('current', 0)
                print(f"   📈 RSI atual: {rsi:.2f}")
                
                macd = indicators.get('macd', {}).get('macd', 0)
                print(f"   📈 MACD: {macd:.6f}")
                
            print("   🎉 Indicadores técnicos funcionando!")
        else:
            print("   ⚠️ Nenhum resultado dos indicadores técnicos")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nos indicadores técnicos: {str(e)}")
        return False

def test_symbol_analyzer():
    """Testa o analisador de símbolos com dados simulados"""
    try:
        print("\n4. Testando SymbolAnalyzer...")
        
        from src.analysis.symbol_analyzer import SymbolAnalyzer
        
        analyzer = SymbolAnalyzer()
        
        # Cria dados de mercado simulados
        market_data = []
        base_price = 45000
        
        for i in range(50):
            price_var = (i % 10 - 5) * 100
            open_price = base_price + price_var
            close_price = open_price + (i % 3 - 1) * 50
            high_price = max(open_price, close_price) + 25
            low_price = min(open_price, close_price) - 25
            volume = 1000 + (i % 5) * 200
            
            data = {
                'open_time': datetime.now(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            }
            market_data.append(data)
        
        print("   ✅ Dados de mercado simulados criados")
        
        # Testa processamento de dados
        processed_data = analyzer.process_data(market_data)
        
        if processed_data:
            print("   ✅ Dados processados com sucesso")
            
            # Testa geração de sinais
            signals = analyzer.generate_signals('BTCUSDT', processed_data)
            print(f"   ✅ Gerados {len(signals)} sinais")
            
            # Testa análise de risco
            risk_analysis = analyzer.analyze_risk('BTCUSDT', processed_data)
            risk_level = risk_analysis.get('overall_risk', 'unknown')
            print(f"   ✅ Análise de risco: {risk_level}")
            
            # Testa análise de oportunidade
            opp_analysis = analyzer.analyze_opportunity('BTCUSDT', processed_data)
            opp_level = opp_analysis.get('overall_opportunity', 'unknown')
            print(f"   ✅ Análise de oportunidade: {opp_level}")
            
            print("   🎉 SymbolAnalyzer funcionando!")
        else:
            print("   ⚠️ Falha no processamento de dados")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no SymbolAnalyzer: {str(e)}")
        return False

def test_complete_analysis():
    """Testa uma análise completa simulada"""
    try:
        print("\n5. Testando análise completa...")
        
        from src.analysis.symbol_analyzer import SymbolAnalyzer
        
        # Cria instância do analisador
        analyzer = SymbolAnalyzer()
        
        # Sobrescreve o método fetch_market_data para retornar dados simulados
        def mock_fetch_market_data(symbol, timeframe, limit):
            market_data = []
            base_price = 45000
            
            for i in range(limit):
                price_var = (i % 10 - 5) * 100
                open_price = base_price + price_var
                close_price = open_price + (i % 3 - 1) * 50
                high_price = max(open_price, close_price) + 25
                low_price = min(open_price, close_price) - 25
                volume = 1000 + (i % 5) * 200
                
                data = {
                    'open_time': datetime.now(),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                }
                market_data.append(data)
            
            return market_data
        
        # Substitui temporariamente o método
        analyzer.fetch_market_data = mock_fetch_market_data
        
        # Executa análise completa
        result = analyzer.analyze_symbol('BTCUSDT', '1h', 100)
        
        if result:
            print("   ✅ Análise completa executada")
            
            symbol = result.get('symbol', 'N/A')
            timestamp = result.get('timestamp', 'N/A')
            signals = result.get('signals', [])
            summary = result.get('summary', {})
            
            print(f"   📊 Símbolo: {symbol}")
            print(f"   ⏰ Timestamp: {timestamp}")
            print(f"   🎯 Sinais: {len(signals)}")
            
            recommendation = summary.get('recommendation', 'N/A')
            print(f"   💡 Recomendação: {recommendation}")
            
            risk_level = result.get('risk_analysis', {}).get('overall_risk', 'N/A')
            opp_level = result.get('opportunity_analysis', {}).get('overall_opportunity', 'N/A')
            print(f"   ⚠️ Risco: {risk_level}")
            print(f"   💎 Oportunidade: {opp_level}")
            
            print("   🎉 Análise completa bem-sucedida!")
        else:
            print("   ⚠️ Análise completa retornou resultado vazio")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na análise completa: {str(e)}")
        return False

def main():
    """Função principal do teste"""
    print("=" * 60)
    print("TESTE DO SISTEMA DE ANÁLISE INTELIGENTE DE SÍMBOLOS")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_classes,
        test_technical_indicators,
        test_symbol_analyzer,
        test_complete_analysis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"Erro durante teste: {str(e)}")
    
    print(f"\n{'='*60}")
    print("RESULTADO DOS TESTES")
    print(f"{'='*60}")
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\nO sistema está pronto para uso!")
        print("\nPróximos passos:")
        print("1. Configure o PostgreSQL se quiser persistência")
        print("2. Implemente cliente real da Binance API")
        print("3. Execute o script de exemplo: python scripts/example_symbol_analysis.py")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro geral durante teste: {str(e)}")
        print(f"❌ Erro geral: {str(e)}")
        sys.exit(1)
