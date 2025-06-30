#!/bin/bash
# Script para iniciar apenas o dashboard do Robot-Crypt

echo "===================================="
echo "  Robot-Crypt Dashboard Standalone  "
echo "===================================="
echo

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não encontrado! Por favor, instale o Python3 primeiro."
    exit 1
fi

# Instala as dependências necessárias para o dashboard se necessário
echo "Verificando dependências..."
pip install dash==2.6.0 dash-core-components==2.0.0 dash-html-components==2.0.0 dash-table==5.0.0 plotly==5.10.0 pandas numpy

# Define a porta do dashboard (padrão 8050)
export DASHBOARD_PORT="${DASHBOARD_PORT:-8050}"

echo "Iniciando dashboard na porta $DASHBOARD_PORT..."
python3 run_dashboard.py

# Se chegar aqui, algo deu errado
echo "Dashboard encerrado. Verifique os logs para mais detalhes."
