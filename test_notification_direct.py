#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Importa o notificador Telegram
from telegram_notifier import TelegramNotifier

# Configura o logging
logging.basicConfig(level=logging.INFO)

# Obtém as credenciais das variáveis de ambiente
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

print(f"Using token: {token}")
print(f"Using chat_id: {chat_id}")

# Create notifier
notifier = TelegramNotifier(token, chat_id)

# Send test message
print("Sending test status message...")
result = notifier.notify_status("🤖 Este é um teste do Robot-Crypt!")
print(f"Status message result: {result}")

print("Sending test trade message...")
result = notifier.notify_trade("🛒 COMPRA de BTCUSDT", "Preço: 40000.00\nQuantidade: 0.001")
print(f"Trade message result: {result}")

print("Test complete!")
