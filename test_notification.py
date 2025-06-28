#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from telegram_notifier import TelegramNotifier

# Load environment variables
load_dotenv()

# Get credentials from environment
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

print(f"Using token: {token}")
print(f"Using chat_id: {chat_id}")

# Create notifier
notifier = TelegramNotifier(token, chat_id)

# Send test message
print("Sending test status message...")
notifier.notify_status("🤖 Este é um teste do Robot-Crypt!")

print("Sending test trade message...")
notifier.notify_trade("🛒 COMPRA de BTCUSDT", "Preço: 40000.00\nQuantidade: 0.001")

print("Test complete!")
