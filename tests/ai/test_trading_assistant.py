"""Test suite for AI trading assistant module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.ai.trading_assistant import TradingAssistant


class TestTradingAssistant:
    """Test cases for TradingAssistant class."""
    
    def setup_method(self):
        """Set up test trading assistant."""
        with patch('src.ai.trading_assistant.get_llm_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            self.assistant = TradingAssistant()
            self.mock_llm_client = mock_client
    
    def create_sample_portfolio(self):
        """Create sample portfolio data for testing."""
        return {
            'BTC': {
                'amount': 0.5,
                'usd_value': 25000.0,
                'avg_price': 50000.0,
                'pnl': 1000.0,
                'pnl_percentage': 4.0
            },
            'ETH': {
                'amount': 10.0,
                'usd_value': 20000.0,
                'avg_price': 2000.0,
                'pnl': -500.0,
                'pnl_percentage': -2.5
            },
            'ADA': {
                'amount': 5000.0,
                'usd_value': 2500.0,
                'avg_price': 0.5,
                'pnl': 250.0,
                'pnl_percentage': 10.0
            }
        }
    
    def test_trading_assistant_initialization(self):
        """Test TradingAssistant initialization."""
        assert self.assistant is not None
        assert hasattr(self.assistant, 'llm_client')
        assert hasattr(self.assistant, 'conversation_history')
        assert hasattr(self.assistant, 'logger')
        assert self.assistant.llm_client is not None
        assert isinstance(self.assistant.conversation_history, list)
        assert len(self.assistant.conversation_history) == 0
    
    @pytest.mark.asyncio
    async def test_chat_analysis_success(self):
        """Test successful chat analysis."""
        user_question = "Should I buy more Bitcoin given the current market conditions?"
        portfolio = self.create_sample_portfolio()
        
        # Mock LLM response
        mock_llm_response = {
            "insights": "Current market conditions show strong bullish momentum for Bitcoin with institutional adoption increasing",
            "recommendations": [
                "Consider dollar-cost averaging into BTC over the next few weeks",
                "Set a stop-loss at $45,000 to protect against significant downside",
                "Monitor the 20-day moving average for trend confirmation"
            ],
            "risk_assessment": "Medium risk - while momentum is positive, volatility remains high",
            "confidence_level": 0.75,
            "follow_up": "Would you like me to analyze specific entry points for your BTC accumulation strategy?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {
                "market_phase": "bullish",
                "volatility": "medium",
                "recent_news": "Positive regulatory developments",
                "technical_indicators": {"rsi": 65, "macd": "+0.5", "bollinger_bands": "tight"}
            }
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert result["insights"] == "Current market conditions show strong bullish momentum for Bitcoin with institutional adoption increasing"
            assert len(result["recommendations"]) == 3
            assert result["risk_assessment"] == "Medium risk - while momentum is positive, volatility remains high"
            assert result["confidence_level"] == 0.75
            assert "entry points" in result["follow_up"]
            
            # Check conversation history
            assert len(self.assistant.conversation_history) == 1
            assert self.assistant.conversation_history[0]["user"] == user_question
            assert self.assistant.conversation_history[0]["assistant"] == mock_llm_response
    
    @pytest.mark.asyncio
    async def test_chat_analysis_error_handling(self):
        """Test chat analysis error handling."""
        user_question = "What should I do with my portfolio?"
        portfolio = self.create_sample_portfolio()
        
        # Mock LLM error
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=Exception("LLM API error"))
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {}
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Analysis failed"
            assert "LLM API error" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_chat_analysis_multiple_questions(self):
        """Test multiple chat analysis questions building conversation history."""
        portfolio = self.create_sample_portfolio()
        
        questions_and_responses = [
            {
                "question": "What's your analysis of my current portfolio?",
                "response": {
                    "insights": "Your portfolio shows good diversification across major cryptocurrencies",
                    "recommendations": ["Consider rebalancing towards BTC", "Take profits on ADA"],
                    "risk_assessment": "Medium risk with good diversification",
                    "confidence_level": 0.8,
                    "follow_up": "Would you like specific rebalancing recommendations?"
                }
            },
            {
                "question": "Yes, please provide rebalancing recommendations",
                "response": {
                    "insights": "Based on current market conditions, increasing BTC allocation would be prudent",
                    "recommendations": ["Sell 50% of ADA position", "Use proceeds to buy more BTC"],
                    "risk_assessment": "Low risk rebalancing strategy",
                    "confidence_level": 0.85,
                    "follow_up": "Should I provide specific timing for these trades?"
                }
            }
        ]
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {"market_phase": "bullish"}
            
            for i, qa in enumerate(questions_and_responses):
                self.mock_llm_client.analyze_json = AsyncMock(return_value=qa["response"])
                
                result = await self.assistant.chat_analysis(qa["question"], portfolio)
                
                assert isinstance(result, dict)
                assert result["insights"] == qa["response"]["insights"]
                assert len(self.assistant.conversation_history) == i + 1
    
    @pytest.mark.asyncio
    async def test_chat_analysis_with_empty_portfolio(self):
        """Test chat analysis with empty portfolio."""
        user_question = "I'm new to crypto trading. Where should I start?"
        portfolio = {}
        
        mock_llm_response = {
            "insights": "As a new trader, it's important to start with education and small positions",
            "recommendations": [
                "Start with Bitcoin and Ethereum",
                "Begin with small amounts you can afford to lose",
                "Learn about dollar-cost averaging"
            ],
            "risk_assessment": "High risk for new traders - education is key",
            "confidence_level": 0.9,
            "follow_up": "Would you like me to explain dollar-cost averaging in detail?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {"market_phase": "neutral"}
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "new trader" in result["insights"]
            assert "education" in result["insights"]
            assert len(result["recommendations"]) == 3
            assert "High risk for new traders" in result["risk_assessment"]
    
    @pytest.mark.asyncio
    async def test_chat_analysis_risk_questions(self):
        """Test chat analysis for risk-related questions."""
        user_question = "How can I reduce the risk in my portfolio?"
        portfolio = self.create_sample_portfolio()
        
        mock_llm_response = {
            "insights": "Your portfolio currently has high concentration risk in volatile assets",
            "recommendations": [
                "Consider adding stablecoins for stability",
                "Implement stop-loss orders on major positions",
                "Diversify across different crypto sectors"
            ],
            "risk_assessment": "Current risk level is high due to concentration in volatile assets",
            "confidence_level": 0.85,
            "follow_up": "Would you like specific recommendations for portfolio allocation percentages?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {"volatility": "high"}
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "concentration risk" in result["insights"]
            assert any("stablecoins" in rec for rec in result["recommendations"])
            assert any("stop-loss" in rec for rec in result["recommendations"])
            assert "high" in result["risk_assessment"]
    
    @pytest.mark.asyncio
    async def test_get_market_context(self):
        """Test market context retrieval."""
        context = await self.assistant._get_market_context()
        
        assert isinstance(context, dict)
        assert "market_phase" in context
        assert "volatility" in context
        assert "recent_news" in context
        assert "technical_indicators" in context
        
        # Check technical indicators structure
        assert isinstance(context["technical_indicators"], dict)
        assert "rsi" in context["technical_indicators"]
        assert "macd" in context["technical_indicators"]
        assert "bollinger_bands" in context["technical_indicators"]
    
    def test_construct_system_prompt(self):
        """Test system prompt construction."""
        market_context = {
            "market_phase": "bullish",
            "volatility": "medium",
            "recent_news": "Positive regulatory developments",
            "technical_indicators": {
                "rsi": 65,
                "macd": "+0.5",
                "bollinger_bands": "tight"
            }
        }
        portfolio = self.create_sample_portfolio()
        
        system_prompt = self.assistant._construct_system_prompt(market_context, portfolio)
        
        assert isinstance(system_prompt, str)
        assert "intelligent trading assistant" in system_prompt
        assert "bullish" in system_prompt
        assert "medium" in system_prompt
        assert "Positive regulatory developments" in system_prompt
        assert "RSI(65)" in system_prompt
        assert "MACD(+0.5)" in system_prompt
        assert "$47500.00" in system_prompt  # Total portfolio value
    
    def test_construct_system_prompt_with_large_portfolio(self):
        """Test system prompt construction with large portfolio."""
        market_context = {
            "market_phase": "bearish",
            "volatility": "high",
            "recent_news": "Market uncertainty",
            "technical_indicators": {"rsi": 30, "macd": "-0.8", "bollinger_bands": "wide"}
        }
        
        # Large portfolio
        portfolio = {
            'BTC': {'amount': 10.0, 'usd_value': 500000.0},
            'ETH': {'amount': 100.0, 'usd_value': 200000.0},
            'ADA': {'amount': 100000.0, 'usd_value': 50000.0}
        }
        
        system_prompt = self.assistant._construct_system_prompt(market_context, portfolio)
        
        assert isinstance(system_prompt, str)
        assert "bearish" in system_prompt
        assert "high" in system_prompt
        assert "$750000.00" in system_prompt  # Total portfolio value
        assert "Market uncertainty" in system_prompt
    
    def test_get_response_schema(self):
        """Test response schema structure."""
        schema = self.assistant._get_response_schema()
        
        assert isinstance(schema, dict)
        assert "insights" in schema
        assert "recommendations" in schema
        assert "risk_assessment" in schema
        assert "confidence_level" in schema
        assert "follow_up" in schema
        
        # Check data types
        assert schema["insights"] == "string"
        assert schema["recommendations"] == "array"
        assert schema["risk_assessment"] == "string"
        assert schema["confidence_level"] == "number"
        assert schema["follow_up"] == "string"
    
    @pytest.mark.asyncio
    async def test_chat_analysis_with_technical_questions(self):
        """Test chat analysis with technical trading questions."""
        user_question = "What do the current technical indicators suggest for Bitcoin?"
        portfolio = self.create_sample_portfolio()
        
        mock_llm_response = {
            "insights": "Bitcoin's RSI at 65 suggests bullish momentum without being overbought yet",
            "recommendations": [
                "Watch for RSI to break above 70 for continued bullish signal",
                "Monitor volume confirmation on price moves",
                "Consider the 50-day MA as dynamic support"
            ],
            "risk_assessment": "Moderate risk - momentum is positive but watch for overbought conditions",
            "confidence_level": 0.8,
            "follow_up": "Would you like me to analyze specific support and resistance levels?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {
                "technical_indicators": {"rsi": 65, "macd": "+0.3", "bollinger_bands": "expanding"}
            }
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "RSI at 65" in result["insights"]
            assert any("RSI to break above 70" in rec for rec in result["recommendations"])
            assert "momentum is positive" in result["risk_assessment"]
    
    @pytest.mark.asyncio
    async def test_chat_analysis_with_timing_questions(self):
        """Test chat analysis with market timing questions."""
        user_question = "Is now a good time to buy or should I wait?"
        portfolio = self.create_sample_portfolio()
        
        mock_llm_response = {
            "insights": "Current market conditions suggest a short-term pullback might offer better entry points",
            "recommendations": [
                "Wait for a 5-10% correction before entering new positions",
                "Set buy orders at key support levels",
                "Consider scaling into positions rather than lump sum buying"
            ],
            "risk_assessment": "Low risk approach - patience may be rewarded with better prices",
            "confidence_level": 0.7,
            "follow_up": "Should I identify specific price levels for your buy orders?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {"market_phase": "consolidation"}
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_llm_response)
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "pullback" in result["insights"]
            assert any("correction" in rec for rec in result["recommendations"])
            assert "patience" in result["risk_assessment"]
    
    @pytest.mark.asyncio
    async def test_chat_analysis_conversation_context(self):
        """Test that conversation history provides context for follow-up questions."""
        portfolio = self.create_sample_portfolio()
        
        # First question
        first_question = "What's your overall assessment of the crypto market?"
        first_response = {
            "insights": "The crypto market is showing signs of institutional adoption with increasing volatility",
            "recommendations": ["Monitor regulatory developments", "Focus on established cryptocurrencies"],
            "risk_assessment": "Medium risk environment",
            "confidence_level": 0.75,
            "follow_up": "Would you like specific coin recommendations?"
        }
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {"market_phase": "bullish"}
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=first_response)
            
            # First analysis
            await self.assistant.chat_analysis(first_question, portfolio)
            
            # Follow-up question
            followup_question = "Yes, please provide specific coin recommendations"
            followup_response = {
                "insights": "Based on our previous discussion about institutional adoption, BTC and ETH remain top choices",
                "recommendations": ["Increase BTC allocation to 60%", "Maintain ETH at 30%", "Limit altcoins to 10%"],
                "risk_assessment": "Conservative approach aligned with institutional trends",
                "confidence_level": 0.8,
                "follow_up": "Should I provide specific rebalancing steps?"
            }
            
            self.mock_llm_client.analyze_json = AsyncMock(return_value=followup_response)
            
            result = await self.assistant.chat_analysis(followup_question, portfolio)
            
            assert len(self.assistant.conversation_history) == 2
            assert "previous discussion" in result["insights"]
            assert any("60%" in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_chat_analysis_with_different_market_phases(self):
        """Test chat analysis behavior in different market phases."""
        user_question = "What strategy should I use in this market?"
        portfolio = self.create_sample_portfolio()
        
        market_phases = ["bullish", "bearish", "neutral", "volatile"]
        
        for phase in market_phases:
            # Reset conversation history for each test
            self.assistant.conversation_history = []
            
            mock_response = {
                "insights": f"In a {phase} market, the strategy should be adjusted accordingly",
                "recommendations": [f"Apply {phase}-specific strategies", "Monitor risk carefully"],
                "risk_assessment": f"Risk level appropriate for {phase} conditions",
                "confidence_level": 0.7,
                "follow_up": f"Need more details about {phase} market strategies?"
            }
            
            with patch.object(self.assistant, '_get_market_context') as mock_market_context:
                mock_market_context.return_value = {"market_phase": phase}
                
                self.mock_llm_client.analyze_json = AsyncMock(return_value=mock_response)
                
                result = await self.assistant.chat_analysis(user_question, portfolio)
                
                assert phase in result["insights"]
                assert any(phase in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_chat_analysis_timeout_handling(self):
        """Test chat analysis with timeout."""
        user_question = "Analyze my portfolio please"
        portfolio = self.create_sample_portfolio()
        
        # Mock timeout
        self.mock_llm_client.analyze_json = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))
        
        with patch.object(self.assistant, '_get_market_context') as mock_market_context:
            mock_market_context.return_value = {}
            
            result = await self.assistant.chat_analysis(user_question, portfolio)
            
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Analysis failed"
            assert "Request timeout" in result["detail"]


if __name__ == '__main__':
    pytest.main([__file__])
