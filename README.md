# Bot de Trading para Criptomoedas em Lançamento

Este bot automatiza a compra de novas criptomoedas listadas na Binance e realiza a venda quando atingir os critérios definidos.

## Funcionalidades

- Monitora anúncios da Binance para detectar novos lançamentos
- Compra automaticamente após 1 minuto da listagem
- Vende com base em critérios de Take Profit (10%), Stop Loss (5%) ou tempo máximo (24h)
- Envia notificações pelo Telegram
- Executa 24/7

## Requisitos

- Python 3.7+
- Conta na Binance com API Key e Secret
- Bot do Telegram para notificações

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/robot-crypt.git
cd robot-crypt
```

2. Crie e ative um ambiente virtual:

   **No Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   **No macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Você saberá que o ambiente virtual está ativo quando o nome do ambiente aparecer no início da linha de comando, como `(venv)`.

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure suas credenciais:
   - Edite o arquivo `config.py` e adicione suas chaves da API da Binance
   - Configure seu token e chat_id do Telegram

## Uso

Execute o bot com o comando:
```bash
python main.py
```

Para executar em segundo plano:
```bash
nohup python main.py > output.log 2>&1 &
```

## Configurações

Você pode ajustar os parâmetros de trading no arquivo `config.py`:
- `TRADE_AMOUNT`: Valor por operação
- `TAKE_PROFIT_PERCENTAGE`: Percentual de lucro para venda
- `STOP_LOSS_PERCENTAGE`: Percentual de perda para venda
- `MAX_HOLD_TIME`: Tempo máximo de hold em segundos
- `ENTRY_DELAY`: Tempo de espera após a listagem

## Segurança

⚠️ **ATENÇÃO**: Nunca compartilhe suas chaves de API ou arquivos de configuração.

## Aviso Legal

Este bot é fornecido apenas para fins educacionais. Opere por sua conta e risco. Criptomoedas são voláteis e você pode perder dinheiro.
