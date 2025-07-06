#!/usr/bin/env python3
"""
Script de exemplo para demonstrar o uso do sistema de análise de símbolos
"""
import sys
import os
import json
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.symbol_analyzer import SymbolAnalyzer, analyze_symbol
from src.database.postgres_manager import PostgresManager
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("symbol_analysis_example")


def main():
    """Função principal do exemplo"""
    
    print("=" * 60)
    print("SISTEMA DE ANÁLISE INTELIGENTE DE SÍMBOLOS")
    print("=" * 60)
    
    # Lista de símbolos para analisar
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']
    timeframe = '1h'
    
    try:
        # Cria instância do analisador
        analyzer = SymbolAnalyzer()
        
        print(f"\nIniciando análise de {len(symbols)} símbolos...")
        print(f"Timeframe: {timeframe}")
        print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {}
        
        for symbol in symbols:
            print(f"\n{'='*40}")
            print(f"Analisando {symbol}...")
            print(f"{'='*40}")
            
            # Executa análise completa
            result = analyzer.analyze_symbol(symbol, timeframe, limit=100)
            
            if result:
                all_results[symbol] = result
                print_analysis_summary(symbol, result)
            else:
                print(f"❌ Falha na análise de {symbol}")
        
        print(f"\n{'='*60}")
        print("RESUMO GERAL")
        print(f"{'='*60}")
        
        # Resumo geral de todos os símbolos
        print_general_summary(all_results)
        
        # Salva resultados em arquivo
        save_results_to_file(all_results)
        
    except Exception as e:
        logger.error(f"Erro no exemplo: {str(e)}")
        print(f"❌ Erro: {str(e)}")


def print_analysis_summary(symbol: str, analysis: dict):
    """Imprime resumo da análise para um símbolo"""
    
    try:
        summary = analysis.get('summary', {})
        signals = analysis.get('signals', [])
        risk = analysis.get('risk_analysis', {})
        opportunity = analysis.get('opportunity_analysis', {})
        
        print(f"\n📊 ANÁLISE DE {symbol}")
        print(f"⏰ Timestamp: {summary.get('timestamp', 'N/A')}")
        
        # Qualidade dos dados
        data_quality = summary.get('data_quality', {})
        completeness = data_quality.get('completeness', 0) * 100
        print(f"📈 Qualidade dos dados: {completeness:.1f}%")
        
        # Sinais
        signals_count = summary.get('signals_count', {})
        total_signals = signals_count.get('total', 0)
        buy_signals = signals_count.get('buy', 0)
        sell_signals = signals_count.get('sell', 0)
        hold_signals = signals_count.get('hold', 0)
        
        print(f"\n🎯 SINAIS IDENTIFICADOS:")
        print(f"   Total: {total_signals}")
        print(f"   🟢 Compra: {buy_signals}")
        print(f"   🔴 Venda: {sell_signals}")
        print(f"   🟡 Aguardar: {hold_signals}")
        
        # Sinal de maior confiança
        best_signal = summary.get('highest_confidence_signal')
        if best_signal:
            signal_type = best_signal['type'].upper()
            confidence = best_signal['confidence'] * 100
            strength = best_signal['strength'] * 100
            reasoning = best_signal['reasoning']
            
            print(f"\n🎪 MELHOR SINAL:")
            print(f"   Tipo: {signal_type}")
            print(f"   Confiança: {confidence:.1f}%")
            print(f"   Força: {strength:.1f}%")
            print(f"   Motivo: {reasoning}")
        
        # Análise de risco
        risk_level = risk.get('overall_risk', 'unknown').upper()
        risk_score = risk.get('risk_score', 0) * 100
        print(f"\n⚠️  ANÁLISE DE RISCO:")
        print(f"   Nível: {risk_level}")
        print(f"   Score: {risk_score:.1f}%")
        
        risk_factors = risk.get('factors', [])
        if risk_factors:
            print(f"   Fatores:")
            for factor in risk_factors:
                print(f"     - {factor.get('description', 'N/A')}")
        
        # Análise de oportunidade
        opp_level = opportunity.get('overall_opportunity', 'unknown').upper()
        opp_score = opportunity.get('opportunity_score', 0) * 100
        print(f"\n💎 ANÁLISE DE OPORTUNIDADE:")
        print(f"   Nível: {opp_level}")
        print(f"   Score: {opp_score:.1f}%")
        
        opp_factors = opportunity.get('factors', [])
        if opp_factors:
            print(f"   Fatores:")
            for factor in opp_factors:
                print(f"     - {factor.get('description', 'N/A')}")
        
        # Recomendação
        recommendation = summary.get('recommendation', 'hold').upper()
        print(f"\n💡 RECOMENDAÇÃO: {recommendation}")
        
        # Observações
        observations = summary.get('observations', [])
        if observations:
            print(f"\n📝 OBSERVAÇÕES:")
            for obs in observations:
                print(f"   • {obs}")
        
        # Dados técnicos resumidos
        tech_data = analysis.get('market_data', {}).get('technical_indicators', {})
        if tech_data:
            print_technical_summary(tech_data)
            
    except Exception as e:
        logger.error(f"Erro ao imprimir resumo de {symbol}: {str(e)}")


