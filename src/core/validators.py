"""
Security validators for Robot-Crypt API.
"""
import re
import ipaddress
from typing import Any, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def validate_trading_symbol(symbol: str) -> bool:
    """Validate trading symbol format (e.g., BTC/USDT)."""
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Formato esperado: BASE/QUOTE onde BASE e QUOTE são strings alfabéticas
    pattern = r'^[A-Z]{2,10}/[A-Z]{2,10}$'
    return bool(re.match(pattern, symbol.upper()))


def validate_api_key(api_key: str) -> bool:
    """Validate Binance API key format."""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Binance API keys são alfanuméricos com exatamente 64 caracteres
    pattern = r'^[A-Za-z0-9]{64}$'
    return bool(re.match(pattern, api_key))


def validate_api_secret(api_secret: str) -> bool:
    """Validate Binance API secret format."""
    if not api_secret or not isinstance(api_secret, str):
        return False
    
    # Binance API secrets são alfanuméricos com exatamente 64 caracteres
    pattern = r'^[A-Za-z0-9]{64}$'
    return bool(re.match(pattern, api_secret))


def sanitize_input(data: Any, max_length: int = 1000) -> Any:
    """Sanitize input data to prevent injection attacks."""
    if isinstance(data, str):
        # Remover caracteres potencialmente perigosos
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        # Limitar tamanho
        data = data[:max_length]
        
        # Remover múltiplos espaços em branco
        data = re.sub(r'\s+', ' ', data).strip()
        
    elif isinstance(data, dict):
        # Recursivamente sanitizar valores do dicionário
        return {key: sanitize_input(value, max_length) for key, value in data.items()}
    
    elif isinstance(data, list):
        # Recursivamente sanitizar itens da lista
        return [sanitize_input(item, max_length) for item in data]
    
    return data


def validate_url_security(url: str, allowed_domains: List[str] = None) -> bool:
    """Validate URL to prevent SSRF attacks."""
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        
        # Apenas HTTPS permitido
        if parsed.scheme != 'https':
            logger.warning(f"Non-HTTPS URL rejected: {url}")
            return False
        
        # Verificar se o domínio é permitido
        if allowed_domains:
            if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
                logger.warning(f"Domain not in allowlist: {parsed.netloc}")
                return False
        
        # Verificar se não é um IP privado/loopback
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                logger.warning(f"Private/loopback IP rejected: {parsed.hostname}")
                return False
        except (ValueError, ipaddress.AddressValueError):
            # Não é um IP, continuar com a validação de domínio
            pass
        
        # Verificar se o hostname é válido
        if not parsed.hostname:
            logger.warning(f"Invalid hostname in URL: {url}")
            return False
        
        # Verificar padrões suspeitos no hostname
        suspicious_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'0\.0\.0\.0',
            r'::1',
            r'metadata\.google\.internal',
            r'169\.254\.',  # Link-local
            r'10\.',        # Private class A
            r'172\.(1[6-9]|2[0-9]|3[01])\.',  # Private class B
            r'192\.168\.',  # Private class C
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, parsed.hostname, re.IGNORECASE):
                logger.warning(f"Suspicious hostname pattern detected: {parsed.hostname}")
                return False
        
        return True
        
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    
    # Padrão básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 254


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """Validate password strength and return issues."""
    if not password or not isinstance(password, str):
        return False, ["Password is required"]
    
    issues = []
    
    # Verificar comprimento mínimo
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    # Verificar se contém letra minúscula
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    # Verificar se contém letra maiúscula
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    # Verificar se contém número
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one number")
    
    # Verificar se contém caractere especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    # Verificar se não é muito comum
    common_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123', 
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    if password.lower() in common_passwords:
        issues.append("Password is too common")
    
    return len(issues) == 0, issues


def validate_amount(amount: Any) -> bool:
    """Validate trading amount."""
    try:
        amount_float = float(amount)
        return 0 < amount_float <= 1000000  # Limite razoável
    except (ValueError, TypeError):
        return False


def validate_percentage(percentage: Any) -> bool:
    """Validate percentage values."""
    try:
        percentage_float = float(percentage)
        return 0 <= percentage_float <= 100
    except (ValueError, TypeError):
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    if not filename or not isinstance(filename, str):
        return "unknown"
    
    # Remover caracteres perigosos
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remover sequências de path traversal
    filename = re.sub(r'\.\.', '', filename)
    
    # Limitar tamanho
    filename = filename[:255]
    
    # Se ficou vazio, usar nome padrão
    if not filename.strip():
        filename = "unnamed_file"
    
    return filename


def validate_json_structure(data: dict, required_fields: List[str] = None) -> tuple[bool, str]:
    """Validate JSON structure and required fields."""
    if not isinstance(data, dict):
        return False, "Data must be a JSON object"
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Verificar profundidade máxima para evitar ataques de DoS
    def check_depth(obj, max_depth=10, current_depth=0):
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            return all(check_depth(v, max_depth, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return all(check_depth(item, max_depth, current_depth + 1) for item in obj)
        
        return True
    
    if not check_depth(data):
        return False, "JSON structure too deep"
    
    return True, "Valid"
