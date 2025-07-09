#!/usr/bin/env python3
"""
Simple script to create a test user for authentication testing.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create a test user directly in the database."""
    
    # Connect to database
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Check if user exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "admin@robotcrypt.com"}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print("✅ User admin@robotcrypt.com already exists")
                print(f"User ID: {existing_user[0]}")
            else:
                # Hash the password
                hashed_password = pwd_context.hash("Robot123!@#")
                
                # Insert user
                await conn.execute(
                    text("""
                        INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
                        VALUES (:email, :password, :name, :active, :superuser)
                    """),
                    {
                        "email": "admin@robotcrypt.com",
                        "password": hashed_password,
                        "name": "Admin Robot-Crypt",
                        "active": True,
                        "superuser": True
                    }
                )
                print("✅ Created user admin@robotcrypt.com")
            
            # Also create a simple test user
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "test@test.com"}
            )
            existing_test = result.fetchone()
            
            if not existing_test:
                hashed_password = pwd_context.hash("test123")
                await conn.execute(
                    text("""
                        INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
                        VALUES (:email, :password, :name, :active, :superuser)
                    """),
                    {
                        "email": "test@test.com",
                        "password": hashed_password,
                        "name": "Test User",
                        "active": True,
                        "superuser": False
                    }
                )
                print("✅ Created user test@test.com")
            else:
                print("✅ User test@test.com already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_user())
