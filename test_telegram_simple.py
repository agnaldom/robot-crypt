#!/usr/bin/env python3

"""
Script simples para testar notificações do Telegram
"""
import requests
import logging
import sys
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Credenciais do bot Telegram das variáveis de ambiente
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_message(text):
    """Envia mensagem para o chat do Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    try:
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        logger.info(f"Enviando para URL: {url}")
        logger.info(f"Chat ID: {CHAT_ID}")
        logger.info(f"Mensagem: {text[:50]}")
        
        response = requests.post(url, data=data)
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Resposta: {response.text[:100]}")
        
        if response.status_code == 200:
            logger.info("✅ Mensagem enviada com sucesso!")
            return True
        else:
            logger.error(f"❌ Falha ao enviar mensagem. Status: {response.status_code}")
            logger.error(f"Detalhes: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
        return False

if __name__ == "__main__":
    # Testa envio de mensagens
    logger.info("===== TESTE DE NOTIFICAÇÕES TELEGRAM =====")
    
    # Teste básico
    logger.info("Enviando mensagem simples...")
    send_message("🤖 Teste de mensagem do Robot-Crypt!")
    
    # Teste com formatação Markdown
    logger.info("Enviando mensagem com formatação...")
    send_message("*Análise de Volume:*\nPar: BTC/USDT\nAumento: +35%\nVolume Atual: 2450.32")
    
    # Teste com emojis
    logger.info("Enviando mensagem com emojis...")
    send_message("📊 *ANÁLISE - BTC/USDT*\n*Tipo*: Volume\nAumento de volume: 35%\nVolume atual: 2450.32\nVolume médio: 1800.50")
    
    logger.info("===== TESTE CONCLUÍDO =====")
