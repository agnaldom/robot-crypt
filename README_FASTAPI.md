# Robot-Crypt FastAPI

Uma aplicação FastAPI robusta para análise de mercado e gestão de operações de criptomoedas com autenticação JWT, banco de dados PostgreSQL e migrações automáticas com Alembic.

## 🚀 Funcionalidades

### Principais
- **Gráficos e Indicadores Técnicos**: Preços em tempo real, médias móveis (MA, EMA), Bandas de Bollinger, RSI, volume
- **Indicadores Macroeconômicos**: Eventos econômicos, notícias macro, índices globais, Fear and Greed Index
- **Performance do Robô**: Taxa de sucesso, retorno acumulado, número de operações, exposição atual
- **Gestão de Risco**: Limites de stop loss/take profit, índice de volatilidade, alertas de risco
- **Alertas e Notificações**: Eventos econômicos, mudanças bruscas, recomendações contextuais
- **Histórico e Relatórios**: Histórico de operações, gráficos de desempenho, exportação (PDF, CSV)
- **Personalização**: Seleção de criptomoedas, ajuste de parâmetros técnicos, layout customizável

### Tecnologias
- **Backend**: Python 3.11+ com FastAPI + Pydantic
- **Banco de Dados**: PostgreSQL + SQLAlchemy + Alembic
- **Autenticação**: JWT com refresh tokens
- **APIs**: Binance API, APIs de notícias e dados macro
- **Documentação**: Swagger/OpenAPI automática
- **Containerização**: Docker multi-stage
- **Testes**: Pytest com cobertura async

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 13+
- Docker (opcional)
- Node.js 18+ (para frontend, se aplicável)

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd robot-crypt
```

### 2. Configure o ambiente

#### Método 1: Ambiente local
```bash
# Instale as dependências
pip install -r requirements.txt

# Copie e configure o arquivo .env
cp .env.example .env
# Edite o .env com suas configurações
```

#### Método 2: Docker
```bash
# Build e execute com Docker
docker build -t robot-crypt-api .
docker run -p 8000:8000 --env-file .env robot-crypt-api
```

#### Método 3: Docker Compose (recomendado)
```bash
# Execute com PostgreSQL incluído
docker-compose up -d
```

### 3. Configure o banco de dados

```bash
# Instale o PostgreSQL (se não estiver usando Docker)
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql

# Configure o banco
createdb robot_crypt
```

### 4. Execute as migrações

```bash
# Inicialize o Alembic (apenas primeira vez)
alembic revision --autogenerate -m "Initial migration"

# Execute as migrações
alembic upgrade head
```

## 🚀 Execução

### Desenvolvimento
```bash
# Execute com hot reload
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Ou usando o Python diretamente
python -m src.main
```

### Produção
```bash
# Execute com configuração de produção
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

A API estará disponível em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Estrutura do Projeto

```
robot-crypt/
├── src/
│   ├── api/
│   │   └── routers/           # Rotas da API
│   │       ├── auth.py        # Autenticação JWT
│   │       ├── users.py       # Gestão de usuários
│   │       ├── assets.py      # Gestão de ativos
│   │       ├── indicators.py  # Indicadores técnicos
│   │       ├── trades.py      # Operações de trading
│   │       └── reports.py     # Relatórios
│   ├── core/
│   │   ├── config.py         # Configurações da aplicação
│   │   └── security.py       # Utilitários de segurança
│   ├── database/
│   │   └── database.py       # Configuração do banco
│   ├── models/               # Modelos SQLAlchemy
│   │   ├── user.py
│   │   ├── asset.py
│   │   ├── technical_indicator.py
│   │   ├── macro_indicator.py
│   │   ├── bot_performance.py
│   │   ├── risk_management.py
│   │   ├── alert.py
│   │   ├── trade.py
│   │   └── report.py
│   ├── schemas/              # Schemas Pydantic
│   │   ├── user.py
│   │   ├── asset.py
│   │   ├── token.py
│   │   └── ...
│   ├── services/             # Lógica de negócio
│   │   ├── user_service.py
│   │   └── ...
│   └── main.py               # Aplicação principal
├── alembic/                  # Migrações do banco
├── tests/                    # Testes automatizados
├── requirements.txt          # Dependências Python
├── Dockerfile               # Container Docker
├── docker-compose.yml       # Orquestração Docker
├── alembic.ini             # Configuração Alembic
└── .env.example            # Exemplo de configuração
```

