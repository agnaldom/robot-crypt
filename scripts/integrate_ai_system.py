#!/usr/bin/env python3
"""
Script de Integração do Sistema de Análise Inteligente ao Bot de Trading
Demonstra como integrar e usar o sistema aprimorado
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ai_integration")


def test_ai_system_availability():
    """Testa se o sistema de IA está disponível"""
    print("🔍 Verificando disponibilidade do Sistema de Análise Inteligente...")
    
    try:
        from src.analysis.symbol_analyzer import SymbolAnalyzer, analyze_symbol
        print("   ✅ Sistema de Análise Inteligente disponível")
        return True
    except ImportError as e:
        print(f"   ❌ Sistema de Análise não disponível: {str(e)}")
        return False


def test_enhanced_strategies():
    """Testa se as estratégias aprimoradas estão disponíveis"""
    print("🔍 Verificando estratégias aprimoradas...")
    
    try:
        from src.strategies.enhanced_strategy import (
            EnhancedScalpingStrategy, 
            EnhancedSwingTradingStrategy,
            create_enhanced_strategy
        )
        print("   ✅ Estratégias aprimoradas disponíveis")
        return True
    except ImportError as e:
        print(f"   ❌ Estratégias aprimoradas não disponíveis: {str(e)}")
        return False


def demo_ai_analysis():
    """Demonstra análise com IA"""
    print("\n🤖 Demonstração de Análise Inteligente...")
    
    try:
        from src.analysis.symbol_analyzer import analyze_symbol
        
        # Demonstra análise de alguns símbolos
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        for symbol in symbols:
            print(f"\n📊 Analisando {symbol}...")
            
            # Executa análise (com dados simulados, pois não temos API real)
            result = analyze_symbol(symbol, timeframe='1h', limit=100)
            
            if result:
                print(f"   ✅ Análise concluída para {symbol}")
                
                # Mostra resumo
                summary = result.get('summary', {})
                signals_count = summary.get('signals_count', {})
                recommendation = summary.get('recommendation', 'N/A')
                risk_level = result.get('risk_analysis', {}).get('overall_risk', 'N/A')
                opportunity_level = result.get('opportunity_analysis', {}).get('overall_opportunity', 'N/A')
                
                print(f"   📈 Sinais: {signals_count.get('total', 0)} total")
                print(f"   💡 Recomendação: {recommendation.upper()}")
                print(f"   ⚠️ Risco: {risk_level}")
                print(f"   💎 Oportunidade: {opportunity_level}")
            else:
                print(f"   ⚠️ Análise de {symbol} retornou resultado vazio")
                
    except Exception as e:
        print(f"   ❌ Erro na demonstração: {str(e)}")


def demo_enhanced_strategy():
    """Demonstra uso de estratégia aprimorada"""
    print("\n🚀 Demonstração de Estratégia Aprimorada...")
    
    try:
        from src.strategies.enhanced_strategy import create_enhanced_strategy
        
        # Mock de configuração e API
        class MockConfig:
            def __init__(self):
                self.scalping = {
                    'risk_per_trade': 0.01,
                    'profit_target': 0.02,
                    'stop_loss': 0.005,
                    'max_position_size': 0.05
                }
                self.swing_trading = {
                    'max_position_size': 0.05,
                    'profit_target': 0.08,
                    'stop_loss': 0.03,
                    'max_hold_time': 48,
                    'min_volume_increase': 0.3,
                    'entry_delay': 5
                }
                self.max_trades_per_day = 10
                self.max_consecutive_losses = 2
                self.risk_reduction_factor = 0.5
        
        class MockBinanceAPI:
            def get_account_info(self):
                return {'balances': [{'asset': 'USDT', 'free': '1000', 'locked': '0'}]}
            
            def get_klines(self, symbol, interval, limit):
                return []  # Dados simulados
        
        config = MockConfig()
        binance_api = MockBinanceAPI()
        
        # Testa criação de estratégias
        for strategy_type in ['scalping', 'swing']:
            print(f"\n🔧 Criando estratégia {strategy_type} aprimorada...")
            
            try:
                strategy = create_enhanced_strategy(strategy_type, config, binance_api)
                print(f"   ✅ Estratégia {strategy_type} criada: {strategy.__class__.__name__}")
                
                # Verifica se IA está ativa
                if hasattr(strategy, 'analysis_enabled'):
                    ai_status = "ATIVA" if strategy.analysis_enabled else "INATIVA"
                    print(f"   🤖 Sistema de IA: {ai_status}")
                    
                    if strategy.analysis_enabled:
                        # Mostra configurações de análise
                        config_info = strategy.analysis_config
                        print(f"   ⚙️ Configurações de IA:")
                        print(f"      - Timeframe: {config_info.get('timeframe', 'N/A')}")
                        print(f"      - Confiança mínima: {config_info.get('min_confidence_threshold', 0)*100:.0f}%")
                        print(f"      - Ajuste de risco: {'SIM' if config_info.get('risk_adjustment') else 'NÃO'}")
                
            except Exception as e:
                print(f"   ❌ Erro ao criar estratégia {strategy_type}: {str(e)}")
                
    except Exception as e:
        print(f"   ❌ Erro na demonstração de estratégia: {str(e)}")


def show_integration_guide():
    """Mostra guia de integração"""
    print("\n📚 GUIA DE INTEGRAÇÃO")
    print("=" * 60)
    
    print("\n1. 🔧 CONFIGURAÇÃO BÁSICA")
    print("   Para usar o sistema aprimorado, certifique-se de que:")
    print("   - O PostgreSQL está configurado (opcional)")
    print("   - Os módulos de análise estão instalados")
    print("   - As dependências estão atualizadas")
    
    print("\n2. 🤖 SISTEMA DE ANÁLISE INTELIGENTE")
    print("   O sistema analisa automaticamente:")
    print("   - Indicadores técnicos (RSI, MACD, Bollinger, etc.)")
    print("   - Padrões de preço (Doji, Hammer, Breakouts)")
    print("   - Volume e volatilidade")
    print("   - Níveis de risco e oportunidade")
    
    print("\n3. 🚀 ESTRATÉGIAS APRIMORADAS")
    print("   As estratégias aprimoradas combinam:")
    print("   - Análise tradicional do bot")
    print("   - Sinais inteligentes da IA")
    print("   - Ajuste dinâmico de risco")
    print("   - Decisões baseadas em múltiplos fatores")
    
    print("\n4. 🎯 COMO FUNCIONA A INTEGRAÇÃO")
    print("   O bot automaticamente:")
    print("   - Detecta se o sistema IA está disponível")
    print("   - Carrega estratégias aprimoradas quando possível")
    print("   - Usa estratégias tradicionais como fallback")
    print("   - Combina análises para decisões mais inteligentes")
    
    print("\n5. 📊 EXEMPLO DE USO NO BOT")
    print("   ```python")
    print("   # O bot agora faz automaticamente:")
    print("   # 1. Análise tradicional (suporte/resistência)")
    print("   # 2. Análise IA (indicadores + padrões)")
    print("   # 3. Combinação das análises")
    print("   # 4. Decisão final baseada em confiança")
    print("   # 5. Ajuste de risco baseado na IA")
    print("   ```")
    
    print("\n6. 🔍 MONITORAMENTO")
    print("   Verifique os logs para:")
    print("   - ✅ 'Estratégia APRIMORADA com IA inicializada'")
    print("   - 🤖 'Usando estratégia aprimorada: Enhanced...'")
    print("   - 🎯 'Melhor sinal IA - BUY/SELL (confiança: X%)'")
    print("   - ⚖️ 'Ajuste de posição: X -> Y (risco: ...)'")


def check_dependencies():
    """Verifica dependências necessárias"""
    print("\n🔍 Verificando dependências...")
    
    dependencies = [
        ('pandas', 'Manipulação de dados'),
        ('numpy', 'Cálculos numéricos'),
        ('psycopg2', 'Driver PostgreSQL (opcional)')
    ]
    
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"   ✅ {package}: {description}")
        except ImportError:
            print(f"   ❌ {package}: {description} - NÃO INSTALADO")


def main():
    """Função principal"""
    print("🔗 INTEGRAÇÃO DO SISTEMA DE ANÁLISE INTELIGENTE")
    print("=" * 60)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verifica dependências
    check_dependencies()
    
    # Testa disponibilidade dos sistemas
    ai_available = test_ai_system_availability()
    strategies_available = test_enhanced_strategies()
    
    print(f"\n📋 STATUS DO SISTEMA:")
    print(f"   🤖 Sistema de IA: {'✅ DISPONÍVEL' if ai_available else '❌ INDISPONÍVEL'}")
    print(f"   🚀 Estratégias Aprimoradas: {'✅ DISPONÍVEL' if strategies_available else '❌ INDISPONÍVEL'}")
    
    if ai_available and strategies_available:
        print(f"\n🎉 SISTEMA TOTALMENTE INTEGRADO!")
        print("   O bot agora usará análise inteligente automaticamente.")
        
        # Demonstrações
        demo_ai_analysis()
        demo_enhanced_strategy()
        
    elif ai_available and not strategies_available:
        print(f"\n⚠️ INTEGRAÇÃO PARCIAL")
        print("   Sistema de IA disponível, mas estratégias aprimoradas não.")
        print("   O bot usará estratégias tradicionais.")
        
    else:
        print(f"\n❌ SISTEMA NÃO INTEGRADO")
        print("   O bot funcionará apenas com estratégias tradicionais.")
        print("\n🔧 Para habilitar o sistema completo:")
        print("   1. Verifique se todos os arquivos foram criados")
        print("   2. Instale dependências: pip install pandas numpy")
        print("   3. Configure PostgreSQL (opcional)")
        print("   4. Execute o teste novamente")
    
    # Mostra guia de integração
    show_integration_guide()
    
    print(f"\n✅ Verificação de integração concluída!")
    print(f"📁 Execute 'python start_robot.py' para usar o bot integrado")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro durante verificação: {str(e)}")
        print(f"❌ Erro: {str(e)}")
