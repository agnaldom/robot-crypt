# 🤖 Robot-Crypt AI Tests

Comprehensive test suite for all AI components in the Robot-Crypt trading bot.

## 📋 Overview

This directory contains comprehensive tests for the AI-powered features of Robot-Crypt:

- **🧠 LLM Client** - Multi-provider LLM integration (OpenAI, Gemini, DeepSeek)
- **📰 News Analyzer** - AI-powered sentiment analysis for crypto news
- **🎯 Strategy Generator** - AI-driven trading strategy creation
- **🔒 AI Security** - Prompt protection and safety measures
- **📈 Hybrid Predictor** - ML + LLM price prediction system

## 🗂️ Test Structure

```
tests/ai/
├── __init__.py                    # Package initialization
├── test_llm_client.py            # LLM client tests (97 tests)
├── test_news_analyzer.py         # News analyzer tests
├── test_strategy_generator.py    # Strategy generator tests  
├── test_ai_security.py          # AI security tests
├── test_hybrid_predictor.py     # Hybrid predictor tests
├── test_runner.py               # Comprehensive test runner
└── README.md                    # This file
```

## 🚀 Running Tests

### Run All AI Tests
```bash
# Using pytest directly
pytest tests/ai/ -v --tb=short

# Using the custom test runner
python tests/ai/test_runner.py run
```

### Run Specific Test Categories
```bash
# LLM Client tests only
python tests/ai/test_runner.py llm
pytest tests/ai/test_llm_client.py -v

# News Analyzer tests only  
python tests/ai/test_runner.py news
pytest tests/ai/test_news_analyzer.py -v

# Strategy Generator tests only
python tests/ai/test_runner.py strategy
pytest tests/ai/test_strategy_generator.py -v

# AI Security tests only
python tests/ai/test_runner.py security
pytest tests/ai/test_ai_security.py -v

# Hybrid Predictor tests only
python tests/ai/test_runner.py predictor
pytest tests/ai/test_hybrid_predictor.py -v
```

### Generate Coverage Reports
```bash
# Generate comprehensive test report
python tests/ai/test_runner.py report

# Run with coverage
pytest tests/ai/ --cov=src/ai --cov-report=html:htmlcov/ai_coverage
```

### Check Dependencies
```bash
# Check if all required dependencies are installed
python tests/ai/test_runner.py check
```

## 🧪 Test Categories

### LLM Client Tests (`test_llm_client.py`)
- **Provider Support**: OpenAI GPT, Google Gemini, DeepSeek
- **Authentication**: API key validation and client initialization  
- **Chat Completion**: Text generation with system prompts
- **JSON Analysis**: Structured response parsing
- **Error Handling**: Network errors, timeout handling, rate limiting
- **Cost Calculation**: Token usage and cost estimation
- **Health Checks**: Service availability monitoring
- **Provider Selection**: Automatic fallback and priority

### News Analyzer Tests (`test_news_analyzer.py`)
- **Data Structures**: CryptoNewsItem and NewsAnalysis dataclasses
- **Sentiment Analysis**: AI-powered news sentiment scoring
- **Symbol Filtering**: News filtering by cryptocurrency symbol
- **Timeframe Filtering**: Recent news prioritization
- **Error Handling**: LLM failures and fallback responses
- **Input Validation**: Malicious content detection
- **Caching**: Analysis result caching for performance
- **Rate Limiting**: Request throttling

### Strategy Generator Tests (`test_strategy_generator.py`)
- **Strategy Creation**: AI-generated trading strategies
- **Market Conditions**: Adaptation to volatility, trend, volume
- **User Preferences**: Risk tolerance and capital consideration
- **Strategy Components**: Stop-loss, take-profit, position sizing
- **Error Handling**: LLM failures and validation
- **Concurrent Generation**: Multiple strategy generation
- **Context Awareness**: Bull/bear market adaptations

### AI Security Tests (`test_ai_security.py`)
- **Prompt Injection**: Detection and prevention
- **Input Sanitization**: Malicious content filtering
- **Output Validation**: AI response verification
- **Rate Limiting**: Abuse prevention
- **Model Poisoning**: Data source validation
- **Content Filtering**: URL and script removal
- **Trading Manipulation**: Pump/dump scheme detection
- **Confidence Thresholds**: Suspicious confidence flagging

