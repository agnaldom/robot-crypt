# BingX Trading Bot 🚀

Bot de trading automatizado para BingX utilizando futuros perpétuos USD com estratégia Harmonic Butterfly Pattern.

## 📋 Características

- **Estratégia Harmonic Butterfly**: Detecta padrões harmônicos Butterfly para identificar oportunidades de trading
- **Futuros Perpétuos USD**: Especializado em contratos futuros perpétuos
- **Gestão de Risco**: Controle rigoroso de risco com stop loss e take profit automáticos
- **Alavancagem Configurável**: Suporte para alavancagem de 1x a 125x
- **Múltiplos Símbolos**: Monitora vários pares de criptomoedas simultaneamente
- **Testnet**: Suporte completo para ambiente de teste

## 🛠️ Instalação

1. **Instale as dependências** (já incluídas no requirements.txt principal):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure as variáveis de ambiente**:
   ```bash
   cp .env.bingx.example .env
   ```

3. **Edite o arquivo `.env`** com suas credenciais:
   ```env
   BINGX_API_KEY=sua_chave_api_aqui
   BINGX_API_SECRET=seu_secret_api_aqui
   BINGX_USE_TESTNET=true
   ```

## 🔧 Configuração

### Obtendo Chaves API da BingX

1. Acesse [BingX](https://bingx.com) e crie uma conta
2. Vá para **Account** → **API Management**
3. Crie uma nova API Key com permissões de:
   - **Futures Trading**
   - **Read Account Information**
4. **IMPORTANTE**: Desabilite permissões de saque para segurança

### Configurações Disponíveis

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `BINGX_API_KEY` | Chave API da BingX | - |
| `BINGX_API_SECRET` | Secret API da BingX | - |
| `BINGX_USE_TESTNET` | Usar testnet (true/false) | true |
| `BINGX_MAX_POSITIONS` | Máximo de posições ativas | 3 |
| `BINGX_RISK_PER_TRADE` | Risco por trade (0.02 = 2%) | 0.02 |
| `BINGX_LEVERAGE` | Alavancagem (1-125) | 10 |
| `BINGX_TIMEFRAME` | Timeframe para análise | 15m |
| `BINGX_SYMBOLS` | Símbolos para trading | BTC-USDT,ETH-USDT,... |
| `BINGX_STOP_LOSS_RATIO` | Stop loss (0.02 = 2%) | 0.02 |
| `BINGX_TAKE_PROFIT_RATIO` | Take profit (0.04 = 4%) | 0.04 |

## 🚀 Uso

### 1. Teste de Configuração

Antes de executar o bot, teste suas configurações:

```bash
python test_bingx_connection.py
```

Este script irá:
- ✅ Validar configurações
- ✅ Testar conexão com BingX
- ✅ Verificar informações da conta
- ✅ Testar dados de mercado
- ✅ Verificar detecção de padrões

### 2. Execução do Bot

```bash
python bingx_bot_main.py
```

O bot irá:
1. Validar configurações
2. Conectar com BingX
3. Mostrar informações da conta
4. Executar análise inicial
5. Perguntar confirmação antes de iniciar trading

### 3. Monitoramento

Durante a execução, o bot exibe:
- 📊 Status das posições ativas
- 🔍 Padrões detectados
- 💰 Informações de P&L
- ⚠️ Alertas de risco

Para parar o bot, pressione `Ctrl+C`.

## 🦋 Estratégia Harmonic Butterfly

### O que é o Padrão Butterfly?

O padrão Harmonic Butterfly é uma formação de preço que segue proporções específicas de Fibonacci:

- **Ponto X**: Início do padrão
- **Ponto A**: Primeira retração
- **Ponto B**: Segunda retração (78.6% de XA)
- **Ponto C**: Terceira retração (38.2%-88.6% de AB)
- **Ponto D**: Ponto de entrada (127.2%-161.8% de BC)

### Como Funciona

1. **Detecção**: O bot identifica padrões Butterfly completos
2. **Entrada**: Posição aberta próximo ao ponto D
3. **Stop Loss**: Baseado na estrutura do padrão
4. **Take Profit**: Múltiplo do risco assumido

### Vantagens

- **Precisão**: Padrões baseados em matemática Fibonacci
- **Risco Controlado**: Stop loss bem definido
- **Múltiplos Timeframes**: Funciona em vários períodos
- **Automação**: Detecção e execução automática

## 📊 Gestão de Risco

### Características de Segurança

- **Limite de Posições**: Máximo 3 posições simultâneas (padrão)
- **Risco por Trade**: 2% do capital por operação (padrão)
- **Stop Loss**: 2% de perda máxima por trade (padrão)
- **Take Profit**: 4% de lucro alvo por trade (padrão)
- **Alavancagem**: 10x (padrão, ajustável)

### Cálculo de Posição

```python
saldo_conta = 1000  # USDT
risco_por_trade = 0.02  # 2%
alavancagem = 10

valor_risco = saldo_conta * risco_por_trade  # 20 USDT
tamanho_posicao = valor_risco * alavancagem  # 200 USDT em posição
```

## 🔍 Monitoramento e Logs

### Tipos de Log

- **INFO**: Operações normais
- **WARNING**: Situações que requerem atenção
- **ERROR**: Erros que impedem operações

### Exemplo de Saída

```
🚀 Iniciando BingX Trading Bot...
✅ Configuração validada com sucesso
✅ Conectado ao BingX - Server Time: 1641234567890
💰 Saldo da conta: 1000.0 USDT
📊 Configurações da estratégia:
  - Símbolos: ['BTC-USDT', 'ETH-USDT', 'BNB-USDT']
  - Timeframe: 15m
  - Leverage: 10x
  - Risco por trade: 2.0%
🔍 Executando análise inicial...
  - BTC-USDT: 0 padrões encontrados
  - ETH-USDT: 1 padrões encontrados
  - BNB-USDT: 0 padrões encontrados
```

## 📈 Exemplo de Trading

### Cenário: Detecção de Padrão Butterfly

```
🦋 Padrão Butterfly detectado em BTC-USDT:
  - Ponto X: 45,000
  - Ponto A: 47,000
  - Ponto B: 46,000
  - Ponto C: 46,800
  - Ponto D: 45,200 (entrada)

📊 Sinal de entrada:
  - Direção: LONG
  - Preço entrada: 45,200
  - Stop Loss: 44,296 (2% abaixo)
  - Take Profit: 47,008 (4% acima)
  - Tamanho posição: 0.44 BTC
```

## ⚠️ Avisos Importantes

### Riscos

- **Mercado Volátil**: Criptomoedas são altamente voláteis
- **Alavancagem**: Pode amplificar tanto lucros quanto perdas
- **Padrões Falsos**: Nem todos os padrões resultam em lucro
- **Risco de Liquidação**: Posições podem ser liquidadas

### Recomendações

1. **Comece com testnet**: Teste sempre antes de usar dinheiro real
2. **Capital de Risco**: Use apenas capital que pode perder
3. **Monitore Constantemente**: Acompanhe o desempenho do bot
4. **Ajuste Parâmetros**: Otimize baseado nos resultados
5. **Tenha Stop Loss**: Nunca desabilite proteções de risco

## 🛡️ Segurança

### Boas Práticas

- **Chaves API**: Mantenha suas chaves seguras
- **Permissões Mínimas**: Apenas trading e leitura
- **Restrições IP**: Configure IP whitelisting na BingX
- **Ambiente Seguro**: Execute em ambiente controlado
- **Backups**: Mantenha backups das configurações

### Testnet

Sempre teste com testnet antes de usar dinheiro real:

```env
BINGX_USE_TESTNET=true
```

## 🐛 Solução de Problemas

### Erros Comuns

1. **Erro de Autenticação**:
   - Verifique API key e secret
   - Confirme permissões da API
   - Teste com testnet primeiro

2. **Erro de Conexão**:
   - Verifique conexão com internet
   - Confirme status da API da BingX
   - Verifique firewall/proxy

3. **Erro de Saldo**:
   - Confirme saldo disponível
   - Verifique se está usando testnet
   - Reduza tamanho das posições

### Logs de Debug

Para mais informações de debug, ajuste o nível de log:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Suporte

Para problemas técnicos:
1. Verifique os logs do bot
2. Execute o teste de configuração
3. Consulte a documentação da API BingX
4. Verifique issues no repositório

## 📝 Changelog

### v1.0.0
- ✅ Implementação inicial do cliente BingX
- ✅ Estratégia Harmonic Butterfly
- ✅ Gestão de risco automática
- ✅ Suporte para testnet
- ✅ Configuração via variáveis de ambiente

---

**Disclaimer**: Este bot é fornecido apenas para fins educacionais. Trading automatizado envolve riscos significativos. Nunca invista mais do que pode perder.
