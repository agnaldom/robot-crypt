#!/bin/bash

# Script de instalação e configuração do Robot-Crypt

echo "===== Robot-Crypt: Instalação e Configuração ====="
echo

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Cria ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv

# Ativa ambiente virtual
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Ativando ambiente virtual (macOS/Linux)..."
    source venv/bin/activate
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Ativando ambiente virtual (Windows)..."
    source venv/Scripts/activate
else 
    echo "Sistema operacional não reconhecido. Tente ativar o ambiente virtual manualmente."
    echo "Em Linux/macOS: source venv/bin/activate"
    echo "Em Windows: venv\\Scripts\\activate"
    exit 1
fi

# Instala dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verifica arquivo .env
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando modelo..."
    cat > .env << EOL
# Credenciais da Binance (obrigatório)
BINANCE_API_KEY=sua_api_key
BINANCE_API_SECRET=seu_api_secret

# Configurações de notificação (opcional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Configurações de trading (opcional - se não definido, usará os valores padrão em config.py)
TRADE_AMOUNT=100
TAKE_PROFIT_PERCENTAGE=2
STOP_LOSS_PERCENTAGE=0.5
MAX_HOLD_TIME=86400
ENTRY_DELAY=60
EOL
    echo "Arquivo .env criado com sucesso."
else
    echo "Arquivo .env já existe."
fi

# Menu de opções pós-instalação
echo
echo "Instalação concluída! O que você gostaria de fazer agora?"
echo
echo "1. Executar o bot em modo de simulação (recomendado para testes)"
echo "2. Configurar modo testnet da Binance"
echo "3. Executar testes automatizados"
echo "4. Sair"
echo
read -p "Escolha uma opção (1-4): " opcao

case $opcao in
    1)
        echo "Configurando modo de simulação..."
        ./setup_simulation.sh
        
        echo
        read -p "Deseja executar o bot agora? (s/n): " executar
        if [[ $executar == "s" || $executar == "S" ]]; then
            python main.py
        fi
        ;;
    2)
        echo "Configurando modo testnet..."
        ./setup_testnet.sh
        ;;
    3)
        echo "Executando testes automatizados..."
        python run_tests.py
        ;;
    4)
        echo "Instalação finalizada. Execute 'python main.py' quando quiser iniciar o bot."
        ;;
    *)
        echo "Opção inválida. Instalação finalizada."
        ;;
esac

# Instruções finais
echo
echo "Robot-Crypt está pronto para uso!"
echo "Para mais informações, consulte o README.md"
STOP_LOSS_PERCENTAGE=0.5
MAX_HOLD_TIME=86400
ENTRY_DELAY=60
EOL
    echo "Arquivo .env criado. Por favor, edite-o para adicionar suas credenciais da Binance."
    echo "Execute o script novamente após configurar o arquivo .env."
    exit 0
fi

echo
echo "Instalação concluída! Para iniciar o bot, execute:"
echo "python main.py"
echo
echo "Para mais informações, consulte o README.md"
