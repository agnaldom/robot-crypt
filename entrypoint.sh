#!/bin/bash

set -e

# Configurações padrão
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}
DEBUG=${DEBUG:-false}
RELOAD_FLAG=${RELOAD_FLAG:-}
LOG_LEVEL=${LOG_LEVEL:-info}
LOG_FORMAT=${LOG_FORMAT:-structured}
LOG_COLORS=${LOG_COLORS:-true}
SHOW_SYSTEM_INFO=${SHOW_SYSTEM_INFO:-true}

# Cores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Função para log estruturado
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ "$LOG_FORMAT" = "structured" ]; then
        local color=""
        case $level in
            "INFO") color="$GREEN" ;;
            "WARN") color="$YELLOW" ;;
            "ERROR") color="$RED" ;;
            "DEBUG") color="$CYAN" ;;
            *) color="$WHITE" ;;
        esac
        
        if [ "$LOG_COLORS" = "true" ]; then
            echo -e "${color}[${timestamp}] [${level}] ${message}${NC}"
        else
            echo "[${timestamp}] [${level}] ${message}"
        fi
    else
        echo "${message}"
    fi
}

# Função para mostrar informações do sistema
show_system_info() {
    if [ "$SHOW_SYSTEM_INFO" = "true" ]; then
        log_message "INFO" "🐳 Container Information:"
        log_message "INFO" "   - Hostname: $(hostname)"
        log_message "INFO" "   - OS: $(uname -s) $(uname -r)"
        log_message "INFO" "   - Python Version: $(python --version)"
        log_message "INFO" "   - User: $(whoami)"
        log_message "INFO" "   - Working Directory: $(pwd)"
        log_message "INFO" "   - Available Memory: $(free -h | grep '^Mem:' | awk '{print $2}' 2>/dev/null || echo 'N/A')"
        log_message "INFO" "   - CPU Cores: $(nproc 2>/dev/null || echo 'N/A')"
        echo ""
    fi
}

# Função para aguardar serviços
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    log_message "INFO" "⏳ Aguardando $service_name ($host:$port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_message "INFO" "✅ $service_name está disponível!"
            return 0
        fi
        
        log_message "DEBUG" "🔄 Tentativa $attempt/$max_attempts - $service_name não está pronto ainda..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_message "ERROR" "❌ Timeout aguardando $service_name após $max_attempts tentativas"
    return 1
}

# Função para verificar dependências
check_dependencies() {
    log_message "INFO" "🔍 Verificando dependências..."
    
    # Extrair informações do DATABASE_URL se disponível
    if [ -n "${DATABASE_URL:-}" ]; then
        # Extrair host e porta do PostgreSQL
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
            log_message "INFO" "💾 Verificando conexão com PostgreSQL..."
            wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
        else
            log_message "WARN" "⚠️ Não foi possível extrair informações do PostgreSQL da DATABASE_URL"
        fi
    else
        log_message "DEBUG" "💾 DATABASE_URL não especificada, pulando verificação do PostgreSQL"
    fi
    
    # Verificar Redis se especificado
    if [ -n "${REDIS_URL:-}" ]; then
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
            log_message "INFO" "📛 Verificando conexão com Redis..."
            wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
        else
            log_message "WARN" "⚠️ Não foi possível extrair informações do Redis da REDIS_URL"
        fi
    else
        log_message "DEBUG" "📛 REDIS_URL não especificada, pulando verificação do Redis"
    fi
    
    log_message "INFO" "✅ Verificação de dependências concluída"
}

