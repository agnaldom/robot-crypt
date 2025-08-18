"""
🚀 Estratégia Avançada: Breakout + Fluxo de Ordens + Risco Controlado

Esta implementação combina:
- Identificação de breakout com análise de volume
- Confirmação via livro de ordens (order book imbalance)
- Execução com alavancagem isolada 20x
- Gestão de risco com SL/TP dinâmicos
- Controle de risco de 1% por trade
"""

import asyncio
import json
import time
import websockets
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd

from src.api.bingx.futures_client import BingXFuturesClient, BingXFuturesAPIException
from src.core.logging_setup import logger


@dataclass
class BreakoutSignal:
    """Sinal de breakout detectado"""
    symbol: str
    direction: str  # 'LONG' ou 'SHORT'
    price: float
    volume: float
    confidence: float
    timestamp: datetime


@dataclass
class OrderBookImbalance:
    """Desequilíbrio do livro de ordens"""
    symbol: str
    bid_volume: float
    ask_volume: float
    imbalance_ratio: float
    wall_detected: bool
    timestamp: datetime


@dataclass
class RiskParameters:
    """Parâmetros de risco para o trade"""
    risk_per_trade: float = 0.01  # 1% por trade
    leverage: int = 20
    risk_reward_ratio: float = 2.0  # 1:2 mínimo
    max_position_size: float = 0.05  # 5% do capital máximo por posição


