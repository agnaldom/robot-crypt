#!/usr/bin/env python3
"""
Test script to verify the fixes for the robot-crypt errors
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime
from src.notifications.telegram_notifier import TelegramNotifier
from src.ai.news_integrator import NewsIntegrator
from src.ai.news_analyzer import NewsAnalysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_notifier():
    """Test the telegram notifier with None analysis data"""
    print("Testing Telegram Notifier...")
    
    # Create a notifier instance (won't send messages without token)
    notifier = TelegramNotifier(token="dummy_token")
    
    # Test with None analysis data - should not crash
    try:
        result = notifier.notify_analysis_report("ADA/USDT", None)
        print("✓ Telegram notifier handles None analysis data correctly")
    except Exception as e:
        print(f"✗ Telegram notifier failed with None data: {e}")
    
    # Test with empty dict
    try:
        result = notifier.notify_analysis_report("ADA/USDT", {})
        print("✓ Telegram notifier handles empty dict correctly")
    except Exception as e:
        print(f"✗ Telegram notifier failed with empty dict: {e}")
    
    # Test with valid data
    try:
        analysis_data = {
            'signals': [],
            'analysis_duration': 5.2,
            'traditional_analysis': {
                'should_trade': False,
                'action': 'hold',
                'price': 0.35
            },
            'ai_analysis': {
                'signals': [],
                'best_signal': None,
                'total_signals': 0,
                'valid_signals': 0
            },
            'risk_assessment': {
                'overall_risk': 'medium',
                'risk_score': 0.5,
                'recommendations': []
            },
            'market_sentiment': {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.5
            },
            'final_decision': {
                'should_trade': False,
                'action': 'hold',
                'reasoning': 'Test analysis'
            }
        }
        
        result = notifier.notify_analysis_report("ADA/USDT", analysis_data)
        print("✓ Telegram notifier handles valid data correctly")
    except Exception as e:
        print(f"✗ Telegram notifier failed with valid data: {e}")

async def test_news_integrator():
    """Test the news integrator timeout handling"""
    print("\nTesting News Integrator...")
    
    try:
        integrator = NewsIntegrator()
        
        # Test with timeout (should return neutral sentiment)
        result = await integrator.get_symbol_sentiment("ADA")
        print(f"✓ News integrator returns sentiment: {result.get('sentiment_label', 'unknown')}")
        
        # Check if it's a neutral/timeout response
        if result.get('reasoning') and 'timeout' in result.get('reasoning', '').lower():
            print("✓ Timeout handled correctly with neutral fallback")
        else:
            print("✓ Normal sentiment analysis completed")
            
    except Exception as e:
        print(f"✗ News integrator failed: {e}")

def test_news_analysis():
    """Test the news analysis structure"""
    print("\nTesting News Analysis...")
    
    try:
        # Test creating a NewsAnalysis object
        analysis = NewsAnalysis(
            sentiment_score=0.0,
            sentiment_label='neutral',
            confidence=0.5,
            impact_level='low',
            key_events=[],
            price_prediction='neutral',
            reasoning='Test analysis',
            article_count=0,
            timestamp=datetime.now()
        )
        
        print(f"✓ NewsAnalysis created successfully: {analysis.sentiment_label}")
        
    except Exception as e:
        print(f"✗ NewsAnalysis creation failed: {e}")

def main():
    """Run all tests"""
    print("Running Robot-Crypt Error Fix Tests...")
    print("=" * 50)
    
    # Test synchronous components
    test_news_analysis()
    
    # Test asynchronous components
    asyncio.run(test_telegram_notifier())
    asyncio.run(test_news_integrator())
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
