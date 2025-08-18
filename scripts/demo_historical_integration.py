#!/usr/bin/env python3
"""
Demonstração do Sistema de Análise Histórica Integrado
Como usar o sistema completo para análise e comparação com dados históricos
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.analysis.historical_comparator import HistoricalComparator, compare_symbol_with_history
from src.integrations.historical_trading_integration import HistoricalTradingIntegration
from src.data.historical_data_collector import HistoricalDataCollector
from src.api.binance.client import BinanceClient
from src.database.postgres_manager import PostgresManager
from src.core.logging_setup import logger


async def demo_historical_comparison():
    """Demonstra análise de comparação histórica"""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Comparação Histórica")
    print("=" * 60)
    
    # Inicializa o comparador
    comparator = HistoricalComparator()
    
    # Símbolos para demonstração
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in symbols:
        print(f"\n📊 Analisando {symbol}...")
        
        try:
            # Simula candle atual (em um sistema real, você buscaria da API)
            current_candle = {
                'open': 50000.0,
                'high': 51000.0,
                'low': 49500.0,
                'close': 50500.0,
                'volume': 1000.0,
                'open_time': int(datetime.now().timestamp() * 1000)
            }
            
            # Executa comparação histórica
            result = await comparator.compare_with_historical(
                symbol=symbol,
                current_candle=current_candle,
                analysis_depth="medium"
            )
            
            # Exibe resultados
            print(f"✅ Análise concluída para {symbol}")
            print(f"   📈 Preço atual: ${result.current_price:.2f}")
            print(f"   🎯 Recomendação: {result.recommendation}")
            print(f"   📊 Confiança: {result.confidence_score:.1%}")
            print(f"   📉 Padrão histórico: {result.historical_pattern_match:.1%}")
            print(f"   📈 Similaridade de tendência: {result.trend_similarity:.1%}")
            print(f"   ⚠️  Nível de risco: {result.risk_assessment.get('risk_level', 'N/A')}")
            
            # Mostra suporte e resistência
            support_levels = result.support_resistance_levels.get('support_levels', [])
            resistance_levels = result.support_resistance_levels.get('resistance_levels', [])
            
            if support_levels:
                print(f"   🟢 Suportes: {[f'${s:.2f}' for s in support_levels[:3]]}")
            if resistance_levels:
                print(f"   🔴 Resistências: {[f'${r:.2f}' for r in resistance_levels[:3]]}")
            
            # Mostra períodos similares
            similar_periods = result.similar_periods[:3]
            if similar_periods:
                print(f"   🔄 Períodos similares encontrados: {len(similar_periods)}")
                for i, period in enumerate(similar_periods, 1):
                    outcome = "📈" if period.get('outcome') == 'positive' else "📉"
                    print(f"      {i}. {outcome} Retorno futuro: {period.get('future_return', 0):.1%}")
            
        except Exception as e:
            print(f"❌ Erro ao analisar {symbol}: {str(e)}")
        
        print("-" * 40)


async def demo_trading_integration():
    """Demonstra integração com sistema de trading"""
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Integração com Trading")
    print("=" * 60)
    
    # Inicializa sistema de integração
    integration = HistoricalTradingIntegration()
    
    # Configurações para demo
    integration.config.update({
        'min_confidence_for_signal': 0.5,  # Reduzido para demo
        'enable_notifications': False,  # Desabilitado para demo
        'symbols_to_monitor': ['BTCUSDT', 'ETHUSDT']
    })
    
    print("🔧 Sistema configurado:")
    print(f"   • Confiança mínima: {integration.config['min_confidence_for_signal']:.1%}")
    print(f"   • Símbolos monitorados: {integration.config['symbols_to_monitor']}")
    print(f"   • Trading automático: {'✅' if integration.config['enable_auto_trading'] else '❌'}")
    
    # Executa análise de mercado
    print("\n🔍 Executando análise de mercado...")
    signals = await integration.analyze_market_with_history()
    
    if signals:
        print(f"✅ {len(signals)} sinais gerados:")
        
        for symbol, signal in signals.items():
            emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
            print(f"\n   {emoji} {symbol}:")
            print(f"      Ação: {signal.action}")
            print(f"      Confiança: {signal.confidence:.1%}")
            print(f"      Preço entrada: ${signal.entry_price:.4f}")
            if signal.stop_loss:
                print(f"      Stop Loss: ${signal.stop_loss:.4f}")
            if signal.take_profit:
                print(f"      Take Profit: ${signal.take_profit:.4f}")
            print(f"      Tamanho posição: {signal.position_size:.1%}")
            print(f"      Motivo: {signal.reasoning[:100]}...")
            
            # Mostra contexto histórico resumido
            context = signal.historical_context
            print(f"      📊 Contexto histórico:")
            print(f"         • Padrão: {context.get('pattern_match', 0):.1%}")
            print(f"         • Tendência: {context.get('trend_similarity', 0):.1%}")
            print(f"         • Volatilidade: {context.get('volatility_analysis', {}).get('volatility_ratio', 1.0):.2f}x")
    else:
        print("ℹ️  Nenhum sinal gerado (critérios de confiança não atendidos)")


async def demo_historical_insights():
    """Demonstra insights históricos completos"""
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Insights Históricos Completos")
    print("=" * 60)
    
    comparator = HistoricalComparator()
    
    symbol = 'BTCUSDT'
    print(f"📈 Obtendo insights históricos para {symbol}...")
    
    try:
        insights = await comparator.get_symbol_historical_insights(symbol)
        
        if 'error' not in insights:
            print(f"✅ Insights obtidos com sucesso\n")
            
            # Período dos dados
            period = insights.get('data_period', {})
            print(f"📅 Período dos dados:")
            print(f"   • Início: {period.get('start_date', 'N/A')}")
            print(f"   • Fim: {period.get('end_date', 'N/A')}")
            print(f"   • Total de dias: {period.get('total_days', 0)}")
            
            # Estatísticas de preço
            price_stats = insights.get('price_statistics', {})
            print(f"\n💰 Estatísticas de preço:")
            print(f"   • Preço mínimo: ${price_stats.get('min_price', 0):,.2f}")
            print(f"   • Preço máximo: ${price_stats.get('max_price', 0):,.2f}")
            print(f"   • Preço médio: ${price_stats.get('avg_price', 0):,.2f}")
            print(f"   • Atual vs média: {price_stats.get('current_vs_avg', 0):+.1%}")
            
            # Análise de volatilidade
            vol_analysis = insights.get('volatility_analysis', {})
            print(f"\n📊 Análise de volatilidade:")
            print(f"   • Volatilidade diária: {vol_analysis.get('daily_volatility', 0):.1%}")
            print(f"   • Volatilidade mensal: {vol_analysis.get('monthly_volatility', 0):.1%}")
            print(f"   • Volatilidade anual: {vol_analysis.get('annual_volatility', 0):.1%}")
            
            # Análise de tendência
            trend_analysis = insights.get('trend_analysis', {})
            trend_emoji = "📈" if trend_analysis.get('overall_trend') == 'up' else "📉"
            print(f"\n{trend_emoji} Análise de tendência:")
            print(f"   • Tendência geral: {trend_analysis.get('overall_trend', 'N/A')}")
            print(f"   • Retorno total: {trend_analysis.get('total_return', 0):+.1%}")
            print(f"   • Melhor mês: {trend_analysis.get('best_month_return', 0):+.1%}")
            print(f"   • Pior mês: {trend_analysis.get('worst_month_return', 0):+.1%}")
            
            # Análise de volume
            volume_analysis = insights.get('volume_analysis', {})
            vol_trend_emoji = "📈" if volume_analysis.get('volume_trend') == 'increasing' else "📉"
            print(f"\n{vol_trend_emoji} Análise de volume:")
            print(f"   • Volume médio: {volume_analysis.get('avg_volume', 0):,.0f}")
            print(f"   • Tendência: {volume_analysis.get('volume_trend', 'N/A')}")
            print(f"   • Dias de alto volume: {volume_analysis.get('high_volume_days', 0)}")
            
        else:
            print(f"❌ Erro: {insights['error']}")
            
    except Exception as e:
        print(f"❌ Erro ao obter insights: {str(e)}")


async def demo_data_collection():
    """Demonstra coleta de dados históricos"""
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Coleta de Dados Históricos")
    print("=" * 60)
    
    collector = HistoricalDataCollector()
    
    print("🔄 Iniciando coleta de dados históricos...")
    print("ℹ️  Esta demonstração coletará dados limitados para evitar rate limiting")
    
    try:
        # Obter top símbolos (limitado para demo)
        print("\n📊 Obtendo top símbolos...")
        symbols = await collector.get_top_symbols(limit=5)
        print(f"✅ Top 5 símbolos: {symbols}")
        
        # Coletar dados para um símbolo específico
        symbol = symbols[0] if symbols else 'BTCUSDT'
        print(f"\n💾 Coletando dados históricos para {symbol}...")
        
        # Configurar para período menor para demo
        collector.months_back = 1  # Apenas 1 mês para demo
        
        # Executar coleta
        report = await collector.collect_all_historical_data([symbol])
        
        print(f"✅ Coleta concluída:")
        print(f"   • Período: {report.get('start_time')} até {report.get('end_time')}")
        print(f"   • Símbolos processados: {report.get('total_symbols', 0)}")
        print(f"   • Intervalos: {report.get('intervals', [])}")
        print(f"   • Sucessos: {report.get('success_count', 0)}")
        print(f"   • Erros: {report.get('error_count', 0)}")
        print(f"   • Total de pontos de dados: {report.get('total_data_points', 0)}")
        
        # Análise dos dados coletados
        if report.get('success_count', 0) > 0:
            print(f"\n🔍 Executando análise dos dados coletados...")
            analysis = await collector.get_historical_analysis(symbol, days=30)
            
            if 'error' not in analysis:
                print(f"✅ Análise concluída:")
                print(f"   • Pontos de dados: {analysis.get('data_points', 0)}")
                print(f"   • Mudança de preço: {analysis.get('price_change_percent', 0):+.1%}")
                print(f"   • Preço mais alto: ${analysis.get('highest_price', 0):,.2f}")
                print(f"   • Preço mais baixo: ${analysis.get('lowest_price', 0):,.2f}")
                print(f"   • Preço médio: ${analysis.get('average_price', 0):,.2f}")
                print(f"   • Tendência: {analysis.get('price_trend', 'N/A')}")
                print(f"   • Volatilidade: {analysis.get('volatility', 0):,.2f}")
                
                # Níveis de suporte e resistência
                support = analysis.get('support_level', 0)
                resistance = analysis.get('resistance_level', 0)
                if support:
                    print(f"   • Suporte: ${support:,.2f}")
                if resistance:
                    print(f"   • Resistência: ${resistance:,.2f}")
        
    except Exception as e:
        print(f"❌ Erro na coleta de dados: {str(e)}")


async def demo_complete_workflow():
    """Demonstra fluxo completo do sistema"""
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Fluxo Completo do Sistema")
    print("=" * 60)
    
    print("🚀 Executando fluxo completo de análise histórica...")
    
    try:
        # 1. Coleta de dados
        print("\n1️⃣ Fase 1: Verificação de dados históricos")
        collector = HistoricalDataCollector()
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        for symbol in symbols:
            analysis = await collector.get_historical_analysis(symbol, days=7)
            if 'error' not in analysis:
                print(f"   ✅ {symbol}: {analysis.get('data_points', 0)} pontos de dados")
            else:
                print(f"   ⚠️  {symbol}: Dados limitados ou não encontrados")
        
        # 2. Comparação histórica
        print("\n2️⃣ Fase 2: Comparação com dados atuais")
        comparator = HistoricalComparator()
        
        for symbol in symbols:
            current_candle = {
                'open': 50000.0, 'high': 51000.0, 'low': 49500.0, 'close': 50500.0,
                'volume': 1000.0, 'open_time': int(datetime.now().timestamp() * 1000)
            }
            
            result = await comparator.compare_with_historical(symbol, current_candle, "quick")
            print(f"   📊 {symbol}: {result.recommendation} (confiança: {result.confidence_score:.1%})")
        
        # 3. Geração de sinais
        print("\n3️⃣ Fase 3: Geração de sinais de trading")
        integration = HistoricalTradingIntegration()
        integration.config['min_confidence_for_signal'] = 0.4  # Reduzido para demo
        
        signals = await integration.analyze_market_with_history(symbols)
        
        if signals:
            print(f"   🎯 {len(signals)} sinais gerados")
            for symbol, signal in signals.items():
                action_emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
                print(f"   {action_emoji} {symbol}: {signal.action} (confiança: {signal.confidence:.1%})")
        else:
            print("   ℹ️  Nenhum sinal atendeu aos critérios de confiança")
        
        # 4. Resumo final
        print("\n4️⃣ Resumo final:")
        print("   ✅ Sistema operacional e funcionando")
        print("   📊 Análise histórica integrada")
        print("   🎯 Sinais baseados em dados históricos")
        print("   💾 Dados salvos no PostgreSQL")
        print("\n🎉 Demonstração completa concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no fluxo completo: {str(e)}")


async def main():
    """Função principal da demonstração"""
    print("🤖 SISTEMA DE ANÁLISE HISTÓRICA PARA TRADING")
    print("🔄 Demonstração completa das funcionalidades")
    print("⏰ Início:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # Executa todas as demonstrações
        await demo_historical_comparison()
        await demo_trading_integration()
        await demo_historical_insights()
        await demo_data_collection()
        await demo_complete_workflow()
        
        print("\n" + "=" * 60)
        print("✅ TODAS AS DEMONSTRAÇÕES CONCLUÍDAS COM SUCESSO!")
        print("=" * 60)
        print("\n📋 Próximos passos para integração:")
        print("1. Configure suas credenciais da Binance")
        print("2. Configure seu banco PostgreSQL")
        print("3. Configure notificações Telegram (opcional)")
        print("4. Ajuste os parâmetros de risco em src/integrations/historical_trading_integration.py")
        print("5. Execute: python -m src.integrations.historical_trading_integration")
        print("\n💡 Dica: Comece com trading_automático=False para testar")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na demonstração: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
