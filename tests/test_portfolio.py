import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.portfolio import (
    PortfolioSnapshot,
    PortfolioAsset,
    PortfolioTransaction,
    TransactionType,
    RiskLevel
)
from src.schemas.portfolio import (
    PortfolioSnapshotCreate,
    PortfolioSnapshotUpdate,
    PortfolioAssetCreate,
    PortfolioAssetUpdate,
    PortfolioTransactionCreate,
    PortfolioTransactionUpdate
)
from src.services.portfolio_service import PortfolioService
from src.services.portfolio_position_service import PortfolioPositionService


class TestPortfolioModels:
    """Test portfolio data models and their validation"""
    
    def test_portfolio_snapshot_creation(self):
        """Test creating a portfolio snapshot with valid data"""
        snapshot = PortfolioSnapshot(
            user_id=1,
            current_market_value=Decimal("10000.00"),
            total_invested_value=Decimal("8000.00"),
            total_profit_loss=Decimal("2000.00"),
            profit_loss_percentage=Decimal("25.00"),
            risk_level=RiskLevel.MODERATE,
            value_at_risk=Decimal("500.00"),
            volatility=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10"),
            created_at=datetime.utcnow()
        )
        
        assert snapshot.user_id == 1
        assert snapshot.current_market_value == Decimal("10000.00")
        assert snapshot.total_invested_value == Decimal("8000.00")
        assert snapshot.total_profit_loss == Decimal("2000.00")
        assert snapshot.profit_loss_percentage == Decimal("25.00")
        assert snapshot.risk_level == RiskLevel.MODERATE
        assert snapshot.value_at_risk == Decimal("500.00")
        assert isinstance(snapshot.created_at, datetime)
    
    def test_portfolio_asset_creation(self):
        """Test creating a portfolio asset with valid data"""
        asset = PortfolioAsset(
            snapshot_id=1,
            asset_id=1,
            symbol="BTC",
            name="Bitcoin",
            quantity=Decimal("0.5"),
            average_price=Decimal("50000.00"),
            current_price=Decimal("60000.00"),
            current_value=Decimal("30000.00"),
            profit_loss=Decimal("5000.00"),
            profit_loss_percentage=Decimal("20.00"),
            allocation_percentage=Decimal("60.00"),
            last_updated=datetime.utcnow()
        )
        
        assert asset.snapshot_id == 1
        assert asset.asset_id == 1
        assert asset.symbol == "BTC"
        assert asset.name == "Bitcoin"
        assert asset.quantity == Decimal("0.5")
        assert asset.average_price == Decimal("50000.00")
        assert asset.current_price == Decimal("60000.00")
        assert asset.current_value == Decimal("30000.00")
        assert asset.profit_loss == Decimal("5000.00")
        assert asset.profit_loss_percentage == Decimal("20.00")
        assert asset.allocation_percentage == Decimal("60.00")
    
    def test_portfolio_transaction_creation(self):
        """Test creating a portfolio transaction with valid data"""
        transaction = PortfolioTransaction(
            user_id=1,
            asset_id=1,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.1"),
            price=Decimal("50000.00"),
            total_value=Decimal("5000.00"),
            fee=Decimal("10.00"),
            realized_profit_loss=Decimal("0.00"),
            profit_loss_percentage=Decimal("0.00"),
            notes="Initial BTC purchase",
            metadata={"exchange": "binance"},
            external_id="ext_12345",
            external_source="binance_api",
            executed_at=datetime.utcnow()
        )
        
        assert transaction.user_id == 1
        assert transaction.asset_id == 1
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.quantity == Decimal("0.1")
        assert transaction.price == Decimal("50000.00")
        assert transaction.total_value == Decimal("5000.00")
        assert transaction.fee == Decimal("10.00")
        assert transaction.notes == "Initial BTC purchase"
        assert transaction.metadata == {"exchange": "binance"}
        assert transaction.external_id == "ext_12345"
        assert transaction.external_source == "binance_api"
    
    def test_transaction_type_enum(self):
        """Test transaction type enumeration"""
        assert TransactionType.BUY == "buy"
        assert TransactionType.SELL == "sell"
        assert TransactionType.TRANSFER_IN == "transfer_in"
        assert TransactionType.TRANSFER_OUT == "transfer_out"
    
    def test_risk_level_enum(self):
        """Test risk level enumeration"""
        assert RiskLevel.CONSERVATIVE == "conservative"
        assert RiskLevel.MODERATE == "moderate"
        assert RiskLevel.AGGRESSIVE == "aggressive"
        assert RiskLevel.VERY_HIGH == "very_high"


