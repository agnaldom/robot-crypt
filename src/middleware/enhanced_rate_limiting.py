"""
Enhanced rate limiting middleware with retry logic and sophisticated limits.
"""
import time
import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import json

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting."""
    
    def __init__(self):
        # Whitelisted IPs (localhost, development IPs) - more lenient limits
        self.whitelisted_ips = {
            "127.0.0.1",
            "localhost",
            "::1",  # IPv6 localhost
            "0.0.0.0",
            "unknown"  # Handle cases where IP can't be determined
        }
        
        # Default limits per endpoint pattern
        self.endpoint_limits = {
            "/portfolio/wallet/total-value": {"calls": 20, "period": 60},  # More restrictive for expensive operations
            "/portfolio/wallet/value-history": {"calls": 15, "period": 60},
            "/portfolio/metrics": {"calls": 30, "period": 60},
            "/portfolio/performance": {"calls": 25, "period": 60},
            "/portfolio/summary": {"calls": 40, "period": 60},
            "/portfolio/analytics/*": {"calls": 10, "period": 60},  # Very restrictive for analytics
            "/auth/*": {"calls": 5, "period": 60},  # Authentication endpoints
            "default": {"calls": 100, "period": 60}  # Default for other endpoints
        }
        
        # Lenient limits for whitelisted IPs (development/frontend)
        self.whitelisted_endpoint_limits = {
            "/portfolio/wallet/total-value": {"calls": 200, "period": 60},  # Much more lenient for frontend
            "/portfolio/wallet/value-history": {"calls": 150, "period": 60},
            "/portfolio/metrics": {"calls": 300, "period": 60},
            "/portfolio/performance": {"calls": 250, "period": 60},
            "/portfolio/summary": {"calls": 400, "period": 60},
            "/portfolio/analytics/*": {"calls": 100, "period": 60},
            "/auth/*": {"calls": 50, "period": 60},
            "default": {"calls": 1000, "period": 60}
        }
        
        # Burst limits (short-term spikes allowed)
        self.burst_limits = {
            "/portfolio/wallet/total-value": {"calls": 20, "period": 10},
            "/portfolio/wallet/value-history": {"calls": 15, "period": 10},
            "default": {"calls": 50, "period": 10}
        }
        
        # Lenient burst limits for whitelisted IPs
        self.whitelisted_burst_limits = {
            "/portfolio/wallet/total-value": {"calls": 50, "period": 10},  # Much more lenient
            "/portfolio/wallet/value-history": {"calls": 30, "period": 10},
            "default": {"calls": 100, "period": 10}
        }


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with:
    - Per-endpoint limits
    - Burst protection
    - Redis support for distributed systems
    - Exponential backoff suggestions
    - Rate limit headers
    """
    
    def __init__(self, app, redis_url: Optional[str] = None, use_redis: bool = False, whitelisted_ips: Optional[list] = None):
        super().__init__(app)
        self.config = RateLimitConfig()
        
        # Update whitelisted IPs if provided
        if whitelisted_ips:
            self.config.whitelisted_ips.update(whitelisted_ips)
        
        self.use_redis = use_redis and redis_url
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory rate limiting.")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
        
        # In-memory storage (fallback or primary)
        self.client_requests = defaultdict(lambda: defaultdict(deque))
        self.client_burst_requests = defaultdict(lambda: defaultdict(deque))
        
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        endpoint = self._get_endpoint_pattern(request.url.path)
        
        # Check rate limits
        rate_limit_result = await self._check_rate_limits(client_ip, endpoint)
        
        if not rate_limit_result["allowed"]:
            return await self._create_rate_limit_response(rate_limit_result)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_limit_result)
        
        # Log slow requests (potential DoS indicators)
        if processing_time > 2.0:
            logger.warning(f"Slow request from {client_ip}: {processing_time:.2f}s for {request.url.path}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support."""
        # Check various headers in order of preference
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        cf_connecting_ip = request.headers.get("CF-Connecting-IP")  # Cloudflare
        if cf_connecting_ip:
            return cf_connecting_ip
            
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """Map request path to rate limit pattern."""
        for pattern in self.config.endpoint_limits:
            if pattern == "default":
                continue
            
            if pattern.endswith("*"):
                # Wildcard matching
                if path.startswith(pattern[:-1]):
                    return pattern
            elif path == pattern or path.startswith(pattern + "/"):
                return pattern
        
        return "default"
    
    def _is_whitelisted_ip(self, client_ip: str) -> bool:
        """Check if the client IP is whitelisted for more lenient rate limiting."""
        # Check exact match
        if client_ip in self.config.whitelisted_ips:
            return True
        
        # Check if it's a localhost variant
        if client_ip in ['127.0.0.1', 'localhost', '::1', '0.0.0.0', 'unknown']:
            return True
        
        # Check if it's a private IP (for development)
        if client_ip.startswith('192.168.') or client_ip.startswith('10.') or client_ip.startswith('172.'):
            return True
        
        return False
    
    async def _check_rate_limits(self, client_ip: str, endpoint: str) -> Dict:
        """Check both regular and burst rate limits."""
        now = time.time()
        
        # Check if IP is whitelisted for more lenient limits
        is_whitelisted = self._is_whitelisted_ip(client_ip)
        
        if is_whitelisted:
            # Use more lenient limits for whitelisted IPs
            regular_limit = self.config.whitelisted_endpoint_limits.get(endpoint, self.config.whitelisted_endpoint_limits["default"])
            burst_limit = self.config.whitelisted_burst_limits.get(endpoint, self.config.whitelisted_burst_limits["default"])
            logger.debug(f"Using whitelisted limits for IP {client_ip}: regular={regular_limit}, burst={burst_limit}")
        else:
            # Use regular limits for non-whitelisted IPs
            regular_limit = self.config.endpoint_limits.get(endpoint, self.config.endpoint_limits["default"])
            burst_limit = self.config.burst_limits.get(endpoint, self.config.burst_limits["default"])
        
        if self.use_redis:
            return await self._check_redis_limits(client_ip, endpoint, regular_limit, burst_limit, now)
        else:
            return self._check_memory_limits(client_ip, endpoint, regular_limit, burst_limit, now)
    
    async def _check_redis_limits(self, client_ip: str, endpoint: str, regular_limit: Dict, burst_limit: Dict, now: float) -> Dict:
        """Check rate limits using Redis."""
        try:
            # Redis keys
            regular_key = f"rate_limit:{client_ip}:{endpoint}:regular"
            burst_key = f"rate_limit:{client_ip}:{endpoint}:burst"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Check regular limit
            pipe.zremrangebyscore(regular_key, 0, now - regular_limit["period"])
            pipe.zcard(regular_key)
            pipe.zadd(regular_key, {str(now): now})
            pipe.expire(regular_key, regular_limit["period"])
            
            # Check burst limit
            pipe.zremrangebyscore(burst_key, 0, now - burst_limit["period"])
            pipe.zcard(burst_key)
            pipe.zadd(burst_key, {str(now): now})
            pipe.expire(burst_key, burst_limit["period"])
            
            results = pipe.execute()
            
            regular_count = results[1]
            burst_count = results[5]
            
            # Check limits
            regular_exceeded = regular_count >= regular_limit["calls"]
            burst_exceeded = burst_count >= burst_limit["calls"]
            
            if regular_exceeded or burst_exceeded:
                return {
                    "allowed": False,
                    "regular_count": regular_count,
                    "regular_limit": regular_limit["calls"],
                    "regular_reset": int(now + regular_limit["period"]),
                    "burst_count": burst_count,
                    "burst_limit": burst_limit["calls"],
                    "burst_reset": int(now + burst_limit["period"]),
                    "exceeded_type": "burst" if burst_exceeded else "regular"
                }
            
            return {
                "allowed": True,
                "regular_count": regular_count,
                "regular_limit": regular_limit["calls"],
                "regular_reset": int(now + regular_limit["period"]),
                "burst_count": burst_count,
                "burst_limit": burst_limit["calls"],
                "burst_reset": int(now + burst_limit["period"])
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to memory-based limiting
            return self._check_memory_limits(client_ip, endpoint, regular_limit, burst_limit, now)
    
    def _check_memory_limits(self, client_ip: str, endpoint: str, regular_limit: Dict, burst_limit: Dict, now: float) -> Dict:
        """Check rate limits using in-memory storage."""
        # Clean old entries
        regular_requests = self.client_requests[client_ip][endpoint]
        burst_requests = self.client_burst_requests[client_ip][endpoint]
        
        # Remove expired regular requests
        while regular_requests and regular_requests[0] < now - regular_limit["period"]:
            regular_requests.popleft()
        
        # Remove expired burst requests
        while burst_requests and burst_requests[0] < now - burst_limit["period"]:
            burst_requests.popleft()
        
        # Check limits
        regular_exceeded = len(regular_requests) >= regular_limit["calls"]
        burst_exceeded = len(burst_requests) >= burst_limit["calls"]
        
        if regular_exceeded or burst_exceeded:
            return {
                "allowed": False,
                "regular_count": len(regular_requests),
                "regular_limit": regular_limit["calls"],
                "regular_reset": int(now + regular_limit["period"]),
                "burst_count": len(burst_requests),
                "burst_limit": burst_limit["calls"],
                "burst_reset": int(now + burst_limit["period"]),
                "exceeded_type": "burst" if burst_exceeded else "regular"
            }
        
        # Add current request
        regular_requests.append(now)
        burst_requests.append(now)
        
        return {
            "allowed": True,
            "regular_count": len(regular_requests),
            "regular_limit": regular_limit["calls"],
            "regular_reset": int(now + regular_limit["period"]),
            "burst_count": len(burst_requests),
            "burst_limit": burst_limit["calls"],
            "burst_reset": int(now + burst_limit["period"])
        }
    
    async def _create_rate_limit_response(self, rate_limit_result: Dict) -> Response:
        """Create a 429 response with helpful headers and retry information."""
        exceeded_type = rate_limit_result.get("exceeded_type", "regular")
        
        if exceeded_type == "burst":
            retry_after = rate_limit_result["burst_reset"] - int(time.time())
            message = "Rate limit exceeded: Too many requests in short period"
        else:
            retry_after = rate_limit_result["regular_reset"] - int(time.time())
            message = "Rate limit exceeded: Too many requests per minute"
        
        # Calculate suggested backoff
        backoff_seconds = min(max(retry_after, 1), 300)  # Between 1 and 300 seconds
        
        headers = {
            "Content-Type": "application/json",
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(rate_limit_result["regular_limit"]),
            "X-RateLimit-Remaining": str(max(0, rate_limit_result["regular_limit"] - rate_limit_result["regular_count"])),
            "X-RateLimit-Reset": str(rate_limit_result["regular_reset"]),
            "X-RateLimit-Burst-Limit": str(rate_limit_result["burst_limit"]),
            "X-RateLimit-Burst-Remaining": str(max(0, rate_limit_result["burst_limit"] - rate_limit_result["burst_count"])),
            "X-RateLimit-Type": exceeded_type
        }
        
        content = {
            "error": "rate_limit_exceeded",
            "message": message,
            "retry_after_seconds": retry_after,
            "suggested_backoff_seconds": backoff_seconds,
            "limits": {
                "regular": {
                    "limit": rate_limit_result["regular_limit"],
                    "remaining": max(0, rate_limit_result["regular_limit"] - rate_limit_result["regular_count"]),
                    "reset_at": rate_limit_result["regular_reset"]
                },
                "burst": {
                    "limit": rate_limit_result["burst_limit"],
                    "remaining": max(0, rate_limit_result["burst_limit"] - rate_limit_result["burst_count"]),
                    "reset_at": rate_limit_result["burst_reset"]
                }
            },
            "suggestions": [
                "Implement exponential backoff in your client",
                "Cache responses when possible",
                "Batch multiple requests if supported",
                f"Wait at least {backoff_seconds} seconds before retrying"
            ]
        }
        
        # Get client IP for logging (this is called from within the middleware context)
        client_ip = "unknown"
        
        logger.warning(f"Rate limit exceeded - Type: {exceeded_type}, IP: {client_ip}, Retry after: {retry_after}s")
        
        return Response(
            content=json.dumps(content, indent=2),
            status_code=429,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_limit_result: Dict):
        """Add rate limiting headers to successful responses."""
        if rate_limit_result["allowed"]:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["regular_limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, rate_limit_result["regular_limit"] - rate_limit_result["regular_count"])
            )
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result["regular_reset"])
            response.headers["X-RateLimit-Burst-Limit"] = str(rate_limit_result["burst_limit"])
            response.headers["X-RateLimit-Burst-Remaining"] = str(
                max(0, rate_limit_result["burst_limit"] - rate_limit_result["burst_count"])
            )


class RetryableHTTPException(HTTPException):
    """HTTP exception that includes retry information."""
    
    def __init__(self, status_code: int, detail: str, retry_after: int = None, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.retry_after = retry_after


async def handle_rate_limited_request(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Utility function to handle rate-limited requests with exponential backoff.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
    
    Returns:
        Result of the function call
    
    Raises:
        HTTPException: If all retries are exhausted
    """
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except HTTPException as e:
            if e.status_code == 429 and attempt < max_retries:
                # Extract retry-after header if available
                retry_after = None
                if hasattr(e, 'headers') and e.headers:
                    retry_after = e.headers.get('Retry-After')
                
                if retry_after:
                    delay = min(int(retry_after), max_delay)
                else:
                    # Exponential backoff: base_delay * 2^attempt
                    delay = min(base_delay * (2 ** attempt), max_delay)
                
                logger.info(f"Rate limited, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
                continue
            else:
                raise
    
    raise HTTPException(status_code=429, detail="Rate limit exceeded after all retry attempts")
