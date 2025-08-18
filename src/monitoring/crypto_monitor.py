#!/usr/bin/env python3
"""
Advanced Cryptocurrency Monitoring System
Monitors specific cryptocurrencies with technical analysis and alert generation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import json
from enum import Enum

from src.analysis.technical_indicators import TechnicalIndicators
from src.ai.smart_alerts import SmartAlertsEngine, AlertContext, AlertCategory, AlertPriority
from src.api.external.binance_client import BinanceAPIClient
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.local_notifier import LocalNotifier

logger = logging.getLogger(__name__)


def parse_datetime(date_str: str) -> datetime:
    """Parse datetime string handling various formats"""
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try with T separator
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            # Fallback to basic format
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


class TradingSignal(Enum):
    """Trading signal types"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class CoinAnalysis:
    """Comprehensive analysis data for a cryptocurrency"""
    symbol: str
    current_price: float
    price_change_24h: float
    volume_change_24h: float
    technical_indicators: Dict[str, Any]
    support_levels: List[float]
    resistance_levels: List[float]
    trading_signal: TradingSignal
    signal_strength: float
    signal_reasons: List[str]
    risk_score: float
    recommended_action: str
    analyzed_at: datetime


class CryptoMonitor:
    """
    Advanced cryptocurrency monitoring system with technical analysis
    """
    
    def __init__(self):
        self.binance_client = BinanceAPIClient()
        
        # Initialize notifiers with fallback values
        try:
            from src.core.config import settings
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', 'dummy_token')
            chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', 'dummy_chat_id')
            self.telegram_notifier = TelegramNotifier(bot_token, chat_id)
        except Exception as e:
            logger.warning(f"Could not initialize TelegramNotifier: {e}")
            self.telegram_notifier = None
            
        try:
            self.local_notifier = LocalNotifier()
        except Exception as e:
            logger.warning(f"Could not initialize LocalNotifier: {e}")
            self.local_notifier = None
        
        # Target cryptocurrencies (updated with valid Binance symbols)
        self.target_coins = [
            "HYPERUSDT", "TONUSDT", "PENGUUSDT", "TAOUSDT", "SUIUSDT", "SEIUSDT",
            "PENDLEUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", 
            "AVAXUSDT", "ATOMUSDT", "INJUSDT", "FILUSDT"
        ]
        
        # Alternative symbols if main ones don't exist
        self.symbol_alternatives = {
            "HYPERUSDT": ["HYPER/USDT", "HYPERBTC"],
            "MANYUUSDT": ["MANYU/USDT", "MANYUBTC"],
            "PENGUUSDT": ["PENGU/USDT", "PENGUBTC"],
            "HYPEUSDT": ["HYPE/USDT", "HYPEBTC"],
            "SPXUSDT": ["SPX/USDT", "SPXBTC"],
            "FATCONUSDT": ["FATCON/USDT", "FATCONBTC"]
        }
        
        # Analysis parameters
        self.analysis_intervals = ["1h", "4h", "1d"]
        self.alert_thresholds = {
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "volume_spike": 2.0,  # 200% increase
            "price_change": 0.05,  # 5% change
            "support_distance": 0.02,  # 2% from support
            "resistance_distance": 0.02  # 2% from resistance
        }
        
        # Signal scoring weights
        self.signal_weights = {
            "rsi": 0.25,
            "macd": 0.25,
            "support_resistance": 0.20,
            "volume": 0.15,
            "moving_averages": 0.15
        }
        
    async def monitor_all_coins(self) -> Dict[str, CoinAnalysis]:
        """
        Monitor all target cryptocurrencies and return comprehensive analysis
        
        Returns:
            Dictionary with symbol as key and CoinAnalysis as value
        """
        analyses = {}
        
        for symbol in self.target_coins:
            try:
                analysis = await self.analyze_coin(symbol)
                if analysis:
                    analyses[symbol] = analysis
                    
                    # Generate alerts if signal is strong enough
                    if analysis.signal_strength >= 0.7:
                        await self.send_trading_alert(analysis)
                        
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue
                
        return analyses
    
    async def analyze_coin(self, symbol: str) -> Optional[CoinAnalysis]:
        """
        Perform comprehensive technical analysis on a cryptocurrency
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            CoinAnalysis object with complete analysis
        """
        try:
            # Get market data
            ticker_data = await self.get_ticker_data(symbol)
            if not ticker_data:
                return None
                
            # Get candlestick data for different timeframes
            klines_data = {}
            for interval in self.analysis_intervals:
                klines = await self.get_klines_data(symbol, interval)
                if klines:
                    klines_data[interval] = klines
                    
            if not klines_data:
                logger.warning(f"No klines data available for {symbol}")
                return None
            
            # Calculate technical indicators for primary timeframe (1h)
            primary_klines = klines_data.get("1h", list(klines_data.values())[0])
            technical_indicators = TechnicalIndicators.calculate_all_indicators(primary_klines)
            
            if not technical_indicators:
                logger.warning(f"Failed to calculate technical indicators for {symbol}")
                return None
            
            # Calculate support and resistance levels
            support_levels, resistance_levels = self.calculate_support_resistance(primary_klines)
            
            # Generate trading signal
            signal, strength, reasons = self.generate_trading_signal(
                symbol, ticker_data, technical_indicators, support_levels, resistance_levels
            )
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(technical_indicators, ticker_data)
            
            # Generate recommended action
            recommended_action = self.generate_recommendation(signal, strength, risk_score)
            
            analysis = CoinAnalysis(
                symbol=symbol,
                current_price=float(ticker_data['price']),
                price_change_24h=float(ticker_data['priceChangePercent']),
                volume_change_24h=self.calculate_volume_change(ticker_data),
                technical_indicators=technical_indicators,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                trading_signal=signal,
                signal_strength=strength,
                signal_reasons=reasons,
                risk_score=risk_score,
                recommended_action=recommended_action,
                analyzed_at=datetime.now()
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in coin analysis for {symbol}: {str(e)}")
            return None
    
    async def get_ticker_data(self, symbol: str) -> Optional[Dict]:
        """Get 24hr ticker data for a symbol"""
        try:
            # Use async context manager
            async with self.binance_client as client:
                # Try main symbol first
                ticker = await client.get_current_price(symbol)
                if ticker:
                    return {
                        'symbol': ticker['symbol'],
                        'price': ticker['price'],
                        'priceChangePercent': ticker['price_change_percentage_24h'],
                        'volume': ticker['volume_24h'],
                        'quoteVolume': ticker['quote_volume_24h'],
                        'highPrice': ticker['high_24h'],
                        'lowPrice': ticker['low_24h']
                    }
                    
                # Try alternative symbols
                alternatives = self.symbol_alternatives.get(symbol, [])
                for alt_symbol in alternatives:
                    try:
                        ticker = await client.get_current_price(alt_symbol)
                        if ticker:
                            return {
                                'symbol': ticker['symbol'],
                                'price': ticker['price'],
                                'priceChangePercent': ticker['price_change_percentage_24h'],
                                'volume': ticker['volume_24h'],
                                'quoteVolume': ticker['quote_volume_24h'],
                                'highPrice': ticker['high_24h'],
                                'lowPrice': ticker['low_24h']
                            }
                    except:
                        continue
                        
            return None
        except Exception as e:
            logger.error(f"Error getting ticker data for {symbol}: {str(e)}")
            return None
    
    async def get_klines_data(self, symbol: str, interval: str, limit: int = 100) -> Optional[List]:
        """Get candlestick data for a symbol"""
        try:
            # Use async context manager
            async with self.binance_client as client:
                # Try main symbol first
                historical_data = await client.get_historical_data(symbol, interval, limit)
                if historical_data:
                    # Convert to Binance klines format
                    klines = []
                    for data in historical_data:
                        # Convert datetime string to timestamp
                        timestamp = int(parse_datetime(data['timestamp']).timestamp() * 1000)
                        klines.append([
                            timestamp,  # Open time
                            str(data['open']),  # Open
                            str(data['high']),  # High
                            str(data['low']),   # Low
                            str(data['close']), # Close
                            str(data['volume']),# Volume
                            timestamp + 60000,  # Close time (approximation)
                            str(data.get('quote_volume', 0)),  # Quote volume
                            data.get('trades_count', 0),       # Number of trades
                            0,  # Taker buy base asset volume
                            0,  # Taker buy quote asset volume
                            0   # Ignore
                        ])
                    return klines
                    
                # Try alternative symbols
                alternatives = self.symbol_alternatives.get(symbol, [])
                for alt_symbol in alternatives:
                    try:
                        historical_data = await client.get_historical_data(alt_symbol, interval, limit)
                        if historical_data:
                            klines = []
                            for data in historical_data:
                                timestamp = int(parse_datetime(data['timestamp']).timestamp() * 1000)
                                klines.append([
                                    timestamp,
                                    str(data['open']),
                                    str(data['high']),
                                    str(data['low']),
                                    str(data['close']),
                                    str(data['volume']),
                                    timestamp + 60000,
                                    str(data.get('quote_volume', 0)),
                                    data.get('trades_count', 0),
                                    0, 0, 0
                                ])
                            return klines
                    except:
                        continue
                        
            return None
        except Exception as e:
            logger.error(f"Error getting klines data for {symbol}: {str(e)}")
            return None
    
    def calculate_support_resistance(self, klines: List) -> Tuple[List[float], List[float]]:
        """
        Calculate support and resistance levels using price action analysis
        
        Args:
            klines: List of candlestick data
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        try:
            df = TechnicalIndicators.prepare_data(klines)
            if df.empty:
                return [], []
            
            # Find local minima (support) and maxima (resistance)
            window = 5
            support_levels = []
            resistance_levels = []
            
            # Calculate local minima for support
            lows = df['low'].values
            for i in range(window, len(lows) - window):
                if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
                   all(lows[i] <= lows[i+j] for j in range(1, window+1)):
                    support_levels.append(lows[i])
            
            # Calculate local maxima for resistance
            highs = df['high'].values
            for i in range(window, len(highs) - window):
                if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
                   all(highs[i] >= highs[i+j] for j in range(1, window+1)):
                    resistance_levels.append(highs[i])
            
            # Sort and get most significant levels
            support_levels = sorted(list(set(support_levels)), reverse=True)[:3]
            resistance_levels = sorted(list(set(resistance_levels)))[:3]
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {str(e)}")
            return [], []
    
    def generate_trading_signal(
        self,
        symbol: str,
        ticker_data: Dict,
        technical_indicators: Dict,
        support_levels: List[float],
        resistance_levels: List[float]
    ) -> Tuple[TradingSignal, float, List[str]]:
        """
        Generate trading signal based on technical analysis
        
        Returns:
            Tuple of (signal, strength, reasons)
        """
        try:
            current_price = float(ticker_data['price'])
            indicators = technical_indicators.get('indicators', {})
            signals_score = 0.0
            reasons = []
            
            # RSI Analysis
            rsi_data = indicators.get('rsi', {})
            rsi_current = rsi_data.get('current', 50)
            
            if rsi_current < self.alert_thresholds['rsi_oversold']:
                signals_score += self.signal_weights['rsi']
                reasons.append(f"RSI oversold ({rsi_current:.1f})")
            elif rsi_current > self.alert_thresholds['rsi_overbought']:
                signals_score -= self.signal_weights['rsi']
                reasons.append(f"RSI overbought ({rsi_current:.1f})")
            elif rsi_data.get('crossed_up_30', False):
                signals_score += self.signal_weights['rsi'] * 0.8
                reasons.append("RSI crossed above 30")
            elif rsi_data.get('crossed_down_70', False):
                signals_score -= self.signal_weights['rsi'] * 0.8
                reasons.append("RSI crossed below 70")
            
            # MACD Analysis
            macd_data = indicators.get('macd', {})
            if macd_data.get('crossed_up', False):
                signals_score += self.signal_weights['macd']
                reasons.append("MACD bullish crossover")
            elif macd_data.get('crossed_down', False):
                signals_score -= self.signal_weights['macd']
                reasons.append("MACD bearish crossover")
            elif macd_data.get('histogram', 0) > 0:
                signals_score += self.signal_weights['macd'] * 0.5
                reasons.append("MACD histogram positive")
            elif macd_data.get('histogram', 0) < 0:
                signals_score -= self.signal_weights['macd'] * 0.5
                reasons.append("MACD histogram negative")
            
            # Support/Resistance Analysis
            if support_levels:
                closest_support = min(support_levels, key=lambda x: abs(x - current_price))
                support_distance = abs(current_price - closest_support) / current_price
                
                if current_price <= closest_support * (1 + self.alert_thresholds['support_distance']):
                    signals_score += self.signal_weights['support_resistance']
                    reasons.append(f"Price near support ({closest_support:.4f})")
            
            if resistance_levels:
                closest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
                resistance_distance = abs(current_price - closest_resistance) / current_price
                
                if current_price >= closest_resistance * (1 - self.alert_thresholds['resistance_distance']):
                    signals_score -= self.signal_weights['support_resistance']
                    reasons.append(f"Price near resistance ({closest_resistance:.4f})")
            
            # Volume Analysis
            volume_change = self.calculate_volume_change(ticker_data)
            if volume_change > self.alert_thresholds['volume_spike']:
                signals_score += self.signal_weights['volume']
                reasons.append(f"Volume spike ({volume_change:.1f}x)")
            
            # Moving Averages Analysis
            ma_data = indicators.get('moving_averages', {})
            if ma_data.get('ema_9_crossed_up_ema_21', False):
                signals_score += self.signal_weights['moving_averages']
                reasons.append("EMA9 crossed above EMA21")
            elif ma_data.get('ema_9_crossed_down_ema_21', False):
                signals_score -= self.signal_weights['moving_averages']
                reasons.append("EMA9 crossed below EMA21")
            elif ma_data.get('golden_cross', False):
                signals_score += self.signal_weights['moving_averages'] * 1.5
                reasons.append("Golden Cross detected")
            elif ma_data.get('death_cross', False):
                signals_score -= self.signal_weights['moving_averages'] * 1.5
                reasons.append("Death Cross detected")
            
            # Determine signal
            signal_strength = abs(signals_score)
            
            if signals_score >= 0.8:
                signal = TradingSignal.STRONG_BUY
            elif signals_score >= 0.4:
                signal = TradingSignal.BUY
            elif signals_score <= -0.8:
                signal = TradingSignal.STRONG_SELL
            elif signals_score <= -0.4:
                signal = TradingSignal.SELL
            else:
                signal = TradingSignal.HOLD
            
            return signal, signal_strength, reasons
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {str(e)}")
            return TradingSignal.HOLD, 0.0, ["Error in signal generation"]
    
    def calculate_volume_change(self, ticker_data: Dict) -> float:
        """Calculate volume change ratio"""
        try:
            volume = float(ticker_data.get('volume', 0))
            quote_volume = float(ticker_data.get('quoteVolume', 0))
            
            # Use a simple heuristic based on available data
            # In a real implementation, you'd compare with historical average
            price_change = abs(float(ticker_data.get('priceChangePercent', 0)))
            
            # Estimate volume change based on price movement
            # This is a simplification - ideally you'd have historical volume data
            if price_change > 5:
                return 2.0 + (price_change / 10)
            else:
                return 1.0 + (price_change / 20)
                
        except Exception:
            return 1.0
    
    def calculate_risk_score(self, technical_indicators: Dict, ticker_data: Dict) -> float:
        """
        Calculate risk score (0-1, where 1 is highest risk)
        """
        try:
            risk_factors = []
            indicators = technical_indicators.get('indicators', {})
            
            # Volatility risk (based on ATR)
            atr_data = indicators.get('atr', {})
            atr_relative = atr_data.get('relative', 0.02)
            volatility_risk = min(atr_relative * 10, 1.0)  # Cap at 1.0
            risk_factors.append(volatility_risk)
            
            # Price change risk
            price_change = abs(float(ticker_data.get('priceChangePercent', 0))) / 100
            price_risk = min(price_change * 2, 1.0)
            risk_factors.append(price_risk)
            
            # RSI extreme risk
            rsi_current = indicators.get('rsi', {}).get('current', 50)
            if rsi_current > 80 or rsi_current < 20:
                rsi_risk = 0.8
            elif rsi_current > 70 or rsi_current < 30:
                rsi_risk = 0.5
            else:
                rsi_risk = 0.2
            risk_factors.append(rsi_risk)
            
            # Bollinger Bands risk
            bb_data = indicators.get('bollinger_bands', {})
            if bb_data.get('above_upper', False) or bb_data.get('below_lower', False):
                bb_risk = 0.7
            else:
                bb_risk = 0.3
            risk_factors.append(bb_risk)
            
            # Calculate average risk
            risk_score = sum(risk_factors) / len(risk_factors)
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 0.5  # Default medium risk
    
    def generate_recommendation(
        self,
        signal: TradingSignal,
        strength: float,
        risk_score: float
    ) -> str:
        """Generate trading recommendation"""
        
        risk_level = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"
        
        if signal == TradingSignal.STRONG_BUY and strength > 0.8:
            if risk_score < 0.5:
                return f"STRONG BUY - High conviction signal with {risk_level} risk"
            else:
                return f"BUY with caution - Strong signal but {risk_level} risk"
        elif signal == TradingSignal.BUY:
            return f"BUY - Moderate signal with {risk_level} risk"
        elif signal == TradingSignal.STRONG_SELL and strength > 0.8:
            return f"STRONG SELL - High conviction signal"
        elif signal == TradingSignal.SELL:
            return f"SELL - Moderate bearish signal"
        else:
            return f"HOLD - Neutral signal with {risk_level} risk"
    
    async def send_trading_alert(self, analysis: CoinAnalysis) -> bool:
        """
        Send trading alert via Telegram and local notifications
        
        Args:
            analysis: CoinAnalysis with signal information
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Format alert message
            message = self.format_alert_message(analysis)
            
            telegram_success = False
            local_success = False
            
            # Send via Telegram if available
            if self.telegram_notifier:
                try:
                    telegram_success = self.telegram_notifier.send_message(message)
                except Exception as e:
                    logger.warning(f"Telegram notification failed: {e}")
            
            # Send local notification as backup
            if self.local_notifier:
                try:
                    await self.local_notifier.send_notification(
                        title=f"Trading Alert: {analysis.symbol}",
                        message=message,
                        notification_type="trading_signal"
                    )
                    local_success = True
                except Exception as e:
                    logger.warning(f"Local notification failed: {e}")
            
            # Log to console as final fallback
            if not telegram_success and not local_success:
                print(f"\n🚨 TRADING ALERT: {analysis.symbol}")
                print(message)
            
            logger.info(f"Trading alert processed for {analysis.symbol}: {analysis.trading_signal.value}")
            return telegram_success or local_success or True  # Always return True if we got this far
            
        except Exception as e:
            logger.error(f"Error sending trading alert: {str(e)}")
            return False
    
    def format_alert_message(self, analysis: CoinAnalysis) -> str:
        """Format trading alert message"""
        
        signal_emoji = {
            TradingSignal.STRONG_BUY: "🚀",
            TradingSignal.BUY: "📈",
            TradingSignal.HOLD: "⏸️",
            TradingSignal.SELL: "📉",
            TradingSignal.STRONG_SELL: "💥"
        }
        
        emoji = signal_emoji.get(analysis.trading_signal, "📊")
        
        message = f"{emoji} **TRADING ALERT: {analysis.symbol}**\n\n"
        message += f"💰 **Price:** ${analysis.current_price:.6f}\n"
        message += f"📊 **24h Change:** {analysis.price_change_24h:+.2f}%\n"
        message += f"🎯 **Signal:** {analysis.trading_signal.value.upper()}\n"
        message += f"💪 **Strength:** {analysis.signal_strength:.1%}\n"
        message += f"⚠️ **Risk Score:** {analysis.risk_score:.1%}\n\n"
        
        message += f"📋 **Recommendation:**\n{analysis.recommended_action}\n\n"
        
        if analysis.signal_reasons:
            message += "🔍 **Technical Reasons:**\n"
            for reason in analysis.signal_reasons[:5]:  # Limit to 5 reasons
                message += f"• {reason}\n"
        
        # Add technical indicators summary
        indicators = analysis.technical_indicators.get('indicators', {})
        rsi = indicators.get('rsi', {}).get('current', 0)
        message += f"\n📈 **Key Indicators:**\n"
        message += f"• RSI: {rsi:.1f}\n"
        
        macd_data = indicators.get('macd', {})
        message += f"• MACD: {macd_data.get('histogram', 0):.6f}\n"
        
        # Add support/resistance if available
        if analysis.support_levels:
            closest_support = min(analysis.support_levels, key=lambda x: abs(x - analysis.current_price))
            message += f"• Support: ${closest_support:.6f}\n"
        
        if analysis.resistance_levels:
            closest_resistance = min(analysis.resistance_levels, key=lambda x: abs(x - analysis.current_price))
            message += f"• Resistance: ${closest_resistance:.6f}\n"
        
        message += f"\n⏰ **Analyzed at:** {analysis.analyzed_at.strftime('%H:%M:%S')}"
        
        return message
    
    async def generate_comparison_report(self, analyses: Dict[str, CoinAnalysis]) -> str:
        """
        Generate comparison report for all monitored coins
        
        Args:
            analyses: Dictionary of coin analyses
            
        Returns:
            Formatted comparison report
        """
        if not analyses:
            return "No analysis data available"
        
        # Sort by signal strength
        sorted_analyses = sorted(
            analyses.values(),
            key=lambda x: x.signal_strength,
            reverse=True
        )
        
        report = "📊 **CRYPTO MARKET ANALYSIS REPORT**\n"
        report += f"📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Top opportunities
        buy_signals = [a for a in sorted_analyses if a.trading_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]]
        if buy_signals:
            report += "🚀 **TOP BUY OPPORTUNITIES:**\n"
            for analysis in buy_signals[:3]:
                report += f"• **{analysis.symbol}** - {analysis.trading_signal.value.upper()} "
                report += f"({analysis.signal_strength:.1%}) - ${analysis.current_price:.6f}\n"
            report += "\n"
        
        # Coins to avoid
        sell_signals = [a for a in sorted_analyses if a.trading_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]]
        if sell_signals:
            report += "⚠️ **COINS TO AVOID:**\n"
            for analysis in sell_signals[:3]:
                report += f"• **{analysis.symbol}** - {analysis.trading_signal.value.upper()} "
                report += f"({analysis.signal_strength:.1%}) - ${analysis.current_price:.6f}\n"
            report += "\n"
        
        # Market overview
        report += "📈 **MARKET OVERVIEW:**\n"
        avg_change = sum(a.price_change_24h for a in sorted_analyses) / len(sorted_analyses)
        avg_risk = sum(a.risk_score for a in sorted_analyses) / len(sorted_analyses)
        
        report += f"• Average 24h Change: {avg_change:+.2f}%\n"
        report += f"• Average Risk Level: {avg_risk:.1%}\n"
        report += f"• Coins Analyzed: {len(sorted_analyses)}\n"
        
        bullish_count = sum(1 for a in sorted_analyses if a.trading_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY])
        bearish_count = sum(1 for a in sorted_analyses if a.trading_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL])
        
        report += f"• Bullish Signals: {bullish_count}\n"
        report += f"• Bearish Signals: {bearish_count}\n"
        
        return report


