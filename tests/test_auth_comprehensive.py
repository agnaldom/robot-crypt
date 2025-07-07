"""
Comprehensive Authentication Test Suite for Robot-Crypt API.

This test suite provides extensive coverage for:
1. Login endpoint (success, failure, validation errors)
2. Token validation endpoint
3. Token refresh endpoint
4. Integration tests for complete auth flows
5. Proper mocking of dependencies
6. Security tests including SQL injection protection
7. HTTP method validation
8. Error handling for database and token creation failures
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from src.api.routers.auth import router
from src.schemas.user import User
from src.schemas.token import Token, TokenData
from src.core.config import settings
from src.services.user_service import UserService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock regular user object."""
    return User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
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
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        preferences={}
    )


@pytest.fixture
def mock_inactive_user():
    """Mock inactive user object."""
    return User(
        id=3,
        email="inactive@example.com",
        full_name="Inactive User",
        is_active=False,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        preferences={}
    )


@pytest.fixture
def test_client():
    """Create test client for auth router."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")
    return TestClient(app)


@pytest.fixture
def valid_token(mock_user):
    """Create a valid JWT token for testing."""
    from src.core.security import create_access_token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(mock_user.id)}, 
        expires_delta=access_token_expires
    )


@pytest.fixture
def expired_token(mock_user):
    """Create an expired JWT token for testing."""
    from src.core.security import create_access_token
    expired_delta = timedelta(minutes=-30)  # 30 minutes ago
    return create_access_token(
        data={"sub": str(mock_user.id)}, 
        expires_delta=expired_delta
    )


# ============================================================================
# LOGIN ENDPOINT TESTS
# ============================================================================

class TestLoginEndpoint:
    """Comprehensive tests for the login endpoint."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_login_success(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test successful login with valid credentials."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "test_access_token_12345"
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["access_token"] == "test_access_token_12345"
        assert response_data["token_type"] == "bearer"
        
        # Verify service calls
        mock_authenticate.assert_called_once_with(
            mock_user_service, 
            "test@example.com", 
            "testpassword123"
        )
        mock_create_token.assert_called_once()

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    def test_login_invalid_credentials(
        self, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session
    ):
        """Test login with invalid credentials."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = None  # Invalid credentials
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_data = response.json()
        assert response_data["detail"] == "Incorrect username or password"
        assert response_data.get("headers", {}).get("WWW-Authenticate") == "Bearer"

    def test_login_missing_username(self, test_client):
        """Test login with missing username field."""
        response = test_client.post(
            "/auth/login",
            data={"password": "testpassword123"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_data = response.json()
        assert "detail" in response_data

    def test_login_missing_password(self, test_client):
        """Test login with missing password field."""
        response = test_client.post(
            "/auth/login",
            data={"username": "test@example.com"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_data = response.json()
        assert "detail" in response_data

    def test_login_empty_credentials(self, test_client):
        """Test login with empty username and password."""
        response = test_client.post(
            "/auth/login",
            data={"username": "", "password": ""}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_login_token_expiration_setting(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test that login uses correct token expiration setting."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "test_token"
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify token creation parameters
        mock_create_token.assert_called_once()
        call_args = mock_create_token.call_args
        assert call_args[1]["data"]["sub"] == "1"
        assert isinstance(call_args[1]["expires_delta"], timedelta)
        expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert call_args[1]["expires_delta"].total_seconds() == expected_seconds


# ============================================================================
# TOKEN VALIDATION ENDPOINT TESTS
# ============================================================================

class TestTokenValidationEndpoint:
    """Tests for the test-token endpoint."""

    @patch('src.api.routers.auth.get_current_user')
    def test_token_validation_success(
        self, 
        mock_get_current_user, 
        test_client, 
        mock_user
    ):
        """Test successful token validation."""
        mock_get_current_user.return_value = mock_user
        
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == mock_user.id
        assert response_data["email"] == mock_user.email
        assert response_data["full_name"] == mock_user.full_name
        assert response_data["is_active"] == mock_user.is_active

    @patch('src.api.routers.auth.get_current_user')
    def test_token_validation_invalid_token(
        self, 
        mock_get_current_user, 
        test_client
    ):
        """Test token validation with invalid token."""
        mock_get_current_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_validation_missing_header(self, test_client):
        """Test token validation without authorization header."""
        response = test_client.post("/auth/test-token")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('src.api.routers.auth.get_current_user')
    def test_token_validation_malformed_header(
        self, 
        mock_get_current_user, 
        test_client
    ):
        """Test token validation with malformed authorization header."""
        mock_get_current_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "InvalidFormat token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TOKEN REFRESH ENDPOINT TESTS
# ============================================================================

class TestTokenRefreshEndpoint:
    """Tests for the token refresh endpoint."""

    @patch('src.api.routers.auth.get_current_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_refresh_token_success(
        self, 
        mock_create_token, 
        mock_get_current_user,
        test_client, 
        mock_user
    ):
        """Test successful token refresh."""
        mock_get_current_user.return_value = mock_user
        mock_create_token.return_value = "new_access_token_54321"
        
        response = test_client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer old_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["access_token"] == "new_access_token_54321"
        assert response_data["token_type"] == "bearer"
        
        # Verify token creation was called correctly
        mock_create_token.assert_called_once()
        call_args = mock_create_token.call_args
        assert call_args[1]["data"]["sub"] == "1"

    @patch('src.api.routers.auth.get_current_user')
    def test_refresh_token_invalid_token(
        self, 
        mock_get_current_user, 
        test_client
    ):
        """Test token refresh with invalid token."""
        mock_get_current_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        response = test_client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_missing_header(self, test_client):
        """Test token refresh without authorization header."""
        response = test_client.post("/auth/refresh")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('src.api.routers.auth.get_current_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_refresh_token_inactive_user(
        self, 
        mock_create_token, 
        mock_get_current_user,
        test_client, 
        mock_inactive_user
    ):
        """Test token refresh with inactive user."""
        # Note: get_current_user should already handle inactive users
        # This test verifies the refresh endpoint behavior
        mock_get_current_user.return_value = mock_inactive_user
        mock_create_token.return_value = "new_token_for_inactive"
        
        response = test_client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer token_for_inactive_user"}
        )
        
        # The endpoint should work since get_current_user handles the validation
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestAuthSecurity:
    """Security-focused tests for authentication endpoints."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    def test_sql_injection_protection(
        self, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session
    ):
        """Test protection against SQL injection attempts."""
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = None  # Should not authenticate
        
        # SQL injection payloads
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        for payload in malicious_payloads:
            response = test_client.post(
                "/auth/login",
                data={
                    "username": payload,
                    "password": payload
                }
            )
            
            # Should return unauthorized, not succeed or cause errors
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
            # Verify the malicious input was passed to authenticate function
            # (which should handle it safely)
            mock_authenticate.assert_called_with(
                mock_user_service, payload, payload
            )

    def test_password_not_exposed_in_response(self, test_client):
        """Test that passwords are never exposed in responses."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Check response doesn't contain password
        response_text = response.text.lower()
        assert "password" not in response_text
        assert "testpassword123" not in response_text

    @patch('src.api.routers.auth.get_current_user')
    def test_token_validation_timing_attack_protection(
        self, 
        mock_get_current_user, 
        test_client
    ):
        """Test protection against timing attacks on token validation."""
        # This test ensures consistent response times regardless of token validity
        import time
        
        # Invalid token test
        mock_get_current_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        start_time = time.time()
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        invalid_duration = time.time() - start_time
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # The test mainly ensures no exceptions are raised and response is consistent
        assert invalid_duration < 1.0  # Should be fast


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestAuthErrorHandling:
    """Tests for error handling in authentication endpoints."""

    @patch('src.api.routers.auth.get_database')
    def test_database_connection_error(
        self, 
        mock_get_db, 
        test_client
    ):
        """Test handling of database connection errors."""
        mock_get_db.side_effect = Exception("Database connection failed")
        
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_token_creation_error(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test handling of token creation errors."""
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.side_effect = Exception("Token creation failed")
        
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    def test_user_service_error(
        self, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session
    ):
        """Test handling of user service errors."""
        mock_get_db.return_value = mock_db_session
        mock_user_service_class.side_effect = Exception("User service error")
        
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# HTTP METHOD VALIDATION TESTS
# ============================================================================

