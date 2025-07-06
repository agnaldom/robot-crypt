#!/usr/bin/env python3
"""
Environment configuration helper for Robot-Crypt
"""
import os

def setup_simulation_mode():
    """Setup environment for simulation mode"""
    os.environ["SIMULATION_MODE"] = "true"
    os.environ["USE_TESTNET"] = "false"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["WALLET_USER_ID"] = "default_user"
    
    print("✓ Simulation mode configured")
    print("  - SIMULATION_MODE=true")
    print("  - USE_TESTNET=false") 
    print("  - LOG_LEVEL=INFO")
    print("  - WALLET_USER_ID=default_user")

def setup_testnet_mode():
    """Setup environment for testnet mode"""
    os.environ["SIMULATION_MODE"] = "false"
    os.environ["USE_TESTNET"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["WALLET_USER_ID"] = "default_user"
    
    print("✓ Testnet mode configured")
    print("  - SIMULATION_MODE=false")
    print("  - USE_TESTNET=true")
    print("  - LOG_LEVEL=INFO")
    print("  - WALLET_USER_ID=default_user")
    print("  NOTE: You need valid testnet API keys!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python configure_env.py [simulation|testnet]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "simulation":
        setup_simulation_mode()
    elif mode == "testnet":
        setup_testnet_mode()
    else:
        print("Invalid mode. Use 'simulation' or 'testnet'")
        sys.exit(1)
