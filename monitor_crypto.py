#!/usr/bin/env python3
"""
Cryptocurrency Monitoring Script
Execute technical analysis and generate alerts for specified cryptocurrencies
"""

import asyncio
import sys
import os
import argparse
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.monitoring.crypto_monitor import (
    CryptoMonitor, 
    run_single_analysis, 
    run_full_monitoring, 
    generate_market_report
)


async def monitor_single_coin(symbol: str):
    """Monitor a single cryptocurrency"""
    print(f"🔍 Analyzing {symbol}...")
    
    analysis = await run_single_analysis(symbol)
    
    if not analysis:
        print(f"❌ Unable to analyze {symbol} - symbol may not exist or data unavailable")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 ANALYSIS RESULT: {analysis.symbol}")
    print(f"{'='*60}")
    print(f"💰 Current Price: ${analysis.current_price:.6f}")
    print(f"📈 24h Change: {analysis.price_change_24h:+.2f}%")
    print(f"🎯 Trading Signal: {analysis.trading_signal.value.upper()}")
    print(f"💪 Signal Strength: {analysis.signal_strength:.1%}")
    print(f"⚠️ Risk Score: {analysis.risk_score:.1%}")
    print(f"📋 Recommendation: {analysis.recommended_action}")
    
    if analysis.signal_reasons:
        print(f"\n🔍 Technical Reasons:")
        for reason in analysis.signal_reasons:
            print(f"  • {reason}")
    
    # Technical indicators
    indicators = analysis.technical_indicators.get('indicators', {})
    print(f"\n📈 Key Technical Indicators:")
    
    rsi = indicators.get('rsi', {})
    print(f"  • RSI: {rsi.get('current', 'N/A'):.1f}")
    
    macd = indicators.get('macd', {})
    print(f"  • MACD Histogram: {macd.get('histogram', 'N/A'):.6f}")
    
    if analysis.support_levels:
        closest_support = min(analysis.support_levels, key=lambda x: abs(x - analysis.current_price))
        print(f"  • Nearest Support: ${closest_support:.6f}")
    
    if analysis.resistance_levels:
        closest_resistance = min(analysis.resistance_levels, key=lambda x: abs(x - analysis.current_price))
        print(f"  • Nearest Resistance: ${closest_resistance:.6f}")
    
    print(f"\n⏰ Analysis completed at: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")


async def monitor_all_coins():
    """Monitor all target cryptocurrencies"""
    print("🚀 Starting full cryptocurrency monitoring...")
    
    analyses = await run_full_monitoring()
    
    if not analyses:
        print("❌ No analysis data available")
        return
    
    print(f"\n✅ Successfully analyzed {len(analyses)} cryptocurrencies")
    
    # Generate and display report
    report = await generate_market_report()
    print(f"\n{report}")
    
    # Show detailed results for strong signals
    strong_signals = {symbol: analysis for symbol, analysis in analyses.items() 
                     if analysis.signal_strength >= 0.7}
    
    if strong_signals:
        print(f"\n{'='*80}")
        print("🎯 DETAILED ANALYSIS FOR STRONG SIGNALS")
        print(f"{'='*80}")
        
        for symbol, analysis in strong_signals.items():
            print(f"\n📊 {symbol}:")
            print(f"  Signal: {analysis.trading_signal.value.upper()}")
            print(f"  Strength: {analysis.signal_strength:.1%}")
            print(f"  Price: ${analysis.current_price:.6f}")
            print(f"  24h Change: {analysis.price_change_24h:+.2f}%")
            print(f"  Risk: {analysis.risk_score:.1%}")
            print(f"  Action: {analysis.recommended_action}")
            
            if analysis.signal_reasons:
                print("  Reasons:")
                for reason in analysis.signal_reasons[:3]:  # Show top 3 reasons
                    print(f"    • {reason}")