def print_technical_summary(tech_data: dict):
    """Imprime resumo dos indicadores técnicos"""
    
    try:
        indicators = tech_data.get('indicators', {})
        price = tech_data.get('price', {})
        
        print(f"\n🔧 INDICADORES TÉCNICOS:")
        
        # Preço atual
        current_price = price.get('close', 0)
        print(f"   Preço atual: ${current_price:.4f}")
        
        # RSI
        rsi_data = indicators.get('rsi', {})
        rsi_current = rsi_data.get('current', 0)
        rsi_status = "🟢 Normal"
        if rsi_data.get('overbought'):
            rsi_status = "🔴 Sobrecompra"
        elif rsi_data.get('oversold'):
            rsi_status = "🟢 Sobrevenda"
        print(f"   RSI: {rsi_current:.2f} ({rsi_status})")
        
        # MACD
        macd_data = indicators.get('macd', {})
        macd_value = macd_data.get('macd', 0)
        signal_value = macd_data.get('signal', 0)
        macd_status = "🟢 Positivo" if macd_value > signal_value else "🔴 Negativo"
        print(f"   MACD: {macd_value:.6f} ({macd_status})")
        
        # Bandas de Bollinger
        bb_data = indicators.get('bollinger_bands', {})
        upper_band = bb_data.get('upper', 0)
        lower_band = bb_data.get('lower', 0)
        middle_band = bb_data.get('middle', 0)
        
        bb_position = "🟡 Centro"
        if bb_data.get('above_upper'):
            bb_position = "🔴 Acima"
        elif bb_data.get('below_lower'):
            bb_position = "🟢 Abaixo"
        
        print(f"   Bollinger: {lower_band:.4f} | {middle_band:.4f} | {upper_band:.4f} ({bb_position})")
        
        # Médias móveis
        ma_data = indicators.get('moving_averages', {})
        ema9 = ma_data.get('ema_9', 0)
        ema21 = ma_data.get('ema_21', 0)
        sma200 = ma_data.get('sma_200', 0)
        
        trend_status = "🟢 Alta" if current_price > sma200 else "🔴 Baixa"
        print(f"   EMA9: {ema9:.4f} | EMA21: {ema21:.4f} | SMA200: {sma200:.4f}")
        print(f"   Tendência de longo prazo: {trend_status}")
        
    except Exception as e:
        logger.error(f"Erro ao imprimir resumo técnico: {str(e)}")


