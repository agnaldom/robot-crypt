#!/bin/bash
# Script aprimorado para configurar o Robot-Crypt para execução com conta real na Binance

echo "========================================================="
echo "  Configuração Avançada para Conta Real no Robot-Crypt   "
echo "========================================================="
echo
echo "ATENÇÃO: Este script configura o bot para operar em AMBIENTE REAL"
echo "com DINHEIRO REAL na sua conta Binance."
echo
echo "Passos para obter as credenciais de produção:"
echo "1. Acesse: https://www.binance.com/pt-BR/my/settings/api-management"
echo "2. Faça login na sua conta Binance"
echo "3. Crie uma nova API Key com permissões de leitura e trading (NÃO PERMITA SAQUES)"
echo "4. Restrinja o acesso por IP para maior segurança (opcional, mas recomendado)"
echo "5. Copie a API Key e Secret Key geradas"
echo
echo "ATENÇÃO: Verifique se você testou adequadamente sua estratégia em:"
echo "1. Modo de simulação (usando setup_simulation.sh)"
echo "2. Modo TestNet (usando setup_testnet.sh)"
echo "antes de passar para produção!"
echo

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando um novo..."
    touch .env
else
    echo "Arquivo .env encontrado. Será feito backup antes de modificações."
    cp .env .env.backup.$(date +%Y%m%d-%H%M%S)
fi

# Confirmar decisão
read -p "Tem certeza que deseja configurar para PRODUÇÃO? (S/N): " confirmation
if [[ $confirmation != [Ss]* ]]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

# Lê os valores das chaves
read -p "API Key de PRODUÇÃO: " api_key
read -p "API Secret de PRODUÇÃO: " api_secret

# Checa se os valores foram fornecidos
if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
    echo "Erro: API Key e Secret são obrigatórios para produção."
    exit 1
fi

# Configuração de notificações Telegram (opcional)
echo
echo "Configuração de Notificações Telegram (opcional)"
echo "-------------------------------------------"
echo "As notificações Telegram permitem acompanhar o bot remotamente."
echo "Deixe em branco para pular esta etapa."
echo
read -p "Telegram Bot Token: " telegram_token
read -p "Telegram Chat ID: " telegram_chat_id

# Configuração de moeda principal
echo
echo "Configuração de Moeda Principal"
echo "--------------------------"
echo "Escolha a moeda principal para operações:"
echo "1) BNB (Recomendado para economizar taxas)"
echo "2) USDT (Maior estabilidade e diversidade de pares)"
echo "3) BRL (Operações em Real)"
read -p "Escolha (1-3): " primary_coin_choice

case $primary_coin_choice in
    1) primary_coin="BNB" ;;
    2) primary_coin="USDT" ;;
    3) primary_coin="BRL" ;;
    *) primary_coin="BNB" ;;
esac

# Configuração de pares de trading
echo
echo "Configuração de Pares de Trading"
echo "--------------------------"

case $primary_coin in
    "BNB")
        default_pairs="BNBBTC,BNBUSDT,BNBETH"
        echo "Pares recomendados para BNB: BNBBTC,BNBUSDT,BNBETH"
        ;;
    "USDT")
        default_pairs="BTCUSDT,ETHUSDT,BNBUSDT,DOGEUSDT,XRPUSDT,MATICUSDT"
        echo "Pares recomendados para USDT: BTCUSDT,ETHUSDT,BNBUSDT,DOGEUSDT,XRPUSDT,MATICUSDT"
        ;;
    "BRL")
        default_pairs="BTCBRL,ETHBRL,BNBBRL,USDTBRL"
        echo "Pares recomendados para BRL: BTCBRL,ETHBRL,BNBBRL,USDTBRL"
        ;;
esac

read -p "Pares de trading (separados por vírgula) [$default_pairs]: " trading_pairs
trading_pairs=${trading_pairs:-$default_pairs}

# Configuração de parâmetros de trading
echo
echo "Configuração de Parâmetros de Trading"
echo "---------------------------------"
echo "Configure seus parâmetros de trading (pressione ENTER para usar valor padrão):"
echo

read -p "Valor por operação (em $primary_coin) [0.01 para BNB, 10 para USDT, 50 para BRL]: " trade_amount
if [ -z "$trade_amount" ]; then
    case $primary_coin in
        "BNB") trade_amount="0.01" ;;
        "USDT") trade_amount="10" ;;
        "BRL") trade_amount="50" ;;
    esac
fi

read -p "Take Profit (%) [1.5]: " take_profit
take_profit=${take_profit:-1.5}

read -p "Stop Loss (%) [0.8]: " stop_loss
stop_loss=${stop_loss:-0.8}

read -p "Tempo máximo de retenção (horas) [48]: " max_hold_time
max_hold_time=${max_hold_time:-48}

read -p "Intervalo de verificação (segundos) [300]: " check_interval
check_interval=${check_interval:-300}

read -p "Delay de entrada (segundos) [60]: " entry_delay
entry_delay=${entry_delay:-60}

# Atualizar arquivo .env
echo
echo "Atualizando arquivo .env..."

# Criando o arquivo do zero para garantir consistência
cat > .env << EOL
# Configuração do Robot-Crypt para conta REAL
# Gerado em $(date)

# Credenciais da API Binance
BINANCE_API_KEY=$api_key
BINANCE_API_SECRET=$api_secret

# Configuração do ambiente
SIMULATION_MODE=false
USE_TESTNET=false

# Configurações do Telegram (opcional)
TELEGRAM_BOT_TOKEN=$telegram_token
TELEGRAM_CHAT_ID=$telegram_chat_id

# Configurações de trading
TRADE_AMOUNT=$trade_amount
TAKE_PROFIT_PERCENTAGE=$take_profit
STOP_LOSS_PERCENTAGE=$stop_loss
MAX_HOLD_TIME=$max_hold_time
CHECK_INTERVAL=$check_interval
ENTRY_DELAY=$entry_delay

# Configurações de moedas
PRIMARY_COIN=$primary_coin
TRADING_PAIRS=$trading_pairs
EOL

echo
echo "========================================================"
echo "  CONFIGURAÇÃO PARA CONTA REAL CONCLUÍDA COM SUCESSO!   "
echo "========================================================"
echo
echo "O Robot-Crypt agora está configurado para operar em AMBIENTE REAL com a moeda $primary_coin"
echo "e os seguintes pares: $trading_pairs"
echo
echo "Para iniciar o bot, execute:"
echo "python main.py"
echo
echo "Para monitorar os logs em tempo real:"
echo "tail -f logs/robot-crypt-\$(date +%Y%m%d).log"
echo
echo "ATENÇÃO: Monitore cuidadosamente as operações iniciais."
echo "Para mais informações sobre monitoramento, consulte docs/MONITORAMENTO.md"
echo
