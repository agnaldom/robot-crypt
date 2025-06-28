# Executando Robot-Crypt em Docker

Este guia explica como executar o Robot-Crypt em um contêiner Docker, facilitando sua implantação em qualquer ambiente sem se preocupar com dependências do Python.

## Requisitos

- Docker instalado (https://docs.docker.com/get-docker/)
- Docker Compose instalado (https://docs.docker.com/compose/install/)

## Modos de Execução

### Script de Execução Rápida

Use o script `docker-run.sh` para uma configuração simplificada:

```bash
chmod +x docker-run.sh
./docker-run.sh
```

Este script oferece opções para:
- Iniciar o bot em modo de simulação
- Iniciar o bot em modo testnet
- Iniciar o bot em modo de produção básico (dinheiro real)
- Iniciar o bot em modo de produção avançado (configuração detalhada para conta real)
- Reconstruir a imagem Docker
- Visualizar logs
- Parar o container
- Ver status de monitoramento

### Execução Manual

#### 1. Construir a imagem

```bash
docker-compose build
```

#### 2. Configurar o ambiente

Escolha um dos modos:

**Simulação** (recomendado para testes):
```bash
python setup_simulation.py
```

**Testnet** (teste com a API da Binance):
```bash
./setup_testnet.sh
```

**Produção Básica** (Binance real):
```bash
./setup_real.sh
```

**Produção Avançada** (Binance real com configuração detalhada):
```bash
./setup_real_advanced.sh
```

#### 3. Executar o container

```bash
docker-compose up -d
```

#### 4. Verificar logs

```bash
docker-compose logs -f
```

#### 5. Parar o container

```bash
docker-compose down
```

## Estrutura do Docker

- **Dockerfile**: Define a imagem base, instala dependências e configura o ambiente
- **docker-compose.yml**: Configura o serviço e volumes para persistência de dados
- **Volumes**:
  - `./.env:/app/.env`: Mapeia o arquivo de configuração
  - `./logs:/app/logs`: Persistência de logs
  - `./data:/app/data`: Persistência do estado da aplicação

## Visualização de Logs (opcional)

O docker-compose.yml inclui um serviço comentado para Dozzle, uma ferramenta de visualização de logs:

1. Descomente as linhas do serviço `logs-viewer` no arquivo `docker-compose.yml`
2. Execute `docker-compose up -d`
3. Acesse `http://localhost:9999` em seu navegador

## Solução de Problemas

### Container Reiniciando Constantemente

Verifique os logs para identificar o problema:
```bash
docker-compose logs -f
```

Problemas comuns:
1. Credenciais inválidas da Binance
2. Erro de configuração no arquivo .env
3. Problemas de rede ao conectar-se à API da Binance

### Verificação de Estado da Aplicação

Para verificar o estado atual da aplicação:
```bash
# Usando a opção 8 do menu
./docker-run.sh
# E depois selecionar opção 8

# OU diretamente
cat data/app_state.json | jq
```

### Backup de Dados

Para fazer backup dos dados da aplicação:
```bash
# Backup do estado
cp data/app_state.json data/app_state_$(date +%Y%m%d).json.bak

# Backup dos logs
tar -czf logs_$(date +%Y%m%d).tar.gz logs/

# Backup da configuração
cp .env .env.$(date +%Y%m%d).bak
```

### Monitoramento Avançado

Para um monitoramento mais detalhado, consulte o documento `docs/MONITORAMENTO.md`.
