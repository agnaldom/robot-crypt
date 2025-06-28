#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()
print("DEBUG ENV VARS:")
print(f"TELEGRAM_BOT_TOKEN = '{os.environ.get('TELEGRAM_BOT_TOKEN')}'")
print(f"TELEGRAM_CHAT_ID = '{os.environ.get('TELEGRAM_CHAT_ID')}'")
