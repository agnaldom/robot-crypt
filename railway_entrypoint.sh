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

# Variáveis globais
SHOULD_EXIT=0
PYTHON_PID=""

# Função para tratamento de sinais
handle_signal() {
  local signal=$1
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Recebido sinal $signal. Preparando encerramento gracioso..."
  
  # Marcar flag de saída, mas não encerrar o script imediatamente
  SHOULD_EXIT=1
  
  # Se o processo Python está em execução, envie o sinal para ele
  if [ ! -z "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Enviando $signal para o processo Python (PID $PYTHON_PID)"
    kill -$signal "$PYTHON_PID" 2>/dev/null
  fi
}

# Registrando handlers para diversos sinais
trap 'handle_signal TERM' SIGTERM
trap 'handle_signal INT' SIGINT
trap 'handle_signal HUP' SIGHUP

# Função para reiniciar o script Python em caso de falha
restart_on_failure() {
  local max_retries=3
  local retry_count=0
  local retry_delay=30
  local exit_code=0
  local log_file="/app/logs/robot-crypt-$(date '+%Y%m%d').log"
  
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Inicializando Robot-Crypt com reinício automático" | tee -a "$log_file"
  
  # Cria o arquivo de log se não existir
  touch "$log_file"
  
  # Loop principal de execução
  while [ $SHOULD_EXIT -eq 0 ]; do
    # Registrar início da execução
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Iniciando execução do Python (tentativa $((retry_count + 1)))" | tee -a "$log_file"
    
    # Cria um FIFO temporário para comunicação entre processos
    FIFO_PATH="/tmp/python_fifo_$$"
    rm -f "$FIFO_PATH"
    mkfifo "$FIFO_PATH"
    
    # Inicia tee em background para capturar logs
    tee -a "$log_file" < "$FIFO_PATH" &
    TEE_PID=$!
    
    # Executa o script Python com saída para o FIFO
    # Para resolver o problema com PID, executamos Python diretamente
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Iniciando processo Python..." | tee -a "$log_file"
    python main.py > "$FIFO_PATH" 2>&1 &
    PYTHON_PID=$!
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Processo Python iniciado com PID $PYTHON_PID" | tee -a "$log_file"
    
    # Aguarda o término do processo em background
    wait $PYTHON_PID || true
    exit_code=$?
    
    # Limpar recursos
    kill $TEE_PID 2>/dev/null || true
    rm -f "$FIFO_PATH" 2>/dev/null || true
    
    # Verifica se a flag de saída foi definida
    if [ $SHOULD_EXIT -eq 1 ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Interrupção solicitada. Encerrando o script." | tee -a "$log_file"
      break
    fi
    
    # Registra a finalização no log
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Script Python encerrou com código: $exit_code" | tee -a "$log_file"
    
    # Se foi encerrado com sucesso, não reinicia
    if [ $exit_code -eq 0 ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Finalização normal. Não será reiniciado." | tee -a "$log_file"
      break
    fi
    
    # Se foi encerrado com sinal de término (SIGTERM=143, SIGINT=130, SIGHUP=129), não reinicia
    if [ $exit_code -eq 143 ] || [ $exit_code -eq 130 ] || [ $exit_code -eq 129 ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Finalização por sinal ($exit_code). Não será reiniciado." | tee -a "$log_file"
      break
    fi
    
    # Verifica se atingiu o limite de tentativas
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Máximo de $max_retries tentativas atingido. Não será reiniciado." | tee -a "$log_file"
      break
    fi
    
    # Espera antes de reiniciar
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Reiniciando em $retry_delay segundos... (tentativa $retry_count de $max_retries)" | tee -a "$log_file"
    
    # Loop de espera que verifica periodicamente se devemos sair
    local waited=0
    while [ $waited -lt $retry_delay ] && [ $SHOULD_EXIT -eq 0 ]; do
      sleep 1
      waited=$((waited + 1))
    done
    
    # Se foi solicitada a saída durante a espera, sai do loop principal
    if [ $SHOULD_EXIT -eq 1 ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Interrupção solicitada durante espera. Encerrando o script." | tee -a "$log_file"
      break
    fi
  done
  
  # Mantém o container em execução para depuração e para evitar restarts
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Script principal encerrado. Mantendo container ativo para depuração." | tee -a "$log_file"
  echo "Para encerrar o container manualmente, use 'docker stop' ou pressione Ctrl+C se estiver em modo interativo." | tee -a "$log_file"
  echo "Você pode acessar os logs em /app/logs/ para investigar qualquer problema." | tee -a "$log_file"
  
  # Ao invés de tail -f, usamos um loop que pode ser interrompido com sinais
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Container continua em execução. Pressione Ctrl+C para encerrar." | tee -a "$log_file"
  
  # Loop que mantém o container em execução mas pode ser interrompido facilmente
  # Define um contador para tentar reiniciar automaticamente se nenhum erro crítico
  local auto_restart_timer=0
  local auto_restart_interval=3600  # 1 hora em segundos
  
  while [ $SHOULD_EXIT -eq 0 ]; do
    # Verifica se deve tentar reiniciar automaticamente após um tempo
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 143 ] || [ $exit_code -eq 130 ] || [ $exit_code -eq 129 ]; then
      # Códigos normais de saída - não reinicia automaticamente
      auto_restart_timer=0
    else
      # Em caso de erro, incrementa o contador para eventual reinício automático
      auto_restart_timer=$((auto_restart_timer + 10))
      
      # Verifica se está na hora de tentar reiniciar
      if [ $auto_restart_timer -ge $auto_restart_interval ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Tentando reinício automático após $auto_restart_interval segundos..." | tee -a "$log_file"
        # Sai deste loop para retornar ao loop principal de execução
        break
      fi
    fi
    
    # Aguarda um pouco
    sleep 10
  done
  
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Encerrando container graciosamente." | tee -a "$log_file"
}

# Configuração adicional para melhor log de erros
set -o pipefail

# Configuração de timezone no log
export TZ="America/Sao_Paulo"

# Registra início do container
echo "$(date '+%Y-%m-%d %H:%M:%S') - Container Robot-Crypt iniciado. Versão do script: 1.1"

# Inicia o script com mecanismo de reinício
restart_on_failure

# Esta linha só é executada quando o script for realmente encerrado
echo "$(date '+%Y-%m-%d %H:%M:%S') - Container Robot-Crypt encerrado."
exit 0
