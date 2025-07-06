#!/usr/bin/env python3
"""
Módulo de utilitários gerais para Robot-Crypt
"""

def format_symbol(symbol):
    """
    Formata um símbolo de trading para o formato correto da API Binance
    
    Args:
        symbol (str or list): Símbolo ou lista de símbolos
        
    Returns:
        str: Símbolo formatado corretamente (ex: 'SHIBUSDT')
    """
    # Se for uma lista, pega o primeiro elemento
    if isinstance(symbol, list):
        symbol = symbol[0] if symbol else ""
    
    # Converte para string se não for
    symbol = str(symbol)
    
    # Remove colchetes de strings que representam listas
    symbol = symbol.replace('[', '').replace(']', '')
    
    # Remove aspas, barras e espaços
    symbol = symbol.replace('/', '').replace('"', '').replace("'", '').strip()
    
    # Remove caracteres de escape URL se presentes
    symbol = symbol.replace('%22', '')  # Remove aspas URL-encoded
    symbol = symbol.replace('%27', '')  # Remove aspas simples URL-encoded
    
    return symbol.upper()
import os
import logging
import random
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

def setup_logger(log_level=logging.INFO):
    """Configura e retorna logger com formatação apropriada"""
    # Cria diretório de logs se não existir
    # Usa o diretório logs/ dentro do projeto, não no home do usuário
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Nome do arquivo de log com timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"robot-crypt-{timestamp}.log"
    
    # Configura logger
    logger = logging.getLogger("robot-crypt")
    logger.setLevel(log_level)
    
    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers = []
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formato dos logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log informativo sobre onde os logs estão sendo salvos
    logger.info(f"Logs sendo salvos em: {log_file}")
    
    return logger

def calculate_fees(value, fee_rate=0.001):
    """Calcula taxas da Binance para um valor"""
    return value * fee_rate
    
def calculate_profit(entry_price, exit_price, quantity, fee_rate=0.001):
    """Calcula o lucro líquido de uma operação após taxas"""
    # Valor bruto de entrada e saída
    entry_value = entry_price * quantity
    exit_value = exit_price * quantity
    
    # Cálculo de taxas (entrada e saída)
    entry_fee = calculate_fees(entry_value, fee_rate)
    exit_fee = calculate_fees(exit_value, fee_rate)
    total_fees = entry_fee + exit_fee
    
    # Lucro bruto e líquido
    gross_profit = exit_value - entry_value
    net_profit = gross_profit - total_fees
    
    # Percentual de lucro após taxas
    profit_percentage = net_profit / entry_value
    
    return {
        'entry_value': entry_value,
        'exit_value': exit_value,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'total_fees': total_fees,
        'profit_percentage': profit_percentage
    }

def track_portfolio_performance(trades_history, initial_capital=100.0):
    """Acompanha performance do portfólio ao longo do tempo"""
    capital = initial_capital
    performance = []
    
    # Ordena trades por data
    sorted_trades = sorted(trades_history, key=lambda x: x['timestamp'])
    
    for trade in sorted_trades:
        # Atualiza capital após cada trade
        capital += trade['net_profit']
        
        # Registra desempenho
        performance.append({
            'timestamp': trade['timestamp'],
            'symbol': trade['symbol'],
            'action': trade['action'],
            'profit': trade['net_profit'],
            'capital': capital,
            'growth': (capital / initial_capital - 1) * 100  # Crescimento percentual
        })
    
    return performance

