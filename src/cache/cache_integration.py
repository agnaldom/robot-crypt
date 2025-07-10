#!/usr/bin/env python3
"""
Módulo de Integração do Cache Histórico
=======================================

Este módulo fornece funções utilitárias para integrar facilmente o cache histórico
com as estratégias de trading e outros componentes do Robot-Crypt.

Autor: Robot-Crypt Team
Data: 2024
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from src.cache.historical_cache_manager import cache_manager, get_cache_status
from src.core.logging_setup import logger


class CacheIntegrationError(Exception):
    """Exceção personalizada para erros de integração do cache."""
    pass


class HistoricalDataProvider:
    """
    Provedor de dados históricos que integra cache e API.
    
    Esta classe atua como uma interface simplificada para obter dados históricos,
    garantindo que o cache seja sempre consultado primeiro.
    """
    
    def __init__(self):
        """Inicializa o provedor de dados históricos."""
        self.cache_manager = cache_manager
        self.request_count = 0
        self.cache_hit_count = 0
        
    def get_market_data(
        self, 
        symbol: str, 
        interval: str = '1d',
        period: Union[int, str] = 30,
        force_refresh: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém dados de mercado com prioridade para cache.
        
        Args:
            symbol: Símbolo da moeda (ex: 'BTCUSDT')
            interval: Intervalo dos dados ('1d', '4h', '1h', '15m')
            period: Período dos dados (int para dias ou str para períodos específicos)
            force_refresh: Se True, força busca na API
            
        Returns:
            Lista de dados históricos ou None se não encontrado
        """
        try:
            # Converte período para dias se necessário
            if isinstance(period, str):
                days_back = self._convert_period_to_days(period)
            else:
                days_back = period
            
            self.request_count += 1
            
            logger.info(f"🔍 Buscando dados para {symbol} {interval} ({days_back} dias)")
            
            # Usa o cache manager para obter dados
            data = self.cache_manager.get_historical_data(
                symbol=symbol,
                interval=interval,
                days_back=days_back,
                force_api=force_refresh
            )
            
            if data:
                # Verifica se veio do cache ou da API
                status = get_cache_status()
                if status['cache_hits'] > self.cache_hit_count:
                    self.cache_hit_count += 1
                    logger.info(f"✅ Dados obtidos do CACHE para {symbol} {interval}")
                else:
                    logger.info(f"🌐 Dados obtidos da API para {symbol} {interval}")
                
                return data
            else:
                logger.warning(f"⚠️ Nenhum dado encontrado para {symbol} {interval}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados para {symbol}: {str(e)}")
            raise CacheIntegrationError(f"Falha ao obter dados para {symbol}: {str(e)}")
    
    def get_multiple_symbols_data(
        self, 
        symbols: List[str], 
        interval: str = '1d',
        period: int = 30
    ) -> Dict[str, Optional[List[Dict[str, Any]]]]:
        """
        Obtém dados para múltiplos símbolos de forma eficiente.
        
        Args:
            symbols: Lista de símbolos
            interval: Intervalo dos dados
            period: Período em dias
            
        Returns:
            Dict com dados para cada símbolo
        """
        try:
            logger.info(f"📊 Buscando dados para {len(symbols)} símbolos...")
            
            results = {}
            successful_count = 0
            failed_count = 0
            
            for symbol in symbols:
                try:
                    data = self.get_market_data(symbol, interval, period)
                    results[symbol] = data
                    
                    if data:
                        successful_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao obter dados para {symbol}: {str(e)}")
                    results[symbol] = None
                    failed_count += 1
            
            logger.info(f"📈 Busca concluída: {successful_count} sucessos, {failed_count} falhas")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de múltiplos símbolos: {str(e)}")
            raise CacheIntegrationError(f"Falha na busca de múltiplos símbolos: {str(e)}")
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Obtém o preço mais recente de um símbolo.
        
        Args:
            symbol: Símbolo da moeda
            
        Returns:
            Preço mais recente ou None se não encontrado
        """
        try:
            # Busca dados do último dia
            data = self.get_market_data(symbol, '1d', 1)
            
            if data and len(data) > 0:
                # Retorna o preço de fechamento mais recente
                latest_data = data[0]  # Dados vêm ordenados por timestamp desc
                return float(latest_data.get('close', 0))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter preço mais recente para {symbol}: {str(e)}")
            return None
    
    def get_price_range(self, symbol: str, days: int = 30) -> Optional[Dict[str, float]]:
        """
        Obtém a faixa de preços (min, max, avg) para um período.
        
        Args:
            symbol: Símbolo da moeda
            days: Número de dias para análise
            
        Returns:
            Dict com min, max, avg ou None se não encontrado
        """
        try:
            data = self.get_market_data(symbol, '1d', days)
            
            if data and len(data) > 0:
                prices = [float(item.get('close', 0)) for item in data if item.get('close')]
                
                if prices:
                    return {
                        'min': min(prices),
                        'max': max(prices),
                        'avg': sum(prices) / len(prices),
                        'current': prices[0],  # Mais recente
                        'count': len(prices)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter faixa de preços para {symbol}: {str(e)}")
            return None
    
    def _convert_period_to_days(self, period: str) -> int:
        """
        Converte string de período para número de dias.
        
        Args:
            period: String do período (ex: '1w', '1m', '3m', '1y')
            
        Returns:
            Número de dias
        """
        period_map = {
            '1d': 1, '3d': 3, '1w': 7, '2w': 14, '1m': 30, 
            '3m': 90, '6m': 180, '1y': 365, '2y': 730
        }
        
        return period_map.get(period.lower(), 30)  # Default 30 dias
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do provedor de dados.
        
        Returns:
            Dict com estatísticas de uso
        """
        cache_status = get_cache_status()
        hit_rate = (self.cache_hit_count / max(self.request_count, 1)) * 100
        
        return {
            'total_requests': self.request_count,
            'cache_hits': self.cache_hit_count,
            'hit_rate': hit_rate,
            'cache_status': cache_status
        }


