# Melhorias nos Logs do Docker

## Visão Geral

O sistema de logs do Robot-Crypt foi completamente redesenhado para fornecer uma experiência mais informativa e configurável. Os logs agora incluem timestamps, cores, níveis de log estruturados e informações detalhadas do sistema.

## Recursos Implementados

### 1. Logs Estruturados
- **Timestamps**: Todos os logs incluem timestamp no formato `YYYY-MM-DD HH:MM:SS`
- **Níveis de Log**: INFO, WARN, ERROR, DEBUG com cores específicas
- **Formatação Consistente**: Formato padronizado `[timestamp] [level] message`

### 2. Cores e Emojis
- **Cores por Nível**: 
  - 🟢 INFO (Verde)
  - 🟡 WARN (Amarelo)
  - 🔴 ERROR (Vermelho)
  - 🔵 DEBUG (Ciano)
- **Emojis Contextuais**: Cada tipo de operação tem seu emoji específico
- **Desabilitação**: Cores podem ser desabilitadas via variável de ambiente

### 3. Informações do Sistema
- **Hardware**: CPU cores, memória disponível
- **Software**: Python version, OS, hostname
- **Container**: Working directory, usuário atual
- **Configurações**: Todas as variáveis de ambiente relevantes

### 4. Monitoramento de Dependências
- **PostgreSQL**: Verificação de conectividade com retry automático
- **Redis**: Verificação opcional de Redis
- **Status Visual**: Indicadores visuais claros de sucesso/falha

## Variáveis de Ambiente

### Novas Variáveis de Log

| Variável | Valores | Padrão | Descrição |
|----------|---------|---------|-----------|
| `LOG_LEVEL` | `debug`, `info`, `warning`, `error` | `info` | Nível de log do sistema |
| `LOG_FORMAT` | `structured`, `simple` | `structured` | Formato dos logs |
| `LOG_COLORS` | `true`, `false` | `true` | Habilita/desabilita cores |
| `SHOW_SYSTEM_INFO` | `true`, `false` | `true` | Mostra informações do sistema |

### Variáveis Existentes Mantidas

| Variável | Valores | Padrão | Descrição |
|----------|---------|---------|-----------|
| `HOST` | IP/hostname | `0.0.0.0` | Host do servidor |
| `PORT` | Número da porta | `8000` | Porta do servidor |
| `DEBUG` | `true`, `false` | `false` | Modo debug |
| `SIMULATION_MODE` | `true`, `false` | `true` | Modo simulação |
| `USE_TESTNET` | `true`, `false` | `false` | Usar testnet |

## Exemplos de Uso

### 1. Logs Estruturados (Padrão)
```bash
docker run -e LOG_FORMAT=structured robot-crypt:latest api
```

**Saída:**
```
[2024-01-15 10:30:45] [INFO] 🚀 ===========================================
[2024-01-15 10:30:45] [INFO] 📚 Iniciando Robot-Crypt API Server
[2024-01-15 10:30:45] [INFO] 🚀 ===========================================
[2024-01-15 10:30:45] [INFO] 🐳 Container Information:
[2024-01-15 10:30:45] [INFO]    - Hostname: robot-crypt-container
[2024-01-15 10:30:45] [INFO]    - OS: Linux 5.4.0
[2024-01-15 10:30:45] [INFO]    - Python Version: Python 3.11.7
```

### 2. Logs Simples
```bash
docker run -e LOG_FORMAT=simple robot-crypt:latest api
```

**Saída:**
```
🚀 ===========================================
📚 Iniciando Robot-Crypt API Server
🚀 ===========================================
🐳 Container Information:
   - Hostname: robot-crypt-container
```

### 3. Logs sem Cores
```bash
docker run -e LOG_COLORS=false robot-crypt:latest api
```

### 4. Modo Debug
```bash
docker run -e LOG_LEVEL=debug robot-crypt:latest api
```

**Saída Adicional:**
```
[2024-01-15 10:30:45] [DEBUG] 💾 DATABASE_URL não especificada, pulando verificação do PostgreSQL
[2024-01-15 10:30:45] [DEBUG] 📛 REDIS_URL não especificada, pulando verificação do Redis
[2024-01-15 10:30:45] [DEBUG] 🔄 Tentativa 1/30 - PostgreSQL não está pronto ainda...
```

## Configuração Docker Compose

### Exemplo Completo
```yaml
version: '3.8'

services:
  robot-crypt-api:
    build: .
    environment:
      # Configurações de log
      - LOG_LEVEL=info
      - LOG_FORMAT=structured
      - LOG_COLORS=true
      - SHOW_SYSTEM_INFO=true
      
      # Configurações da aplicação
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
      - SIMULATION_MODE=true
```

### Configuração para Desenvolvimento
```yaml
environment:
  - LOG_LEVEL=debug
  - LOG_FORMAT=structured
  - LOG_COLORS=true
  - SHOW_SYSTEM_INFO=true
  - DEBUG=true
```

### Configuração para Produção
```yaml
environment:
  - LOG_LEVEL=info
  - LOG_FORMAT=structured
  - LOG_COLORS=false
  - SHOW_SYSTEM_INFO=false
  - DEBUG=false
```

## Benefícios das Melhorias

### 1. Debugging Melhorado
- **Timestamps precisos** para análise temporal
- **Níveis de log claros** para filtrar informações
- **Informações do sistema** para diagnóstico

### 2. Monitoramento Aprimorado
- **Status de dependências** em tempo real
- **Configurações visíveis** na inicialização
- **Indicadores visuais** de sucesso/falha

### 3. Experiência do Desenvolvedor
- **Logs coloridos** para melhor legibilidade
- **Emojis contextuais** para identificação rápida
- **Configuração flexível** para diferentes ambientes

### 4. Produção-Ready
- **Desabilitação de cores** para logs de produção
- **Controle de verbosidade** via LOG_LEVEL
- **Formato estruturado** para parsing automático

## Comandos Úteis

### Visualizar logs em tempo real
```bash
docker logs -f robot-crypt-api
```

### Filtrar logs por nível
```bash
docker logs robot-crypt-api 2>&1 | grep "\[ERROR\]"
```

### Salvar logs em arquivo
```bash
docker logs robot-crypt-api > logs/app.log 2>&1
```

### Logs sem cores para análise
```bash
docker run -e LOG_COLORS=false robot-crypt:latest api > app.log
```

## Troubleshooting

### Problemas Comuns

1. **Logs não aparecem coloridos**
   - Verificar se `LOG_COLORS=true`
   - Verificar se o terminal suporta cores

2. **Muitos logs debug**
   - Alterar `LOG_LEVEL=info` ou `LOG_LEVEL=warning`

3. **Informações do sistema não aparecem**
   - Verificar se `SHOW_SYSTEM_INFO=true`

4. **Dependências não são verificadas**
   - Verificar se `DATABASE_URL` e `REDIS_URL` estão definidas corretamente

## Próximos Passos

- [ ] Integração com sistemas de logging externos (ELK Stack, Splunk)
- [ ] Métricas de performance nos logs
- [ ] Logs estruturados em JSON para produção
- [ ] Rotação automática de logs
- [ ] Dashboard de logs em tempo real
