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
- Iniciar o bot em modo de produção (dinheiro real)
- Reconstruir a imagem Docker
- Visualizar logs
- Parar o container

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

**Produção** (Binance real):
Configure manualmente o arquivo `.env`

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
  - `./logs:/root/.robot-crypt/logs`: Persistência de logs

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
