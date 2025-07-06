#!/usr/bin/env python3
"""
Script para inicializar o projeto Robot-Crypt FastAPI.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import settings
from src.core.security import get_password_hash
from src.database.database import async_engine, Base
from src.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")


async def create_admin_user():
    """Create initial admin user."""
    print("Creating admin user...")
    
    admin_email = "admin@robot-crypt.com"
    admin_password = "admin123"  # Change this in production!
    
    async with AsyncSession(async_engine) as session:
        # Check if admin user already exists
        from sqlalchemy.future import select
        result = await session.execute(select(User).where(User.email == admin_email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"⚠️  Admin user {admin_email} already exists!")
            return
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name="Robot-Crypt Admin",
            is_active=True,
            is_superuser=True,
            preferences={}
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"✅ Admin user created!")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print("   ⚠️  Please change the password after first login!")


async def initialize_project():
    """Initialize the entire project."""
    print("🚀 Initializing Robot-Crypt FastAPI Project...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Simulation mode: {settings.SIMULATION_MODE}")
    print()
    
    try:
        # Create tables
        await create_tables()
        
        # Create admin user
        await create_admin_user()
        
        print()
        print("🎉 Project initialized successfully!")
        print()
        print("Next steps:")
        print("1. Start the API server:")
        print("   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload")
        print()
        print("2. Access the API documentation:")
        print("   http://localhost:8000/docs")
        print()
        print("3. Login with admin credentials:")
        print("   POST /auth/login")
        print(f"   Email: admin@robot-crypt.com")
        print(f"   Password: admin123")
        print()
        
    except Exception as e:
        print(f"❌ Error initializing project: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(initialize_project())
