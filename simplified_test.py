#!/usr/bin/env python3
"""
Simplified test of the check_volume_increase method
"""
import sys

def check_volume_increase(symbol, threshold=0.30):
    """Verifica se o volume da moeda aumentou acima do threshold (30% por padrão)
    
    Args:
        symbol (str): Par de trading para verificar
        threshold (float): Percentual mínimo de aumento (0.30 = 30%)
    
    Returns:
        bool: True se o volume aumentou mais que o threshold, False caso contrário
    """
    try:
        # Simulating the get_volume_data method for different scenarios
        if symbol == "TEST1":
            volume_data = {
                'avg_volume': 100000,
                'current_volume': 140000  # 40% above average
            }
        elif symbol == "TEST2":
            volume_data = {
                'avg_volume': 100000,
                'current_volume': 110000  # 10% above average
            }
        elif symbol == "TEST3":
            volume_data = {
                'volume_increase': 0.5  # 50% increase
            }
        elif symbol == "TEST4":
            volume_data = None
        else:
            volume_data = {
                'avg_volume': 100000,
                'current_volume': 140000
            }
        
        if not volume_data:
            return False
            
        # If we have pre-calculated volume data, use it
        if 'volume_increase' in volume_data:
            volume_increase = volume_data['volume_increase']
        # If not, calculate from average and current volume
        elif 'avg_volume' in volume_data and 'current_volume' in volume_data:
            avg_volume = volume_data['avg_volume']
            current_volume = volume_data['current_volume']
            volume_increase = (current_volume - avg_volume) / avg_volume
        else:
            print(f"Insufficient volume data for {symbol}")
            return False
            
        result = volume_increase >= threshold
        print(f"{symbol} - Volume increase: {volume_increase:.2%} (threshold: {threshold:.2%})")
        return result
    except Exception as e:
        print(f"Error checking volume increase for {symbol}: {str(e)}")
        return False

# Run tests
print("Test 1 (40% increase):", check_volume_increase("TEST1"))
print("Test 2 (10% increase):", check_volume_increase("TEST2"))
print("Test 3 (direct 50% increase):", check_volume_increase("TEST3"))
print("Test 4 (None data):", check_volume_increase("TEST4"))

# Expected results:
# Test 1: True (40% > 30% threshold)
# Test 2: False (10% < 30% threshold)
# Test 3: True (50% > 30% threshold)
# Test 4: False (No data)
