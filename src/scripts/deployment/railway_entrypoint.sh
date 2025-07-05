#!/bin/bash
# Entrypoint script for Railway deployment
# Version: 2.0

# Function to log messages with timestamp and category
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [${level}] - ${message}" | tee -a "$LOG_FILE"
}

# Set up initial variables
LOG_FILE="/app/logs/robot-crypt-$(date '+%Y%m%d').log"
SHOULD_EXIT=0
PYTHON_PID=""
DASHBOARD_PID=""
MAX_RESTARTS=5
RESTART_COUNT=0
RESTART_DELAY=30
HEALTH_CHECK_INTERVAL=30
MAX_MEMORY_PERCENT=85  # Maximum memory usage percentage before forcing restart

log "INFO" "Starting Robot-Crypt deployment on Railway..."
log "INFO" "Script Version: 2.0"

# Validate environment variables
log "INFO" "Validating environment variables..."

# Check for API keys
if [ -z "$BINANCE_API_KEY" ]; then
  log "ERROR" "BINANCE_API_KEY is not set!"
  exit 1
fi

if [ -z "$BINANCE_API_SECRET" ]; then
  log "ERROR" "BINANCE_API_SECRET is not set!"
  exit 1
fi

# Check for Telegram configuration if enabled
if [ "$NOTIFICATIONS_ENABLED" = "true" ] || [ "$NOTIFICATIONS_ENABLED" = "1" ]; then
  if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    log "ERROR" "NOTIFICATIONS_ENABLED is set to true but TELEGRAM_BOT_TOKEN is missing!"
    exit 1
  fi
  
  if [ -z "$TELEGRAM_CHAT_ID" ]; then
    log "ERROR" "NOTIFICATIONS_ENABLED is set to true but TELEGRAM_CHAT_ID is missing!"
    exit 1
  fi
fi

# Make sure data directories exist
mkdir -p /app/logs
mkdir -p /app/data
mkdir -p /app/reports

# Set permissions
chmod -R 777 /app/logs /app/data /app/reports

log "INFO" "Environment validated. Setting up Robot-Crypt..."

# Check for NEWS API key
if [ -z "$NEWS_API_KEY" ]; then
  log "WARNING" "NEWS_API_KEY not set. Contextual analysis may not work correctly."
fi

# Verify dashboard port configuration
if [ -z "$DASHBOARD_PORT" ]; then
  export DASHBOARD_PORT=8050
  log "INFO" "DASHBOARD_PORT not specified. Using default port: 8050"
fi

