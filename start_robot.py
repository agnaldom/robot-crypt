#!/usr/bin/env python3
"""
Robot-Crypt startup script with automatic error recovery
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Add src directory to Python path for proper imports
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def run_tests():
    """Run comprehensive tests"""
    logger = setup_logging()
    logger.info("Running comprehensive tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_robot_crypt.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logger.info("✓ All tests passed")
            return True
        else:
            logger.error("✗ Tests failed:")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

def start_robot():
    """Start the trading bot"""
    logger = setup_logging()
    logger.info("Starting Robot-Crypt...")
    
    # Set up environment for subprocess
    env = os.environ.copy()
    src_path = str(project_root / 'src')
    
    # Add src directory to PYTHONPATH for subprocess
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = src_path
    
    try:
        # Run the bot with proper PYTHONPATH
        subprocess.run([sys.executable, "src/trading_bot_main.py"], 
                      env=env, check=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

def main():
    """Main startup function"""
    logger = setup_logging()
    
    print("=== Robot-Crypt Startup ===\n")
    
    # Check if we should run tests first
    if "--skip-tests" not in sys.argv:
        if not run_tests():
            print("\nTests failed. Use --skip-tests to start anyway.")
            return 1
    
    # Setup simulation mode by default
    if "SIMULATION_MODE" not in os.environ:
        logger.info("Setting up simulation mode by default...")
        os.environ["SIMULATION_MODE"] = "true"
        os.environ["USE_TESTNET"] = "false"
    
    # Start the bot
    start_robot()
    return 0

if __name__ == "__main__":
    exit(main())
