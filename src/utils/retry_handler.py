#!/usr/bin/env python3
"""
Sistema de retry logic avançado para APIs lentas e instáveis
"""
import time
import logging
import random
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Estratégias de retry disponíveis"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    FIBONACCI = "fibonacci"


@dataclass
class RetryConfig:
    """Configuração para retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()


class RetryHandler:
    """Handler avançado para retry logic"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(__name__)
        
    def calculate_delay(self, attempt: int) -> float:
        """Calcula o delay baseado na estratégia configurada"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(attempt + 1)
        else:
            delay = self.config.base_delay
        
        # Aplica limite máximo
        delay = min(delay, self.config.max_delay)
        
        # Adiciona jitter para evitar thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% de variação
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calcula número de Fibonacci"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determina se deve tentar novamente baseado na exceção e tentativa"""
        # Verifica se atingiu o máximo de tentativas
        if attempt >= self.config.max_attempts:
            return False
        
        # Verifica exceções não-retryables
        if isinstance(exception, self.config.non_retryable_exceptions):
            return False
        
        # Verifica exceções retryables
        if isinstance(exception, self.config.retryable_exceptions):
            return True
        
        return False
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                self.logger.debug(f"Tentativa {attempt + 1}/{self.config.max_attempts} para {func.__name__}")
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(f"Sucesso na tentativa {attempt + 1} para {func.__name__}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                self.logger.warning(f"Tentativa {attempt + 1} falhou para {func.__name__}: {str(e)}")
                
                if not self.should_retry(e, attempt):
                    self.logger.error(f"Não retentando {func.__name__}: {type(e).__name__}")
                    break
                
                if attempt < self.config.max_attempts - 1:  # Não delay na última tentativa
                    delay = self.calculate_delay(attempt)
                    self.logger.info(f"Aguardando {delay:.2f}s antes da próxima tentativa")
                    time.sleep(delay)
        
        # Se chegou aqui, todas as tentativas falharam
        self.logger.error(f"Todas as {self.config.max_attempts} tentativas falharam para {func.__name__}")
        raise last_exception


def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = ()
):
    """
    Decorator para aplicar retry logic a funções
    
    Args:
        max_attempts: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        strategy: Estratégia de retry
        retryable_exceptions: Exceções que devem ser retentadas
        non_retryable_exceptions: Exceções que não devem ser retentadas
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions,
                non_retryable_exceptions=non_retryable_exceptions
            )
            
            retry_handler = RetryHandler(config)
            return retry_handler.execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker para evitar sobrecarregar APIs com problemas"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função através do circuit breaker"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker mudou para HALF_OPEN")
            else:
                raise Exception("Circuit breaker está OPEN - chamadas bloqueadas")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar resetar o circuit breaker"""
        if self.last_failure_time is None:
            return False
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Chamado quando operação é bem-sucedida"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.logger.info("Circuit breaker resetado para CLOSED")
    
    def _on_failure(self):
        """Chamado quando operação falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker aberto após {self.failure_count} falhas")


class AdaptiveRetryHandler:
    """Handler de retry que se adapta à qualidade da API"""
    
    def __init__(self):
        self.api_health_scores = {}  # endpoint -> score (0-100)
        self.response_times = {}     # endpoint -> list of response times
        self.logger = logging.getLogger(__name__)
    
    def get_retry_config(self, endpoint: str) -> RetryConfig:
        """Retorna configuração de retry adaptada à saúde da API"""
        health_score = self.api_health_scores.get(endpoint, 100)
        avg_response_time = self._get_avg_response_time(endpoint)
        
        if health_score >= 80:
            # API saudável - retry conservador
            return RetryConfig(
                max_attempts=2,
                base_delay=0.5,
                strategy=RetryStrategy.FIXED
            )
        elif health_score >= 60:
            # API com problemas leves - retry moderado
            return RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                strategy=RetryStrategy.LINEAR
            )
        else:
            # API com problemas sérios - retry agressivo
            return RetryConfig(
                max_attempts=5,
                base_delay=2.0,
                max_delay=30.0,
                strategy=RetryStrategy.EXPONENTIAL
            )
    
    def record_api_call(self, endpoint: str, success: bool, response_time: float):
        """Registra resultado de chamada à API para adaptar estratégia"""
        # Atualiza score de saúde
        if endpoint not in self.api_health_scores:
            self.api_health_scores[endpoint] = 100
        
        if success:
            self.api_health_scores[endpoint] = min(100, self.api_health_scores[endpoint] + 2)
        else:
            self.api_health_scores[endpoint] = max(0, self.api_health_scores[endpoint] - 10)
        
        # Atualiza tempos de resposta
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        
        self.response_times[endpoint].append(response_time)
        
        # Mantém apenas os últimos 50 registros
        if len(self.response_times[endpoint]) > 50:
            self.response_times[endpoint] = self.response_times[endpoint][-50:]
    
    def _get_avg_response_time(self, endpoint: str) -> float:
        """Calcula tempo médio de resposta"""
        times = self.response_times.get(endpoint, [])
        return sum(times) / len(times) if times else 0.0
    
    def execute_adaptive_retry(self, func: Callable, endpoint: str, *args, **kwargs) -> Any:
        """Executa função com retry adaptativo"""
        config = self.get_retry_config(endpoint)
        retry_handler = RetryHandler(config)
        
        start_time = time.time()
        try:
            result = retry_handler.execute_with_retry(func, *args, **kwargs)
            response_time = time.time() - start_time
            self.record_api_call(endpoint, True, response_time)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            self.record_api_call(endpoint, False, response_time)
            raise


# Instância global para retry adaptativo
adaptive_retry = AdaptiveRetryHandler()
