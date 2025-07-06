#!/bin/bash
# Script para verificar o saldo total da carteira

# Obtém o diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verifica se temos Python instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não está instalado. Por favor, instale o Python 3 antes de continuar."
    exit 1
fi

# Executa o script de sincronização em modo de saldo apenas
echo "Consultando saldo da carteira..."
python3 sync_wallet.py --balance-only "$@"
