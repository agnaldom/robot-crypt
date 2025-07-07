"""
AI Smart Alerts Module

This module provides intelligent alert generation and management capabilities
for the robot-crypt trading bot. It integrates with existing notification
infrastructure and uses AI to generate contextual, actionable alerts.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.alert import Alert
from src.models.user import User
from src.models.asset import Asset
from src.schemas.alert import AlertCreate, AlertTrigger
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.local_notifier import LocalNotifier
from .llm_client import LLMClient, get_llm_client
from .pattern_detector import AdvancedPatternDetector
from .news_analyzer import LLMNewsAnalyzer
from src.core.database import get_db
from src.core.config import settings


logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Smart alert categories"""
    MARKET_ANOMALY = "market_anomaly"
    TECHNICAL_PATTERN = "technical_pattern"
    NEWS_SENTIMENT = "news_sentiment"
    RISK_MANAGEMENT = "risk_management"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    MACRO_ECONOMIC = "macro_economic"
    CORRELATION_BREAK = "correlation_break"
    VOLATILITY_SPIKE = "volatility_spike"


@dataclass
class AlertContext:
    """Context information for generating smart alerts"""
    asset_symbol: str
    current_price: float
    price_change_24h: float
    volume_change_24h: float
    technical_indicators: Dict[str, Any]
    market_sentiment: Optional[str] = None
    news_events: List[Dict[str, Any]] = None
    portfolio_impact: Optional[Dict[str, Any]] = None
    correlation_data: Optional[Dict[str, Any]] = None