def calculate_bnb_allocation(bnb_balance, total_balance_usd, risk_factor=0.025):
    """Calcula a alocação ideal de BNB para cada operação
    
    Parameters:
    -----------
    bnb_balance : float
        Saldo de BNB disponível
    total_balance_usd : float
        Valor total da carteira em USD
    risk_factor : float
        Fator de risco (percentual do saldo total a ser alocado por operação)
        
    Returns:
    --------
    dict
        Dicionário com informações sobre alocação recomendada de BNB
    """
    # Valor aproximado de BNB em USD (assumindo preço médio de $450)
    bnb_value_usd = bnb_balance * 450.0
    
    # Percentual de BNB no portfólio total
    bnb_portfolio_percent = (bnb_value_usd / total_balance_usd) * 100 if total_balance_usd > 0 else 0
    
    # Para saldos pequenos (menos de 0.05 BNB), usamos uma abordagem mais conservadora
    if bnb_balance < 0.05:
        # Nunca mais que 15% do saldo de BNB disponível para carteiras pequenas
        max_allocation_percent = 15.0
    else:
        # Para saldos maiores, podemos usar até 30%
        max_allocation_percent = 30.0
        
    max_allocation_bnb = bnb_balance * (max_allocation_percent / 100)
    
    # Valor a ser alocado por operação com base no risk_factor
    risk_allocation_usd = total_balance_usd * risk_factor
    risk_allocation_bnb = risk_allocation_usd / 450.0  # Conversão para BNB
    
    # Alocação recomendada é o menor valor entre o máximo seguro e o risco calculado
    recommended_allocation_bnb = min(max_allocation_bnb, risk_allocation_bnb)
    
    # Define um mínimo apropriado baseado no saldo total
    if bnb_balance < 0.035:
        # Para saldos muito pequenos (<0.035 BNB), usamos um mínimo de 0.001 BNB
        # Isso é adequado para o saldo informado de 0.0310868 BNB
        min_allocation = 0.001
    elif bnb_balance < 0.05:
        # Para saldos pequenos (<0.05 BNB), usamos um mínimo de 0.002 BNB (~$0.90)
        min_allocation = 0.002
    elif bnb_balance < 0.1:
        # Para saldos pequenos (<0.1 BNB), usamos um mínimo de 0.005 BNB (~$2.25)
        min_allocation = 0.005
    else:
        # Para saldos maiores, podemos usar um mínimo de 0.01 BNB (~$4.50)
        min_allocation = 0.01
        
    # Se a alocação recomendada for menor que o mínimo, usamos o mínimo
    # desde que isso não represente mais de 20% do saldo total
    if recommended_allocation_bnb < min_allocation and min_allocation <= bnb_balance * 0.2:
        recommended_allocation_bnb = min_allocation
    
    return {
        'bnb_balance': bnb_balance,
        'bnb_value_usd': bnb_value_usd,
        'bnb_portfolio_percent': bnb_portfolio_percent,
        'max_allocation_bnb': max_allocation_bnb,
        'recommended_allocation_bnb': recommended_allocation_bnb,
        'recommended_allocation_percent': (recommended_allocation_bnb / bnb_balance) * 100 if bnb_balance > 0 else 0
    }

def filtrar_pares_por_liquidez(pares, binance_api=None, min_volume_24h=100000):
    """Filtra pares de trading por liquidez mínima
    
    Args:
        pares (list): Lista de pares para filtrar
        binance_api (BinanceAPI, optional): Instância da API da Binance
        min_volume_24h (float): Volume mínimo em 24h
        
    Returns:
        list: Lista de pares que atendem ao critério de liquidez
    """
    try:
        logger = logging.getLogger("robot-crypt")
        pares_filtrados = []
        
        for par in pares:
            try:
                # Se não temos API, assumimos que todos os pares são válidos
                if not binance_api:
                    pares_filtrados.append(par)
                    continue
                    
                # Obtém estatísticas do ticker para verificar volume
                symbol = par.replace('/', '')
                ticker = binance_api.get_24hr_ticker(symbol)
                
                if ticker and 'volume' in ticker:
                    volume_24h = float(ticker['volume'])
                    if volume_24h >= min_volume_24h:
                        pares_filtrados.append(par)
                        logger.debug(f"Par {par} incluído - Volume 24h: {volume_24h:,.0f}")
                    else:
                        logger.debug(f"Par {par} filtrado - Volume 24h baixo: {volume_24h:,.0f}")
                else:
                    # Se não conseguir obter dados, inclui o par por segurança
                    pares_filtrados.append(par)
                    logger.warning(f"Não foi possível obter volume para {par}, incluindo por segurança")
                    
            except Exception as e:
                logger.warning(f"Erro ao verificar liquidez de {par}: {str(e)}")
                # Em caso de erro, inclui o par para não bloquear o trading
                pares_filtrados.append(par)
        
        logger.info(f"Filtro de liquidez: {len(pares_filtrados)}/{len(pares)} pares aprovados")
        return pares_filtrados
        
    except Exception as e:
        logger = logging.getLogger("robot-crypt")
        logger.error(f"Erro no filtro de liquidez: {str(e)}")
        # Em caso de erro, retorna todos os pares
        return pares


