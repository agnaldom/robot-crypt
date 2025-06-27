import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import logging
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_API_URL

logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET
        self.base_url = BINANCE_API_URL
        
    def _get_signature(self, params):
        """Gera a assinatura para autenticação na API."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """Faz uma requisição para a API da Binance."""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if signed:
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._get_signature(params)
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            elif method == "POST":
                response = requests.post(url, params=params, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para a Binance: {e}")
            return None
    
    def get_exchange_info(self):
        """Obtém informações da exchange."""
        return self._make_request("GET", "/api/v3/exchangeInfo")
    
    def get_symbol_info(self, symbol):
        """Obtém informações de um par de trading específico."""
        exchange_info = self.get_exchange_info()
        if not exchange_info:
            return None
            
        for symbol_info in exchange_info.get('symbols', []):
            if symbol_info['symbol'] == symbol:
                return symbol_info
        return None
    
    def get_latest_price(self, symbol):
        """Obtém o preço atual de um par de trading."""
        endpoint = "/api/v3/ticker/price"
        params = {'symbol': symbol}
        response = self._make_request("GET", endpoint, params)
        if response:
            return float(response['price'])
        return None
    
    def create_order(self, symbol, side, quantity):
        """Cria uma ordem de compra ou venda."""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'side': side,  # 'BUY' ou 'SELL'
            'type': 'MARKET',
            'quantity': quantity,
        }
        return self._make_request("POST", endpoint, params, signed=True)
    
    def get_account_balance(self):
        """Obtém o saldo da conta."""
        endpoint = "/api/v3/account"
        return self._make_request("GET", endpoint, signed=True)
    
    def get_asset_balance(self, asset):
        """Obtém o saldo de um ativo específico."""
        account_info = self.get_account_balance()
        if not account_info:
            return None
            
        for balance in account_info.get('balances', []):
            if balance['asset'] == asset:
                return {
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                }
        return None
