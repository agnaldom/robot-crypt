#!/bin/bash
# setup_real_account.sh - Script para configurar ambiente real para Robot-Crypt

echo "🚀 Robot-Crypt - Configuração de Conta Real 🚀"
echo "----------------------------------------------"
echo "Este script irá configurar o ambiente para operar com sua conta real da Binance."
echo "Por favor, tenha suas credenciais da API Binance em mãos."
echo ""

# Verifica se o .env já existe e faz backup se existir
if [ -f .env ]; then
    echo "⚠️  Arquivo .env existente encontrado. Fazendo backup..."
    cp .env .env.backup.$(date +"%Y%m%d_%H%M%S")
    echo "✅ Backup criado com sucesso!"
fi

# Solicita as credenciais da API
echo "📝 Digite sua API KEY da Binance:"
read -r API_KEY
echo "📝 Digite sua API SECRET da Binance:"
read -r API_SECRET

# Solicita configurações do Telegram (opcional)
echo "📱 Deseja configurar notificações por Telegram? (s/n)"
read -r USE_TELEGRAM

TELEGRAM_CONFIG=""
if [[ "$USE_TELEGRAM" == "s" || "$USE_TELEGRAM" == "S" ]]; then
    echo "📝 Digite seu TELEGRAM BOT TOKEN:"
    read -r TELEGRAM_TOKEN
    echo "📝 Digite seu TELEGRAM CHAT ID:"
    read -r TELEGRAM_CHAT_ID
    
    TELEGRAM_CONFIG="
# Configurações do Telegram
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID"
fi

# Solicita configurações de trading
echo "💹 Digite o valor em BNB por operação (recomendado: 0.01 para seu saldo atual):"
read -r TRADE_AMOUNT
echo "📈 Digite o alvo de lucro em porcentagem (recomendado: 1.5):"
read -r TAKE_PROFIT
echo "📉 Digite o limite de perda em porcentagem (recomendado: 0.8):"
read -r STOP_LOSS

# Cria o arquivo .env
cat > .env << EOL
# Credenciais da API Binance
BINANCE_API_KEY=$API_KEY
BINANCE_API_SECRET=$API_SECRET

# Configuração do ambiente
SIMULATION_MODE=false
USE_TESTNET=false
$TELEGRAM_CONFIG

# Configurações de trading
TRADE_AMOUNT=$TRADE_AMOUNT
TAKE_PROFIT_PERCENTAGE=$TAKE_PROFIT
STOP_LOSS_PERCENTAGE=$STOP_LOSS
MAX_HOLD_TIME=48
CHECK_INTERVAL=300

# Configurações de moedas
PRIMARY_COIN=BNB
EOL

echo ""
echo "✅ Configuração concluída com sucesso!"
echo "🚀 Para iniciar o bot, execute: python main.py"
echo ""
echo "⚠️  AVISO IMPORTANTE ⚠️"
echo "Este bot realizará operações reais na sua conta da Binance."
echo "Recomendo iniciar com valores pequenos até confirmar que está"
echo "funcionando conforme o esperado."
echo ""
echo "Bons trades! 💰"

# Torna o arquivo executável
chmod +x setup_real_account.sh
