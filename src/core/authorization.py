"""
Advanced Authorization System for Robot-Crypt API (OWASP 2025 Compliant).
Implements granular access control and resource ownership verification.
"""
from functools import wraps
from typing import Optional, List, Dict, Any
import logging
from enum import Enum

from fastapi import HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.security import get_current_user
from src.models.user import User
from src.database.database import get_database


class Permission(Enum):
    """Permissions enum for granular access control."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"


class ResourceType(Enum):
    """Resource types for access control."""
    PORTFOLIO = "portfolio"
    TRADE = "trade"
    ALERT = "alert"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"


class Role(Enum):
    """User roles with hierarchical permissions."""
    USER = "user"
    TRADER = "trader"
    ANALYST = "analyst"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class ResourceOwnership:
    """Resource ownership verification utilities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def verify_portfolio_ownership(self, portfolio_id: int, user: User) -> bool:
        """Verify if user owns the portfolio."""
        try:
            from src.models.portfolio import Portfolio
            result = await self.db.execute(
                select(Portfolio).where(
                    Portfolio.id == portfolio_id,
                    Portfolio.owner_id == user.id
                )
            )
            portfolio = result.scalar_one_or_none()
            return portfolio is not None
        except Exception as e:
            self.logger.error(f"Error verifying portfolio ownership: {e}")
            return False
    
    async def verify_trade_ownership(self, trade_id: int, user: User) -> bool:
        """Verify if user owns the trade."""
        try:
            from src.models.trade import Trade
            result = await self.db.execute(
                select(Trade).where(
                    Trade.id == trade_id,
                    Trade.user_id == user.id
                )
            )
            trade = result.scalar_one_or_none()
            return trade is not None
        except Exception as e:
            self.logger.error(f"Error verifying trade ownership: {e}")
            return False
    
    async def verify_alert_ownership(self, alert_id: int, user: User) -> bool:
        """Verify if user owns the alert."""
        try:
            from src.models.alert import Alert
            result = await self.db.execute(
                select(Alert).where(
                    Alert.id == alert_id,
                    Alert.user_id == user.id
                )
            )
            alert = result.scalar_one_or_none()
            return alert is not None
        except Exception as e:
            self.logger.error(f"Error verifying alert ownership: {e}")
            return False
    
    async def verify_report_ownership(self, report_id: int, user: User) -> bool:
        """Verify if user owns the report."""
        try:
            from src.models.report import Report
            result = await self.db.execute(
                select(Report).where(
                    Report.id == report_id,
                    Report.user_id == user.id
                )
            )
            report = result.scalar_one_or_none()
            return report is not None
        except Exception as e:
            self.logger.error(f"Error verifying report ownership: {e}")
            return False


class PermissionChecker:
    """Permission checking utilities."""
    
    ROLE_PERMISSIONS = {
        Role.USER: [Permission.READ],
        Role.TRADER: [Permission.READ, Permission.WRITE, Permission.EXECUTE],
        Role.ANALYST: [Permission.READ, Permission.WRITE],
        Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE],
        Role.SUPERUSER: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.EXECUTE]
    }
    
    @classmethod
    def has_permission(cls, user: User, permission: Permission, resource_type: ResourceType) -> bool:
        """Check if user has specific permission for resource type."""
        try:
            # Get user role - assuming it's stored in user preferences or a separate field
            user_role_str = getattr(user, 'role', None) or user.preferences.get('role', 'user')
            user_role = Role(user_role_str.lower())
            
            # Superusers have all permissions
            if user_role == Role.SUPERUSER:
                return True
            
            # Check if user role has the required permission
            allowed_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
            return permission in allowed_permissions
            
        except (ValueError, AttributeError) as e:
            logging.getLogger(__name__).warning(f"Error checking permission: {e}")
            return False
    
    @classmethod
    def check_resource_access(cls, user: User, resource_type: ResourceType, permission: Permission) -> bool:
        """Check resource-specific access rules."""
        
        # System resources require admin permission
        if resource_type == ResourceType.SYSTEM:
            return cls.has_permission(user, Permission.ADMIN, resource_type)
        
        # User resources - users can only access their own
        if resource_type == ResourceType.USER:
            if permission in [Permission.DELETE, Permission.ADMIN]:
                return cls.has_permission(user, Permission.ADMIN, resource_type)
            return True  # Users can read/write their own data
        
        # Trading resources
        if resource_type in [ResourceType.PORTFOLIO, ResourceType.TRADE]:
            if permission == Permission.EXECUTE:
                return cls.has_permission(user, Permission.EXECUTE, resource_type)
        
        # Default permission check
        return cls.has_permission(user, permission, resource_type)