### Hybrid Predictor Tests (`test_hybrid_predictor.py`)
- **Price Prediction**: ML + LLM combination for price movement
- **Technical Analysis**: RSI, MACD, Bollinger Bands integration
- **News Integration**: Sentiment-aware price prediction
- **Multi-timeframe**: 1h, 4h, 1d analysis combination
- **Direction Prediction**: Bullish, bearish, neutral signals
- **Confidence Scoring**: Prediction reliability measurement
- **Strategy Recommendations**: BUY/SELL/HOLD suggestions
- **Historical Context**: Support/resistance level consideration

## 🔧 Dependencies

### Required
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `unittest.mock` - Mocking utilities

### Optional (for full AI functionality)
- `openai` - OpenAI GPT client
- `google.generativeai` - Google Gemini client  
- `tiktoken` - OpenAI tokenizer

Install missing dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
pip install openai google-generativeai tiktoken  # Optional
```

## 🎯 Test Features

### Mocking and Isolation
- **LLM Client Mocking**: No real API calls during tests
- **Database Mocking**: Isolated database operations
- **Time Mocking**: Deterministic timestamp testing
- **Security Guard Mocking**: Controlled security responses

### Async Support
- **Pytest-asyncio**: Native async/await test support
- **Concurrent Testing**: Multiple async operations
- **Timeout Testing**: Long-running operation handling
- **Error Propagation**: Async exception handling

### Data Generation
- **Realistic Test Data**: Crypto news, market data, user preferences
- **Edge Cases**: Extreme market conditions, invalid inputs
- **Error Scenarios**: Network failures, API limits, malformed responses
- **Performance Testing**: Large data sets, concurrent requests

### Security Testing
- **OWASP 2025 AI Risks**: Protection against prompt injection, model poisoning
- **Input Validation**: Malicious prompt detection
- **Output Sanitization**: Response validation and filtering
- **Rate Limiting**: Abuse prevention testing

## 📊 Coverage Goals

Target coverage for each module:
- **LLM Client**: >90%
- **News Analyzer**: >85%
- **Strategy Generator**: >85%
- **AI Security**: >95%
- **Hybrid Predictor**: >80%

Current coverage can be viewed at: `htmlcov/ai_coverage/index.html`

## 🐛 Common Issues

### Import Errors
```bash
# Ensure project root is in Python path
export PYTHONPATH="/path/to/robot-crypt:$PYTHONPATH"
```

### API Key Warnings
```bash
# Set test environment to suppress API warnings
export TESTING=1
export LOG_LEVEL=WARNING
```

### Async Test Failures
```bash
# Install latest pytest-asyncio
pip install --upgrade pytest-asyncio
```

### Missing Dependencies
```bash
# Check and install missing packages
python tests/ai/test_runner.py check
```

## 🚀 Adding New Tests

### Test File Structure
```python
#!/usr/bin/env python3
"""
Tests for [Component] AI functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.ai.[module] import [Component]

class Test[Component]:
    """Test [Component] functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.component = [Component]()
    
    def test_initialization(self):
        """Test component initialization"""
        assert self.component is not None
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async operations"""
        result = await self.component.async_method()
        assert result is not None
```

### Best Practices
1. **Use descriptive test names** that explain what is being tested
2. **Mock external dependencies** (LLM APIs, databases)
3. **Test both success and failure scenarios**
4. **Use realistic test data** that matches production patterns
5. **Test edge cases** and boundary conditions
6. **Include performance tests** for critical operations
7. **Validate security** for all AI inputs and outputs

## 📈 Performance Benchmarks

Expected test execution times:
- **Individual test**: <1s
- **Test file**: <30s
- **Full suite**: <5min
- **With coverage**: <10min

## 🔗 Integration with CI/CD

Tests are designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run AI Tests
  run: |
    pip install pytest pytest-asyncio pytest-cov
    python tests/ai/test_runner.py check
    pytest tests/ai/ --junitxml=ai-test-results.xml --cov=src/ai
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Google Gemini API Documentation](https://ai.google.dev/docs/)
- [OWASP AI Security Guide](https://owasp.org/www-project-ai-security-and-privacy-guide/)

---

🤖 **Robot-Crypt AI Testing Suite** - Ensuring reliable and secure AI-powered trading decisions.
