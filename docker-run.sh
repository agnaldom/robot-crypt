#!/bin/bash

# Script para executar o Robot-Crypt em Docker

echo "================================"
echo "  Robot-Crypt Docker Launcher   "
echo "================================"
echo

# Verificando se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker não está instalado. Por favor, instale o Docker primeiro."
    echo "Visite: https://docs.docker.com/get-docker/"
    exit 1
fi

# Menu de opções
echo "Escolha um modo de execução:"
echo "1. Modo de Simulação (sem API real)"
echo "2. Modo Testnet (API da Binance Testnet)"
echo "3. Modo Produção (API da Binance Real)"
echo "4. Construir/Reconstruir a imagem Docker"
echo "5. Visualizar logs"
echo "6. Parar o container"
echo "7. Sair"
echo
read -p "Opção: " opcao

case $opcao in
    1)
        echo "Configurando modo de simulação..."
        python setup_simulation.py
        echo "Iniciando container em modo de simulação..."
        docker-compose up -d
        ;;
    2)
        echo "Configurando modo testnet..."
        ./setup_testnet.sh
        echo "Iniciando container em modo testnet..."
        docker-compose up -d
        ;;
    3)
        echo "⚠️ ATENÇÃO: Modo de Produção usa DINHEIRO REAL! ⚠️"
        read -p "Tem certeza que deseja continuar? (s/n): " confirmacao
        if [[ "$confirmacao" == "s" || "$confirmacao" == "S" ]]; then
            echo "Certifique-se que seu arquivo .env está configurado corretamente com:"
            echo "- SIMULATION_MODE=false"
            echo "- USE_TESTNET=false"
            echo "- BINANCE_API_KEY e BINANCE_API_SECRET válidos"
            read -p "Pressione ENTER para continuar ou CTRL+C para cancelar"
            echo "Iniciando container em modo de produção..."
            docker-compose up -d
        else
            echo "Operação cancelada."
        fi
        ;;
    4)
        echo "Construindo/Reconstruindo a imagem Docker..."
        docker-compose build --no-cache
        echo "Imagem construída com sucesso!"
        ;;
    5)
        echo "Visualizando logs (pressione CTRL+C para sair)..."
        docker-compose logs -f
        ;;
    6)
        echo "Parando o container..."
        docker-compose down
        echo "Container parado."
        ;;
    7)
        echo "Saindo..."
        exit 0
        ;;
    *)
        echo "Opção inválida."
        exit 1
        ;;
esac

echo
echo "Operação concluída!"
