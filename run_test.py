#!/usr/bin/env python3
"""
Script to run a specific test without dotenv prompts
"""
import unittest
import os
import sys

# Disable dotenv auto-loading by setting the environment variable
os.environ['PYTHON_DOTENV_SKIP'] = '1'

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test class
from tests.test_strategy import TestSwingTradingStrategy

# Run the specific test
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSwingTradingStrategy)
    result = unittest.TextTestRunner().run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
