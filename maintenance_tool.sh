#!/bin/bash
# Ferramenta de manutenção e diagnóstico para Robot-Crypt em operações reais

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}  Robot-Crypt: Ferramenta de Manutenção e Diagnóstico    ${NC}"
echo -e "${BLUE}=========================================================${NC}"
echo

# Função para verificar o estado do bot
check_bot_status() {
    echo -e "${YELLOW}Verificando o estado do bot...${NC}"
    
    # Verifica se o processo está rodando
    if pgrep -f "python main.py" > /dev/null; then
        echo -e "${GREEN}✓ Bot está rodando${NC}"
        # Mostrar PID e tempo de execução
        pid=$(pgrep -f "python main.py")
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            started=$(ps -p $pid -o lstart=)
            echo -e "  PID: $pid (iniciado em $started)"
        else
            # Linux
            started=$(ps -p $pid -o lstart=)
            echo -e "  PID: $pid (iniciado em $started)"
        fi
    else
        echo -e "${RED}✗ Bot não está rodando${NC}"
    fi
    echo
}

# Função para verificar logs recentes
check_recent_logs() {
    echo -e "${YELLOW}Verificando logs recentes...${NC}"
    
    # Verificar se diretório de logs existe
    if [ ! -d "logs" ]; then
        echo -e "${RED}Diretório de logs não encontrado${NC}"
        return
    fi
    
    # Encontrar log mais recente
    today=$(date +%Y%m%d)
    latest_log="logs/robot-crypt-$today.log"
    
    if [ ! -f "$latest_log" ]; then
        echo -e "${RED}Arquivo de log para hoje não encontrado${NC}"
        # Tenta encontrar o log mais recente
        latest_log=$(ls -t logs/robot-crypt-*.log 2>/dev/null | head -1)
        
        if [ -z "$latest_log" ]; then
            echo -e "${RED}Nenhum arquivo de log encontrado${NC}"
            return
        fi
        
        echo -e "${YELLOW}Usando log mais recente: $latest_log${NC}"
    fi
    
    echo -e "${GREEN}Log mais recente: $latest_log${NC}"
    
    # Mostrar últimas 10 linhas de log
    echo -e "${BLUE}Últimas entradas de log:${NC}"
    tail -n 10 "$latest_log"
    
    # Verificar erros recentes
    echo -e "\n${BLUE}Erros recentes:${NC}"
    errors=$(grep -i "error\|exception\|falha" "$latest_log" | tail -n 5)
    if [ -z "$errors" ]; then
        echo -e "${GREEN}Nenhum erro recente encontrado${NC}"
    else
        echo -e "${RED}$errors${NC}"
    fi
    
    # Verificar operações recentes
    echo -e "\n${BLUE}Operações recentes:${NC}"
    trades=$(grep -i "compra\|venda\|ordem\|posição\|executada" "$latest_log" | tail -n 5)
    if [ -z "$trades" ]; then
        echo -e "${YELLOW}Nenhuma operação recente encontrada${NC}"
    else
        echo "$trades"
    fi
    echo
}

