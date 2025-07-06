#!/bin/bash
# Ativa o modo de simulação para o robot-crypt

echo "===================================="
echo "  Configurando Modo de Simulação    "
echo "===================================="
echo 
echo "Este script irá configurar o arquivo .env para"
echo "executar o bot em modo de simulação, sem conectar"
echo "à API da Binance."
echo
echo "Perfeito para testes e desenvolvimento."
echo

# Executa o script Python que configura o modo de simulação
python setup_simulation.py

# Confirmação
echo
echo "Configuração concluída!"
echo "Execute o bot com:"
echo "python main.py"
