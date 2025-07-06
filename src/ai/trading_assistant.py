#!/usr/bin/env python3
"""
Intelligent Trading Assistant using LLM
Provides contextual analysis and recommendations for trading
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from .llm_client import get_llm_client

logger = logging.getLogger(__name__)


class TradingAssistant:
    """Assistente de Trading com IA"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.conversation_history = []
        self.logger = logging.getLogger("robot-crypt.trading_assistant")
    
    async def chat_analysis(self, user_question: str, current_portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conversational analysis for trading insights
        
        Args:
            user_question: User's query
            current_portfolio: User's current portfolio details
            
        Returns:
            Dict with AI analysis and suggestions
        """
        try:
            # Fetch market context
            market_context = await self._get_market_context()
            
            # System prompt for OpenAI and Gemini 
            system_prompt = self._construct_system_prompt(market_context, current_portfolio)
            
            # Add to conversation history
            self.conversation_history.append({
                "user": user_question,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send query to LLM
            response = await self.llm_client.analyze_json(
                prompt=user_question,
                system_prompt=system_prompt,
                schema=self._get_response_schema()
            )
            
            # Add assistant response to history
            self.conversation_history[-1]["assistant"] = response
            
            return response
            
        except Exception as e:
            self.logger.error(f"Chat analysis failed: {e}")
            return {
                "error": "Analysis failed",
                "detail": str(e)
            }
    
    async def _get_market_context(self) -> Dict[str, Any]:
        """Simulate fetching current market context"""
        # Placeholder for actual implementation
        return {
            "market_phase": "bullish",
            "volatility": "medium",
            "recent_news": "Positive developments in blockchain regulation across major markets.",
            "technical_indicators": {
                "rsi": 65,
                "macd": "+0.5",
                "bollinger_bands": "tight"
            }
        }
    
    def _construct_system_prompt(self, market_context: Dict[str, Any], portfolio: Dict[str, Any]) -> str:
        """Construct system prompt for LLM"""
        portfolio_value = sum(value.get('usd_value', 0) for value in portfolio.values()) if portfolio else 0.0
        
        # Safely extract market context with defaults
        market_phase = market_context.get('market_phase', 'unknown')
        volatility = market_context.get('volatility', 'unknown')
        recent_news = market_context.get('recent_news', 'No recent news available')
        
        technical_indicators = market_context.get('technical_indicators', {})
        rsi = technical_indicators.get('rsi', 'N/A')
        macd = technical_indicators.get('macd', 'N/A')
        bollinger_bands = technical_indicators.get('bollinger_bands', 'N/A')
        
        return f"""
        You are an intelligent trading assistant for cryptocurrencies.

        Current Market Context:
        Market Phase: {market_phase}
        Volatility: {volatility}
        Technical Indicators: RSI({rsi}),
        MACD({macd}),
        Bollinger Bands: {bollinger_bands}

        Current Portfolio Value: ${portfolio_value:.2f}
        Recent News: {recent_news}

        Provide actionable insights, risk assessments, and recommend strategies or adjustments based on the above context and user inquiry.
        """
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Schema for AI response structure"""
        return {
            "insights": "string",
            "recommendations": "array",
            "risk_assessment": "string",
            "confidence_level": "number",
            "follow_up": "string"
        }
