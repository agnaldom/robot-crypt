#!/usr/bin/env python3
"""
Script completo para testar configurações do Telegram do robot-crypt

Este script testa todas as funcionalidades de notificação do Telegram:
- Mensagens simples
- Notificações de trade
- Alertas de erro
- Alertas de mercado
- Status do sistema
- Relatórios de análise

Uso:
    python scripts/test_telegram.py
    python scripts/test_telegram.py --quick     # Apenas teste básico
    python scripts/test_telegram.py --full      # Todos os testes
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

def check_requirements():
    """Verifica se os módulos necessários estão disponíveis"""
    try:
        import requests
        from dotenv import load_dotenv
        return True
    except ImportError as e:
        print(f"❌ Módulo necessário não encontrado: {e}")
        print("📦 Instale os requisitos: pip install requests python-dotenv")
        return False

def load_config():
    """Carrega configurações do arquivo .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        return bot_token, chat_id
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return None, None

def test_basic_connectivity(bot_token):
    """Testa conectividade básica com a API do Telegram"""
    try:
        import requests
        
        print("🔍 Testando conectividade com API do Telegram...")
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Conectividade OK - Bot: @{bot_info.get('username', 'N/A')}")
            return True
        else:
            print(f"❌ Erro na API: {data.get('description', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False

async def test_telegram_notifier(bot_token, chat_id):
    """Testa o TelegramNotifier diretamente"""
    try:
        from src.notifications.telegram_notifier import TelegramNotifier
        
        print("🔍 Testando TelegramNotifier...")
        notifier = TelegramNotifier(bot_token, chat_id)
        
        # Teste de mensagem simples
        success = notifier.send_message("🤖 Robot-Crypt: Teste do TelegramNotifier")
        
        if success:
            print("✅ TelegramNotifier: OK")
            return True
        else:
            print("❌ TelegramNotifier: FALHOU")
            return False
            
    except ImportError:
        print("❌ TelegramNotifier não encontrado - verifique o módulo src.notifications.telegram_notifier")
        return False
    except Exception as e:
        print(f"❌ Erro no TelegramNotifier: {e}")
        return False

async def test_telegram_service():
    """Testa o TelegramService"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando TelegramService...")
        telegram = get_telegram_service()
        
        if not telegram.is_available():
            print("❌ TelegramService não disponível")
            return False
        
        # Teste de mensagem simples
        success = await telegram.send_message("🤖 Robot-Crypt: Teste do TelegramService")
        
        if success:
            print("✅ TelegramService: OK")
            return True
        else:
            print("❌ TelegramService: FALHOU")
            return False
            
    except ImportError:
        print("❌ TelegramService não encontrado - verifique o módulo src.services.telegram")
        return False
    except Exception as e:
        print(f"❌ Erro no TelegramService: {e}")
        return False

async def test_trade_notification():
    """Testa notificação de trade"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando notificação de trade...")
        telegram = get_telegram_service()
        
        trade_data = {
            'symbol': 'BTC/USDT',
            'side': 'BUY',
            'price': 43250.50,
            'quantity': 0.001,
            'profit_loss': 2.5,
            'strategy': 'Test Strategy',
            'reason': 'Teste de configuração do sistema',
            'indicators': {
                'RSI': 35.2,
                'MACD': 'Bullish',
                'Volume': 'Alto'
            },
            'risk_reward_ratio': '1:3'
        }
        
        success = await telegram.send_trade_notification(trade_data)
        
        if success:
            print("✅ Notificação de trade: OK")
            return True
        else:
            print("❌ Notificação de trade: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro na notificação de trade: {e}")
        return False

