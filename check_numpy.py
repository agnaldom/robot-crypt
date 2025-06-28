#!/usr/bin/env python3
"""
Check if numpy is installed and working
"""
try:
    import numpy as np
    print(f"Numpy version: {np.__version__}")
    print("Calculating mean:", np.mean([1, 2, 3, 4, 5]))
    print("Numpy is working correctly!")
except ImportError:
    print("Numpy is not installed. Please install it using:")
    print("pip install numpy")
except Exception as e:
    print(f"Error using numpy: {str(e)}")
