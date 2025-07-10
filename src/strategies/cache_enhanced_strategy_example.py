#!/usr/bin/env python3
"""
Exemplo de Estratégia com Cache Histórico Integrado
==================================================

Este exemplo demonstra como usar o sistema de cache histórico
nas estratégias de trading do Robot-Crypt.

O cache garante que:
1. SEMPRE consulta o banco de dados primeiro
2. Só busca na API se não encontrar dados suficientes
3. Salva automaticamente novos dados no banco
4. Análises são MUITO mais rápidas após o primeiro uso

Autor: Robot-Crypt Team
Data: 2024
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

# Importa funcionalidades do cache (interface simplificada)
from src.cache import (
    get_market_data,      # Função principal para obter dados históricos
    get_latest_price,     # Função para obter preço mais recente
    get_price_range,      # Função para análise de faixas de preço
    ensure_cache_ready,   # Garante que cache está inicializado
    is_cache_healthy,     # Verifica saúde do cache
    maintain_cache_health # Manutenção do cache
)

from src.core.logging_setup import logger


class CacheEnhancedTradingStrategy:
    """
    Estratégia de trading que usa o cache histórico de forma otimizada.
    
    BENEFÍCIOS:
    - Análises 10x-100x mais rápidas após cache inicial
    - Redução drástica de chamadas à API da Binance
    - Dados sempre atualizados automaticamente
    - Funciona offline com dados em cache
    """
    
    def __init__(self, config, binance_client):
        """
        Inicializa a estratégia com cache histórico.
        
        Args:
            config: Configuração do bot
            binance_client: Cliente da API Binance
        """
        self.config = config
        self.binance_client = binance_client
        self.name = "Cache Enhanced Strategy"
        
        # Estatísticas de uso do cache
        self.cache_hits = 0
        self.api_calls = 0
        self.analysis_count = 0
        
        logger.info(f"✅ {self.name} inicializada com cache histórico")
    
    async def initialize_strategy(self, symbols: List[str]) -> bool:
        """
        Inicializa a estratégia garantindo que o cache esteja pronto.
        
        Args:
            symbols: Lista de símbolos que a estratégia irá usar
            
        Returns:
            True se inicialização foi bem-sucedida
        """
        try:
            logger.info(f"🚀 Inicializando estratégia para {len(symbols)} símbolos...")
            
            # PASSO 1: Garante que o cache está pronto
            logger.info("📊 Preparando cache histórico...")
            cache_ready = await ensure_cache_ready(symbols)
            
            if cache_ready:
                logger.info("✅ Cache histórico pronto!")
            else:
                logger.warning("⚠️ Cache não pôde ser inicializado - usando API diretamente")
            
            # PASSO 2: Verifica saúde do cache
            if is_cache_healthy():
                logger.info("💪 Cache está saudável e funcionando bem")
            else:
                logger.warning("⚠️ Cache apresenta problemas - executando manutenção...")
                await maintain_cache_health()
            
            logger.info(f"🎯 Estratégia inicializada para símbolos: {', '.join(symbols)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar estratégia: {str(e)}")
            return False
    
    def analyze_market_with_cache(self, symbol: str) -> Dict[str, Any]:
        """
        Analisa o mercado usando dados do cache (SUPER RÁPIDO).
        
        Este método demonstra como usar o cache para análises técnicas.
        
        Args:
            symbol: Símbolo para analisar (ex: 'BTCUSDT')
            
        Returns:
            Dict com análise do mercado
        """
        try:
            self.analysis_count += 1
            logger.info(f"📊 Analisando {symbol} usando cache histórico...")
            
            # BUSCA DADOS DO CACHE (ou API se necessário)
            # Essa linha FAZ TODA A MÁGICA: cache -> API -> salva no cache
            
            # Dados de 30 dias para análise de tendência
            historical_data = get_market_data(
                symbol=symbol,
                interval='1d',
                period=30,  # Últimos 30 dias
                force_refresh=False  # Prioriza cache
            )
            
            if not historical_data:
                logger.warning(f"⚠️ Nenhum dado encontrado para {symbol}")
                return {'error': 'Dados não disponíveis'}
            
            # ANÁLISE TÉCNICA COM DADOS DO CACHE
            analysis = self._perform_technical_analysis(symbol, historical_data)
            
            # OBTÉM PREÇO ATUAL (cache first)
            current_price = get_latest_price(symbol)
            if current_price:
                analysis['current_price'] = current_price
                logger.info(f"💰 Preço atual de {symbol}: ${current_price:.2f}")
            
            # OBTÉM FAIXA DE PREÇOS (análise de suporte/resistência)
            price_range = get_price_range(symbol, days=30)
            if price_range:
                analysis['support_level'] = price_range['min']
                analysis['resistance_level'] = price_range['max']
                analysis['avg_price'] = price_range['avg']
                
                logger.info(f"📈 Faixa de {symbol}: ${price_range['min']:.2f} - ${price_range['max']:.2f}")
            
            # GERA SINAL DE TRADING
            trading_signal = self._generate_trading_signal(analysis)
            analysis['signal'] = trading_signal
            
            logger.info(f"🎯 Análise de {symbol} concluída: {trading_signal['action']}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _perform_technical_analysis(self, symbol: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa análise técnica com os dados históricos.
        
        Args:
            symbol: Símbolo analisado
            data: Dados históricos OHLCV
            
        Returns:
            Dict com indicadores técnicos
        """
        try:
            # Extrai preços de fechamento
            closes = [float(candle['close']) for candle in data]
            highs = [float(candle['high']) for candle in data]
            lows = [float(candle['low']) for candle in data]
            volumes = [float(candle['volume']) for candle in data]
            
            # Calcula indicadores técnicos básicos
            sma_20 = sum(closes[:20]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
            sma_50 = sum(closes[:50]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
            
            # RSI simplificado
            rsi = self._calculate_simple_rsi(closes[:14]) if len(closes) >= 14 else 50
            
            # Volatilidade
            volatility = (max(closes) - min(closes)) / min(closes) * 100
            
            # Tendência
            trend = 'bullish' if closes[0] > sma_20 else 'bearish'
            
            # Volume médio
            avg_volume = sum(volumes) / len(volumes)
            
            return {
                'symbol': symbol,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'rsi': rsi,
                'volatility': volatility,
                'trend': trend,
                'avg_volume': avg_volume,
                'data_points': len(data),
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na análise técnica: {str(e)}")
            return {}
    
    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calcula RSI simplificado.
        
        Args:
            prices: Lista de preços
            period: Período para o RSI
            
        Returns:
            Valor do RSI (0-100)
        """
        try:
            if len(prices) < period:
                return 50  # Valor neutro
            
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return 50  # Valor neutro em caso de erro
    
    def _generate_trading_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera sinal de trading baseado na análise.
        
        Args:
            analysis: Resultado da análise técnica
            
        Returns:
            Dict com sinal de trading
        """
        try:
            signal = {
                'action': 'hold',
                'confidence': 0,
                'reason': '',
                'timestamp': datetime.now().isoformat()
            }
            
            if not analysis or 'current_price' not in analysis:
                signal['reason'] = 'Dados insuficientes'
                return signal
            
            current_price = analysis['current_price']
            sma_20 = analysis.get('sma_20', current_price)
            rsi = analysis.get('rsi', 50)
            support = analysis.get('support_level', current_price * 0.95)
            resistance = analysis.get('resistance_level', current_price * 1.05)
            
            # Lógica de trading simplificada
            confidence = 0
            reasons = []
            
            # Sinal de COMPRA
            if (current_price > sma_20 and rsi < 30 and 
                current_price <= support * 1.02):
                signal['action'] = 'buy'
                confidence += 70
                reasons.append('Preço próximo ao suporte com RSI baixo')
            
            # Sinal de VENDA
            elif (current_price < sma_20 and rsi > 70 and 
                  current_price >= resistance * 0.98):
                signal['action'] = 'sell'
                confidence += 70
                reasons.append('Preço próximo à resistência com RSI alto')
            
            # Sinais adicionais
            if analysis.get('trend') == 'bullish':
                confidence += 15
                reasons.append('Tendência de alta')
            elif analysis.get('trend') == 'bearish':
                confidence -= 15
                reasons.append('Tendência de baixa')
            
            signal['confidence'] = max(0, min(100, confidence))
            signal['reason'] = '; '.join(reasons) if reasons else 'Sem sinais claros'
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar sinal: {str(e)}")
            return {
                'action': 'hold',
                'confidence': 0,
                'reason': f'Erro: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas da estratégia e uso do cache.
        
        Returns:
            Dict com estatísticas detalhadas
        """
        try:
            # Importa status do cache
            from src.cache import get_cache_status
            cache_status = get_cache_status()
            
            return {
                'strategy_name': self.name,
                'analysis_count': self.analysis_count,
                'cache_status': cache_status,
                'performance': {
                    'cache_efficiency': cache_status.get('cache_efficiency', 'N/A'),
                    'hit_rate': cache_status.get('hit_rate', 0),
                    'total_symbols': cache_status.get('cached_symbols', 0)
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {str(e)}")
            return {'error': str(e)}
    
    async def maintain_strategy(self) -> None:
        """
        Executa manutenção da estratégia e do cache.
        Deve ser chamada periodicamente (ex: a cada hora).
        """
        try:
            logger.info("🔧 Executando manutenção da estratégia...")
            
            # Executa manutenção do cache
            await maintain_cache_health()
            
            # Verifica saúde do cache
            if not is_cache_healthy():
                logger.warning("⚠️ Cache não está saudável após manutenção")
            
            # Mostra estatísticas
            stats = self.get_strategy_stats()
            logger.info(f"📊 Análises realizadas: {stats.get('analysis_count', 0)}")
            logger.info(f"📈 Eficiência do cache: {stats.get('performance', {}).get('cache_efficiency', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Erro na manutenção da estratégia: {str(e)}")


# EXEMPLO DE USO DA ESTRATÉGIA
async def exemplo_uso_estrategia():
    """
    Exemplo prático de como usar a estratégia com cache.
    """
    print("🧪 Demonstrando estratégia com cache histórico...")
    
    # Simula configuração e cliente Binance
    class MockConfig:
        pass
    
    class MockBinanceClient:
        pass
    
    config = MockConfig()
    binance_client = MockBinanceClient()
    
    # Cria estratégia
    strategy = CacheEnhancedTradingStrategy(config, binance_client)
    
    # Lista de símbolos para trading
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    # Inicializa estratégia (garante cache pronto)
    success = await strategy.initialize_strategy(symbols)
    
    if success:
        print("✅ Estratégia inicializada com sucesso!")
        
        # Analisa cada símbolo (MUITO RÁPIDO após cache)
        for symbol in symbols:
            print(f"\n📊 Analisando {symbol}...")
            analysis = strategy.analyze_market_with_cache(symbol)
            
            if 'error' not in analysis:
                signal = analysis.get('signal', {})
                print(f"🎯 Sinal: {signal.get('action', 'N/A')} "
                      f"(Confiança: {signal.get('confidence', 0)}%)")
                print(f"💭 Razão: {signal.get('reason', 'N/A')}")
            else:
                print(f"❌ Erro: {analysis['error']}")
        
        # Mostra estatísticas
        print(f"\n📈 Estatísticas da estratégia:")
        stats = strategy.get_strategy_stats()
        print(f"   Análises realizadas: {stats.get('analysis_count', 0)}")
        print(f"   Eficiência do cache: {stats.get('performance', {}).get('cache_efficiency', 'N/A')}")
        
        # Executa manutenção
        await strategy.maintain_strategy()
        
        print("✅ Demonstração concluída!")
    else:
        print("❌ Falha ao inicializar estratégia")


if __name__ == "__main__":
    # Executa exemplo
    import asyncio
    asyncio.run(exemplo_uso_estrategia())
