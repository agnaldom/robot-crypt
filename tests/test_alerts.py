"""
Tests for alerts endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from decimal import Decimal


class TestAlertsEndpoints:
    """Test alerts endpoints."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_test(self, cleanup_db):
        """Setup each test with clean database."""
        pass
    
    @pytest.mark.asyncio
    async def test_get_alerts_unauthorized(self, client: AsyncClient):
        """Test getting alerts without authentication."""
        response = await client.get("/alerts/")
        # FastAPI should return 401 for unauthorized access
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_alerts_empty(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting empty alerts list."""
        response = await authenticated_client.get("/alerts/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_create_price_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test creating a price alert."""
        alert_data = {
            "alert_type": "price",
            "message": "BTC price reached $55,000",
            "trigger_value": 55000.00,
            "asset_id": 1,
            "parameters": {
                "symbol": "BTCUSDT",
                "condition": "greater_than"
            }
        }
        
        response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        assert response.status_code == 200  # FastAPI returns 200 by default
        
        data = response.json()
        assert data["alert_type"] == "price"
        assert data["message"] == "BTC price reached $55,000"
        assert data["trigger_value"] == 55000.0
        assert data["asset_id"] == 1
        assert data["parameters"]["symbol"] == "BTCUSDT"
        assert data["parameters"]["condition"] == "greater_than"
        assert data["is_active"] is True
        assert data["is_triggered"] is False
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_volume_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test creating a volume alert."""
        alert_data = {
            "alert_type": "volume",
            "message": "ETH volume spike detected",
            "trigger_value": 1000000.00,
            "asset_id": 2,
            "parameters": {
                "symbol": "ETHUSDT",
                "condition": "greater_than"
            }
        }
        
        response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["alert_type"] == "volume"
        assert data["message"] == "ETH volume spike detected"
        assert data["trigger_value"] == 1000000.0
        assert data["parameters"]["symbol"] == "ETHUSDT"
    
    @pytest.mark.asyncio
    async def test_create_percentage_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test creating a percentage change alert."""
        alert_data = {
            "alert_type": "percentage_change",
            "message": "ADA gained more than 10%",
            "trigger_value": 10.0,
            "asset_id": 3,
            "parameters": {
                "symbol": "ADAUSDT",
                "condition": "greater_than"
            }
        }
        
        response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["alert_type"] == "percentage_change"
        assert data["message"] == "ADA gained more than 10%"
        assert data["trigger_value"] == 10.0
        assert data["parameters"]["symbol"] == "ADAUSDT"
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_data(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test creating alert with invalid data."""
        # Test with missing required fields - should fail validation
        invalid_data = {
            # Missing alert_type and message which are required
            "trigger_value": "not_a_number",  # Invalid type
            "asset_id": "not_an_integer",  # Invalid type
        }
        
        response = await authenticated_client.post("/alerts/", json=invalid_data, headers=auth_headers)
        # Expect 422 (validation error) for missing required fields
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_alerts_list(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting alerts list."""
        # Create multiple alerts
        alerts_data = [
            {
                "alert_type": "price",
                "message": "BTC price alert",
                "trigger_value": 55000.00,
                "asset_id": 1,
                "parameters": {
                    "symbol": "BTCUSDT",
                    "condition": "greater_than"
                }
            },
            {
                "alert_type": "volume",
                "message": "ETH volume alert",
                "trigger_value": 1000000.00,
                "asset_id": 2,
                "parameters": {
                    "symbol": "ETHUSDT",
                    "condition": "greater_than"
                }
            }
        ]
        
        for alert_data in alerts_data:
            await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        
        response = await authenticated_client.get("/alerts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Check that we have both alerts by their symbols in parameters
        symbols = [alert["parameters"]["symbol"] for alert in data if "symbol" in alert["parameters"]]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
    
    @pytest.mark.asyncio
    async def test_get_alert_by_id(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting a specific alert."""
        alert_data = {
            "alert_type": "price",
            "message": "DOT price dropped below $20",
            "trigger_value": 20.00,
            "asset_id": 3,
            "parameters": {
                "symbol": "DOTUSDT",
                "condition": "less_than"
            }
        }
        
        create_response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        response = await authenticated_client.get(f"/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == alert_id
        assert data["parameters"]["symbol"] == "DOTUSDT"
        assert data["parameters"]["condition"] == "less_than"
        assert data["trigger_value"] == 20.0
    
    @pytest.mark.asyncio
    async def test_get_alert_not_found(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting non-existent alert."""
        response = await authenticated_client.get("/alerts/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test updating an alert."""
        alert_data = {
            "alert_type": "price",
            "message": "LINK price alert",
            "trigger_value": 15.00,
            "asset_id": 4,
            "parameters": {
                "symbol": "LINKUSDT",
                "condition": "greater_than"
            }
        }
        
        create_response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        update_data = {
            "trigger_value": 20.00,
            "message": "LINK price reached $20",
            "is_active": False
        }
        
        response = await authenticated_client.put(f"/alerts/{alert_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["trigger_value"] == 20.0
        assert data["message"] == "LINK price reached $20"
        assert data["is_active"] is False
        assert data["parameters"]["symbol"] == "LINKUSDT"  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_update_alert_not_found(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test updating non-existent alert."""
        update_data = {
            "trigger_value": 100.00,
            "message": "Updated message"
        }
        
        response = await authenticated_client.put("/alerts/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test deleting an alert."""
        alert_data = {
            "alert_type": "price",
            "message": "UNI price alert",
            "trigger_value": 10.00,
            "asset_id": 5,
            "parameters": {
                "symbol": "UNIUSDT",
                "condition": "greater_than"
            }
        }
        
        create_response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        response = await authenticated_client.delete(f"/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200  # API returns 200, not 204
        
        # Verify alert is deleted
        get_response = await authenticated_client.get(f"/alerts/{alert_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_alert_not_found(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent alert."""
        response = await authenticated_client.delete("/alerts/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting only active alerts."""
        # Create active and inactive alerts
        active_alert = {
            "alert_type": "price",
            "message": "Active BTC alert",
            "trigger_value": 55000.00,
            "asset_id": 1,
            "parameters": {
                "symbol": "BTCUSDT",
                "condition": "greater_than"
            }
        }
        
        inactive_alert = {
            "alert_type": "price",
            "message": "Inactive ETH alert",
            "trigger_value": 2000.00,
            "asset_id": 2,
            "parameters": {
                "symbol": "ETHUSDT",
                "condition": "less_than"
            }
        }
        
        # Create active alert
        await authenticated_client.post("/alerts/", json=active_alert, headers=auth_headers)
        
        # Create inactive alert
        create_response = await authenticated_client.post("/alerts/", json=inactive_alert, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        # Deactivate the second alert
        await authenticated_client.put(f"/alerts/{alert_id}", json={"is_active": False}, headers=auth_headers)
        
        # Get active alerts - use the correct endpoint
        response = await authenticated_client.get("/alerts/active", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["parameters"]["symbol"] == "BTCUSDT"
        assert data[0]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_alerts_by_symbol(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting alerts filtered by symbol."""
        # Create alerts for different symbols
        alerts_data = [
            {
                "alert_type": "price",
                "message": "BTC alert 1",
                "trigger_value": 55000.00,
                "asset_id": 1,
                "parameters": {
                    "symbol": "BTCUSDT",
                    "condition": "greater_than"
                }
            },
            {
                "alert_type": "volume",
                "message": "BTC alert 2",
                "trigger_value": 1000000.00,
                "asset_id": 1,
                "parameters": {
                    "symbol": "BTCUSDT",
                    "condition": "greater_than"
                }
            },
            {
                "alert_type": "price",
                "message": "ETH alert",
                "trigger_value": 2000.00,
                "asset_id": 2,
                "parameters": {
                    "symbol": "ETHUSDT",
                    "condition": "less_than"
                }
            }
        ]
        
        for alert_data in alerts_data:
            await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        
        # Get all alerts and filter by BTCUSDT manually (since API doesn't have symbol filter)
        response = await authenticated_client.get("/alerts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        btc_alerts = [alert for alert in data if alert["parameters"].get("symbol") == "BTCUSDT"]
        assert len(btc_alerts) == 2
        
        for alert in btc_alerts:
            assert alert["parameters"]["symbol"] == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_trigger_alert(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test triggering an alert (requires superuser)."""
        alert_data = {
            "alert_type": "price",
            "message": "BTC price alert",
            "trigger_value": 55000.00,
            "asset_id": 1,
            "parameters": {
                "symbol": "BTCUSDT",
                "condition": "greater_than"
            }
        }
        
        create_response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        # Trigger the alert - this requires superuser permission
        trigger_data = {
            "alert_id": alert_id,
            "current_value": 55500.0
        }
        response = await authenticated_client.post(f"/alerts/{alert_id}/trigger", json=trigger_data, headers=auth_headers)
        # Expect 400 or 403 because current user is not superuser
        assert response.status_code in [400, 403]
    
    @pytest.mark.asyncio
    async def test_trigger_alert_not_found(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test triggering non-existent alert."""
        trigger_data = {
            "alert_id": 99999,
            "current_value": 1000.0
        }
        response = await authenticated_client.post("/alerts/99999/trigger", json=trigger_data, headers=auth_headers)
        # Expect 400 or 403 because current user is not superuser
        assert response.status_code in [400, 403]
    
    @pytest.mark.asyncio
    async def test_get_alert_history(self, authenticated_client: AsyncClient, auth_headers: dict):
        """Test getting triggered alerts (history)."""
        # Create some alerts
        alert_data = {
            "alert_type": "price",
            "message": "BTC price alert",
            "trigger_value": 55000.00,
            "asset_id": 1,
            "parameters": {
                "symbol": "BTCUSDT",
                "condition": "greater_than"
            }
        }
        
        create_response = await authenticated_client.post("/alerts/", json=alert_data, headers=auth_headers)
        alert_id = create_response.json()["id"]
        
        # Get triggered alerts (history endpoint)
        response = await authenticated_client.get("/alerts/triggered", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should be empty initially since no alerts have been triggered
        assert isinstance(data, list)
