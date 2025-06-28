#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv
from telegram_notifier import TelegramNotifier
from binance_simulator import BinanceSimulator
from strategy import SwingTradingStrategy
from config import Config

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robot-crypt")

# Obtém as credenciais das variáveis de ambiente
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

print(f"Usando token Telegram: {telegram_token}")
print(f"Usando chat ID: {telegram_chat_id}")

# Inicializa o notificador
notifier = TelegramNotifier(telegram_token, telegram_chat_id)

# Testa notificação básica
print("Enviando notificação de teste...")
notifier.notify_status("🤖 Teste de notificação do Robot-Crypt")

# Inicializa simulador e estratégia
config = Config()
binance = BinanceSimulator()
strategy = SwingTradingStrategy(config, binance)

# Testa análise de volume com notificação
print("Testando análise de volume...")
pairs = ["BTC/USDT", "ETH/USDT"]

for pair in pairs:
    print(f"Analisando {pair}...")
    
    # Notifica início da análise
    notifier.notify_status(f"🔎 Iniciando análise do par {pair}")
    
    # Analisa volume
    volume_data = strategy.analyze_volume(pair, notifier=notifier)
    
    if volume_data:
        print(f"Volume atual: {volume_data['current_volume']:.2f}")
        print(f"Volume médio: {volume_data['avg_volume']:.2f}")
        print(f"Aumento: {volume_data['volume_increase']:.2%}")
    else:
        print("Falha ao obter dados de volume")

print("Teste completo!")