async def test_error_alert():
    """Testa alerta de erro"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando alerta de erro...")
        telegram = get_telegram_service()
        
        success = await telegram.send_error_alert(
            error_message="Erro de teste do sistema",
            component="Test Component",
            traceback="Traceback de teste:\n  File test.py, line 1\n    test_error()\nTestError: Erro simulado"
        )
        
        if success:
            print("✅ Alerta de erro: OK")
            return True
        else:
            print("❌ Alerta de erro: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro no alerta de erro: {e}")
        return False

async def test_market_alert():
    """Testa alerta de mercado"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando alerta de mercado...")
        telegram = get_telegram_service()
        
        market_data = {
            'price': 43250.50,
            'volume': 'Alto',
            'resistance': 43500.00,
            'support': 43000.00,
            'action_levels': {
                'entry': 43200.00,
                'take_profit': 44000.00,
                'stop_loss': 42800.00
            }
        }
        
        success = await telegram.send_market_alert(
            symbol="BTC/USDT",
            alert_type="breakout",
            message="Rompimento de resistência detectado em teste",
            market_data=market_data
        )
        
        if success:
            print("✅ Alerta de mercado: OK")
            return True
        else:
            print("❌ Alerta de mercado: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro no alerta de mercado: {e}")
        return False

async def test_system_status():
    """Testa notificação de status do sistema"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando status do sistema...")
        telegram = get_telegram_service()
        
        status_details = {
            'uptime': '10 minutos',
            'memory': '128MB',
            'cpu': '15%',
            'operações': 5,
            'conexão': 'Estável'
        }
        
        success = await telegram.send_system_status(
            status_message="Sistema funcionando corretamente - Teste de configuração",
            details=status_details,
            status_type="success"
        )
        
        if success:
            print("✅ Status do sistema: OK")
            return True
        else:
            print("❌ Status do sistema: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro no status do sistema: {e}")
        return False

async def test_performance_summary():
    """Testa resumo de performance"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando resumo de performance...")
        telegram = get_telegram_service()
        
        performance_data = {
            'initial_capital': 1000.0,
            'current_capital': 1150.0,
            'total_trades': 25,
            'profit_trades': 18,
            'loss_trades': 7,
            'additional_metrics': {
                'Sharpe Ratio': 1.85,
                'Drawdown Máximo': -5.2,
                'Tempo médio por trade': '45 minutos'
            }
        }
        
        success = await telegram.send_performance_summary(performance_data)
        
        if success:
            print("✅ Resumo de performance: OK")
            return True
        else:
            print("❌ Resumo de performance: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro no resumo de performance: {e}")
        return False

async def test_analysis_report():
    """Testa relatório de análise"""
    try:
        from src.services.telegram import get_telegram_service
        
        print("🔍 Testando relatório de análise...")
        telegram = get_telegram_service()
        
        analysis_data = {
            'signals': [
                {
                    'signal_type': 'BUY',
                    'confidence': 0.75,
                    'reasoning': 'RSI oversold + MACD bullish crossover'
                },
                {
                    'signal_type': 'BUY',
                    'confidence': 0.65,
                    'reasoning': 'Volume breakout confirmation'
                }
            ],
            'analysis_duration': 2.5,
            'traditional_analysis': {
                'should_trade': True,
                'action': 'buy',
                'price': 43250.50
            },
            'ai_analysis': {
                'signals': [{'signal_type': 'buy', 'confidence': 0.75}],
                'best_signal': {'signal_type': 'buy', 'confidence': 0.75},
                'total_signals': 2,
                'valid_signals': 2
            },
            'risk_assessment': {
                'overall_risk': 'medium',
                'risk_score': 0.4,
                'recommendations': ['Use stop loss', 'Monitor volume']
            },
            'market_sentiment': {
                'sentiment_score': 0.3,
                'sentiment_label': 'bullish',
                'confidence': 0.8,
                'reasoning': 'Positive market indicators'
            },
            'final_decision': {
                'should_trade': True,
                'action': 'buy',
                'reasoning': 'Strong bullish signals with manageable risk'
            }
        }
        
        success = await telegram.send_detailed_analysis_report(
            symbol="BTC/USDT",
            analysis_data=analysis_data,
            timeframe="1h"
        )
        
        if success:
            print("✅ Relatório de análise: OK")
            return True
        else:
            print("❌ Relatório de análise: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Erro no relatório de análise: {e}")
        return False

