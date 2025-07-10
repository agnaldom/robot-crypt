#!/usr/bin/env python3
"""
Script para integrar análise histórica com o robô de trading existente.
Demonstra como usar os dados históricos da Binance para melhorar as decisões de trading.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.binance.client import BinanceClient
from api.binance.historical_data_manager import HistoricalDataManager
from strategies.historical_enhanced_strategy import HistoricalEnhancedStrategy
from core.logging_setup import logger


class HistoricalTradingBot:
    """
    Bot de trading aprimorado com análise histórica.
    Integra dados históricos da Binance para tomar decisões mais informadas.
    """
    
    def __init__(self):
        """Inicializa o bot com análise histórica."""
        self.binance_client = BinanceClient()
        self.historical_manager = HistoricalDataManager(self.binance_client)
        self.strategy = HistoricalEnhancedStrategy(self.binance_client)
        
        # Símbolos para monitorar
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "DOTUSDT", "MATICUSDT", "LINKUSDT", "AVAXUSDT", "ATOMUSDT"
        ]
        
        # Configurações
        self.min_confidence = 75.0  # Confiança mínima para executar trades
        self.analysis_interval = 300  # Análise a cada 5 minutos
        self.report_interval = 3600  # Relatório a cada hora
        
        # Estado do bot
        self.running = False
        self.last_analysis = None
        self.last_report = None
        
    async def start(self):
        """Inicia o bot de trading."""
        print("🚀 Iniciando Bot de Trading com Análise Histórica")
        print("=" * 60)
        
        self.running = True
        
        try:
            # Inicialização
            await self.initialize_historical_data()
            
            # Loop principal
            while self.running:
                await self.run_analysis_cycle()
                await asyncio.sleep(60)  # Verifica a cada minuto
                
        except KeyboardInterrupt:
            print("\n👋 Bot interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro fatal: {str(e)}")
            logger.error(f"Erro fatal no bot: {str(e)}")
        finally:
            self.running = False
            print("🛑 Bot finalizado")
    
    async def initialize_historical_data(self):
        """Inicializa dados históricos para os símbolos principais."""
        print("📊 Inicializando dados históricos...")
        
        for symbol in self.symbols[:3]:  # Inicializa só os 3 primeiros para não demorar
            try:
                print(f"   Carregando histórico de {symbol}...")
                await self.historical_manager.fetch_historical_data(
                    symbol=symbol,
                    interval="1d",
                    months_back=12,
                    force_refresh=False
                )
                print(f"   ✅ {symbol} carregado")
                
            except Exception as e:
                print(f"   ❌ Erro ao carregar {symbol}: {str(e)}")
        
        print("✅ Inicialização concluída")
        print()
    
    async def run_analysis_cycle(self):
        """Executa um ciclo de análise."""
        current_time = datetime.now()
        
        # Análise de oportunidades
        if (self.last_analysis is None or 
            current_time - self.last_analysis > timedelta(seconds=self.analysis_interval)):
            
            await self.analyze_market_opportunities()
            self.last_analysis = current_time
        
        # Relatório detalhado
        if (self.last_report is None or 
            current_time - self.last_report > timedelta(seconds=self.report_interval)):
            
            await self.generate_detailed_report()
            self.last_report = current_time
    
    async def analyze_market_opportunities(self):
        """Analisa oportunidades de mercado."""
        print(f"🔍 Analisando oportunidades - {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # Escaneia oportunidades
            opportunities = await self.strategy.scan_market_opportunities(
                symbols=self.symbols,
                min_confidence=self.min_confidence
            )
            
            if opportunities:
                print(f"🎯 {len(opportunities)} oportunidades encontradas:")
                
                for i, signal in enumerate(opportunities[:5], 1):  # Mostra top 5
                    print(f"   {i}. {signal.symbol}: {signal.action}")
                    print(f"      Confiança: {signal.confidence:.1f}%")
                    print(f"      Preço: ${signal.current_price:,.2f}")
                    print(f"      Stop Loss: ${signal.stop_loss:,.2f}")
                    print(f"      Take Profit: ${signal.take_profit:,.2f}")
                    
                    # Mostra principal razão
                    if signal.reasoning:
                        print(f"      Razão: {signal.reasoning[0]}")
                    print()
                
                # Aqui você pode integrar com a execução real de trades
                # Por exemplo:
                # await self.execute_trades(opportunities)
                
            else:
                print("   Nenhuma oportunidade encontrada no momento")
            
        except Exception as e:
            print(f"❌ Erro na análise: {str(e)}")
            logger.error(f"Erro na análise de oportunidades: {str(e)}")
    
    async def generate_detailed_report(self):
        """Gera relatório detalhado do mercado."""
        print("📈 Gerando relatório detalhado...")
        
        try:
            report = await self.strategy.generate_market_report(self.symbols)
            
            # Salva relatório
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"market_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Mostra resumo
            summary = report['market_summary']
            print(f"📊 RESUMO DO MERCADO:")
            print(f"   Altista: {summary['bullish_count']} símbolos")
            print(f"   Baixista: {summary['bearish_count']} símbolos")
            print(f"   Neutro: {summary['neutral_count']} símbolos")
            print(f"   Confiança média: {summary['avg_confidence']:.1f}%")
            print(f"   Oportunidades: {len(report['opportunities'])}")
            print(f"   Relatório salvo: {report_file}")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {str(e)}")
            logger.error(f"Erro ao gerar relatório: {str(e)}")
    
    async def execute_trades(self, opportunities: List):
        """
        Executa trades baseados nas oportunidades.
        ATENÇÃO: Esta é uma versão simulada!
        """
        print("⚠️  SIMULAÇÃO DE EXECUÇÃO DE TRADES")
        print("    (Não executando trades reais)")
        
        for signal in opportunities[:3]:  # Executa apenas top 3
            print(f"   Simulando {signal.action} para {signal.symbol}")
            print(f"   Confiança: {signal.confidence:.1f}%")
            print(f"   Preço de entrada: ${signal.entry_price:,.2f}")
            
            # Aqui você integraria com a execução real:
            # if signal.action == "BUY":
            #     await self.execute_buy_order(signal)
            # elif signal.action == "SELL":
            #     await self.execute_sell_order(signal)
    
    async def execute_buy_order(self, signal):
        """Executa ordem de compra (exemplo)."""
        # Implementação exemplo - NÃO USE EM PRODUÇÃO SEM AJUSTES
        try:
            # Calcula quantidade baseada no risco
            risk_amount = 100.0  # $100 por trade
            quantity = risk_amount / signal.current_price
            
            # order = self.binance_client.create_order(
            #     symbol=signal.symbol,
            #     side='BUY',
            #     order_type='LIMIT',
            #     quantity=quantity,
            #     price=signal.entry_price
            # )
            
            print(f"✅ Ordem de compra simulada para {signal.symbol}")
            
        except Exception as e:
            print(f"❌ Erro ao executar compra: {str(e)}")
    
    async def execute_sell_order(self, signal):
        """Executa ordem de venda (exemplo)."""
        # Similar ao execute_buy_order
        print(f"✅ Ordem de venda simulada para {signal.symbol}")
    
    def stop(self):
        """Para o bot."""
        self.running = False


async def demo_integration():
    """Demonstra a integração completa."""
    print("🔧 DEMONSTRAÇÃO DE INTEGRAÇÃO")
    print("=" * 50)
    
    strategy = HistoricalEnhancedStrategy()
    
    # Teste com um símbolo
    symbol = "BTCUSDT"
    
    try:
        print(f"📊 Testando análise integrada para {symbol}...")
        
        # Análise com contexto histórico
        signal = await strategy.analyze_symbol_with_history(
            symbol=symbol,
            timeframe="1d",
            months_back=12
        )
        
        print(f"🎯 RESULTADO DA ANÁLISE:")
        print(f"   Símbolo: {signal.symbol}")
        print(f"   Ação: {signal.action}")
        print(f"   Confiança: {signal.confidence:.1f}%")
        print(f"   Preço atual: ${signal.current_price:,.2f}")
        print(f"   Entrada: ${signal.entry_price:,.2f}")
        print(f"   Stop Loss: ${signal.stop_loss:,.2f}")
        print(f"   Take Profit: ${signal.take_profit:,.2f}")
        print()
        
        print("📝 RACIOCÍNIO:")
        for i, reason in enumerate(signal.reasoning, 1):
            print(f"   {i}. {reason}")
        print()
        
        print("📊 CONTEXTO HISTÓRICO:")
        ctx = signal.historical_context
        print(f"   Preço médio histórico: ${ctx['avg_price']:,.2f}")
        print(f"   Máximo histórico: ${ctx['max_price']:,.2f}")
        print(f"   Mínimo histórico: ${ctx['min_price']:,.2f}")
        print(f"   Volatilidade: {ctx['volatility']:.2%}")
        print(f"   Tendência: {ctx['trend']}")
        print(f"   Variação vs média: {ctx['price_vs_avg_pct']:.1f}%")
        print()
        
        # Cálculo de risco/retorno
        if signal.action != "HOLD":
            potential_return = strategy._calculate_potential_return(signal)
            risk_reward = strategy._calculate_risk_reward_ratio(signal)
            
            print("💰 ANÁLISE DE RISCO/RETORNO:")
            print(f"   Retorno potencial: {potential_return:.2f}%")
            print(f"   Relação risco/retorno: 1:{risk_reward:.2f}")
            print()
        
        print("✅ Integração funcionando perfeitamente!")
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {str(e)}")


async def main():
    """Função principal."""
    print("🚀 INTEGRAÇÃO DE ANÁLISE HISTÓRICA COM ROBÔ DE TRADING")
    print("=" * 70)
    print()
    
    # Opções
    print("Escolha uma opção:")
    print("1. Demonstração de integração")
    print("2. Executar bot completo (simulação)")
    print("3. Análise única de símbolo")
    print()
    
    choice = input("Digite sua escolha (1-3): ").strip()
    
    if choice == "1":
        await demo_integration()
    
    elif choice == "2":
        print("⚠️  MODO SIMULAÇÃO - Nenhum trade real será executado")
        print()
        
        bot = HistoricalTradingBot()
        await bot.start()
    
    elif choice == "3":
        symbol = input("Digite o símbolo (ex: BTCUSDT): ").strip().upper()
        
        if symbol:
            strategy = HistoricalEnhancedStrategy()
            
            try:
                signal = await strategy.analyze_symbol_with_history(symbol)
                
                print(f"\n📊 ANÁLISE DE {symbol}:")
                print(f"   Recomendação: {signal.action}")
                print(f"   Confiança: {signal.confidence:.1f}%")
                print(f"   Preço atual: ${signal.current_price:,.2f}")
                
                if signal.reasoning:
                    print(f"   Principal razão: {signal.reasoning[0]}")
                
            except Exception as e:
                print(f"❌ Erro na análise: {str(e)}")
        else:
            print("❌ Símbolo não informado")
    
    else:
        print("❌ Opção inválida")
    
    print("\n" + "=" * 70)
    print("💡 PRÓXIMOS PASSOS PARA IMPLEMENTAÇÃO:")
    print("   1. Configure suas chaves da API Binance")
    print("   2. Ajuste os parâmetros de risco no código")
    print("   3. Teste em ambiente de simulação")
    print("   4. Implemente notificações (Telegram, email)")
    print("   5. Configure monitoramento 24/7")
    print("   6. Implemente gestão de risco avançada")
    print()
    print("⚠️  IMPORTANTE: Sempre teste em ambiente de simulação antes de usar com dinheiro real!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        sys.exit(1)