@dataclass
class SmartAlert:
    """Smart alert data structure"""
    category: AlertCategory
    priority: AlertPriority
    title: str
    message: str
    action_items: List[str]
    confidence_score: float
    asset_symbol: str
    trigger_value: Optional[float] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class SmartAlertsEngine:
    """
    AI-powered smart alerts engine that generates contextual,
    actionable alerts based on market conditions and patterns.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        pattern_detector: AdvancedPatternDetector,
        news_analyzer: LLMNewsAnalyzer,
        telegram_notifier: TelegramNotifier,
        local_notifier: LocalNotifier
    ):
        self.llm_client = llm_client
        self.pattern_detector = pattern_detector
        self.news_analyzer = news_analyzer
        self.telegram_notifier = telegram_notifier
        self.local_notifier = local_notifier
        
        # Alert generation parameters
        self.min_confidence_threshold = 0.7
        self.max_alerts_per_hour = 10
        self.recent_alerts_cache = {}
        
    async def generate_smart_alerts(
        self,
        context: AlertContext,
        user_id: int,
        db: Session
    ) -> List[SmartAlert]:
        """
        Generate smart alerts based on current market context
        
        Args:
            context: Market and asset context
            user_id: User ID for personalized alerts
            db: Database session
            
        Returns:
            List of generated smart alerts
        """
        try:
            alerts = []
            
            # 1. Technical pattern alerts
            pattern_alerts = await self._generate_pattern_alerts(context)
            alerts.extend(pattern_alerts)
            
            # 2. News sentiment alerts
            news_alerts = await self._generate_news_alerts(context)
            alerts.extend(news_alerts)
            
            # 3. Risk management alerts
            risk_alerts = await self._generate_risk_alerts(context, user_id, db)
            alerts.extend(risk_alerts)
            
            # 4. Market anomaly alerts
            anomaly_alerts = await self._generate_anomaly_alerts(context)
            alerts.extend(anomaly_alerts)
            
            # 5. Portfolio optimization alerts
            portfolio_alerts = await self._generate_portfolio_alerts(context, user_id, db)
            alerts.extend(portfolio_alerts)
            
            # Filter and rank alerts
            filtered_alerts = self._filter_and_rank_alerts(alerts, user_id)
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Error generating smart alerts: {str(e)}")
            return []
    
    async def _generate_pattern_alerts(self, context: AlertContext) -> List[SmartAlert]:
        """Generate alerts based on technical patterns"""
        alerts = []
        
        try:
            # Convert technical indicators to price/volume data format for pattern detector
            # This is a simplified conversion - in practice you'd need real OHLCV data
            price_data = [{
                'timestamp': datetime.now().isoformat(),
                'open': context.current_price * 0.995,
                'high': context.current_price * 1.005,
                'low': context.current_price * 0.99,
                'close': context.current_price,
                'volume': context.technical_indicators.get('volume', 1000000)
            }]
            volume_data = [{
                'timestamp': datetime.now().isoformat(),
                'volume': context.technical_indicators.get('volume', 1000000)
            }]
            
            # Use pattern detector to identify patterns
            patterns = await self.pattern_detector.detect_complex_patterns(
                price_data,
                volume_data
            )
            
            for pattern in patterns:
                pattern_confidence = pattern.get('confidence', 0) / 100.0  # Convert percentage to decimal
                if pattern_confidence > self.min_confidence_threshold:
                    alert = SmartAlert(
                        category=AlertCategory.TECHNICAL_PATTERN,
                        priority=self._determine_priority(pattern_confidence, 0.8),  # Default strength
                        title=f"Technical Pattern Detected: {pattern.get('name', 'Unknown')}",
                        message=await self._generate_pattern_message(pattern, context),
                        action_items=self._generate_pattern_actions(pattern),
                        confidence_score=pattern_confidence,
                        asset_symbol=context.asset_symbol,
                        trigger_value=context.current_price,
                        metadata={"pattern": pattern}
                    )
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error generating pattern alerts: {str(e)}")
            
        return alerts
    
    async def _generate_news_alerts(self, context: AlertContext) -> List[SmartAlert]:
        """Generate alerts based on news sentiment"""
        alerts = []
        
        try:
            if not context.news_events:
                return alerts
                
            # Convert news events to CryptoNewsItem format
            from .news_analyzer import CryptoNewsItem
            news_items = []
            for event in context.news_events:
                news_item = CryptoNewsItem(
                    title=event.get('title', 'News Event'),
                    content=event.get('content', event.get('description', '')),
                    source=event.get('source', 'Unknown'),
                    published_at=datetime.now(),
                    symbols_mentioned=[context.asset_symbol]
                )
                news_items.append(news_item)
            
            # Analyze news sentiment
            sentiment_analysis = await self.news_analyzer.analyze_crypto_news(
                news_items,
                context.asset_symbol
            )
            
            if sentiment_analysis.confidence > self.min_confidence_threshold:
                alert = SmartAlert(
                    category=AlertCategory.NEWS_SENTIMENT,
                    priority=self._determine_news_priority(sentiment_analysis),
                    title=f"News Sentiment Alert: {sentiment_analysis.sentiment_label}",
                    message=await self._generate_news_message(sentiment_analysis, context),
                    action_items=self._generate_news_actions(sentiment_analysis),
                    confidence_score=sentiment_analysis.confidence,
                    asset_symbol=context.asset_symbol,
                    metadata={"sentiment": asdict(sentiment_analysis)}
                )
                alerts.append(alert)
                
        except Exception as e:
            logger.error(f"Error generating news alerts: {str(e)}")
            
        return alerts
    
    async def _generate_risk_alerts(
        self,
        context: AlertContext,
        user_id: int,
        db: Session
    ) -> List[SmartAlert]:
        """Generate risk management alerts"""
        alerts = []
        
        try:
            # Check for various risk scenarios
            risk_scenarios = await self._analyze_risk_scenarios(context, user_id, db)
            
            for scenario in risk_scenarios:
                if scenario["severity"] >= 0.7:
                    alert = SmartAlert(
                        category=AlertCategory.RISK_MANAGEMENT,
                        priority=self._determine_risk_priority(scenario["severity"]),
                        title=f"Risk Alert: {scenario['type']}",
                        message=await self._generate_risk_message(scenario, context),
                        action_items=self._generate_risk_actions(scenario),
                        confidence_score=scenario["confidence"],
                        asset_symbol=context.asset_symbol,
                        metadata={"risk_scenario": scenario}
                    )
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error generating risk alerts: {str(e)}")
            
        return alerts
    
    async def _generate_anomaly_alerts(self, context: AlertContext) -> List[SmartAlert]:
        """Generate market anomaly alerts"""
        alerts = []
        
        try:
            # Detect various anomalies
            anomalies = await self._detect_market_anomalies(context)
            
            for anomaly in anomalies:
                if anomaly["significance"] > 0.8:
                    alert = SmartAlert(
                        category=AlertCategory.MARKET_ANOMALY,
                        priority=self._determine_anomaly_priority(anomaly),
                        title=f"Market Anomaly: {anomaly['type']}",
                        message=await self._generate_anomaly_message(anomaly, context),
                        action_items=self._generate_anomaly_actions(anomaly),
                        confidence_score=anomaly["confidence"],
                        asset_symbol=context.asset_symbol,
                        metadata={"anomaly": anomaly}
                    )
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error generating anomaly alerts: {str(e)}")
            
        return alerts
    
    async def _generate_portfolio_alerts(
        self,
        context: AlertContext,
        user_id: int,
        db: Session
    ) -> List[SmartAlert]:
        """Generate portfolio optimization alerts"""
        alerts = []
        
        try:
            if not context.portfolio_impact:
                return alerts
                
            # Analyze portfolio optimization opportunities
            opportunities = await self._analyze_portfolio_opportunities(
                context, user_id, db
            )
            
            for opportunity in opportunities:
                if opportunity["potential_impact"] > 0.1:  # 10% potential impact
                    alert = SmartAlert(
                        category=AlertCategory.PORTFOLIO_OPTIMIZATION,
                        priority=self._determine_portfolio_priority(opportunity),
                        title=f"Portfolio Optimization: {opportunity['type']}",
                        message=await self._generate_portfolio_message(opportunity, context),
                        action_items=self._generate_portfolio_actions(opportunity),
                        confidence_score=opportunity["confidence"],
                        asset_symbol=context.asset_symbol,
                        metadata={"opportunity": opportunity}
                    )
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error generating portfolio alerts: {str(e)}")
            
        return alerts
    
    async def _generate_pattern_message(self, pattern, context: AlertContext) -> str:
        """Generate AI-powered message for pattern alerts"""
        pattern_name = pattern.get('name', 'Unknown Pattern') if isinstance(pattern, dict) else getattr(pattern, 'name', 'Unknown Pattern')
        pattern_confidence = pattern.get('confidence', 75) if isinstance(pattern, dict) else getattr(pattern, 'confidence', 75)
        
        prompt = f"""
        Generate a concise, actionable alert message for a technical pattern detection:
        
        Pattern: {pattern_name}
        Asset: {context.asset_symbol}
        Current Price: ${context.current_price:.2f}
        24h Change: {context.price_change_24h:.2f}%
        Confidence: {pattern_confidence}%
        
        Include:
        - What the pattern indicates
        - Potential price targets
        - Risk considerations
        - Timeframe expectations
        
        Keep it under 200 words and actionable.
        """
        
        try:
            return await self.llm_client.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating pattern message: {e}")
            return f"Technical pattern {pattern_name} detected on {context.asset_symbol} with {pattern_confidence}% confidence."
    
    async def _generate_news_message(self, sentiment_analysis, context: AlertContext) -> str:
        """Generate AI-powered message for news alerts"""
        prompt = f"""
        Generate a concise alert message for news sentiment impact:
        
        Asset: {context.asset_symbol}
        Sentiment: {sentiment_analysis.sentiment_label}
        Confidence: {sentiment_analysis.confidence:.1%}
        Current Price: ${context.current_price:.2f}
        
        Key news events:
        {json.dumps(sentiment_analysis.key_events, indent=2)}
        
        Include:
        - Summary of key developments
        - Expected market impact
        - Trading implications
        - Risk factors
        
        Keep it under 200 words and actionable.
        """
        
        try:
            return await self.llm_client.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating news message: {e}")
            return f"News sentiment for {context.asset_symbol} is {sentiment_analysis.sentiment_label} with {sentiment_analysis.confidence:.1%} confidence."
    
    async def _generate_risk_message(self, scenario, context: AlertContext) -> str:
        """Generate AI-powered message for risk alerts"""
        try:
            prompt = f"""
            Generate a concise alert message for a risk management scenario:
            
            Asset: {context.asset_symbol}
            Risk Type: {scenario['type']}
            Severity: {scenario['severity']:.1%}
            Current Price: ${context.current_price:.2f}
            
            Include:
            - Description of the risk
            - Potential impact
            - Recommended actions
            - Risk mitigation strategies
            
            Keep it under 200 words and actionable.
            """
            return await self.llm_client.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating risk message: {e}")
            return f"Risk alert: {scenario['type']} detected for {context.asset_symbol} with {scenario['severity']:.1%} severity."
    
    async def _generate_anomaly_message(self, anomaly, context: AlertContext) -> str:
        """Generate AI-powered message for anomaly alerts"""
        try:
            prompt = f"""
            Generate a concise alert message for a market anomaly:
            
            Asset: {context.asset_symbol}
            Anomaly Type: {anomaly['type']}
            Significance: {anomaly['significance']:.1%}
            Current Price: ${context.current_price:.2f}
            
            Include:
            - Description of the anomaly
            - Potential market implications
            - Recommended monitoring actions
            - Risk considerations
            
            Keep it under 200 words and actionable.
            """
            return await self.llm_client.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating anomaly message: {e}")
            return f"Market anomaly: {anomaly['type']} detected for {context.asset_symbol} with {anomaly['significance']:.1%} significance."
    
    async def _generate_portfolio_message(self, opportunity, context: AlertContext) -> str:
        """Generate AI-powered message for portfolio alerts"""
        try:
            prompt = f"""
            Generate a concise alert message for a portfolio optimization opportunity:
            
            Asset: {context.asset_symbol}
            Opportunity Type: {opportunity['type']}
            Potential Impact: {opportunity['potential_impact']:.1%}
            Current Price: ${context.current_price:.2f}
            
            Include:
            - Description of the opportunity
            - Expected benefits
            - Implementation considerations
            - Risk factors
            
            Keep it under 200 words and actionable.
            """
            return await self.llm_client.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating portfolio message: {e}")
            return f"Portfolio opportunity: {opportunity['type']} for {context.asset_symbol} with {opportunity['potential_impact']:.1%} potential impact."
    
    async def send_smart_alert(
        self,
        alert: SmartAlert,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Send smart alert to user via appropriate channels
        
        Args:
            alert: Smart alert to send
            user_id: Target user ID
            db: Database session
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create alert record in database
            alert_record = Alert(
                user_id=user_id,
                alert_type="smart_alert",
                message=alert.message,
                trigger_value=alert.trigger_value,
                is_active=True,
                is_triggered=True,
                parameters={
                    "category": alert.category.value,
                    "priority": alert.priority.value,
                    "confidence_score": alert.confidence_score,
                    "action_items": alert.action_items,
                    "metadata": alert.metadata
                },
                triggered_at=datetime.now(timezone.utc)
            )
            
            db.add(alert_record)
            db.commit()
            
            # Format message for notifications
            formatted_message = self._format_alert_message(alert)
            
            # Send via Telegram (with fallback to local)
            success = await self.telegram_notifier.send_message(
                user_id=user_id,
                message=formatted_message,
                priority=alert.priority.value
            )
            
            if not success:
                # Fallback to local notification
                await self.local_notifier.send_notification(
                    title=alert.title,
                    message=formatted_message,
                    notification_type="smart_alert"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending smart alert: {str(e)}")
            return False
    
    def _format_alert_message(self, alert: SmartAlert) -> str:
        """Format alert message for notifications"""
        priority_emoji = {
            AlertPriority.LOW: "🔵",
            AlertPriority.MEDIUM: "🟡",
            AlertPriority.HIGH: "🟠",
            AlertPriority.CRITICAL: "🔴"
        }
        
        emoji = priority_emoji.get(alert.priority, "🔵")
        
        message = f"{emoji} **{alert.title}**\n\n"
        message += f"📊 **Asset:** {alert.asset_symbol}\n"
        message += f"📈 **Confidence:** {alert.confidence_score:.1%}\n"
        message += f"🎯 **Category:** {alert.category.value.replace('_', ' ').title()}\n\n"
        
        message += f"**Analysis:**\n{alert.message}\n\n"
        
        if alert.action_items:
            message += "**Recommended Actions:**\n"
            for i, action in enumerate(alert.action_items, 1):
                message += f"{i}. {action}\n"
        
        return message
    
    def _filter_and_rank_alerts(
        self,
        alerts: List[SmartAlert],
        user_id: int
    ) -> List[SmartAlert]:
        """Filter and rank alerts by relevance and priority"""
        # Remove duplicates and low-confidence alerts
        filtered_alerts = []
        seen_categories = set()
        
        for alert in sorted(alerts, key=lambda x: (x.priority.value, -x.confidence_score)):
            # Skip if we already have an alert for this category
            category_key = (alert.category, alert.asset_symbol)
            if category_key in seen_categories:
                continue
                
            # Skip if confidence is too low
            if alert.confidence_score < self.min_confidence_threshold:
                continue
                
            filtered_alerts.append(alert)
            seen_categories.add(category_key)
            
            # Limit number of alerts
            if len(filtered_alerts) >= 5:
                break
                
        return filtered_alerts
    
    def _determine_priority(self, confidence: float, strength: float) -> AlertPriority:
        """Determine alert priority based on confidence and strength"""
        score = (confidence + strength) / 2
        
        if score >= 0.9:
            return AlertPriority.CRITICAL
        elif score >= 0.8:
            return AlertPriority.HIGH
        elif score >= 0.7:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    # Placeholder methods for various analysis functions
    async def _analyze_risk_scenarios(self, context: AlertContext, user_id: int, db: Session) -> List[Dict]:
        """Analyze various risk scenarios"""
        # Implementation would include:
        # - Position size analysis
        # - Correlation risk
        # - Volatility analysis
        # - Drawdown risk
        # - Liquidity risk
        return []
    
    async def _detect_market_anomalies(self, context: AlertContext) -> List[Dict]:
        """Detect market anomalies"""
        # Implementation would include:
        # - Volume anomalies
        # - Price anomalies
        # - Spread anomalies
        # - Order book anomalies
        return []
    
    async def _analyze_portfolio_opportunities(
        self,
        context: AlertContext,
        user_id: int,
        db: Session
    ) -> List[Dict]:
        """Analyze portfolio optimization opportunities"""
        # Implementation would include:
        # - Rebalancing opportunities
        # - Diversification improvements
        # - Risk-adjusted return optimization
        # - Tax optimization
        return []
    
    # Additional helper methods for action generation
    def _generate_pattern_actions(self, pattern) -> List[str]:
        """Generate action items for pattern alerts"""
        pattern_name = pattern.get('name', 'detected pattern') if isinstance(pattern, dict) else getattr(pattern, 'name', 'detected pattern')
        return [
            f"Monitor {pattern_name} pattern completion",
            "Set appropriate stop-loss levels",
            "Consider position sizing based on pattern reliability",
            "Watch for volume confirmation"
        ]
    
    def _generate_news_actions(self, sentiment_analysis) -> List[str]:
        """Generate action items for news alerts"""
        return [
            "Monitor news developments closely",
            "Consider adjusting position size",
            "Review risk management parameters",
            "Watch for market reaction confirmation"
        ]
    
    def _generate_risk_actions(self, scenario) -> List[str]:
        """Generate action items for risk alerts"""
        return [
            "Review position sizing",
            "Consider hedging strategies",
            "Update stop-loss levels",
            "Monitor correlation changes"
        ]
    
    def _generate_anomaly_actions(self, anomaly) -> List[str]:
        """Generate action items for anomaly alerts"""
        return [
            "Investigate underlying causes",
            "Monitor for pattern continuation",
            "Consider contrarian opportunities",
            "Review market structure changes"
        ]
    
    def _generate_portfolio_actions(self, opportunity) -> List[str]:
        """Generate action items for portfolio alerts"""
        return [
            "Review portfolio allocation",
            "Consider rebalancing",
            "Analyze risk-return profile",
            "Monitor implementation timing"
        ]
    
    def _determine_news_priority(self, sentiment_analysis) -> AlertPriority:
        """Determine priority for news alerts"""
        # Use confidence and impact_level to determine priority
        confidence = sentiment_analysis.confidence
        impact_level = sentiment_analysis.impact_level
        
        if impact_level == "high" and confidence > 0.8:
            return AlertPriority.CRITICAL
        elif impact_level == "high" or confidence > 0.7:
            return AlertPriority.HIGH
        elif impact_level == "medium" or confidence > 0.5:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    def _determine_risk_priority(self, severity: float) -> AlertPriority:
        """Determine priority for risk alerts"""
        if severity > 0.9:
            return AlertPriority.CRITICAL
        elif severity > 0.8:
            return AlertPriority.HIGH
        elif severity > 0.7:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    def _determine_anomaly_priority(self, anomaly) -> AlertPriority:
        """Determine priority for anomaly alerts"""
        significance = anomaly["significance"]
        if significance > 0.95:
            return AlertPriority.CRITICAL
        elif significance > 0.9:
            return AlertPriority.HIGH
        elif significance > 0.85:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    def _determine_portfolio_priority(self, opportunity) -> AlertPriority:
        """Determine priority for portfolio alerts"""
        impact = opportunity["potential_impact"]
        if impact > 0.3:
            return AlertPriority.CRITICAL
        elif impact > 0.2:
            return AlertPriority.HIGH
        elif impact > 0.15:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW


# Factory function to create SmartAlertsEngine instance
def create_smart_alerts_engine() -> SmartAlertsEngine:
    """Create a SmartAlertsEngine instance with dependencies"""
    from .llm_client import get_llm_client
    from .pattern_detector import AdvancedPatternDetector
    from .news_analyzer import LLMNewsAnalyzer
    from src.notifications.telegram_notifier import TelegramNotifier
    from src.notifications.local_notifier import LocalNotifier
    from src.core.config import settings
    
    llm_client = get_llm_client()
    pattern_detector = AdvancedPatternDetector()
    news_analyzer = LLMNewsAnalyzer()
    telegram_notifier = TelegramNotifier(
        bot_token=settings.TELEGRAM_BOT_TOKEN or "dummy_token",
        chat_id=settings.TELEGRAM_CHAT_ID or "dummy_chat_id"
    )
    local_notifier = LocalNotifier()
    
    return SmartAlertsEngine(
        llm_client=llm_client,
        pattern_detector=pattern_detector,
        news_analyzer=news_analyzer,
        telegram_notifier=telegram_notifier,
        local_notifier=local_notifier
    )
