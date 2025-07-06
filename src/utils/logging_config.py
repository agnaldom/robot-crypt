"""
Sistema de logging configurável para o sistema de treinamento.
"""

import logging
import logging.handlers
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class LoggingConfig:
    """
    Configurador de logging para o sistema de treinamento.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o configurador de logging.
        
        Args:
            config: Configurações de logging
        """
        self.config = config
        self.loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """
        Configura o sistema de logging.
        """
        # Configuração básica do logging
        log_level = getattr(logging, self.config.get('level', 'INFO').upper())
        
        # Remove handlers existentes
        for logger_name in logging.root.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
        
        # Configura o formato
        formatter = logging.Formatter(
            self.config.get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        
        # Configura handler para console
        if self.config.get('console', {}).get('enabled', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            
            # Adiciona ao logger raiz
            logging.root.addHandler(console_handler)
            logging.root.setLevel(log_level)
        
        # Configura handlers para arquivos
        self._setup_file_handlers(formatter, log_level)
        
        # Configura loggers específicos
        self._setup_specific_loggers(formatter, log_level)
    
    def _setup_file_handlers(self, formatter: logging.Formatter, log_level: int):
        """
        Configura handlers para arquivos de log.
        """
        files_config = self.config.get('files', {})
        rotation_config = self.config.get('rotation', {})
        
        for log_type, file_path in files_config.items():
            if not file_path:
                continue
            
            # Cria o diretório se não existir
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configura rotação de arquivos
            if rotation_config.get('enabled', True):
                handler = logging.handlers.RotatingFileHandler(
                    filename=file_path,
                    maxBytes=rotation_config.get('max_size', 10 * 1024 * 1024),  # 10MB
                    backupCount=rotation_config.get('backup_count', 5),
                    encoding='utf-8'
                )
            else:
                handler = logging.FileHandler(file_path, encoding='utf-8')
            
            handler.setFormatter(formatter)
            handler.setLevel(log_level)
            
            # Adiciona ao logger específico
            logger_name = f"trading_bot.{log_type}"
            logger = logging.getLogger(logger_name)
            logger.addHandler(handler)
            logger.setLevel(log_level)
            
            self.loggers[log_type] = logger
    
    def _setup_specific_loggers(self, formatter: logging.Formatter, log_level: int):
        """
        Configura loggers específicos.
        """
        # Logger para dados de mercado
        market_logger = logging.getLogger('trading_bot.market_data')
        market_logger.setLevel(log_level)
        
        # Logger para modelo ML
        ml_logger = logging.getLogger('trading_bot.ml_model')
        ml_logger.setLevel(log_level)
        
        # Logger para sinais de trading
        signals_logger = logging.getLogger('trading_bot.signals')
        signals_logger.setLevel(log_level)
        
        # Logger para erros
        error_logger = logging.getLogger('trading_bot.errors')
        error_logger.setLevel(logging.ERROR)
        
        # Armazena referências
        self.loggers.update({
            'market_data': market_logger,
            'ml_model': ml_logger,
            'signals': signals_logger,
            'errors': error_logger
        })
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtém um logger específico.
        
        Args:
            name: Nome do logger
        
        Returns:
            Logger configurado
        """
        if name in self.loggers:
            return self.loggers[name]
        
        # Cria um novo logger se não existir
        logger = logging.getLogger(f'trading_bot.{name}')
        logger.setLevel(getattr(logging, self.config.get('level', 'INFO').upper()))
        
        self.loggers[name] = logger
        return logger
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """
        Registra informações de performance.
        
        Args:
            operation: Nome da operação
            duration: Duração em segundos
            details: Detalhes adicionais
        """
        perf_logger = self.get_logger('performance')
        
        message = f"Performance - {operation}: {duration:.2f}s"
        if details:
            message += f" - Details: {details}"
        
        perf_logger.info(message)
    
    def log_market_data(self, symbol: str, data_type: str, message: str):
        """
        Registra informações de dados de mercado.
        
        Args:
            symbol: Símbolo da criptomoeda
            data_type: Tipo de dados (price, volume, etc.)
            message: Mensagem de log
        """
        market_logger = self.get_logger('market_data')
        market_logger.info(f"[{symbol}] {data_type}: {message}")
    
    def log_ml_event(self, event_type: str, message: str, details: Dict[str, Any] = None):
        """
        Registra eventos de machine learning.
        
        Args:
            event_type: Tipo de evento (training, prediction, etc.)
            message: Mensagem de log
            details: Detalhes adicionais
        """
        ml_logger = self.get_logger('ml_model')
        
        log_message = f"ML Event - {event_type}: {message}"
        if details:
            log_message += f" - Details: {details}"
        
        ml_logger.info(log_message)
    
    def log_signal(self, symbol: str, signal_type: str, confidence: float, message: str):
        """
        Registra sinais de trading.
        
        Args:
            symbol: Símbolo da criptomoeda
            signal_type: Tipo de sinal (BUY, SELL, HOLD)
            confidence: Nível de confiança
            message: Mensagem de log
        """
        signals_logger = self.get_logger('signals')
        signals_logger.info(f"SIGNAL [{symbol}] {signal_type} (confidence: {confidence:.2f}): {message}")
    
    def log_error(self, error: Exception, context: str = None):
        """
        Registra erros com contexto.
        
        Args:
            error: Exceção capturada
            context: Contexto onde o erro ocorreu
        """
        error_logger = self.get_logger('errors')
        
        error_message = f"Error: {str(error)}"
        if context:
            error_message = f"Error in {context}: {str(error)}"
        
        error_logger.error(error_message, exc_info=True)
    
    def create_session_log(self, session_type: str) -> str:
        """
        Cria um arquivo de log específico para uma sessão.
        
        Args:
            session_type: Tipo de sessão (training, prediction, etc.)
        
        Returns:
            Caminho do arquivo de log da sessão
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_log_path = Path(self.config.get('files', {}).get('training', 'logs/training.log')).parent / f"{session_type}_{timestamp}.log"
        
        # Cria o diretório se não existir
        session_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cria handler específico para a sessão
        session_handler = logging.FileHandler(session_log_path, encoding='utf-8')
        session_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Cria logger específico para a sessão
        session_logger = logging.getLogger(f'trading_bot.session.{session_type}')
        session_logger.addHandler(session_handler)
        session_logger.setLevel(getattr(logging, self.config.get('level', 'INFO').upper()))
        
        return str(session_log_path)
    
    def cleanup_old_logs(self, max_age_days: int = 30):
        """
        Remove arquivos de log antigos.
        
        Args:
            max_age_days: Idade máxima dos logs em dias
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for log_type, file_path in self.config.get('files', {}).items():
            if not file_path:
                continue
            
            log_dir = Path(file_path).parent
            if not log_dir.exists():
                continue
            
            # Remove arquivos antigos
            for log_file in log_dir.glob('*.log*'):
                try:
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        log_file.unlink()
                        logging.info(f"Removed old log file: {log_file}")
                except Exception as e:
                    logging.warning(f"Could not remove log file {log_file}: {e}")


def setup_logging(config: Dict[str, Any]) -> LoggingConfig:
    """
    Configura o sistema de logging.
    
    Args:
        config: Configurações de logging
    
    Returns:
        Instância do LoggingConfig
    """
    return LoggingConfig(config)


def get_performance_logger() -> logging.Logger:
    """
    Obtém o logger de performance.
    
    Returns:
        Logger de performance
    """
    return logging.getLogger('trading_bot.performance')


def get_market_data_logger() -> logging.Logger:
    """
    Obtém o logger de dados de mercado.
    
    Returns:
        Logger de dados de mercado
    """
    return logging.getLogger('trading_bot.market_data')


def get_ml_logger() -> logging.Logger:
    """
    Obtém o logger de machine learning.
    
    Returns:
        Logger de ML
    """
    return logging.getLogger('trading_bot.ml_model')


def get_signals_logger() -> logging.Logger:
    """
    Obtém o logger de sinais.
    
    Returns:
        Logger de sinais
    """
    return logging.getLogger('trading_bot.signals')


def get_error_logger() -> logging.Logger:
    """
    Obtém o logger de erros.
    
    Returns:
        Logger de erros
    """
    return logging.getLogger('trading_bot.errors')


# Decorador para logging de performance
def log_performance(operation_name: str = None):
    """
    Decorador para registrar performance de funções.
    
    Args:
        operation_name: Nome da operação (usa o nome da função se não especificado)
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger = get_performance_logger()
                perf_logger.info(f"Performance - {operation}: {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_logger = get_error_logger()
                error_logger.error(f"Error in {operation} after {duration:.2f}s: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator
