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

# Run the main Python script
python main.py
