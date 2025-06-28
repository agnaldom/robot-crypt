#!/usr/bin/env python3
"""
Script para criar arquivo .env para modo de simulação
"""
import os
from pathlib import Path

def create_simulation_env():
    """Cria arquivo .env configurado para simulação"""
    env_file = Path(".env")
    
    # Se o arquivo já existe, faz backup
    if env_file.exists():
        backup_file = Path(".env.backup")
        with open(env_file, "r") as src, open(backup_file, "w") as dst:
            dst.write(src.read())
        print(f"Backup do arquivo .env criado em .env.backup")
    
    # Cria diretório de logs se não existir (útil para Docker)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("Diretório de logs verificado/criado")
    
    # Conteúdo do novo arquivo .env
    env_content = """# Arquivo .env configurado para MODO DE SIMULAÇÃO
# Não são necessárias chaves reais da API

# Modo de simulação ativado
SIMULATION_MODE=true

# Modo testnet (ignorado em modo de simulação)
USE_TESTNET=true

# Credenciais (não utilizadas em modo de simulação)
BINANCE_API_KEY=
BINANCE_API_SECRET=
TESTNET_API_KEY=
TESTNET_API_SECRET=

# Configurações de notificação Telegram (opcional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Configurações de trading
TRADE_AMOUNT=100
TAKE_PROFIT_PERCENTAGE=2
STOP_LOSS_PERCENTAGE=0.5
MAX_HOLD_TIME=86400
ENTRY_DELAY=60
"""
    
    # Escreve o novo arquivo
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("Arquivo .env configurado para modo de simulação!")
    print("Execute o bot com 'python main.py' para iniciar a simulação")

if __name__ == "__main__":
    create_simulation_env()
