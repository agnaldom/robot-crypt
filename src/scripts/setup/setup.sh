#!/bin/bash
# Script de Setup Consolidado do Robot-Crypt
# Estrutura modular organizada

set -e

# Detecta o diretório raiz do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

show_help() {
    echo "Uso: $0 [modo]"
    echo ""
    echo "Modos disponíveis:"
    echo "  simulation  - Configura modo de simulação (padrão)"
    echo "  testnet     - Configura para Binance TestNet"
    echo "  production  - Configura para produção (conta real)"
    echo "  help        - Mostra esta ajuda"
    echo ""
}

setup_simulation() {
    echo "🔄 Configurando modo de simulação..."
    export SIMULATION_MODE=true
    export USE_TESTNET=false
    echo "SIMULATION_MODE=true" >> .env
    echo "USE_TESTNET=false" >> .env
    echo "✅ Modo de simulação configurado!"
}

setup_testnet() {
    echo "🧪 Configurando modo TestNet..."
    echo "⚠️  Você precisará de credenciais específicas da TestNet"
    echo "📖 Obtenha em: https://testnet.binance.vision/"
    
    read -p "Digite sua TestNet API Key: " TESTNET_API_KEY
    read -s -p "Digite sua TestNet Secret Key: " TESTNET_SECRET_KEY
    echo ""
    
    echo "TESTNET_API_KEY=$TESTNET_API_KEY" >> .env
    echo "TESTNET_SECRET_KEY=$TESTNET_SECRET_KEY" >> .env
    echo "USE_TESTNET=true" >> .env
    echo "SIMULATION_MODE=false" >> .env
    echo "✅ Modo TestNet configurado!"
}

setup_production() {
    echo "🚨 ATENÇÃO: Configurando modo de PRODUÇÃO com dinheiro real!"
    echo "⚠️  Certifique-se de que você entende os riscos"
    
    read -p "Você tem certeza? (digite 'SIM' para continuar): " confirm
    if [ "$confirm" != "SIM" ]; then
        echo "❌ Configuração cancelada"
        exit 1
    fi
    
    read -p "Digite sua API Key de produção: " PROD_API_KEY
    read -s -p "Digite sua Secret Key de produção: " PROD_SECRET_KEY
    echo ""
    
    echo "BINANCE_API_KEY=$PROD_API_KEY" >> .env
    echo "BINANCE_API_SECRET=$PROD_SECRET_KEY" >> .env
    echo "USE_TESTNET=false" >> .env
    echo "SIMULATION_MODE=false" >> .env
    echo "✅ Modo de produção configurado!"
    echo "🚨 CUIDADO: O bot agora operará com dinheiro real!"
}

# Função principal
main() {
    local mode=${1:-simulation}
    
    case $mode in
        "simulation"|"sim")
            setup_simulation
            ;;
        "testnet"|"test")
            setup_testnet
            ;;
        "production"|"prod"|"real")
            setup_production
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "❌ Modo inválido: $mode"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
