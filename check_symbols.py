#!/usr/bin/env python3
"""
Check which symbols are available on Binance
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api.external.binance_client import BinanceAPIClient


async def check_symbols():
    """Check which symbols are available"""
    
    # Symbols to check (original list)
    symbols_to_check = [
        "HYPERUSDT", "TONUSDT", "MANYUUSDT", "PENGUUSDT", "TAOUSDT",
        "HYPEUSDT", "SUIUSDT", "SPXUSDT", "SEIUSDT", "KASUSDT", "FATCONUSDT"
    ]
    
    # Alternative symbol variations
    alternative_symbols = [
        "TAIUSDT",   # TAO might be TAI
        "PENDLEUSDT", # PENGU might be PENDLE
        "SOLUSDT",   # Common crypto
        "ADAUSDT",   # Popular crypto
        "DOTUSDT",   # Popular crypto
        "LINKUSDT",  # Popular crypto
        "AVAXUSDT",  # Popular crypto
        "ATOMUSDT",  # Popular crypto
        "INJUSDT",   # Popular crypto
        "FILUSDT",   # Popular crypto
    ]
    
    all_symbols = symbols_to_check + alternative_symbols
    
    print("🔍 Checking symbol availability on Binance...")
    print("=" * 60)
    
    valid_symbols = []
    invalid_symbols = []
    
    async with BinanceAPIClient() as client:
        for symbol in all_symbols:
            try:
                price_data = await client.get_current_price(symbol)
                if price_data:
                    valid_symbols.append(symbol)
                    print(f"✅ {symbol:<12} - ${price_data['price']:.6f} ({price_data['price_change_percentage_24h']:+.2f}%)")
                else:
                    invalid_symbols.append(symbol)
                    print(f"❌ {symbol:<12} - Not found")
            except Exception as e:
                invalid_symbols.append(symbol)
                print(f"❌ {symbol:<12} - Error: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"Valid symbols: {len(valid_symbols)}")
    print(f"Invalid symbols: {len(invalid_symbols)}")
    
    print(f"\n🎯 RECOMMENDED SYMBOL LIST:")
    print("symbols = [")
    for symbol in valid_symbols:
        print(f'    "{symbol}",')
    print("]")
    
    # Get top volume coins as additional suggestions
    print(f"\n🚀 TOP VOLUME COINS (USDT pairs):")
    try:
        async with BinanceAPIClient() as client:
            top_symbols = await client.get_top_symbols(10)
            if top_symbols:
                for coin in top_symbols:
                    symbol = coin['symbol'].replace('/', '')
                    print(f"💎 {symbol:<12} - ${coin['price']:.6f} ({coin['price_change_percentage_24h']:+.2f}%)")
    except Exception as e:
        print(f"Error getting top symbols: {e}")


if __name__ == "__main__":
    asyncio.run(check_symbols())