async def run_quick_tests():
    """Executa testes rápidos básicos"""
    print("🚀 Executando testes rápidos...")
    
    tests = [
        ("TelegramService", test_telegram_service),
        ("Notificação de trade", test_trade_notification),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📤 {test_name}...")
        try:
            success = await test_func()
            results.append(success)
            print(f"{'✅' if success else '❌'} {test_name}: {'OK' if success else 'FALHOU'}")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {str(e)}")
            results.append(False)
        
        # Pequena pausa entre testes
        await asyncio.sleep(1)
    
    return results

async def run_full_tests():
    """Executa todos os testes disponíveis"""
    print("🚀 Executando teste completo...")
    
    tests = [
        ("TelegramService", test_telegram_service),
        ("Notificação de trade", test_trade_notification),
        ("Alerta de erro", test_error_alert),
        ("Alerta de mercado", test_market_alert),
        ("Status do sistema", test_system_status),
        ("Resumo de performance", test_performance_summary),
        ("Relatório de análise", test_analysis_report),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📤 {test_name}...")
        try:
            success = await test_func()
            results.append(success)
            print(f"{'✅' if success else '❌'} {test_name}: {'OK' if success else 'FALHOU'}")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {str(e)}")
            results.append(False)
        
        # Pausa entre testes para evitar rate limiting
        await asyncio.sleep(2)
    
    return results

async def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Testa configurações do Telegram para robot-crypt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/test_telegram.py              # Teste padrão
  python scripts/test_telegram.py --quick      # Apenas testes básicos
  python scripts/test_telegram.py --full       # Todos os testes disponíveis
        """
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Executa apenas testes básicos e rápidos'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Executa todos os testes disponíveis'
    )
    
    args = parser.parse_args()
    
    print("🤖 Teste de Configurações do Telegram - Robot-Crypt")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)
    
    # Carregar configurações
    bot_token, chat_id = load_config()
    
    if not bot_token or not chat_id:
        print("❌ Configurações do Telegram não encontradas!")
        print("📝 Verifique se TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID estão definidos no .env")
        print("💡 Execute: python scripts/get_telegram_chat_id.py para obter o Chat ID")
        sys.exit(1)
    
    print(f"✅ Configurações carregadas:")
    print(f"   Token: ...{bot_token[-10:]}")  # Mostra apenas os últimos 10 caracteres
    print(f"   Chat ID: {chat_id}")
    print()
    
    # Teste de conectividade básica
    if not test_basic_connectivity(bot_token):
        print("❌ Falha na conectividade básica")
        sys.exit(1)
    
    print()
    print("=" * 60)
    
    # Executar testes
    if args.quick:
        results = await run_quick_tests()
    elif args.full:
        results = await run_full_tests()
    else:
        # Teste padrão (balanceado)
        print("🚀 Executando testes padrão...")
        
        tests = [
            ("TelegramService", test_telegram_service),
            ("Notificação de trade", test_trade_notification),
            ("Alerta de erro", test_error_alert),
            ("Status do sistema", test_system_status),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📤 {test_name}...")
            try:
                success = await test_func()
                results.append(success)
                print(f"{'✅' if success else '❌'} {test_name}: {'OK' if success else 'FALHOU'}")
            except Exception as e:
                print(f"❌ {test_name}: ERRO - {str(e)}")
                results.append(False)
            
            # Pausa entre testes
            await asyncio.sleep(1.5)
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"📊 RESUMO DOS TESTES:")
    print(f"   ✅ Passaram: {passed}")
    print(f"   ❌ Falharam: {total - passed}")
    print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
    print(f"   ⏰ Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Configuração do Telegram OK!")
        print("🚀 Seu robot-crypt está pronto para enviar notificações!")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} teste(s) falharam, mas as funcionalidades básicas estão OK")
        print("🔧 Verifique os erros acima para resolver problemas específicos")
    else:
        print("\n❌ Todos os testes falharam!")
        print("📝 Verifique a configuração do Telegram:")
        print("   1. Token do bot está correto?")
        print("   2. Chat ID está correto?")
        print("   3. Você enviou uma mensagem para o bot?")
        print("   4. Há conectividade com a internet?")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
