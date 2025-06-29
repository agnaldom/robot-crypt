#!/usr/bin/env python3
"""
Módulo para interação com a API da Binance
"""
import time
import hmac
import hashlib
import requests
import logging
import os
from urllib.parse import urlencode

class BinanceAPI:
    """Classe para interagir com a API da Binance"""
    
    def __init__(self, api_key="", api_secret="", testnet=True):
        """Inicializa a conexão com a API da Binance"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Define URLs base de acordo com testnet ou produção
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
        else:
            self.base_url = "https://api.binance.com/api"
        
        self.logger = logging.getLogger("robot-crypt")
        
        # Configurações de proxy do ambiente
        self.proxies = {}
        
        # Configura proxies a partir das variáveis de ambiente
        http_proxy = os.environ.get('HTTP_PROXY', '')
        https_proxy = os.environ.get('HTTPS_PROXY', '')
        
        if http_proxy:
            self.proxies['http'] = http_proxy
            self.logger.info(f"Usando HTTP proxy: {http_proxy}")
        
        if https_proxy:
            self.proxies['https'] = https_proxy
            self.logger.info(f"Usando HTTPS proxy: {https_proxy}")
            
        # Log de uso de proxy
        if self.proxies:
            self.logger.info("Conexão através de proxy configurada")
        else:
            self.logger.debug("Conexão direta (sem proxy)")
        
        # Log de inicialização com informações parciais da chave para debug
        if self.api_key:
            masked_key = self.api_key[:4] + "..." + self.api_key[-4:]
            self.logger.info(f"Inicializando API da Binance com chave {masked_key}")
            self.logger.info(f"Usando {'testnet' if testnet else 'produção'}")
        else:
            self.logger.warning("API Key não fornecida. A maioria das operações não funcionará.")
    
    def _generate_signature(self, params):
        """Gera assinatura para requisições autenticadas"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """Faz uma requisição para a API da Binance"""
        url = f"{self.base_url}{endpoint}"
        
        # Verifica se API key foi configurada
        if not self.api_key or not self.api_secret:
            error_msg = "API Key e Secret não configurados. Verifique seu arquivo .env"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        if params is None:
            params = {}
        
        if signed:
            # Adiciona timestamp para requisições assinadas
            params['timestamp'] = int(time.time() * 1000)
            # Gera assinatura
            params['signature'] = self._generate_signature(params)
            
            # Log para debug (sem mostrar a assinatura completa)
            self.logger.debug(f"Request: {method} {endpoint} - Timestamp: {params['timestamp']} - Sig: {params['signature'][:8]}...")
        
        try:
            # Adiciona log detalhado para parâmetros importantes como symbol
            if 'symbol' in params:
                self.logger.info(f"Fazendo requisição para símbolo: {params['symbol']}")
            
            self.logger.debug(f"Enviando requisição {method} para {url}")
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            # Log da resposta para debug
            self.logger.debug(f"Status: {response.status_code}")
            
            # Verifica se a requisição foi bem-sucedida
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro na requisição à API da Binance: {str(e)}"
            self.logger.error(error_msg)
            
            if hasattr(e, 'response') and e.response:
                try:
                    error_details = e.response.json()
                    self.logger.error(f"Detalhes do erro: {error_details}")
                except:
                    self.logger.error(f"Resposta: {e.response.text}")
            
            # Se for erro de autenticação na testnet, sugere verificar credenciais específicas da testnet
            if self.testnet and hasattr(e, 'response') and e.response.status_code == 401:
                self.logger.error("IMPORTANTE: Para usar a testnet da Binance, você precisa de credenciais específicas da testnet.")
                self.logger.error("Obtenha credenciais em: https://testnet.binance.vision/")
            
            # Se for erro 451, indica restrição de IP/região
            if hasattr(e, 'response') and e.response.status_code == 451:
                self.logger.error("ERRO 451: Este erro indica que seu acesso está sendo bloqueado devido a restrições de IP ou região.")
                self.logger.error("Soluções possíveis:")
                self.logger.error("1. Configure um proxy/VPN em seu deployment")
                self.logger.error("2. Use a variável de ambiente HTTP_PROXY e HTTPS_PROXY")
                self.logger.error("3. Considere usar um provedor de hospedagem em uma região permitida pela Binance")
            
            raise
    
    def get_account_info(self):
        """Obtém informações da conta"""
        endpoint = "/v3/account"
        return self._make_request('GET', endpoint, signed=True)
    
    def get_ticker_price(self, symbol):
        """Obtém preço atual de um par"""
        endpoint = "/v3/ticker/price"
        params = {'symbol': symbol.replace('/', '')}
        return self._make_request('GET', endpoint, params)
    
    def get_klines(self, symbol, interval, limit=500):
        """Obtém dados de candlestick (OHLCV)"""
        endpoint = "/v3/klines"
        params = {
            'symbol': symbol.replace('/', ''),
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', endpoint, params)
    
    def create_order(self, symbol, side, type, quantity=None, price=None, time_in_force=None):
        """Cria uma ordem de compra ou venda"""
        endpoint = "/v3/order"
        
        # Converte o símbolo para o formato da Binance
        symbol = symbol.replace('/', '')
        
        params = {
            'symbol': symbol,
            'side': side.upper(),  # SELL ou BUY
            'type': type.upper()   # LIMIT, MARKET, STOP_LOSS, etc.
        }
        
        # Adiciona parâmetros específicos de acordo com o tipo de ordem
        if quantity:
            params['quantity'] = quantity
            
        if price and type.upper() != 'MARKET':
            params['price'] = price
            
        if time_in_force and type.upper() == 'LIMIT':
            params['timeInForce'] = time_in_force
        
        return self._make_request('POST', endpoint, params, signed=True)
    
    def get_order(self, symbol, order_id):
        """Obtém informações sobre uma ordem específica"""
        endpoint = "/v3/order"
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id
        }
        return self._make_request('GET', endpoint, params, signed=True)
    
    def cancel_order(self, symbol, order_id):
        """Cancela uma ordem específica"""
        endpoint = "/v3/order"
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id
        }
        return self._make_request('DELETE', endpoint, params, signed=True)
    
    def get_exchange_info(self):
        """Obtém informações sobre regras de negociação e símbolos"""
        endpoint = "/v3/exchangeInfo"
        return self._make_request('GET', endpoint)
    
    def get_24hr_ticker(self, symbol=None):
        """Obtém estatísticas de 24h para um símbolo ou todos os símbolos"""
        endpoint = "/v3/ticker/24hr"
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        return self._make_request('GET', endpoint, params)
    
    def test_connection(self):
        """Testa a conexão com a API da Binance"""
        try:
            # Teste 1: Endpoint de ping que não requer autenticação
            self.logger.info("Testando conexão básica com a API...")
            endpoint = "/v3/ping"
            result = None
            
            try:
                # Fazemos o request manualmente para evitar exceções neste estágio
                url = f"{self.base_url}{endpoint}"
                response = requests.get(
                    url, 
                    proxies=self.proxies, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                self.logger.info("✓ Conexão básica com a API estabelecida")
            except Exception as e:
                self.logger.error(f"✗ Falha na conexão básica: {str(e)}")
                
                # Se for erro 451, indica restrição de IP/região
                if hasattr(e, 'response') and e.response.status_code == 451:
                    self.logger.error("ERRO 451: Este erro indica que seu acesso está sendo bloqueado devido a restrições de IP ou região.")
                    self.logger.error("Soluções possíveis:")
                    self.logger.error("1. Configure um proxy/VPN em seu deployment")
                    self.logger.error("2. Use a variável de ambiente HTTP_PROXY e HTTPS_PROXY")
                    self.logger.error("3. Considere usar um provedor de hospedagem em uma região permitida pela Binance")
                
                return False
            
            # Teste 2: Verificando tempo do servidor
            self.logger.info("Verificando sincronização de tempo com o servidor...")
            try:
                server_time = self.get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = abs(local_time - server_time)
                self.logger.info(f"✓ Tempo do servidor: {server_time}, Tempo local: {local_time}, Diferença: {time_diff}ms")
                
                if time_diff > 1000:  # Mais de 1 segundo de diferença
                    self.logger.warning(f"⚠️ Diferença de tempo entre cliente e servidor é grande: {time_diff}ms")
                
            except Exception as e:
                self.logger.error(f"✗ Falha ao verificar tempo do servidor: {str(e)}")
                # Continuamos mesmo com falha neste teste
            
            # Teste 3: Endpoint que requer autenticação
            self.logger.info("Testando autenticação com a API...")
            try:
                if self.testnet:
                    # Na testnet, tentamos obter as ordens abertas (mais simples que account info)
                    endpoint = "/v3/openOrders"
                    params = {'timestamp': int(time.time() * 1000)}
                    params['signature'] = self._generate_signature(params)
                    
                    url = f"{self.base_url}{endpoint}"
                    headers = {
                        'X-MBX-APIKEY': self.api_key,
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                    
                    self.logger.debug(f"Enviando requisição de teste para: {url}")
                    response = requests.get(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
                    
                    # Log detalhado para debug
                    self.logger.debug(f"Status: {response.status_code}")
                    self.logger.debug(f"Resposta: {response.text[:200]}...")  # Primeiros 200 caracteres
                    
                    response.raise_for_status()
                    self.logger.info("✓ Autenticação bem-sucedida (testnet)")
                else:
                    # Na produção, usamos account info
                    self.get_account_info()
                    self.logger.info("✓ Autenticação bem-sucedida")
                
                return True
            except Exception as e:
                self.logger.error(f"✗ Falha na autenticação: {str(e)}")
                
                if self.testnet:
                    self.logger.error("NOTA: Para a testnet da Binance você precisa de credenciais específicas.")
                    self.logger.error("Gere uma chave testnet em: https://testnet.binance.vision/")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Erro geral ao testar conexão: {str(e)}")
            return False
    
    def get_server_time(self):
        """Obtém o tempo do servidor da Binance para sincronização"""
        endpoint = "/v3/time"
        result = self._make_request('GET', endpoint)
        return result["serverTime"]
