#!/usr/bin/env python3
"""
Update requirements to use compatible versions
"""
import subprocess
import sys

def update_requirements():
    """Update requirements with compatible versions"""
    
    # Compatible package versions
    packages = [
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0", 
        "fastapi>=0.100.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-mock>=3.10.0"
    ]
    
    print("Updating packages to compatible versions...")
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✓ Updated {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to update {package}: {e}")

if __name__ == "__main__":
    update_requirements()
