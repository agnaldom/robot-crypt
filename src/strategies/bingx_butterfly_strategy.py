"""
BingX Butterfly Strategy for trading perpetual futures using Harmonic Butterfly patterns.
"""
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
import numpy as np

from src.api.bingx.futures_client import BingXFuturesClient, BingXFuturesAPIException
from src.api.bingx.harmonic_patterns import HarmonicPatternDetector
from src.core.logging_setup import logger


class BingXButterflyStrategy:
    """
    Trading strategy for BingX futures using Harmonic Butterfly patterns.
    
    This strategy:
    1. Identifies Butterfly patterns in market data
    2. Enters positions at pattern completion points
    3. Sets stop losses and take profits based on pattern structure
    4. Manages risk with position sizing and leverage control
    """
    
    def __init__(
        self,
        client: BingXFuturesClient,
        max_positions: int = 3,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        leverage: int = 10,
        min_profit_ratio: float = 1.5,  # Minimum risk/reward ratio
        **kwargs
    ):
        """
        Initialize the BingX Butterfly Strategy.
        
        Args:
            client (BingXFuturesClient): BingX futures client
            max_positions (int): Maximum number of open positions
            risk_per_trade (float): Risk percentage per trade (0.02 = 2%)
            leverage (int): Leverage to use (1-125)
            min_profit_ratio (float): Minimum profit/loss ratio
            **kwargs: Additional parameters
        """
        self.client = client
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.leverage = leverage
        self.min_profit_ratio = min_profit_ratio
        
        # Initialize pattern detector
        self.pattern_detector = HarmonicPatternDetector()
        
        # Strategy state
        self.active_positions = {}
        self.last_analysis = {}
        
        # Strategy parameters
        self.timeframe = kwargs.get('timeframe', '15m')
        self.symbols = kwargs.get('symbols', ['BTC-USDT', 'ETH-USDT', 'BNB-USDT'])
        self.stop_loss_ratio = kwargs.get('stop_loss_ratio', 0.02)  # 2% stop loss
        self.take_profit_ratio = kwargs.get('take_profit_ratio', 0.04)  # 4% take profit
        
        logger.info(f"BingX Butterfly Strategy initialized with {len(self.symbols)} symbols")
    
    def analyze_market(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Analyze market data for butterfly patterns.
        
        Args:
            symbol (str): Symbol to analyze
            limit (int): Number of candles to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            # Get klines data
            klines = self.client.get_klines(
                symbol=symbol,
                interval=self.timeframe,
                limit=limit
            )
            
            if not klines:
                logger.warning(f"No klines data for {symbol}")
                return {}
            
            # Convert to float arrays for analysis
            klines_float = [[float(x) for x in kline] for kline in klines]
            
            # Detect butterfly patterns
            patterns = self.pattern_detector.detect_butterfly_pattern(klines_float)
            
            # Get current price and market data
            ticker = self.client.get_ticker_price(symbol)
            current_price = float(ticker['data']['price'])
            
            # Calculate technical indicators
            closes = np.array([float(k[4]) for k in klines])
            
            # Simple moving averages
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else current_price
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else current_price
            
            # Volatility (standard deviation)
            volatility = np.std(closes[-20:]) if len(closes) >= 20 else 0
            
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'patterns': patterns,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volatility': volatility,
                'timestamp': int(time.time() * 1000)
            }
            
            # Store analysis for later use
            self.last_analysis[symbol] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {str(e)}")
            return {}
    
    def should_enter_position(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if we should enter a position based on analysis.
        
        Args:
            analysis (Dict[str, Any]): Market analysis data
            
        Returns:
            Dict[str, Any]: Entry signal with details
        """
        if not analysis or not analysis.get('patterns'):
            return {}
        
        symbol = analysis['symbol']
        current_price = analysis['current_price']
        patterns = analysis['patterns']
        
        # Check if we already have a position for this symbol
        if symbol in self.active_positions:
            return {}
        
        # Check if we're at max positions
        if len(self.active_positions) >= self.max_positions:
            return {}
        
        # Find the most recent pattern
        if patterns:
            latest_pattern = patterns[-1]
            pattern_points = latest_pattern['points']
            
            # Determine entry based on pattern completion
            # D point is the entry point for Butterfly pattern
            d_point = pattern_points[4]  # D point (completion)
            
            # Determine direction based on pattern structure
            # If current price is near D point, consider entry
            price_diff = abs(current_price - d_point) / current_price
            
            if price_diff < 0.005:  # Within 0.5% of D point
                # Determine long/short based on pattern direction
                x_point = pattern_points[0]  # X point (start)
                
                # If D > X, it's a bullish pattern (potential long)
                # If D < X, it's a bearish pattern (potential short)
                if d_point > x_point:
                    side = 'LONG'
                    position_side = 'LONG'
                    entry_price = current_price
                    stop_loss = entry_price * (1 - self.stop_loss_ratio)
                    take_profit = entry_price * (1 + self.take_profit_ratio)
                else:
                    side = 'SHORT'
                    position_side = 'SHORT'
                    entry_price = current_price
                    stop_loss = entry_price * (1 + self.stop_loss_ratio)
                    take_profit = entry_price * (1 - self.take_profit_ratio)
                
                # Calculate position size based on risk
                account_balance = self.get_account_balance()
                if account_balance > 0:
                    risk_amount = account_balance * self.risk_per_trade
                    price_diff_sl = abs(entry_price - stop_loss)
                    position_size = risk_amount / price_diff_sl
                    
                    # Apply leverage
                    position_size *= self.leverage
                    
                    return {
                        'symbol': symbol,
                        'side': side,
                        'position_side': position_side,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'position_size': position_size,
                        'pattern': latest_pattern,
                        'reason': 'Butterfly pattern completion'
                    }
        
        return {}
    
    def enter_position(self, signal: Dict[str, Any]) -> bool:
        """
        Enter a position based on the trading signal.
        
        Args:
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            bool: True if position entered successfully
        """
        try:
            symbol = signal['symbol']
            
            # Set leverage first
            self.client.set_leverage(symbol, self.leverage)
            
            # Create the main order
            order = self.client.create_order(
                symbol=symbol,
                side='BUY' if signal['side'] == 'LONG' else 'SELL',
                position_side=signal['position_side'],
                order_type='MARKET',
                quantity=signal['position_size']
            )
            
            if order and order.get('data'):
                logger.info(f"Entered {signal['side']} position for {symbol}")
                
                # Store position information
                self.active_positions[symbol] = {
                    'order_id': order['data']['orderId'],
                    'entry_price': signal['entry_price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'position_size': signal['position_size'],
                    'side': signal['side'],
                    'position_side': signal['position_side'],
                    'entry_time': int(time.time() * 1000),
                    'pattern': signal['pattern']
                }
                
                # Set stop loss and take profit orders
                self.set_stop_loss_take_profit(symbol, signal)
                
                return True
            
        except BingXFuturesAPIException as e:
            logger.error(f"Error entering position for {signal['symbol']}: {str(e)}")
            
        return False
    
    def set_stop_loss_take_profit(self, symbol: str, signal: Dict[str, Any]):
        """
        Set stop loss and take profit orders.
        
        Args:
            symbol (str): Symbol
            signal (Dict[str, Any]): Trading signal
        """
        try:
            # Stop loss order
            stop_side = 'SELL' if signal['side'] == 'LONG' else 'BUY'
            self.client.create_order(
                symbol=symbol,
                side=stop_side,
                position_side=signal['position_side'],
                order_type='STOP_MARKET',
                quantity=signal['position_size'],
                stopPrice=signal['stop_loss'],
                reduce_only=True
            )
            
            # Take profit order
            self.client.create_order(
                symbol=symbol,
                side=stop_side,
                position_side=signal['position_side'],
                order_type='TAKE_PROFIT_MARKET',
                quantity=signal['position_size'],
                stopPrice=signal['take_profit'],
                reduce_only=True
            )
            
            logger.info(f"Set SL/TP orders for {symbol}")
            
        except Exception as e:
            logger.error(f"Error setting SL/TP for {symbol}: {str(e)}")
    
    def get_account_balance(self) -> float:
        """
        Get account balance in USDT.
        
        Returns:
            float: Account balance
        """
        try:
            account = self.client.get_account()
            if account and account.get('data'):
                balance_data = account['data']['balance']
                if balance_data:
                    return float(balance_data[0]['balance'])
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
        
        return 0.0
    
    def check_positions(self):
        """
        Check and manage existing positions.
        """
        if not self.active_positions:
            return
        
        try:
            # Get current positions from exchange
            positions = self.client.get_positions()
            
            # Update active positions based on exchange data
            for symbol in list(self.active_positions.keys()):
                position_found = False
                for pos in positions:
                    if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                        position_found = True
                        break
                
                # If position not found on exchange, remove from active
                if not position_found:
                    logger.info(f"Position for {symbol} closed")
                    del self.active_positions[symbol]
                    
        except Exception as e:
            logger.error(f"Error checking positions: {str(e)}")
    
    def run_strategy(self):
        """
        Main strategy execution loop.
        """
        logger.info("Starting BingX Butterfly Strategy...")
        
        while True:
            try:
                # Check existing positions
                self.check_positions()
                
                # Analyze each symbol
                for symbol in self.symbols:
                    analysis = self.analyze_market(symbol)
                    
                    if analysis:
                        # Check for entry signals
                        signal = self.should_enter_position(analysis)
                        
                        if signal:
                            logger.info(f"Entry signal for {symbol}: {signal['reason']}")
                            success = self.enter_position(signal)
                            
                            if success:
                                logger.info(f"Successfully entered position for {symbol}")
                            else:
                                logger.warning(f"Failed to enter position for {symbol}")
                
                # Wait before next iteration
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Strategy stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in strategy loop: {str(e)}")
                time.sleep(30)  # Wait before retrying
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """
        Get current strategy status.
        
        Returns:
            Dict[str, Any]: Strategy status
        """
        return {
            'active_positions': len(self.active_positions),
            'max_positions': self.max_positions,
            'symbols': self.symbols,
            'timeframe': self.timeframe,
            'leverage': self.leverage,
            'risk_per_trade': self.risk_per_trade,
            'positions': self.active_positions,
            'last_analysis': self.last_analysis
        }
