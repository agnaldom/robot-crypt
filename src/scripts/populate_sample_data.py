#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import settings
from src.database.database import async_engine
from src.models import User, Asset, TechnicalIndicator, MacroIndicator, BotPerformance, RiskManagement, Alert, Trade, Report
from src.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession


async def create_sample_assets():
    """Create sample cryptocurrency assets."""
    print("Creating sample assets...")
    
    async with AsyncSession(async_engine) as session:
        assets = [
            Asset(
                symbol="BTC/USDT",
                name="Bitcoin",
                type="crypto",
                current_price=45000.0,
                market_cap=850000000000.0,
                volume_24h=28000000000.0,
                is_active=True,
                is_monitored=True,
                metadata={"description": "Leading cryptocurrency"}
            ),
            Asset(
                symbol="ETH/USDT",
                name="Ethereum",
                type="crypto",
                current_price=2800.0,
                market_cap=335000000000.0,
                volume_24h=12000000000.0,
                is_active=True,
                is_monitored=True,
                metadata={"description": "Smart contract platform"}
            ),
            Asset(
                symbol="BNB/USDT",
                name="Binance Coin",
                type="crypto",
                current_price=320.0,
                market_cap=50000000000.0,
                volume_24h=1500000000.0,
                is_active=True,
                is_monitored=True,
                metadata={"description": "Binance exchange token"}
            ),
            Asset(
                symbol="ADA/USDT",
                name="Cardano",
                type="crypto",
                current_price=0.45,
                market_cap=15000000000.0,
                volume_24h=800000000.0,
                is_active=True,
                is_monitored=False,
                metadata={"description": "Proof-of-stake blockchain"}
            ),
            Asset(
                symbol="SOL/USDT",
                name="Solana",
                type="crypto",
                current_price=65.0,
                market_cap=28000000000.0,
                volume_24h=2200000000.0,
                is_active=True,
                is_monitored=True,
                metadata={"description": "High-performance blockchain"}
            )
        ]
        
        for asset in assets:
            session.add(asset)
        
        await session.commit()
        print(f"✅ Created {len(assets)} sample assets")


async def create_sample_users():
    """Create sample users."""
    print("Creating sample users...")
    
    async with AsyncSession(async_engine) as session:
        # Check if admin user exists
        from sqlalchemy.future import select
        result = await session.execute(select(User).where(User.email == "admin@robot-crypt.com"))
        admin_exists = result.scalar_one_or_none()
        
        users = []
        
        if not admin_exists:
            admin_user = User(
                email="admin@robot-crypt.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Robot-Crypt Admin",
                is_active=True,
                is_superuser=True,
                preferences={"theme": "dark", "notifications": True}
            )
            users.append(admin_user)
        
        # Create sample regular users
        regular_users = [
            User(
                email="trader1@robot-crypt.com",
                hashed_password=get_password_hash("trader123"),
                full_name="Alice Trader",
                is_active=True,
                is_superuser=False,
                preferences={"theme": "light", "notifications": True, "risk_level": "moderate"}
            ),
            User(
                email="trader2@robot-crypt.com",
                hashed_password=get_password_hash("trader123"),
                full_name="Bob Investor",
                is_active=True,
                is_superuser=False,
                preferences={"theme": "dark", "notifications": False, "risk_level": "conservative"}
            ),
            User(
                email="analyst@robot-crypt.com",
                hashed_password=get_password_hash("analyst123"),
                full_name="Charlie Analyst",
                is_active=True,
                is_superuser=False,
                preferences={"theme": "auto", "notifications": True, "risk_level": "aggressive"}
            )
        ]
        
        users.extend(regular_users)
        
        for user in users:
            session.add(user)
        
        await session.commit()
        print(f"✅ Created {len(users)} sample users")