def save_state(state_data, filename="app_state.json"):
    """Salva o estado atual da aplicação em um arquivo JSON
    
    Parameters:
    -----------
    state_data : dict
        Dicionário com os dados que devem ser salvos
    filename : str
        Nome do arquivo onde os dados serão salvos
        
    Returns:
    --------
    bool
        True se salvo com sucesso, False caso contrário
    """
    try:
        # Cria o diretório de dados se não existir
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True, parents=True)
        
        # Caminho completo do arquivo
        file_path = data_dir / filename
        
        # Adiciona timestamp ao estado
        state_data['timestamp'] = datetime.now().isoformat()
        
        # Função para converter objetos datetime para string ISO
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Pré-processamento dos dados para lidar com objetos datetime
        processed_data = json.loads(json.dumps(state_data, default=convert_datetime))
        
        # Salva os dados em formato JSON
        with open(file_path, 'w') as f:
            json.dump(processed_data, f, indent=4)
            
        logger = logging.getLogger("robot-crypt")
        logger.info(f"Estado salvo em: {file_path}")
        return True
    except Exception as e:
        logger = logging.getLogger("robot-crypt")
        logger.error(f"Erro ao salvar estado: {str(e)}")
        return False

def load_state(filename="app_state.json"):
    """Carrega o estado da aplicação de um arquivo JSON
    
    Parameters:
    -----------
    filename : str
        Nome do arquivo de onde os dados serão carregados
        
    Returns:
    --------
    dict ou None
        Dicionário com os dados carregados ou None se o arquivo não existir ou houver erro
    """
    try:
        # Caminho do arquivo
        data_dir = Path(__file__).parent / "data"
        file_path = data_dir / filename
        
        # Verifica se o arquivo existe
        if not file_path.exists():
            logger = logging.getLogger("robot-crypt")
            logger.info(f"Arquivo de estado não encontrado: {file_path}")
            return None
        
        # Carrega os dados do arquivo JSON
        with open(file_path, 'r') as f:
            state_data = json.load(f)
            
        logger = logging.getLogger("robot-crypt")
        logger.info(f"Estado carregado de: {file_path} (timestamp: {state_data.get('timestamp', 'desconhecido')})")
        return state_data
    except Exception as e:
        logger = logging.getLogger("robot-crypt")
        logger.error(f"Erro ao carregar estado: {str(e)}")
        return None

