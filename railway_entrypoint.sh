#!/bin/bash
# Entrypoint script for Railway deployment

echo "Starting Robot-Crypt deployment on Railway..."

# Validate environment variables
echo "Validating environment variables..."

# Check for API keys
if [ -z "$BINANCE_API_KEY" ]; then
  echo "ERROR: BINANCE_API_KEY is not set!"
  exit 1
fi

if [ -z "$BINANCE_API_SECRET" ]; then
  echo "ERROR: BINANCE_API_SECRET is not set!"
  exit 1
fi

# Check for Telegram configuration if enabled
if [ "$NOTIFICATIONS_ENABLED" = "true" ] || [ "$NOTIFICATIONS_ENABLED" = "1" ]; then
  if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "ERROR: NOTIFICATIONS_ENABLED is set to true but TELEGRAM_BOT_TOKEN is missing!"
    exit 1
  fi
  
  if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "ERROR: NOTIFICATIONS_ENABLED is set to true but TELEGRAM_CHAT_ID is missing!"
    exit 1
  fi
fi

# Make sure data directories exist
mkdir -p /app/logs
mkdir -p /app/data
mkdir -p /app/reports

# Set permissions
chmod -R 777 /app/logs /app/data /app/reports

echo "Environment validated. Starting Robot-Crypt..."

# Função para tratamento de sinais
handle_sigterm() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Recebido sinal de término. Encerrando aplicação graciosamente..."
  if [ ! -z "$PID" ]; then
    echo "Enviando SIGTERM para PID $PID"
    kill -TERM "$PID" 2>/dev/null
  fi
  exit 0
}

# Registrando handlers para sinais
trap handle_sigterm SIGTERM SIGINT

# Função para reiniciar o script Python em caso de falha
restart_on_failure() {
  local max_retries=3
  local retry_count=0
  local retry_delay=30
  local exit_code=0
  
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Inicializando Robot-Crypt com reinício automático"
  
  while true; do
    # Executa o script Python e redireciona saídas para arquivos de log (mantendo também no console)
    python main.py 2>&1 | tee -a /app/logs/robot-crypt-$(date '+%Y%m%d').log &
    PID=$!
    
    # Aguarda o término do processo em background
    wait $PID
    exit_code=$?
    
    # Registra a finalização no log
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Script Python encerrou com código: $exit_code"
    
    # Se foi encerrado com sucesso ou por sinal, não reinicia
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 143 ]; then  # 143 = 128 + 15 (SIGTERM)
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Finalização normal ou solicitada. Não será reiniciado."
      break
    fi
    
    # Verifica se atingiu o limite de tentativas
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Máximo de $max_retries tentativas atingido. Não será reiniciado."
      break
    fi
    
    # Espera antes de reiniciar
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Reiniciando em $retry_delay segundos... (tentativa $retry_count de $max_retries)"
    sleep $retry_delay
  done
  
  # Mantém o container em execução para depuração e para evitar restarts
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Script principal encerrado. Mantendo container ativo para depuração."
  echo "Para encerrar o container manualmente, use 'docker stop' ou pressione Ctrl+C se estiver em modo interativo."
  echo "Você pode acessar os logs em /app/logs/ para investigar qualquer problema."
  
  # Loop infinito que mantém o container em execução, mas é sensível a sinais
  tail -f /dev/null
}

# Inicia o script com mecanismo de reinício
restart_on_failure
