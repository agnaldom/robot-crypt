#!/usr/bin/env python3
"""
Demonstração das Funcionalidades de IA do Robot-Crypt
Script para testar e demonstrar as novas capacidades de IA
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.ai import (
    LLMNewsAnalyzer, 
    HybridPricePredictor, 
    AIStrategyGenerator,
    TradingAssistant,
    AdvancedPatternDetector
)
from src.ai.news_analyzer import CryptoNewsItem
from src.ai.llm_client import get_llm_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_llm_client():
    """Demonstra o cliente LLM unificado"""
    print("\n🤖 DEMONSTRAÇÃO: Cliente LLM Unificado")
    print("=" * 60)
    
    try:
        client = get_llm_client()
        
        # Health check
        health = await client.health_check()
        print(f"📊 Status do Cliente: {health['status']}")
        print(f"🔧 Provedor: {health['provider']}")
        print(f"🎯 Modelo: {health['model']}")
        print(f"📱 OpenAI Disponível: {health['openai_available']}")
        print(f"🌟 Gemini Disponível: {health['gemini_available']}")
        
        # Teste simples
        if health['status'] == 'healthy':
            print("\n🧪 Testando análise simples...")
            response = await client.chat(
                "What are the current trends in cryptocurrency markets? Respond briefly.",
                temperature=0.7,
                max_tokens=150
            )
            print(f"💭 Resposta: {response.content[:200]}...")
            print(f"💰 Custo estimado: ${response.cost_estimate:.6f}")
            print(f"🔢 Tokens usados: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no cliente LLM: {e}")
        return False


async def demo_news_analyzer():
    """Demonstra o analisador de notícias"""
    print("\n📰 DEMONSTRAÇÃO: Analisador de Notícias com IA")
    print("=" * 60)
    
    try:
        analyzer = LLMNewsAnalyzer()
        
        # Cria notícias de exemplo
        sample_news = [
            CryptoNewsItem(
                title="Bitcoin Surges to New Monthly High as Institutional Adoption Grows",
                content="Bitcoin has reached a new monthly high following increased institutional adoption...",
                source="CryptoDaily",
                published_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["BTC", "BITCOIN"]
            ),
            CryptoNewsItem(
                title="Ethereum 2.0 Staking Rewards Attract More Validators",
                content="The Ethereum network continues to see growth in validator participation...",
                source="BlockNews",
                published_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["ETH", "ETHEREUM"]
            ),
            CryptoNewsItem(
                title="Regulatory Clarity Brings Optimism to Crypto Markets",
                content="New regulatory frameworks provide much-needed clarity for crypto institutions...",
                source="CoinDesk",
                published_at=datetime.now() - timedelta(minutes=30),
                symbols_mentioned=["BTC", "ETH", "CRYPTO"]
            )
        ]
        
        print(f"📄 Analisando {len(sample_news)} notícias...")
        
        # Análise geral
        analysis = await analyzer.analyze_crypto_news(sample_news)
        
        print("\n📊 RESULTADO DA ANÁLISE:")
        print(f"   📈 Sentimento: {analysis.sentiment_label} (score: {analysis.sentiment_score:.2f})")
        print(f"   🎯 Confiança: {analysis.confidence:.2%}")
        print(f"   💥 Impacto: {analysis.impact_level}")
        print(f"   🔮 Predição: {analysis.price_prediction}")
        print(f"   🧠 Reasoning: {analysis.reasoning[:150]}...")
        
        if analysis.key_events:
            print(f"   🔑 Eventos importantes:")
            for event in analysis.key_events[:3]:
                print(f"      • {event}")
        
        # Análise específica de Bitcoin
        print(f"\n🔍 Análise específica para Bitcoin:")
        btc_analysis = await analyzer.analyze_crypto_news(sample_news, symbol="BTC")
        print(f"   📈 Sentimento BTC: {btc_analysis.sentiment_label} ({btc_analysis.sentiment_score:.2f})")
        print(f"   🎯 Confiança: {btc_analysis.confidence:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no analisador de notícias: {e}")
        return False


async def demo_hybrid_predictor():
    """Demonstra o preditor híbrido"""
    print("\n🔮 DEMONSTRAÇÃO: Preditor Híbrido (ML + LLM)")
    print("=" * 60)
    
    try:
        predictor = HybridPricePredictor()
        
        # Dados técnicos simulados
        technical_data = {
            "rsi": 45.2,
            "macd": 0.15,
            "bb_upper": 43500.0,
            "bb_lower": 42000.0,
            "current_price": 42750.0,
            "volume_ratio": 1.3,
            "sma_20": 42300.0,
            "ema_50": 42100.0
        }
        
        # Notícias contextuais
        news_context = """
        Recent news: Bitcoin institutional adoption continues with major investment firms 
        allocating portions of their portfolios to cryptocurrency. Technical indicators 
        show consolidation above key support levels.
        """
        
        print("🔍 Dados de entrada:")
        print(f"   📊 RSI: {technical_data['rsi']}")
        print(f"   📈 MACD: {technical_data['macd']}")
        print(f"   💰 Preço atual: ${technical_data['current_price']:,.2f}")
        print(f"   📊 Volume: {technical_data['volume_ratio']:.1f}x da média")
        
        print("\n⚙️ Executando predição híbrida...")
        
        prediction = await predictor.predict_price_movement(
            symbol="BTCUSDT",
            technical_data=technical_data,
            news_data=news_context
        )
        
        print("\n🎯 RESULTADO DA PREDIÇÃO:")
        print(f"   📊 Direção: {prediction['direction'].upper()}")
        print(f"   🎯 Confiança: {prediction['confidence']:.2%}")
        print(f"   💡 Estratégia: {prediction['strategy']}")
        print(f"   🧠 Reasoning: {prediction['reasoning'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no preditor híbrido: {e}")
        return False


async def demo_strategy_generator():
    """Demonstra o gerador de estratégias"""
    print("\n🎲 DEMONSTRAÇÃO: Gerador de Estratégias com IA")
    print("=" * 60)
    
    try:
        generator = AIStrategyGenerator()
        
        # Condições de mercado simuladas
        market_conditions = {
            "volatility": 15.5,  # %
            "trend": "bullish",
            "volume": "high",
            "support_level": 42000,
            "resistance_level": 45000
        }
        
        # Preferências do usuário
        user_preferences = {
            "risk_tolerance": "medium",
            "capital": 1000,  # USD
            "timeframe": "4h",
            "max_drawdown": 5  # %
        }
        
        print("📊 Condições de mercado:")
        for key, value in market_conditions.items():
            print(f"   {key}: {value}")
        
        print(f"\n👤 Preferências do usuário:")
        for key, value in user_preferences.items():
            print(f"   {key}: {value}")
        
        print(f"\n⚙️ Gerando estratégia personalizada...")
        
        strategy = await generator.generate_custom_strategy(
            market_conditions=market_conditions,
            user_preferences=user_preferences
        )
        
        if "error" not in strategy:
            print(f"\n🎯 ESTRATÉGIA GERADA:")
            for key, value in strategy.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Erro na geração: {strategy['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no gerador de estratégias: {e}")
        return False


async def demo_trading_assistant():
    """Demonstra o assistente de trading"""
    print("\n🤝 DEMONSTRAÇÃO: Assistente de Trading")
    print("=" * 60)
    
    try:
        assistant = TradingAssistant()
        
        # Portfolio simulado
        current_portfolio = {
            "BTC": {"amount": 0.5, "usd_value": 21375.0},
            "ETH": {"amount": 2.0, "usd_value": 4800.0},
            "USDT": {"amount": 5000.0, "usd_value": 5000.0}
        }
        
        print("💼 Portfolio atual:")
        total_value = sum(asset["usd_value"] for asset in current_portfolio.values())
        for symbol, data in current_portfolio.items():
            percentage = (data["usd_value"] / total_value) * 100
            print(f"   {symbol}: ${data['usd_value']:,.2f} ({percentage:.1f}%)")
        print(f"   Total: ${total_value:,.2f}")
        
        # Perguntas de exemplo
        questions = [
            "Should I rebalance my portfolio given current market conditions?",
            "What's your opinion on the current Bitcoin trend?",
            "Are there any risk factors I should be aware of?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Pergunta {i}: {question}")
            
            response = await assistant.chat_analysis(
                user_question=question,
                current_portfolio=current_portfolio
            )
            
            if "error" not in response:
                print(f"💭 Insights: {response.get('insights', 'N/A')[:200]}...")
                print(f"⚠️ Risco: {response.get('risk_assessment', 'N/A')[:100]}...")
                if response.get('recommendations'):
                    print(f"💡 Recomendações:")
                    for rec in response['recommendations'][:2]:
                        print(f"   • {rec}")
            else:
                print(f"❌ Erro: {response['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no assistente de trading: {e}")
        return False


async def demo_pattern_detector():
    """Demonstra o detector de padrões"""
    print("\n📊 DEMONSTRAÇÃO: Detector de Padrões Avançados")
    print("=" * 60)
    
    try:
        detector = AdvancedPatternDetector()
        
        # Dados de preço simulados (OHLCV)
        base_price = 42500
        price_data = []
        
        for i in range(50):
            # Simula movimento de preço com tendência e ruído
            trend = i * 0.5
            noise = (i % 7 - 3) * 20
            price = base_price + trend + noise
            
            price_data.append({
                "timestamp": (datetime.now() - timedelta(hours=50-i)).isoformat(),
                "open": price - 10,
                "high": price + 15,
                "low": price - 25,
                "close": price,
                "volume": 1000000 + (i % 3) * 200000
            })
        
        # Dados de volume
        volume_data = [{"volume": p["volume"]} for p in price_data]
        
        print(f"📈 Analisando {len(price_data)} períodos de dados...")
        print(f"💰 Faixa de preços: ${price_data[0]['close']:,.2f} - ${price_data[-1]['close']:,.2f}")
        
        # Detecta padrões complexos
        patterns = await detector.detect_complex_patterns(price_data, volume_data)
        
        print(f"\n🔍 PADRÕES DETECTADOS: {len(patterns)}")
        for i, pattern in enumerate(patterns[:3], 1):
            print(f"\n   📊 Padrão {i}: {pattern.get('name', 'Unknown')}")
            print(f"      📝 Descrição: {pattern.get('description', 'N/A')[:100]}...")
            print(f"      🎯 Confiança: {pattern.get('confidence', 0)}%")
            print(f"      📈 Direção: {pattern.get('direction', 'neutral')}")
            if pattern.get('target_levels'):
                print(f"      🎯 Alvos: {pattern['target_levels'][:2]}")
        
        # Análise de breakout
        print(f"\n🚀 ANÁLISE DE BREAKOUT:")
        breakout_analysis = await detector.analyze_breakout_probability(price_data, "BTCUSDT")
        
        print(f"   📊 Probabilidade: {breakout_analysis['breakout_probability']:.2%}")
        print(f"   📈 Direção: {breakout_analysis['direction']}")
        print(f"   🎯 Confiança: {breakout_analysis['confidence']:.2%}")
        print(f"   🧠 Reasoning: {breakout_analysis['reasoning'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no detector de padrões: {e}")
        return False


async def main():
    """Função principal da demonstração"""
    print("🚀 DEMONSTRAÇÃO DAS FUNCIONALIDADES DE IA - Robot-Crypt")
    print("=" * 80)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verifica se as chaves de API estão configuradas
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GOOGLE_AI_API_KEY")
    
    if not openai_key and not gemini_key:
        print("⚠️  AVISO: Nenhuma chave de API de IA foi encontrada!")
        print("   Configure pelo menos uma das seguintes variáveis de ambiente:")
        print("   - OPENAI_API_KEY (para OpenAI GPT)")
        print("   - GOOGLE_AI_API_KEY (para Google Gemini)")
        print("   ")
        print("   As demonstrações irão falhar sem as chaves de API.")
        print()
        
        response = input("Deseja continuar mesmo assim? (y/N): ")
        if response.lower() != 'y':
            print("Demonstração cancelada.")
            return
    
    demos = [
        ("Cliente LLM", demo_llm_client),
        ("Analisador de Notícias", demo_news_analyzer),
        ("Preditor Híbrido", demo_hybrid_predictor),
        ("Gerador de Estratégias", demo_strategy_generator),
        ("Assistente de Trading", demo_trading_assistant),
        ("Detector de Padrões", demo_pattern_detector)
    ]
    
    results = {}
    
    for name, demo_func in demos:
        try:
            print(f"\n{'='*80}")
            success = await demo_func()
            results[name] = "✅ Sucesso" if success else "❌ Falhou"
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Demonstração interrompida pelo usuário")
            break
        except Exception as e:
            logger.error(f"Erro na demonstração {name}: {e}")
            results[name] = f"❌ Erro: {str(e)[:50]}..."
    
    # Sumário final
    print(f"\n{'='*80}")
    print("📋 SUMÁRIO DAS DEMONSTRAÇÕES")
    print("=" * 80)
    
    for name, result in results.items():
        print(f"   {result} {name}")
    
    success_count = sum(1 for r in results.values() if "✅" in r)
    total_count = len(results)
    
    print(f"\n🎯 Resultado: {success_count}/{total_count} demonstrações bem-sucedidas")
    
    if success_count == total_count:
        print("🎉 Todas as funcionalidades de IA estão funcionando!")
    elif success_count > 0:
        print("⚠️  Algumas funcionalidades precisam de atenção.")
    else:
        print("❌ Nenhuma funcionalidade de IA está funcionando. Verifique a configuração.")
    
    print(f"\n📚 Para usar essas funcionalidades no bot:")
    print(f"   1. Configure as chaves de API no arquivo .env")
    print(f"   2. As funcionalidades serão integradas automaticamente")
    print(f"   3. Verifique os logs para acompanhar a análise de IA")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\nDemonstração interrompida. Até logo! 👋")
    except Exception as e:
        logger.error(f"Erro fatal na demonstração: {e}")
        print(f"❌ Erro fatal: {e}")