class BinanceSimulator:
    """Classe para simular a API da Binance para testes"""
    
    def __init__(self):
        """Inicializa o simulador"""
        self.logger = logging.getLogger("robot-crypt")
        self.logger.info("Inicializando simulador da Binance")
        
        # Dados simulados
        self.simulated_balance = {
            "USDT": 100.0,
            "BTC": 0.001,
            "ETH": 0.01,
            "BRL": 500.0,
            "BNB": 1.5,
        }
        
        # Armazena ordens simuladas
        self.orders = {}
        self.next_order_id = 1000
        
        # Preços base simulados
        self.base_prices = {
            "BTCBRL": 150000.0,
            "ETHBRL": 8500.0,
            "SHIBUSDT": 0.00001,
            "FLOKIUSDT": 0.00002,
            "BTCUSDT": 30000.0,
            "ETHUSDT": 1700.0,
            "BNBUSDT": 450.0,
            "BNBBTC": 0.015,
            "BNBBRL": 2250.0,
        }
    
    def test_connection(self):
        """Simula teste de conexão"""
        self.logger.info("Simulando teste de conexão - sempre retorna sucesso")
        time.sleep(0.5)  # Simula latência da rede
        return True
    
    def get_account_info(self):
        """Retorna informações simuladas da conta"""
        self.logger.info("Retornando informações simuladas da conta")
        
        # Formata os dados no mesmo formato que a API da Binance
        balances = []
        for asset, amount in self.simulated_balance.items():
            balances.append({
                "asset": asset,
                "free": str(amount * 0.8),  # 80% livre
                "locked": str(amount * 0.2)  # 20% bloqueado (simulando ordens abertas)
            })
        
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": balances
        }
    
    def get_ticker_price(self, symbol):
        """Retorna preço simulado para um par"""
        # Remove a / se presente
        clean_symbol = format_symbol(symbol)
        
        # Verifica se temos um preço base para este símbolo
        base_price = self.base_prices.get(clean_symbol, 100.0)
        
        # Adiciona uma variação aleatória (-2% a +2%)
        variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + variation)
        
        self.logger.info(f"Preço simulado para {symbol}: {current_price:.8f}")
        
        return {
            "symbol": clean_symbol,
            "price": str(current_price)
        }
    
    def get_klines(self, symbol, interval, limit=500):
        """Gera dados de candlestick (OHLCV) simulados"""
        clean_symbol = format_symbol(symbol)
        base_price = self.base_prices.get(clean_symbol, 100.0)
        
        # Determina o tamanho dos candles baseado no intervalo
        if interval == "1m":
            candle_size = 0.001
        elif interval == "5m":
            candle_size = 0.003
        elif interval == "15m":
            candle_size = 0.005
        elif interval == "1h":
            candle_size = 0.01
        elif interval == "4h":
            candle_size = 0.02
        elif interval == "1d":
            candle_size = 0.05
        else:
            candle_size = 0.01
        
        # Gera dados simulados para o número de candles solicitado
        klines = []
        current_time = int(time.time() * 1000)
        
        # Determina o timeframe em milissegundos
        if interval == "1m":
            timeframe = 60 * 1000
        elif interval == "5m":
            timeframe = 5 * 60 * 1000
        elif interval == "15m":
            timeframe = 15 * 60 * 1000
        elif interval == "1h":
            timeframe = 60 * 60 * 1000
        elif interval == "4h":
            timeframe = 4 * 60 * 60 * 1000
        elif interval == "1d":
            timeframe = 24 * 60 * 60 * 1000
        else:
            timeframe = 60 * 60 * 1000  # Padrão: 1h
        
        # Gera candles históricos
        for i in range(limit):
            # Cada candle tem: [open_time, open, high, low, close, volume, ...]
            candle_time = current_time - ((limit - i) * timeframe)
            
            # Gera preços simulados com tendência (80% chance de seguir tendência anterior)
            if i > 0:
                prev_close = float(klines[i-1][4])
                if random.random() < 0.8:
                    # Segue a tendência (alta ou baixa)
                    trend = (prev_close - float(klines[i-1][1])) / float(klines[i-1][1])  # (close-open)/open
                    open_price = prev_close
                    close_price = open_price * (1 + trend + random.uniform(-0.5, 0.5) * candle_size)
                else:
                    # Inverte a tendência
                    trend = (prev_close - float(klines[i-1][1])) / float(klines[i-1][1])
                    open_price = prev_close
                    close_price = open_price * (1 - trend + random.uniform(-0.5, 0.5) * candle_size)
            else:
                # Primeiro candle - preços baseados no preço médio
                open_price = base_price * (1 + random.uniform(-0.01, 0.01))
                close_price = open_price * (1 + random.uniform(-candle_size, candle_size))
            
            # Gera o candle (OHLCV)
            klines.append([
                candle_time,  # open_time
                f"{open_price:.8f}",  # open
                f"{open_price + random.uniform(-candle_size, candle_size):.8f}",  # high
                f"{open_price - random.uniform(-candle_size, candle_size):.8f}",  # low
                f"{close_price:.8f}",  # close
                f"{random.uniform(1, 100)}",  # volume
                # Outros campos do candlestick podem ser adicionados aqui se necessário
            ])
        
        # Inverte a lista para ter os candles mais antigos primeiro (como na Binance)
        klines.reverse()
        
        self.logger.info(f"Gerados {len(klines)} candles simulados para {symbol} no intervalo {interval}")
        
        return klines
    
    def create_order(self, symbol, side, order_type, quantity, price=None, stop_price=None, time_in_force="GTC"):
        """Cria uma ordem simulada"""
        self.logger.info(f"Criando ordem simulada: {side} {quantity} de {symbol} a {price}")
        
        # Simula um delay na execução da ordem
        time.sleep(1)
        
        # Cria uma ordem fictícia com ID único
        order_id = self.next_order_id
        self.next_order_id += 1
        
        # Armazena a ordem
        self.orders[order_id] = {
            "symbol": symbol,
            "orderId": order_id,
            "clientOrderId": f"mock-{order_id}",
            "price": str(price),
            "origQty": str(quantity),
            "executedQty": "0",
            "status": "NEW",
            "timeInForce": time_in_force,
            "type": order_type,
            "side": side,
            "stopPrice": str(stop_price) if stop_price else None,
            "icebergQty": "0",
            "time": int(time.time() * 1000),
            "updateTime": int(time.time() * 1000),
            "isWorking": True,
            "fills": []  # Preenchements vazios inicialmente
        }
        
        return self.orders[order_id]
    
    def get_order(self, order_id):
        """Retorna uma ordem simulada pelo ID"""
        return self.orders.get(order_id, None)
    
    def cancel_order(self, order_id):
        """Cancela uma ordem simulada"""
        order = self.get_order(order_id)
        if order:
            order['status'] = 'CANCELLED'
            order['updateTime'] = int(time.time() * 1000)
            self.logger.info(f"Ordem {order_id} cancelada com sucesso")
            return order
        else:
            self.logger.warning(f"Tentativa de cancelar ordem que não existe: {order_id}")
            return None
    
    def get_open_orders(self, symbol=None):
        """Retorna ordens abertas simuladas"""
        open_orders = [order for order in self.orders.values() if order['status'] == 'NEW']
        
        if symbol:
            open_orders = [order for order in open_orders if order['symbol'] == symbol]
        
        return open_orders
    
    def get_historical_trades(self, symbol, limit=500):
        """Gera negociações históricas simuladas"""
        clean_symbol = symbol.replace('/', '')
        base_price = self.base_prices.get(clean_symbol, 100.0)
        
        trades = []
        current_time = int(time.time() * 1000)
        
        for i in range(limit):
            # Cada negociação tem: [id, preço, quantidade, timestamp, símbolo, comprador, vendedor, taxa, ...]
            trade_time = current_time - ((limit - i) * 60 * 1000)  # A cada minuto
            
            # Preço e quantidade aleatórios
            price = base_price * (1 + random.uniform(-0.01, 0.01))
            quantity = random.uniform(0.001, 1.0)
            
            trades.append([
                i + 1,  # ID
                f"{price:.8f}",  # Preço
                f"{quantity:.8f}",  # Quantidade
                trade_time,  # Timestamp
                clean_symbol,  # Símbolo
                "buyer_mock",  # Comprador (mock)
                "seller_mock",  # Vendedor (mock)
                "0.001",  # Taxa fixa simulada
                # Outros campos podem ser adicionados aqui se necessário
            ])
        
        # Inverte a lista para ter as negociações mais antigas primeiro
        trades.reverse()
        
        self.logger.info(f"Geradas {len(trades)} negociações históricas simuladas para {symbol}")
        
        return trades
    
    def get_my_trades(self, symbol=None, limit=500):
        """Retorna as minhas negociações simuladas"""
        all_trades = self.get_historical_trades(symbol, limit)
        
        # Adiciona informações de lucro e taxa
        my_trades = []
        for trade in all_trades:
            price = float(trade[1])
            quantity = float(trade[2])
            fee = 0.001  # Taxa fixa simulada
            
            # Lucro simulado: 70% de chance de ser positivo
            if random.random() < 0.7:
                exit_price = price * (1 + random.uniform(0.01, 0.1))
            else:
                exit_price = price * (1 - random.uniform(0.01, 0.1))
            
            # Cálculo de lucro líquido
            profit_data = calculate_profit(price, exit_price, quantity, fee_rate=fee)
            
            my_trades.append({
                'id': trade[0],
                'symbol': trade[4],
                'action': 'BUY' if random.random() < 0.5 else 'SELL',
                'price': f"{price:.8f}",
                'quantity': f"{quantity:.8f}",
                'timestamp': trade[3],
                'fee': f"{fee:.8f}",
                'net_profit': f"{profit_data['net_profit']:.8f}",
                'exit_price': f"{exit_price:.8f}",
                # Outros campos podem ser adicionados aqui se necessário
            })
        
        return my_trades
    
    def transfer(self, asset, amount, to_spot=True):
        """Simula transferência entre contas (ex: FUTURE para SPOT)"""
        self.logger.info(f"Transferindo {amount} {asset} para {'SPOT' if to_spot else 'FUTURE'}")
        
        # Simula um delay na transferência
        time.sleep(1)
        
        # Atualiza o saldo simulado
        if to_spot:
            self.simulated_balance[asset] = self.simulated_balance.get(asset, 0) + amount
        else:
            self.simulated_balance[asset] = self.simulated_balance.get(asset, 0) - amount
    
    def set_leverage(self, symbol, leverage):
        """Simula ajuste de margem para um símbolo"""
        self.logger.info(f"Ajustando margem para {symbol} - Leverage: {leverage}x")
        
        # Simula um delay na operação
        time.sleep(1)
        
        # Armazena o valor da margem (mock)
        self.orders['margin'] = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000)
        }
    
    def get_position_info(self, symbol):
        """Retorna informações simuladas de posição para um símbolo"""
        return {
            "symbol": symbol,
            "positionAmt": "0",
            "entryPrice": "0",
            "avgEntryPrice": "0",
            "liquidationPrice": "0",
            "unrealizedProfit": "0",
            "marginType": "CROSSED",
            "isAutoMarginEnabled": True,
            "isolatedMargin": "0",
            "positionSide": "BOTH",
            "leverage": "20",
            "maxNotionalValue": "100000",
            "marginCallPrice": "0",
            "liquidationPrice": "0",
            "unrealizedProfit": "0",
            "positionStatus": "NORMAL",
            "symbol": symbol
        }
    
    def ping(self):
        """Simula o ping na API da Binance"""
        self.logger.info("Pong! (simulação de ping)")
        return True
    
    def close(self):
        """Fecha o simulador (limpa ordens e saldos)"""
        self.logger.info("Fechando simulador da Binance")
        
        # Limpa ordens
        self.orders = {}
        self.next_order_id = 1000
        
        # Restaura saldo inicial simulado
        self.simulated_balance = {
            "USDT": 100.0,
            "BTC": 0.001,
            "ETH": 0.01,
            "BRL": 500.0,
            "BNB": 1.5,
        }
        
        self.logger.info("Simulador fechado e saldo restaurado")

