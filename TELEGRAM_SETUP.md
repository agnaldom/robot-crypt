# 🤖 Guia de Configuração: Notificações Telegram

Este guia mostra como configurar as notificações do Telegram para o robot-crypt.

## 📋 Pré-requisitos

1. Uma conta no Telegram
2. Acesso ao bot @BotFather no Telegram
3. O projeto robot-crypt já instalado

## 🔧 Passo 1: Criar um Bot no Telegram

### 1.1 Abrir o BotFather
1. Abra o Telegram
2. Procure por `@BotFather`
3. Inicie uma conversa

### 1.2 Criar o Bot
1. Envie o comando: `/newbot`
2. Escolha um nome para o bot (ex: "Robot Crypt Notifications")
3. Escolha um username único (ex: "robot_crypt_notifications_bot")
4. **Guarde o token** que será fornecido (formato: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`)

### 1.3 Configurar o Bot (Opcional)
```
/setdescription - Define uma descrição para o bot
/setuserpic - Define uma foto de perfil
/setcommands - Define comandos do bot
```

## 🔑 Passo 2: Obter o Chat ID

### 2.1 Método 1: Usar o @userinfobot
1. Procure por `@userinfobot` no Telegram
2. Inicie uma conversa
3. Seu Chat ID será mostrado

### 2.2 Método 2: Usar a API do Telegram
1. Inicie uma conversa com seu bot
2. Envie qualquer mensagem
3. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
4. Procure pelo campo `"id"` dentro de `"chat"`

### 2.3 Método 3: Script Python
```python
import requests

def get_chat_id(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    data = response.json()
    
    if data['ok'] and data['result']:
        chat_id = data['result'][0]['message']['chat']['id']
        print(f"Seu Chat ID: {chat_id}")
        return chat_id
    else:
        print("Nenhuma mensagem encontrada. Envie uma mensagem para o bot primeiro.")
        return None

# Substitua pelo seu token
bot_token = "SEU_TOKEN_AQUI"
get_chat_id(bot_token)
```

## ⚙️ Passo 3: Configurar as Variáveis de Ambiente

### 3.1 Editar o arquivo .env
```bash
# === CONFIGURAÇÕES DE NOTIFICAÇÃO ===
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
TELEGRAM_CHAT_ID=123456789

# === CONFIGURAÇÕES AVANÇADAS (OPCIONAL) ===
TELEGRAM_AUDIT_CHAT_ID=123456789      # Chat para logs de auditoria
TELEGRAM_ALERTS_CHAT_ID=123456789     # Chat para alertas críticos
TELEGRAM_REPORTS_CHAT_ID=123456789    # Chat para relatórios
```

### 3.2 Verificar configurações
```bash
# Verificar se as variáveis foram carregadas
python -c "import os; print('Token:', os.getenv('TELEGRAM_BOT_TOKEN', 'NÃO CONFIGURADO')); print('Chat ID:', os.getenv('TELEGRAM_CHAT_ID', 'NÃO CONFIGURADO'))"
```

## 🧪 Passo 4: Testar as Notificações

### 4.1 Teste básico
```python
# Criar arquivo: test_telegram.py
import os
import sys
sys.path.append('.')

from src.notifications.telegram_notifier import TelegramNotifier

# Obter configurações
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    print("❌ Configurações do Telegram não encontradas!")
    print("Verifique se TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID estão definidos no .env")
    sys.exit(1)

# Criar notificador
notifier = TelegramNotifier(bot_token, chat_id)

# Teste de mensagem simples
print("📤 Enviando mensagem de teste...")
success = notifier.send_message("🤖 Robot-Crypt: Teste de configuração realizado com sucesso!")

if success:
    print("✅ Mensagem enviada com sucesso!")
else:
    print("❌ Erro ao enviar mensagem")
```

### 4.2 Executar o teste
```bash
python test_telegram.py
```

### 4.3 Teste de notificação de trade
```python
# Criar arquivo: test_telegram_trade.py
import os
import sys
sys.path.append('.')

from src.notifications.telegram_notifier import TelegramNotifier

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

notifier = TelegramNotifier(bot_token, chat_id)

# Teste de notificação de trade
trade_data = {
    'symbol': 'BTC/USDT',
    'side': 'BUY',
    'price': 43250.50,
    'quantity': 0.001,
    'profit_loss': 2.5,
    'strategy': 'Enhanced Strategy',
    'reason': 'Rompimento de resistência com volume alto',
    'indicators': {
        'RSI': 35.2,
        'MACD': 'Bullish',
        'Volume': 'Alto'
    },
    'risk_reward_ratio': '1:3'
}

print("📤 Enviando notificação de trade...")
success = notifier.notify_trade("COMPRA de BTC/USDT", "Trade executado com sucesso", trade_data)

if success:
    print("✅ Notificação de trade enviada!")
else:
    print("❌ Erro ao enviar notificação de trade")
```

## 📊 Passo 5: Configurar Tipos de Notificação

### 5.1 Notificações de Trade
```python
# Exemplo de uso no código
from src.services.telegram import get_telegram_service

telegram = get_telegram_service()

# Enviar notificação de trade
await telegram.send_trade_notification({
    'symbol': 'BTC/USDT',
    'side': 'BUY',
    'price': 43250.50,
    'quantity': 0.001,
    'reason': 'Sinal de compra forte',
    'strategy': 'Enhanced Strategy'
})
```

### 5.2 Alertas de Erro
```python
# Enviar alerta de erro
await telegram.send_error_alert(
    error_message="Erro na conexão com a API",
    component="Binance API",
    traceback="Stack trace completo..."
)
```

### 5.3 Alertas de Mercado
```python
# Enviar alerta de mercado
await telegram.send_market_alert(
    symbol="BTC/USDT",
    alert_type="breakout",
    message="Rompimento de resistência detectado",
    market_data={'price': 43250.50, 'volume': 'Alto'}
)
```

### 5.4 Resumo de Performance
```python
# Enviar resumo de performance
await telegram.send_performance_summary({
    'initial_capital': 1000.0,
    'current_capital': 1150.0,
    'total_trades': 25,
    'profit_trades': 18,
    'loss_trades': 7,
    'additional_metrics': {
        'Sharpe Ratio': 1.85,
        'Drawdown Máximo': -5.2
    }
})
```

## 🔒 Passo 6: Configurações de Segurança

### 6.1 Configurar Multiple Chats (Opcional)
```bash
# No arquivo .env
TELEGRAM_CHAT_ID=123456789              # Chat principal
TELEGRAM_AUDIT_CHAT_ID=987654321        # Chat para auditoria
TELEGRAM_ALERTS_CHAT_ID=555666777       # Chat para alertas críticos
TELEGRAM_REPORTS_CHAT_ID=444555666      # Chat para relatórios
```

### 6.2 Configurar Permissões do Bot
1. Acesse o @BotFather
2. Use `/mybots`
3. Selecione seu bot
4. Configure:
   - `Bot Settings` → `Group Privacy` → `Turn off`
   - `Bot Settings` → `Allow Groups` → `Turn on`

## 🚀 Passo 7: Integrar com o Sistema

### 7.1 Verificar integração no main.py
```python
# No arquivo principal do sistema
from src.core.config import settings

# Verificar se as notificações estão habilitadas
if settings.notifications_enabled:
    print("✅ Notificações Telegram habilitadas")
else:
    print("❌ Notificações Telegram desabilitadas")
    print("Verifique TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
```

### 7.2 Usar o serviço simplificado
```python
# Usar funções de conveniência
from src.services.telegram import (
    send_trade_report,
    send_risk_alert,
    send_performance_summary,
    send_system_alert
)

# Exemplo de uso
await send_trade_report(trade_data)
await send_risk_alert("Stop Loss", "Stop loss acionado", "BTC/USDT", "high")
await send_system_alert("Sistema iniciado com sucesso", "info")
```

## 🔧 Passo 8: Troubleshooting

### 8.1 Problemas Comuns

**Erro: "Unauthorized"**
- Verifique se o token está correto
- Certifique-se de que não há espaços no token

**Erro: "Chat not found"**
- Verifique se o Chat ID está correto
- Certifique-se de que iniciou uma conversa com o bot

**Erro: "Bad Request"**
- Verifique se a mensagem não excede 4096 caracteres
- Certifique-se de que não há caracteres especiais problemáticos

### 8.2 Verificar logs
```bash
# Verificar logs do sistema
tail -f logs/robot_crypt.log | grep -i telegram
```

### 8.3 Testar conectividade
```bash
# Testar conectividade com a API do Telegram
curl -X GET "https://api.telegram.org/bot<SEU_TOKEN>/getMe"
```

## 📝 Exemplo de Configuração Completa

### Arquivo .env final:
```bash
# === CONFIGURAÇÕES DE NOTIFICAÇÃO ===
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
TELEGRAM_CHAT_ID=123456789

# === CONFIGURAÇÕES AVANÇADAS ===
TELEGRAM_AUDIT_CHAT_ID=123456789
TELEGRAM_ALERTS_CHAT_ID=123456789
TELEGRAM_REPORTS_CHAT_ID=123456789
```

### Script de teste completo:
```python
#!/usr/bin/env python3
"""
Script completo para testar configurações do Telegram
"""
import os
import sys
import asyncio
sys.path.append('.')

from src.services.telegram import get_telegram_service

async def test_telegram_setup():
    """Testa a configuração completa do Telegram"""
    
    # Verificar variáveis de ambiente
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Configurações do Telegram não encontradas!")
        return False
    
    # Obter serviço do Telegram
    telegram = get_telegram_service()
    
    if not telegram.is_available():
        print("❌ Serviço do Telegram não disponível!")
        return False
    
    print("✅ Serviço do Telegram disponível")
    
    # Testes sequenciais
    tests = [
        ("Mensagem simples", test_simple_message),
        ("Notificação de trade", test_trade_notification),
        ("Alerta de erro", test_error_alert),
        ("Alerta de mercado", test_market_alert),
        ("Status do sistema", test_system_status),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📤 Testando: {test_name}")
        try:
            success = await test_func(telegram)
            results.append(success)
            print(f"{'✅' if success else '❌'} {test_name}: {'OK' if success else 'FALHOU'}")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {str(e)}")
            results.append(False)
    
    # Resumo
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Resumo: {passed}/{total} testes passaram")
    
    return passed == total

async def test_simple_message(telegram):
    """Testa envio de mensagem simples"""
    return await telegram.send_message("🤖 Robot-Crypt: Teste de configuração!")

async def test_trade_notification(telegram):
    """Testa notificação de trade"""
    trade_data = {
        'symbol': 'BTC/USDT',
        'side': 'BUY',
        'price': 43250.50,
        'quantity': 0.001,
        'reason': 'Teste de configuração',
        'strategy': 'Test Strategy'
    }
    return await telegram.send_trade_notification(trade_data)

async def test_error_alert(telegram):
    """Testa alerta de erro"""
    return await telegram.send_error_alert(
        "Erro de teste",
        "Test Component",
        "Test traceback"
    )

async def test_market_alert(telegram):
    """Testa alerta de mercado"""
    return await telegram.send_market_alert(
        "BTC/USDT",
        "test",
        "Alerta de teste",
        {'price': 43250.50}
    )

async def test_system_status(telegram):
    """Testa notificação de status"""
    return await telegram.send_system_status(
        "Sistema funcionando corretamente",
        {'uptime': '10 minutos', 'memory': '128MB'},
        "success"
    )

if __name__ == "__main__":
    print("🚀 Iniciando teste completo das configurações do Telegram")
    success = asyncio.run(test_telegram_setup())
    
    if success:
        print("\n🎉 Todos os testes passaram! Configuração do Telegram OK!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique a configuração.")
        sys.exit(1)
```

## 🏁 Finalização

Após completar todos os passos:

1. ✅ Bot criado no Telegram
2. ✅ Token e Chat ID configurados
3. ✅ Variáveis de ambiente definidas
4. ✅ Testes executados com sucesso
5. ✅ Integração verificada

Seu robot-crypt agora está configurado para enviar notificações via Telegram! 🎉

## 📚 Recursos Adicionais

- [Documentação da API do Telegram](https://core.telegram.org/bots/api)
- [Guia do BotFather](https://core.telegram.org/bots#6-botfather)
- [Exemplos de uso no código](src/notifications/telegram_notifier.py)

---

**Dicas importantes:**
- Mantenha o token do bot em segurança
- Não compartilhe o token em repositórios públicos
- Use múltiplos chats para organizar diferentes tipos de notificação
- Teste regularmente as notificações para garantir funcionamento