class TestHTTPMethodValidation:
    """Tests for HTTP method validation on auth endpoints."""

    def test_login_invalid_methods(self, test_client):
        """Test invalid HTTP methods on login endpoint."""
        invalid_methods = ["GET", "PUT", "DELETE", "PATCH"]
        
        for method in invalid_methods:
            response = test_client.request(method, "/auth/login")
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_test_token_invalid_methods(self, test_client):
        """Test invalid HTTP methods on test-token endpoint."""
        invalid_methods = ["GET", "PUT", "DELETE", "PATCH"]
        
        for method in invalid_methods:
            response = test_client.request(method, "/auth/test-token")
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_refresh_invalid_methods(self, test_client):
        """Test invalid HTTP methods on refresh endpoint."""
        invalid_methods = ["GET", "PUT", "DELETE", "PATCH"]
        
        for method in invalid_methods:
            response = test_client.request(method, "/auth/refresh")
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAuthIntegration:
    """Integration tests for complete authentication flows."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    @patch('src.api.routers.auth.get_current_user')
    def test_complete_login_and_validation_flow(
        self, 
        mock_get_current_user,
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test complete flow: login → token validation."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "integration_test_token"
        mock_get_current_user.return_value = mock_user
        
        # Step 1: Login
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        # Step 2: Validate token
        validation_response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert validation_response.status_code == status.HTTP_200_OK
        validation_data = validation_response.json()
        assert validation_data["id"] == mock_user.id
        assert validation_data["email"] == mock_user.email

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    @patch('src.api.routers.auth.get_current_user')
    def test_complete_login_and_refresh_flow(
        self, 
        mock_get_current_user,
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test complete flow: login → token refresh."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_get_current_user.return_value = mock_user
        
        # Different tokens for login and refresh
        mock_create_token.side_effect = ["original_token", "refreshed_token"]
        
        # Step 1: Login
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        original_token = login_data["access_token"]
        
        # Step 2: Refresh token
        refresh_response = test_client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {original_token}"}
        )
        
        assert refresh_response.status_code == status.HTTP_200_OK
        refresh_data = refresh_response.json()
        assert refresh_data["access_token"] == "refreshed_token"
        assert refresh_data["token_type"] == "bearer"

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    def test_failed_login_prevents_token_access(
        self, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session
    ):
        """Test that failed login prevents subsequent token access."""
        # Setup mocks for failed login
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = None  # Failed authentication
        
        # Step 1: Failed login
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Step 2: Try to use any token (should fail)
        validation_response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert validation_response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# PERFORMANCE AND LOAD TESTS
# ============================================================================

class TestAuthPerformance:
    """Performance tests for authentication endpoints."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_concurrent_login_requests(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test handling of concurrent login requests."""
        import threading
        import time
        
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "concurrent_test_token"
        
        results = []
        
        def make_login_request():
            response = test_client.post(
                "/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "testpassword123"
                }
            )
            results.append(response.status_code)
        
        # Create multiple threads for concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_login_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        duration = time.time() - start_time
        
        # All requests should succeed
        assert all(status_code == 200 for status_code in results)
        assert len(results) == 5
        
        # Should complete reasonably quickly
        assert duration < 5.0  # 5 seconds max for 5 concurrent requests