def filtrar_pares_por_liquidez(pares, volume_minimo, binance_api):
    """Filtra pares de trading com base no volume mínimo de negociação e validade
    
    Args:
        pares (list): Lista de pares de trading no formato "BTC/USDT"
        volume_minimo (float): Volume mínimo de negociação em USD nas últimas 24 horas
        binance_api: Instância da API da Binance para consultar volumes
        
    Returns:
        list: Lista de pares filtrados que atendem ao critério de volume mínimo
    """
    pares_filtrados = []
    logger = logging.getLogger("robot-crypt")
    
    # Validamos primeiro se os pares existem e estão disponíveis para trading
    pares_validos = []
    for par in pares:
        # Validar se o par é válido antes de verificar volume
        if binance_api.validate_trading_pair(par):
            pares_validos.append(par)
        else:
            logger.warning(f"Par {par} ignorado: não é válido ou não está disponível para trading")
    
    logger.info(f"Total de {len(pares_validos)}/{len(pares)} pares validados como disponíveis para trading")
    
    # Agora filtra por volume
    for par in pares_validos:
        try:
            # Obter ticker de 24h para o par
            api_symbol = par.replace('/', '')
            ticker_24h = binance_api.get_ticker_24h(api_symbol)
            
            # Verificar se o volume atende ao mínimo
            volume_24h_usd = float(ticker_24h['quoteVolume'])  # Volume em moeda quote (geralmente USDT)
            
            if volume_24h_usd >= volume_minimo:
                pares_filtrados.append(par)
            else:
                logger.info(f"Par {par} descartado por volume insuficiente: ${volume_24h_usd:.2f} (mínimo: ${volume_minimo:.2f})")
                
        except Exception as e:
            logger.warning(f"Erro ao verificar volume de {par}: {str(e)}")
    
    return pares_filtrados

