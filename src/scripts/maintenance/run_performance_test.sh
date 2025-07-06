#!/usr/bin/env bash
# Script para executar teste de desempenho no Robot-Crypt

# Cores para formatação
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}            TESTE DE EXECUÇÃO DO ROBOT-CRYPT              ${NC}"
echo -e "${BLUE}===========================================================${NC}"

# Verifica se estamos em ambiente virtual Python
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Aviso: Não está em um ambiente virtual Python.${NC}"
    echo -e "${YELLOW}Recomenda-se usar um ambiente virtual para testes.${NC}"
    echo ""
    
    # Tenta localizar um ambiente virtual existente
    if [[ -d "venv" ]]; then
        echo -e "${GREEN}Ambiente virtual encontrado. Ativando...${NC}"
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        echo -e "${GREEN}Ambiente virtual encontrado. Ativando...${NC}"
        source .venv/bin/activate
    else
        echo -e "${YELLOW}Nenhum ambiente virtual encontrado. Continuando com Python do sistema.${NC}"
    fi
fi

# Verifica dependências
echo -e "${BLUE}Verificando dependências...${NC}"
if ! python -c "import psutil" &> /dev/null; then
    echo -e "${YELLOW}Instalando dependência: psutil${NC}"
    pip install psutil
fi

# Verifica se o arquivo de teste existe
if [[ ! -f "test_execution.py" ]]; then
    echo -e "${RED}Arquivo de teste não encontrado: test_execution.py${NC}"
    exit 1
fi

# Dá permissão de execução ao arquivo de teste
chmod +x test_execution.py

echo -e "${BLUE}===========================================================${NC}"
echo -e "${GREEN}Iniciando teste de execução...${NC}"
echo -e "${BLUE}===========================================================${NC}"

# Executa o teste e captura saída
./test_execution.py

# Verifica o código de retorno
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Teste completo executado com sucesso!${NC}"
    
    # Verifica logs recentes
    echo -e "\n${BLUE}Procurando mensagens importantes nos logs...${NC}"
    if [[ -d "logs" ]]; then
        LATEST_LOG=$(ls -t logs/robot-crypt-* 2>/dev/null | head -n 1)
        if [[ -n "$LATEST_LOG" ]]; then
            echo -e "${GREEN}Arquivo de log mais recente: $LATEST_LOG${NC}"
            echo -e "\n${YELLOW}Últimas mensagens de erro (se houver):${NC}"
            grep -i "erro\|error\|falha\|fail\|exception" "$LATEST_LOG" | tail -n 10
            
            echo -e "\n${YELLOW}Informações sobre tempo de análise:${NC}"
            grep -i "ciclo de análise\|tempo médio" "$LATEST_LOG" | tail -n 5
        else
            echo -e "${YELLOW}Nenhum arquivo de log encontrado.${NC}"
        fi
    fi
    
    # Verifica configurações atuais
    echo -e "\n${BLUE}Verificando configuração...${NC}"
    if [[ -f ".env" ]]; then
        echo -e "${YELLOW}Configurações relevantes de .env:${NC}"
        grep -i "TRADING_INTERVAL\|SIMULATION_MODE\|USE_TESTNET\|API_KEY" .env | grep -v "SECRET"
    fi
    
    echo -e "\n${GREEN}Teste concluído. O sistema parece estar funcionando corretamente.${NC}"
else
    echo -e "${RED}❌ Teste falhou!${NC}"
    echo -e "${YELLOW}Verifique os logs acima para detalhes do problema.${NC}"
fi

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}              TESTE DE EXECUÇÃO FINALIZADO               ${NC}"
echo -e "${BLUE}===========================================================${NC}"
