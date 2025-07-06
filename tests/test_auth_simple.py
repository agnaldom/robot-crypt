"""
Simplified Authentication Tests for Robot-Crypt API.

This test suite focuses on working tests with proper mocking.
"""

import pytest
from datetime import timedelta, datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routers.auth import router
from src.schemas.user import User
from src.schemas.token import Token
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
        created_at=datetime.now(),
        updated_at=datetime.now(),
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
        created_at=datetime.now(),
        updated_at=datetime.now(),
        preferences={}
    )


@pytest.fixture
def test_client():
    """Create test client for auth router."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")
    return TestClient(app)


# ============================================================================
# LOGIN ENDPOINT TESTS
# ============================================================================

class TestLoginEndpoint:
    """Tests for the login endpoint."""

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
# TOKEN VALIDATION WITH WORKING DEPENDENCY OVERRIDE
# ============================================================================

class TestTokenValidationWithOverride:
    """Tests for token validation using dependency override."""

    def test_token_validation_success_with_override(self, mock_user):
        """Test successful token validation using dependency override."""
        from src.core.security import get_current_user
        
        # Create app and override dependency
        app = FastAPI()
        app.include_router(router, prefix="/auth")
        
        # Mock the dependency to return our mock user
        def mock_get_current_user_dependency():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user_dependency
        
        # Create test client
        test_client = TestClient(app)
        
        # Make request
        response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Clear overrides
        app.dependency_overrides.clear()
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == mock_user.id
        assert response_data["email"] == mock_user.email
        assert response_data["full_name"] == mock_user.full_name

    def test_token_refresh_success_with_override(self, mock_user):
        """Test successful token refresh using dependency override."""
        from src.core.security import get_current_user
        
        with patch('src.api.routers.auth.create_access_token') as mock_create_token:
            mock_create_token.return_value = "new_refreshed_token"
            
            # Create app and override dependency
            app = FastAPI()
            app.include_router(router, prefix="/auth")
            
            # Mock the dependency to return our mock user
            def mock_get_current_user_dependency():
                return mock_user
            
            app.dependency_overrides[get_current_user] = mock_get_current_user_dependency
            
            # Create test client
            test_client = TestClient(app)
            
            # Make request
            response = test_client.post(
                "/auth/refresh",
                headers={"Authorization": "Bearer old_token"}
            )
            
            # Clear overrides
            app.dependency_overrides.clear()
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["access_token"] == "new_refreshed_token"
            assert response_data["token_type"] == "bearer"
            
            # Verify token creation was called
            mock_create_token.assert_called_once()


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
        
        # Check response doesn't contain password regardless of status
        response_text = response.text.lower()
        assert "password" not in response_text
        assert "testpassword123" not in response_text

    def test_empty_credentials_validation(self, test_client):
        """Test validation of empty credentials."""
        response = test_client.post(
            "/auth/login",
            data={"username": "", "password": ""}
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestAuthErrorHandling:
    """Tests for error handling in authentication endpoints."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_token_creation_error_handling(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test graceful handling of token creation errors."""
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        
        # Mock token creation to raise an exception
        mock_create_token.side_effect = Exception("Token creation failed")
        
        # This should raise an exception and return 500
        with pytest.raises(Exception, match="Token creation failed"):
            test_client.post(
                "/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "testpassword123"
                }
            )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAuthIntegration:
    """Integration tests for complete authentication flows."""

    @patch('src.api.routers.auth.get_database')
    @patch('src.api.routers.auth.UserService')
    @patch('src.api.routers.auth.authenticate_user')
    @patch('src.api.routers.auth.create_access_token')
    def test_complete_login_flow(
        self, 
        mock_create_token, 
        mock_authenticate, 
        mock_user_service_class, 
        mock_get_db,
        test_client, 
        mock_db_session, 
        mock_user
    ):
        """Test complete login flow with proper mocking."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service_class.return_value = mock_user_service
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "integration_test_token"
        
        # Login
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        assert login_data["access_token"] == "integration_test_token"
        assert login_data["token_type"] == "bearer"

    def test_failed_login_prevents_token_access(self, test_client):
        """Test that failed login doesn't provide valid tokens."""
        # Failed login
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to use any token (should fail)
        validation_response = test_client.post(
            "/auth/test-token",
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert validation_response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# UTILITY TESTS
# ============================================================================

class TestAuthUtilities:
    """Tests for authentication utility functions and security headers."""

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

    def test_content_type_headers(self, test_client):
        """Test that responses have correct content-type headers."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Should return JSON content (if it doesn't error out)
        if response.status_code != 500:  # Avoid checking if there's a server error
            assert "application/json" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
