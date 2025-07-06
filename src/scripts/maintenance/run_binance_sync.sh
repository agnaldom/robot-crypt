#!/bin/bash

# Script para executar a sincronização de dados da Binance sem prompt

# Carrega as variáveis de ambiente do arquivo .env manualmente
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Executa o script Python que não utiliza dotenv
python binance_data_sync_noprompt.py
