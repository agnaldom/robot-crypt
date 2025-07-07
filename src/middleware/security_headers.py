"""
Security headers middleware for Robot-Crypt API.
"""
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de segurança - ajustado para permitir Swagger UI
        # Check if this is a docs request to allow more permissive CSP
        is_docs_request = request.url.path.startswith('/docs') or request.url.path.startswith('/redoc') or request.url.path.startswith('/openapi.json')
        
        if is_docs_request:
            # More permissive CSP for documentation
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
                "connect-src 'self' https://cdn.jsdelivr.net; "
                "frame-src 'none'; "
                "object-src 'none'"
            )
        else:
            # Strict CSP for regular pages
            csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
        
        # Adjust cache control for docs
        cache_control = "public, max-age=300" if is_docs_request else "no-store, no-cache, must-revalidate, private"
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": csp,
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cache-Control": cache_control
        }
        
        # Aplicar headers
        for header, value in security_headers.items():
            response.headers[header] = value
            
        # Remover headers que podem expor informações
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
            
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        now = time.time()
        
        # Limpar entradas antigas
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < self.period
        ]
        
        # Verificar limite
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # Adicionar timestamp atual
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"


class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            # SQL Injection patterns (more specific to avoid false positives)
            r"(?i)\b(union\s+select|insert\s+into|update\s+set|delete\s+from|drop\s+table|create\s+table|alter\s+table)\b",
            # XSS patterns
            r"(?i)(<script|javascript:|vbscript:|onload=|onerror=)",
            # Path traversal
            r"(\.\./|\.\.\\\|%2e%2e%2f|%2e%2e%5c)",
            # Command injection
            r"(?i)(;\s*rm\s|;\s*cat\s|\&\&\s*rm\s|\|\|\s*rm\s|`\s*rm\s|\$\(\s*rm|\${\s*rm)"
        ]
        
        # Paths that should be excluded from security scanning
        self.excluded_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/static/",
            "/health",
            "/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # Verificar padrões suspeitos na URL e query parameters
        suspicious = self._check_suspicious_content(request)
        if suspicious:
            logger.warning(f"Suspicious request from {client_ip}: {request.url}")
            return Response(
                content='{"detail": "Request blocked by security policy"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )
        
        # Processar request normal
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log requests demoradas (possível DoS)
        if process_time > 5.0:
            logger.warning(f"Slow request from {client_ip}: {process_time:.2f}s for {request.url}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _check_suspicious_content(self, request: Request) -> bool:
        """Check for suspicious patterns in request."""
        import re
        
        # Check if path should be excluded from security scanning
        request_path = request.url.path
        for excluded_path in self.excluded_paths:
            if request_path.startswith(excluded_path):
                return False
        
        # Verificar URL path
        for pattern in self.suspicious_patterns:
            if re.search(pattern, str(request.url)):
                return True
        
        # Verificar headers
        for header_value in request.headers.values():
            for pattern in self.suspicious_patterns:
                if re.search(pattern, header_value):
                    return True
        
        return False