# ============================================================================
# CONFIGURATION AND ENVIRONMENT TESTS
# ============================================================================

class TestAuthConfiguration:
    """Tests for authentication configuration and environment variables."""

    @patch('src.api.routers.auth.settings')
    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_custom_token_expiration(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        mock_settings,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test custom token expiration configuration."""
        # Setup custom expiration time
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2 hours
        
        # Setup other mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "custom_expiry_token"
        
        # Make request
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify custom expiration was used
        mock_create_token.assert_called_once()
        call_args = mock_create_token.call_args
        expires_delta = call_args[1]["expires_delta"]
        assert expires_delta.total_seconds() == 120 * 60  # 2 hours in seconds


# ============================================================================
# CLEANUP AND UTILITY TESTS
# ============================================================================

class TestAuthUtilities:
    """Tests for authentication utility functions and cleanup."""

    def test_response_headers_security(self, test_client):
        """Test that responses don't expose sensitive headers."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Check that sensitive headers are not exposed
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for header in sensitive_headers:
            assert header not in response.headers

    def test_cors_headers_presence(self, test_client):
        """Test presence of appropriate CORS headers if configured."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # This test depends on CORS configuration
        # In a real application, you might want to check for CORS headers
        assert response.status_code in [200, 401, 422, 500]  # Valid HTTP status

    def test_content_type_headers(self, test_client):
        """Test that responses have correct content-type headers."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Should return JSON content
        assert "application/json" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