def get_precision_for_symbol(symbol, price, binance_api=None):
    """Determina a precisão adequada para uma moeda com base em seu preço e regras da exchange
    
    Args:
        symbol (str): Símbolo da moeda (ex: 'BTC/USDT' ou 'BTCUSDT')
        price (float): Preço atual da moeda
        binance_api (BinanceAPI, optional): Instância da API da Binance para consultar regras exatas
        
    Returns:
        dict: Dicionário com precisões para quantidade e preço
    """
    # Formato padrão para retorno
    result = {
        'quantity_precision': 6,  # Padrão: 6 casas decimais para quantidade
        'price_precision': 2,      # Padrão: 2 casas decimais para preço
        'min_qty': 0.000001,       # Quantidade mínima padrão
        'min_notional': 10.0       # Valor mínimo da ordem em USDT/BRL
    }
    
    # Se temos acesso à API da Binance, consultamos as regras exatas do símbolo
    if binance_api:
        try:
            # Formato esperado pela API
            api_symbol = symbol.replace('/', '')
            symbol_info = binance_api.get_symbol_info(api_symbol)
            
            if symbol_info and 'filters' in symbol_info:
                # Extrai informações dos filtros da Binance
                for filter_data in symbol_info['filters']:
                    # Filtro de precisão de preço (PRICE_FILTER)
                    if filter_data['filterType'] == 'PRICE_FILTER':
                        tick_size = float(filter_data['tickSize'])
                        # Calcula a precisão a partir do tickSize
                        price_precision = 0
                        if tick_size < 1:
                            decimal_str = str(tick_size).split('.')[-1]
                            # Conta o número de zeros após o ponto decimal
                            price_precision = len(decimal_str.rstrip('0'))
                        result['price_precision'] = price_precision
                    
                    # Filtro de precisão de lote (LOT_SIZE)
                    elif filter_data['filterType'] == 'LOT_SIZE':
                        step_size = float(filter_data['stepSize'])
                        min_qty = float(filter_data['minQty'])
                        # Calcula a precisão a partir do stepSize
                        qty_precision = 0
                        if step_size < 1:
                            decimal_str = str(step_size).split('.')[-1]
                            qty_precision = len(decimal_str.rstrip('0'))
                        result['quantity_precision'] = qty_precision
                        result['min_qty'] = min_qty
                    
                    # Filtro de valor mínimo (MIN_NOTIONAL)
                    elif filter_data['filterType'] == 'MIN_NOTIONAL':
                        min_notional = float(filter_data['minNotional'])
                        result['min_notional'] = min_notional
                
                return result
        except Exception as e:
            logger = logging.getLogger("robot-crypt")
            logger.warning(f"Erro ao obter precisão para {symbol} via API: {str(e)}")
            # Continua com a lógica baseada em preço
    
    # Lógica baseada em preço quando não temos acesso à API ou falhou
    # Essa é uma heurística simplificada que funciona bem para a maioria dos casos
    
    # Determina a precisão do preço com base no valor
    if price < 0.00001:    # Extremamente pequeno (ex: SHIB)
        result['price_precision'] = 8
    elif price < 0.0001:   # Muito pequeno
        result['price_precision'] = 7
    elif price < 0.001:    # Pequeno
        result['price_precision'] = 6
    elif price < 0.01:     # Moderado-baixo
        result['price_precision'] = 5
    elif price < 0.1:      # Moderado
        result['price_precision'] = 4
    elif price < 1.0:      # Normal-baixo
        result['price_precision'] = 3
    elif price < 10.0:     # Normal
        result['price_precision'] = 2
    elif price < 1000.0:   # Alto
        result['price_precision'] = 2
    else:                   # Muito alto (ex: BTC)
        result['price_precision'] = 1
    
    # Determina a precisão da quantidade com base no preço
    # As regras aqui são inversas: quanto maior o preço, maior a precisão da quantidade
    if price < 0.000001:   # Extremamente pequeno
        result['quantity_precision'] = 0  # Sem casas decimais (geralmente grandes quantidades)
    elif price < 0.0001:   # Muito pequeno
        result['quantity_precision'] = 0
    elif price < 0.01:     # Pequeno
        result['quantity_precision'] = 2
    elif price < 0.1:      # Moderado-baixo
        result['quantity_precision'] = 4
    elif price < 1.0:      # Moderado
        result['quantity_precision'] = 4
    elif price < 10.0:     # Normal-baixo
        result['quantity_precision'] = 5
    elif price < 100.0:    # Normal
        result['quantity_precision'] = 6
    elif price < 1000.0:   # Alto
        result['quantity_precision'] = 6
    elif price < 10000.0:  # Muito alto
        result['quantity_precision'] = 7
    else:                   # Extremamente alto
        result['quantity_precision'] = 8
    
    # Definir valores mínimos com base no preço
    if price < 0.00001:    # Extremamente pequeno
        result['min_qty'] = 1.0       # Geralmente para moedas como SHIB
        result['min_notional'] = 5.0  # Valor mínimo em USDT/BRL
    elif price < 0.01:     # Pequeno
        result['min_qty'] = 0.1
        result['min_notional'] = 5.0
    elif price < 1.0:      # Moderado
        result['min_qty'] = 0.01
        result['min_notional'] = 10.0
    elif price < 100.0:    # Normal
        result['min_qty'] = 0.001
        result['min_notional'] = 10.0
    elif price < 1000.0:   # Alto
        result['min_qty'] = 0.0001
        result['min_notional'] = 10.0
    else:                   # Muito alto
        result['min_qty'] = 0.00001
        result['min_notional'] = 10.0
    
    return result

