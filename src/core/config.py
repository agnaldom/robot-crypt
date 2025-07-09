#!/usr/bin/env python3
"""
Módulo de configuração para Robot-Crypt FastAPI
"""
import os
import secrets
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from urllib.parse import unquote

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


def sanitize_trading_symbol(symbol: str) -> str:
    """
    Sanitiza um símbolo de trading removendo quotes, brackets e decodificando URL.
    Converte símbolos como "BNBUSDT" para "BNB/USDT".
    
    Args:
        symbol: Símbolo a ser sanitizado
        
    Returns:
        Símbolo limpo no formato "BASE/QUOTE"
    """
    if not symbol:
        return symbol
    
    # Remove URL encoding
    symbol = unquote(symbol)
    
    # Remove quotes duplas e simples
    symbol = symbol.replace('"', '').replace("'", '')
    
    # Remove brackets
    symbol = symbol.replace('[', '').replace(']', '')
    
    # Remove espaços em branco
    symbol = symbol.strip().upper()
    
    # Se já tem barra, apenas retorna
    if '/' in symbol:
        return symbol
    
    # Converte formato "BNBUSDT" para "BNB/USDT"
    # Lista de possíveis quote assets (moedas de cotação)
    quote_assets = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB', 'BRL', 'EUR', 'USD']
    
    for quote in quote_assets:
        if symbol.endswith(quote) and len(symbol) > len(quote):
            base = symbol[:-len(quote)]
            return f"{base}/{quote}"
    
    # Se não conseguir converter, retorna como está
    return symbol


