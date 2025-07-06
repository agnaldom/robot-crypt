#!/usr/bin/env python3
"""
Fix all ConfigDict import issues
"""
import os
import sys
import logging
import re

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fix_configdict_import(file_path):
    """Fix ConfigDict import in a specific file"""
    logger = setup_logging()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file uses ConfigDict but doesn't import it
        if 'ConfigDict' in content and 'from pydantic import' in content:
            # Check if ConfigDict is already in the import
            pydantic_import_pattern = r'from pydantic import ([^, ConfigDict\\n]+)'
            match = re.search(pydantic_import_pattern, content)
            
            if match:
                imports = match.group(1)
                if 'ConfigDict' not in imports:
                    # Add ConfigDict to the import
                    new_imports = imports.strip() + ', ConfigDict'
                    content = re.sub(
                        pydantic_import_pattern,
                        f'from pydantic import ([^, ConfigDictnew_imports}',
                        content
                    )
                    logger.info(f"✓ Added ConfigDict import to {file_path}")
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix all ConfigDict imports"""
    logger = setup_logging()
    
    print("=== Fixing ConfigDict Import Issues ===\n")
    
    # Find all Python files that use ConfigDict
    python_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # Check if file uses ConfigDict
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'ConfigDict' in content and 'from pydantic import' in content:
                            python_files.append(file_path)
                except:
                    continue
    
    fixed_files = 0
    for file_path in python_files:
        if fix_configdict_import(file_path):
            fixed_files += 1
    
    logger.info(f"✓ Fixed ConfigDict imports in {fixed_files} files")
    
    # Also check specific files that are known to have issues
    specific_files = [
        "src/schemas/technical_indicator.py",
        "src/schemas/macro_indicator.py", 
        "src/schemas/bot_performance.py",
        "src/schemas/risk_management.py",
        "src/schemas/trading_session.py",
        "src/schemas/report.py",
        "src/modules/users/schemas/user.py",
        "src/modules/portfolio/schemas/portfolio.py"
    ]
    
    additional_fixes = 0
    for file_path in specific_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            if fix_configdict_import(full_path):
                additional_fixes += 1
    
    logger.info(f"✓ Fixed {additional_fixes} additional specific files")
    
    # Final summary
    print(f"\n🎉 Fixed ConfigDict imports in {fixed_files + additional_fixes} files total!")
    print("\nNext steps:")
    print("1. Test: python test_robot_crypt.py")
    print("2. Start: python start_robot.py")
    
    return 0

if __name__ == "__main__":
    exit(main())
