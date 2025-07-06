"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful user registration."""
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["telegram_id"] == sample_user_data["telegram_id"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with duplicate email."""
        # First registration
        await client.post("/auth/register", json=sample_user_data)
        
        # Second registration with same email
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_data(self, client: AsyncClient):
        """Test registration with invalid data."""
        invalid_data = {
            "email": "invalid-email",
            "full_name": "",
            "password": "short"
        }
        
        response = await client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful login."""
        # First register a user
        await client.post("/auth/register", json=sample_user_data)
        
        # Then login
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, sample_user_data: dict):
        """Test login with invalid credentials."""
        # Register a user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": sample_user_data["email"],
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, sample_user_data: dict):
        """Test getting current user information."""
        # Register a user
        register_response = await client.post("/auth/register", json=sample_user_data)
        user_id = register_response.json()["id"]
        
        # Login to get token
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = await client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401