class Settings(BaseSettings):
    """
    Configurações da aplicação Robot-Crypt FastAPI.
    Carrega configurações de variáveis de ambiente com fallback para valores padrão.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="",
        json_schema_extra={
            "env_prefix": "",
            "env_nested_delimiter": "__"
        }
    )
    
    # === CONFIGURAÇÕES DA APLICAÇÃO ===
    APP_NAME: str = Field(default="Robot-Crypt API", description="Nome da aplicação")
    APP_VERSION: str = Field(default="1.0.0", description="Versão da aplicação")
    DEBUG: bool = Field(default=False, description="Modo de debug")
    HOST: str = Field(default="0.0.0.0", description="Host do servidor")
    PORT: int = Field(default=8000, description="Porta do servidor")
    
    # === CONFIGURAÇÕES DE SEGURANÇA ===
    SECRET_KEY: str = Field(
        default=None,
        description="Chave secreta para JWT (OBRIGATÓRIA em produção)"
    )
    ALGORITHM: str = Field(default="HS256", description="Algoritmo de hash para JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Tempo de expiração do token de acesso (minutos)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Tempo de expiração do token de refresh (dias)"
    )
    
    # === CONFIGURAÇÕES DE USUÁRIO PADRÃO ===
    USER_EMAIL: str = Field(
        default="admin@robotcrypt.com",
        description="Email do superadmin"
    )
    USER_PASSWORD: str = Field(
        default="Robot123!@#",
        description="Senha do superadmin"
    )
    USER_NAME: str = Field(
        default="Admin Robot-Crypt",
        description="Nome do superadmin"
    )
    
    # === CONFIGURAÇÕES DO BANCO DE DADOS ===
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/robot_crypt",
        description="URL de conexão com o banco de dados"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Habilitar logs SQL do SQLAlchemy"
    )
    
    # === CONFIGURAÇÕES DE CORS ===
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Origens permitidas para CORS (formato string)",
        alias="ALLOWED_ORIGINS"
    )
    
    # === CONFIGURAÇÕES DA BINANCE ===
    BINANCE_API_KEY: Optional[str] = Field(
        default=None,
        description="Chave da API da Binance"
    )
    BINANCE_API_SECRET: Optional[str] = Field(
        default=None,
        description="Segredo da API da Binance"
    )
    USE_TESTNET: bool = Field(
        default=True,
        description="Usar Testnet da Binance"
    )
    SIMULATION_MODE: bool = Field(
        default=True,
        description="Modo de simulação (sem operações reais)"
    )
    
    # === CONFIGURAÇÕES DE TRADING ===
    TRADING_PAIRS_RAW: str = Field(
        default='["BTC/USDT", "ETH/USDT", "BNB/USDT"]',
        description="Pares de trading monitorados (formato string)",
        alias="TRADING_PAIRS"
    )
    TRADE_AMOUNT: float = Field(
        default=100.0,
        description="Valor padrão por operação"
    )
    TAKE_PROFIT_PERCENTAGE: float = Field(
        default=2.0,
        description="Percentual de take profit padrão"
    )
    STOP_LOSS_PERCENTAGE: float = Field(
        default=1.0,
        description="Percentual de stop loss padrão"
    )
    MAX_CONSECUTIVE_LOSSES: int = Field(
        default=3,
        description="Máximo de perdas consecutivas"
    )
    RISK_REDUCTION_FACTOR: float = Field(
        default=0.5,
        description="Fator de redução de risco após perdas"
    )
    
    # === CONFIGURAÇÕES DE NOTIFICAÇÃO ===
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None,
        description="Token do bot do Telegram"
    )
    TELEGRAM_CHAT_ID: Optional[str] = Field(
        default=None,
        description="ID do chat do Telegram"
    )
    
    # === CONFIGURAÇÕES DE APIs EXTERNAS ===
    COINMARKETCAP_API_KEY: Optional[str] = Field(
        default=None,
        description="Chave da API do CoinMarketCap"
    )
    COINMARKETCAL_API_KEY: Optional[str] = Field(
        default=None,
        description="Chave da API do CoinMarketCal"
    )
    CRYPTOPANIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Chave da API do CryptoPanic"
    )
    NEWS_API_KEY: Optional[str] = Field(
        default=None,
        description="Chave da API do NewsAPI (newsapi.org)"
    )
    
    # === CONFIGURAÇÕES DE CACHE E RATE LIMITING ===
    CACHE_TTL: int = Field(
        default=300,
        description="Tempo de vida do cache (segundos)"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Limite de requisições por minuto"
    )
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="URL de conexão com Redis para rate limiting distribuído"
    )
    WHITELISTED_IPS: str = Field(
        default="127.0.0.1,localhost,::1,0.0.0.0",
        description="IPs com rate limiting mais leniente (separados por vírgula)"
    )
    
    # === CONFIGURAÇÕES DE LOGGING ===
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_FILE: str = Field(
        default="logs/robot_crypt.log",
        description="Caminho do arquivo de log"
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Valida a chave secreta para JWT."""
        if not v:
            # Em desenvolvimento, gera uma chave temporária
            import os
            if os.environ.get("DEBUG", "false").lower() == "true":
                return secrets.token_urlsafe(32)
            raise ValueError("SECRET_KEY é obrigatória em produção. Defina uma chave forte de pelo menos 32 caracteres.")
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres para segurança adequada.")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Valida e converte a URL do banco de dados."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    @property
    def TRADING_PAIRS(self) -> List[str]:
        """Converte TRADING_PAIRS_RAW em lista de strings."""
        v = self.TRADING_PAIRS_RAW
        
        if not v:
            return ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        
        # Remove espaços em branco no início e fim
        v = v.strip()
        
        try:
            # Tenta fazer parse como JSON
            trading_pairs = json.loads(v)
            if isinstance(trading_pairs, list):
                return [sanitize_trading_symbol(pair) for pair in trading_pairs if pair]
            else:
                # Se não for lista, trata como string única
                return [sanitize_trading_symbol(str(trading_pairs))]
        except (json.JSONDecodeError, TypeError, ValueError):
            # Se falhar JSON parse, tenta como CSV
            pairs = [pair.strip() for pair in v.split(",") if pair.strip()]
            if pairs:
                return [sanitize_trading_symbol(pair) for pair in pairs]
            else:
                # Se não conseguir parsear, retorna lista padrão
                return ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Converte ALLOWED_ORIGINS_RAW em lista de strings."""
        v = self.ALLOWED_ORIGINS_RAW
        
        if not v:
            return ["http://localhost:3000", "http://localhost:8080"]
        
        # Remove espaços em branco no início e fim
        v = v.strip()
        
        # Parse como CSV (comma-separated values)
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        if origins:
            return origins
        else:
            # Se não conseguir parsear, retorna lista padrão
            return ["http://localhost:3000", "http://localhost:8080"]
    
    @property
    def notifications_enabled(self) -> bool:
        """Verifica se as notificações estão habilitadas."""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)
    
    @property
    def whitelisted_ips_list(self) -> List[str]:
        """Converte WHITELISTED_IPS em lista de strings."""
        if not self.WHITELISTED_IPS:
            return ["127.0.0.1", "localhost", "::1", "0.0.0.0"]
        
        # Parse como CSV (comma-separated values)
        ips = [ip.strip() for ip in self.WHITELISTED_IPS.split(",") if ip.strip()]
        if ips:
            return ips
        else:
            # Se não conseguir parsear, retorna lista padrão
            return ["127.0.0.1", "localhost", "::1", "0.0.0.0"]
    
    def get_binance_config(self) -> Dict[str, Any]:
        """Retorna configuração da Binance."""
        return {
            "api_key": self.BINANCE_API_KEY,
            "api_secret": self.BINANCE_API_SECRET,
            "testnet": self.USE_TESTNET,
            "simulation": self.SIMULATION_MODE
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Retorna configuração de trading."""
        return {
            "pairs": self.TRADING_PAIRS,
            "trade_amount": self.TRADE_AMOUNT,
            "take_profit": self.TAKE_PROFIT_PERCENTAGE / 100,
            "stop_loss": self.STOP_LOSS_PERCENTAGE / 100,
            "max_consecutive_losses": self.MAX_CONSECUTIVE_LOSSES,
            "risk_reduction_factor": self.RISK_REDUCTION_FACTOR
        }