# Instância global do provedor de dados
data_provider = HistoricalDataProvider()


def get_market_data(
    symbol: str, 
    interval: str = '1d',
    period: Union[int, str] = 30,
    force_refresh: bool = False
) -> Optional[List[Dict[str, Any]]]:
    """
    Função conveniente para obter dados de mercado.
    
    Args:
        symbol: Símbolo da moeda (ex: 'BTCUSDT')
        interval: Intervalo dos dados ('1d', '4h', '1h', '15m')
        period: Período dos dados (int para dias ou str para períodos específicos)
        force_refresh: Se True, força busca na API
        
    Returns:
        Lista de dados históricos ou None se não encontrado
    """
    return data_provider.get_market_data(symbol, interval, period, force_refresh)


def get_latest_price(symbol: str) -> Optional[float]:
    """
    Função conveniente para obter o preço mais recente.
    
    Args:
        symbol: Símbolo da moeda
        
    Returns:
        Preço mais recente ou None se não encontrado
    """
    return data_provider.get_latest_price(symbol)


def get_price_range(symbol: str, days: int = 30) -> Optional[Dict[str, float]]:
    """
    Função conveniente para obter faixa de preços.
    
    Args:
        symbol: Símbolo da moeda
        days: Número de dias para análise
        
    Returns:
        Dict com min, max, avg ou None se não encontrado
    """
    return data_provider.get_price_range(symbol, days)


async def ensure_cache_ready(symbols: Optional[List[str]] = None) -> bool:
    """
    Garante que o cache esteja pronto para uso.
    
    Args:
        symbols: Lista de símbolos para garantir em cache
        
    Returns:
        True se cache está pronto
    """
    try:
        logger.info("🔄 Verificando se cache está pronto...")
        
        # Verifica status atual
        status = get_cache_status()
        
        if status['coverage_percentage'] >= 70:
            logger.info("✅ Cache já está adequadamente inicializado")
            return True
        
        # Se não está pronto, tenta inicializar
        logger.info("🚀 Inicializando cache...")
        from src.cache.historical_cache_manager import initialize_historical_cache
        
        success = await initialize_historical_cache(symbols)
        
        if success:
            logger.info("✅ Cache inicializado com sucesso")
            return True
        else:
            logger.warning("⚠️ Falha ao inicializar cache - dados serão buscados da API")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao preparar cache: {str(e)}")
        return False


def is_cache_healthy() -> bool:
    """
    Verifica se o cache está saudável.
    
    Returns:
        True se o cache está funcionando bem
    """
    try:
        status = get_cache_status()
        
        # Considera saudável se:
        # - Tem pelo menos 50% de cobertura
        # - Taxa de acerto é pelo menos 40%
        # - Status não é 'Baixo'
        
        is_healthy = (
            status['coverage_percentage'] >= 50 and
            status['hit_rate'] >= 40 and
            status['status'] != 'Baixo'
        )
        
        if not is_healthy:
            logger.warning(f"⚠️ Cache não está saudável: {status}")
        
        return is_healthy
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar saúde do cache: {str(e)}")
        return False


async def maintain_cache_health() -> None:
    """
    Executa manutenção para manter o cache saudável.
    Deve ser chamada periodicamente.
    """
    try:
        logger.info("🔧 Executando manutenção do cache...")
        
        # Executa manutenção automática
        await cache_manager.maintain_cache()
        
        # Verifica saúde após manutenção
        if is_cache_healthy():
            logger.info("✅ Cache está saudável após manutenção")
        else:
            logger.warning("⚠️ Cache ainda apresenta problemas após manutenção")
            
    except Exception as e:
        logger.error(f"❌ Erro na manutenção do cache: {str(e)}")


if __name__ == "__main__":
    # Teste básico do módulo
    async def test_integration():
        print("🧪 Testando integração do cache...")
        
        # Garante que cache está pronto
        await ensure_cache_ready(['BTCUSDT', 'ETHUSDT'])
        
        # Testa busca de dados
        btc_data = get_market_data('BTCUSDT', '1d', 7)
        if btc_data:
            print(f"✅ Dados obtidos para BTC: {len(btc_data)} registros")
        
        # Testa preço mais recente
        btc_price = get_latest_price('BTCUSDT')
        if btc_price:
            print(f"💰 Preço atual do BTC: ${btc_price:.2f}")
        
        # Testa faixa de preços
        btc_range = get_price_range('BTCUSDT', 30)
        if btc_range:
            print(f"📊 Faixa de preços BTC (30d): ${btc_range['min']:.2f} - ${btc_range['max']:.2f}")
        
        # Mostra estatísticas
        stats = data_provider.get_stats()
        print(f"📈 Estatísticas: {stats}")
        
        print("✅ Teste concluído!")
    
    # Executa teste
    asyncio.run(test_integration())
