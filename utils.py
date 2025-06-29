#!/usr/bin/env python3
"""
Módulo de utilidades para Robot-Crypt
"""
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

def calculate_profit(entry_price, exit_price, quantity, fee_rate=0.001):
    """Calcula o lucro real de uma operação considerando taxas
    
    Parameters:
    -----------
    entry_price : float
        Preço de compra
    exit_price : float
        Preço de venda
    quantity : float
        Quantidade negociada
    fee_rate : float
        Taxa por operação (padrão: 0.1%)
        
    Returns:
    --------
    dict
        Dicionário com valores de lucro bruto, taxas e lucro líquido
    """
    # Valor total da compra e venda
    entry_value = entry_price * quantity
    exit_value = exit_price * quantity
    
    # Lucro bruto
    gross_profit = exit_value - entry_value
    
    # Cálculo das taxas
    entry_fee = entry_value * fee_rate
    exit_fee = exit_value * fee_rate
    total_fees = entry_fee + exit_fee
    
    # Lucro líquido
    net_profit = gross_profit - total_fees
    
    # Porcentagem de lucro
    profit_percent = (net_profit / entry_value) * 100
    
    return {
        'entry_value': entry_value,
        'exit_value': exit_value,
        'gross_profit': gross_profit,
        'total_fees': total_fees,
        'net_profit': net_profit,
        'profit_percent': profit_percent
    }

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
        clean_symbol = symbol.replace('/', '')
        
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
        clean_symbol = symbol.replace('/', '')
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
    """Filtra pares de trading com base no volume mínimo de negociação
    
    Args:
        pares (list): Lista de pares de trading no formato "BTC/USDT"
        volume_minimo (float): Volume mínimo de negociação em USD nas últimas 24 horas
        binance_api: Instância da API da Binance para consultar volumes
        
    Returns:
        list: Lista de pares filtrados que atendem ao critério de volume mínimo
    """
    pares_filtrados = []
    
    for par in pares:
        try:
            # Obter ticker de 24h para o par
            api_symbol = par.replace('/', '')
            ticker_24h = binance_api.get_ticker_24h(api_symbol)
            
            # Verificar se o volume atende ao mínimo
            volume_24h_usd = float(ticker_24h['quoteVolume'])  # Volume em moeda quote (geralmente USDT)
            
            if volume_24h_usd >= volume_minimo:
                pares_filtrados.append(par)
            else:
                logger = logging.getLogger("robot-crypt")
                logger.info(f"Par {par} descartado por volume insuficiente: ${volume_24h_usd:.2f} (mínimo: ${volume_minimo:.2f})")
                
        except Exception as e:
            logger = logging.getLogger("robot-crypt")
            logger.warning(f"Erro ao verificar volume de {par}: {str(e)}")
    
    return pares_filtrados