class AdvancedBreakoutStrategy:
    """
    Estratégia avançada de breakout com análise de fluxo de ordens
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        risk_params: Optional[RiskParameters] = None
    ):
        self.client = BingXFuturesClient(api_key, api_secret, testnet=testnet)
        self.risk_params = risk_params or RiskParameters()
        
        # Cache para dados em tempo real
        self.current_price: Dict[str, float] = {}
        self.order_book: Dict[str, Dict] = {}
        self.volume_profile: Dict[str, List] = {}
        self.klines_cache: Dict[str, List] = {}
        
        # Posições ativas
        self.active_positions: Dict[str, Dict] = {}
        
        # Configurações de breakout
        self.min_volume_increase = 2.0  # Volume deve ser 2x maior que a média
        self.lookback_periods = 20  # Períodos para análise de suporte/resistência
        self.min_confidence = 0.7  # Confiança mínima para entrada
        
        logger.info("🚀 Estratégia de Breakout Avançada inicializada")
    
    async def start_websocket_streams(self, symbols: List[str]):
        """
        Inicia streams WebSocket para dados em tempo real
        """
        try:
            # Configurar streams para klines, ticker e depth
            tasks = []
            for symbol in symbols:
                tasks.append(self._stream_klines(symbol))
                tasks.append(self._stream_ticker(symbol))
                tasks.append(self._stream_depth(symbol))
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar WebSocket streams: {e}")
    
    async def _stream_klines(self, symbol: str):
        """Stream de klines/candlesticks"""
        # Implementação do WebSocket para klines
        # Nota: BingX WebSocket implementation would go here
        pass
    
    async def _stream_ticker(self, symbol: str):
        """Stream de ticker data"""
        # Implementação do WebSocket para ticker
        pass
    
    async def _stream_depth(self, symbol: str):
        """Stream de order book depth"""
        # Implementação do WebSocket para depth
        pass
    
    def identify_support_resistance(self, symbol: str) -> Tuple[List[float], List[float]]:
        """
        🔓 Identifica níveis de suporte e resistência
        
        Returns:
            Tuple[List[float], List[float]]: (support_levels, resistance_levels)
        """
        try:
            # Obter dados históricos
            klines = self.client.get_klines(
                symbol=symbol,
                interval='1h',
                limit=self.lookback_periods * 2
            )
            
            # Converter para DataFrame para análise
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            df = df.astype({
                'high': float, 'low': float, 'close': float, 'volume': float
            })
            
            # Identificar pivots de alta e baixa
            highs = df['high'].rolling(window=3, center=True).max()
            lows = df['low'].rolling(window=3, center=True).min()
            
            # Níveis de resistência (pivots de alta)
            resistance_levels = []
            for i in range(1, len(df) - 1):
                if df.iloc[i]['high'] == highs.iloc[i]:
                    resistance_levels.append(df.iloc[i]['high'])
            
            # Níveis de suporte (pivots de baixa)
            support_levels = []
            for i in range(1, len(df) - 1):
                if df.iloc[i]['low'] == lows.iloc[i]:
                    support_levels.append(df.iloc[i]['low'])
            
            # Filtrar níveis mais significativos
            resistance_levels = sorted(list(set(resistance_levels)))[-5:]  # Top 5
            support_levels = sorted(list(set(support_levels)))[:5]  # Bottom 5
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"❌ Erro ao identificar S/R para {symbol}: {e}")
            return [], []
    
    def detect_breakout(self, symbol: str) -> Optional[BreakoutSignal]:
        """
        🔓 Detecta breakout com confirmação de volume
        """
        try:
            # Obter dados recentes
            klines = self.client.get_klines(symbol=symbol, interval='1h', limit=50)
            
            if len(klines) < 20:
                return None
            
            # Converter para análise
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            df = df.astype({
                'open': float, 'high': float, 'low': float, 
                'close': float, 'volume': float
            })
            
            # Candle atual e anterior
            current_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]
            
            # Calcular volume médio
            avg_volume = df['volume'].tail(20).mean()
            volume_increase = current_candle['volume'] / avg_volume
            
            # Identificar suporte e resistência
            support_levels, resistance_levels = self.identify_support_resistance(symbol)
            
            # Detectar breakout LONG
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_candle['close']))
                if (current_candle['close'] > nearest_resistance and 
                    current_candle['close'] > prev_candle['high'] and
                    volume_increase >= self.min_volume_increase):
                    
                    confidence = min(0.95, volume_increase / self.min_volume_increase * 0.5)
                    
                    return BreakoutSignal(
                        symbol=symbol,
                        direction='LONG',
                        price=current_candle['close'],
                        volume=current_candle['volume'],
                        confidence=confidence,
                        timestamp=datetime.now()
                    )
            
            # Detectar breakout SHORT
            if support_levels:
                nearest_support = max(support_levels, key=lambda x: abs(x - current_candle['close']))
                if (current_candle['close'] < nearest_support and 
                    current_candle['close'] < prev_candle['low'] and
                    volume_increase >= self.min_volume_increase):
                    
                    confidence = min(0.95, volume_increase / self.min_volume_increase * 0.5)
                    
                    return BreakoutSignal(
                        symbol=symbol,
                        direction='SHORT',
                        price=current_candle['close'],
                        volume=current_candle['volume'],
                        confidence=confidence,
                        timestamp=datetime.now()
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao detectar breakout para {symbol}: {e}")
            return None
    
    def analyze_order_book_imbalance(self, symbol: str) -> Optional[OrderBookImbalance]:
        """
        💡 Analisa desequilíbrio no livro de ordens
        """
        try:
            # Obter depth do livro de ordens
            depth = self.client.get_depth(symbol=symbol, limit=100)
            
            if 'data' not in depth:
                return None
            
            bids = depth['data']['bids']
            asks = depth['data']['asks']
            
            # Calcular volumes totais
            total_bid_volume = sum(float(bid[1]) for bid in bids[:20])  # Top 20
            total_ask_volume = sum(float(ask[1]) for ask in asks[:20])  # Top 20
            
            # Calcular ratio de desequilíbrio
            if total_ask_volume > 0:
                imbalance_ratio = total_bid_volume / total_ask_volume
            else:
                imbalance_ratio = float('inf')
            
            # Detectar walls (grandes volumes)
            wall_detected = False
            for bid in bids[:5]:
                if float(bid[1]) > total_bid_volume * 0.3:  # 30% do volume total
                    wall_detected = True
                    break
            
            for ask in asks[:5]:
                if float(ask[1]) > total_ask_volume * 0.3:
                    wall_detected = True
                    break
            
            return OrderBookImbalance(
                symbol=symbol,
                bid_volume=total_bid_volume,
                ask_volume=total_ask_volume,
                imbalance_ratio=imbalance_ratio,
                wall_detected=wall_detected,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar order book para {symbol}: {e}")
            return None
    
    def confirm_breakout_with_order_flow(
        self, 
        breakout_signal: BreakoutSignal, 
        order_book_imbalance: OrderBookImbalance
    ) -> bool:
        """
        💡 Confirma breakout com análise de fluxo de ordens
        """
        try:
            # Confirmação para LONG
            if breakout_signal.direction == 'LONG':
                # Bid volume deve ser significativamente maior que ask volume
                if (order_book_imbalance.imbalance_ratio > 1.5 and 
                    not order_book_imbalance.wall_detected):
                    return True
            
            # Confirmação para SHORT
            elif breakout_signal.direction == 'SHORT':
                # Ask volume deve ser significativamente maior que bid volume
                if (order_book_imbalance.imbalance_ratio < 0.67 and 
                    not order_book_imbalance.wall_detected):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao confirmar breakout: {e}")
            return False
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """
        🧮 Calcula tamanho da posição baseado no risco
        """
        try:
            # Obter saldo da conta
            account = self.client.get_account()
            available_balance = float(account['data']['balance']['availableMargin'])
            
            # Calcular risco por trade
            risk_amount = available_balance * self.risk_params.risk_per_trade
            
            # Calcular distância do stop loss
            price_diff = abs(entry_price - stop_loss)
            
            # Calcular tamanho da posição
            position_size = risk_amount / price_diff
            
            # Aplicar alavancagem
            position_size *= self.risk_params.leverage
            
            # Limitar tamanho máximo da posição
            max_position = available_balance * self.risk_params.max_position_size
            position_size = min(position_size, max_position)
            
            return round(position_size, 8)
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular tamanho da posição: {e}")
            return 0.0
    
    def calculate_stop_loss_take_profit(
        self, 
        symbol: str, 
        entry_price: float, 
        direction: str
    ) -> Tuple[float, float]:
        """
        🛡️ Calcula Stop Loss e Take Profit
        """
        try:
            # Obter ATR (Average True Range) para volatilidade
            klines = self.client.get_klines(symbol=symbol, interval='1h', limit=20)
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            df = df.astype({'high': float, 'low': float, 'close': float})
            
            # Calcular ATR
            df['tr'] = df[['high', 'low', 'close']].apply(
                lambda x: max(x['high'] - x['low'], 
                             abs(x['high'] - x['close']), 
                             abs(x['low'] - x['close'])), axis=1
            )
            atr = df['tr'].mean()
            
            if direction == 'LONG':
                # Stop loss abaixo do último suporte
                stop_loss = entry_price - (atr * 1.5)
                # Take profit com ratio 1:2
                take_profit = entry_price + (atr * 3.0)
            else:  # SHORT
                # Stop loss acima da última resistência
                stop_loss = entry_price + (atr * 1.5)
                # Take profit com ratio 1:2
                take_profit = entry_price - (atr * 3.0)
            
            return round(stop_loss, 8), round(take_profit, 8)
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular SL/TP: {e}")
            return 0.0, 0.0
    
    async def execute_trade(self, breakout_signal: BreakoutSignal) -> bool:
        """
        🎯 Executa trade com alavancagem isolada
        """
        try:
            symbol = breakout_signal.symbol
            direction = breakout_signal.direction
            entry_price = breakout_signal.price
            
            # Configurar margem isolada
            try:
                # Definir alavancagem
                self.client.set_leverage(
                    symbol=symbol,
                    leverage=self.risk_params.leverage,
                    side='BOTH'
                )
                logger.info(f"📊 Alavancagem {self.risk_params.leverage}x configurada para {symbol}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao configurar alavancagem: {e}")
            
            # Calcular SL e TP
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                symbol, entry_price, direction
            )
            
            # Calcular tamanho da posição
            position_size = self.calculate_position_size(symbol, entry_price, stop_loss)
            
            if position_size <= 0:
                logger.warning(f"⚠️ Tamanho da posição inválido: {position_size}")
                return False
            
            # Executar ordem de mercado
            if direction == 'LONG':
                side = 'BUY'
                position_side = 'LONG'
            else:
                side = 'SELL'
                position_side = 'SHORT'
            
            # Ordem principal
            order_response = self.client.create_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                order_type='MARKET',
                quantity=position_size,
                reduce_only=False
            )
            
            logger.info(f"🚀 Trade executado: {direction} {symbol} - Size: {position_size}")
            
            # Configurar Stop Loss e Take Profit
            await self._set_stop_loss_take_profit(
                symbol, position_side, stop_loss, take_profit, position_size
            )
            
            # Salvar posição ativa
            self.active_positions[symbol] = {
                'direction': direction,
                'entry_price': entry_price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now(),
                'order_id': order_response.get('data', {}).get('orderId')
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar trade: {e}")
            return False
    
    async def _set_stop_loss_take_profit(
        self, 
        symbol: str, 
        position_side: str, 
        stop_loss: float, 
        take_profit: float,
        quantity: float
    ):
        """
        🛡️ Configura Stop Loss e Take Profit
        """
        try:
            # Stop Loss
            stop_side = 'SELL' if position_side == 'LONG' else 'BUY'
            self.client.create_order(
                symbol=symbol,
                side=stop_side,
                position_side=position_side,
                order_type='STOP_MARKET',
                quantity=quantity,
                stop_price=stop_loss,
                reduce_only=True
            )
            
            # Take Profit
            tp_side = 'SELL' if position_side == 'LONG' else 'BUY'
            self.client.create_order(
                symbol=symbol,
                side=tp_side,
                position_side=position_side,
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                stop_price=take_profit,
                reduce_only=True
            )
            
            logger.info(f"🛡️ SL: {stop_loss} | TP: {take_profit} configurados para {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar SL/TP: {e}")
    
    async def monitor_positions(self):
        """
        🛠️ Monitora posições ativas
        """
        while True:
            try:
                for symbol in list(self.active_positions.keys()):
                    await self._monitor_single_position(symbol)
                
                await asyncio.sleep(30)  # Verificar a cada 30 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro ao monitorar posições: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_single_position(self, symbol: str):
        """
        🛠️ Monitora uma posição individual
        """
        try:
            position_data = self.active_positions.get(symbol)
            if not position_data:
                return
            
            # Verificar se posição ainda está ativa
            positions = self.client.get_positions(symbol=symbol)
            
            active_position = None
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    active_position = pos
                    break
            
            if not active_position:
                # Posição foi fechada
                logger.info(f"📊 Posição {symbol} foi fechada")
                del self.active_positions[symbol]
                return
            
            # Verificar funding rate para possíveis ajustes
            current_price = float(active_position['markPrice'])
            entry_price = position_data['entry_price']
            
            # Calcular PnL
            if position_data['direction'] == 'LONG':
                pnl_pct = (current_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - current_price) / entry_price * 100
            
            # Implementar trailing stop se necessário
            if pnl_pct > 10:  # 10% de lucro
                await self._implement_trailing_stop(symbol, position_data, current_price)
            
            logger.info(f"📊 {symbol}: PnL {pnl_pct:.2f}% | Preço: {current_price}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao monitorar posição {symbol}: {e}")
    
    async def _implement_trailing_stop(self, symbol: str, position_data: Dict, current_price: float):
        """
        🛠️ Implementa trailing stop
        """
        try:
            # Ajustar stop loss para breakeven + pequeno lucro
            direction = position_data['direction']
            entry_price = position_data['entry_price']
            
            if direction == 'LONG':
                new_stop = entry_price * 1.02  # 2% acima da entrada
            else:
                new_stop = entry_price * 0.98  # 2% abaixo da entrada
            
            # Atualizar stop loss apenas se for melhor
            current_stop = position_data['stop_loss']
            
            if ((direction == 'LONG' and new_stop > current_stop) or
                (direction == 'SHORT' and new_stop < current_stop)):
                
                # Cancelar stop loss antigo e criar novo
                await self._update_stop_loss(symbol, new_stop, position_data)
                
                logger.info(f"🛡️ Trailing stop atualizado para {symbol}: {new_stop}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao implementar trailing stop: {e}")
    
    async def _update_stop_loss(self, symbol: str, new_stop: float, position_data: Dict):
        """
        🛡️ Atualiza stop loss
        """
        try:
            # Cancelar ordens de stop existentes
            open_orders = self.client.get_open_orders(symbol=symbol)
            for order in open_orders:
                if order['type'] in ['STOP_MARKET', 'STOP']:
                    self.client.cancel_order(symbol=symbol, order_id=order['orderId'])
            
            # Criar novo stop loss
            position_side = 'LONG' if position_data['direction'] == 'LONG' else 'SHORT'
            stop_side = 'SELL' if position_data['direction'] == 'LONG' else 'BUY'
            
            self.client.create_order(
                symbol=symbol,
                side=stop_side,
                position_side=position_side,
                order_type='STOP_MARKET',
                quantity=position_data['position_size'],
                stop_price=new_stop,
                reduce_only=True
            )
            
            # Atualizar cache
            self.active_positions[symbol]['stop_loss'] = new_stop
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar stop loss: {e}")
    
    async def run_strategy(self, symbols: List[str]):
        """
        🚀 Executa a estratégia completa
        """
        logger.info(f"🚀 Iniciando estratégia para símbolos: {symbols}")
        
        # Iniciar monitoramento de posições
        asyncio.create_task(self.monitor_positions())
        
        while True:
            try:
                for symbol in symbols:
                    # Verificar se já tem posição ativa
                    if symbol in self.active_positions:
                        continue
                    
                    # 1. Detectar breakout
                    breakout_signal = self.detect_breakout(symbol)
                    if not breakout_signal:
                        continue
                    
                    # 2. Verificar confiança mínima
                    if breakout_signal.confidence < self.min_confidence:
                        logger.info(f"⚠️ Confiança baixa para {symbol}: {breakout_signal.confidence:.2f}")
                        continue
                    
                    # 3. Analisar order book
                    order_book_imbalance = self.analyze_order_book_imbalance(symbol)
                    if not order_book_imbalance:
                        continue
                    
                    # 4. Confirmar com fluxo de ordens
                    if not self.confirm_breakout_with_order_flow(breakout_signal, order_book_imbalance):
                        logger.info(f"❌ Breakout não confirmado pelo order flow para {symbol}")
                        continue
                    
                    # 5. Executar trade
                    logger.info(f"🎯 Executando trade para {symbol}: {breakout_signal.direction}")
                    success = await self.execute_trade(breakout_signal)
                    
                    if success:
                        logger.info(f"✅ Trade executado com sucesso para {symbol}")
                    else:
                        logger.error(f"❌ Falha ao executar trade para {symbol}")
                    
                    # Aguardar antes de verificar próximo símbolo
                    await asyncio.sleep(5)
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                await asyncio.sleep(60)


# Exemplo de uso
async def main():
    """
    Exemplo de execução da estratégia
    """
    # Configurar credenciais
    API_KEY = "sua_api_key_aqui"
    API_SECRET = "sua_api_secret_aqui"
    
    # Parâmetros de risco personalizados
    risk_params = RiskParameters(
        risk_per_trade=0.01,  # 1% por trade
        leverage=20,          # Alavancagem 20x
        risk_reward_ratio=2.0,  # 1:2
        max_position_size=0.05  # 5% máximo
    )
    
    # Símbolos para trading
    symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT']
    
    # Inicializar estratégia
    strategy = AdvancedBreakoutStrategy(
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=True,  # Usar testnet primeiro
        risk_params=risk_params
    )
    
    # Executar estratégia
    await strategy.run_strategy(symbols)


if __name__ == "__main__":
    asyncio.run(main())
