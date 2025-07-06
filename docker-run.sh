#!/bin/bash

# Robot-Crypt Docker Helper Script
# Este script facilita a execução da aplicação Robot-Crypt com Docker

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}Robot-Crypt Docker Helper${NC}"
    echo -e "${BLUE}===========================${NC}"
    echo ""
    echo "Uso: $0 [COMANDO] [OPÇÕES]"
    echo ""
    echo -e "${GREEN}Comandos disponíveis:${NC}"
    echo "  build              - Construir a imagem Docker"
    echo "  api               - Executar API FastAPI"
    echo "  robot             - Executar bot de trading"
    echo "  dev               - Executar em modo desenvolvimento"
    echo "  full              - Executar API + Bot + Banco + Redis"
    echo "  stop              - Parar todos os serviços"
    echo "  logs              - Mostrar logs"
    echo "  status            - Mostrar status dos containers"
    echo "  clean             - Limpeza completa"
    echo "  shell             - Acesso shell ao container da API"
    echo "  db                - Acesso ao PostgreSQL"
    echo "  test              - Executar testes"
    echo "  backup            - Fazer backup do banco"
    echo "  restore           - Restaurar backup do banco"
    echo ""
    echo -e "${GREEN}Exemplos:${NC}"
    echo "  $0 api            # Iniciar apenas a API"
    echo "  $0 dev            # Modo desenvolvimento com hot reload"
    echo "  $0 full           # Ambiente completo"
    echo "  $0 logs api       # Ver logs da API"
    echo ""
}

# Função para verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker não está instalado${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose não está instalado${NC}"
        exit 1
    fi
}

# Função para criar diretórios necessários
create_dirs() {
    echo -e "${YELLOW}📁 Criando diretórios necessários...${NC}"
    mkdir -p logs data
    chmod -R 755 logs data
}

# Função para construir imagem
build_image() {
    echo -e "${YELLOW}🏗️  Construindo imagem Docker...${NC}"
    docker build -t robot-crypt .
    echo -e "${GREEN}✅ Imagem construída com sucesso${NC}"
}

# Função para iniciar API
start_api() {
    echo -e "${YELLOW}🚀 Iniciando API FastAPI...${NC}"
    create_dirs
    docker-compose up -d api
    echo -e "${GREEN}✅ API iniciada com sucesso${NC}"
    echo -e "${BLUE}📍 Acesse: http://localhost:8000${NC}"
    echo -e "${BLUE}📚 Docs: http://localhost:8000/docs${NC}"
}

# Função para iniciar bot
start_robot() {
    echo -e "${YELLOW}🤖 Iniciando bot de trading...${NC}"
    create_dirs
    docker-compose --profile bot up -d
    echo -e "${GREEN}✅ Bot iniciado com sucesso${NC}"
}

# Função para modo desenvolvimento
start_dev() {
    echo -e "${YELLOW}🛠️  Iniciando modo desenvolvimento...${NC}"
    create_dirs
    docker-compose --profile dev up -d
    echo -e "${GREEN}✅ Ambiente de desenvolvimento iniciado${NC}"
    echo -e "${BLUE}📍 Acesse: http://localhost:8000${NC}"
    echo -e "${YELLOW}🔥 Hot reload ativado${NC}"
}

# Função para ambiente completo
start_full() {
    echo -e "${YELLOW}🌟 Iniciando ambiente completo...${NC}"
    create_dirs
    docker-compose --profile bot up -d
    echo -e "${GREEN}✅ Ambiente completo iniciado${NC}"
    echo -e "${BLUE}📍 API: http://localhost:8000${NC}"
    echo -e "${BLUE}🗄️  Admin DB: http://localhost:8080${NC}"
}

# Função para parar serviços
stop_services() {
    echo -e "${YELLOW}⏹️  Parando todos os serviços...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Serviços parados${NC}"
}

# Função para mostrar logs
show_logs() {
    local service=${2:-""}
    if [ -n "$service" ]; then
        echo -e "${YELLOW}📄 Mostrando logs do serviço: $service${NC}"
        docker-compose logs -f "$service"
    else
        echo -e "${YELLOW}📄 Mostrando logs de todos os serviços${NC}"
        docker-compose logs -f
    fi
}

# Função para mostrar status
show_status() {
    echo -e "${YELLOW}📊 Status dos containers:${NC}"
    docker-compose ps
    echo ""
    echo -e "${YELLOW}🏥 Health check:${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API está saudável${NC}"
    else
        echo -e "${RED}❌ API não está respondendo${NC}"
    fi
}

# Função para limpeza
clean_all() {
    echo -e "${YELLOW}🧹 Limpeza completa...${NC}"
    read -p "Tem certeza? Isso removerá TODOS os dados (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        docker image prune -f
        echo -e "${GREEN}✅ Limpeza concluída${NC}"
    else
        echo -e "${YELLOW}⏭️  Limpeza cancelada${NC}"
    fi
}

# Função para acesso shell
shell_access() {
    echo -e "${YELLOW}🐚 Acessando shell do container da API...${NC}"
    docker-compose exec api bash
}

# Função para acesso ao banco
db_access() {
    echo -e "${YELLOW}🗄️  Acessando PostgreSQL...${NC}"
    docker-compose exec db psql -U postgres robot_crypt
}

# Função para executar testes
run_tests() {
    echo -e "${YELLOW}🧪 Executando testes...${NC}"
    docker-compose exec api python -m pytest
}

# Função para backup
backup_db() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${YELLOW}💾 Fazendo backup do banco...${NC}"
    docker-compose exec db pg_dump -U postgres robot_crypt > "$backup_file"
    echo -e "${GREEN}✅ Backup salvo em: $backup_file${NC}"
}

# Função para restore
restore_db() {
    local backup_file="$2"
    if [ -z "$backup_file" ]; then
        echo -e "${RED}❌ Especifique o arquivo de backup${NC}"
        echo "Uso: $0 restore <arquivo.sql>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}❌ Arquivo não encontrado: $backup_file${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}📥 Restaurando backup...${NC}"
    docker-compose exec -T db psql -U postgres robot_crypt < "$backup_file"
    echo -e "${GREEN}✅ Backup restaurado${NC}"
}

# Main
main() {
    check_docker
    
    case "${1:-help}" in
        "build")
            build_image
            ;;
        "api")
            start_api
            ;;
        "robot")
            start_robot
            ;;
        "dev")
            start_dev
            ;;
        "full")
            start_full
            ;;
        "stop")
            stop_services
            ;;
        "logs")
            show_logs "$@"
            ;;
        "status")
            show_status
            ;;
        "clean")
            clean_all
            ;;
        "shell")
            shell_access
            ;;
        "db")
            db_access
            ;;
        "test")
            run_tests
            ;;
        "backup")
            backup_db
            ;;
        "restore")
            restore_db "$@"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando desconhecido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"
