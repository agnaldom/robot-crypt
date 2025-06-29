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
import json
from datetime import datetime
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
        
        # Configurações de logging melhoradas para Docker
        self.log_request_details = os.environ.get("LOG_REQUEST_DETAILS", "false").lower() in ["true", "1", "yes", "y"]
        self.log_response_details = os.environ.get("LOG_RESPONSE_DETAILS", "false").lower() in ["true", "1", "yes", "y"]
        self.show_masked_credentials = os.environ.get("SHOW_MASKED_CREDENTIALS", "true").lower() in ["true", "1", "yes", "y"]
        
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
        start_time = time.time()
        
        # Verifica se API key foi configurada
        if not self.api_key or not self.api_secret:
            error_msg = "API Key e Secret não configurados. Verifique seu arquivo .env"
            self._log_structured("error", error_msg)
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
            
        # Log estruturado da requisição
        self._log_request(method, url, params, headers)
        
        # Log específico para símbolos (útil para diagnosticar problemas)
        if 'symbol' in params:
            self._log_structured("info", f"Processando símbolo: {params['symbol']}", {
                "symbol": params['symbol'],
                "endpoint": endpoint,
                "testnet": self.testnet
            })
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            # Calcula o tempo de resposta em milissegundos
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Log estruturado da resposta
            content = response.text  # Guarda o texto da resposta antes de tentar parse
            self._log_response(response.status_code, content[:1000], elapsed_ms)
            
            # Log de latência para monitoramento de performance
            if elapsed_ms > 1000:  # Se demorou mais de 1s
                self._log_structured("warning", f"Requisição API lenta: {elapsed_ms}ms", {
                    "elapsed_ms": elapsed_ms,
                    "endpoint": endpoint,
                    "method": method
                })
            
            # Verifica se a requisição foi bem-sucedida
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            # Calcula o tempo decorrido mesmo em caso de erro
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Log estruturado detalhado para o erro
            error_context = {
                "elapsed_ms": elapsed_ms,
                "endpoint": endpoint,
                "method": method,
                "error_type": e.__class__.__name__,
            }
            
            if hasattr(e, 'response') and e.response:
                error_context["status_code"] = e.response.status_code
                
                try:
                    error_details = e.response.json()
                    error_context["response"] = error_details
                except:
                    error_context["response_text"] = e.response.text[:500]
            
            self._log_structured("error", f"Erro na API Binance: {endpoint}", error_context, e)
            
            # Tratamento para conexão timeout e problemas de rede
            if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                self._log_structured("warning", 
                    f"Erro de timeout ou conexão ao acessar {endpoint}",
                    {"endpoint": endpoint, "retry": "auto", "fallback": "dados vazios"}
                )
                    
                if 'account' in endpoint:
                    self._log_structured("warning", 
                        "Falha ao obter informações da conta. Retornando dados vazios para tentar continuar.",
                        {"action": "continue", "fallback_data": "empty_balances"}
                    )
                    return {"balances": []}  # Retorna estrutura mínima para evitar falhas
            
            # Tratamento para resposta de erro quando disponível
            if hasattr(e, 'response') and e.response:
                # Se for erro de autenticação na testnet, sugere verificar credenciais específicas
                if self.testnet and e.response.status_code == 401:
                    self._log_structured("error", 
                        "Erro de autenticação na TestNet Binance",
                        {
                            "status_code": e.response.status_code,
                            "solution": "Obter novas credenciais TestNet em https://testnet.binance.vision/"
                        }
                    )
                
                # Se for erro 451, indica restrição de IP/região
                if e.response.status_code == 451:
                    self._log_structured("error", 
                        "Acesso bloqueado por restrições geográficas (Erro 451)",
                        {
                            "status_code": 451,
                            "solutions": [
                                "Configure um proxy/VPN em seu deployment",
                                "Use a variável de ambiente HTTP_PROXY e HTTPS_PROXY",
                                "Considere usar um provedor de hospedagem em região permitida"
                            ]
                        }
                    )
                    
                # Se for erro de rate limit, log específico
                if e.response.status_code == 429:
                    self._log_structured("warning", 
                        "Rate limit atingido na API Binance",
                        {
                            "status_code": 429,
                            "recommendation": "Reduzir frequência de requisições ou implementar exponential backoff"
                        }
                    )
            
            # Para erros críticos, levanta exceção. Para erros de rede, tenta continuar
            if not isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                raise
            
            # Para erros de rede, retorna um valor padrão para permitir que a execução continue
            if 'ticker' in endpoint:
                self._log_structured("warning", "Retornando preço zerado devido a erro de rede", {"fallback": "zero_price"})
                return {"price": "0"}  # Valor padrão para ticker
            elif 'klines' in endpoint or 'candlestick' in endpoint:
                self._log_structured("warning", "Retornando array vazio de candles devido a erro de rede", {"fallback": "empty_array"})
                return []  # Lista vazia para candlesticks/klines
            else:
                self._log_structured("warning", "Retornando objeto vazio devido a erro de rede", {"fallback": "empty_object", "endpoint": endpoint})
                return {}  # Objeto vazio para outros endpoints
    
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
            self._log_structured("info", "Iniciando teste de conexão com API Binance", 
                {"stage": "connection_test", "environment": "testnet" if self.testnet else "production"})
                
            endpoint = "/v3/ping"
            result = None
            
            try:
                # Fazemos o request manualmente para evitar exceções neste estágio
                url = f"{self.base_url}{endpoint}"
                start_time = time.time()
                
                response = requests.get(
                    url, 
                    proxies=self.proxies, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    },
                    timeout=30
                )
                
                # Calcula tempo de resposta
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                response.raise_for_status()
                result = response.json()
                
                self._log_structured("info", "Teste de ping concluído com sucesso", {
                    "test": "basic_connectivity",
                    "url": url,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms
                })
            except Exception as e:
                self._log_structured("error", "Falha no teste de conectividade básica", 
                    {"test": "basic_connectivity", "url": url}, e)
                
                # Se for erro 451, indica restrição de IP/região
                if hasattr(e, 'response') and e.response and e.response.status_code == 451:
                    self._log_structured("error", "Acesso bloqueado por restrições geográficas (Erro 451)", {
                        "status_code": 451,
                        "solutions": [
                            "Configure um proxy/VPN em seu deployment",
                            "Use a variável de ambiente HTTP_PROXY e HTTPS_PROXY",
                            "Considere usar um provedor de hospedagem em região permitida"
                        ]
                    })
                
                return False
            
            # Teste 2: Verificando tempo do servidor
            self._log_structured("info", "Verificando sincronização de tempo com o servidor", {"test": "time_sync"})
            try:
                server_time = self.get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = abs(local_time - server_time)
                
                sync_status = "ok"
                if time_diff > 1000:  # Mais de 1 segundo de diferença
                    sync_status = "warning"
                elif time_diff > 5000:  # Mais de 5 segundos
                    sync_status = "critical"
                    
                self._log_structured("info" if sync_status == "ok" else "warning", 
                    f"Sincronização de tempo: {sync_status.upper()}", {
                        "server_time": server_time,
                        "local_time": local_time, 
                        "difference_ms": time_diff,
                        "status": sync_status
                    }
                )
                
            except Exception as e:
                self._log_structured("error", "Falha ao verificar sincronização de tempo", 
                    {"test": "time_sync", "continue": True}, e)
                # Continuamos mesmo com falha neste teste
            
            # Teste 3: Endpoint que requer autenticação
            self._log_structured("info", "Testando autenticação com a API", {"test": "authentication"})
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
                    
                    start_time = time.time()
                    
                    # Log estruturado da requisição
                    safe_headers = headers.copy()
                    if self.show_masked_credentials:
                        api_key = safe_headers['X-MBX-APIKEY'] 
                        safe_headers['X-MBX-APIKEY'] = api_key[:4] + '...' + api_key[-4:]
                    else:
                        safe_headers['X-MBX-APIKEY'] = '[REDACTED]'
                    
                    self._log_structured("debug", 
                        f"Enviando requisição de autenticação (testnet): {endpoint}", {
                            "url": url,
                            "headers": safe_headers,
                            "has_signature": "signature" in params
                        }
                    )
                    
                    response = requests.get(url, headers=headers, params=params, proxies=self.proxies, timeout=30)
                    
                    # Calcula tempo de resposta
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    
                    self._log_structured("debug", 
                        f"Resposta de autenticação recebida: {response.status_code}", {
                            "status_code": response.status_code,
                            "elapsed_ms": elapsed_ms,
                            "content_preview": response.text[:100]
                        }
                    )
                    
                    response.raise_for_status()
                    self._log_structured("info", "Autenticação testnet bem-sucedida", 
                        {"test": "authentication", "environment": "testnet", "status": "success"})
                else:
                    # Na produção, usamos account info
                    self.get_account_info()
                    self._log_structured("info", "Autenticação produção bem-sucedida", 
                        {"test": "authentication", "environment": "production", "status": "success"})
                
                return True
            except Exception as e:
                self._log_structured("error", "Falha na autenticação", {"test": "authentication"}, e)
                
                if self.testnet:
                    self._log_structured("error", "Credenciais TestNet inválidas ou expiradas", {
                        "solution": "Gere uma nova chave testnet em https://testnet.binance.vision/",
                        "note": "As credenciais da TestNet expiram após 30 dias"
                    })
                
                return False
                
        except Exception as e:
            self._log_structured("error", "Erro geral ao testar conexão com Binance API", 
                {"test": "general", "recoverable": False}, e)
            return False
    
    def get_server_time(self):
        """Obtém o tempo do servidor da Binance para sincronização"""
        endpoint = "/v3/time"
        self._log_structured("debug", "Consultando tempo do servidor Binance", {"endpoint": endpoint})
        start_time = time.time()
        
        try:
            result = self._make_request('GET', endpoint)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            self._log_structured("debug", "Tempo do servidor obtido com sucesso", {
                "server_time": result["serverTime"],
                "local_time": int(time.time() * 1000),
                "request_time_ms": elapsed_ms
            })
            
            return result["serverTime"]
        except Exception as e:
            self._log_structured("error", "Falha ao obter tempo do servidor", 
                {"endpoint": endpoint, "fallback": "local_time"}, e)
            # Retorna tempo local como fallback
            return int(time.time() * 1000)
    
    def _log_structured(self, level, message, data=None, error=None):
        """
        Cria logs estruturados que são mais fáceis de analisar em ambientes Docker/Cloud
        
        Args:
            level: Nível de log (info, warning, error, debug)
            message: Mensagem principal do log
            data: Dados adicionais a serem incluídos no log (dict)
            error: Objeto de exceção ou string de erro
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "service": "binance-api",
            "message": message,
            "level": level,
        }
        
        if data:
            log_data["data"] = data
            
        if error:
            if isinstance(error, Exception):
                log_data["error"] = {
                    "type": error.__class__.__name__,
                    "message": str(error)
                }
            else:
                log_data["error"] = {"message": str(error)}
        
        # Os logs estruturados são melhores para ambientes containerizados
        # mas também queremos manter o formato legível para desenvolvimento
        if os.environ.get("LOG_FORMAT", "").lower() == "json":
            # Formato JSON para ambientes de produção/container
            log_entry = json.dumps(log_data)
        else:
            # Formato legível para desenvolvimento
            if data or error:
                extras = []
                if data:
                    extras.append(f"data={json.dumps(data, ensure_ascii=False)[:100]}")
                if error:
                    if isinstance(error, Exception):
                        extras.append(f"error={error.__class__.__name__}: {str(error)}")
                    else:
                        extras.append(f"error={str(error)}")
                log_entry = f"{message} | {' | '.join(extras)}"
            else:
                log_entry = message
        
        # Use o logger apropriado com base no nível
        if level == "error":
            self.logger.error(log_entry)
        elif level == "warning":
            self.logger.warning(log_entry)
        elif level == "debug":
            self.logger.debug(log_entry)
        else:
            self.logger.info(log_entry)
            
    def _log_request(self, method, url, params=None, headers=None):
        """Log detalhado de requisição de API com formato amigável para Docker"""
        if not self.log_request_details:
            return
            
        # Cria cópia dos parâmetros para evitar modificar os originais
        safe_params = {}
        if params:
            safe_params = params.copy()
            
            # Remove dados sensíveis
            if 'signature' in safe_params:
                safe_params['signature'] = safe_params['signature'][:8] + '...'
                
        # Cria cópia dos headers para evitar modificar os originais
        safe_headers = {}
        if headers:
            safe_headers = headers.copy()
            
            # Remove dados sensíveis
            if 'X-MBX-APIKEY' in safe_headers and self.show_masked_credentials:
                key = safe_headers['X-MBX-APIKEY']
                if len(key) > 8:
                    safe_headers['X-MBX-APIKEY'] = key[:4] + '...' + key[-4:]
                else:
                    safe_headers['X-MBX-APIKEY'] = '****'
            elif 'X-MBX-APIKEY' in safe_headers:
                safe_headers['X-MBX-APIKEY'] = '[REDACTED]'
                
        self._log_structured(
            "debug",
            f"API Request: {method} {url}",
            {
                "method": method,
                "url": url,
                "params": safe_params,
                "headers": safe_headers,
                "environment": "testnet" if self.testnet else "production"
            }
        )
        
    def _log_response(self, status_code, content, elapsed_ms=None):
        """Log detalhado de resposta de API com formato amigável para Docker"""
        if not self.log_response_details:
            return
            
        # Prepara o conteúdo para log, limitando o tamanho
        if isinstance(content, str) and len(content) > 500:
            safe_content = content[:500] + "..."
        elif isinstance(content, dict):
            # Para dicts, converte para string e limita tamanho
            safe_content = json.dumps(content, ensure_ascii=False)[:500]
            if len(safe_content) == 500:
                safe_content += "..."
        else:
            safe_content = str(content)
            
        self._log_structured(
            "debug" if status_code < 400 else "error",
            f"API Response: Status {status_code}",
            {
                "status_code": status_code,
                "response": safe_content,
                "elapsed_ms": elapsed_ms
            }
        )
