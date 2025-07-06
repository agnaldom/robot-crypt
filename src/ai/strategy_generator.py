#!/usr/bin/env python3
"""
AI-Driven Strategy Generator for Crypto Trading
Creates custom strategies based on market conditions and user preferences
"""

import logging
from typing import Dict, Optional, Any
import asyncio

from .llm_client import get_llm_client

logger = logging.getLogger(__name__)


class AIStrategyGenerator:
    """Gerador de Estratégias usando LLM"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger("robot-crypt.strategy_generator")
    
    async def generate_custom_strategy(self,
                                       market_conditions: Dict[str, Any],
                                       user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a custom trading strategy
        
        Args:
            market_conditions: Current market data and indicators
            user_preferences: User-specific settings and risk tolerance
            
        Returns:
            Dict with tailored strategy parameters
        """
        try:
            # Construct strategy prompt
            strategy_prompt = self._construct_strategy_prompt(market_conditions, user_preferences)
            
            # Get model response
            response = await self.llm_client.analyze_json(
                prompt=strategy_prompt,
                system_prompt=self._get_system_prompt(),
                schema=self._get_expected_schema()
            )
            
            self.logger.info("Generated custom strategy using AI")
            return response
            
        except Exception as e:
            self.logger.error(f"Strategy generation failed: {e}")
            return {
                "error": "Failed to generate strategy",
                "reason": str(e)
            }
    
    def _construct_strategy_prompt(self, market_conditions: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """Prepare the strategy generation prompt"""
        return f"""
        Based on the current market conditions and user preferences, generate a cryptocurrency trading strategy:

        Market Conditions:
        - Volatility: {market_conditions['volatility']}%
        - Trend: {market_conditions['trend']}
        - Volume: {market_conditions['volume']}

        User Preferences:
        - Risk Tolerance: {user_preferences['risk_tolerance']}
        - Available Capital: {user_preferences['capital']}
        - Preferred Timeframe: {user_preferences['timeframe']}

        Strategy Requirements:
        1. Dynamic stop-loss settings
        2. Adaptive take-profit targets
        3. Position sizing rules
        4. Entry and exit signals criteria

        Please ensure all elements of the strategy are quantitatively defined and adaptable to market changes.
        """
    
    def _get_system_prompt(self) -> str:
        """System prompt for generation process"""
        return "You are an AI specializing in virtual asset trading strategies. Generate logical, efficient, and realistic strategies that respect the user's risk preferences."
    
    def _get_expected_schema(self) -> Dict[str, Any]:
        """Expected JSON schema for strategy generation"""
        return {
            "dynamic_stop_loss": "string",
            "adaptive_take_profit": "string",
            "position_sizing": "string",
            "entry_signals": "array",
            "exit_signals": "array"
        }
