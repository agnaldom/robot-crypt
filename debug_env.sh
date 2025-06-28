#!/bin/bash

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Print them
echo "TELEGRAM_BOT_TOKEN = '$TELEGRAM_BOT_TOKEN'"
echo "TELEGRAM_CHAT_ID = '$TELEGRAM_CHAT_ID'"