def adjust_quantity_precision(quantity, symbol, price, binance_api=None):
    """Ajusta a precisão da quantidade de acordo com as regras da exchange
    
    Args:
        quantity (float): Quantidade a ser ajustada
        symbol (str): Símbolo da moeda (ex: 'BTC/USDT')
        price (float): Preço atual da moeda
        binance_api (BinanceAPI, optional): Instância da API da Binance para consultar regras exatas
        
    Returns:
        float: Quantidade ajustada com precisão correta
    """
    # Obtém as regras de precisão para o símbolo
    precision_rules = get_precision_for_symbol(symbol, price, binance_api)
    
    # Obtém a precisão da quantidade
    qty_precision = precision_rules['quantity_precision']
    min_qty = precision_rules['min_qty']
    min_notional = precision_rules['min_notional']
    
    # Ajusta a quantidade de acordo com a precisão
    adjusted_quantity = round(quantity, qty_precision)
    
    # Garante que a quantidade é pelo menos o mínimo permitido
    adjusted_quantity = max(adjusted_quantity, min_qty)
    
    # Verifica se o valor total da ordem atinge o mínimo notional
    notional_value = adjusted_quantity * price
    if notional_value < min_notional:
        # Ajusta a quantidade para atingir o valor mínimo
        min_required_qty = min_notional / price
        adjusted_quantity = max(adjusted_quantity, min_required_qty)
        # Arredonda novamente para a precisão correta
        adjusted_quantity = round(adjusted_quantity, qty_precision)
    
    return adjusted_quantity

