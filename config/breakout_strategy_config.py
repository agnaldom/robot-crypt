"""
🔧 Configuração da Estratégia de Breakout Avançada

Este arquivo contém todas as configurações necessárias para executar
a estratégia de breakout com análise de fluxo de ordens.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class BingXCredentials:
    """Credenciais da API BingX"""
    api_key: str
    api_secret: str
    testnet: bool = True  # Sempre começar com testnet


@dataclass
class RiskManagementConfig:
    """Configurações de gestão de risco"""
    risk_per_trade: float = 0.01  # 1% por trade
    leverage: int = 20  # Alavancagem 20x
    risk_reward_ratio: float = 2.0  # Mínimo 1:2
    max_position_size: float = 0.05  # 5% máximo por posição
    max_daily_loss: float = 0.05  # 5% perda máxima diária
    max_concurrent_positions: int = 3  # Máximo 3 posições simultâneas


@dataclass
class BreakoutDetectionConfig:
    """Configurações de detecção de breakout"""
    min_volume_increase: float = 2.0  # Volume 2x maior que média
    lookback_periods: int = 20  # Períodos para análise S/R
    min_confidence: float = 0.7  # Confiança mínima (70%)
    timeframe: str = '1h'  # Timeframe principal
    volume_sma_period: int = 20  # Período para SMA do volume


@dataclass
class OrderBookAnalysisConfig:
    """Configurações de análise do livro de ordens"""
    depth_levels: int = 100  # Níveis de profundidade
    imbalance_threshold_long: float = 1.5  # Ratio mínimo bid/ask para LONG
    imbalance_threshold_short: float = 0.67  # Ratio máximo bid/ask para SHORT
    wall_detection_threshold: float = 0.3  # 30% do volume para detectar wall
    top_levels_analysis: int = 20  # Analisar top 20 níveis


@dataclass
class TradingConfig:
    """Configurações de trading"""
    symbols: List[str] = None  # Lista de símbolos para trading
    check_interval: int = 60  # Intervalo de verificação (segundos)
    position_monitor_interval: int = 30  # Intervalo de monitoramento (segundos)
    trailing_stop_threshold: float = 0.10  # 10% de lucro para trailing stop
    trailing_stop_offset: float = 0.02  # 2% de offset para trailing stop
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT']


@dataclass
class NotificationConfig:
    """Configurações de notificações"""
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_to: str = ""


@dataclass
class LoggingConfig:
    """Configurações de logging"""
    log_level: str = "INFO"
    log_file: str = "logs/breakout_strategy.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class BreakoutStrategyConfig:
    """
    Configuração principal da estratégia de breakout
    """
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Carrega configurações do arquivo ou variáveis de ambiente"""
        
        # Credenciais BingX
        self.bingx = BingXCredentials(
            api_key=os.getenv('BINGX_API_KEY', ''),
            api_secret=os.getenv('BINGX_API_SECRET', ''),
            testnet=os.getenv('BINGX_TESTNET', 'true').lower() == 'true'
        )
        
        # Gestão de risco
        self.risk_management = RiskManagementConfig(
            risk_per_trade=float(os.getenv('RISK_PER_TRADE', '0.01')),
            leverage=int(os.getenv('LEVERAGE', '20')),
            risk_reward_ratio=float(os.getenv('RISK_REWARD_RATIO', '2.0')),
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '0.05')),
            max_daily_loss=float(os.getenv('MAX_DAILY_LOSS', '0.05')),
            max_concurrent_positions=int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))
        )
        
        # Detecção de breakout
        self.breakout_detection = BreakoutDetectionConfig(
            min_volume_increase=float(os.getenv('MIN_VOLUME_INCREASE', '2.0')),
            lookback_periods=int(os.getenv('LOOKBACK_PERIODS', '20')),
            min_confidence=float(os.getenv('MIN_CONFIDENCE', '0.7')),
            timeframe=os.getenv('TIMEFRAME', '1h'),
            volume_sma_period=int(os.getenv('VOLUME_SMA_PERIOD', '20'))
        )
        
        # Análise do livro de ordens
        self.order_book_analysis = OrderBookAnalysisConfig(
            depth_levels=int(os.getenv('DEPTH_LEVELS', '100')),
            imbalance_threshold_long=float(os.getenv('IMBALANCE_THRESHOLD_LONG', '1.5')),
            imbalance_threshold_short=float(os.getenv('IMBALANCE_THRESHOLD_SHORT', '0.67')),
            wall_detection_threshold=float(os.getenv('WALL_DETECTION_THRESHOLD', '0.3')),
            top_levels_analysis=int(os.getenv('TOP_LEVELS_ANALYSIS', '20'))
        )
        
        # Trading
        symbols_env = os.getenv('TRADING_SYMBOLS', '')
        symbols = symbols_env.split(',') if symbols_env else None
        
        self.trading = TradingConfig(
            symbols=symbols,
            check_interval=int(os.getenv('CHECK_INTERVAL', '60')),
            position_monitor_interval=int(os.getenv('POSITION_MONITOR_INTERVAL', '30')),
            trailing_stop_threshold=float(os.getenv('TRAILING_STOP_THRESHOLD', '0.10')),
            trailing_stop_offset=float(os.getenv('TRAILING_STOP_OFFSET', '0.02'))
        )
        
        # Notificações
        self.notifications = NotificationConfig(
            telegram_enabled=os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true',
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
            email_enabled=os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            email_smtp_server=os.getenv('EMAIL_SMTP_SERVER', ''),
            email_smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '587')),
            email_username=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            email_to=os.getenv('EMAIL_TO', '')
        )
        
        # Logging
        self.logging = LoggingConfig(
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'logs/breakout_strategy.log'),
            max_log_size=int(os.getenv('MAX_LOG_SIZE', str(10 * 1024 * 1024))),
            backup_count=int(os.getenv('BACKUP_COUNT', '5'))
        )
    
    def validate_config(self) -> List[str]:
        """
        Valida as configurações e retorna lista de erros
        """
        errors = []
        
        # Validar credenciais BingX
        if not self.bingx.api_key:
            errors.append("BingX API Key é obrigatória")
        
        if not self.bingx.api_secret:
            errors.append("BingX API Secret é obrigatória")
        
        # Validar configurações de risco
        if self.risk_management.risk_per_trade <= 0 or self.risk_management.risk_per_trade > 0.1:
            errors.append("Risk per trade deve estar entre 0 e 0.1 (10%)")
        
        if self.risk_management.leverage < 1 or self.risk_management.leverage > 125:
            errors.append("Leverage deve estar entre 1 e 125")
        
        if self.risk_management.risk_reward_ratio < 1:
            errors.append("Risk reward ratio deve ser >= 1")
        
        # Validar símbolos
        if not self.trading.symbols:
            errors.append("Lista de símbolos não pode estar vazia")
        
        # Validar configurações de breakout
        if self.breakout_detection.min_volume_increase < 1:
            errors.append("Min volume increase deve ser >= 1")
        
        if self.breakout_detection.min_confidence < 0 or self.breakout_detection.min_confidence > 1:
            errors.append("Min confidence deve estar entre 0 e 1")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte configuração para dicionário
        """
        return {
            'bingx': self.bingx.__dict__,
            'risk_management': self.risk_management.__dict__,
            'breakout_detection': self.breakout_detection.__dict__,
            'order_book_analysis': self.order_book_analysis.__dict__,
            'trading': self.trading.__dict__,
            'notifications': self.notifications.__dict__,
            'logging': self.logging.__dict__
        }
    
    def print_config(self):
        """
        Imprime configuração atual (sem secrets)
        """
        config_dict = self.to_dict()
        
        # Mascarar secrets
        if config_dict['bingx']['api_key']:
            config_dict['bingx']['api_key'] = config_dict['bingx']['api_key'][:8] + "..."
        if config_dict['bingx']['api_secret']:
            config_dict['bingx']['api_secret'] = "***"
        
        print("📊 Configuração da Estratégia de Breakout:")
        print("=" * 50)
        
        for section, values in config_dict.items():
            print(f"\n{section.upper()}:")
            for key, value in values.items():
                print(f"  {key}: {value}")


# Exemplo de uso
if __name__ == "__main__":
    # Carregar configuração
    config = BreakoutStrategyConfig()
    
    # Validar configuração
    errors = config.validate_config()
    if errors:
        print("❌ Erros de configuração:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuração válida!")
        config.print_config()
