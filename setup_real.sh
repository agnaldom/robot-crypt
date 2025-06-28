#!/bin/bash
# Script para configurar o Robot-Crypt para execução real na Binance

echo "======================================================="
echo "  Configuração de PRODUÇÃO da Binance para Robot-Crypt "
echo "======================================================="
echo
echo "ATENÇÃO: Este script configura o bot para operar em AMBIENTE REAL"
echo "com DINHEIRO REAL na sua conta Binance."
echo
echo "Passos para obter as credenciais de produção:"
echo "1. Acesse: https://www.binance.com/pt-BR/my/settings/api-management"
echo "2. Faça login na sua conta Binance"
echo "3. Crie uma nova API Key com permissões de leitura e trading"
echo "4. Copie a API Key e Secret Key geradas"
echo
echo "ATENÇÃO: Verifique se você testou adequadamente sua estratégia em:"
echo "1. Modo de simulação (usando setup_simulation.sh)"
echo "2. Modo TestNet (usando setup_testnet.sh)"
echo "antes de passar para produção!"
echo

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando um novo..."
    touch .env
fi

# Confirmar decisão
read -p "Tem certeza que deseja configurar para PRODUÇÃO? (S/N): " confirmation
if [[ $confirmation != [Ss]* ]]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

# Lê os valores das chaves
read -p "API Key de PRODUÇÃO: " api_key
read -p "API Secret de PRODUÇÃO: " api_secret

# Checa se os valores foram fornecidos
if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
    echo "Erro: API Key e Secret são obrigatórios para produção."
    exit 1
fi

# Backup do arquivo .env
cp .env .env.backup
echo "Backup do arquivo .env criado em .env.backup"

# Atualiza ou adiciona as variáveis no arquivo .env
if grep -q "BINANCE_API_KEY" .env; then
    # Se a variável já existir, atualiza o valor
    sed -i "" "s/BINANCE_API_KEY=.*/BINANCE_API_KEY=$api_key/" .env
    sed -i "" "s/BINANCE_API_SECRET=.*/BINANCE_API_SECRET=$api_secret/" .env
    sed -i "" "s/USE_TESTNET=.*/USE_TESTNET=false/" .env
    sed -i "" "s/SIMULATION_MODE=.*/SIMULATION_MODE=false/" .env
else
    # Caso contrário, adiciona as variáveis ao final do arquivo
    echo "" >> .env
    echo "# Credenciais para PRODUÇÃO" >> .env
    echo "BINANCE_API_KEY=$api_key" >> .env
    echo "BINANCE_API_SECRET=$api_secret" >> .env
    echo "USE_TESTNET=false" >> .env
    echo "SIMULATION_MODE=false" >> .env
fi

echo
echo "==================================================="
echo "  CONFIGURAÇÃO DE PRODUÇÃO CONCLUÍDA COM SUCESSO!  "
echo "==================================================="
echo
echo "O Robot-Crypt agora está configurado para operar com DINHEIRO REAL."
echo "Execute com: python main.py"
echo
echo "ATENÇÃO: Monitore cuidadosamente as operações iniciais."
echo