# Função para tratamento de sinais
handle_signal() {
  local signal=$1
  log "INFO" "Received signal $signal. Preparing graceful shutdown..."
  
  # Set exit flag but don't terminate script immediately
  SHOULD_EXIT=1
  
  # Send signal to Python process if running
  if [ ! -z "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
    log "INFO" "Sending $signal to Python process (PID $PYTHON_PID)"
    kill -$signal "$PYTHON_PID" 2>/dev/null
  fi
  
  # Send signal to Dashboard process if running
  if [ ! -z "$DASHBOARD_PID" ] && kill -0 "$DASHBOARD_PID" 2>/dev/null; then
    log "INFO" "Sending $signal to Dashboard process (PID $DASHBOARD_PID)"
    kill -$signal "$DASHBOARD_PID" 2>/dev/null
  fi
}

# Register signal handlers
trap 'handle_signal TERM' SIGTERM
trap 'handle_signal INT' SIGINT
trap 'handle_signal HUP' SIGHUP

# Health check function to monitor the main Python process
check_health() {
  local pid=$1
  local name=$2
  
  # Check if process is running
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    log "WARNING" "$name process (PID $pid) is not running!"
    return 1
  fi
  
  # Check CPU and memory usage
  if command -v ps >/dev/null 2>&1; then
    local mem_usage=$(ps -p $pid -o %mem= 2>/dev/null || echo "0")
    local cpu_usage=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
    
    mem_usage=$(echo $mem_usage | tr -d ' ')
    cpu_usage=$(echo $cpu_usage | tr -d ' ')
    
    log "DEBUG" "$name resource usage - Memory: ${mem_usage}%, CPU: ${cpu_usage}%"
    
    # Check if memory usage exceeds threshold
    if (( $(echo "$mem_usage > $MAX_MEMORY_PERCENT" | bc -l) )); then
      log "WARNING" "High memory usage detected (${mem_usage}%)! Recommending restart."
      return 2
    fi
  fi
  
  return 0
}

# Dashboard removido - será implementado como um projeto separado
start_dashboard() {
  log "INFO" "Dashboard foi removido e será implementado como um projeto separado"
  # Função mantida para compatibilidade com o script
  tee -a "$LOG_FILE" < "$DASHBOARD_FIFO" &
  DASHBOARD_TEE_PID=$!
  
  # Start the dashboard in background with its own log capture
  python dashboard.py > "$DASHBOARD_FIFO" 2>&1 &
  DASHBOARD_PID=$!
  
  log "INFO" "Dashboard started with PID $DASHBOARD_PID"
  
  # Wait a moment to ensure it starts properly
  sleep 3
  
  # Verify dashboard started correctly
  if ! kill -0 "$DASHBOARD_PID" 2>/dev/null; then
    log "ERROR" "Dashboard failed to start properly!"
    kill $DASHBOARD_TEE_PID 2>/dev/null || true
    rm -f "$DASHBOARD_FIFO" 2>/dev/null || true
    DASHBOARD_PID=""
    return 1
  fi
  
  return 0
}

# Main function to manage the application
main_loop() {
  log "INFO" "Initializing Robot-Crypt with automatic restart capability"
  
  # Start the dashboard first
  start_dashboard
  
  # Reset restart counter when successfully running for a while
  local stable_time=0
  
  while [ $SHOULD_EXIT -eq 0 ]; do
    # Check if we've exceeded max restarts
    if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
      log "ERROR" "Maximum restart limit ($MAX_RESTARTS) reached. Waiting 15 minutes before trying again."
      RESTART_COUNT=0
      sleep 900  # 15 minutes
    fi
    
    log "INFO" "Starting main Python application (attempt $((RESTART_COUNT + 1)))"
    
    # Create a FIFO for Python process logs
    PYTHON_FIFO="/tmp/python_fifo_$$"
    rm -f "$PYTHON_FIFO"
    mkfifo "$PYTHON_FIFO"
    
    # Start tee in background to capture logs
    tee -a "$LOG_FILE" < "$PYTHON_FIFO" &
    PYTHON_TEE_PID=$!
    
    # Start the main Python application
    log "INFO" "Starting Python process..."
    python main.py > "$PYTHON_FIFO" 2>&1 &
    PYTHON_PID=$!
    
    log "INFO" "Python process started with PID $PYTHON_PID"
    
    # Health check loop
    local run_time=0
    local exit_code=0
    local healthy_time=0
    
    while [ $SHOULD_EXIT -eq 0 ]; do
      # Perform health check on main process
      check_health "$PYTHON_PID" "Python"
      local health_status=$?
      
      # If process is healthy, increase healthy time counter
      if [ $health_status -eq 0 ]; then
        healthy_time=$((healthy_time + HEALTH_CHECK_INTERVAL))
      fi
      
      # If process has been healthy for a while, reset restart counter
      if [ $healthy_time -ge 300 ]; then  # 5 minutes of stable operation
        if [ $RESTART_COUNT -gt 0 ]; then
          log "INFO" "Application stable for 5 minutes, resetting restart counter"
          RESTART_COUNT=0
          healthy_time=0
        fi
      fi
      
      # Check for dashboard health
      if [ ! -z "$DASHBOARD_PID" ]; then
        check_health "$DASHBOARD_PID" "Dashboard"
        local dashboard_health=$?
        
        # If dashboard died, try to restart it
        if [ $dashboard_health -ne 0 ]; then
          log "WARNING" "Dashboard not running, attempting to restart..."
          start_dashboard
        fi
      fi
      
      # Critical health issue - needs restart
      if [ $health_status -eq 2 ]; then
        log "WARNING" "Critical health issue detected. Restarting application..."
        if [ ! -z "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
          kill -TERM "$PYTHON_PID" 2>/dev/null
          sleep 5
          # Force kill if still running
          kill -9 "$PYTHON_PID" 2>/dev/null || true
        fi
        break
      fi
      
      # Process died
      if [ $health_status -eq 1 ]; then
        log "WARNING" "Python process no longer running"
        # Get exit code if possible
        wait "$PYTHON_PID" 2>/dev/null || true
        exit_code=$?
        log "INFO" "Python process exited with code: $exit_code"
        break
      fi
      
      # Increment run time counter
      run_time=$((run_time + HEALTH_CHECK_INTERVAL))
      
      # Sleep for health check interval
      local waited=0
      while [ $waited -lt $HEALTH_CHECK_INTERVAL ] && [ $SHOULD_EXIT -eq 0 ]; do
        sleep 1
        waited=$((waited + 1))
      done
      
      # Check if exit was requested
      if [ $SHOULD_EXIT -eq 1 ]; then
        log "INFO" "Shutdown requested during health check. Exiting..."
        break
      fi
    done
    
    # Clean up Python process resources
    kill $PYTHON_TEE_PID 2>/dev/null || true
    rm -f "$PYTHON_FIFO" 2>/dev/null || true
    
    # If exit requested, break out of restart loop
    if [ $SHOULD_EXIT -eq 1 ]; then
      log "INFO" "Shutdown requested. Stopping all processes..."
      break
    fi
    
    # Normal exit (code 0) or signal-triggered exit - don't restart
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 143 ] || [ $exit_code -eq 130 ] || [ $exit_code -eq 129 ]; then
      log "INFO" "Normal termination (code $exit_code). Not restarting."
      break
    fi
    
    # Increment restart counter and add exponential backoff delay
    RESTART_COUNT=$((RESTART_COUNT + 1))
    local current_delay=$((RESTART_DELAY * RESTART_COUNT))
    
    # Cap the delay at 5 minutes
    if [ $current_delay -gt 300 ]; then
      current_delay=300
    fi
    
    log "INFO" "Restarting in $current_delay seconds... (attempt $RESTART_COUNT of $MAX_RESTARTS)"
    
    # Wait with periodic checks for exit signal
    local waited=0
    while [ $waited -lt $current_delay ] && [ $SHOULD_EXIT -eq 0 ]; do
      sleep 1
      waited=$((waited + 1))
    done
    
    # If exit requested during wait, break
    if [ $SHOULD_EXIT -eq 1 ]; then
      log "INFO" "Shutdown requested during restart delay. Exiting..."
      break
    fi
  done
  
  # Clean up dashboard process if running
  if [ ! -z "$DASHBOARD_PID" ] && kill -0 "$DASHBOARD_PID" 2>/dev/null; then
    log "INFO" "Stopping dashboard process..."
    kill -TERM "$DASHBOARD_PID" 2>/dev/null
    sleep 2
    kill -9 "$DASHBOARD_PID" 2>/dev/null || true
  fi
  
  # Clean up dashboard resources
  if [ ! -z "$DASHBOARD_TEE_PID" ]; then
    kill $DASHBOARD_TEE_PID 2>/dev/null || true
    rm -f "$DASHBOARD_FIFO" 2>/dev/null || true
  fi
  
  log "INFO" "All processes terminated. Container will exit shortly."
}

# Set up additional error handling
set -o pipefail

# Set timezone for logs
export TZ="America/Sao_Paulo"

# Run the main application loop
main_loop

log "INFO" "Container Robot-Crypt shutdown complete."
exit 0