def retry_operation(operation, max_retries=3, initial_wait=1, max_wait=60, logger=None):
    """
    Executa uma operação com mecanismo de retry com backoff exponencial
    
    Args:
        operation (callable): Função a ser executada
        max_retries (int): Número máximo de tentativas
        initial_wait (int): Tempo de espera inicial em segundos
        max_wait (int): Tempo máximo de espera em segundos
        logger (logging.Logger): Logger para registrar mensagens
    
    Returns:
        O resultado da operação se bem sucedido, None caso contrário
    """
    import time
    import random
    from requests.exceptions import RequestException, Timeout, ConnectionError
    
    for attempt in range(max_retries):
        try:
            return operation()
        except (RequestException, Timeout, ConnectionError) as e:
            # Calcula tempo de espera com jitter para evitar thundering herd
            wait_time = min(max_wait, initial_wait * (2 ** attempt) + random.uniform(0, 1))
            
            if logger:
                error_type = e.__class__.__name__
                logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou com erro {error_type}: {str(e)}")
                logger.warning(f"Aguardando {wait_time:.2f}s antes da próxima tentativa")
                
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                if logger:
                    logger.error(f"Operação falhou após {max_retries} tentativas")
                return None
        except Exception as e:
            # Para outros tipos de erro, não tentamos novamente
            if logger:
                logger.error(f"Erro não recuperável: {str(e)}")
            raise