def print_general_summary(all_results: dict):
    """Imprime resumo geral de todos os símbolos analisados"""
    
    try:
        if not all_results:
            print("❌ Nenhum resultado para mostrar")
            return
        
        buy_recommendations = []
        sell_recommendations = []
        hold_recommendations = []
        high_opportunities = []
        high_risks = []
        
        for symbol, analysis in all_results.items():
            summary = analysis.get('summary', {})
            recommendation = summary.get('recommendation', 'hold')
            
            if recommendation == 'buy':
                buy_recommendations.append(symbol)
            elif recommendation == 'sell':
                sell_recommendations.append(symbol)
            else:
                hold_recommendations.append(symbol)
            
            # Verifica oportunidades altas
            opp_score = analysis.get('opportunity_analysis', {}).get('opportunity_score', 0)
            if opp_score > 0.7:
                high_opportunities.append((symbol, opp_score))
            
            # Verifica riscos altos
            risk_score = analysis.get('risk_analysis', {}).get('risk_score', 0)
            if risk_score > 0.7:
                high_risks.append((symbol, risk_score))
        
        print(f"📊 Total de símbolos analisados: {len(all_results)}")
        
        print(f"\n🎯 RECOMENDAÇÕES:")
        print(f"   🟢 Compra: {len(buy_recommendations)} símbolos {buy_recommendations}")
        print(f"   🔴 Venda: {len(sell_recommendations)} símbolos {sell_recommendations}")
        print(f"   🟡 Aguardar: {len(hold_recommendations)} símbolos {hold_recommendations}")
        
        if high_opportunities:
            print(f"\n💎 ALTAS OPORTUNIDADES:")
            for symbol, score in sorted(high_opportunities, key=lambda x: x[1], reverse=True):
                print(f"   • {symbol}: {score*100:.1f}%")
        
        if high_risks:
            print(f"\n⚠️  ALTOS RISCOS:")
            for symbol, score in sorted(high_risks, key=lambda x: x[1], reverse=True):
                print(f"   • {symbol}: {score*100:.1f}%")
        
        if not high_opportunities and not high_risks:
            print(f"\n✅ Todos os símbolos apresentam risco e oportunidade moderados")
        
    except Exception as e:
        logger.error(f"Erro ao imprimir resumo geral: {str(e)}")


def save_results_to_file(all_results: dict):
    """Salva resultados em arquivo JSON"""
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"symbol_analysis_results_{timestamp}.json"
        
        # Converte datetime objects para strings para serialização JSON
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {key: convert_datetime(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_datetime(all_results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados salvos em: {filename}")
        
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {str(e)}")


def test_individual_functions():
    """Testa funções individuais do sistema"""
    
    print(f"\n{'='*60}")
    print("TESTE DE FUNÇÕES INDIVIDUAIS")
    print(f"{'='*60}")
    
    symbol = 'BTCUSDT'
    
    try:
        analyzer = SymbolAnalyzer()
        
        # Teste 1: Buscar dados de mercado
        print(f"\n1. Buscando dados de mercado para {symbol}...")
        market_data = analyzer.fetch_market_data(symbol, '1h', 50)
        print(f"   ✅ Obtidos {len(market_data)} registros")
        
        if market_data:
            # Teste 2: Processar dados
            print(f"\n2. Processando dados...")
            processed_data = analyzer.process_data(market_data)
            print(f"   ✅ Dados processados com {len(processed_data)} seções")
            
            # Teste 3: Gerar sinais
            print(f"\n3. Gerando sinais...")
            signals = analyzer.generate_signals(symbol, processed_data)
            print(f"   ✅ Gerados {len(signals)} sinais")
            
            # Teste 4: Análise de risco
            print(f"\n4. Analisando riscos...")
            risk_analysis = analyzer.analyze_risk(symbol, processed_data)
            risk_level = risk_analysis.get('overall_risk', 'unknown')
            print(f"   ✅ Nível de risco: {risk_level}")
            
            # Teste 5: Análise de oportunidade
            print(f"\n5. Analisando oportunidades...")
            opp_analysis = analyzer.analyze_opportunity(symbol, processed_data)
            opp_level = opp_analysis.get('overall_opportunity', 'unknown')
            print(f"   ✅ Nível de oportunidade: {opp_level}")
            
            print(f"\n✅ Todos os testes individuais passaram!")
        
    except Exception as e:
        logger.error(f"Erro nos testes individuais: {str(e)}")
        print(f"❌ Erro nos testes: {str(e)}")


if __name__ == "__main__":
    try:
        print("Escolha uma opção:")
        print("1. Análise completa de múltiplos símbolos")
        print("2. Teste de funções individuais")
        print("3. Ambos")
        
        choice = input("\nDigite sua escolha (1-3): ").strip()
        
        if choice == "1":
            main()
        elif choice == "2":
            test_individual_functions()
        elif choice == "3":
            main()
            test_individual_functions()
        else:
            print("Opção inválida. Executando análise completa...")
            main()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Análise interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro na execução principal: {str(e)}")
        print(f"❌ Erro geral: {str(e)}")