class TestPortfolioSchemas:
    """Test portfolio Pydantic schemas and validation"""
    
    def test_portfolio_snapshot_create_schema(self):
        """Test portfolio snapshot creation schema"""
        snapshot_data = {
            "user_id": 1,
            "current_market_value": "10000.00",
            "total_invested_value": "8000.00",
            "total_profit_loss": "2000.00",
            "profit_loss_percentage": "25.00",
            "risk_level": "moderate",
            "value_at_risk": "500.00",
            "volatility": "0.15",
            "sharpe_ratio": "1.5",
            "max_drawdown": "0.10"
        }
        
        schema = PortfolioSnapshotCreate(**snapshot_data)
        
        assert schema.user_id == 1
        assert schema.current_market_value == Decimal("10000.00")
        assert schema.total_invested_value == Decimal("8000.00")
        assert schema.total_profit_loss == Decimal("2000.00")
        assert schema.profit_loss_percentage == Decimal("25.00")
        assert schema.risk_level == "moderate"
        assert schema.value_at_risk == Decimal("500.00")
        assert schema.volatility == Decimal("0.15")
        assert schema.sharpe_ratio == Decimal("1.5")
        assert schema.max_drawdown == Decimal("0.10")
    
    def test_portfolio_asset_create_schema(self):
        """Test portfolio asset creation schema"""
        asset_data = {
            "snapshot_id": 1,
            "asset_id": 1,
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": "0.5",
            "average_price": "50000.00",
            "current_price": "60000.00",
            "current_value": "30000.00",
            "profit_loss": "5000.00",
            "profit_loss_percentage": "20.00",
            "allocation_percentage": "60.00"
        }
        
        schema = PortfolioAssetCreate(**asset_data)
        
        assert schema.snapshot_id == 1
        assert schema.asset_id == 1
        assert schema.symbol == "BTC"
        assert schema.name == "Bitcoin"
        assert schema.quantity == Decimal("0.5")
        assert schema.average_price == Decimal("50000.00")
        assert schema.current_price == Decimal("60000.00")
        assert schema.current_value == Decimal("30000.00")
        assert schema.profit_loss == Decimal("5000.00")
        assert schema.profit_loss_percentage == Decimal("20.00")
        assert schema.allocation_percentage == Decimal("60.00")
    
    def test_portfolio_transaction_create_schema(self):
        """Test portfolio transaction creation schema"""
        transaction_data = {
            "user_id": 1,
            "asset_id": 1,
            "transaction_type": "buy",
            "quantity": "0.1",
            "price": "50000.00",
            "total_value": "5000.00",
            "fee": "10.00",
            "realized_profit_loss": "0.00",
            "profit_loss_percentage": "0.00",
            "notes": "Initial BTC purchase",
            "metadata": {"exchange": "binance"},
            "external_id": "ext_12345",
            "external_source": "binance_api",
            "executed_at": datetime.utcnow()
        }
        
        schema = PortfolioTransactionCreate(**transaction_data)
        
        assert schema.user_id == 1
        assert schema.asset_id == 1
        assert schema.transaction_type == "buy"
        assert schema.quantity == Decimal("0.1")
        assert schema.price == Decimal("50000.00")
        assert schema.total_value == Decimal("5000.00")
        assert schema.fee == Decimal("10.00")
        assert schema.realized_profit_loss == Decimal("0.00")
        assert schema.profit_loss_percentage == Decimal("0.00")
        assert schema.notes == "Initial BTC purchase"
        assert schema.metadata == {"exchange": "binance"}
        assert schema.external_id == "ext_12345"
        assert schema.external_source == "binance_api"
        assert isinstance(schema.executed_at, datetime)


