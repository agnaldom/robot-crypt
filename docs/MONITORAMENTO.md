# Guia de Monitoramento para Operações Reais

Este guia fornece instruções detalhadas para monitorar o Robot-Crypt em operações com conta real na Binance.

## 1. Ferramentas de Monitoramento

### 1.1. Logs do Sistema

O Robot-Crypt registra todas as operações no diretório `logs/` com o formato `robot-crypt-AAAAMMDD.log`. Use estes logs para:

- Verificar decisões de trading
- Identificar erros de execução
- Analisar desempenho e comportamento

```bash
# Ver logs em tempo real
tail -f logs/robot-crypt-$(date +%Y%m%d).log

# Filtrar apenas operações de compra
grep "Comprando" logs/robot-crypt-*.log

# Filtrar apenas operações de venda
grep "Vendendo" logs/robot-crypt-*.log
```

### 1.2. Estado da Aplicação

O estado persistido da aplicação é salvo em `data/app_state.json` e contém:

- Posições abertas
- Histórico de operações
- Estatísticas de desempenho
- Último saldo conhecido

Este arquivo é crucial para o bot retomar suas operações após uma reinicialização.

### 1.3. Notificações Telegram

Se configurado, o bot envia alertas via Telegram para eventos importantes:

- Início e parada do bot
- Execução de compra/venda
- Atingimento de take profit/stop loss
- Erros críticos de execução

## 2. Métricas de Desempenho

Métricas principais para acompanhamento:

| Métrica | Descrição | Onde encontrar |
|---------|-----------|----------------|
| Win Rate | Percentual de operações lucrativas | Logs, app_state.json |
| Profit Factor | Relação entre lucros e perdas | Logs, app_state.json |
| Drawdown | Máxima queda do capital desde o pico | Logs, app_state.json |
| ROI | Retorno sobre investimento total | Logs, app_state.json |

## 3. Procedimentos de Verificação

### 3.1. Verificação Diária

Realize estas verificações diariamente:

1. **Verificação de Logs**:
   ```bash
   grep "ERROR" logs/robot-crypt-$(date +%Y%m%d).log
   ```

2. **Verificação de Saldo**:
   Confirme se o saldo reportado no log corresponde ao da sua conta Binance.

3. **Verificação de Estado**:
   ```bash
   cat data/app_state.json | grep "timestamp"
   ```
   Confirme que o timestamp é recente (última execução do bot).

### 3.2. Verificação Semanal

1. **Análise de Desempenho**:
   Calcule métricas semanais e compare com semanas anteriores.

2. **Verificação de Pares**:
   Avalie quais pares estão tendo melhor desempenho.

3. **Ajustes de Parâmetros**:
   Considere ajustar stop loss, take profit ou tamanho das posições.

## 4. Resolução de Problemas

### 4.1. Problemas Comuns e Soluções

| Problema | Possível Causa | Solução |
|----------|----------------|---------|
| Erro 400 da API | Par inválido ou indisponível | Verifique se os pares configurados estão disponíveis na Binance |
| Ordem rejeitada | Saldo insuficiente ou restrições | Verifique logs para detalhes e ajuste valor de trade |
| Bot parou de operar | Erro crítico ou problema de conexão | Verifique logs de erros e reinicie o bot |
| Ordens não estão sendo executadas | API key sem permissões de trading | Verifique as permissões da API key |

### 4.2. Procedimento de Emergência

Se o bot estiver realizando operações indesejadas ou errôneas:

1. **Parada Imediata**:
   ```bash
   # Encontre o processo do bot
   ps aux | grep main.py
   
   # Encerre o processo
   kill -9 [PID]
   ```

2. **Desativação Temporária da API**:
   Acesse o gerenciamento de API da Binance e desative temporariamente a API key.

3. **Análise da Causa**:
   Consulte os logs para identificar a causa do comportamento indesejado.

## 5. Monitoramento de Longo Prazo

Para análises de longo prazo, considere:

1. **Arquivo de Logs Consolidados**:
   ```bash
   cat logs/robot-crypt-*.log > logs/consolidado.log
   ```

2. **Extração de Estatísticas**:
   ```bash
   grep "Lucro realizado" logs/consolidado.log | awk '{sum+=$5} END {print "Lucro total:", sum}'
   ```

3. **Visualização de Dados**:
   Considere exportar dados de logs para ferramentas como Excel ou Python com Pandas para análises gráficas.

## 6. Backup de Dados

Regularmente faça backup de:

1. **Estado da Aplicação**:
   ```bash
   cp data/app_state.json data/app_state_$(date +%Y%m%d).json.bak
   ```

2. **Logs**:
   ```bash
   tar -czf logs_$(date +%Y%m%d).tar.gz logs/
   ```

3. **Arquivo de Configuração**:
   ```bash
   cp .env .env.$(date +%Y%m%d).bak
   ```

Esta rotina de backup é crucial para evitar perda de dados e histórico de trading.
