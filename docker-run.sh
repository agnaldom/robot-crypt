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
echo "3. Modo Produção Básico (API da Binance Real)"
echo "4. Modo Produção Avançado (Configuração detalhada para conta real)"
echo "5. Construir/Reconstruir a imagem Docker"
echo "6. Visualizar logs"
echo "7. Parar o container"
echo "8. Ver status de monitoramento"
echo "9. Sair"
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
            echo "Configurando modo de produção básico..."
            ./setup_real.sh
            echo "Iniciando container em modo de produção..."
            docker-compose up -d
        else
            echo "Operação cancelada."
        fi
        ;;
    4)
        echo "⚠️ ATENÇÃO: Modo de Produção Avançado usa DINHEIRO REAL! ⚠️"
        read -p "Tem certeza que deseja continuar? (s/n): " confirmacao
        if [[ "$confirmacao" == "s" || "$confirmacao" == "S" ]]; then
            echo "Configurando modo de produção avançado..."
            chmod +x setup_real_advanced.sh
            ./setup_real_advanced.sh
            echo "Iniciando container em modo de produção..."
            docker-compose up -d
        else
            echo "Operação cancelada."
        fi
        ;;
    5)
        echo "Construindo/Reconstruindo a imagem Docker..."
        docker-compose build --no-cache
        echo "Imagem construída com sucesso!"
        ;;
    6)
        echo "Visualizando logs (pressione CTRL+C para sair)..."
        docker-compose logs -f
        ;;
    7)
        echo "Parando o container..."
        docker-compose down
        echo "Container parado."
        ;;
    8)
        echo "Verificando status de monitoramento..."
        # Verificar se o container está em execução
        if docker ps | grep -q "robot-crypt"; then
            echo "✅ Bot em execução"
            
            # Criar diretórios necessários caso não existam
            mkdir -p logs
            mkdir -p data
            
            # Verificar logs recentes
            echo "📝 Logs recentes:"
            docker-compose logs --tail=10
            
            # Verificar estado (se arquivo existe)
            if [ -f "data/app_state.json" ]; then
                echo "💾 Arquivo de estado encontrado ($(date -r data/app_state.json '+%Y-%m-%d %H:%M:%S'))"
                
                # Se tiver jq instalado, mostrar informações do estado
                if command -v jq &> /dev/null; then
                    echo "📊 Resumo do estado:"
                    jq -r '.timestamp // "N/A"' data/app_state.json 2>/dev/null | xargs echo "- Última atualização:"
                    jq '.trades_history | length // 0' data/app_state.json 2>/dev/null | xargs echo "- Total de operações:"
                    jq '.open_positions | length // 0' data/app_state.json 2>/dev/null | xargs echo "- Posições abertas:"
                fi
            else
                echo "❌ Arquivo de estado não encontrado"
            fi
        else
            echo "❌ Bot não está em execução"
        fi
        ;;
    9)
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
