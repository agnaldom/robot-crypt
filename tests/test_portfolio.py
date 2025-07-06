"""
Tests for portfolio endpoints.
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestPortfolioEndpoints:
    """Test portfolio endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_portfolio_unauthorized(self, client: AsyncClient):
        """Test getting portfolio without authentication."""
        response = await client.get("/portfolio/")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_portfolio_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting empty portfolio."""
        response = await client.get("/portfolio/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_value"] == 0
        assert data["total_profit_loss"] == 0
        assert data["total_profit_loss_percentage"] == 0
        assert data["positions"] == []
    
    @pytest.mark.asyncio
    async def test_get_portfolio_with_positions(self, client: AsyncClient, auth_headers: dict):
        """Test getting portfolio with positions."""
        # Create some portfolio positions first
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.5",
            "average_price": "45000.00",
            "current_price": "50000.00"
        }
        
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/portfolio/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_value"] == 25000.0  # 0.5 * 50000
        assert data["total_profit_loss"] == 2500.0  # 0.5 * (50000 - 45000)
        assert data["total_profit_loss_percentage"] == 11.11  # Approximately
        assert len(data["positions"]) == 1
        assert data["positions"][0]["symbol"] == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_create_portfolio_position(self, client: AsyncClient, auth_headers: dict):
        """Test creating a portfolio position."""
        position_data = {
            "symbol": "ETHUSDT",
            "quantity": "2.0",
            "average_price": "3000.00",
            "current_price": "3200.00"
        }
        
        response = await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == "ETHUSDT"
        assert float(data["quantity"]) == 2.0
        assert float(data["average_price"]) == 3000.0
        assert float(data["current_price"]) == 3200.0
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_portfolio_position_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """Test creating portfolio position with invalid data."""
        invalid_data = {
            "symbol": "",
            "quantity": "-1",
            "average_price": "0",
            "current_price": "-100"
        }
        
        response = await client.post("/portfolio/positions", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_portfolio_positions(self, client: AsyncClient, auth_headers: dict):
        """Test getting portfolio positions."""
        # Create multiple positions
        positions_data = [
            {
                "symbol": "BTCUSDT",
                "quantity": "0.5",
                "average_price": "45000.00",
                "current_price": "50000.00"
            },
            {
                "symbol": "ETHUSDT",
                "quantity": "2.0",
                "average_price": "3000.00",
                "current_price": "3200.00"
            }
        ]
        
        for position_data in positions_data:
            await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/portfolio/positions", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        symbols = [pos["symbol"] for pos in data]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
    
    @pytest.mark.asyncio
    async def test_get_portfolio_position_by_id(self, client: AsyncClient, auth_headers: dict):
        """Test getting a specific portfolio position."""
        position_data = {
            "symbol": "ADAUSDT",
            "quantity": "100.0",
            "average_price": "1.50",
            "current_price": "1.75"
        }
        
        create_response = await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        position_id = create_response.json()["id"]
        
        response = await client.get(f"/portfolio/positions/{position_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == position_id
        assert data["symbol"] == "ADAUSDT"
        assert float(data["quantity"]) == 100.0
    
    @pytest.mark.asyncio
    async def test_get_portfolio_position_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent portfolio position."""
        response = await client.get("/portfolio/positions/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_portfolio_position(self, client: AsyncClient, auth_headers: dict):
        """Test updating a portfolio position."""
        position_data = {
            "symbol": "DOTUSDT",
            "quantity": "50.0",
            "average_price": "25.00",
            "current_price": "30.00"
        }
        
        create_response = await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        position_id = create_response.json()["id"]
        
        update_data = {
            "quantity": "75.0",
            "current_price": "35.00"
        }
        
        response = await client.put(f"/portfolio/positions/{position_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["quantity"]) == 75.0
        assert float(data["current_price"]) == 35.0
        assert data["symbol"] == "DOTUSDT"  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_update_portfolio_position_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent portfolio position."""
        update_data = {
            "quantity": "10.0",
            "current_price": "100.00"
        }
        
        response = await client.put("/portfolio/positions/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_portfolio_position(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a portfolio position."""
        position_data = {
            "symbol": "LINKUSDT",
            "quantity": "10.0",
            "average_price": "20.00",
            "current_price": "25.00"
        }
        
        create_response = await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        position_id = create_response.json()["id"]
        
        response = await client.delete(f"/portfolio/positions/{position_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify position is deleted
        get_response = await client.get(f"/portfolio/positions/{position_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_portfolio_position_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent portfolio position."""
        response = await client.delete("/portfolio/positions/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_portfolio_performance(self, client: AsyncClient, auth_headers: dict):
        """Test getting portfolio performance."""
        # Create some positions first
        positions_data = [
            {
                "symbol": "BTCUSDT",
                "quantity": "0.1",
                "average_price": "40000.00",
                "current_price": "50000.00"
            },
            {
                "symbol": "ETHUSDT",
                "quantity": "1.0",
                "average_price": "2500.00",
                "current_price": "3000.00"
            }
        ]
        
        for position_data in positions_data:
            await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/portfolio/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_invested" in data
        assert "current_value" in data
        assert "total_profit_loss" in data
        assert "total_profit_loss_percentage" in data
        assert "best_performing_asset" in data
        assert "worst_performing_asset" in data
        
        # Check calculations
        expected_invested = 40000 * 0.1 + 2500 * 1.0  # 4000 + 2500 = 6500
        expected_current = 50000 * 0.1 + 3000 * 1.0   # 5000 + 3000 = 8000
        expected_profit = expected_current - expected_invested  # 1500
        
        assert data["total_invested"] == expected_invested
        assert data["current_value"] == expected_current
        assert data["total_profit_loss"] == expected_profit
