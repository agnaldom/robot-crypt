#!/bin/bash
# Script para ajudar a configurar as credenciais da testnet da Binance

echo "======================================================="
echo "  Configuração da Testnet da Binance para Robot-Crypt  "
echo "======================================================="
echo
echo "Este script ajudará você a configurar corretamente as credenciais"
echo "da testnet da Binance no seu arquivo .env"
echo
echo "Passos para obter as credenciais da testnet:"
echo "1. Acesse: https://testnet.binance.vision/"
echo "2. Faça login com sua conta Google/Github"
echo "3. Na página inicial, clique em 'Generate HMAC_SHA256 Key'"
echo "4. Copie a API Key e Secret Key geradas"
echo
echo "Agora, digite as credenciais obtidas:"

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando um novo..."
    touch .env
fi

# Lê os valores das chaves
read -p "Testnet API Key: " testnet_key
read -p "Testnet API Secret: " testnet_secret

# Checa se os valores foram fornecidos
if [ -z "$testnet_key" ] || [ -z "$testnet_secret" ]; then
    echo "Erro: API Key e Secret são obrigatórios para a testnet."
    exit 1
fi

# Atualiza ou adiciona as variáveis no arquivo .env
if grep -q "TESTNET_API_KEY" .env; then
    # Se a variável já existir, atualiza o valor
    sed -i "" "s/TESTNET_API_KEY=.*/TESTNET_API_KEY=$testnet_key/" .env
    sed -i "" "s/TESTNET_API_SECRET=.*/TESTNET_API_SECRET=$testnet_secret/" .env
    sed -i "" "s/USE_TESTNET=.*/USE_TESTNET=true/" .env
else
    # Caso contrário, adiciona as variáveis ao final do arquivo
    echo "" >> .env
    echo "# Credenciais para testnet" >> .env
    echo "TESTNET_API_KEY=$testnet_key" >> .env
    echo "TESTNET_API_SECRET=$testnet_secret" >> .env
    echo "USE_TESTNET=true" >> .env
fi

echo
echo "Credenciais da testnet configuradas com sucesso!"
echo
echo "Para executar o bot usando a testnet:"
echo "$ python main.py"
echo
echo "Para alternar entre testnet e produção, modifique a variável USE_TESTNET no arquivo .env"
