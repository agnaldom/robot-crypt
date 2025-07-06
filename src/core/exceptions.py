"""
Custom exceptions for Robot-Crypt API.

Provides standardized exception classes for different error scenarios.
"""

from typing import Any, Dict, Optional


class RobotCryptBaseException(Exception):
    """Base exception class for Robot-Crypt API."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(RobotCryptBaseException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            details: Additional validation details
        """
        if field:
            message = f"Validation failed for field '{field}': {message}"
        
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(message, "VALIDATION_ERROR", error_details)


class NotFoundError(RobotCryptBaseException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource (e.g., "User", "Alert")
            resource_id: ID of the missing resource
            details: Additional details
        """
        if resource_type and resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id is not None:
            error_details["resource_id"] = str(resource_id)
        
        super().__init__(message, "NOT_FOUND", error_details)


class BadRequestError(RobotCryptBaseException):
    """Raised when the request is malformed or invalid."""
    
    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize bad request error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, "BAD_REQUEST", details)


class UnauthorizedError(RobotCryptBaseException):
    """Raised when authentication is required but not provided or invalid."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize unauthorized error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, "UNAUTHORIZED", details)


class ForbiddenError(RobotCryptBaseException):
    """Raised when the user doesn't have permission to access a resource."""
    
    def __init__(
        self,
        message: str = "Access forbidden",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize forbidden error.
        
        Args:
            message: Error message
            resource: Resource being accessed
            action: Action being attempted
            details: Additional error details
        """
        if resource and action:
            message = f"Permission denied: cannot {action} {resource}"
        
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
        if action:
            error_details["action"] = action
        
        super().__init__(message, "FORBIDDEN", error_details)


class ConflictError(RobotCryptBaseException):
    """Raised when a resource conflict occurs (e.g., duplicate entries)."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize conflict error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, "CONFLICT", details)


class TooManyRequestsError(RobotCryptBaseException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        
        super().__init__(message, "TOO_MANY_REQUESTS", error_details)


class InternalServerError(RobotCryptBaseException):
    """Raised when an internal server error occurs."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize internal server error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, "INTERNAL_SERVER_ERROR", details)


class ExternalServiceError(RobotCryptBaseException):
    """Raised when an external service (API, database) fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize external service error.
        
        Args:
            message: Error message
            service_name: Name of the external service
            status_code: HTTP status code from service
            details: Additional error details
        """
        if service_name:
            message = f"External service '{service_name}' error: {message}"
        
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", error_details)


class TradingError(RobotCryptBaseException):
    """Raised when trading operations fail."""
    
    def __init__(
        self,
        message: str = "Trading operation failed",
        operation: Optional[str] = None,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize trading error.
        
        Args:
            message: Error message
            operation: Trading operation (buy, sell, etc.)
            symbol: Trading symbol
            details: Additional error details
        """
        if operation and symbol:
            message = f"Trading error ({operation} {symbol}): {message}"
        
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        if symbol:
            error_details["symbol"] = symbol
        
        super().__init__(message, "TRADING_ERROR", error_details)


class DataError(RobotCryptBaseException):
    """Raised when data processing or validation fails."""
    
    def __init__(
        self,
        message: str = "Data processing error",
        data_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize data error.
        
        Args:
            message: Error message
            data_type: Type of data being processed
            details: Additional error details
        """
        if data_type:
            message = f"Data error ({data_type}): {message}"
        
        error_details = details or {}
        if data_type:
            error_details["data_type"] = data_type
        
        super().__init__(message, "DATA_ERROR", error_details)


class ConfigurationError(RobotCryptBaseException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that's invalid
            details: Additional error details
        """
        if config_key:
            message = f"Configuration error for '{config_key}': {message}"
        
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        
        super().__init__(message, "CONFIGURATION_ERROR", error_details)


# Convenience functions for raising common errors
def not_found(
    resource_type: str,
    resource_id: Any,
    message: Optional[str] = None
) -> NotFoundError:
    """Create a NotFoundError for a specific resource."""
    if not message:
        message = f"{resource_type} with ID {resource_id} not found"
    
    return NotFoundError(
        message=message,
        resource_type=resource_type,
        resource_id=resource_id
    )


def bad_request(
    message: str,
    field: Optional[str] = None,
    **details
) -> BadRequestError:
    """Create a BadRequestError with optional field information."""
    error_details = details
    if field:
        error_details["field"] = field
    
    return BadRequestError(message=message, details=error_details)


def forbidden(
    resource: str,
    action: str = "access",
    message: Optional[str] = None
) -> ForbiddenError:
    """Create a ForbiddenError for resource access."""
    if not message:
        message = f"Permission denied: cannot {action} {resource}"
    
    return ForbiddenError(
        message=message,
        resource=resource,
        action=action
    )


def validation_error(
    field: str,
    message: str,
    value: Optional[Any] = None
) -> ValidationError:
    """Create a ValidationError for a specific field."""
    return ValidationError(
        message=message,
        field=field,
        value=value
    )


def external_service_error(
    service_name: str,
    message: str,
    status_code: Optional[int] = None
) -> ExternalServiceError:
    """Create an ExternalServiceError for a specific service."""
    return ExternalServiceError(
        message=message,
        service_name=service_name,
        status_code=status_code
    )


def trading_error(
    operation: str,
    symbol: str,
    message: str
) -> TradingError:
    """Create a TradingError for a specific operation."""
    return TradingError(
        message=message,
        operation=operation,
        symbol=symbol
    )
