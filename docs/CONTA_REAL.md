# Guia de Configuração para Conta Real

Este guia descreve como configurar e utilizar o Robot-Crypt com sua conta real da Binance.

## 1. Pré-requisitos

Antes de começar, você precisará:

- Uma conta na Binance
- API Key e Secret da Binance com permissões de leitura e trading
- Saldo em uma ou mais das moedas suportadas (BNB, USDT, BRL)
- (Opcional) Bot do Telegram para receber notificações

## 2. Criar API Keys na Binance

1. Acesse [Binance API Management](https://www.binance.com/pt-BR/my/settings/api-management)
2. Clique em "Criar API"
3. Complete a verificação de segurança
4. Configure as restrições de segurança:
   - Ative a autenticação em 2 fatores
   - Restrinja o acesso por IP (recomendado)
   - Desative saques (muito importante para segurança)
   - Permita apenas Trading e Leitura
5. Anote a API Key e Secret Key

## 3. Configuração do Ambiente

### 3.1. Usando o script de configuração

O modo mais fácil é usar o script `setup_real.sh`:

```bash
./setup_real.sh
```

O script solicitará suas credenciais e configurará o ambiente adequadamente.

### 3.2. Configuração manual do arquivo .env

Alternativamente, você pode configurar manualmente copiando o arquivo `.env.example.real`:

```bash
cp .env.example.real .env
```

E edite o arquivo `.env` com suas informações:

```bash
# Credenciais da API Binance
BINANCE_API_KEY=SUA_API_KEY_AQUI
BINANCE_API_SECRET=SUA_API_SECRET_AQUI

# Configuração do ambiente
SIMULATION_MODE=false
USE_TESTNET=false

# Configurações do Telegram
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_AQUI
TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI

# Configurações de trading
TRADE_AMOUNT=0.01          # Valor em BNB por operação
TAKE_PROFIT_PERCENTAGE=1.5  # Alvo de lucro em porcentagem
STOP_LOSS_PERCENTAGE=0.8   # Limite de perda em porcentagem
MAX_HOLD_TIME=48           # Tempo máximo de retenção em horas
CHECK_INTERVAL=300         # Intervalo entre verificações em segundos

# Configurações de moedas
PRIMARY_COIN=BNB           # Sua moeda principal para trading
```

## 4. Configuração do Telegram (Opcional)

Para receber notificações via Telegram:

1. Crie um bot no Telegram conversando com [@BotFather](https://t.me/botfather)
2. Use o comando `/newbot` e siga as instruções
3. Anote o token do bot fornecido
4. Crie um grupo ou canal onde deseja receber as notificações
5. Adicione o bot ao grupo/canal
6. Obtenha o Chat ID usando o bot [@getidsbot](https://t.me/getidsbot)
7. Configure as variáveis `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no arquivo `.env`

## 5. Configurações de Trading

As configurações padrão são seguras para iniciantes, mas você pode ajustar conforme seu perfil de risco:

### 5.1. Configurações de Risco

- `RISK_PER_TRADE`: Porcentagem do capital alocado por operação (recomendado: 1-2%)
- `STOP_LOSS_PERCENTAGE`: Limite de perda (recomendado: 0.8-1.5%)
- `MAX_TRADES`: Número máximo de operações simultâneas

### 5.2. Configurações de Lucro

- `TAKE_PROFIT_PERCENTAGE`: Alvo de lucro (recomendado começar com 1.5-2%)
- `MAX_HOLD_TIME`: Tempo máximo para manter uma posição aberta (em horas)

### 5.3. Configurações Gerais

- `CHECK_INTERVAL`: Tempo entre verificações de mercado (em segundos)
- `TRADING_PAIRS`: Lista de pares a serem negociados (separados por vírgula)

## 6. Execução do Bot

### 6.1. Execução Local

```bash
python main.py
```

### 6.2. Execução com Docker

```bash
docker-compose up -d
```

Ou, alternativamente:

```bash
./docker-run.sh
```

## 7. Monitoramento

### 7.1. Logs

Os logs são salvos no diretório `logs/` com o formato `robot-crypt-YYYYMMDD.log`:

```bash
tail -f logs/robot-crypt-$(date +%Y%m%d).log
```

### 7.2. Notificações Telegram

Se configurado, você receberá notificações sobre:
- Início do bot
- Análises de mercado
- Ordens executadas (compras e vendas)
- Lucros e perdas
- Erros e alertas
- Relatórios periódicos de desempenho

### 7.3. Estado do Bot

O estado é salvo no diretório `data/`:
- `app_state.json`: Estado atual
- `app_state_final.json`: Estado salvo ao encerrar

## 8. Considerações Importantes para Conta Real

### 8.1. Gerenciamento de Risco

- Comece com valores pequenos para testar
- Aumente gradualmente conforme ganha confiança
- Nunca invista mais do que pode perder
- Monitore as primeiras operações de perto

### 8.2. Uso de BNB para Taxas

O bot está configurado para usar BNB para pagar taxas (desconto de 15-25%). Certifique-se de manter um pequeno saldo de BNB para taxas, mesmo que esteja operando com outras moedas.

### 8.3. Compatibilidade de Pares

Nem todos os pares estão disponíveis em todas as contas ou regiões. O bot detectará automaticamente pares inválidos e os removerá da lista.

### 8.4. Seleção Automática de Estratégia

- Capital < R$300: Estratégia de Scalping (operações mais rápidas)
- Capital >= R$300: Estratégia de Swing Trading (operações mais longas)

## 9. Solução de Problemas Comuns

### 9.1. Erro de Autenticação (401)

- Verifique se a API Key e Secret estão corretas
- Confirme se as permissões apropriadas estão habilitadas
- Verifique se o IP do seu servidor está na lista de permissões

### 9.2. Erro 400 (Bad Request)

- Geralmente ocorre quando um par de negociação não está disponível
- O bot removerá automaticamente esse par da lista

### 9.3. Erro 429 (Rate Limit)

- O bot está fazendo muitas requisições
- Aumente o `CHECK_INTERVAL` para reduzir a frequência

### 9.4. Notificações Telegram não funcionando

- Verifique se o token do bot está correto
- Confirme se o chat ID está correto (com o sinal de menos para grupos)
- Verifique se o bot tem permissão para enviar mensagens no grupo

## 10. Backups e Segurança

- Mantenha suas API Keys seguras
- Nunca compartilhe o arquivo `.env`
- Faça backups regulares do diretório `data/`
- Considere usar secret managers em ambientes de produção

Lembre-se: trading envolve riscos. Monitore o bot regularmente e ajuste as configurações conforme necessário baseado em seu desempenho.
