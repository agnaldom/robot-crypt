#!/usr/bin/env python3
"""
Sistema de Cache de Dados Históricos para Robot-Crypt
======================================================

Este módulo implementa um sistema de cache inteligente que:
1. Busca dados históricos na inicialização do bot
2. Armazena dados no banco de dados para acesso rápido
3. Sempre consulta o banco primeiro, depois a API da Binance
4. Mantém os dados atualizados automaticamente

Autor: Robot-Crypt Team
Data: 2024
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, text

from src.api.binance.client import BinanceClient
from src.models.price_history import PriceHistory
from src.database.database import sync_session_maker
from src.core.logging_setup import logger


@dataclass
class CacheStats:
    """Estatísticas do cache de dados históricos."""
    total_symbols: int = 0
    cached_symbols: int = 0
    api_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_update: Optional[datetime] = None
    data_coverage_days: int = 0


class HistoricalCacheManager:
    """
    Gerenciador de cache para dados históricos.
    
    Responsável por:
    - Buscar dados históricos na inicialização
    - Manter cache atualizado no banco de dados
    - Fornecer dados com prioridade: Cache -> API -> Erro
    """
    
    def __init__(self, binance_client: Optional[BinanceClient] = None):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            binance_client: Cliente Binance opcional
        """
        self.client = binance_client or BinanceClient()
        self.cache_stats = CacheStats()
        self.default_intervals = ['1d', '4h', '1h', '15m']
        self.default_history_days = 720  # 24 meses
        self.rate_limit_delay = 0.1  # 100ms entre requisições
        
        # Símbolos prioritários para cache
        self.priority_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'DOGEUSDT', 'SOLUSDT', 'MATICUSDT', 'LINKUSDT', 'LTCUSDT',
            'DOTUSDT', 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'FILUSDT'
        ]
        
    async def initialize_cache(self, symbols: Optional[List[str]] = None) -> bool:
        """
        Inicializa o cache de dados históricos NA INICIALIZAÇÃO DO BOT.
        
        ESTA É A FUNÇÃO PRINCIPAL que deve ser chamada quando o bot inicia!
        
        Args:
            symbols: Lista de símbolos para cachear (usa padrão se None)
            
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        try:
            logger.info("🚀 =================== INICIALIZANDO CACHE HISTÓRICO ====================")
            logger.info("📊 Esta operação pode demorar alguns minutos na primeira execução...")
            
            # Usa símbolos prioritários se não especificado
            if symbols is None:
                symbols = self.priority_symbols
                logger.info(f"📋 Usando símbolos prioritários padrão: {len(symbols)} símbolos")
            else:
                logger.info(f"📋 Usando símbolos fornecidos: {len(symbols)} símbolos")
            
            logger.info(f"🎯 Símbolos para cache: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
            
            self.cache_stats.total_symbols = len(symbols)
            self.cache_stats.last_update = datetime.now(timezone.utc)
            
            # Verifica quais símbolos já têm dados suficientes em cache
            logger.info("🔍 Verificando símbolos já em cache...")
            cached_symbols = self._get_cached_symbols_with_coverage()
            missing_symbols = [s for s in symbols if s not in cached_symbols]
            
            self.cache_stats.cached_symbols = len(cached_symbols)
            
            if cached_symbols:
                logger.info(f"✅ Símbolos já em cache com cobertura adequada: {len(cached_symbols)}")
                logger.info(f"📊 Cache existente: {', '.join(cached_symbols[:3])}{'...' if len(cached_symbols) > 3 else ''}")
            
            if missing_symbols:
                logger.info(f"📥 Símbolos necessitando cache: {len(missing_symbols)}")
                logger.info(f"🔄 Iniciando download de dados históricos...")
                
                success_count = 0
                error_count = 0
                
                # Busca dados históricos para símbolos em falta
                for i, symbol in enumerate(missing_symbols, 1):
                    logger.info(f"⬇️ [{i}/{len(missing_symbols)}] Cacheando {symbol}...")
                    
                    try:
                        cache_success = await self._cache_symbol_data(symbol)
                        if cache_success:
                            success_count += 1
                            logger.info(f"✅ {symbol} cacheado com sucesso")
                        else:
                            error_count += 1
                            logger.warning(f"⚠️ Falha ao cachear {symbol}")
                    except Exception as e:
                        error_count += 1
                        logger.error(f"❌ Erro ao cachear {symbol}: {str(e)}")
                    
                    # Rate limiting para evitar sobrecarga da API
                    await asyncio.sleep(self.rate_limit_delay)
                
                logger.info(f"📊 Resultado do cache: {success_count} sucessos, {error_count} erros")
            else:
                logger.info(f"✅ Todos os {len(symbols)} símbolos já estão adequadamente em cache")
            
            # Atualiza estatísticas finais
            self._update_cache_stats()
            
            # Relatório final
            logger.info("🎉 =================== CACHE HISTÓRICO INICIALIZADO ====================")
            logger.info(f"📈 Cobertura de dados: {self.cache_stats.data_coverage_days} dias")
            logger.info(f"🎯 Símbolos em cache: {self.cache_stats.cached_symbols}/{self.cache_stats.total_symbols}")
            logger.info(f"📊 Taxa de cobertura: {(self.cache_stats.cached_symbols / max(self.cache_stats.total_symbols, 1)) * 100:.1f}%")
            logger.info("✅ Cache pronto! Próximas consultas serão MUITO mais rápidas.")
            logger.info("===================================================================")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO ao inicializar cache: {str(e)}")
            logger.error("🚨 Bot continuará sem cache - dados serão buscados sempre da API")
            return False
    
    def get_historical_data(
        self, 
        symbol: str, 
        interval: str = '1d',
        days_back: int = 30,
        force_api: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém dados históricos com prioridade ABSOLUTA para cache do banco de dados.
        
        FLUXO DE PRIORIDADE:
        1. SEMPRE busca primeiro no banco de dados
        2. Se não encontrar OU dados insuficientes, busca na API da Binance
        3. Salva resultado da API no banco para próximas consultas
        
        Args:
            symbol: Símbolo da moeda
            interval: Intervalo dos dados
            days_back: Quantos dias buscar
            force_api: Se True, força busca na API mesmo com dados em cache
            
        Returns:
            Lista de dados históricos ou None se não encontrado
        """
        try:
            # PRIORIDADE 1: SEMPRE consulta o banco de dados primeiro
            logger.debug(f"🔍 Consultando banco de dados para {symbol} {interval} ({days_back} dias)")
            
            if not force_api:
                cached_data = self._get_cached_data(symbol, interval, days_back)
                if cached_data:
                    self.cache_stats.cache_hits += 1
                    logger.info(f"✅ Cache HIT: {len(cached_data)} registros encontrados para {symbol} {interval}")
                    return cached_data
                else:
                    logger.info(f"❌ Cache MISS: Nenhum dado suficiente no banco para {symbol} {interval}")
            
            # PRIORIDADE 2: Se não encontrou no banco, busca na API da Binance
            logger.info(f"🌐 Buscando {symbol} {interval} na API da Binance (últimos {days_back} dias)...")
            self.cache_stats.cache_misses += 1
            self.cache_stats.api_requests += 1
            
            # Busca na API
            api_data = self._fetch_from_api(symbol, interval, days_back)
            
            if api_data:
                # PRIORIDADE 3: Salva IMEDIATAMENTE no banco para futuras consultas
                logger.info(f"💾 Salvando {len(api_data)} registros no banco de dados...")
                save_success = self._save_to_cache(symbol, interval, api_data)
                
                if save_success:
                    logger.info(f"✅ Dados de {symbol} {interval} salvos no banco e retornados")
                else:
                    logger.warning(f"⚠️ Falha ao salvar no banco, mas retornando dados da API")
                
                return api_data
            
            logger.warning(f"⚠️ Nenhum dado encontrado na API para {symbol} {interval}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados históricos para {symbol}: {str(e)}")
            # Em caso de erro, tenta uma última busca no cache sem validação de cobertura
            try:
                logger.info(f"🔄 Tentando busca de emergência no cache para {symbol} {interval}")
                emergency_data = self._get_emergency_cached_data(symbol, interval, days_back)
                if emergency_data:
                    logger.info(f"🆘 Dados de emergência encontrados: {len(emergency_data)} registros")
                    return emergency_data
            except Exception:
                pass
            return None
    
    def _get_cached_symbols(self) -> List[str]:
        """
        Obtém lista de símbolos que já estão em cache.
        
        Returns:
            Lista de símbolos em cache
        """
        try:
            with sync_session_maker() as db:
                result = db.query(PriceHistory.symbol).distinct().all()
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Erro ao obter símbolos em cache: {str(e)}")
            return []
    
    def _get_cached_symbols_with_coverage(self) -> List[str]:
        """
        Obtém lista de símbolos que já estão em cache COM COBERTURA ADEQUADA.
        
        Returns:
            Lista de símbolos com dados suficientes em cache
        """
        try:
            symbols_with_coverage = []
            
            with sync_session_maker() as db:
                # Busca todos os símbolos únicos
                all_symbols = db.query(PriceHistory.symbol).distinct().all()
                
                for symbol_row in all_symbols:
                    symbol = symbol_row[0]
                    
                    # Verifica cobertura para o intervalo principal (1d)
                    start_date = datetime.now(timezone.utc) - timedelta(days=30)  # Últimos 30 dias
                    
                    cached_data = db.query(PriceHistory).filter(
                        and_(
                            PriceHistory.symbol == symbol,
                            PriceHistory.interval == '1d',
                            PriceHistory.timestamp >= start_date
                        )
                    ).count()
                    
                    expected_points = self._calculate_expected_points('1d', 30)
                    coverage = (cached_data / expected_points) * 100 if expected_points > 0 else 0
                    
                    # Considera adequado se tiver pelo menos 70% de cobertura
                    if coverage >= 70:
                        symbols_with_coverage.append(symbol)
                        logger.debug(f"📊 {symbol}: {coverage:.1f}% cobertura (adequado)")
                    else:
                        logger.debug(f"⚠️ {symbol}: {coverage:.1f}% cobertura (insuficiente)")
                
            return symbols_with_coverage
            
        except Exception as e:
            logger.error(f"Erro ao verificar cobertura dos símbolos: {str(e)}")
            return []
    
    def _get_cached_data(
        self, 
        symbol: str, 
        interval: str, 
        days_back: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Busca dados no cache do banco de dados com validação rigorosa.
        
        Args:
            symbol: Símbolo da moeda
            interval: Intervalo dos dados
            days_back: Quantos dias buscar
            
        Returns:
            Lista de dados do cache ou None se cobertura insuficiente
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            with sync_session_maker() as db:
                # Busca todos os dados disponíveis no período
                cached_data = db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.interval == interval,
                        PriceHistory.timestamp >= start_date
                    )
                ).order_by(PriceHistory.timestamp.desc()).all()
                
                if cached_data:
                    # Valida a cobertura de dados
                    expected_points = self._calculate_expected_points(interval, days_back)
                    actual_points = len(cached_data)
                    
                    coverage = (actual_points / expected_points) * 100 if expected_points > 0 else 0
                    
                    # Critério mais flexível: 70% para aceitar cache
                    if coverage >= 70:
                        logger.info(f"📊 Cache válido para {symbol} {interval}: {actual_points}/{expected_points} pontos ({coverage:.1f}% cobertura)")
                        return [item.to_dict() for item in cached_data]
                    else:
                        logger.info(f"⚠️ Cache insuficiente para {symbol} {interval}: {actual_points}/{expected_points} pontos ({coverage:.1f}% cobertura)")
                        return None
                else:
                    logger.info(f"💾 Nenhum dado em cache para {symbol} {interval}")
                    return None
                        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados no cache: {str(e)}")
        
        return None
    
    def _get_emergency_cached_data(
        self, 
        symbol: str, 
        interval: str, 
        days_back: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Busca dados no cache sem validação de cobertura (para situações de emergência).
        
        Args:
            symbol: Símbolo da moeda
            interval: Intervalo dos dados
            days_back: Quantos dias buscar
            
        Returns:
            Lista de QUALQUER dado disponível no cache, independente da cobertura
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            with sync_session_maker() as db:
                # Busca QUALQUER dado disponível, mesmo que seja pouco
                cached_data = db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.interval == interval,
                        PriceHistory.timestamp >= start_date
                    )
                ).order_by(PriceHistory.timestamp.desc()).all()
                
                if cached_data:
                    logger.warning(f"🆘 Usando dados de emergência: {len(cached_data)} registros para {symbol} {interval}")
                    return [item.to_dict() for item in cached_data]
                
        except Exception as e:
            logger.error(f"❌ Erro na busca de emergência: {str(e)}")
        
        return None
    
    def _fetch_from_api(
        self, 
        symbol: str, 
        interval: str, 
        days_back: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Busca dados da API da Binance.
        
        Args:
            symbol: Símbolo da moeda
            interval: Intervalo dos dados
            days_back: Quantos dias buscar
            
        Returns:
            Lista de dados da API ou None
        """
        try:
            # Calcula timestamps
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days_back)
            
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            
            # Busca dados da API
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_ts,
                end_time=end_ts,
                limit=1000
            )
            
            if not klines:
                return None
            
            # Converte para formato padrão
            data = []
            for kline in klines:
                data_point = {
                    'open_time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6]),
                    'quote_asset_volume': float(kline[7]),
                    'number_of_trades': int(kline[8]),
                    'taker_buy_base_volume': float(kline[9]),
                    'taker_buy_quote_volume': float(kline[10])
                }
                data.append(data_point)
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados da API: {str(e)}")
            return None
    
    def _save_to_cache(
        self, 
        symbol: str, 
        interval: str, 
        data: List[Dict[str, Any]]
    ) -> bool:
        """
        Salva dados no cache do banco de dados.
        
        Args:
            symbol: Símbolo da moeda
            interval: Intervalo dos dados
            data: Lista de dados para salvar
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            with sync_session_maker() as db:
                saved_count = 0
                
                for data_point in data:
                    # Verifica se já existe
                    timestamp = datetime.fromtimestamp(data_point['open_time'] / 1000)
                    
                    existing = db.query(PriceHistory).filter(
                        and_(
                            PriceHistory.symbol == symbol,
                            PriceHistory.interval == interval,
                            PriceHistory.timestamp == timestamp
                        )
                    ).first()
                    
                    if not existing:
                        price_history = PriceHistory.from_ohlcv_data(
                            symbol=symbol,
                            ohlcv_data=data_point,
                            interval=interval
                        )
                        db.add(price_history)
                        saved_count += 1
                
                db.commit()
                logger.debug(f"💾 Salvos {saved_count} novos registros para {symbol} {interval}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar no cache: {str(e)}")
            return False
    
    async def _cache_symbol_data(self, symbol: str) -> bool:
        """
        Busca e cacheia dados históricos para um símbolo.
        
        Args:
            symbol: Símbolo para cachear
            
        Returns:
            bool: True se cacheou com sucesso
        """
        try:
            logger.info(f"🔍 Cacheando dados históricos para {symbol}...")
            
            success_count = 0
            for interval in self.default_intervals:
                # Busca dados da API
                data = self._fetch_from_api(symbol, interval, self.default_history_days)
                
                if data:
                    # Salva no cache
                    if self._save_to_cache(symbol, interval, data):
                        success_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                else:
                    logger.warning(f"⚠️ Nenhum dado encontrado para {symbol} {interval}")
            
            if success_count > 0:
                logger.info(f"✅ {symbol}: {success_count}/{len(self.default_intervals)} intervalos cacheados")
                return True
            else:
                logger.warning(f"❌ {symbol}: Nenhum intervalo foi cacheado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao cachear {symbol}: {str(e)}")
            return False
    
    def _calculate_expected_points(self, interval: str, days_back: int) -> int:
        """
        Calcula quantos pontos de dados esperamos para um período.
        
        Args:
            interval: Intervalo dos dados
            days_back: Quantos dias
            
        Returns:
            int: Número esperado de pontos
        """
        minutes_per_day = 24 * 60
        total_minutes = days_back * minutes_per_day
        
        # Mapeia intervalos para minutos
        interval_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '8h': 480,
            '12h': 720,
            '1d': 1440,
            '3d': 4320,
            '1w': 10080
        }
        
        minutes = interval_minutes.get(interval, 1440)  # Default para 1d
        return int(total_minutes / minutes)
    
    def _update_cache_stats(self):
        """Atualiza estatísticas do cache."""
        try:
            with sync_session_maker() as db:
                # Conta símbolos únicos
                symbol_count = db.query(func.count(func.distinct(PriceHistory.symbol))).scalar()
                self.cache_stats.cached_symbols = symbol_count or 0
                
                # Calcula cobertura de dados
                oldest_record = db.query(func.min(PriceHistory.timestamp)).scalar()
                if oldest_record:
                    # Ensure both datetimes are timezone-aware for comparison
                    now = datetime.now(timezone.utc)
                    if oldest_record.tzinfo is None:
                        oldest_record = oldest_record.replace(tzinfo=timezone.utc)
                    elif now.tzinfo is None:
                        now = now.replace(tzinfo=timezone.utc)
                    days_diff = (now - oldest_record).days
                    self.cache_stats.data_coverage_days = days_diff
                
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {str(e)}")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do cache com informações detalhadas.
        
        Returns:
            Dict com estatísticas do cache
        """
        hit_rate = (self.cache_stats.cache_hits / max(self.cache_stats.cache_hits + self.cache_stats.cache_misses, 1)) * 100
        coverage_percentage = (self.cache_stats.cached_symbols / max(self.cache_stats.total_symbols, 1)) * 100
        
        return {
            'total_symbols': self.cache_stats.total_symbols,
            'cached_symbols': self.cache_stats.cached_symbols,
            'coverage_percentage': coverage_percentage,
            'data_coverage_days': self.cache_stats.data_coverage_days,
            'cache_hits': self.cache_stats.cache_hits,
            'cache_misses': self.cache_stats.cache_misses,
            'api_requests': self.cache_stats.api_requests,
            'last_update': self.cache_stats.last_update.isoformat() if self.cache_stats.last_update else None,
            'hit_rate': hit_rate,
            'cache_efficiency': 'Excelente' if hit_rate >= 80 else 'Boa' if hit_rate >= 60 else 'Regular' if hit_rate >= 40 else 'Baixa',
            'status': 'Ativo' if coverage_percentage >= 70 else 'Parcial' if coverage_percentage >= 30 else 'Baixo'
        }
    
    async def update_cache_data(self, symbols: Optional[List[str]] = None, force_refresh: bool = False) -> bool:
        """
        Atualiza dados do cache com novos dados da API.
        
        Args:
            symbols: Lista de símbolos para atualizar (usa todos em cache se None)
            force_refresh: Se True, atualiza mesmo dados recentes
            
        Returns:
            bool: True se atualização foi bem-sucedida
        """
        try:
            logger.info("🔄 Iniciando atualização do cache histórico...")
            
            # Define quais símbolos atualizar
            if symbols is None:
                symbols = self._get_cached_symbols()
                if not symbols:
                    logger.warning("Nenhum símbolo encontrado em cache para atualizar")
                    return False
            
            logger.info(f"📊 Atualizando cache para {len(symbols)} símbolos...")
            
            updated_count = 0
            error_count = 0
            
            for symbol in symbols:
                try:
                    # Verifica se precisa atualizar
                    if not force_refresh and self._is_cache_recent(symbol):
                        logger.debug(f"⏭️ {symbol}: cache recente, pulando atualização")
                        continue
                    
                    logger.info(f"🔄 Atualizando {symbol}...")
                    
                    # Atualiza dados para todos os intervalos
                    for interval in self.default_intervals:
                        # Busca apenas dados dos últimos 7 dias para atualização
                        api_data = self._fetch_from_api(symbol, interval, 7)
                        
                        if api_data:
                            # Salva novos dados
                            self._save_to_cache(symbol, interval, api_data)
                        
                        # Rate limiting
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    updated_count += 1
                    logger.debug(f"✅ {symbol} atualizado com sucesso")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Erro ao atualizar {symbol}: {str(e)}")
            
            # Atualiza estatísticas
            self._update_cache_stats()
            
            logger.info(f"✅ Atualização do cache concluída: {updated_count} sucessos, {error_count} erros")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na atualização do cache: {str(e)}")
            return False
    
    def _is_cache_recent(self, symbol: str, hours_threshold: int = 6) -> bool:
        """
        Verifica se o cache de um símbolo é recente.
        
        Args:
            symbol: Símbolo para verificar
            hours_threshold: Horas para considerar recente
            
        Returns:
            bool: True se o cache é recente
        """
        try:
            threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
            
            with sync_session_maker() as db:
                latest_record = db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.interval == '1d'
                    )
                ).order_by(PriceHistory.timestamp.desc()).first()
                
                if latest_record and latest_record.timestamp >= threshold_time:
                    return True
                    
        except Exception as e:
            logger.error(f"Erro ao verificar cache recente para {symbol}: {str(e)}")
        
        return False
    
    async def maintain_cache(self) -> None:
        """
        Função de manutenção automática do cache.
        Deve ser executada periodicamente para manter o cache atualizado.
        """
        try:
            logger.info("🔧 Iniciando manutenção automática do cache...")
            
            # 1. Atualiza dados recentes
            await self.update_cache_data()
            
            # 2. Remove dados muito antigos (mantém últimos 90 dias)
            removed_count = self.cleanup_old_data(days_to_keep=90)
            
            # 3. Verifica integridade dos dados
            integrity_ok = self._check_cache_integrity()
            
            # 4. Relatório de manutenção
            status = self.get_cache_status()
            
            logger.info("📋 Relatório de manutenção do cache:")
            logger.info(f"   📊 Símbolos em cache: {status['cached_symbols']}")
            logger.info(f"   🎯 Taxa de acerto: {status['hit_rate']:.1f}%")
            logger.info(f"   🧹 Registros removidos: {removed_count}")
            logger.info(f"   ✅ Integridade: {'OK' if integrity_ok else 'PROBLEMAS DETECTADOS'}")
            
            self.cache_stats.last_update = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"❌ Erro na manutenção do cache: {str(e)}")
    
    def _check_cache_integrity(self) -> bool:
        """
        Verifica a integridade dos dados em cache.
        
        Returns:
            bool: True se a integridade está OK
        """
        try:
            with sync_session_maker() as db:
                # Verifica se há registros duplicados
                duplicates = db.execute(text("""
                    SELECT symbol, interval, timestamp, COUNT(*)
                    FROM price_history 
                    GROUP BY symbol, interval, timestamp 
                    HAVING COUNT(*) > 1
                """)).fetchall()
                
                if duplicates:
                    logger.warning(f"⚠️ Encontrados {len(duplicates)} registros duplicados no cache")
                    return False
                
                # Verifica se há lacunas significativas nos dados
                symbols = self._get_cached_symbols()
                for symbol in symbols[:5]:  # Verifica apenas os primeiros 5
                    gap_count = self._count_data_gaps(symbol, '1d')
                    if gap_count > 10:
                        logger.warning(f"⚠️ {symbol}: {gap_count} lacunas detectadas nos dados")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Erro na verificação de integridade: {str(e)}")
            return False
    
    def _count_data_gaps(self, symbol: str, interval: str) -> int:
        """
        Conta lacunas nos dados de um símbolo.
        
        Args:
            symbol: Símbolo para verificar
            interval: Intervalo dos dados
            
        Returns:
            int: Número de lacunas encontradas
        """
        try:
            with sync_session_maker() as db:
                # Busca dados dos últimos 30 dias
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                records = db.query(PriceHistory.timestamp).filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.interval == interval,
                        PriceHistory.timestamp >= start_date
                    )
                ).order_by(PriceHistory.timestamp).all()
                
                if len(records) < 2:
                    return 0
                
                gaps = 0
                expected_interval_hours = {
                    '1d': 24, '4h': 4, '1h': 1, '15m': 0.25
                }
                
                interval_hours = expected_interval_hours.get(interval, 24)
                
                for i in range(1, len(records)):
                    time_diff = (records[i][0] - records[i-1][0]).total_seconds() / 3600
                    if time_diff > interval_hours * 2:  # Considera lacuna se for mais que 2x o intervalo
                        gaps += 1
                
                return gaps
                
        except Exception as e:
            logger.error(f"Erro ao contar lacunas para {symbol}: {str(e)}")
            return 0
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        Remove dados antigos do cache.
        
        Args:
            days_to_keep: Quantos dias manter
            
        Returns:
            int: Número de registros removidos
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            with sync_session_maker() as db:
                deleted = db.query(PriceHistory).filter(
                    PriceHistory.timestamp < cutoff_date
                ).delete()
                
                db.commit()
                
                if deleted > 0:
                    logger.info(f"🧹 Removidos {deleted} registros antigos do cache")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Erro ao limpar dados antigos: {str(e)}")
            return 0


# Instância global do cache manager
cache_manager = HistoricalCacheManager()


async def initialize_historical_cache(symbols: Optional[List[str]] = None) -> bool:
    """
    Função conveniente para inicializar o cache histórico.
    
    Args:
        symbols: Lista de símbolos para cachear
        
    Returns:
        bool: True se inicialização foi bem-sucedida
    """
    return await cache_manager.initialize_cache(symbols)


def get_historical_data_cached(
    symbol: str, 
    interval: str = '1d',
    days_back: int = 30,
    force_api: bool = False
) -> Optional[List[Dict[str, Any]]]:
    """
    Função conveniente para obter dados históricos do cache.
    
    Args:
        symbol: Símbolo da moeda
        interval: Intervalo dos dados
        days_back: Quantos dias buscar
        force_api: Se True, força busca na API
        
    Returns:
        Lista de dados históricos ou None
    """
    return cache_manager.get_historical_data(symbol, interval, days_back, force_api)


def get_cache_status() -> Dict[str, Any]:
    """
    Função conveniente para obter status do cache.
    
    Returns:
        Dict com estatísticas do cache
    """
    return cache_manager.get_cache_status()


if __name__ == "__main__":
    # Teste do sistema de cache
    async def test_cache():
        print("🧪 Testando sistema de cache...")
        
        # Inicializa o cache
        success = await initialize_historical_cache(['BTCUSDT', 'ETHUSDT'])
        
        if success:
            print("✅ Cache inicializado com sucesso!")
            
            # Testa busca de dados
            btc_data = get_historical_data_cached('BTCUSDT', '1d', 7)
            if btc_data:
                print(f"📊 Obtidos {len(btc_data)} pontos de dados para BTCUSDT")
            
            # Mostra status
            status = get_cache_status()
            print(f"📈 Status do cache: {status}")
        else:
            print("❌ Falha ao inicializar cache")
    
    # Executa teste
    asyncio.run(test_cache())
