"""
Tests for authentication router endpoints.
"""

import pytest
import pytest_asyncio
from datetime import timedelta, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routers.auth import router
from src.schemas.user import User
from src.schemas.token import Token
from src.core.config import settings


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock user object."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        is_active=True,
        is_superuser=False,
        full_name="Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        preferences={}
    )


@pytest.fixture
def mock_superuser():
    """Mock superuser object."""
    return User(
        id=2,
        email="admin@example.com",
        username="admin",
        is_active=True,
        is_superuser=True,
        full_name="Admin User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        preferences={}
    )


@pytest.fixture
def test_client():
    """Create test client for auth router."""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi import Request
    import logging
    
    app = FastAPI()
    
    # Add the same exception handler as the main app
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    app.include_router(router, prefix="/auth")
    return TestClient(app)


class TestLoginEndpoint:
    """Tests for the login endpoint."""
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_success(self, mock_get_db, mock_user_service, 
                               mock_create_token, mock_authenticate, 
                               test_client, mock_db, mock_user):
        """Test successful login."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "fake_access_token"
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["access_token"] == "fake_access_token"
        assert response_data["token_type"] == "bearer"
        
        # Verify service calls
        mock_authenticate.assert_called_once_with(
            mock_user_service.return_value, "testuser", "testpass123"
        )
        mock_create_token.assert_called_once()
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_invalid_credentials(self, mock_get_db, mock_user_service,
                                           mock_authenticate, test_client, mock_db):
        """Test login with invalid credentials."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_authenticate.return_value = None  # Invalid credentials
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpass"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_data = response.json()
        assert response_data["detail"] == "Incorrect username or password"
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_missing_username(self, mock_get_db, mock_user_service,
                                        mock_authenticate, test_client, mock_db):
        """Test login with missing username."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "password": "testpass123"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_missing_password(self, mock_get_db, mock_user_service,
                                        mock_authenticate, test_client, mock_db):
        """Test login with missing password."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "testuser"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_token_expiration_setting(self, mock_get_db, mock_user_service,
                                                 mock_create_token, mock_authenticate,
                                                 test_client, mock_db, mock_user):
        """Test that login uses correct token expiration setting."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "fake_access_token"
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        
        # Verify token creation was called with correct expiration
        mock_create_token.assert_called_once()
        call_args = mock_create_token.call_args
        assert call_args[1]["data"]["sub"] == "1"  # User ID as string
        assert isinstance(call_args[1]["expires_delta"], timedelta)
        assert call_args[1]["expires_delta"].total_seconds() == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TestTokenEndpoint:
    """Tests for the test token endpoint."""
    
    def test_test_token_success(self, test_client, mock_user):
        """Test successful token validation."""
        from src.core.security import get_current_user
        
        # Override the dependency to return our mock user
        def override_get_current_user():
            return mock_user
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Make request with Authorization header
            response = test_client.post(
                "/auth/test-token",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["id"] == mock_user.id
            assert response_data["email"] == mock_user.email
        finally:
            # Clean up the override
            test_client.app.dependency_overrides.pop(get_current_user, None)
    
    @patch('src.api.routers.auth.get_current_user')
    def test_test_token_invalid_token(self, mock_get_current_user, test_client):
        """Test token validation with invalid token."""
        from fastapi import HTTPException
        
        # Setup mock to raise an exception
        mock_get_current_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        # Make request with invalid token
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    def test_test_token_missing_auth_header(self, test_client):
        """Test token validation without authorization header."""
        # Make request without Authorization header
        response = test_client.post("/auth/test-token")
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshTokenEndpoint:
    """Tests for the refresh token endpoint."""
    
    def test_refresh_token_success(self, test_client, mock_user):
        """Test successful token refresh."""
        from src.core.security import get_current_user, create_access_token
        from unittest.mock import Mock
        
        # Mock the create_access_token function
        mock_create_token = Mock(return_value="new_access_token")
        
        # Override dependencies
        def override_get_current_user():
            return mock_user
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Patch the create_access_token function
        with patch('src.api.routers.auth.create_access_token', mock_create_token):
            try:
                # Make request
                response = test_client.post(
                    "/auth/refresh",
                    headers={"Authorization": "Bearer old_token"}
                )
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["access_token"] == "new_access_token"
                assert response_data["token_type"] == "bearer"
                
                # Verify token creation was called
                mock_create_token.assert_called_once()
                call_args = mock_create_token.call_args
                assert call_args[1]["data"]["sub"] == "1"  # User ID as string
                assert isinstance(call_args[1]["expires_delta"], timedelta)
            finally:
                # Clean up the override
                test_client.app.dependency_overrides.pop(get_current_user, None)
    
    def test_refresh_token_invalid_token(self, test_client):
        """Test token refresh with invalid token."""
        from src.core.security import get_current_user
        from fastapi import HTTPException
        
        # Override dependency to raise an exception
        def override_get_current_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Make request
            response = test_client.post(
                "/auth/refresh",
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            # Assertions
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            # Clean up the override
            test_client.app.dependency_overrides.pop(get_current_user, None)
    
    def test_refresh_token_missing_auth_header(self, test_client):
        """Test token refresh without authorization header."""
        # Make request without Authorization header
        response = test_client.post("/auth/refresh")
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_inactive_user(self, test_client):
        """Test token refresh with inactive user."""
        from src.core.security import get_current_user
        from fastapi import HTTPException
        
        # Override dependency to raise an exception for inactive user
        def override_get_current_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Make request - should fail because user is inactive
            response = test_client.post(
                "/auth/refresh",
                headers={"Authorization": "Bearer old_token"}
            )
            
            # Should fail with 401 because user is inactive
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Inactive user" in response.json()["detail"]
        finally:
            # Clean up the override
            test_client.app.dependency_overrides.pop(get_current_user, None)


class TestAuthRouterIntegration:
    """Integration tests for auth router."""
    
    def test_login_then_test_token_flow(self, test_client, mock_user):
        """Test complete login and token validation flow."""
        from src.core.security import get_current_user
        from src.database.database import get_database
        from unittest.mock import AsyncMock
        
        # Create mock database
        mock_db = AsyncMock()
        
        # Override dependencies
        def override_get_current_user():
            return mock_user
            
        def override_get_database():
            return mock_db
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        test_client.app.dependency_overrides[get_database] = override_get_database
        
        # Patch the functions that need mocking
        with patch('src.api.routers.auth.authenticate_user') as mock_authenticate, \
             patch('src.api.routers.auth.create_access_token') as mock_create_token, \
             patch('src.api.routers.auth.UserService') as mock_user_service:
            
            # Setup mocks
            mock_authenticate.return_value = mock_user
            mock_create_token.return_value = "test_access_token"
            mock_user_service.return_value = AsyncMock()
            
            try:
                # 1. Login
                login_response = test_client.post(
                    "/auth/login",
                    data={
                        "username": "testuser",
                        "password": "testpass123"
                    }
                )
                
                assert login_response.status_code == status.HTTP_200_OK
                login_data = login_response.json()
                access_token = login_data["access_token"]
                
                # 2. Test token
                token_response = test_client.post(
                    "/auth/test-token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert token_response.status_code == status.HTTP_200_OK
                token_data = token_response.json()
                assert token_data["id"] == mock_user.id
                assert token_data["email"] == mock_user.email
            finally:
                # Clean up overrides
                test_client.app.dependency_overrides.pop(get_current_user, None)
                test_client.app.dependency_overrides.pop(get_database, None)
    
    def test_refresh_token_flow(self, test_client, mock_user):
        """Test token refresh flow."""
        from src.core.security import get_current_user
        
        # Override dependency
        def override_get_current_user():
            return mock_user
        
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Patch create_access_token
        with patch('src.api.routers.auth.create_access_token') as mock_create_token:
            mock_create_token.return_value = "refreshed_access_token"
            
            try:
                # Refresh token
                refresh_response = test_client.post(
                    "/auth/refresh",
                    headers={"Authorization": "Bearer old_token"}
                )
                
                assert refresh_response.status_code == status.HTTP_200_OK
                refresh_data = refresh_response.json()
                assert refresh_data["access_token"] == "refreshed_access_token"
                assert refresh_data["token_type"] == "bearer"
            finally:
                # Clean up override
                test_client.app.dependency_overrides.pop(get_current_user, None)


class TestAuthRouterErrorHandling:
    """Tests for error handling in auth router."""
    
    def test_login_database_error(self, test_client):
        """Test login with database error."""
        from src.database.database import get_database
        import pytest
        
        # Override dependency to raise an error
        def override_get_database():
            raise Exception("Database connection failed")
        
        test_client.app.dependency_overrides[get_database] = override_get_database
        
        try:
            # Make request - should raise exception due to dependency injection error
            with pytest.raises(Exception, match="Database connection failed"):
                response = test_client.post(
                    "/auth/login",
                    data={
                        "username": "testuser",
                        "password": "testpass123"
                    }
                )
        finally:
            # Clean up override
            test_client.app.dependency_overrides.pop(get_database, None)
    
    def test_login_token_creation_error(self, test_client, mock_user):
        """Test login with token creation error."""
        from src.database.database import get_database
        from unittest.mock import AsyncMock
        import pytest
        
        # Create mock database
        mock_db = AsyncMock()
        
        # Override dependencies
        def override_get_database():
            return mock_db
        
        test_client.app.dependency_overrides[get_database] = override_get_database
        
        # Patch functions to simulate error
        with patch('src.api.routers.auth.authenticate_user') as mock_authenticate, \
             patch('src.api.routers.auth.create_access_token') as mock_create_token, \
             patch('src.api.routers.auth.UserService') as mock_user_service:
            
            # Setup mocks
            mock_authenticate.return_value = mock_user
            mock_create_token.side_effect = Exception("Token creation failed")
            mock_user_service.return_value = AsyncMock()
            
            try:
                # Make request - should raise exception due to token creation error
                with pytest.raises(Exception, match="Token creation failed"):
                    response = test_client.post(
                        "/auth/login",
                        data={
                            "username": "testuser",
                            "password": "testpass123"
                        }
                    )
            finally:
                # Clean up override
                test_client.app.dependency_overrides.pop(get_database, None)
    
    def test_invalid_http_method(self, test_client):
        """Test invalid HTTP methods on auth endpoints."""
        # Test GET on login endpoint (should be POST)
        response = test_client.get("/auth/login")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test PUT on test-token endpoint (should be POST)
        response = test_client.put("/auth/test-token")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test DELETE on refresh endpoint (should be POST)
        response = test_client.delete("/auth/refresh")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestAuthRouterSecurity:
    """Security-focused tests for auth router."""
    
    def test_login_empty_credentials(self, test_client):
        """Test login with empty credentials."""
        from src.database.database import get_database
        from unittest.mock import AsyncMock
        
        # Create mock database
        mock_db = AsyncMock()
        
        # Override dependencies
        def override_get_database():
            return mock_db
        
        test_client.app.dependency_overrides[get_database] = override_get_database
        
        # Patch the functions
        with patch('src.api.routers.auth.authenticate_user') as mock_authenticate, \
             patch('src.api.routers.auth.UserService') as mock_user_service:
            
            # Setup mocks - empty credentials should fail authentication
            mock_authenticate.return_value = None  # Failed authentication
            mock_user_service.return_value = AsyncMock()
            
            try:
                # Make request with empty credentials
                response = test_client.post(
                    "/auth/login",
                    data={
                        "username": "",
                        "password": ""
                    }
                )
                
                # Should return 401 for invalid credentials
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
                response_data = response.json()
                assert response_data["detail"] == "Incorrect username or password"
            finally:
                # Clean up override
                test_client.app.dependency_overrides.pop(get_database, None)
    
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.get_database')
    def test_login_sql_injection_attempt(self, mock_get_db, mock_user_service,
                                             mock_authenticate, test_client, mock_db):
        """Test login with SQL injection attempt."""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_authenticate.return_value = None  # Should not authenticate
        
        # Make request with SQL injection attempt
        response = test_client.post(
            "/auth/login",
            data={
                "username": "'; DROP TABLE users; --",
                "password": "' OR '1'='1"
            }
        )
        
        # Should return unauthorized (not authenticate)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify authenticate was called with the malicious input
        mock_authenticate.assert_called_once_with(
            mock_user_service.return_value,
            "'; DROP TABLE users; --",
            "' OR '1'='1"
        )
    
    def test_token_endpoint_rate_limiting_headers(self, test_client):
        """Test that auth endpoints don't expose sensitive headers."""
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        # Check that response doesn't contain sensitive server info
        assert "Server" not in response.headers
        assert "X-Powered-By" not in response.headers