# Instância global das configurações
settings = Settings()


# Classe de configuração legada para compatibilidade
class Config:
    """Classe de configuração do bot - mantida para compatibilidade."""
    
    def __init__(self, config_file=None):
        """Inicializa a configuração do bot."""
        # Valores padrão
        self.api_key = os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = os.environ.get("BINANCE_API_SECRET", "")
        
        # Verifica se deve usar testnet ou produção
        testnet_mode = os.environ.get("USE_TESTNET", "true").lower()
        self.use_testnet = testnet_mode in ["true", "1", "yes", "y", "sim", "s"]
        
        # Verifica se deve usar modo de simulação (sem API)
        simulation_mode = os.environ.get("SIMULATION_MODE", "false").lower()
        self.simulation_mode = simulation_mode in ["true", "1", "yes", "y", "sim", "s"]
        
        # Controle de perdas consecutivas
        self.max_consecutive_losses = int(os.environ.get("MAX_CONSECUTIVE_LOSSES", "3"))
        self.risk_reduction_factor = float(os.environ.get("RISK_REDUCTION_FACTOR", "0.5"))
        
        # Verifica se existem chaves específicas para testnet
        if self.use_testnet:
            testnet_key = os.environ.get("TESTNET_API_KEY")
            testnet_secret = os.environ.get("TESTNET_API_SECRET")
            
            if testnet_key and testnet_secret:
                self.api_key = testnet_key
                self.api_secret = testnet_secret
        
        # Conversão do intervalo de trading para segundos
        trading_interval = os.environ.get("TRADING_INTERVAL", "5m")
        self.check_interval = self._convert_interval_to_seconds(trading_interval)
        self.max_trades_per_day = 3  # Máximo de 3 trades por dia (conforme plano)
        
        # Carrega configurações de notificação do Telegram
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.notifications_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        
        # Carrega configurações personalizadas de trading do arquivo .env, se disponíveis
        trade_amount = os.environ.get("TRADE_AMOUNT")
        take_profit_percentage = os.environ.get("TAKE_PROFIT_PERCENTAGE")
        stop_loss_percentage = os.environ.get("STOP_LOSS_PERCENTAGE")
        max_hold_time = os.environ.get("MAX_HOLD_TIME")
        
        # Tenta pegar entry_delay, mas sanitiza para remover comentários
        entry_delay_str = os.environ.get("ENTRY_DELAY", "")
        if entry_delay_str:
            # Remove qualquer comentário que possa estar na string
            entry_delay = entry_delay_str.split('#')[0].strip()
        else:
            entry_delay = None
        
        # Carrega pares de trading do arquivo .env
        trading_pairs_str = os.environ.get("TRADING_PAIRS", "")
        self.trading_pairs = []
        
        # Lista de pares disponíveis na TestNet da Binance
        testnet_supported_pairs = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "TRX/USDT", "XRP/USDT", 
            "LTC/USDT", "BCH/USDT", "EOS/USDT", "ADA/USDT", "DOT/USDT",
            "LINK/USDT", "BTC/BUSD", "ETH/BUSD", "BNB/BUSD", "BTC/ETH",
            "BNB/BTC", "ETH/BTC"
        ]
        
        if trading_pairs_str:
            # Converte de BNBUSDT para BNB/USDT (formato aceito pela API)
            raw_pairs = trading_pairs_str.split(",")
            for pair in raw_pairs:
                pair = pair.strip()
                if len(pair) >= 6:  # Pelo menos 3 letras para cada símbolo
                    # Descobre o ponto de divisão (geralmente XXXYYY onde XXX é a base e YYY é a cotação)
                    for i in range(3, len(pair) - 2):
                        # Tenta fazer a divisão em pontos comuns (BTC, ETH, USDT, BRL, etc)
                        if pair[i:i+3] in ["BTC", "ETH", "USD", "BRL", "BNB", "EUR"]:
                            formatted_pair = f"{pair[:i]}/{pair[i:]}"
                            
                            # Se estiver em modo testnet, só adiciona pares suportados
                            if self.use_testnet:
                                if formatted_pair in testnet_supported_pairs:
                                    self.trading_pairs.append(formatted_pair)
                                else:
                                    print(f"Aviso: Par {formatted_pair} ignorado porque não é suportado na TestNet")
                            else:
                                self.trading_pairs.append(formatted_pair)
                            break
                    else:
                        # Se não conseguir dividir, usa o formato original
                        self.trading_pairs.append(pair)
        
        # Log dos pares de trading carregados
        if self.trading_pairs:
            print(f"Pares de trading carregados do .env: {self.trading_pairs}")
        
        # Estratégia de Scalping (Fase 2)
        self.scalping = {
            "risk_per_trade": 0.01,  # 1% de risco por operação
            "profit_target": float(take_profit_percentage) / 100 if take_profit_percentage else 0.02,   # Padrão: 2% 
            "stop_loss": float(stop_loss_percentage) / 100 if stop_loss_percentage else 0.005,      # Padrão: 0.5%
            "max_position_size": 0.05,  # Máximo 5% do capital por posição
            "trade_amount": float(trade_amount) if trade_amount else 100.0  # Valor padrão: R$100
        }
        
        # Estratégia de Swing Trading (Fase 3) - Atualizada para altcoins voláteis
        self.swing_trading = {
            "min_volume_increase": 0.50,  # 50% acima da média diária para altcoins voláteis
            "profit_target": float(take_profit_percentage) / 100 if take_profit_percentage else 0.15,  # 15% para altcoins de alta volatilidade
            "stop_loss": float(stop_loss_percentage) / 100 if stop_loss_percentage else 0.03,          # Padrão: 3%
            "max_hold_time": float(max_hold_time) / 3600 if max_hold_time else 48,  # Converter segundos para horas
            "max_position_size": 0.05,    # Máximo 5% do capital por posição
            "entry_delay": 60,  # Delay entre análise e execução (segundos)
            "volatility_threshold": 0.3,  # Threshold para identificar altcoins voláteis
            "use_ai_timing": True,  # Usar análise IA para timing
            "ai_confidence_min": 0.6  # Confiança mínima da IA para executar trades
        }
        
        # Carrega configuração de arquivo se fornecido
        if config_file:
            self._load_config(config_file)
        else:
            # Tenta carregar do arquivo padrão
            default_config = Path.home() / ".robot-crypt" / "config.json"
            if default_config.exists():
                self._load_config(default_config)
    
    def _load_config(self, config_file):
        """Carrega configuração de arquivo"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Atualiza atributos com valores do arquivo
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except Exception as e:
            print(f"Erro ao carregar arquivo de configuração: {str(e)}")
    
    def save_config(self, config_file=None):
        """Salva configuração em arquivo"""
        if not config_file:
            config_dir = Path.home() / ".robot-crypt"
            config_dir.mkdir(exist_ok=True, parents=True)
            config_file = config_dir / "config.json"
        
        try:
            # Cria dicionário de configuração
            config = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "use_testnet": self.use_testnet,
                "check_interval": self.check_interval,
                "max_trades_per_day": self.max_trades_per_day,
                "scalping": self.scalping,
                "swing_trading": self.swing_trading
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar arquivo de configuração: {str(e)}")
    
    def get_balance(self, account_info):
        """Calcula o saldo total em BRL ou equivalente"""
        import logging
        logger = logging.getLogger("robot-crypt")
        balance = 0.0
        
        # Se não tivermos dados da conta, retorna o valor padrão para simulação
        if not account_info or not isinstance(account_info, dict):
            logger.warning("Dados da conta inválidos ou ausentes, usando valor padrão para simulação: 100.0 BRL")
            return 100.0  # Valor padrão para simulação
        
        # Taxas de conversão aproximadas para BRL
        conversion_rates = {
            'BRL': 1.0,
            'USDT': 5.0,       # 1 USDT ≈ 5 BRL
            'BTC': 150000.0,   # 1 BTC ≈ 150,000 BRL
            'ETH': 8500.0,     # 1 ETH ≈ 8,500 BRL
            'BNB': 2250.0      # 1 BNB ≈ 2,250 BRL
        }
        
        try:
            # Pega os saldos da conta
            if 'balances' in account_info:
                for asset in account_info['balances']:
                    try:
                        asset_name = asset['asset']
                        asset_balance = float(asset.get('free', '0')) + float(asset.get('locked', '0'))
                        
                        # Só considera ativos com saldo positivo
                        if asset_balance > 0:
                            # Se temos taxa de conversão para esse ativo
                            if asset_name in conversion_rates:
                                asset_value = asset_balance * conversion_rates[asset_name]
                                balance += asset_value
                                logger.debug(f"Saldo de {asset_name}: {asset_balance} = {asset_value:.2f} BRL")
                            # Para outros ativos, tentamos uma estimativa conservadora
                            else:
                                # Assumimos um valor conservador de 1 BRL por unidade para ativos desconhecidos
                                # Se for um altcoin, isso pode estar subestimado, mas é melhor que ignorar
                                estimated_value = asset_balance * 1.0  # valor conservador
                                balance += estimated_value
                                logger.debug(f"Saldo de {asset_name}: {asset_balance} (valor estimado: {estimated_value:.2f} BRL)")
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Erro ao processar saldo do ativo: {str(e)}")
                        continue
            
            # Se ainda não encontramos saldo, usar valor padrão para simulação
            if balance == 0:
                balance = 100.0
                logger.warning("Nenhum saldo detectado, usando valor padrão para simulação: 100.0 BRL")
                
            logger.info(f"Saldo total estimado: {balance:.2f} BRL")
            return balance
            
        except Exception as e:
            logger.error(f"Erro ao calcular saldo total: {str(e)}")
            logger.error("Usando valor padrão de 100.0 BRL")
            return 100.0  # Valor padrão em caso de erro
    
    def _convert_interval_to_seconds(self, interval):
        """Converte intervalos como '1m', '15m', '1h' para segundos"""
        import logging
        logger = logging.getLogger("robot-crypt")
        
        try:
            # Extrai o valor numérico e a unidade
            value = int(''.join(filter(str.isdigit, interval)))
            unit = ''.join(filter(str.isalpha, interval)).lower()
            
            # Conversão para segundos com base na unidade
            if unit == 'm' or unit == 'min':
                seconds = value * 60
            elif unit == 'h' or unit == 'hour':
                seconds = value * 3600
            elif unit == 'd' or unit == 'day':
                seconds = value * 86400
            elif unit == 's' or unit == 'sec':
                seconds = value
            else:
                logger.warning(f"Unidade de intervalo não reconhecida: {unit}. Usando padrão de 300 segundos.")
                seconds = 300
                
            logger.info(f"Intervalo de verificação configurado: {interval} ({seconds} segundos)")
            return seconds
            
        except Exception as e:
            logger.error(f"Erro ao converter intervalo {interval}: {str(e)}. Usando padrão de 300 segundos.")
            return 300  # Padrão: 5 minutos