async def continuous_monitoring(interval_minutes: int = 15):
    """Run continuous monitoring with specified interval"""
    print(f"🔄 Starting continuous monitoring (interval: {interval_minutes} minutes)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"📅 Monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Run monitoring
            analyses = await run_full_monitoring()
            
            if analyses:
                # Check for strong buy/sell signals
                strong_signals = {symbol: analysis for symbol, analysis in analyses.items() 
                                if analysis.signal_strength >= 0.7}
                
                if strong_signals:
                    print(f"🚨 Found {len(strong_signals)} strong signals!")
                    for symbol, analysis in strong_signals.items():
                        print(f"  {symbol}: {analysis.trading_signal.value.upper()} "
                              f"({analysis.signal_strength:.1%})")
                else:
                    print("📊 No strong signals detected in this cycle")
                
                # Show market summary
                avg_change = sum(a.price_change_24h for a in analyses.values()) / len(analyses)
                bullish_count = sum(1 for a in analyses.values() 
                                  if a.trading_signal.value in ['buy', 'strong_buy'])
                bearish_count = sum(1 for a in analyses.values() 
                                  if a.trading_signal.value in ['sell', 'strong_sell'])
                
                print(f"\n📈 Market Summary:")
                print(f"  Average 24h Change: {avg_change:+.2f}%")
                print(f"  Bullish Signals: {bullish_count}")
                print(f"  Bearish Signals: {bearish_count}")
            else:
                print("❌ No data available in this cycle")
            
            # Wait for next cycle
            print(f"\n⏳ Waiting {interval_minutes} minutes for next cycle...")
            await asyncio.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")


async def export_analysis(output_file: str):
    """Export analysis results to JSON file"""
    print(f"📁 Exporting analysis to {output_file}...")
    
    analyses = await run_full_monitoring()
    
    if not analyses:
        print("❌ No analysis data to export")
        return
    
    # Convert to serializable format
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_coins_analyzed": len(analyses),
        "analyses": {}
    }
    
    for symbol, analysis in analyses.items():
        export_data["analyses"][symbol] = {
            "symbol": analysis.symbol,
            "current_price": analysis.current_price,
            "price_change_24h": analysis.price_change_24h,
            "volume_change_24h": analysis.volume_change_24h,
            "trading_signal": analysis.trading_signal.value,
            "signal_strength": analysis.signal_strength,
            "signal_reasons": analysis.signal_reasons,
            "risk_score": analysis.risk_score,
            "recommended_action": analysis.recommended_action,
            "support_levels": analysis.support_levels,
            "resistance_levels": analysis.resistance_levels,
            "analyzed_at": analysis.analyzed_at.isoformat(),
            "technical_indicators": analysis.technical_indicators
        }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"✅ Analysis exported successfully to {output_file}")
    except Exception as e:
        print(f"❌ Error exporting analysis: {str(e)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Cryptocurrency Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_crypto.py --all                    # Monitor all coins
  python monitor_crypto.py --coin BTCUSDT          # Monitor single coin
  python monitor_crypto.py --continuous --interval 30  # Continuous monitoring every 30 min
  python monitor_crypto.py --all --export results.json # Export results to file
  
Target Coins: HYPER, TON, MANYU, PENGU, TAO, HYPE, SUI, SPX, SEI, KAS, FATCON
        """
    )
    
    parser.add_argument(
        '--coin', '-c',
        type=str,
        help='Analyze a specific cryptocurrency (e.g., BTCUSDT, TONUSDT)'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Monitor all target cryptocurrencies'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=15,
        help='Monitoring interval in minutes for continuous mode (default: 15)'
    )
    
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Export results to JSON file'
    )
    
    parser.add_argument(
        '--list-coins',
        action='store_true',
        help='List all target cryptocurrencies'
    )
    
    args = parser.parse_args()
    
    if args.list_coins:
        monitor = CryptoMonitor()
        print("🎯 Target Cryptocurrencies:")
        for coin in monitor.target_coins:
            print(f"  • {coin}")
        return
    
    if not any([args.coin, args.all, args.continuous]):
        parser.print_help()
        return
    
    try:
        if args.continuous:
            asyncio.run(continuous_monitoring(args.interval))
        elif args.coin:
            asyncio.run(monitor_single_coin(args.coin))
        elif args.all:
            if args.export:
                asyncio.run(export_analysis(args.export))
            else:
                asyncio.run(monitor_all_coins())
    
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure you have configured your Binance API credentials and internet connection")


if __name__ == "__main__":
    main()
