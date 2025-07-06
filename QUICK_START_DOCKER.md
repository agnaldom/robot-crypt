# 🚀 Quick Start - Docker Robot-Crypt

## ⚡ Comandos Mais Simples

### Usando o script helper (Recomendado)
```bash
# Dar permissão (apenas uma vez)
chmod +x docker-run.sh

# Executar API
./docker-run.sh api

# Executar bot de trading
./docker-run.sh robot

# Modo desenvolvimento (com hot reload)
./docker-run.sh dev

# Ver status
./docker-run.sh status

# Parar tudo
./docker-run.sh stop
```

### Usando Docker Compose diretamente
```bash
# API apenas
docker-compose up -d api

# Bot de trading
docker-compose --profile bot up -d

# Desenvolvimento
docker-compose --profile dev up -d

# Parar tudo
docker-compose down
```

### Usando Docker diretamente
```bash
# Construir imagem
docker build -t robot-crypt .

# Executar API
docker run -p 8000:8000 robot-crypt api

# Executar bot
docker run robot-crypt robot
```

## 🔗 Acessos Rápidos

- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin DB**: http://localhost:8080

## 📋 Equivalências dos Comandos

| Comando Original | Docker Compose | Script Helper |
|------------------|----------------|---------------|
| `python start_robot.py` | `docker-compose --profile bot up -d` | `./docker-run.sh robot` |
| `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload` | `docker-compose --profile dev up -d` | `./docker-run.sh dev` |
| `uvicorn src.main:app --host 0.0.0.0 --port 8000` | `docker-compose up -d api` | `./docker-run.sh api` |

## 🛡️ Modo Seguro (Padrão)

Por padrão, a aplicação roda em:
- ✅ **Modo Simulação** (`SIMULATION_MODE=true`)
- ✅ **Sem Testnet** (`USE_TESTNET=false`)
- ✅ **Ambiente Seguro** (sem trading real)

## 🔧 Personalização Rápida

Crie um arquivo `.env`:
```env
SIMULATION_MODE=true
DEBUG=false
SECRET_KEY=sua-chave-secreta-aqui
```

## 🆘 Problemas Comuns

```bash
# Porta ocupada? Mude no docker-compose.yml
ports:
  - "8001:8000"  # Usar porta 8001

# Reconstruir se houver problemas
docker-compose build --no-cache

# Ver logs se algo der errado
docker-compose logs api
```

## ✅ Teste Rápido

```bash
# 1. Iniciar API
./docker-run.sh api

# 2. Testar (em outro terminal)
curl http://localhost:8000/health

# 3. Ver documentação
open http://localhost:8000/docs
```

Pronto! Sua aplicação está rodando no Docker! 🎉