@pytest.mark.asyncio
class TestPortfolioService:
    """Test portfolio service functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def portfolio_service(self, mock_db_session):
        """Create portfolio service instance with mocked database"""
        return PortfolioService(mock_db_session)
    
    async def test_create_portfolio_snapshot(self, portfolio_service, mock_db_session):
        """Test creating a new portfolio snapshot"""
        # Mock data
        snapshot_data = PortfolioSnapshotCreate(
            user_id=1,
            current_market_value=Decimal("10000.00"),
            total_invested_value=Decimal("8000.00"),
            total_profit_loss=Decimal("2000.00"),
            profit_loss_percentage=Decimal("25.00"),
            risk_level="moderate",
            value_at_risk=Decimal("500.00"),
            volatility=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10")
        )
        
        # Mock return value
        mock_snapshot = PortfolioSnapshot(
            id=1,
            user_id=1,
            current_market_value=Decimal("10000.00"),
            total_invested_value=Decimal("8000.00"),
            total_profit_loss=Decimal("2000.00"),
            profit_loss_percentage=Decimal("25.00"),
            risk_level=RiskLevel.MODERATE,
            value_at_risk=Decimal("500.00"),
            volatility=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10"),
            created_at=datetime.utcnow()
        )
        
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock(return_value=mock_snapshot)
        
        # Call the service method
        result = await portfolio_service.create_portfolio_snapshot(snapshot_data)
        
        # Assertions
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result.user_id == 1
        assert result.current_market_value == Decimal("10000.00")
        assert result.total_invested_value == Decimal("8000.00")
        assert result.total_profit_loss == Decimal("2000.00")
    
    async def test_get_latest_portfolio_snapshot(self, portfolio_service, mock_db_session):
        """Test getting the latest portfolio snapshot"""
        # Mock return value
        mock_snapshot = PortfolioSnapshot(
            id=1,
            user_id=1,
            current_market_value=Decimal("10000.00"),
            total_invested_value=Decimal("8000.00"),
            total_profit_loss=Decimal("2000.00"),
            profit_loss_percentage=Decimal("25.00"),
            risk_level=RiskLevel.MODERATE,
            value_at_risk=Decimal("500.00"),
            volatility=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10"),
            created_at=datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_snapshot
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Call the service method
        result = await portfolio_service.get_latest_portfolio_snapshot(1)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        mock_result.scalar_one_or_none.assert_called_once()
        assert result == mock_snapshot
        assert result.id == 1
        assert result.user_id == 1
        assert result.current_market_value == Decimal("10000.00")
    
    async def test_get_portfolio_snapshots(self, portfolio_service, mock_db_session):
        """Test getting portfolio snapshots with pagination"""
        # Mock return values
        mock_snapshots = [
            PortfolioSnapshot(
                id=1,
                user_id=1,
                current_market_value=Decimal("10000.00"),
                total_invested_value=Decimal("8000.00"),
                total_profit_loss=Decimal("2000.00"),
                profit_loss_percentage=Decimal("25.00"),
                risk_level=RiskLevel.MODERATE,
                value_at_risk=Decimal("500.00"),
                volatility=Decimal("0.15"),
                sharpe_ratio=Decimal("1.5"),
                max_drawdown=Decimal("0.10"),
                created_at=datetime.utcnow()
            ),
            PortfolioSnapshot(
                id=2,
                user_id=1,
                current_market_value=Decimal("9500.00"),
                total_invested_value=Decimal("8000.00"),
                total_profit_loss=Decimal("1500.00"),
                profit_loss_percentage=Decimal("18.75"),
                risk_level=RiskLevel.MODERATE,
                value_at_risk=Decimal("475.00"),
                volatility=Decimal("0.12"),
                sharpe_ratio=Decimal("1.2"),
                max_drawdown=Decimal("0.08"),
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_snapshots
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Call the service method
        result = await portfolio_service.get_portfolio_snapshots(1, 0, 10)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        mock_result.scalars.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[0].current_market_value == Decimal("10000.00")
        assert result[1].current_market_value == Decimal("9500.00")
    
    async def test_create_portfolio_transaction(self, portfolio_service, mock_db_session):
        """Test creating a new portfolio transaction"""
        # Mock data
        transaction_data = PortfolioTransactionCreate(
            user_id=1,
            asset_id=1,
            transaction_type="buy",
            quantity=Decimal("0.1"),
            price=Decimal("50000.00"),
            total_value=Decimal("5000.00"),
            fee=Decimal("10.00"),
            realized_profit_loss=Decimal("0.00"),
            profit_loss_percentage=Decimal("0.00"),
            notes="Initial BTC purchase",
            metadata={"exchange": "binance"},
            external_id="ext_12345",
            external_source="binance_api",
            executed_at=datetime.utcnow()
        )
        
        # Mock return value
        mock_transaction = PortfolioTransaction(
            id=1,
            user_id=1,
            asset_id=1,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.1"),
            price=Decimal("50000.00"),
            total_value=Decimal("5000.00"),
            fee=Decimal("10.00"),
            realized_profit_loss=Decimal("0.00"),
            profit_loss_percentage=Decimal("0.00"),
            notes="Initial BTC purchase",
            metadata={"exchange": "binance"},
            external_id="ext_12345",
            external_source="binance_api",
            executed_at=datetime.utcnow()
        )
        
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock(return_value=mock_transaction)
        
        # Call the service method
        result = await portfolio_service.create_portfolio_transaction(transaction_data)
        
        # Assertions
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result.user_id == 1
        assert result.asset_id == 1
        assert result.transaction_type == TransactionType.BUY
        assert result.quantity == Decimal("0.1")
        assert result.price == Decimal("50000.00")
        assert result.total_value == Decimal("5000.00")
        assert result.fee == Decimal("10.00")
        assert result.notes == "Initial BTC purchase"
        assert result.metadata == {"exchange": "binance"}
        assert result.external_id == "ext_12345"
        assert result.external_source == "binance_api"
    
    async def test_get_portfolio_summary(self, portfolio_service, mock_db_session):
        """Test getting portfolio summary"""
        # Mock latest snapshot
        mock_snapshot = PortfolioSnapshot(
            id=1,
            user_id=1,
            current_market_value=Decimal("10000.00"),
            total_invested_value=Decimal("8000.00"),
            total_profit_loss=Decimal("2000.00"),
            profit_loss_percentage=Decimal("25.00"),
            risk_level=RiskLevel.MODERATE,
            value_at_risk=Decimal("500.00"),
            volatility=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10"),
            created_at=datetime.utcnow()
        )
        
        # Mock assets
        mock_assets = [
            PortfolioAsset(
                id=1,
                snapshot_id=1,
                asset_id=1,
                symbol="BTC",
                name="Bitcoin",
                quantity=Decimal("0.5"),
                average_price=Decimal("50000.00"),
                current_price=Decimal("60000.00"),
                current_value=Decimal("30000.00"),
                profit_loss=Decimal("5000.00"),
                profit_loss_percentage=Decimal("20.00"),
                allocation_percentage=Decimal("60.00"),
                last_updated=datetime.utcnow()
            )
        ]
        
        # Mock transactions
        mock_transactions = [
            PortfolioTransaction(
                id=1,
                user_id=1,
                asset_id=1,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("0.1"),
                price=Decimal("50000.00"),
                total_value=Decimal("5000.00"),
                fee=Decimal("10.00"),
                realized_profit_loss=Decimal("0.00"),
                profit_loss_percentage=Decimal("0.00"),
                notes="Initial BTC purchase",
                metadata={"exchange": "binance"},
                external_id="ext_12345",
                external_source="binance_api",
                executed_at=datetime.utcnow()
            )
        ]
        
        # Mock database calls
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_snapshot
        mock_result.scalars.return_value.all.return_value = mock_assets
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock service methods
        portfolio_service.get_latest_portfolio_snapshot = AsyncMock(return_value=mock_snapshot)
        portfolio_service.get_portfolio_snapshots = AsyncMock(return_value=[mock_snapshot])
        portfolio_service.get_portfolio_transactions = AsyncMock(return_value=mock_transactions)
        
        # Call the service method
        result = await portfolio_service.get_portfolio_summary(1, 30)
        
        # Assertions
        assert result["status"] == "success"
        assert result["data"]["portfolio_value"] == Decimal("10000.00")
        assert result["data"]["total_invested"] == Decimal("8000.00")
        assert result["data"]["total_profit_loss"] == Decimal("2000.00")
        assert result["data"]["profit_loss_percentage"] == Decimal("25.00")
        assert result["data"]["risk_level"] == RiskLevel.MODERATE
        assert result["data"]["value_at_risk"] == Decimal("500.00")
        assert result["data"]["assets_count"] == 1
        assert "assets_distribution" in result["data"]
        assert "recent_transactions" in result["data"]
        assert len(result["data"]["recent_transactions"]) == 1
    
    async def test_get_portfolio_summary_empty(self, portfolio_service, mock_db_session):
        """Test getting portfolio summary when no data exists"""
        # Mock empty result
        portfolio_service.get_latest_portfolio_snapshot = AsyncMock(return_value=None)
        
        # Call the service method
        result = await portfolio_service.get_portfolio_summary(1, 30)
        
        # Assertions
        assert result["status"] == "empty"
        assert result["message"] == "No portfolio data available"
        assert result["data"] == {}
    
    async def test_get_portfolio_performance(self, portfolio_service, mock_db_session):
        """Test getting portfolio performance metrics"""
        # Mock snapshots
        mock_snapshots = [
            PortfolioSnapshot(
                id=1,
                user_id=1,
                current_market_value=Decimal("10000.00"),
                total_invested_value=Decimal("8000.00"),
                total_profit_loss=Decimal("2000.00"),
                profit_loss_percentage=Decimal("25.00"),
                risk_level=RiskLevel.MODERATE,
                value_at_risk=Decimal("500.00"),
                volatility=Decimal("0.15"),
                sharpe_ratio=Decimal("1.5"),
                max_drawdown=Decimal("0.10"),
                created_at=datetime.utcnow()
            ),
            PortfolioSnapshot(
                id=2,
                user_id=1,
                current_market_value=Decimal("9000.00"),
                total_invested_value=Decimal("8000.00"),
                total_profit_loss=Decimal("1000.00"),
                profit_loss_percentage=Decimal("12.50"),
                risk_level=RiskLevel.MODERATE,
                value_at_risk=Decimal("450.00"),
                volatility=Decimal("0.12"),
                sharpe_ratio=Decimal("1.2"),
                max_drawdown=Decimal("0.08"),
                created_at=datetime.utcnow() - timedelta(days=30)
            )
        ]
        
        # Mock service method
        portfolio_service.get_portfolio_snapshots = AsyncMock(return_value=mock_snapshots)
        
        # Call the service method
        result = await portfolio_service.get_portfolio_performance(1, "month")
        
        # Assertions
        assert result["status"] == "success"
        assert result["data"]["period"] == "month"
        assert "performance_history" in result["data"]
        assert "metrics" in result["data"]
        assert len(result["data"]["performance_history"]) == 2
        assert result["data"]["metrics"]["starting_value"] == Decimal("9000.00")
        assert result["data"]["metrics"]["ending_value"] == Decimal("10000.00")
        assert result["data"]["metrics"]["absolute_return"] == Decimal("1000.00")
        # Calculate expected percentage return: (1000/9000)*100 ≈ 11.111...
        expected_percentage = Decimal("1000") / Decimal("9000") * Decimal("100")
        assert result["data"]["metrics"]["percentage_return"] == expected_percentage
    
    async def test_update_portfolio_transaction(self, portfolio_service, mock_db_session):
        """Test updating a portfolio transaction"""
        # Mock existing transaction
        mock_transaction = PortfolioTransaction(
            id=1,
            user_id=1,
            asset_id=1,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.1"),
            price=Decimal("50000.00"),
            total_value=Decimal("5000.00"),
            fee=Decimal("10.00"),
            realized_profit_loss=Decimal("0.00"),
            profit_loss_percentage=Decimal("0.00"),
            notes="Initial BTC purchase",
            metadata={"exchange": "binance"},
            external_id="ext_12345",
            external_source="binance_api",
            executed_at=datetime.utcnow()
        )
        
        # Mock update data
        update_data = PortfolioTransactionUpdate(
            notes="Updated BTC purchase",
            metadata={"exchange": "binance", "updated": True}
        )
        
        # Mock database calls
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Call the service method
        result = await portfolio_service.update_portfolio_transaction(1, update_data, 1)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result == mock_transaction
        assert result.notes == "Updated BTC purchase"
        assert result.metadata == {"exchange": "binance", "updated": True}
    
    async def test_update_portfolio_transaction_not_found(self, portfolio_service, mock_db_session):
        """Test updating a portfolio transaction that doesn't exist"""
        # Mock no transaction found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock update data
        update_data = PortfolioTransactionUpdate(
            notes="Updated BTC purchase"
        )
        
        # Call the service method
        result = await portfolio_service.update_portfolio_transaction(999, update_data, 1)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        assert result is None
    
    async def test_delete_portfolio_transaction(self, portfolio_service, mock_db_session):
        """Test deleting a portfolio transaction"""
        # Mock existing transaction
        mock_transaction = PortfolioTransaction(
            id=1,
            user_id=1,
            asset_id=1,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.1"),
            price=Decimal("50000.00"),
            total_value=Decimal("5000.00"),
            fee=Decimal("10.00"),
            realized_profit_loss=Decimal("0.00"),
            profit_loss_percentage=Decimal("0.00"),
            notes="Initial BTC purchase",
            metadata={"exchange": "binance"},
            external_id="ext_12345",
            external_source="binance_api",
            executed_at=datetime.utcnow()
        )
        
        # Mock database calls
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Call the service method
        result = await portfolio_service.delete_portfolio_transaction(1, 1)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        mock_db_session.delete.assert_called_once_with(mock_transaction)
        mock_db_session.commit.assert_called_once()
        assert result == mock_transaction
    
    async def test_delete_portfolio_transaction_not_found(self, portfolio_service, mock_db_session):
        """Test deleting a portfolio transaction that doesn't exist"""
        # Mock no transaction found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Call the service method
        result = await portfolio_service.delete_portfolio_transaction(999, 1)
        
        # Assertions
        mock_db_session.execute.assert_called_once()
        assert result is None


