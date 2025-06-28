#!/usr/bin/env python3
"""
Manual test of check_volume_increase
"""
import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Point to test environment file instead of .env
os.environ['DOTENV_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.test')

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the SwingTradingStrategy class
from strategy import SwingTradingStrategy

# Create a simple mock config and binance API
class MockConfig:
    def __init__(self):
        self.swing_trading = {
            'min_volume_increase': 0.3,
            'profit_target': 0.08,
            'stop_loss': 0.03,
            'max_hold_time': 48,
            'max_position_size': 0.05,
            'entry_delay': 60
        }
        self.max_trades_per_day = 3
    
    def get_balance(self, account_info):
        return 1000.0

class MockBinance:
    def __init__(self):
        pass

# Setup logging to console
logging.basicConfig(level=logging.INFO)

# Create the strategy instance
config = MockConfig()
binance = MockBinance()
strategy = SwingTradingStrategy(config, binance)

# Mock the get_volume_data method
strategy.get_volume_data = MagicMock(return_value={
    'avg_volume': 100000,
    'current_volume': 140000  # 40% above average
})

# Test check_volume_increase with volume above threshold
result1 = strategy.check_volume_increase("TEST/BRL")
print(f"Test 1 (volume 40% above avg): {result1}")

# Test with volume below threshold
strategy.get_volume_data = MagicMock(return_value={
    'avg_volume': 100000,
    'current_volume': 110000  # 10% above average
})
result2 = strategy.check_volume_increase("TEST/BRL")
print(f"Test 2 (volume 10% above avg): {result2}")

# Test with direct volume_increase value
strategy.get_volume_data = MagicMock(return_value={
    'volume_increase': 0.5  # 50% increase
})
result3 = strategy.check_volume_increase("TEST/BRL")
print(f"Test 3 (direct volume_increase 50%): {result3}")

# All tests should pass if:
# result1 = True (40% > 30% threshold)
# result2 = False (10% < 30% threshold)
# result3 = True (50% > 30% threshold)
print(f"All tests passed: {result1 and not result2 and result3}")
