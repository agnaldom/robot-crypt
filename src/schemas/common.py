"""
Common schemas for Robot-Crypt API.

Provides reusable schema classes for API responses, pagination, and common data structures.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field, ConfigDict


# Generic type for paginated responses
T = TypeVar('T')


class BaseResponse(BaseModel):
    """Base response schema for all API responses."""
    
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )


class SuccessResponse(BaseResponse):
    """Schema for successful operation responses."""
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    trace_id: Optional[str] = Field(None, description="Request trace ID for debugging")


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[str] = Field(None, description="Invalid value")


class ValidationErrorResponse(ErrorResponse):
    """Schema for validation error responses."""
    
    error: str = Field(default="VALIDATION_ERROR", description="Error code")
    validation_errors: List[ValidationErrorDetail] = Field(
        default_factory=list, 
        description="Detailed validation errors"
    )


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    
    page: int = Field(
        default=1, 
        ge=1, 
        description="Page number (1-based)"
    )
    page_size: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Number of items per page (1-100)"
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginationMeta(BaseModel):
    """Schema for pagination metadata."""
    
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_previous: bool = Field(..., description="Whether there's a previous page")
    
    @classmethod
    def from_params(
        cls, 
        params: PaginationParams, 
        total_items: int
    ) -> "PaginationMeta":
        """Create pagination metadata from parameters and total count."""
        total_pages = (total_items + params.page_size - 1) // params.page_size
        
        return cls(
            page=params.page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )


class PaginatedResponse(BaseResponse, Generic[T]):
    """Schema for paginated responses."""
    
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls, 
        items: List[T], 
        params: PaginationParams, 
        total_items: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        return cls(
            items=items,
            pagination=PaginationMeta.from_params(params, total_items)
        )


class FilterParams(BaseModel):
    """Base schema for filter parameters."""
    
    search: Optional[str] = Field(
        None, 
        description="Search term for text fields",
        min_length=1,
        max_length=100
    )
    sort_by: Optional[str] = Field(
        None, 
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="asc", 
        description="Sort order (asc or desc)",
        pattern="^(asc|desc)$"
    )
    created_after: Optional[datetime] = Field(
        None, 
        description="Filter items created after this date"
    )
    created_before: Optional[datetime] = Field(
        None, 
        description="Filter items created before this date"
    )


class DateRangeFilter(BaseModel):
    """Schema for date range filters."""
    
    start_date: Optional[datetime] = Field(
        None, 
        description="Start date for filtering"
    )
    end_date: Optional[datetime] = Field(
        None, 
        description="End date for filtering"
    )
    
    def model_post_init(self) -> None:
        """Validate date range after initialization."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")


class StatusFilter(BaseModel):
    """Schema for status-based filters."""
    
    status: Optional[str] = Field(
        None, 
        description="Filter by status"
    )
    is_active: Optional[bool] = Field(
        None, 
        description="Filter by active status"
    )


class HealthCheckResponse(BaseResponse):
    """Schema for health check responses."""
    
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    checks: Optional[Dict[str, Any]] = Field(None, description="Detailed health check results")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")


class MetricsResponse(BaseResponse):
    """Schema for metrics and statistics responses."""
    
    metrics: Dict[str, Union[int, float, str]] = Field(..., description="Metrics data")
    period: Optional[str] = Field(None, description="Metrics period (e.g., '24h', '7d')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")


class BulkOperationResponse(BaseResponse):
    """Schema for bulk operation responses."""
    
    total_requested: int = Field(..., description="Total number of operations requested")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Details of failed operations")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requested == 0:
            return 0.0
        return (self.successful / self.total_requested) * 100


class FileUploadResponse(BaseResponse):
    """Schema for file upload responses."""
    
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    file_id: Optional[str] = Field(None, description="Unique file identifier")
    download_url: Optional[str] = Field(None, description="Download URL")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")


class AsyncTaskResponse(BaseResponse):
    """Schema for asynchronous task responses."""
    
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status (pending, running, completed, failed)")
    progress: Optional[float] = Field(None, description="Task progress (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class ConfigurationItem(BaseModel):
    """Schema for configuration items."""
    
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    is_sensitive: bool = Field(default=False, description="Whether the value is sensitive")
    category: Optional[str] = Field(None, description="Configuration category")


class ConfigurationResponse(BaseResponse):
    """Schema for configuration responses."""
    
    configurations: List[ConfigurationItem] = Field(..., description="List of configurations")
    environment: str = Field(..., description="Current environment")
    version: str = Field(..., description="Configuration version")


class PermissionCheck(BaseModel):
    """Schema for permission check results."""
    
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(..., description="Action being performed")
    allowed: bool = Field(..., description="Whether the action is allowed")
    reason: Optional[str] = Field(None, description="Reason for denial (if not allowed)")


class PermissionResponse(BaseResponse):
    """Schema for permission check responses."""
    
    permissions: List[PermissionCheck] = Field(..., description="Permission check results")
    user_id: Optional[int] = Field(None, description="User ID being checked")
    role: Optional[str] = Field(None, description="User role")


# Utility functions for creating common responses
def success_response(
    message: str, 
    data: Optional[Dict[str, Any]] = None
) -> SuccessResponse:
    """Create a success response."""
    return SuccessResponse(message=message, data=data)


def error_response(
    error: str, 
    message: str, 
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        error=error, 
        message=message, 
        details=details,
        trace_id=trace_id
    )


def validation_error_response(
    message: str, 
    validation_errors: List[ValidationErrorDetail]
) -> ValidationErrorResponse:
    """Create a validation error response."""
    return ValidationErrorResponse(
        message=message,
        validation_errors=validation_errors
    )


def paginated_response(
    items: List[T], 
    params: PaginationParams, 
    total_items: int
) -> PaginatedResponse[T]:
    """Create a paginated response."""
    return PaginatedResponse.create(items, params, total_items)


def health_response(
    status: str, 
    service: str, 
    version: str,
    checks: Optional[Dict[str, Any]] = None,
    uptime: Optional[float] = None
) -> HealthCheckResponse:
    """Create a health check response."""
    return HealthCheckResponse(
        status=status,
        service=service,
        version=version,
        checks=checks,
        uptime=uptime
    )
