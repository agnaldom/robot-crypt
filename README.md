# Robot-Crypt 🤖💹

Bot de negociação para crescimento na Binance a partir de R$100, com foco em baixo risco e progressão sustentável.

![Robot-Crypt Logo](https://img.shields.io/badge/Robot--Crypt-Trading%20Bot-blue)
![Version](https://img.shields.io/badge/versão-2.0.0-green)
![Tests](https://img.shields.io/badge/testes-passing-success)

## Visão Geral

O Robot-Crypt é um bot de trading cripto focado em crescimento sustentável e baixo risco. 
Ele implementa uma estratégia progressiva que evolui de acordo com o crescimento do capital:

- Começa com **R$100** usando técnicas de scalping em ativos líquidos
- Evolui para swing trading à medida que o capital cresce
- Implementa rígido controle de risco e gestão de capital
- Envia alertas e relatórios via Telegram

## Plano Estratégico

O bot implementa o seguinte plano estratégico progressivo:

### Fase 1: Educação & Preparação (Semanas 1-2)
- Estudar análise técnica usando TradingView, Binance Academy
- Dominar a Binance com Testnet e simulações
- Analisar mercados com CoinGecko e CryptoPanic

### Fase 2: Operações Iniciais (R$100 → R$300)
- **Estratégia**: Scalping de Baixo Risco
- **Pares**: BTC/BRL, ETH/BRL (alta liquidez)
- **Entradas**: Compra quando o ativo cai 1.5% em 1h e está próximo do suporte diário
- **Alvos**: Ganhos de 1-3% por operação (descontando taxas)
- **Stop Loss**: 0.5% abaixo do preço de entrada
- **Gestão de Risco**: Máximo 1% do capital em risco por operação

### Fase 3: Aceleração (R$300 → R$1.000)
- **Estratégia**: Swing Trading em Altcoins
- **Pares**: Criptomoedas < R$1.00 (SHIB/BRL, FLOKI/BRL, DOGE/BRL, etc.)
- **Entradas**: Volume 30% acima da média diária ou novas listagens
- **Alvos**: 7-10% de lucro (descontando taxas)
- **Stop Loss**: 3% abaixo do preço de entrada
- **Saída por Tempo**: Vende após 48h independente do resultado
- **Alocação**: Máximo 5% do capital por posição

### Fase 4: Otimização (R$1.000+)
Esta fase está planejada para implementação futura e incluirá:

| Tática | Retorno Estimado | Risco |
|--------|------------------|-------|
| Staking | 5-10%/ano | Baixo |
| Launchpads | 10-50% por IEO | Médio |
| Bot Trading | 0.5-2% ao dia | Controlado |

## Regras de Ouro Implementadas

O bot implementa as seguintes regras rígidas de gestão de risco:

- **Risco Controlado**: Nunca arrisca >5% do capital em uma única operação
- **Cálculo de Taxas**: Contabiliza corretamente as taxas (0.1% spot na Binance) antes de operar
- **Limite de Negociações**: Máximo de 3 trades por dia para evitar over-trading
- **Parada após Perdas**: Para operações após 2 prejuízos consecutivos
- **Gestão de Exposição**: Cálculo de posição proporcional ao risco tolerado
- **Stop Loss Automático**: Proteção contra movimentos adversos de preço

### Fórmula de Risco

```python
# Cálculo do valor de entrada por operação
capital = 100  # R$
risco_por_operacao = 1  # 1%
entrada = capital * (risco_por_operacao / 100)  # R$1

# Cálculo das taxas
custo_total = (valor * 0.001) * 2  # 0.1% na compra + 0.1% na venda
```

### Critérios Técnicos

O bot implementa critérios técnicos específicos para cada fase:

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/robot-crypt.git
cd robot-crypt
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure suas chaves de API da Binance:
```
export BINANCE_API_KEY="sua_api_key"
export BINANCE_API_SECRET="seu_api_secret"
```

## Performance e Métricas

O Robot-Crypt gera relatórios diários de performance, monitorando:

- Crescimento do capital (valores absolutos e percentuais)
- Taxa de acertos (win rate)
- Lucro/prejuízo médio por operação
- Tempo médio de posições abertas
- Desempenho por par de moedas

O bot também rastreia métricas de mercado para melhorar a tomada de decisões:
- Variação de volume (24h)
- Níveis de suporte e resistência
- Tendências de curto e médio prazo

## Notificações e Alertas

O bot pode enviar notificações via Telegram, incluindo:

- Alertas de compra/venda em tempo real
- Relatórios diários de desempenho
- Avisos de movimentos significativos de mercado
- Avisos de erros ou problemas operacionais

## Uso

### Configuração rápida

Para uma instalação completa com todas as dependências:
```bash
./setup.sh
```

### Configurando suas chaves API

Para usar com sua conta real ou testnet da Binance:

1. Crie um arquivo `.env` na raiz do projeto
2. Adicione suas chaves de API:

```
BINANCE_API_KEY="sua_api_key"
BINANCE_API_SECRET="seu_api_secret"
USE_TESTNET=true  # Use 'false' para operar com dinheiro real
```

3. Para configurar notificações via Telegram:

```
TELEGRAM_BOT_TOKEN="seu_token_do_bot"
TELEGRAM_CHAT_ID="seu_chat_id"
```

### Modos de execução

O bot pode ser executado em três modos:

1. **Modo de Simulação** (recomendado para testes iniciais)
```bash
./setup_simulation.sh  # Configura o modo de simulação
python main.py         # Executa o bot
```

2. **Modo Testnet** (usa a API da Binance, mas com dinheiro virtual)
```bash
./setup_testnet.sh     # Guia para configurar suas credenciais da testnet
python main.py         # Executa o bot
```

3. **Modo Real** (CUIDADO: Usa dinheiro real!)
```bash
./setup_real.sh        # Configura para uso com dinheiro real
python main.py         # Executa o bot
```

### Executando com Docker (Recomendado)

Para executar o bot com Docker (sem precisar instalar dependências no host):

```bash
# Torne o script executável
chmod +x docker-run.sh

# Execute o script e siga as instruções
./docker-run.sh
```

Para mais detalhes sobre Docker, consulte [DOCKER.md](DOCKER.md).

## Exemplo Prático

### Ciclo de Operação na Fase 2 (Scalping)

```
Dia 1:
- Capital inicial: R$100
- Bot detecta BTC/BRL caindo 1,8% em 1h e próximo do suporte
- Compra 0.00066 BTC a R$150.000 (invest. R$99 + R$0.10 taxa)
- 2h depois, BTC sobe 2.2%
- Bot vende a R$153.300 (R$101.18 - R$0.10 taxa)
- Lucro líquido: R$2.08 (+2.08%)

Dia 3:
- Capital: R$102.08
- Bot detecta ETH/BRL caindo 1,7% e próximo do suporte
- Compra 0.012 ETH a R$8.500 (invest. R$102 + R$0.10 taxa)
- 4h depois, ETH sobe 1.9%
- Bot vende a R$8.661,50 (R$103.94 - R$0.10 taxa)
- Lucro líquido: R$1.84 (+1.80%)

Após 2 semanas:
- 8-10 operações bem sucedidas
- Capital estimado: ~R$115
- Win rate: ~70%
```

### Ciclo de Operação na Fase 3 (Swing Trading)

```
Semana 3 (Capital: R$320):
- Bot detecta DOGE com volume 35% acima da média
- Compra 450 DOGE a R$0.70 (invest. R$315 + R$0.32 taxa)
- 30h depois, DOGE sobe 9%
- Bot vende a R$0.763 (R$343.35 - R$0.34 taxa)
- Lucro líquido: R$27.69 (+8.7%)

Semana 5 (Capital: R$520):
- Bot detecta SHIB listado em nova exchange
- Compra 60.000 SHIB a R$0.0085 (invest. R$510 + R$0.51 taxa)
- 48h depois (tempo máximo), SHIB subiu 12%
- Bot vende a R$0.00952 (R$571.20 - R$0.57 taxa)
- Lucro líquido: R$60.12 (+11.7%)

## Considerações de Segurança

### Proteção de Chaves de API

- **NUNCA** compartilhe suas chaves de API
- Configure permissões mínimas necessárias (apenas leitura e trading)
- **DESABILITE** permissões de saque na Binance
- Utilize restrições de IP quando possível

### Gestão de Risco

- Comece com um capital que você pode perder totalmente
- Não deposite fundos adicionais até compreender o comportamento do bot
- Monitore regularmente o desempenho
- Verifique a integridade do bot após atualizações de mercado
- Realize backups regulares do histórico de operações

### Riscos do Mercado Cripto

- Mercados cripto são voláteis por natureza
- Nenhum bot garante lucros consistentes
- Performance passada não garante resultados futuros
- Esteja preparado para perdas temporárias
- O bot implementa proteções, mas não elimina todos os riscos

## Disclaimer

Este bot é fornecido apenas para fins educacionais e de pesquisa. Opere por sua conta e risco. Os desenvolvedores não são responsáveis por perdas financeiras resultantes do uso deste software.

"O segredo para investir em cripto não está em tentar ficar rico rapidamente, mas em construir consistentemente ao longo do tempo com disciplina e gestão de risco." - Adaptado de disciplinas tradicionais de investimento
```
```

### Notificações via Telegram

Para receber notificações sobre operações via Telegram:
1. Crie um bot no Telegram usando o @BotFather
2. Adicione as seguintes variáveis no arquivo .env:
```
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

## Aviso de Risco

Este bot é uma ferramenta educacional e não garante lucros. Criptomoedas são investimentos de alto risco. Nunca invista mais do que pode perder.

## Exemplos Práticos

### Simulação Rápida

Para testar o bot rapidamente sem configurar credenciais:

```bash
# Instala dependências e configura ambiente
./setup.sh

# Ativa modo de simulação
./setup_simulation.sh

# Executa o bot
python main.py
```

### Usando a Testnet da Binance

Para operar com dinheiro virtual na Testnet:

```bash
# Instala dependências e configura ambiente
./setup.sh

# Configura credenciais Testnet
./setup_testnet.sh

# Executa o bot
python main.py
```

### Operação em Produção

Para operar com dinheiro real (CUIDADO):

1. Edite o arquivo `.env`:
```bash
# Credenciais reais da Binance
BINANCE_API_KEY=sua_chave_real
BINANCE_API_SECRET=seu_secret_real
USE_TESTNET=false
SIMULATION_MODE=false
```

2. Execute o bot:
```bash
python main.py
```

## Troubleshooting

### Erros de Autenticação (401)

Se você receber erros de autenticação:

1. Verifique se suas credenciais estão corretas no arquivo `.env`
2. Se estiver usando testnet, garanta que está usando as credenciais específicas da testnet
3. Para testnet, você pode gerar novas credenciais em https://testnet.binance.vision/

### Problemas com Simulação

Se a simulação não estiver funcionando corretamente:

1. Verifique se `SIMULATION_MODE=true` no seu arquivo `.env`
2. Execute `./setup_simulation.sh` para resetar a configuração de simulação

### Testes Automatizados

Execute os testes para verificar se tudo está funcionando como esperado:

```bash
python run_tests.py
```

## Executando os Testes

O projeto inclui testes automatizados para validar as funcionalidades principais:

```bash
# Executa todos os testes
python run_tests.py

# Executa testes específicos
python -m unittest tests.test_simulator
python -m unittest tests.test_strategy
```

## Licença

MIT