## 🔧 Configuração

### Variáveis de Ambiente (arquivo .env)

```bash
# Aplicação
APP_NAME=Robot-Crypt API
DEBUG=false
SECRET_KEY=your-super-secret-key

# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/robot_crypt

# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
USE_TESTNET=true

# Trading
TRADING_PAIRS=BTC/USDT,ETH/USDT,BNB/USDT
TRADE_AMOUNT=100.0
SIMULATION_MODE=true

# Notificações
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📊 API Endpoints

### Autenticação
- `POST /auth/login` - Login com email/senha
- `POST /auth/refresh` - Renovar token de acesso
- `POST /auth/test-token` - Testar token

### Usuários
- `GET /users/me` - Perfil do usuário logado
- `PUT /users/me` - Atualizar perfil
- `GET /users/` - Listar usuários (admin)
- `POST /users/` - Criar usuário (admin)

### Ativos
- `GET /assets/` - Listar criptomoedas monitoradas
- `POST /assets/` - Adicionar novo ativo
- `GET /assets/{id}` - Detalhes do ativo

### Indicadores
- `GET /indicators/technical` - Indicadores técnicos
- `GET /indicators/macro` - Indicadores macroeconômicos
- `POST /indicators/calculate` - Calcular indicadores

### Trading
- `GET /trades/` - Histórico de operações
- `POST /trades/` - Executar operação
- `GET /trades/performance` - Performance do bot

### Relatórios
- `GET /reports/` - Listar relatórios
- `POST /reports/generate` - Gerar relatório
- `GET /reports/{id}/download` - Download de relatório

## 🧪 Testes

```bash
# Execute todos os testes
pytest

# Execute com cobertura
pytest --cov=src

# Execute testes específicos
pytest tests/test_auth.py

# Execute testes async
pytest -v tests/test_users.py
```

## 🔒 Segurança

- **Autenticação JWT** com tokens de acesso e refresh
- **Hashing de senhas** com bcrypt
- **Validação de entrada** com Pydantic
- **Rate limiting** para prevenir abuso
- **CORS configurado** para frontend
- **Headers de segurança** em produção

## 📈 Monitoramento

### Health Check
```bash
curl http://localhost:8000/health
```

### Métricas
- Logs estruturados com Python logging
- Health checks automáticos
- Monitoramento de performance do banco

## 🐳 Docker

### Build local
```bash
docker build -t robot-crypt-api .
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/robot_crypt
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: robot_crypt
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## 🚀 Deploy

### Railway (recomendado)
```bash
# Instale Railway CLI
npm install -g @railway/cli

# Login e deploy
railway login
railway init
railway up
```

### Heroku
```bash
# Configure buildpack
heroku buildpacks:set heroku/python

# Configure banco
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
```

## 🔧 Desenvolvimento

### Adicionar nova funcionalidade

1. **Criar modelo** em `src/models/`
2. **Criar schema** em `src/schemas/`
3. **Criar serviço** em `src/services/`
4. **Criar router** em `src/api/routers/`
5. **Gerar migração**: `alembic revision --autogenerate -m "Add feature"`
6. **Aplicar migração**: `alembic upgrade head`
7. **Escrever testes** em `tests/`

### Comandos úteis

```bash
# Gerar nova migração
alembic revision --autogenerate -m "Description"

# Ver histórico de migrações
alembic history

# Reverter migração
alembic downgrade -1

# Ver SQL de migração
alembic upgrade head --sql

# Formatar código
black src/
flake8 src/

# Type checking
mypy src/
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação da API em `/docs`
2. Consulte os logs da aplicação
3. Verifique issues do repositório
4. Entre em contato com a equipe de desenvolvimento

## 📄 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para detalhes.
