# Deploy no Railway - Guia Rápido

Este documento descreve como implantar o Robot-Crypt no Railway, especificamente na região de Singapura (Southeast Asia) para evitar restrições regionais da Binance.

## Configuração da Região

Para garantir que o bot seja implantado em Singapura, execute:

```bash
# Configure a região para Singapura
railway variables set RAILWAY_REGION=asia-southeast1-eqsg3a
```

## Deploy do Projeto

```bash
# Vincular o projeto (se ainda não estiver vinculado)
railway link

# Implante o projeto
railway up
```

## Variáveis de Ambiente Necessárias

Configure estas variáveis no painel do Railway:

1. **Credenciais da Binance**:
   - `BINANCE_API_KEY` - Sua chave API da Binance
   - `BINANCE_API_SECRET` - Seu segredo API da Binance
   - `USE_TESTNET` - "false" para usar a API de produção

2. **Configuração do Telegram**:
   - `TELEGRAM_BOT_TOKEN` - Token do seu bot do Telegram
   - `TELEGRAM_CHAT_ID` - ID do chat para notificações

3. **Configurações de Trading**:
   - `TRADING_PAIRS` - Lista de pares para negociação (ex: "BTCUSDT,ETHUSDT")
   - `TRADE_AMOUNT` - Valor das ordens (opcional)
   - `TAKE_PROFIT_PERCENTAGE` - Porcentagem de lucro (opcional)
   - `STOP_LOSS_PERCENTAGE` - Porcentagem de stop loss (opcional)

## Monitoramento

Para monitorar os logs do bot:

```bash
railway logs
```

## Solução de Problemas

Se você ainda encontrar erros 451 mesmo sendo hospedado em Singapura:

1. Verifique se a região realmente é Singapura:
   ```bash
   railway variables get RAILWAY_REGION
   ```

2. Se necessário, reinstale com o proxy Tor:
   ```bash
   # Desvincular o projeto atual
   railway unlink
   
   # Vincular novamente e forçar a região
   railway link
   railway variables set RAILWAY_REGION=asia-southeast1-eqsg3a
   ```

3. Caso precise do proxy Tor mesmo em Singapura, restaure as alterações anteriores do Dockerfile e start.sh