@pytest.mark.asyncio
class TestPortfolioPositionService:
    """Test portfolio position service functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def position_service(self, mock_db_session):
        """Create portfolio position service instance with mocked database"""
        return PortfolioPositionService(mock_db_session)
    
    async def test_calculate_position_value(self, position_service):
        """Test calculating position value"""
        # Mock position data
        quantity = Decimal("0.5")
        current_price = Decimal("60000.00")
        
        # Calculate position value
        position_value = position_service.calculate_position_value(quantity, current_price)
        
        # Assertions
        assert position_value == Decimal("30000.00")
    
    async def test_calculate_profit_loss(self, position_service):
        """Test calculating profit/loss"""
        # Mock position data
        quantity = Decimal("0.5")
        current_price = Decimal("60000.00")
        average_price = Decimal("50000.00")
        
        # Calculate profit/loss
        profit_loss = position_service.calculate_profit_loss(quantity, current_price, average_price)
        
        # Assertions
        assert profit_loss == Decimal("5000.00")  # 0.5 * (60000 - 50000)
    
    async def test_calculate_profit_loss_percentage(self, position_service):
        """Test calculating profit/loss percentage"""
        # Mock position data
        quantity = Decimal("0.5")
        current_price = Decimal("60000.00")
        average_price = Decimal("50000.00")
        
        # Calculate profit/loss percentage
        profit_loss_percentage = position_service.calculate_profit_loss_percentage(
            quantity, current_price, average_price
        )
        
        # Assertions
        assert profit_loss_percentage == Decimal("20.00")  # ((60000 - 50000) / 50000) * 100
    
    async def test_calculate_allocation_percentage(self, position_service):
        """Test calculating allocation percentage"""
        # Mock position data
        position_value = Decimal("30000.00")
        total_portfolio_value = Decimal("50000.00")
        
        # Calculate allocation percentage
        allocation_percentage = position_service.calculate_allocation_percentage(
            position_value, total_portfolio_value
        )
        
        # Assertions
        assert allocation_percentage == Decimal("60.00")  # (30000 / 50000) * 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
