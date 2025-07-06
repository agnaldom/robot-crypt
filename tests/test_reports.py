"""
Tests for reports endpoints.
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, timedelta


class TestReportsEndpoints:
    """Test reports endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_portfolio_report_unauthorized(self, client: AsyncClient):
        """Test getting portfolio report without authentication."""
        response = await client.get("/reports/portfolio")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_portfolio_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting portfolio report with no data."""
        response = await client.get("/reports/portfolio", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_value"] == 0.0
        assert data["total_invested"] == 0.0
        assert data["total_profit_loss"] == 0.0
        assert data["total_profit_loss_percentage"] == 0.0
        assert data["positions"] == []
        assert data["performance_over_time"] == []
    
    @pytest.mark.asyncio
    async def test_get_portfolio_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting portfolio report with positions."""
        # Create some portfolio positions first
        positions_data = [
            {
                "symbol": "BTCUSDT",
                "quantity": "0.01",
                "average_price": "55000.00",
                "current_price": "60000.00"
            },
            {
                "symbol": "ETHUSDT",
                "quantity": "0.5",
                "average_price": "2000.00",
                "current_price": "2200.00"
            }
        ]
        
        for position_data in positions_data:
            await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/reports/portfolio", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["total_value"]) > 0
        assert float(data["total_invested"]) > 0
        assert float(data["total_profit_loss"]) > 0  # Should be profitable
        assert len(data["positions"]) == 2
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_get_trades_report_unauthorized(self, client: AsyncClient):
        """Test getting trades report without authentication."""
        response = await client.get("/reports/trades")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_trades_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades report with no data."""
        response = await client.get("/reports/trades", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_trades"] == 0
        assert data["total_volume"] == 0.0
        assert data["buy_trades"] == 0
        assert data["sell_trades"] == 0
        assert data["executed_trades"] == 0
        assert data["pending_trades"] == 0
        assert data["cancelled_trades"] == 0
        assert data["profit_loss"] == 0.0
        assert data["trades"] == []
    
    @pytest.mark.asyncio
    async def test_get_trades_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades report with trades."""
        # Create some trades first
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
        
        response = await client.get("/reports/trades", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_trades"] == 2
        assert data["executed_trades"] == 2
        assert data["buy_trades"] == 1
        assert data["sell_trades"] == 1
        assert float(data["total_volume"]) > 0
        assert len(data["trades"]) == 2
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_get_trades_report_with_date_range(self, client: AsyncClient, auth_headers: dict):
        """Test getting trades report with date range filter."""
        # Create a trade
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        
        # Get report with date range
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = await client.get(
            f"/reports/trades?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_trades"] >= 1
        assert data["executed_trades"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_performance_report_unauthorized(self, client: AsyncClient):
        """Test getting performance report without authentication."""
        response = await client.get("/reports/performance")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_performance_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting performance report with no data."""
        response = await client.get("/reports/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_invested"] == 0.0
        assert data["current_value"] == 0.0
        assert data["profit_loss"] == 0.0
        assert data["profit_loss_percentage"] == 0.0
        assert data["performance_over_time"] == []
        assert data["asset_allocation"] == []
    
    @pytest.mark.asyncio
    async def test_get_performance_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting performance report with portfolio data."""
        # Create some portfolio positions
        positions_data = [
            {
                "symbol": "BTCUSDT",
                "quantity": "0.01",
                "average_price": "50000.00",
                "current_price": "60000.00"
            },
            {
                "symbol": "ETHUSDT",
                "quantity": "0.5",
                "average_price": "2000.00",
                "current_price": "2200.00"
            }
        ]
        
        for position_data in positions_data:
            await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/reports/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["total_invested"]) > 0
        assert float(data["current_value"]) > 0
        assert float(data["profit_loss"]) > 0  # Should be profitable
        assert float(data["profit_loss_percentage"]) > 0
        assert len(data["asset_allocation"]) == 2
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_get_performance_report_with_period(self, client: AsyncClient, auth_headers: dict):
        """Test getting performance report with specific period."""
        # Create portfolio positions
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.01",
            "average_price": "50000.00",
            "current_price": "60000.00"
        }
        
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        # Test different periods
        periods = ["1d", "7d", "30d", "1y"]
        
        for period in periods:
            response = await client.get(f"/reports/performance?period={period}", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "period" in data
            assert data["period"] == period
            assert "total_invested" in data
            assert "current_value" in data
    
    @pytest.mark.asyncio
    async def test_get_alerts_report_unauthorized(self, client: AsyncClient):
        """Test getting alerts report without authentication."""
        response = await client.get("/reports/alerts")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_alerts_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting alerts report with no data."""
        response = await client.get("/reports/alerts", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_alerts"] == 0
        assert data["active_alerts"] == 0
        assert data["triggered_alerts"] == 0
        assert data["price_alerts"] == 0
        assert data["volume_alerts"] == 0
        assert data["percentage_alerts"] == 0
        assert data["alerts"] == []
    
    @pytest.mark.asyncio
    async def test_get_alerts_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting alerts report with alerts."""
        # Create some alerts
        alerts_data = [
            {
                "symbol": "BTCUSDT",
                "alert_type": "price",
                "condition": "above",
                "threshold": "60000.00",
                "message": "BTC above $60k"
            },
            {
                "symbol": "ETHUSDT",
                "alert_type": "volume",
                "condition": "above",
                "threshold": "1000000.00",
                "message": "ETH high volume"
            }
        ]
        
        alert_ids = []
        for alert_data in alerts_data:
            create_response = await client.post("/alerts/", json=alert_data, headers=auth_headers)
            alert_id = create_response.json()["id"]
            alert_ids.append(alert_id)
        
        # Trigger one alert
        await client.post(f"/alerts/{alert_ids[0]}/trigger", headers=auth_headers)
        
        response = await client.get("/reports/alerts", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_alerts"] == 2
        assert data["active_alerts"] == 1
        assert data["triggered_alerts"] == 1
        assert data["price_alerts"] == 1
        assert data["volume_alerts"] == 1
        assert len(data["alerts"]) == 2
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_get_risk_report_unauthorized(self, client: AsyncClient):
        """Test getting risk report without authentication."""
        response = await client.get("/reports/risk")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_risk_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting risk report with no data."""
        response = await client.get("/reports/risk", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["portfolio_value"] == 0.0
        assert data["risk_score"] == 0.0
        assert data["volatility"] == 0.0
        assert data["diversification_score"] == 0.0
        assert data["concentration_risk"] == 0.0
        assert data["risk_recommendations"] == []
    
    @pytest.mark.asyncio
    async def test_get_risk_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting risk report with portfolio data."""
        # Create diversified portfolio positions
        positions_data = [
            {
                "symbol": "BTCUSDT",
                "quantity": "0.01",
                "average_price": "50000.00",
                "current_price": "60000.00"
            },
            {
                "symbol": "ETHUSDT",
                "quantity": "0.5",
                "average_price": "2000.00",
                "current_price": "2200.00"
            },
            {
                "symbol": "ADAUSDT",
                "quantity": "100",
                "average_price": "1.00",
                "current_price": "1.50"
            }
        ]
        
        for position_data in positions_data:
            await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/reports/risk", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["portfolio_value"]) > 0
        assert float(data["risk_score"]) >= 0
        assert float(data["volatility"]) >= 0
        assert float(data["diversification_score"]) >= 0
        assert float(data["concentration_risk"]) >= 0
        assert isinstance(data["risk_recommendations"], list)
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_get_summary_report_unauthorized(self, client: AsyncClient):
        """Test getting summary report without authentication."""
        response = await client.get("/reports/summary")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_summary_report_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting summary report with no data."""
        response = await client.get("/reports/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["portfolio_value"] == 0.0
        assert data["total_trades"] == 0
        assert data["total_alerts"] == 0
        assert data["profit_loss"] == 0.0
        assert data["profit_loss_percentage"] == 0.0
        assert data["active_positions"] == 0
        assert data["recent_trades"] == []
        assert data["recent_alerts"] == []
    
    @pytest.mark.asyncio
    async def test_get_summary_report_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test getting summary report with comprehensive data."""
        # Create portfolio positions
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.01",
            "average_price": "50000.00",
            "current_price": "60000.00"
        }
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        # Create trades
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        
        # Create alerts
        alert_data = {
            "symbol": "BTCUSDT",
            "alert_type": "price",
            "condition": "above",
            "threshold": "60000.00",
            "message": "BTC above $60k"
        }
        await client.post("/alerts/", json=alert_data, headers=auth_headers)
        
        response = await client.get("/reports/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert float(data["portfolio_value"]) > 0
        assert data["total_trades"] >= 1
        assert data["total_alerts"] >= 1
        assert float(data["profit_loss"]) > 0
        assert float(data["profit_loss_percentage"]) > 0
        assert data["active_positions"] >= 1
        assert len(data["recent_trades"]) >= 1
        assert len(data["recent_alerts"]) >= 1
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_export_report_unauthorized(self, client: AsyncClient):
        """Test exporting report without authentication."""
        response = await client.get("/reports/export/portfolio")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_export_portfolio_report_csv(self, client: AsyncClient, auth_headers: dict):
        """Test exporting portfolio report as CSV."""
        # Create some portfolio positions
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.01",
            "average_price": "50000.00",
            "current_price": "60000.00"
        }
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/reports/export/portfolio?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check CSV content
        csv_content = response.text
        assert "symbol" in csv_content.lower()
        assert "quantity" in csv_content.lower()
        assert "BTCUSDT" in csv_content
    
    @pytest.mark.asyncio
    async def test_export_portfolio_report_pdf(self, client: AsyncClient, auth_headers: dict):
        """Test exporting portfolio report as PDF."""
        # Create some portfolio positions
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.01",
            "average_price": "50000.00",
            "current_price": "60000.00"
        }
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        response = await client.get("/reports/export/portfolio?format=pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check PDF content (basic check)
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")
    
    @pytest.mark.asyncio
    async def test_export_trades_report_csv(self, client: AsyncClient, auth_headers: dict):
        """Test exporting trades report as CSV."""
        # Create some trades
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "price": "55000.00",
            "exchange": "binance"
        }
        create_response = await client.post("/trades/", json=trade_data, headers=auth_headers)
        trade_id = create_response.json()["id"]
        await client.post(f"/trades/{trade_id}/execute", headers=auth_headers)
        
        response = await client.get("/reports/export/trades?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check CSV content
        csv_content = response.text
        assert "symbol" in csv_content.lower()
        assert "side" in csv_content.lower()
        assert "BTCUSDT" in csv_content
    
    @pytest.mark.asyncio
    async def test_export_invalid_format(self, client: AsyncClient, auth_headers: dict):
        """Test exporting report with invalid format."""
        response = await client.get("/reports/export/portfolio?format=invalid", headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_export_invalid_report_type(self, client: AsyncClient, auth_headers: dict):
        """Test exporting invalid report type."""
        response = await client.get("/reports/export/invalid?format=csv", headers=auth_headers)
        assert response.status_code == 404
        assert "report type not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_custom_report(self, client: AsyncClient, auth_headers: dict):
        """Test generating custom report with specific parameters."""
        # Create some test data
        position_data = {
            "symbol": "BTCUSDT",
            "quantity": "0.01",
            "average_price": "50000.00",
            "current_price": "60000.00"
        }
        await client.post("/portfolio/positions", json=position_data, headers=auth_headers)
        
        # Generate custom report
        custom_report_data = {
            "report_type": "custom",
            "include_portfolio": True,
            "include_trades": True,
            "include_alerts": False,
            "date_range": {
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            },
            "symbols": ["BTCUSDT"],
            "metrics": ["profit_loss", "portfolio_value", "asset_allocation"]
        }
        
        response = await client.post("/reports/custom", json=custom_report_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["report_type"] == "custom"
        assert "portfolio_data" in data
        assert "trades_data" in data
        assert "alerts_data" not in data  # Should be excluded
        assert "metrics" in data
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_schedule_report_generation(self, client: AsyncClient, auth_headers: dict):
        """Test scheduling automatic report generation."""
        schedule_data = {
            "report_type": "portfolio",
            "frequency": "daily",
            "time": "09:00",
            "format": "pdf",
            "email_recipients": ["user@example.com"],
            "enabled": True
        }
        
        response = await client.post("/reports/schedule", json=schedule_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["report_type"] == "portfolio"
        assert data["frequency"] == "daily"
        assert data["format"] == "pdf"
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_scheduled_reports(self, client: AsyncClient, auth_headers: dict):
        """Test getting list of scheduled reports."""
        # Create a scheduled report first
        schedule_data = {
            "report_type": "trades",
            "frequency": "weekly",
            "time": "08:00",
            "format": "csv",
            "email_recipients": ["user@example.com"],
            "enabled": True
        }
        await client.post("/reports/schedule", json=schedule_data, headers=auth_headers)
        
        response = await client.get("/reports/schedule", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        schedule = data[0]
        assert "id" in schedule
        assert "report_type" in schedule
        assert "frequency" in schedule
        assert "enabled" in schedule
    
    @pytest.mark.asyncio
    async def test_update_scheduled_report(self, client: AsyncClient, auth_headers: dict):
        """Test updating a scheduled report."""
        # Create a scheduled report
        schedule_data = {
            "report_type": "portfolio",
            "frequency": "daily",
            "time": "09:00",
            "format": "pdf",
            "email_recipients": ["user@example.com"],
            "enabled": True
        }
        create_response = await client.post("/reports/schedule", json=schedule_data, headers=auth_headers)
        schedule_id = create_response.json()["id"]
        
        # Update the schedule
        update_data = {
            "frequency": "weekly",
            "time": "10:00",
            "enabled": False
        }
        
        response = await client.put(f"/reports/schedule/{schedule_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["frequency"] == "weekly"
        assert data["time"] == "10:00"
        assert data["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_delete_scheduled_report(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a scheduled report."""
        # Create a scheduled report
        schedule_data = {
            "report_type": "portfolio",
            "frequency": "daily",
            "time": "09:00",
            "format": "pdf",
            "email_recipients": ["user@example.com"],
            "enabled": True
        }
        create_response = await client.post("/reports/schedule", json=schedule_data, headers=auth_headers)
        schedule_id = create_response.json()["id"]
        
        # Delete the schedule
        response = await client.delete(f"/reports/schedule/{schedule_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/reports/schedule/{schedule_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_report_history(self, client: AsyncClient, auth_headers: dict):
        """Test getting report generation history."""
        # Generate a report to create history
        await client.get("/reports/portfolio", headers=auth_headers)
        
        response = await client.get("/reports/history", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            history_entry = data[0]
            assert "id" in history_entry
            assert "report_type" in history_entry
            assert "generated_at" in history_entry
            assert "status" in history_entry
    
    @pytest.mark.asyncio
    async def test_get_report_metrics(self, client: AsyncClient, auth_headers: dict):
        """Test getting report generation metrics."""
        response = await client.get("/reports/metrics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_reports_generated" in data
        assert "reports_by_type" in data
        assert "reports_by_format" in data
        assert "average_generation_time" in data
        assert "most_requested_report" in data
        assert "generated_at" in data
        
        # Verify data types
        assert isinstance(data["total_reports_generated"], int)
        assert isinstance(data["reports_by_type"], dict)
        assert isinstance(data["reports_by_format"], dict)
        assert isinstance(data["average_generation_time"], (int, float))
