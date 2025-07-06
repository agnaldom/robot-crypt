"""Test suite for AI smart alerts module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from dataclasses import asdict

from src.ai.smart_alerts import (
    SmartAlertsEngine,
    AlertPriority,
    AlertCategory,
    AlertContext,
    SmartAlert
)


class TestAlertDataClasses:
    """Test cases for alert data classes."""
    
    def test_alert_priority_enum(self):
        """Test AlertPriority enum values."""
        assert AlertPriority.LOW.value == "low"
        assert AlertPriority.MEDIUM.value == "medium"
        assert AlertPriority.HIGH.value == "high"
        assert AlertPriority.CRITICAL.value == "critical"
    
    def test_alert_category_enum(self):
        """Test AlertCategory enum values."""
        assert AlertCategory.MARKET_ANOMALY.value == "market_anomaly"
        assert AlertCategory.TECHNICAL_PATTERN.value == "technical_pattern"
        assert AlertCategory.NEWS_SENTIMENT.value == "news_sentiment"
        assert AlertCategory.RISK_MANAGEMENT.value == "risk_management"
    
    def test_alert_context_creation(self):
        """Test AlertContext dataclass creation."""
        context = AlertContext(
            asset_symbol="BTC/USDT",
            current_price=50000.0,
            price_change_24h=2.5,
            volume_change_24h=15.0,
            technical_indicators={
                "rsi": 65,
                "macd": 150,
                "bb_position": "upper"
            },
            market_sentiment="bullish",
            news_events=[
                {"title": "Bitcoin ETF Approved", "sentiment": "positive"}
            ],
            portfolio_impact={"total_exposure": 0.3, "risk_level": "medium"}
        )
        
        assert context.asset_symbol == "BTC/USDT"
        assert context.current_price == 50000.0
        assert context.technical_indicators["rsi"] == 65
        assert context.market_sentiment == "bullish"
        assert len(context.news_events) == 1
    
    def test_smart_alert_creation(self):
        """Test SmartAlert dataclass creation."""
        alert = SmartAlert(
            category=AlertCategory.TECHNICAL_PATTERN,
            priority=AlertPriority.HIGH,
            title="Bullish Flag Pattern Detected",
            message="A bullish flag pattern has formed on BTC/USDT",
            action_items=["Monitor breakout", "Set stop-loss"],
            confidence_score=0.85,
            asset_symbol="BTC/USDT",
            trigger_value=50000.0,
            expires_at=datetime.now() + timedelta(hours=24),
            metadata={"pattern": "bullish_flag", "timeframe": "4h"}
        )
        
        assert alert.category == AlertCategory.TECHNICAL_PATTERN
        assert alert.priority == AlertPriority.HIGH
        assert alert.confidence_score == 0.85
        assert len(alert.action_items) == 2
        assert alert.metadata["pattern"] == "bullish_flag"


class TestSmartAlertsEngine:
    """Test cases for SmartAlertsEngine class."""
    
    def setup_method(self):
        """Set up test smart alerts engine."""
        self.mock_llm_client = Mock()
        self.mock_pattern_detector = Mock()
        self.mock_news_analyzer = Mock()
        self.mock_telegram_notifier = Mock()
        self.mock_local_notifier = Mock()
        
        self.engine = SmartAlertsEngine(
            llm_client=self.mock_llm_client,
            pattern_detector=self.mock_pattern_detector,
            news_analyzer=self.mock_news_analyzer,
            telegram_notifier=self.mock_telegram_notifier,
            local_notifier=self.mock_local_notifier
        )
    
    def create_sample_alert_context(self):
        """Create sample alert context for testing."""
        return AlertContext(
            asset_symbol="BTC/USDT",
            current_price=50000.0,
            price_change_24h=5.2,
            volume_change_24h=25.0,
            technical_indicators={
                "rsi": 75,
                "macd": 200,
                "bb_position": "upper",
                "volume": "high"
            },
            market_sentiment="bullish",
            news_events=[
                {"title": "Major Exchange Lists Bitcoin", "sentiment": "positive"}
            ]
        )
    
    def test_smart_alerts_engine_initialization(self):
        """Test SmartAlertsEngine initialization."""
        assert self.engine is not None
        assert self.engine.llm_client is not None
        assert self.engine.pattern_detector is not None
        assert self.engine.news_analyzer is not None
        assert self.engine.min_confidence_threshold == 0.7
        assert self.engine.max_alerts_per_hour == 10
        assert isinstance(self.engine.recent_alerts_cache, dict)
    
    @pytest.mark.asyncio
    async def test_generate_smart_alerts_success(self):
        """Test successful smart alerts generation."""
        context = self.create_sample_alert_context()
        user_id = 1
        
        # Mock database session
        mock_db = Mock()
        
        # Mock individual alert generation methods
        with patch.object(self.engine, '_generate_pattern_alerts') as mock_pattern, \
             patch.object(self.engine, '_generate_news_alerts') as mock_news, \
             patch.object(self.engine, '_generate_risk_alerts') as mock_risk, \
             patch.object(self.engine, '_generate_anomaly_alerts') as mock_anomaly, \
             patch.object(self.engine, '_generate_portfolio_alerts') as mock_portfolio, \
             patch.object(self.engine, '_filter_and_rank_alerts') as mock_filter:
            
            # Mock alert responses
            pattern_alert = SmartAlert(
                category=AlertCategory.TECHNICAL_PATTERN,
                priority=AlertPriority.HIGH,
                title="RSI Overbought",
                message="RSI indicates overbought condition",
                action_items=["Consider taking profits"],
                confidence_score=0.85,
                asset_symbol="BTC/USDT"
            )
            
            mock_pattern.return_value = [pattern_alert]
            mock_news.return_value = []
            mock_risk.return_value = []
            mock_anomaly.return_value = []
            mock_portfolio.return_value = []
            mock_filter.return_value = [pattern_alert]
            
            alerts = await self.engine.generate_smart_alerts(context, user_id, mock_db)
            
            assert isinstance(alerts, list)
            assert len(alerts) == 1
            assert alerts[0].category == AlertCategory.TECHNICAL_PATTERN
            assert alerts[0].confidence_score == 0.85
    
    @pytest.mark.asyncio
    async def test_generate_smart_alerts_error_handling(self):
        """Test smart alerts generation error handling."""
        context = self.create_sample_alert_context()
        user_id = 1
        mock_db = Mock()
        
        # Mock an error in pattern alerts
        with patch.object(self.engine, '_generate_pattern_alerts') as mock_pattern:
            mock_pattern.side_effect = Exception("Pattern detection error")
            
            alerts = await self.engine.generate_smart_alerts(context, user_id, mock_db)
            
            assert isinstance(alerts, list)
            assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_generate_pattern_alerts(self):
        """Test pattern alerts generation."""
        context = self.create_sample_alert_context()
        
        # Mock pattern detector response - use dict-like object that supports .get()
        mock_pattern = {
            "confidence": 80,  # Should be percentage (0-100)
            "strength": 0.7,
            "name": "Double Top",
            "pattern_type": "reversal"
        }
        
        self.mock_pattern_detector.detect_complex_patterns = AsyncMock(return_value=[mock_pattern])
        
        with patch.object(self.engine, '_generate_pattern_message') as mock_message, \
             patch.object(self.engine, '_generate_pattern_actions') as mock_actions, \
             patch.object(self.engine, '_determine_priority') as mock_priority:
            
            mock_message.return_value = "Double top pattern detected"
            mock_actions.return_value = ["Watch for breakdown"]
            mock_priority.return_value = AlertPriority.HIGH
            
            alerts = await self.engine._generate_pattern_alerts(context)
            
            assert len(alerts) == 1
            assert alerts[0].category == AlertCategory.TECHNICAL_PATTERN
            assert alerts[0].title == "Technical Pattern Detected: Double Top"
            assert alerts[0].confidence_score == 0.8
    
    @pytest.mark.asyncio
    async def test_generate_news_alerts(self):
        """Test news alerts generation."""
        context = self.create_sample_alert_context()

        # Mock news analyzer response - use proper dataclass-like object
        from dataclasses import dataclass

        @dataclass
        class MockSentiment:
            confidence: float = 0.9
            overall_sentiment: str = "very_bullish"
            sentiment_label: str = "very_bullish"  # Added missing attribute
            impact_level: str = "high"
            key_events: list = None

            def __post_init__(self):
                if self.key_events is None:
                    self.key_events = []

        mock_sentiment = MockSentiment()
        
        self.mock_news_analyzer.analyze_crypto_news = AsyncMock(return_value=mock_sentiment)
        
        with patch.object(self.engine, '_generate_news_message') as mock_message, \
             patch.object(self.engine, '_generate_news_actions') as mock_actions, \
             patch.object(self.engine, '_determine_news_priority') as mock_priority:
            
            mock_message.return_value = "Strong bullish news sentiment"
            mock_actions.return_value = ["Monitor news developments"]
            mock_priority.return_value = AlertPriority.HIGH
            
            alerts = await self.engine._generate_news_alerts(context)
            
            assert len(alerts) == 1
            assert alerts[0].category == AlertCategory.NEWS_SENTIMENT
            assert alerts[0].title == "News Sentiment Alert: very_bullish"
    
    @pytest.mark.asyncio
    async def test_generate_news_alerts_no_events(self):
        """Test news alerts generation with no news events."""
        context = AlertContext(
            asset_symbol="BTC/USDT",
            current_price=50000.0,
            price_change_24h=2.0,
            volume_change_24h=10.0,
            technical_indicators={},
            news_events=None  # No news events
        )
        
        alerts = await self.engine._generate_news_alerts(context)
        
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_generate_risk_alerts(self):
        """Test risk alerts generation."""
        context = self.create_sample_alert_context()
        user_id = 1
        mock_db = Mock()
        
        # Mock risk scenario analysis
        with patch.object(self.engine, '_analyze_risk_scenarios') as mock_analyze:
            mock_analyze.return_value = [
                {
                    "type": "concentration_risk",
                    "severity": 0.8,
                    "confidence": 0.9,
                    "description": "High concentration in volatile assets"
                }
            ]
            
            with patch.object(self.engine, '_generate_risk_message') as mock_message, \
                 patch.object(self.engine, '_generate_risk_actions') as mock_actions, \
                 patch.object(self.engine, '_determine_risk_priority') as mock_priority:
                
                mock_message.return_value = "Concentration risk detected"
                mock_actions.return_value = ["Diversify portfolio"]
                mock_priority.return_value = AlertPriority.HIGH
                
                alerts = await self.engine._generate_risk_alerts(context, user_id, mock_db)
                
                assert len(alerts) == 1
                assert alerts[0].category == AlertCategory.RISK_MANAGEMENT
                assert alerts[0].title == "Risk Alert: concentration_risk"
    
    @pytest.mark.asyncio
    async def test_generate_anomaly_alerts(self):
        """Test anomaly alerts generation."""
        context = self.create_sample_alert_context()
        
        # Mock anomaly detection
        with patch.object(self.engine, '_detect_market_anomalies') as mock_detect:
            mock_detect.return_value = [
                {
                    "type": "volume_spike",
                    "significance": 0.9,
                    "confidence": 0.85,
                    "description": "Unusual volume spike detected"
                }
            ]
            
            with patch.object(self.engine, '_generate_anomaly_message') as mock_message, \
                 patch.object(self.engine, '_generate_anomaly_actions') as mock_actions, \
                 patch.object(self.engine, '_determine_anomaly_priority') as mock_priority:
                
                mock_message.return_value = "Volume anomaly detected"
                mock_actions.return_value = ["Investigate volume spike"]
                mock_priority.return_value = AlertPriority.HIGH
                
                alerts = await self.engine._generate_anomaly_alerts(context)
                
                assert len(alerts) == 1
                assert alerts[0].category == AlertCategory.MARKET_ANOMALY
    
    @pytest.mark.asyncio
    async def test_generate_portfolio_alerts(self):
        """Test portfolio alerts generation."""
        context = AlertContext(
            asset_symbol="BTC/USDT",
            current_price=50000.0,
            price_change_24h=2.0,
            volume_change_24h=10.0,
            technical_indicators={},
            portfolio_impact={"exposure": 0.6, "risk": "high"}
        )
        user_id = 1
        mock_db = Mock()
        
        # Mock portfolio opportunity analysis
        with patch.object(self.engine, '_analyze_portfolio_opportunities') as mock_analyze:
            mock_analyze.return_value = [
                {
                    "type": "rebalancing",
                    "potential_impact": 0.15,
                    "confidence": 0.8,
                    "description": "Portfolio rebalancing opportunity"
                }
            ]
            
            with patch.object(self.engine, '_generate_portfolio_message') as mock_message, \
                 patch.object(self.engine, '_generate_portfolio_actions') as mock_actions, \
                 patch.object(self.engine, '_determine_portfolio_priority') as mock_priority:
                
                mock_message.return_value = "Rebalancing opportunity"
                mock_actions.return_value = ["Review allocation"]
                mock_priority.return_value = AlertPriority.MEDIUM
                
                alerts = await self.engine._generate_portfolio_alerts(context, user_id, mock_db)
                
                assert len(alerts) == 1
                assert alerts[0].category == AlertCategory.PORTFOLIO_OPTIMIZATION
    
    @pytest.mark.asyncio
    async def test_generate_portfolio_alerts_no_impact(self):
        """Test portfolio alerts generation with no portfolio impact."""
        context = AlertContext(
            asset_symbol="BTC/USDT",
            current_price=50000.0,
            price_change_24h=2.0,
            volume_change_24h=10.0,
            technical_indicators={},
            portfolio_impact=None  # No portfolio impact
        )
        user_id = 1
        mock_db = Mock()
        
        alerts = await self.engine._generate_portfolio_alerts(context, user_id, mock_db)
        
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_generate_pattern_message(self):
        """Test pattern message generation."""
        mock_pattern = Mock()
        mock_pattern.name = "Head and Shoulders"
        mock_pattern.confidence = 0.85
        
        context = self.create_sample_alert_context()
        
        self.mock_llm_client.generate_text = AsyncMock(
            return_value="Head and Shoulders pattern suggests potential reversal with 85% confidence."
        )
        
        message = await self.engine._generate_pattern_message(mock_pattern, context)
        
        assert isinstance(message, str)
        assert "Head and Shoulders" in message or "pattern" in message.lower()
    
    @pytest.mark.asyncio
    async def test_generate_news_message(self):
        """Test news message generation."""
        from dataclasses import dataclass

        @dataclass
        class MockSentiment:
            overall_sentiment: str = "bullish"
            sentiment_label: str = "bullish"  # Added missing attribute
            confidence: float = 0.9
            key_events: list = None
            impact_level: str = "high"

            def __post_init__(self):
                if self.key_events is None:
                    self.key_events = ["Bitcoin ETF approved", "Institutional adoption"]

        mock_sentiment = MockSentiment()
        
        context = self.create_sample_alert_context()
        
        self.mock_llm_client.generate_text = AsyncMock(
            return_value="Strong bullish sentiment driven by ETF approval and institutional adoption."
        )
        
        message = await self.engine._generate_news_message(mock_sentiment, context)
        
        assert isinstance(message, str)
        assert len(message) > 0
    
    @pytest.mark.asyncio
    async def test_send_smart_alert_success(self):
        """Test successful smart alert sending."""
        alert = SmartAlert(
            category=AlertCategory.TECHNICAL_PATTERN,
            priority=AlertPriority.HIGH,
            title="Test Alert",
            message="Test alert message",
            action_items=["Test action"],
            confidence_score=0.8,
            asset_symbol="BTC/USDT"
        )
        user_id = 1
        
        # Mock database session
        mock_db = Mock()
        
        # Mock successful telegram notification
        self.mock_telegram_notifier.send_message = AsyncMock(return_value=True)
        
        # Mock the database operations to avoid SQLAlchemy errors
        with patch('src.ai.smart_alerts.Alert') as mock_alert_model:
            mock_alert_instance = Mock()
            mock_alert_model.return_value = mock_alert_instance
            
            result = await self.engine.send_smart_alert(alert, user_id, mock_db)
            
            assert result is True
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            self.mock_telegram_notifier.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_smart_alert_telegram_fallback(self):
        """Test smart alert sending with telegram fallback to local."""
        alert = SmartAlert(
            category=AlertCategory.NEWS_SENTIMENT,
            priority=AlertPriority.MEDIUM,
            title="News Alert",
            message="News alert message",
            action_items=["Check news"],
            confidence_score=0.7,
            asset_symbol="ETH/USDT"
        )
        user_id = 1
        mock_db = Mock()
        
        # Mock failed telegram, successful local notification
        self.mock_telegram_notifier.send_message = AsyncMock(return_value=False)
        self.mock_local_notifier.send_notification = AsyncMock(return_value=True)
        
        # Mock the database operations to avoid SQLAlchemy errors
        with patch('src.ai.smart_alerts.Alert') as mock_alert_model:
            mock_alert_instance = Mock()
            mock_alert_model.return_value = mock_alert_instance
            
            result = await self.engine.send_smart_alert(alert, user_id, mock_db)
            
            assert result is True
            self.mock_telegram_notifier.send_message.assert_called_once()
            self.mock_local_notifier.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_smart_alert_error(self):
        """Test smart alert sending error handling."""
        alert = SmartAlert(
            category=AlertCategory.RISK_MANAGEMENT,
            priority=AlertPriority.CRITICAL,
            title="Risk Alert",
            message="Critical risk detected",
            action_items=["Take action"],
            confidence_score=0.95,
            asset_symbol="BTC/USDT"
        )
        user_id = 1
        
        # Mock database error
        mock_db = Mock()
        mock_db.add.side_effect = Exception("Database error")
        
        # Mock the database operations to avoid SQLAlchemy errors
        with patch('src.ai.smart_alerts.Alert') as mock_alert_model:
            mock_alert_instance = Mock()
            mock_alert_model.return_value = mock_alert_instance
            
            result = await self.engine.send_smart_alert(alert, user_id, mock_db)
            
            assert result is False
    
    def test_format_alert_message(self):
        """Test alert message formatting."""
        alert = SmartAlert(
            category=AlertCategory.TECHNICAL_PATTERN,
            priority=AlertPriority.HIGH,
            title="Pattern Alert",
            message="Technical pattern detected with strong signals",
            action_items=["Monitor breakout", "Set stop-loss", "Adjust position size"],
            confidence_score=0.87,
            asset_symbol="BTC/USDT"
        )
        
        formatted_message = self.engine._format_alert_message(alert)
        
        assert isinstance(formatted_message, str)
        assert "🟠" in formatted_message  # High priority emoji
        assert "Pattern Alert" in formatted_message
        assert "BTC/USDT" in formatted_message
        assert "87.0%" in formatted_message  # Confidence
        assert "Technical Pattern" in formatted_message  # Category
        assert "Monitor breakout" in formatted_message  # Action items
        assert "Set stop-loss" in formatted_message
    
    def test_filter_and_rank_alerts(self):
        """Test alert filtering and ranking."""
        alerts = [
            SmartAlert(
                category=AlertCategory.TECHNICAL_PATTERN,
                priority=AlertPriority.LOW,
                title="Low Priority Alert",
                message="Low priority message",
                action_items=[],
                confidence_score=0.6,  # Below threshold
                asset_symbol="BTC/USDT"
            ),
            SmartAlert(
                category=AlertCategory.NEWS_SENTIMENT,
                priority=AlertPriority.HIGH,
                title="High Priority Alert",
                message="High priority message",
                action_items=[],
                confidence_score=0.9,
                asset_symbol="BTC/USDT"
            ),
            SmartAlert(
                category=AlertCategory.TECHNICAL_PATTERN,  # Duplicate category+symbol
                priority=AlertPriority.MEDIUM,
                title="Duplicate Category Alert",
                message="Another technical alert",
                action_items=[],
                confidence_score=0.8,
                asset_symbol="BTC/USDT"
            )
        ]
        
        filtered_alerts = self.engine._filter_and_rank_alerts(alerts, user_id=1)
        
        # Should filter out low confidence (0.6) and keep both high confidence alerts
        # since they have different categories (TECHNICAL_PATTERN vs NEWS_SENTIMENT)
        assert len(filtered_alerts) == 2
        # The highest priority and confidence should be first
        assert filtered_alerts[0].priority == AlertPriority.HIGH
        assert filtered_alerts[0].confidence_score == 0.9
    
    def test_determine_priority_levels(self):
        """Test priority determination based on confidence and strength."""
        test_cases = [
            (0.95, 0.9, AlertPriority.CRITICAL),
            (0.85, 0.8, AlertPriority.HIGH),
            (0.75, 0.7, AlertPriority.MEDIUM),
            (0.6, 0.5, AlertPriority.LOW)
        ]
        
        for confidence, strength, expected_priority in test_cases:
            priority = self.engine._determine_priority(confidence, strength)
            assert priority == expected_priority
    
    def test_generate_action_items(self):
        """Test action item generation for different alert types."""
        # Test pattern actions
        mock_pattern = Mock()
        mock_pattern.name = "Bull Flag"
        
        pattern_actions = self.engine._generate_pattern_actions(mock_pattern)
        assert isinstance(pattern_actions, list)
        assert len(pattern_actions) > 0
        assert any("pattern" in action.lower() for action in pattern_actions)
        
        # Test news actions
        from dataclasses import dataclass
        
        @dataclass
        class MockSentiment:
            overall_sentiment: str = "bullish"
            impact_level: str = "high"
            
        mock_sentiment = MockSentiment()
        news_actions = self.engine._generate_news_actions(mock_sentiment)
        assert isinstance(news_actions, list)
        assert len(news_actions) > 0
        
        # Test risk actions
        mock_scenario = {"type": "high_volatility"}
        risk_actions = self.engine._generate_risk_actions(mock_scenario)
        assert isinstance(risk_actions, list)
        assert len(risk_actions) > 0
        
        # Test anomaly actions
        mock_anomaly = {"type": "volume_spike"}
        anomaly_actions = self.engine._generate_anomaly_actions(mock_anomaly)
        assert isinstance(anomaly_actions, list)
        assert len(anomaly_actions) > 0
        
        # Test portfolio actions
        mock_opportunity = {"type": "rebalancing"}
        portfolio_actions = self.engine._generate_portfolio_actions(mock_opportunity)
        assert isinstance(portfolio_actions, list)
        assert len(portfolio_actions) > 0
    
    def test_priority_determination_methods(self):
        """Test various priority determination methods."""
        # Test news priority - create proper dataclass-like object
        from dataclasses import dataclass
        
        @dataclass
        class MockSentiment:
            impact_score: float
            confidence: float = 0.9
            overall_sentiment: str = "bullish"
            impact_level: str = "high"
            
        mock_sentiment = MockSentiment(impact_score=0.9)
        priority = self.engine._determine_news_priority(mock_sentiment)
        assert priority == AlertPriority.CRITICAL
        
        # Test risk priority
        priority = self.engine._determine_risk_priority(0.85)
        assert priority == AlertPriority.HIGH
        
        # Test anomaly priority
        mock_anomaly = {"significance": 0.92}
        priority = self.engine._determine_anomaly_priority(mock_anomaly)
        assert priority == AlertPriority.HIGH
        
        # Test portfolio priority
        mock_opportunity = {"potential_impact": 0.25}
        priority = self.engine._determine_portfolio_priority(mock_opportunity)
        assert priority == AlertPriority.HIGH


class TestCreateSmartAlertsEngine:
    """Test cases for the factory function."""
    
    @patch('src.ai.smart_alerts.get_llm_client')
    @patch('src.ai.smart_alerts.AdvancedPatternDetector')
    @patch('src.ai.smart_alerts.LLMNewsAnalyzer')
    @patch('src.ai.smart_alerts.TelegramNotifier')
    @patch('src.ai.smart_alerts.LocalNotifier')
    def test_create_smart_alerts_engine(self, mock_local, mock_telegram, 
                                      mock_news_analyzer, mock_pattern_detector, 
                                      mock_llm_client):
        """Test factory function for creating SmartAlertsEngine."""
        from src.ai.smart_alerts import create_smart_alerts_engine
        
        # Mock all dependencies
        mock_llm_client.return_value = Mock()
        mock_pattern_detector.return_value = Mock()
        mock_news_analyzer.return_value = Mock()
        mock_telegram.return_value = Mock()
        mock_local.return_value = Mock()
        
        engine = create_smart_alerts_engine()
        
        assert isinstance(engine, SmartAlertsEngine)
        assert engine.llm_client is not None
        assert engine.pattern_detector is not None
        assert engine.news_analyzer is not None
        assert engine.telegram_notifier is not None
        assert engine.local_notifier is not None


if __name__ == '__main__':
    pytest.main([__file__])
