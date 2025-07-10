#!/usr/bin/env python3
"""
Script de demonstração para análise histórica da Binance.
Mostra como usar o HistoricalDataManager para analisar dados históricos
e tomar decisões de compra/venda baseadas em análise técnica.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.binance.client import BinanceClient
from api.binance.historical_data_manager import HistoricalDataManager
from core.logging_setup import logger


async def demo_single_symbol_analysis():
    """Demonstra análise de um símbolo específico."""
    print("🔍 ANÁLISE HISTÓRICA DE SÍMBOLO ÚNICO")
    print("=" * 50)
    
    # Inicializa o gerenciador
    manager = HistoricalDataManager()
    
    # Símbolo para análise
    symbol = "BTCUSDT"
    
    try:
        # Busca preço atual
        current_price_data = manager.client.get_ticker_price(symbol)
        current_price = float(current_price_data['price'])
        
        print(f"📊 Analisando {symbol}")
        print(f"💰 Preço atual: ${current_price:,.2f}")
        print()
        
        # Análise histórica de 24 meses
        print("🕐 Buscando dados históricos (24 meses)...")
        analysis = await manager.analyze_historical_vs_current(
            symbol=symbol,
            current_price=current_price,
            interval="1d",
            months_back=24
        )
        
        # Exibe resultados
        print(f"📈 ANÁLISE HISTÓRICA DE {symbol}")
        print(f"   Preço atual: ${analysis.current_price:,.2f}")
        print(f"   Média histórica: ${analysis.historical_avg:,.2f}")
        print(f"   Máximo histórico: ${analysis.historical_max:,.2f}")
        print(f"   Mínimo histórico: ${analysis.historical_min:,.2f}")
        print(f"   Tendência: {analysis.trend_direction}")
        print(f"   Volatilidade: {analysis.volatility:.2%}")
        print()
        
        # Níveis de suporte e resistência
        print("🎯 NÍVEIS TÉCNICOS:")
        if analysis.support_levels:
            print(f"   Suportes: {[f'${s:,.2f}' for s in analysis.support_levels]}")
        if analysis.resistance_levels:
            print(f"   Resistências: {[f'${r:,.2f}' for r in analysis.resistance_levels]}")
        print()
        
        # Recomendação
        print("🚀 RECOMENDAÇÃO:")
        print(f"   Ação: {analysis.recommendation}")
        print(f"   Confiança: {analysis.confidence_score:.1f}%")
        
        # Explicação da recomendação
        if analysis.recommendation == "COMPRAR":
            print("   💡 Fatores positivos detectados")
        elif analysis.recommendation == "VENDER":
            print("   ⚠️ Fatores negativos detectados")
        else:
            print("   🤔 Aguardar melhores condições")
        
        print()
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")


async def demo_multiple_symbols_analysis():
    """Demonstra análise de múltiplos símbolos."""
    print("🔍 ANÁLISE DE MÚLTIPLOS SÍMBOLOS")
    print("=" * 50)
    
    # Inicializa o gerenciador
    manager = HistoricalDataManager()
    
    # Símbolos para análise
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"]
    
    try:
        print(f"📊 Analisando {len(symbols)} símbolos...")
        print()
        
        # Gera resumo do mercado
        summary = await manager.get_market_summary(symbols)
        
        print(f"📈 RESUMO DO MERCADO - {summary['timestamp'][:19]}")
        print(f"🌍 Sentimento geral: {summary['market_sentiment'].upper()}")
        print()
        
        # Exibe análises individuais
        for symbol, data in summary['analyses'].items():
            if 'error' in data:
                print(f"❌ {symbol}: Erro - {data['error']}")
                continue
            
            print(f"🪙 {symbol}:")
            print(f"   Preço: ${data['current_price']:,.2f}")
            print(f"   Recomendação: {data['recommendation']}")
            print(f"   Confiança: {data['confidence']:.1f}%")
            print(f"   Tendência: {data['trend']}")
            print(f"   Volatilidade: {data['volatility']:.2%}")
            print()
        
        # Estatísticas gerais
        recommendations = [data.get('recommendation', 'ERRO') for data in summary['analyses'].values() if 'recommendation' in data]
        buy_count = recommendations.count('COMPRAR')
        sell_count = recommendations.count('VENDER')
        wait_count = recommendations.count('AGUARDAR')
        
        print("📊 ESTATÍSTICAS:")
        print(f"   Comprar: {buy_count} símbolos")
        print(f"   Vender: {sell_count} símbolos")
        print(f"   Aguardar: {wait_count} símbolos")
        print()
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")


async def demo_historical_data_fetch():
    """Demonstra busca de dados históricos."""
    print("🔍 BUSCA DE DADOS HISTÓRICOS")
    print("=" * 50)
    
    # Inicializa o gerenciador
    manager = HistoricalDataManager()
    
    symbol = "BTCUSDT"
    
    try:
        print(f"📊 Buscando histórico de {symbol}...")
        
        # Busca dados históricos
        historical_data = await manager.fetch_historical_data(
            symbol=symbol,
            interval="1d",
            months_back=12,  # 12 meses
            force_refresh=False  # Usa cache se disponível
        )
        
        print(f"📈 Dados coletados: {len(historical_data)} registros")
        print()
        
        # Mostra alguns pontos de dados
        print("📅 AMOSTRAS DE DADOS (últimos 5 dias):")
        for data in historical_data[-5:]:
            date = datetime.fromtimestamp(data['open_time'] / 1000)
            print(f"   {date.strftime('%Y-%m-%d')}: Open=${data['open']:,.2f}, High=${data['high']:,.2f}, Low=${data['low']:,.2f}, Close=${data['close']:,.2f}")
        
        print()
        
        # Estatísticas básicas
        prices = [float(d['close']) for d in historical_data]
        print("📊 ESTATÍSTICAS BÁSICAS:")
        print(f"   Preço médio: ${sum(prices) / len(prices):,.2f}")
        print(f"   Preço máximo: ${max(prices):,.2f}")
        print(f"   Preço mínimo: ${min(prices):,.2f}")
        print(f"   Variação: {((max(prices) - min(prices)) / min(prices)) * 100:.1f}%")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {str(e)}")


async def demo_trend_analysis():
    """Demonstra análise de tendência."""
    print("🔍 ANÁLISE DE TENDÊNCIA")
    print("=" * 50)
    
    # Inicializa o gerenciador
    manager = HistoricalDataManager()
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    try:
        for symbol in symbols:
            print(f"📊 Analisando tendência de {symbol}...")
            
            # Busca preço atual
            current_price_data = manager.client.get_ticker_price(symbol)
            current_price = float(current_price_data['price'])
            
            # Análise de diferentes períodos
            periods = [
                (3, "3 meses"),
                (6, "6 meses"),
                (12, "12 meses"),
                (24, "24 meses")
            ]
            
            for months, period_name in periods:
                try:
                    analysis = await manager.analyze_historical_vs_current(
                        symbol=symbol,
                        current_price=current_price,
                        interval="1d",
                        months_back=months
                    )
                    
                    print(f"   {period_name}: {analysis.trend_direction} (Confiança: {analysis.confidence_score:.1f}%)")
                    
                except Exception as e:
                    print(f"   {period_name}: Erro - {str(e)}")
            
            print()
            
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")


async def demo_backtesting_opportunity():
    """Demonstra oportunidade de backtesting."""
    print("🔍 OPORTUNIDADE DE BACKTESTING")
    print("=" * 50)
    
    # Inicializa o gerenciador
    manager = HistoricalDataManager()
    
    symbol = "BTCUSDT"
    
    try:
        print(f"📊 Simulando estratégia para {symbol}...")
        
        # Busca dados históricos
        historical_data = await manager.fetch_historical_data(
            symbol=symbol,
            interval="1d",
            months_back=12
        )
        
        # Simula estratégia simples: compra quando preço < média móvel 20, vende quando > média móvel 20
        buy_signals = []
        sell_signals = []
        
        for i in range(20, len(historical_data)):
            # Calcula média móvel de 20 dias
            ma20 = sum(float(d['close']) for d in historical_data[i-20:i]) / 20
            current_price = float(historical_data[i]['close'])
            prev_price = float(historical_data[i-1]['close'])
            prev_ma20 = sum(float(d['close']) for d in historical_data[i-21:i-1]) / 20
            
            # Sinal de compra: preço cruza acima da MA20
            if prev_price <= prev_ma20 and current_price > ma20:
                buy_signals.append({
                    'date': datetime.fromtimestamp(historical_data[i]['open_time'] / 1000),
                    'price': current_price,
                    'ma20': ma20
                })
            
            # Sinal de venda: preço cruza abaixo da MA20
            elif prev_price >= prev_ma20 and current_price < ma20:
                sell_signals.append({
                    'date': datetime.fromtimestamp(historical_data[i]['open_time'] / 1000),
                    'price': current_price,
                    'ma20': ma20
                })
        
        print(f"📈 Sinais de compra encontrados: {len(buy_signals)}")
        print(f"📉 Sinais de venda encontrados: {len(sell_signals)}")
        print()
        
        # Mostra últimos sinais
        if buy_signals:
            print("🔵 ÚLTIMOS SINAIS DE COMPRA:")
            for signal in buy_signals[-3:]:
                print(f"   {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:,.2f} (MA20: ${signal['ma20']:,.2f})")
        
        if sell_signals:
            print("🔴 ÚLTIMOS SINAIS DE VENDA:")
            for signal in sell_signals[-3:]:
                print(f"   {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:,.2f} (MA20: ${signal['ma20']:,.2f})")
        
        print()
        print("💡 Esta é uma estratégia básica. Você pode implementar estratégias mais complexas!")
        print()
        
    except Exception as e:
        print(f"❌ Erro no backtesting: {str(e)}")


async def main():
    """Função principal que executa todas as demonstrações."""
    print("🚀 DEMONSTRAÇÃO DE ANÁLISE HISTÓRICA DA BINANCE")
    print("=" * 60)
    print()
    
    # Lista de demonstrações
    demos = [
        ("Análise de Símbolo Único", demo_single_symbol_analysis),
        ("Busca de Dados Históricos", demo_historical_data_fetch),
        ("Análise de Múltiplos Símbolos", demo_multiple_symbols_analysis),
        ("Análise de Tendência", demo_trend_analysis),
        ("Oportunidade de Backtesting", demo_backtesting_opportunity),
    ]
    
    for i, (title, demo_func) in enumerate(demos, 1):
        print(f"📋 {i}. {title}")
        print()
        
        try:
            await demo_func()
        except Exception as e:
            print(f"❌ Erro na demonstração: {str(e)}")
        
        print("-" * 60)
        print()
        
        # Pausa entre demonstrações
        if i < len(demos):
            print("⏳ Aguardando 3 segundos...")
            await asyncio.sleep(3)
    
    print("✅ Demonstração concluída!")
    print()
    print("💡 PRÓXIMOS PASSOS:")
    print("   1. Integre esta análise no seu robô de trading")
    print("   2. Configure alertas baseados nas recomendações")
    print("   3. Implemente estratégias de backtesting")
    print("   4. Monitore o desempenho das decisões")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        sys.exit(1)
