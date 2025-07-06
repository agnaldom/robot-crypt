#!/bin/bash

set -e

# Configurações padrão
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
DEBUG=${DEBUG:-false}
RELOAD_FLAG=${RELOAD_FLAG:-}

# Função para aguardar serviços
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo "Aguardando $service_name ($host:$port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name está disponível!"
            return 0
        fi
        
        echo "⏳ Tentativa $attempt/$max_attempts - $service_name não está pronto ainda..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Timeout aguardando $service_name"
    return 1
}

# Função para verificar dependências
check_dependencies() {
    # Extrair informações do DATABASE_URL se disponível
    if [ -n "${DATABASE_URL:-}" ]; then
        # Extrair host e porta do PostgreSQL
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
            wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
        fi
    fi
    
    # Verificar Redis se especificado
    if [ -n "${REDIS_URL:-}" ]; then
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
            wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
        fi
    fi
}

# Funcao para iniciar a API
start_api() {
    echo "=========================================="
    echo "Iniciando Robot-Crypt API Server"
    echo "Host: $HOST"
    echo "Port: $PORT"
    echo "Debug: $DEBUG"
    echo "Simulation Mode: ${SIMULATION_MODE:-true}"
    echo "=========================================="
    
    # Verificar dependências
    check_dependencies
    
    # Construir comando uvicorn
    UVICORN_CMD="uvicorn src.main:app --host $HOST --port $PORT"
    
    # Adicionar flag de reload se especificado
    if [ "$DEBUG" = "true" ] || [ -n "$RELOAD_FLAG" ]; then
        UVICORN_CMD="$UVICORN_CMD --reload"
        echo "Hot reload ativado"
    fi
    
    # Adicionar log level baseado no debug
    if [ "$DEBUG" = "true" ]; then
        UVICORN_CMD="$UVICORN_CMD --log-level debug"
    else
        UVICORN_CMD="$UVICORN_CMD --log-level info"
    fi
    
    echo "Executando: $UVICORN_CMD"
    echo "=========================================="
    
    exec $UVICORN_CMD
}

# Funcao para iniciar o bot
start_robot() {
    echo "=========================================="
    echo "Iniciando Robot-Crypt Trading Bot"
    echo "Simulation Mode: ${SIMULATION_MODE:-true}"
    echo "Use Testnet: ${USE_TESTNET:-false}"
    echo "=========================================="
    
    # Verificar dependências
    check_dependencies
    
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
        echo "Comandos disponíveis:"
        echo "  api      - Iniciar o servidor API"
        echo "  robot    - Iniciar o bot de trading"
        exit 0
        ;;
    *)
        echo "Comando desconhecido: $1"
        echo "Use './entrypoint.sh help' para ver os comandos disponíveis"
        exit 1
        ;;
esac

