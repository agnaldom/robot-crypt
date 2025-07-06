#!/usr/bin/env python3
"""
Comprehensive test script for Robot-Crypt
"""
import os
import sys
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test all critical imports"""
    logger = setup_logging()
    logger.info("Testing imports...")
    
    try:
        from src import Config
        logger.info("✓ Config import successful")
    except Exception as e:
        logger.error(f"✗ Config import failed: {e}")
        return False
    
    try:
        from src import BinanceAPI
        logger.info("✓ BinanceAPI import successful")
    except Exception as e:
        logger.error(f"✗ BinanceAPI import failed: {e}")
        return False
    
    try:
        from src import ScalpingStrategy, SwingTradingStrategy
        logger.info("✓ Strategy imports successful")
    except Exception as e:
        logger.error(f"✗ Strategy imports failed: {e}")
        return False
    
    try:
        from src import PostgresManager
        logger.info("✓ PostgresManager import successful")
    except Exception as e:
        logger.error(f"✗ PostgresManager import failed: {e}")
        return False
    
    try:
        from src import WalletManager
        logger.info("✓ WalletManager import successful")
    except Exception as e:
        logger.error(f"✗ WalletManager import failed: {e}")
        return False
    
    try:
        from binance_simulator import BinanceSimulator
        logger.info("✓ BinanceSimulator import successful")
    except Exception as e:
        logger.error(f"✗ BinanceSimulator import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection"""
    logger = setup_logging()
    logger.info("Testing database connection...")
    
    try:
        from src.database.postgres_manager import PostgresManager
        pm = PostgresManager()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_binance_simulator():
    """Test Binance simulator"""
    logger = setup_logging()
    logger.info("Testing Binance simulator...")
    
    try:
        from binance_simulator import BinanceSimulator
        sim = BinanceSimulator()
        
        # Test connection
        if sim.test_connection():
            logger.info("✓ Simulator connection test passed")
        
        # Test account info
        account = sim.get_account_info()
        if account and 'balances' in account:
            logger.info("✓ Simulator account info test passed")
        
        # Test ticker price
        price = sim.get_ticker_price("BTC/USDT")
        if price:
            logger.info(f"✓ Simulator ticker test passed: BTC/USDT = {price.get('price')}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Simulator test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger = setup_logging()
    
    print("=== Robot-Crypt Comprehensive Test ===\n")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test database
    if not test_database():
        all_passed = False
    
    # Test simulator
    if not test_binance_simulator():
        all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Robot-Crypt is ready to run.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
