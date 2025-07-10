"""
Cache Module for Robot-Crypt
============================

Módulo responsável pelo cache inteligente de dados históricos.

Principais componentes:
- HistoricalCacheManager: Gerenciador principal do cache
- HistoricalDataProvider: Interface simplificada para estratégias
- Funções convenientes para acesso aos dados
- Sistema de priorização: SEMPRE Cache -> API -> Salva no Cache

Prioridade ABSOLUTA para banco de dados!
"""

# Importa funcionalidades principais do cache histórico
from .historical_cache_manager import (
    HistoricalCacheManager,
    CacheStats,
    cache_manager,
    initialize_historical_cache,
    get_historical_data_cached,
    get_cache_status
)

# Importa funcionalidades de integração simplificada
from .cache_integration import (
    HistoricalDataProvider,
    data_provider,
    get_market_data,
    get_latest_price,
    get_price_range,
    ensure_cache_ready,
    is_cache_healthy,
    maintain_cache_health,
    CacheIntegrationError
)

__all__ = [
    # Cache Manager principal
    'HistoricalCacheManager',
    'CacheStats', 
    'cache_manager',
    'initialize_historical_cache',
    'get_historical_data_cached',
    'get_cache_status',
    
    # Integração simplificada (recomendado para uso nas estratégias)
    'HistoricalDataProvider',
    'data_provider',
    'get_market_data',      # <- Função principal para obter dados
    'get_latest_price',     # <- Função para preço mais recente
    'get_price_range',      # <- Função para análise de faixas
    'ensure_cache_ready',   # <- Função para garantir cache pronto
    'is_cache_healthy',     # <- Função para verificar saúde
    'maintain_cache_health', # <- Função para manutenção
    'CacheIntegrationError'
]
