# Docker Usage Guide - Robot-Crypt

Este guia explica como usar o Docker para executar a aplicação Robot-Crypt de diferentes maneiras.

## 🚀 Modos de Execução

A aplicação suporta dois modos principais:

1. **API Mode**: Executa o servidor FastAPI (`uvicorn src.main:app`)
2. **Robot Mode**: Executa o bot de trading (`python start_robot.py`)

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Pelo menos 2GB de RAM livre
- Portas 8000, 5432, 6379 e 8080 disponíveis

## 🛠️ Comandos Principais

### 1. Construir a Imagem

```bash
# Construir a imagem Docker
docker build -t robot-crypt .
```

### 2. Execução Direta com Docker

#### Modo API (FastAPI)
```bash
# Executar apenas o servidor API
docker run -p 8000:8000 robot-crypt api

# Ou usando o comando completo equivalente
docker run -p 8000:8000 robot-crypt
```

#### Modo Bot (Trading Robot)
```bash
# Executar apenas o bot de trading
docker run robot-crypt robot
```

#### Modo Desenvolvimento (com reload)
```bash
# API com hot reload
docker run -p 8000:8000 -e DEBUG=true -e RELOAD_FLAG=--reload -v $(pwd):/app robot-crypt api
```

### 3. Usando Docker Compose (Recomendado)

#### Ambiente Completo de Produção
```bash
# Iniciar API + PostgreSQL + Redis + Adminer
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f api
```

#### Ambiente de Desenvolvimento
```bash
# Iniciar em modo desenvolvimento (com hot reload)
docker-compose --profile dev up -d

# Ver logs do desenvolvimento
docker-compose logs -f dev
```

#### Executar o Bot de Trading
```bash
# Iniciar o bot junto com os serviços
docker-compose --profile bot up -d

# Ou iniciar apenas o bot (assumindo que DB e Redis já estão rodando)
docker-compose up robot
```

#### Ambiente Completo (API + Bot)
```bash
# Iniciar tudo: API, Bot, Database, Redis
docker-compose --profile bot up -d
```

## 🔧 Configuração de Ambiente

### Variáveis de Ambiente Disponíveis

```bash
# Configurações gerais
SIMULATION_MODE=true          # Modo simulação (padrão: true)
USE_TESTNET=false            # Usar testnet (padrão: false)
DEBUG=false                  # Modo debug (padrão: false)

# Servidor
HOST=0.0.0.0                 # Host do servidor
PORT=8000                    # Porta do servidor

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/robot_crypt

# Redis
REDIS_URL=redis://redis:6379

# Segurança
SECRET_KEY=your-secret-key-here
```

### Arquivo .env
Crie um arquivo `.env` na raiz do projeto:

```env
# .env
SIMULATION_MODE=true
USE_TESTNET=false
DEBUG=false
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/robot_crypt
REDIS_URL=redis://redis:6379

# API Keys (se necessário)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

## 📊 Monitoramento e Logs

### Verificar Status dos Serviços
```bash
# Status geral
docker-compose ps

# Health check
curl http://localhost:8000/health

# Logs em tempo real
docker-compose logs -f
```

### Acessar Serviços

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database Admin**: http://localhost:8080
- **Redis**: localhost:6379

## 🗂️ Estrutura de Volumes

```bash
# Volumes criados automaticamente
./logs:/app/logs              # Logs da aplicação
./data:/app/data              # Dados da aplicação
postgres_data:/var/lib/postgresql/data  # Dados do PostgreSQL
redis_data:/data              # Dados do Redis
```

## 🛡️ Comandos Úteis

### Limpeza
```bash
# Parar todos os serviços
docker-compose down

# Remover volumes (CUIDADO: perde dados)
docker-compose down -v

# Remover imagens
docker rmi robot-crypt

# Limpeza completa
docker-compose down -v --rmi all
```

### Backup do Banco de Dados
```bash
# Backup
docker-compose exec db pg_dump -U postgres robot_crypt > backup.sql

# Restore
docker-compose exec -T db psql -U postgres robot_crypt < backup.sql
```

### Acesso ao Container
```bash
# Acesso ao container da API
docker-compose exec api bash

# Acesso ao container do bot
docker-compose exec robot bash

# Acesso ao banco de dados
docker-compose exec db psql -U postgres robot_crypt
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Porta já em uso**
   ```bash
   # Verificar qual processo está usando a porta
   lsof -i :8000
   
   # Mudar porta no docker-compose.yml
   ports:
     - "8001:8000"  # Usar porta 8001 no host
   ```

2. **Problemas de permissão**
   ```bash
   # Dar permissões aos diretórios
   chmod -R 755 logs data
   ```

3. **Banco de dados não conecta**
   ```bash
   # Verificar se o PostgreSQL está rodando
   docker-compose ps db
   
   # Verificar logs do banco
   docker-compose logs db
   ```

4. **Container não inicia**
   ```bash
   # Verificar logs
   docker-compose logs api
   
   # Reconstruir imagem
   docker-compose build --no-cache
   ```

## 🚦 Comandos de Exemplo para Uso Diário

### Desenvolvimento
```bash
# Iniciar ambiente de desenvolvimento
docker-compose --profile dev up -d

# Acompanhar logs
docker-compose logs -f dev
```

### Produção
```bash
# Iniciar apenas API
docker-compose up -d api

# Iniciar API + Bot
docker-compose --profile bot up -d

# Verificar saúde
curl http://localhost:8000/health
```

### Teste
```bash
# Executar testes
docker-compose exec api python -m pytest

# Executar bot uma vez
docker-compose run --rm robot
```

## 📝 Notas Importantes

1. **Primeira execução**: Na primeira vez, o Docker baixará as imagens necessárias
2. **Dados persistentes**: Os dados do banco ficam salvos mesmo após parar os containers
3. **Modo simulação**: Por padrão, a aplicação roda em modo simulação (seguro)
4. **Logs**: Todos os logs são salvos no diretório `./logs`
5. **Segurança**: Altere as senhas padrão em produção

## 🔗 Links Úteis

- API Documentation: http://localhost:8000/docs
- API Redoc: http://localhost:8000/redoc
- Database Admin: http://localhost:8080
- Health Check: http://localhost:8000/health