# Função para verificar arquivo de estado
check_state_file() {
    echo -e "${YELLOW}Verificando arquivo de estado...${NC}"
    
    state_file="data/app_state.json"
    
    if [ ! -f "$state_file" ]; then
        echo -e "${RED}Arquivo de estado não encontrado${NC}"
        return
    fi
    
    # Verificar data de modificação
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$state_file")
    else
        # Linux
        mod_time=$(stat -c "%y" "$state_file")
    fi
    
    echo -e "${GREEN}Arquivo de estado encontrado${NC}"
    echo -e "  Última modificação: $mod_time"
    
    # Extrair e mostrar informações relevantes
    if command -v jq &> /dev/null; then
        echo -e "\n${BLUE}Resumo do estado:${NC}"
        
        # Tentar extrair timestamp
        timestamp=$(jq -r '.timestamp // "N/A"' "$state_file" 2>/dev/null)
        echo -e "  Timestamp: $timestamp"
        
        # Tentar extrair total de operações
        if jq -e '.trades_history' "$state_file" &>/dev/null; then
            trade_count=$(jq '.trades_history | length' "$state_file")
            echo -e "  Total de operações: $trade_count"
        fi
        
        # Tentar extrair posições abertas
        if jq -e '.open_positions' "$state_file" &>/dev/null; then
            open_pos=$(jq '.open_positions | length' "$state_file")
            echo -e "  Posições abertas: $open_pos"
            
            if [ "$open_pos" -gt 0 ]; then
                echo -e "\n${BLUE}Posições abertas:${NC}"
                jq -r '.open_positions | to_entries[] | "  \(.key): Entrada: \(.value.entry_price), Quantidade: \(.value.quantity), Timestamp: \(.value.timestamp)"' "$state_file" 2>/dev/null
            fi
        fi
    else
        echo -e "${YELLOW}Instale o 'jq' para ver detalhes do arquivo de estado${NC}"
        echo -e "  Conteúdo bruto do arquivo de estado:"
        head -n 20 "$state_file" | cat -n
    fi
    echo
}

# Função para verificar configuração
check_config() {
    echo -e "${YELLOW}Verificando configurações...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}Arquivo .env não encontrado${NC}"
        return
    fi
    
    echo -e "${GREEN}Arquivo .env encontrado${NC}"
    
    # Verificar configurações críticas
    simulation=$(grep "SIMULATION_MODE" .env | grep -v "^#" | cut -d "=" -f2)
    testnet=$(grep "USE_TESTNET" .env | grep -v "^#" | cut -d "=" -f2)
    
    if [[ "$simulation" == "true" ]]; then
        echo -e "${RED}Aviso: Bot está configurado para MODO DE SIMULAÇÃO${NC}"
    else
        echo -e "${GREEN}Bot configurado para operações reais${NC}"
    fi
    
    if [[ "$testnet" == "true" ]]; then
        echo -e "${RED}Aviso: Bot está configurado para usar TESTNET${NC}"
    else
        echo -e "${GREEN}Bot configurado para usar API de produção${NC}"
    fi
    
    # Verificar outras configurações importantes
    primary_coin=$(grep "PRIMARY_COIN" .env | grep -v "^#" | cut -d "=" -f2)
    trade_amount=$(grep "TRADE_AMOUNT" .env | grep -v "^#" | cut -d "=" -f2)
    take_profit=$(grep "TAKE_PROFIT_PERCENTAGE" .env | grep -v "^#" | cut -d "=" -f2)
    stop_loss=$(grep "STOP_LOSS_PERCENTAGE" .env | grep -v "^#" | cut -d "=" -f2)
    
    echo -e "\n${BLUE}Configurações de trading:${NC}"
    echo -e "  Moeda principal: $primary_coin"
    echo -e "  Valor por operação: $trade_amount"
    echo -e "  Take Profit: $take_profit%"
    echo -e "  Stop Loss: $stop_loss%"
    
    # Verificar se Telegram está configurado
    telegram_token=$(grep "TELEGRAM_BOT_TOKEN" .env | grep -v "^#" | cut -d "=" -f2)
    if [ -z "$telegram_token" ] || [ "$telegram_token" == "" ]; then
        echo -e "\n${YELLOW}Notificações Telegram não configuradas${NC}"
    else
        echo -e "\n${GREEN}Notificações Telegram configuradas${NC}"
    fi
    
    echo
}