async def create_sample_trades():
    """Create sample trades."""
    print("Creating sample trades...")
    
    async with AsyncSession(async_engine) as session:
        from sqlalchemy.future import select
        from datetime import datetime, timedelta
        import random
        
        # Get users and assets
        users_result = await session.execute(select(User).where(User.is_superuser == False))
        users = users_result.scalars().all()
        
        assets_result = await session.execute(select(Asset))
        assets = assets_result.scalars().all()
        
        if not users or not assets:
            print("⚠️  No users or assets found, skipping trade creation")
            return
        
        trades = []
        
        # Create trades for the last 30 days
        for i in range(50):
            user = random.choice(users)
            asset = random.choice(assets)
            
            # Random trade from last 30 days
            days_ago = random.randint(0, 30)
            trade_date = datetime.now() - timedelta(days=days_ago)
            
            trade_type = random.choice(["buy", "sell"])
            price = asset.current_price * random.uniform(0.95, 1.05)
            quantity = random.uniform(0.001, 0.1)
            total_value = price * quantity
            fee = total_value * 0.001  # 0.1% fee
            
            # Calculate profit/loss for sell orders
            is_profitable = None
            profit_loss = None
            profit_loss_percentage = None
            
            if trade_type == "sell":
                # Assume buy price was 95-105% of current sell price
                buy_price = price * random.uniform(0.95, 1.05)
                profit_loss = (price - buy_price) * quantity
                profit_loss_percentage = (profit_loss / (buy_price * quantity)) * 100
                is_profitable = profit_loss > 0
            
            trade = Trade(
                user_id=user.id,
                asset_id=asset.id,
                trade_type=trade_type,
                quantity=quantity,
                price=price,
                total_value=total_value,
                fee=fee,
                status="executed",
                is_profitable=is_profitable,
                profit_loss=profit_loss,
                profit_loss_percentage=profit_loss_percentage,
                notes=f"Sample {trade_type} trade",
                metadata={"strategy": random.choice(["scalping", "swing", "dca"])},
                executed_at=trade_date
            )
            trades.append(trade)
        
        for trade in trades:
            session.add(trade)
        
        await session.commit()
        print(f"✅ Created {len(trades)} sample trades")


async def create_sample_bot_performance():
    """Create sample bot performance records."""
    print("Creating sample bot performance...")
    
    async with AsyncSession(async_engine) as session:
        from datetime import datetime, timedelta
        
        performance_records = []
        
        # Daily performance for last 30 days
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            
            performance = BotPerformance(
                period="daily",
                total_trades=random.randint(2, 8),
                successful_trades=random.randint(1, 6),
                success_rate=random.uniform(55, 85),
                total_return=random.uniform(-200, 500),
                return_percentage=random.uniform(-2, 5),
                current_exposure=random.uniform(20, 80),
                metrics={
                    "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
                    "max_drawdown": round(random.uniform(2, 15), 2),
                    "volatility": round(random.uniform(15, 45), 2)
                },
                recorded_at=date
            )
            performance_records.append(performance)
        
        # Weekly performance
        for i in range(12):
            date = datetime.now() - timedelta(weeks=i)
            
            performance = BotPerformance(
                period="weekly",
                total_trades=random.randint(10, 50),
                successful_trades=random.randint(6, 35),
                success_rate=random.uniform(60, 80),
                total_return=random.uniform(-1000, 3000),
                return_percentage=random.uniform(-5, 15),
                current_exposure=random.uniform(30, 70),
                metrics={
                    "sharpe_ratio": round(random.uniform(0.8, 2.2), 2),
                    "max_drawdown": round(random.uniform(5, 25), 2),
                    "volatility": round(random.uniform(20, 50), 2)
                },
                recorded_at=date
            )
            performance_records.append(performance)
        
        # Monthly performance
        for i in range(6):
            date = datetime.now() - timedelta(days=i*30)
            
            performance = BotPerformance(
                period="monthly",
                total_trades=random.randint(40, 200),
                successful_trades=random.randint(25, 140),
                success_rate=random.uniform(65, 75),
                total_return=random.uniform(-3000, 12000),
                return_percentage=random.uniform(-10, 25),
                current_exposure=random.uniform(40, 80),
                metrics={
                    "sharpe_ratio": round(random.uniform(1.0, 2.0), 2),
                    "max_drawdown": round(random.uniform(8, 30), 2),
                    "volatility": round(random.uniform(25, 55), 2)
                },
                recorded_at=date
            )
            performance_records.append(performance)
        
        for record in performance_records:
            session.add(record)
        
        await session.commit()
        print(f"✅ Created {len(performance_records)} bot performance records")


async def populate_database():
    """Populate database with sample data."""
    print("🚀 Populating Robot-Crypt database with sample data...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print()
    
    try:
        await create_sample_users()
        await create_sample_assets()
        await create_sample_trades()
        await create_sample_bot_performance()
        
        print()
        print("🎉 Database populated successfully!")
        print()
        print("Sample data created:")
        print("- Admin user: admin@robot-crypt.com / admin123")
        print("- Regular users: trader1@robot-crypt.com, trader2@robot-crypt.com, analyst@robot-crypt.com")
        print("- Password for all regular users: trader123 or analyst123")
        print("- 5 cryptocurrency assets")
        print("- 50 sample trades")
        print("- Bot performance data for last 6 months")
        print()
        print("You can now test the API endpoints!")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(populate_database())
