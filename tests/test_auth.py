"""
Test suite for authentication and authorization modules.
"""
import pytest
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from src.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    decode_jwt_with_validation,
    authenticate_user,
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    get_current_user_websocket
)
from src.core.authorization import (
    Permission,
    ResourceType,
    Role,
    ResourceOwnership,
    PermissionChecker,
    require_permission,
    require_ownership,
    require_role,
    AuthorizationAuditor,
    authorization_auditor
)
from src.core.config import settings
from src.schemas.token import Token, TokenData, TokenPayload
from src.schemas.user import User, UserCreate, UserUpdate
from src.models.user import User as UserModel
from src.services.user_service import UserService


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 20  # Argon2 hashes are long
        assert hashed.startswith("$argon2")  # Argon2 hash format
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Should be different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTSecurity:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are quite long
        
        # Decode without verification to check structure
        unverified_payload = jwt.get_unverified_claims(token)
        assert unverified_payload["sub"] == "123"
        assert "exp" in unverified_payload
        assert "iat" in unverified_payload
        assert "nbf" in unverified_payload
        assert "iss" in unverified_payload
        assert "aud" in unverified_payload
    
    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        data = {"sub": "123"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        unverified_payload = jwt.get_unverified_claims(token)
        expected_exp = datetime.now(timezone.utc) + expires_delta
        actual_exp = datetime.fromtimestamp(unverified_payload["exp"], tz=timezone.utc)
        
        # Allow 5 second tolerance
        assert abs((actual_exp - expected_exp).total_seconds()) < 5
    
    def test_decode_jwt_valid_token(self):
        """Test decoding valid JWT token."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        payload = decode_jwt_with_validation(token)
        
        assert payload["sub"] == "123"
        assert payload["iss"] == "robot-crypt-api"
        assert payload["aud"] == "robot-crypt-client"
    
    def test_decode_jwt_expired_token(self):
        """Test decoding expired JWT token."""
        data = {"sub": "123"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        
        with pytest.raises(Exception):  # JWTError or similar
            decode_jwt_with_validation(token)
    
    def test_decode_jwt_invalid_signature(self):
        """Test decoding JWT with invalid signature."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"
        
        with pytest.raises(Exception):  # JWTError
            decode_jwt_with_validation(tampered_token)
    
    def test_decode_jwt_missing_claims(self):
        """Test decoding JWT with missing required claims."""
        # Create token manually without required claims
        payload = {"sub": "123", "exp": time.time() + 3600}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        with pytest.raises(Exception):  # JWTError due to missing claims
            decode_jwt_with_validation(token)


class TestAuthentication:
    """Test user authentication functionality."""
    
    @pytest.fixture
    def mock_user_service(self):
        """Create mock user service."""
        return AsyncMock(spec=UserService)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return UserModel(
            id=1,
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={"role": "user"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_user_service, sample_user):
        """Test successful user authentication."""
        mock_user_service.get_by_email.return_value = sample_user
        
        user = await authenticate_user(mock_user_service, "test@example.com", "password123")
        
        assert user is not None
        assert user.email == "test@example.com"
        mock_user_service.get_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_user_service, sample_user):
        """Test authentication with wrong password."""
        mock_user_service.get_by_email.return_value = sample_user
        
        user = await authenticate_user(mock_user_service, "test@example.com", "wrong_password")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_user_service):
        """Test authentication with non-existent user."""
        mock_user_service.get_by_email.return_value = None
        
        user = await authenticate_user(mock_user_service, "nonexistent@example.com", "password123")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, sample_user):
        """Test getting current user with valid token."""
        # Create valid token
        token = create_access_token({"sub": str(sample_user.id)})
        
        # Mock database and user service
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service.get.return_value = sample_user
        
        with patch('src.core.security.UserService', return_value=mock_user_service):
            user = await get_current_user(mock_db, token)
        
        assert user.id == sample_user.id
        assert user.email == sample_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        mock_db = AsyncMock(spec=AsyncSession)
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, invalid_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, sample_user):
        """Test getting current user when user is inactive."""
        sample_user.is_active = False
        token = create_access_token({"sub": str(sample_user.id)})
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service.get.return_value = sample_user
        
        with patch('src.core.security.UserService', return_value=mock_user_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_db, token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Inactive user" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_active_superuser(self, sample_user):
        """Test getting current active superuser."""
        sample_user.is_superuser = True
        
        user = await get_current_active_superuser(sample_user)
        assert user.is_superuser is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_superuser_not_superuser(self, sample_user):
        """Test getting current active superuser when user is not superuser."""
        sample_user.is_superuser = False
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_superuser(sample_user)
        
        assert exc_info.value.status_code == 400


class TestPermissionChecker:
    """Test permission checking functionality."""
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return UserModel(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={"role": "user"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_has_permission_user_role(self, sample_user):
        """Test permission checking for user role."""
        sample_user.preferences = {"role": "user"}
        
        assert PermissionChecker.has_permission(sample_user, Permission.READ, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.WRITE, ResourceType.PORTFOLIO) is False
        assert PermissionChecker.has_permission(sample_user, Permission.DELETE, ResourceType.PORTFOLIO) is False
    
    def test_has_permission_trader_role(self, sample_user):
        """Test permission checking for trader role."""
        sample_user.preferences = {"role": "trader"}
        
        assert PermissionChecker.has_permission(sample_user, Permission.READ, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.WRITE, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.EXECUTE, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.DELETE, ResourceType.PORTFOLIO) is False
    
    def test_has_permission_admin_role(self, sample_user):
        """Test permission checking for admin role."""
        sample_user.preferences = {"role": "admin"}
        
        assert PermissionChecker.has_permission(sample_user, Permission.READ, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.WRITE, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.DELETE, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(sample_user, Permission.EXECUTE, ResourceType.PORTFOLIO) is True
    
    def test_has_permission_superuser_role(self, sample_user):
        """Test permission checking for superuser role."""
        sample_user.preferences = {"role": "superuser"}
        
        # Superusers have all permissions
        assert PermissionChecker.has_permission(sample_user, Permission.READ, ResourceType.SYSTEM) is True
        assert PermissionChecker.has_permission(sample_user, Permission.ADMIN, ResourceType.SYSTEM) is True
        assert PermissionChecker.has_permission(sample_user, Permission.DELETE, ResourceType.USER) is True
    
    def test_check_resource_access_system(self, sample_user):
        """Test resource access checking for system resources."""
        sample_user.preferences = {"role": "user"}
        
        # Only admins can access system resources
        assert PermissionChecker.check_resource_access(sample_user, ResourceType.SYSTEM, Permission.READ) is False
        
        sample_user.preferences = {"role": "admin"}
        assert PermissionChecker.check_resource_access(sample_user, ResourceType.SYSTEM, Permission.READ) is True
    
    def test_check_resource_access_user(self, sample_user):
        """Test resource access checking for user resources."""
        sample_user.preferences = {"role": "user"}
        
        # Users can read/write their own data
        assert PermissionChecker.check_resource_access(sample_user, ResourceType.USER, Permission.READ) is True
        assert PermissionChecker.check_resource_access(sample_user, ResourceType.USER, Permission.WRITE) is True
        
        # Only admins can delete users
        assert PermissionChecker.check_resource_access(sample_user, ResourceType.USER, Permission.DELETE) is False


class TestResourceOwnership:
    """Test resource ownership verification."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return UserModel(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def resource_ownership(self, mock_db):
        """Create ResourceOwnership instance."""
        return ResourceOwnership(mock_db)
    
    @pytest.mark.asyncio
    async def test_verify_portfolio_ownership_success(self, resource_ownership, mock_db, sample_user):
        """Test successful portfolio ownership verification."""
        # Mock portfolio exists and belongs to user
        mock_result = MagicMock()
        mock_portfolio = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_portfolio
        mock_db.execute.return_value = mock_result
        
        is_owner = await resource_ownership.verify_portfolio_ownership(1, sample_user)
        
        assert is_owner is True
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_portfolio_ownership_failure(self, resource_ownership, mock_db, sample_user):
        """Test failed portfolio ownership verification."""
        # Mock portfolio doesn't exist or doesn't belong to user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        is_owner = await resource_ownership.verify_portfolio_ownership(1, sample_user)
        
        assert is_owner is False
    
    @pytest.mark.asyncio
    async def test_verify_trade_ownership_success(self, resource_ownership, mock_db, sample_user):
        """Test successful trade ownership verification."""
        mock_result = MagicMock()
        mock_trade = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_trade
        mock_db.execute.return_value = mock_result
        
        is_owner = await resource_ownership.verify_trade_ownership(1, sample_user)
        
        assert is_owner is True
    
    @pytest.mark.asyncio
    async def test_verify_ownership_database_error(self, resource_ownership, mock_db, sample_user):
        """Test ownership verification with database error."""
        mock_db.execute.side_effect = Exception("Database error")
        
        is_owner = await resource_ownership.verify_portfolio_ownership(1, sample_user)
        
        assert is_owner is False


class TestAuthorizationDecorators:
    """Test authorization decorators."""
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return UserModel(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={"role": "trader"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_success(self, sample_user):
        """Test successful permission requirement."""
        
        @require_permission(Permission.READ, ResourceType.PORTFOLIO)
        async def test_endpoint(user):
            return {"message": "success"}
        
        result = await test_endpoint(sample_user)
        assert result["message"] == "success"
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_failure(self, sample_user):
        """Test failed permission requirement."""
        sample_user.preferences = {"role": "user"}  # User role doesn't have WRITE permission
        
        @require_permission(Permission.WRITE, ResourceType.PORTFOLIO)
        async def test_endpoint(user):
            return {"message": "success"}
        
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(sample_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_require_role_decorator_success(self, sample_user):
        """Test successful role requirement."""
        
        @require_role(Role.TRADER)
        async def test_endpoint(user):
            return {"message": "success"}
        
        result = await test_endpoint(sample_user)
        assert result["message"] == "success"
    
    @pytest.mark.asyncio
    async def test_require_role_decorator_failure(self, sample_user):
        """Test failed role requirement."""
        sample_user.preferences = {"role": "user"}  # User role is lower than TRADER
        
        @require_role(Role.ADMIN)
        async def test_endpoint(user):
            return {"message": "success"}
        
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(sample_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestAuthorizationAuditor:
    """Test authorization auditing functionality."""
    
    def test_auditor_initialization(self):
        """Test auditor initialization."""
        auditor = AuthorizationAuditor()
        assert auditor.logger is not None
    
    def test_log_access_attempt_granted(self):
        """Test logging granted access attempt."""
        auditor = AuthorizationAuditor()
        
        with patch.object(auditor.logger, 'info') as mock_info:
            auditor.log_access_attempt(
                user_id=1,
                resource_type="portfolio",
                resource_id="123",
                permission="read",
                granted=True
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "Access granted" in call_args
    
    def test_log_access_attempt_denied(self):
        """Test logging denied access attempt."""
        auditor = AuthorizationAuditor()
        
        with patch.object(auditor.logger, 'warning') as mock_warning:
            auditor.log_access_attempt(
                user_id=1,
                resource_type="portfolio",
                resource_id="123",
                permission="delete",
                granted=False,
                reason="Insufficient permissions"
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            assert "Access denied" in call_args
    
    def test_log_privilege_escalation_attempt(self):
        """Test logging privilege escalation attempt."""
        auditor = AuthorizationAuditor()
        
        with patch.object(auditor.logger, 'critical') as mock_critical:
            auditor.log_privilege_escalation_attempt(
                user_id=1,
                attempted_action="Access admin panel without permissions"
            )
            
            mock_critical.assert_called_once()
            call_args = mock_critical.call_args[0][0]
            assert "Privilege escalation attempt" in call_args
            assert "User 1" in call_args


class TestEnums:
    """Test enum classes."""
    
    def test_permission_enum(self):
        """Test Permission enum values."""
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.DELETE.value == "delete"
        assert Permission.ADMIN.value == "admin"
        assert Permission.EXECUTE.value == "execute"
    
    def test_resource_type_enum(self):
        """Test ResourceType enum values."""
        assert ResourceType.PORTFOLIO.value == "portfolio"
        assert ResourceType.TRADE.value == "trade"
        assert ResourceType.ALERT.value == "alert"
        assert ResourceType.REPORT.value == "report"
        assert ResourceType.USER.value == "user"
        assert ResourceType.SYSTEM.value == "system"
    
    def test_role_enum(self):
        """Test Role enum values."""
        assert Role.USER.value == "user"
        assert Role.TRADER.value == "trader"
        assert Role.ANALYST.value == "analyst"
        assert Role.ADMIN.value == "admin"
        assert Role.SUPERUSER.value == "superuser"


class TestTokenSchemas:
    """Test token-related schemas."""
    
    def test_token_schema(self):
        """Test Token schema."""
        token_data = {
            "access_token": "test_token_123",
            "token_type": "bearer"
        }
        token = Token(**token_data)
        
        assert token.access_token == "test_token_123"
        assert token.token_type == "bearer"
        assert token.refresh_token is None
    
    def test_token_schema_with_refresh(self):
        """Test Token schema with refresh token."""
        token_data = {
            "access_token": "test_token_123",
            "token_type": "bearer",
            "refresh_token": "refresh_token_456"
        }
        token = Token(**token_data)
        
        assert token.refresh_token == "refresh_token_456"
    
    def test_token_data_schema(self):
        """Test TokenData schema."""
        token_data = TokenData(username="test@example.com", user_id=123)
        
        assert token_data.username == "test@example.com"
        assert token_data.user_id == 123
    
    def test_token_payload_schema(self):
        """Test TokenPayload schema."""
        payload = TokenPayload(sub=123, exp=1234567890)
        
        assert payload.sub == 123
        assert payload.exp == 1234567890


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_create_schema(self):
        """Test UserCreate schema."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "is_active": True,
            "preferences": {"theme": "dark"}
        }
        user = UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.preferences["theme"] == "dark"
    
    def test_user_create_schema_password_validation(self):
        """Test UserCreate schema password validation."""
        user_data = {
            "email": "test@example.com",
            "password": "short",  # Too short
            "full_name": "Test User"
        }
        
        with pytest.raises(Exception):  # Validation error
            UserCreate(**user_data)
    
    def test_user_update_schema(self):
        """Test UserUpdate schema."""
        update_data = {
            "full_name": "Updated Name",
            "preferences": {"theme": "light"}
        }
        user_update = UserUpdate(**update_data)
        
        assert user_update.full_name == "Updated Name"
        assert user_update.preferences["theme"] == "light"
        assert user_update.email is None  # Optional field
    
    def test_user_schema(self):
        """Test User schema."""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            "preferences": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        user = User(**user_data)
        
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_active is True


# Integration tests
class TestAuthIntegration:
    """Test integration between auth components."""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self):
        """Test complete authentication flow."""
        # 1. Create user with hashed password
        password = "test_password_123"
        hashed_password = get_password_hash(password)
        user = UserModel(
            id=1,
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={"role": "trader"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 2. Mock user service
        mock_user_service = AsyncMock(spec=UserService)
        mock_user_service.get_by_email.return_value = user
        mock_user_service.get.return_value = user
        
        # 3. Authenticate user
        authenticated_user = await authenticate_user(mock_user_service, "test@example.com", password)
        assert authenticated_user is not None
        
        # 4. Create access token
        token = create_access_token({"sub": str(authenticated_user.id)})
        assert isinstance(token, str)
        
        # 5. Verify token and get user
        mock_db = AsyncMock(spec=AsyncSession)
        with patch('src.core.security.UserService', return_value=mock_user_service):
            current_user = await get_current_user(mock_db, token)
        
        assert current_user.id == user.id
        assert current_user.email == user.email
        
        # 6. Check permissions
        assert PermissionChecker.has_permission(current_user, Permission.READ, ResourceType.PORTFOLIO) is True
        assert PermissionChecker.has_permission(current_user, Permission.EXECUTE, ResourceType.TRADE) is True
    
    @pytest.mark.asyncio
    async def test_auth_with_ownership_verification(self):
        """Test authentication with resource ownership verification."""
        # Create user
        user = UserModel(
            id=1,
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            preferences={"role": "trader"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock database and ownership verification
        mock_db = AsyncMock(spec=AsyncSession)
        ownership = ResourceOwnership(mock_db)
        
        # Mock successful ownership verification
        mock_result = MagicMock()
        mock_portfolio = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_portfolio
        mock_db.execute.return_value = mock_result
        
        is_owner = await ownership.verify_portfolio_ownership(1, user)
        assert is_owner is True
        
        # Check that user has appropriate permissions
        assert PermissionChecker.check_resource_access(user, ResourceType.PORTFOLIO, Permission.READ) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