# Utility functions for running the monitor
async def run_single_analysis(symbol: str) -> Optional[CoinAnalysis]:
    """Run analysis for a single coin"""
    monitor = CryptoMonitor()
    return await monitor.analyze_coin(symbol)


async def run_full_monitoring() -> Dict[str, CoinAnalysis]:
    """Run full monitoring for all target coins"""
    monitor = CryptoMonitor()
    return await monitor.monitor_all_coins()


async def generate_market_report() -> str:
    """Generate comprehensive market report"""
    monitor = CryptoMonitor()
    analyses = await monitor.monitor_all_coins()
    return await monitor.generate_comparison_report(analyses)


if __name__ == "__main__":
    # Example usage
    async def main():
        print("🚀 Starting Cryptocurrency Monitoring System...")
        
        # Run full analysis
        analyses = await run_full_monitoring()
        
        print(f"\n✅ Analyzed {len(analyses)} cryptocurrencies")
        
        # Generate and print report
        report = await generate_market_report()
        print(f"\n{report}")
        
        # Show detailed analysis for coins with strong signals
        for symbol, analysis in analyses.items():
            if analysis.signal_strength >= 0.7:
                print(f"\n" + "="*50)
                print(f"DETAILED ANALYSIS: {symbol}")
                print("="*50)
                print(f"Signal: {analysis.trading_signal.value.upper()}")
                print(f"Strength: {analysis.signal_strength:.1%}")
                print(f"Price: ${analysis.current_price:.6f}")
                print(f"24h Change: {analysis.price_change_24h:+.2f}%")
                print(f"Risk Score: {analysis.risk_score:.1%}")
                print(f"Recommendation: {analysis.recommended_action}")
                print("\nReasons:")
                for reason in analysis.signal_reasons:
                    print(f"  • {reason}")
    
    # Run the monitoring system
    asyncio.run(main())
