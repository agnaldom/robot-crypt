"""
Tests for trades endpoints.
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, timedelta


class TestTradesEndpoints:
    """Test trades endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_trades_unauthorized(self, client: AsyncClient):
        """Test getting trades without authentication."""
        response = await client.get("/trades/")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_trades_empty(self, client: AsyncClient, auth_headers: dict, test_user):
        """Test getting empty trades list."""
        response = await client.get("/trades/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_create_buy_trade(self, authenticated_client: AsyncClient):
        """Test creating a buy trade."""
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        response = await authenticated_client.post("/trades/", json=trade_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["side"] == "buy"
        assert float(data["quantity"]) == 0.01
        assert float(data["price"]) == 55000.0
        assert data["exchange"] == "binance"
        assert data["status"] == "pending"
        assert float(data["total_value"]) == 550.0  # 0.01 * 55000
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_sell_trade(self, authenticated_client: AsyncClient):
        """Test creating a sell trade."""
        trade_data = {
            "symbol": "ETHUSDT",
            "side": "sell",
            "quantity": "0.5",
            "price": "2000.00",
            "exchange": "binance"
        }
        
        response = await authenticated_client.post("/trades/", json=trade_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == "ETHUSDT"
        assert data["side"] == "sell"
        assert float(data["quantity"]) == 0.5
        assert float(data["price"]) == 2000.0
        assert data["exchange"] == "binance"
        assert data["status"] == "pending"
        assert float(data["total_value"]) == 1000.0  # 0.5 * 2000
    
    @pytest.mark.asyncio
    async def test_create_trade_with_stop_loss(self, authenticated_client: AsyncClient):
        """Test creating a trade with stop loss."""
        trade_data = {
            "symbol": "ADAUSDT",
            "side": "buy",
            "quantity": "100",
            "price": "1.50",
            "exchange": "binance",
            "stop_loss": "1.30"
        }
        
        response = await authenticated_client.post("/trades/", json=trade_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == "ADAUSDT"
        assert float(data["stop_loss"]) == 1.30
        assert float(data["total_value"]) == 150.0  # 100 * 1.50
    
    @pytest.mark.asyncio
    async def test_create_trade_with_take_profit(self, authenticated_client: AsyncClient):
        """Test creating a trade with take profit."""
        trade_data = {
            "symbol": "DOTUSDT",
            "side": "buy",
            "quantity": "10",
            "price": "20.00",
            "exchange": "binance",
            "take_profit": "25.00"
        }
        
        response = await authenticated_client.post("/trades/", json=trade_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == "DOTUSDT"
        assert float(data["take_profit"]) == 25.0
        assert float(data["total_value"]) == 200.0  # 10 * 20
    
    @pytest.mark.asyncio
    async def test_create_trade_invalid_data(self, authenticated_client: AsyncClient):
        """Test creating trade with invalid data."""
        invalid_data = {
            "symbol": "",
            "side": "invalid_side",
            "quantity": "-1",
            "price": "0",
            "exchange": ""
        }
        
        response = await authenticated_client.post("/trades/", json=invalid_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_trades_list(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades list."""
        # Create multiple trades
        trades_data = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": "0.01",
                "price": "55000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "sell",
                "quantity": "0.5",
                "price": "2000.00",
                "exchange": "binance"
            }
        ]
        
        for trade_data in trades_data:
            await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        response = await client.get("/trades/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        symbols = [trade["symbol"] for trade in data]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
    
    @pytest.mark.asyncio
    async def test_get_trade_by_id(self, client: AsyncClient, auth_headers: dict):
        """Test getting a specific trade."""
        trade_data = {
            "symbol": "LINKUSDT",
            "side": "buy",
            "quantity": "5",
            "price": "15.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        response = await client.get(f"/trades/{trade_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == trade_id
        assert data["symbol"] == "LINKUSDT"
        assert data["side"] == "buy"
        assert float(data["quantity"]) == 5.0
        assert float(data["price"]) == 15.0
    
    @pytest.mark.asyncio
    async def test_get_trade_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent trade."""
        response = await client.get("/trades/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_trade(self, client: AsyncClient, auth_headers: dict):
        """Test updating a trade."""
        trade_data = {
            "symbol": "UNIUSDT",
            "side": "buy",
            "quantity": "2",
            "price": "10.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        update_data = {
            "quantity": "3",
            "price": "12.00",
            "stop_loss": "9.00"
        }
        
        response = await client.put(f"/trades/{trade_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["quantity"]) == 3.0
        assert float(data["price"]) == 12.0
        assert float(data["stop_loss"]) == 9.0
        assert float(data["total_value"]) == 36.0  # 3 * 12
        assert data["symbol"] == "UNIUSDT"  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_update_trade_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent trade."""
        update_data = {
            "quantity": "5",
            "price": "100.00"
        }
        
        response = await client.put("/trades/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_trade(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a trade."""
        trade_data = {
            "symbol": "SOLUSDT",
            "side": "buy",
            "quantity": "1",
            "price": "100.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        response = await client.delete(f"/trades/{trade_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify trade is deleted
        get_response = await client.get(f"/trades/{trade_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_trade_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent trade."""
        response = await client.delete("/trades/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_trade(self, client: AsyncClient, auth_headers: dict):
        """Test executing a pending trade."""
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        # Execute the trade
        response = await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "executed"
        assert "executed_at" in data
        assert data["executed_price"] is not None
        assert data["executed_quantity"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_trade_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test executing non-existent trade."""
        response = await client.post("/trades/99999/execute", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_cancel_trade(self, client: AsyncClient, auth_headers: dict):
        """Test canceling a pending trade."""
        trade_data = {
            "symbol": "ETHUSDT",
            "side": "sell",
            "quantity": "0.5",
            "price": "2000.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        # Cancel the trade
        response = await client.post(f"/trades/{trade_id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "cancelled"
        assert "cancelled_at" in data
    
    @pytest.mark.asyncio
    async def test_cancel_trade_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test canceling non-existent trade."""
        response = await client.post("/trades/99999/cancel", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_trades_by_symbol(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades filtered by symbol."""
        # Create trades for different symbols
        trades_data = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": "0.01",
                "price": "55000.00",
                "exchange": "binance"
            },
            {
                "symbol": "BTCUSDT",
                "side": "sell",
                "quantity": "0.005",
                "price": "56000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "buy",
                "quantity": "0.5",
                "price": "2000.00",
                "exchange": "binance"
            }
        ]
        
        for trade_data in trades_data:
            await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        # Get trades for BTCUSDT only
        response = await client.get("/trades/?symbol=BTCUSDT", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        for trade in data:
            assert trade["symbol"] == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_get_trades_by_side(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades filtered by side."""
        # Create buy and sell trades
        trades_data = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": "0.01",
                "price": "55000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "buy",
                "quantity": "0.5",
                "price": "2000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ADAUSDT",
                "side": "sell",
                "quantity": "100",
                "price": "1.50",
                "exchange": "binance"
            }
        ]
        
        for trade_data in trades_data:
            await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        # Get only buy trades
        response = await client.get("/trades/?side=buy", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        for trade in data:
            assert trade["side"] == "buy"
    
    @pytest.mark.asyncio
    async def test_get_trades_by_status(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades filtered by status."""
        # Create pending trade
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        
        # Execute the trade
        await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        
        # Create another pending trade
        await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        # Get only executed trades
        response = await client.get("/trades/?status=executed", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "executed"
    
    @pytest.mark.asyncio
    async def test_get_trades_by_exchange(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades filtered by exchange."""
        # Create trades for different exchanges
        trades_data = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": "0.01",
                "price": "55000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "buy",
                "quantity": "0.5",
                "price": "2000.00",
                "exchange": "coinbase"
            },
            {
                "symbol": "ADAUSDT",
                "side": "sell",
                "quantity": "100",
                "price": "1.50",
                "exchange": "binance"
            }
        ]
        
        for trade_data in trades_data:
            await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        # Get only Binance trades
        response = await client.get("/trades/?exchange=binance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        for trade in data:
            assert trade["exchange"] == "binance"
    
    @pytest.mark.asyncio
    async def test_get_trades_with_pagination(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades with pagination."""
        # Create multiple trades
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        for i in range(5):
            await client.post("/trades/", json=trade_data, headers=auth_headers)
        
        # Get trades with limit
        response = await client.get("/trades/?limit=2", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Get next page
        response = await client.get("/trades/?limit=2&offset=2", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
    
    @pytest.mark.asyncio
    async def test_get_trade_statistics(self, client: AsyncClient, auth_headers: dict):
        """Test getting trade statistics."""
        # Create some executed trades
        trades_data = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": "0.01",
                "price": "55000.00",
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "sell",
                "quantity": "0.5",
                "price": "2000.00",
                "exchange": "binance"
            }
        ]
        
        trade_ids = []
        for trade_data in trades_data:
            create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
            trade_id = create_response.json()["id"]
            trade_ids.append(trade_id)
            
            # Execute the trade
            await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        
        response = await client.get("/trades/statistics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_trades" in data
        assert "total_volume" in data
        assert "buy_trades" in data
        assert "sell_trades" in data
        assert "executed_trades" in data
        assert "pending_trades" in data
        assert "cancelled_trades" in data
        
        assert data["total_trades"] >= 2
        assert data["executed_trades"] >= 2
        assert float(data["total_volume"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_trade_profit_loss(self, client: AsyncClient, auth_headers: dict):
        """Test getting trade profit/loss calculation."""
        # Create a buy trade
        buy_trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "50000.00",
            "exchange": "binance"
        }
        
        buy_response = await client.post("/trades/", json=buy_trade_data, headers=auth_headers)
        buy_trade_id = buy_response.json()["id"]
        
        # Execute the buy trade
        await client.post(f"/trades/{buy_trade_id}/execute", headers=auth_headers)
        
        # Create a sell trade at higher price
        sell_trade_data = {
            "symbol": "BTCUSDT",
            "side": "sell",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        sell_response = await client.post("/trades/", json=sell_trade_data, headers=auth_headers)
        sell_trade_id = sell_response.json()["id"]
        
        # Execute the sell trade
        await client.post(f"/trades/{sell_trade_id}/execute", headers=auth_headers)
        
        # Get profit/loss for the symbol
        response = await client.get("/trades/profit-loss?symbol=BTCUSDT", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "profit_loss" in data
        assert "profit_loss_percentage" in data
        assert "total_buy_volume" in data
        assert "total_sell_volume" in data
        
        assert data["symbol"] == "BTCUSDT"
        assert float(data["profit_loss"]) > 0  # Should be profitable
        assert float(data["profit_loss_percentage"]) > 0