# Função para verificar conexão com a Binance
check_binance_connection() {
    echo -e "${YELLOW}Verificando conexão com a Binance...${NC}"
    
    # Executar um teste simples de conexão
    python -c "
import sys
sys.path.append('.')
from binance_api import BinanceAPI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
use_testnet = os.getenv('USE_TESTNET', 'false').lower() in ['true', '1', 'yes', 'y', 'sim', 's']

if not api_key or not api_secret:
    print('Credenciais de API não encontradas no arquivo .env')
    sys.exit(1)

try:
    api = BinanceAPI(api_key, api_secret, testnet=use_testnet)
    if api.test_connection():
        print('OK')
        # Tenta obter informações da conta
        account = api.get_account_info()
        print('ACCOUNT_OK')
    else:
        print('FAIL')
except Exception as e:
    print(f'ERROR: {str(e)}')
" > /tmp/binance_connection_check.txt

    connection_result=$(cat /tmp/binance_connection_check.txt)
    
    if [[ "$connection_result" == *"OK"* ]]; then
        echo -e "${GREEN}✓ Conexão com a API da Binance bem-sucedida${NC}"
        
        if [[ "$connection_result" == *"ACCOUNT_OK"* ]]; then
            echo -e "${GREEN}✓ Informações da conta recuperadas com sucesso${NC}"
            
            # Mostrar saldos disponíveis
            echo -e "\n${BLUE}Verificando saldos disponíveis...${NC}"
            python -c "
import sys
sys.path.append('.')
from binance_api import BinanceAPI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
use_testnet = os.getenv('USE_TESTNET', 'false').lower() in ['true', '1', 'yes', 'y', 'sim', 's']

try:
    api = BinanceAPI(api_key, api_secret, testnet=use_testnet)
    account = api.get_account_info()
    
    relevant_coins = ['BNB', 'USDT', 'BTC', 'ETH', 'BRL']
    
    for balance in account['balances']:
        asset = balance.get('asset', '')
        free = float(balance.get('free', '0'))
        locked = float(balance.get('locked', '0'))
        total = free + locked
        
        if asset in relevant_coins or total > 0:
            print(f'{asset}: Livre={free}, Bloqueado={locked}, Total={total}')
        
except Exception as e:
    print(f'Erro ao obter saldos: {str(e)}')
"
        fi
    else
        error_msg=$(echo "$connection_result" | grep "ERROR")
        echo -e "${RED}✗ Falha na conexão com a API da Binance${NC}"
        echo -e "${RED}  $error_msg${NC}"
        
        # Verificar se as credenciais estão presentes
        if [[ "$connection_result" == *"Credenciais de API não encontradas"* ]]; then
            echo -e "${RED}  As credenciais da API não foram encontradas no arquivo .env${NC}"
            echo -e "${YELLOW}  Execute setup_real.sh ou setup_real_advanced.sh para configurar suas credenciais${NC}"
        fi
    fi
    
    # Limpar arquivo temporário
    rm /tmp/binance_connection_check.txt
    echo
}

# Função para reiniciar o bot
restart_bot() {
    echo -e "${YELLOW}Reiniciando o bot...${NC}"
    
    # Verificar se o bot está rodando
    if pgrep -f "python main.py" > /dev/null; then
        pid=$(pgrep -f "python main.py")
        echo -e "Encerrando processo $pid..."
        kill $pid
        
        # Aguarda processo terminar
        sleep 3
        if pgrep -f "python main.py" > /dev/null; then
            echo -e "${RED}Processo não respondeu, forçando encerramento...${NC}"
            kill -9 $pid
            sleep 1
        fi
    fi
    
    echo -e "Iniciando o bot..."
    nohup python main.py > /tmp/robot_crypt_start.log 2>&1 &
    
    sleep 2
    if pgrep -f "python main.py" > /dev/null; then
        new_pid=$(pgrep -f "python main.py")
        echo -e "${GREEN}Bot reiniciado com sucesso (PID: $new_pid)${NC}"
        echo -e "Verifique os logs com: tail -f logs/robot-crypt-\$(date +%Y%m%d).log"
    else
        echo -e "${RED}Falha ao reiniciar o bot. Verifique o log de inicialização:${NC}"
        cat /tmp/robot_crypt_start.log
    fi
    echo
}

# Função para criar backup
create_backup() {
    echo -e "${YELLOW}Criando backup dos dados...${NC}"
    
    backup_dir="backups"
    mkdir -p $backup_dir
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$backup_dir/robot_crypt_backup_$timestamp.tar.gz"
    
    # Arquivos para backup
    echo "Incluindo arquivos de configuração e dados no backup..."
    tar -czf $backup_file .env data/ logs/ 2>/dev/null
    
    echo -e "${GREEN}Backup criado em: $backup_file${NC}"
    echo
}

