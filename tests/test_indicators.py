"""
Tests for indicators endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from unittest.mock import AsyncMock, patch
import json

from src.schemas.technical_indicator import TechnicalIndicatorCreate
from src.schemas.macro_indicator import MacroIndicatorCreate
from src.models.technical_indicator import TechnicalIndicator
from src.models.macro_indicator import MacroIndicator
from src.models.asset import Asset
from src.models.user import User


class TestTechnicalIndicatorsEndpoints:
    """Test technical indicators endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_technical_indicators_success(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test successful retrieval of technical indicators."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        response = await client.get("/indicators/technical", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_technical_indicators_with_filters(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test retrieval of technical indicators with filters."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {
            "asset_id": 1,
            "indicator_type": "RSI",
            "timeframe": "1h",
            "skip": 0,
            "limit": 10
        }
        
        response = await client.get("/indicators/technical", headers=headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_technical_indicators_unauthorized(self, client: AsyncClient):
        """Test unauthorized access to technical indicators."""
        response = await client.get("/indicators/technical")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_technical_indicator_success(
        self, client: AsyncClient, authenticated_user_data: dict, test_db: AsyncSession
    ):
        """Test successful creation of technical indicator."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Create a test asset first
        from src.models.asset import Asset
        test_asset = Asset(
            symbol="BTC/USDT",
            name="Bitcoin",
            current_price=45000.0,
            volume_24h=1000000.0,
            market_cap=850000000.0
        )
        test_db.add(test_asset)
        await test_db.commit()
        await test_db.refresh(test_asset)
        
        indicator_data = {
            "asset_id": test_asset.id,
            "indicator_type": "RSI",
            "timeframe": "1h",
            "value": 65.5,
            "parameters": {"period": 14}
        }
        
        response = await client.post("/indicators/technical", headers=headers, json=indicator_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == test_asset.id
        assert data["indicator_type"] == "RSI"
        assert data["timeframe"] == "1h"
        assert data["value"] == 65.5
        assert data["parameters"]["period"] == 14
        assert "id" in data
        assert "calculated_at" in data
    
    @pytest.mark.asyncio
    async def test_create_technical_indicator_invalid_data(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test creation of technical indicator with invalid data."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        invalid_data = {
            "asset_id": "invalid",  # Should be integer
            "indicator_type": "",   # Should not be empty
            "timeframe": ""         # Should not be empty
        }
        
        response = await client.post("/indicators/technical", headers=headers, json=invalid_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_calculate_indicators_success(
        self, client: AsyncClient, authenticated_user_data: dict, test_db: AsyncSession
    ):
        """Test successful calculation of indicators."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Create a test asset first
        test_asset = Asset(
            symbol="BTC/USDT",
            name="Bitcoin",
            current_price=45000.0,
            volume_24h=1000000.0,
            market_cap=850000000.0
        )
        test_db.add(test_asset)
        await test_db.commit()
        await test_db.refresh(test_asset)
        
        params = {
            "asset_symbol": test_asset.symbol,
            "timeframe": "1h",
            "indicators": ["RSI", "MA", "EMA"]
        }
        
        with patch('src.services.technical_indicator_service.TechnicalIndicatorService.calculate_multiple_indicators') as mock_calc:
            mock_calc.return_value = {
                "RSI": {"value": 65.5, "signal": "neutral"},
                "SMA": {"value": 44500.0, "period": 20},
                "EMA": {"value": 44800.0, "period": 12}
            }
            
            response = await client.post("/indicators/calculate", headers=headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["asset_symbol"] == test_asset.symbol
        assert data["asset_id"] == test_asset.id
        assert data["timeframe"] == "1h"
        assert "indicators" in data
        assert "calculated_at" in data
    
    @pytest.mark.asyncio
    async def test_calculate_indicators_asset_not_found(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test calculation of indicators for non-existent asset."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {
            "asset_symbol": "NONEXISTENT/USDT",
            "timeframe": "1h",
            "indicators": ["RSI"]
        }
        
        response = await client.post("/indicators/calculate", headers=headers, params=params)
        
        assert response.status_code == 404
        assert "Asset not found" in response.json()["detail"]


class TestMacroIndicatorsEndpoints:
    """Test macro indicators endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_macro_indicators_success(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test successful retrieval of macro indicators."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        response = await client.get("/indicators/macro", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_macro_indicators_with_filters(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test retrieval of macro indicators with filters."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {
            "category": "fear_greed",
            "impact": "high",
            "skip": 0,
            "limit": 10
        }
        
        response = await client.get("/indicators/macro", headers=headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_create_macro_indicator_success(
        self, client: AsyncClient, superuser_data: dict
    ):
        """Test successful creation of macro indicator (superuser only)."""
        headers = {"Authorization": f"Bearer {superuser_data['token']}"}
        
        indicator_data = {
            "name": "Fear & Greed Index",
            "category": "fear_greed",
            "value": 45.0,
            "description": "Market sentiment indicator",
            "source": "Alternative.me",
            "impact": "medium",
            "metadata": {"classification": "Fear"}
        }
        
        response = await client.post("/indicators/macro", headers=headers, json=indicator_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Fear & Greed Index"
        assert data["category"] == "fear_greed"
        assert data["value"] == 45.0
        assert data["impact"] == "medium"
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_macro_indicator_unauthorized(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test creation of macro indicator with regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        indicator_data = {
            "name": "Test Indicator",
            "category": "test",
            "value": 100.0,
            "description": "Test indicator",
            "source": "Test",
            "impact": "low"
        }
        
        response = await client.post("/indicators/macro", headers=headers, json=indicator_data)
        
        assert response.status_code == 403  # Forbidden - superuser required


class TestTradingSignalsEndpoints:
    """Test trading signals endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_trading_signals_general(
        self, client: AsyncClient, authenticated_user_data: dict, test_db: AsyncSession
    ):
        """Test getting general trading signals."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Create test assets
        test_assets = [
            Asset(symbol="BTC/USDT", name="Bitcoin", current_price=45000.0),
            Asset(symbol="ETH/USDT", name="Ethereum", current_price=3000.0),
            Asset(symbol="ADA/USDT", name="Cardano", current_price=1.5),
            Asset(symbol="SOL/USDT", name="Solana", current_price=100.0)
        ]
        
        for asset in test_assets:
            test_db.add(asset)
        await test_db.commit()
        
        with patch('src.services.technical_indicator_service.TechnicalIndicatorService.generate_trading_signals') as mock_signals:
            mock_signals.return_value = {
                "signal": "buy",
                "confidence": 0.75,
                "individual_signals": [{"reason": "RSI oversold", "type": "buy"}],
                "indicators_used": ["RSI"],
                "generated_at": datetime.now().isoformat()
            }
            
            response = await client.get("/indicators/signals", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "generated_at" in data
        assert "total_signals" in data
        assert isinstance(data["signals"], list)
    
    @pytest.mark.asyncio
    async def test_get_trading_signals_specific_asset(
        self, client: AsyncClient, authenticated_user_data: dict, test_db: AsyncSession
    ):
        """Test getting trading signals for specific asset."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Create test asset
        test_asset = Asset(
            symbol="BTC/USDT",
            name="Bitcoin",
            current_price=45000.0
        )
        test_db.add(test_asset)
        await test_db.commit()
        await test_db.refresh(test_asset)
        
        params = {
            "asset_symbol": "BTC/USDT",
            "signal_type": "buy",
            "strength_min": 0.5
        }
        
        with patch('src.services.technical_indicator_service.TechnicalIndicatorService.generate_trading_signals') as mock_signals:
            mock_signals.return_value = {
                "signal": "buy",
                "confidence": 0.75,
                "individual_signals": [{"reason": "RSI oversold", "type": "buy"}],
                "indicators_used": ["RSI"],
                "generated_at": datetime.now().isoformat()
            }
            
            response = await client.get("/indicators/signals", headers=headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        signals = data["signals"]
        if signals:  # If there are signals
            assert all(signal["signal_type"] == "buy" for signal in signals)
            assert all(signal["strength"] >= 0.5 for signal in signals)


class TestMarketOverviewEndpoint:
    """Test market overview endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_market_overview_success(
        self, client: AsyncClient, authenticated_user_data: dict, test_db: AsyncSession
    ):
        """Test successful retrieval of market overview."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Create test data
        fear_greed = MacroIndicator(
            name="Fear & Greed Index",
            category="fear_greed",
            value=45.0,
            description="Market sentiment",
            source="Alternative.me",
            impact="medium",
            metadata={"classification": "Fear"}
        )
        test_db.add(fear_greed)
        await test_db.commit()
        
        with patch('src.services.macro_indicator_service.MacroIndicatorService.get_market_sentiment_analysis') as mock_sentiment:
            mock_sentiment.return_value = {
                "sentiment_score": 45.0,
                "overall_sentiment": "Bearish",
                "sentiment_factors": []
            }
            
            response = await client.get("/indicators/market-overview", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "fear_greed_index" in data
        assert "market_sentiment" in data
        assert "market_trend" in data
        assert "volume_analysis" in data
        assert "top_movers" in data
        assert "recent_events" in data
        assert "upcoming_events" in data
        assert "market_indices" in data
        assert "generated_at" in data
        
        # Check data structure
        assert isinstance(data["top_movers"]["gainers"], list)
        assert isinstance(data["top_movers"]["losers"], list)
        assert isinstance(data["recent_events"], list)
        assert isinstance(data["upcoming_events"], list)
        assert isinstance(data["market_indices"], list)
    
    @pytest.mark.asyncio
    async def test_get_market_overview_unauthorized(self, client: AsyncClient):
        """Test unauthorized access to market overview."""
        response = await client.get("/indicators/market-overview")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestIndicatorsErrorHandling:
    """Test error handling for indicators endpoints."""
    
    @pytest.mark.asyncio
    async def test_invalid_timeframe_parameter(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test handling of invalid timeframe parameter."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {"timeframe": "invalid_timeframe"}
        
        response = await client.get("/indicators/technical", headers=headers, params=params)
        
        # Should still return 200 but with empty results
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_database_error_handling(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test handling of database errors."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        with patch('src.services.technical_indicator_service.TechnicalIndicatorService.get_multi') as mock_get:
            mock_get.side_effect = Exception("Database connection error")
            
            response = await client.get("/indicators/technical", headers=headers)
        
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test handling of invalid JSON payload."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        # Send invalid JSON
        response = await client.post(
            "/indicators/technical", 
            headers=headers, 
            content="invalid json"
        )
        
        assert response.status_code == 422


class TestIndicatorsPerformance:
    """Test performance aspects of indicators endpoints."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test handling of large datasets."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {"limit": 1000}  # Large limit
        
        response = await client.get("/indicators/technical", headers=headers, params=params)
        
        assert response.status_code == 200
        # Response should be handled within reasonable time
        # This is implicitly tested by the test framework timeout
    
    @pytest.mark.asyncio
    async def test_pagination_parameters(
        self, client: AsyncClient, authenticated_user_data: dict
    ):
        """Test pagination parameters."""
        headers = {"Authorization": f"Bearer {authenticated_user_data['token']}"}
        
        params = {"skip": 10, "limit": 5}
        
        response = await client.get("/indicators/technical", headers=headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
