"""
Security utilities for Robot-Crypt API.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import time
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database.database import get_database
from src.schemas.token import TokenData
from src.schemas.user import User
from src.services.user_service import UserService

# Password hashing with Argon2
pwd_hasher = PasswordHasher()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        pwd_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_hasher.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token with enhanced security."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    
    # Adicionar claims de segurança
    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at
        "nbf": now,  # Not before
        "iss": "robot-crypt-api",  # Issuer
        "aud": "robot-crypt-client"  # Audience
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_jwt_with_validation(token: str) -> dict:
    """Decode JWT with comprehensive security validation."""
    logger = logging.getLogger(__name__)
    
    try:
        # Decodificar com validação rigorosa
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True, 
                "verify_iat": True,
                "verify_nbf": True,
                "verify_aud": True,
                "verify_iss": True
            },
            audience="robot-crypt-client",
            issuer="robot-crypt-api"
        )
        
        # Validar claims obrigatórios
        required_claims = ["sub", "exp", "iat", "nbf", "iss", "aud"]
        missing_claims = [claim for claim in required_claims if claim not in payload]
        if missing_claims:
            logger.warning(f"JWT missing required claims: {missing_claims}")
            raise JWTError(f"Missing required claims: {missing_claims}")
            
        # Validar timestamp issued at não está no futuro
        if payload.get("iat", 0) > time.time() + 60:  # Tolerância de 60 segundos
            logger.warning("JWT issued in the future")
            raise JWTError("Token issued in the future")
            
        # Validar que o token não é muito antigo (proteção contra replay)
        max_age = 24 * 60 * 60  # 24 horas
        if time.time() - payload.get("iat", 0) > max_age:
            logger.warning("JWT too old")
            raise JWTError("Token too old")
            
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise


async def authenticate_user(
    user_service: UserService, username: str, password: str
) -> Optional[User]:
    """Authenticate a user."""
    user = await user_service.get_by_email(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_database),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current authenticated user with enhanced validation."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Usar validação JWT rigorosa
        payload = decode_jwt_with_validation(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id))
    except (JWTError, ValueError) as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Authentication failed: {str(e)}")
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    # Verificar se o usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_user_websocket(
    token: str, db: AsyncSession
) -> Optional[User]:
    """Get the current authenticated user for WebSocket connections."""
    try:
        # Usar validação JWT rigorosa
        payload = decode_jwt_with_validation(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        user_service = UserService(db)
        user = await user_service.get(int(user_id))
        if user is None:
            return None
        
        # Verificar se o usuário está ativo
        if not user.is_active:
            return None
        
        return user
    except (JWTError, ValueError) as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"WebSocket authentication failed: {str(e)}")
        return None