# Função para iniciar a API
start_api() {
    echo ""
    log_message "INFO" "🚀 ==========================================="
    log_message "INFO" "📚 Iniciando Robot-Crypt API Server"
    log_message "INFO" "🚀 ==========================================="
    
    # Mostrar informações do sistema
    show_system_info
    
    # Mostrar configurações
    log_message "INFO" "⚙️ Configurações do Servidor:"
    log_message "INFO" "   - Host: $HOST"
    log_message "INFO" "   - Port: $PORT"
    log_message "INFO" "   - Debug: $DEBUG"
    log_message "INFO" "   - Log Level: $LOG_LEVEL"
    log_message "INFO" "   - Log Format: $LOG_FORMAT"
    log_message "INFO" "   - Simulation Mode: ${SIMULATION_MODE:-true}"
    log_message "INFO" "   - Use Testnet: ${USE_TESTNET:-false}"
    echo ""
    
    # Verificar dependências
    check_dependencies
    echo ""
    
    # Construir comando uvicorn
    UVICORN_CMD="uvicorn src.main:app --host $HOST --port $PORT"
    
    # Adicionar flag de reload se especificado
    if [ "$DEBUG" = "true" ] || [ -n "$RELOAD_FLAG" ]; then
        UVICORN_CMD="$UVICORN_CMD --reload"
        log_message "INFO" "🔄 Hot reload ativado"
    fi
    
    # Adicionar log level baseado na configuração (converter para minúsculo)
    UVICORN_LOG_LEVEL=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')
    UVICORN_CMD="$UVICORN_CMD --log-level $UVICORN_LOG_LEVEL"
    
    log_message "INFO" "💻 Executando: $UVICORN_CMD"
    log_message "INFO" "🚀 ==========================================="
    echo ""
    
    exec $UVICORN_CMD
}

# Função para iniciar o bot
start_robot() {
    echo ""
    log_message "INFO" "🤖 ==========================================="
    log_message "INFO" "💹 Iniciando Robot-Crypt Trading Bot"
    log_message "INFO" "🤖 ==========================================="
    
    # Mostrar informações do sistema
    show_system_info
    
    # Mostrar configurações
    log_message "INFO" "⚙️ Configurações do Bot:"
    log_message "INFO" "   - Simulation Mode: ${SIMULATION_MODE:-true}"
    log_message "INFO" "   - Use Testnet: ${USE_TESTNET:-false}"
    log_message "INFO" "   - Debug: $DEBUG"
    log_message "INFO" "   - Log Level: $LOG_LEVEL"
    log_message "INFO" "   - Log Format: $LOG_FORMAT"
    echo ""
    
    # Verificar dependências
    check_dependencies
    echo ""
    
    log_message "INFO" "🔄 Executando: python start_robot.py"
    log_message "INFO" "🤖 ==========================================="
    echo ""
    
    exec python start_robot.py
}

# Verificar comando
case "$1" in
    api)
        start_api
        ;;
    robot)
        start_robot
        ;;
    ""|help|-h|--help)
        echo ""
        log_message "INFO" "📝 Comandos disponíveis:"
        log_message "INFO" "   api      - Iniciar o servidor API"
        log_message "INFO" "   robot    - Iniciar o bot de trading"
        log_message "INFO" "   help     - Mostrar esta mensagem"
        echo ""
        log_message "INFO" "📝 Variáveis de ambiente:"
        log_message "INFO" "   HOST              - Host do servidor (padrão: 0.0.0.0)"
        log_message "INFO" "   PORT              - Porta do servidor (padrão: 8080)"
        log_message "INFO" "   DEBUG             - Modo debug (padrão: false)"
        log_message "INFO" "   LOG_LEVEL         - Nível de log (padrão: info)"
        log_message "INFO" "   LOG_FORMAT        - Formato do log (padrão: structured)"
        log_message "INFO" "   LOG_COLORS        - Cores nos logs (padrão: true)"
        log_message "INFO" "   SHOW_SYSTEM_INFO  - Mostrar info do sistema (padrão: true)"
        log_message "INFO" "   SIMULATION_MODE   - Modo simulação (padrão: true)"
        log_message "INFO" "   USE_TESTNET       - Usar testnet (padrão: false)"
        echo ""
        exit 0
        ;;
    *)
        log_message "ERROR" "❌ Comando desconhecido: $1"
        log_message "INFO" "📝 Use './entrypoint.sh help' para ver os comandos disponíveis"
        exit 1
        ;;
esac

