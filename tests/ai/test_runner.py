#!/usr/bin/env python3
"""
AI Test Runner - Comprehensive test suite for all AI components
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_ai_tests():
    """Run all AI tests with comprehensive reporting"""
    
    print("🤖 Robot-Crypt AI Test Suite")
    print("=" * 50)
    
    # Test configuration
    test_args = [
        "tests/ai/",
        "-v",                    # Verbose output
        "--tb=short",           # Short traceback format
        "--strict-markers",     # Strict marker checking
        "--strict-config",      # Strict config checking
        "-ra",                  # Show all test results (except passed)
        "--durations=10",       # Show 10 slowest tests
        "--cov=src/ai",         # Coverage for AI modules
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov/ai_coverage",  # HTML coverage report
        "--asyncio-mode=auto",  # Auto-detect asyncio tests
    ]
    
    # Add markers for different test categories
    markers = [
        "unit: Unit tests for individual components",
        "integration: Integration tests for AI workflows", 
        "security: Security tests for AI protection",
        "performance: Performance tests for AI operations",
        "slow: Tests that take longer to run"
    ]
    
    # Create pytest configuration
    pytest_ini_content = f"""
[tool:pytest]
markers =
    {chr(10).join(markers)}
    
testpaths = tests/ai
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --strict-config
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""
    
    # Run the tests
    print(f"📁 Running tests from: {project_root}/tests/ai/")
    print(f"🔧 Test arguments: {' '.join(test_args)}")
    print()
    
    try:
        # Set environment variables for testing
        os.environ.setdefault("TESTING", "1")
        os.environ.setdefault("LOG_LEVEL", "WARNING")  # Reduce log noise during tests
        
        # Run pytest
        exit_code = pytest.main(test_args)
        
        print()
        print("=" * 50)
        
        if exit_code == 0:
            print("✅ All AI tests passed!")
            print()
            print("📊 Coverage report generated at: htmlcov/ai_coverage/index.html")
            print("🔍 To view: open htmlcov/ai_coverage/index.html")
        else:
            print("❌ Some tests failed!")
            print(f"   Exit code: {exit_code}")
        
        print()
        print("📚 Test categories covered:")
        print("   🧠 LLM Client (Multiple providers: OpenAI, Gemini, DeepSeek)")
        print("   📰 News Analyzer (Sentiment analysis with AI)")
        print("   🎯 Strategy Generator (AI-driven trading strategies)")
        print("   🔒 AI Security (Prompt protection & safety)")
        print("   📈 Hybrid Predictor (ML + LLM price prediction)")
        print("   🔗 Integration Tests (End-to-end AI workflows)")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


def run_specific_test_category(category):
    """Run tests for a specific AI component"""
    
    category_map = {
        "llm": "test_llm_client.py",
        "news": "test_news_analyzer.py", 
        "strategy": "test_strategy_generator.py",
        "security": "test_ai_security.py",
        "predictor": "test_hybrid_predictor.py"
    }
    
    if category not in category_map:
        print(f"❌ Unknown category: {category}")
        print(f"   Available categories: {', '.join(category_map.keys())}")
        return 1
    
    test_file = f"tests/ai/{category_map[category]}"
    
    print(f"🎯 Running {category.upper()} tests from: {test_file}")
    print("=" * 50)
    
    test_args = [
        test_file,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ]
    
    return pytest.main(test_args)


def check_ai_dependencies():
    """Check if AI test dependencies are available"""
    
    print("🔍 Checking AI test dependencies...")
    
    required_packages = [
        ("pytest", "pytest"),
        ("pytest-asyncio", "pytest_asyncio"),
        ("pytest-cov", "pytest_cov"),
        ("unittest.mock", "unittest.mock")
    ]
    
    optional_packages = [
        ("openai", "OpenAI API client"),
        ("google.generativeai", "Google Gemini API client"),
        ("tiktoken", "OpenAI tokenizer")
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} (REQUIRED)")
            missing_required.append(package_name)
    
    # Check optional packages  
    for package_name, import_name in optional_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ⚠️  {package_name} (optional)")
            missing_optional.append(package_name)
    
    print()
    
    if missing_required:
        print("❌ Missing required dependencies:")
        for package in missing_required:
            print(f"   pip install {package}")
        return False
    
    if missing_optional:
        print("⚠️  Missing optional dependencies (AI features may be limited):")
        for package in missing_optional:
            print(f"   pip install {package}")
    
    print("✅ Dependencies check complete")
    return True


def generate_test_report():
    """Generate a comprehensive test report"""
    
    print("📊 Generating AI Test Report...")
    print("=" * 50)
    
    # Run tests with XML output for reporting
    test_args = [
        "tests/ai/",
        "--junitxml=test-reports/ai-tests.xml",
        "--cov=src/ai",
        "--cov-report=xml:test-reports/ai-coverage.xml",
        "--cov-report=html:test-reports/ai-coverage-html",
        "--tb=short",
        "-v"
    ]
    
    # Create reports directory
    os.makedirs("test-reports", exist_ok=True)
    
    exit_code = pytest.main(test_args)
    
    print()
    print("📋 Reports generated:")
    print("   📄 JUnit XML: test-reports/ai-tests.xml")
    print("   📊 Coverage XML: test-reports/ai-coverage.xml")
    print("   🌐 Coverage HTML: test-reports/ai-coverage-html/index.html")
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Robot-Crypt AI Test Runner")
    parser.add_argument(
        "action", 
        nargs="?", 
        default="run",
        choices=["run", "check", "report", "llm", "news", "strategy", "security", "predictor"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "check":
        success = check_ai_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.action == "report":
        exit_code = generate_test_report()
        sys.exit(exit_code)
    
    elif args.action in ["llm", "news", "strategy", "security", "predictor"]:
        exit_code = run_specific_test_category(args.action)
        sys.exit(exit_code)
    
    else:  # args.action == "run"
        if not check_ai_dependencies():
            print("\n⚠️  Some dependencies are missing. Tests may fail.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        exit_code = run_ai_tests()
        sys.exit(exit_code)