# Função para verificar a integridade do banco de dados SQLite
check_database() {
    echo -e "${YELLOW}Verificando banco de dados SQLite...${NC}"
    
    if [ -f "data/robot_crypt.db" ]; then
        echo -e "✓ ${GREEN}Banco de dados encontrado${NC}"
        
        # Verifica integridade com SQLite
        echo "Executando verificação de integridade..."
        integrity=$(echo "PRAGMA integrity_check;" | sqlite3 data/robot_crypt.db)
        
        if [ "$integrity" == "ok" ]; then
            echo -e "✓ ${GREEN}Integridade do banco de dados: OK${NC}"
        else
            echo -e "✗ ${RED}Problemas de integridade no banco de dados!${NC}"
            echo -e "${YELLOW}Deseja criar um backup e reparar o banco de dados? (s/n)${NC}"
            read -r repair_db
            
            if [[ $repair_db == "s" || $repair_db == "S" ]]; then
                repair_database
            fi
        fi
    else
        echo -e "✗ ${RED}Banco de dados não encontrado!${NC}"
        echo -e "${YELLOW}Um novo banco de dados será criado quando o bot for executado.${NC}"
    fi
    
    echo
}

# Função para reparar o banco de dados
repair_database() {
    echo -e "${YELLOW}Reparando banco de dados...${NC}"
    
    # Faz backup do banco atual
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="data/robot_crypt_backup_$timestamp.db"
    
    cp data/robot_crypt.db "$backup_file"
    echo -e "✓ ${GREEN}Backup criado: $backup_file${NC}"
    
    # Cria um novo banco de dados vazio
    rm data/robot_crypt.db
    echo -e "✓ ${GREEN}Banco de dados corrompido removido${NC}"
    echo -e "${YELLOW}Um novo banco de dados será criado quando o bot for executado.${NC}"
    
    # Copia dados do estado do app_state.json para o novo banco
    if [ -f "data/app_state.json" ]; then
        echo -e "✓ ${GREEN}Arquivo app_state.json encontrado para migração${NC}"
    else
        echo -e "✗ ${RED}Arquivo app_state.json não encontrado!${NC}"
        echo -e "${YELLOW}O bot iniciará com um estado limpo.${NC}"
    fi
}

# Função para limpar os arquivos temporários e desnecessários
clean_temp_files() {
    echo -e "${YELLOW}Limpando arquivos temporários...${NC}"
    
    # Remove arquivos .pyc
    find . -name "*.pyc" -delete
    echo -e "✓ ${GREEN}Arquivos .pyc removidos${NC}"
    
    # Remove diretórios __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} +
    echo -e "✓ ${GREEN}Diretórios __pycache__ removidos${NC}"
    
    # Limpa logs antigos (mais de 30 dias)
    find logs -name "*.log" -type f -mtime +30 -delete
    echo -e "✓ ${GREEN}Logs antigos removidos${NC}"
    
    echo
}

# Menu principal
while true; do
    echo -e "${BLUE}Menu de Manutenção do Robot-Crypt${NC}"
    echo "1. Verificar status do bot"
    echo "2. Verificar logs recentes"
    echo "3. Verificar arquivo de estado"
    echo "4. Verificar configurações"
    echo "5. Verificar conexão com Binance e saldos"
    echo "6. Reiniciar o bot"
    echo "7. Criar backup"
    echo "8. Verificar e reparar banco de dados"
    echo "9. Limpar arquivos temporários"
    echo "10. Sair"
    echo
    read -p "Escolha uma opção (1-10): " option
    echo
    
    case $option in
        1) check_bot_status ;;
        2) check_recent_logs ;;
        3) check_state_file ;;
        4) check_config ;;
        5) check_binance_connection ;;
        6) restart_bot ;;
        7) create_backup ;;
        8) check_database ;;
        9) clean_temp_files ;;
        10) echo "Encerrando..."; exit 0 ;;
        *) echo -e "${RED}Opção inválida${NC}" ;;
    esac
    
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo
    read -p "Pressione ENTER para continuar..."
    echo
done