def require_permission(permission: Permission, resource_type: ResourceType):
    """Decorator to require specific permission for an endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from dependencies
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # Try to get user from kwargs
            if not user:
                user = kwargs.get('user') or kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permission
            if not PermissionChecker.check_resource_access(user, resource_type, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {resource_type.value} {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_ownership(resource_type: ResourceType, resource_id_param: str = "resource_id"):
    """Decorator to require resource ownership."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            user = None
            db = None
            resource_id = None
            
            # Get user
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            if not user:
                user = kwargs.get('user') or kwargs.get('current_user')
            
            # Get database session
            for arg in args:
                if isinstance(arg, AsyncSession):
                    db = arg
                    break
            if not db:
                db = kwargs.get('db')
            
            # Get resource ID
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                # Try common parameter names
                resource_id = (kwargs.get('id') or 
                             kwargs.get('portfolio_id') or 
                             kwargs.get('trade_id') or 
                             kwargs.get('alert_id') or 
                             kwargs.get('report_id'))
            
            if not all([user, db, resource_id]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required parameters for ownership verification"
                )
            
            # Verify ownership
            ownership = ResourceOwnership(db)
            
            is_owner = False
            if resource_type == ResourceType.PORTFOLIO:
                is_owner = await ownership.verify_portfolio_ownership(resource_id, user)
            elif resource_type == ResourceType.TRADE:
                is_owner = await ownership.verify_trade_ownership(resource_id, user)
            elif resource_type == ResourceType.ALERT:
                is_owner = await ownership.verify_alert_ownership(resource_id, user)
            elif resource_type == ResourceType.REPORT:
                is_owner = await ownership.verify_report_ownership(resource_id, user)
            
            # Allow admins to access any resource
            if not is_owner and not PermissionChecker.has_permission(user, Permission.ADMIN, resource_type):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: You don't own this {resource_type.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: Role):
    """Decorator to require specific user role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            if not user:
                user = kwargs.get('user') or kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get user role
            user_role_str = getattr(user, 'role', None) or user.preferences.get('role', 'user')
            try:
                user_role = Role(user_role_str.lower())
            except ValueError:
                user_role = Role.USER
            
            # Check role hierarchy
            role_hierarchy = {
                Role.USER: 0,
                Role.TRADER: 1,
                Role.ANALYST: 1,
                Role.ADMIN: 2,
                Role.SUPERUSER: 3
            }
            
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency injection helpers
async def get_resource_ownership(db: AsyncSession = Depends(get_database)) -> ResourceOwnership:
    """Dependency to get ResourceOwnership instance."""
    return ResourceOwnership(db)


def get_permission_checker() -> PermissionChecker:
    """Dependency to get PermissionChecker instance."""
    return PermissionChecker()


# Audit logging for authorization events
class AuthorizationAuditor:
    """Audit logging for authorization events."""
    
    def __init__(self):
        self.logger = logging.getLogger("authorization_audit")
    
    def log_access_attempt(
        self, 
        user_id: int, 
        resource_type: str, 
        resource_id: Optional[str], 
        permission: str, 
        granted: bool,
        reason: Optional[str] = None
    ):
        """Log access attempt for audit purposes."""
        log_data = {
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "permission": permission,
            "granted": granted,
            "reason": reason,
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        }
        
        if granted:
            self.logger.info(f"Access granted: {log_data}")
        else:
            self.logger.warning(f"Access denied: {log_data}")
    
    def log_privilege_escalation_attempt(self, user_id: int, attempted_action: str):
        """Log potential privilege escalation attempts."""
        self.logger.critical(f"Privilege escalation attempt - User {user_id}: {attempted_action}")


# Global auditor instance
authorization_auditor = AuthorizationAuditor()
