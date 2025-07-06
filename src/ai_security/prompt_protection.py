"""
AI Security Protection System for Robot-Crypt (OWASP 2025 - A10: AI Security Risks).
Protects against prompt injection, model poisoning, and AI hallucination attacks.
"""
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np


class AISecurityGuard:
    """Advanced protection against AI/ML attacks and vulnerabilities."""
    
    def __init__(self):
        self.logger = logging.getLogger("ai_security")
        
        # Prompt injection patterns (updated for 2025 threats)
        self.blocked_patterns = [
            # Classic prompt injection
            r'ignore\s+(all\s+)?(previous\s+)?instructions',
            r'forget\s+(everything|all|previous)',
            r'new\s+instructions?\s*:',
            r'system\s+prompt\s*:',
            r'jailbreak',
            r'developer\s+mode',
            r'pretend\s+(you\s+are|to\s+be)',
            
            # 2025 Advanced threats
            r'override\s+safety\s+protocols',
            r'bypass\s+content\s+filter',
            r'act\s+as\s+(if\s+)?you\s+(are|were)',
            r'roleplay\s+as',
            r'simulate\s+(being|that\s+you\s+are)',
            r'from\s+now\s+on',
            r'instead\s+of\s+following',
            r'disregard\s+(all|any|previous)',
            
            # Trading-specific AI threats
            r'always\s+(buy|sell)',
            r'guaranteed\s+profit',
            r'risk-free\s+trade',
            r'manipulate\s+(price|market)',
            r'insider\s+information',
            
            # Data exfiltration attempts
            r'show\s+me\s+(your|the)\s+(training|system)',
            r'what\s+(are\s+)?your\s+(instructions|rules)',
            r'reveal\s+(your|the)\s+prompt',
            r'print\s+(your|the)\s+system',
        ]
        
        # Trusted news sources for sentiment analysis
        self.trusted_sources = {
            'Reuters', 'Bloomberg', 'CoinDesk', 'Cointelegraph', 
            'The Block', 'Decrypt', 'CoinMarketCap', 'Binance',
            'Financial Times', 'Wall Street Journal', 'Forbes'
        }
        
        # Model behavior monitoring
        self.output_anomalies = defaultdict(list)
        self.input_patterns = defaultdict(int)
        
        # Confidence thresholds
        self.min_confidence_threshold = 0.3
        self.max_confidence_threshold = 0.95
        
        # Rate limiting for AI requests
        self.ai_request_history = defaultdict(list)
        self.max_ai_requests_per_hour = 100
    
    def sanitize_ai_input(self, text: str, context: str = "general") -> str:
        """
        Sanitize input for AI models with context-aware protection.
        
        Args:
            text: Input text to sanitize
            context: Context of the input (trading, sentiment, general)
        
        Returns:
            Sanitized text safe for AI processing
        
        Raises:
            ValueError: If malicious content is detected
        """
        if not text:
            return ""
        
        # Convert to string and normalize
        text = str(text).strip()
        
        # Detect prompt injection attempts
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                self.logger.warning(f"Prompt injection attempt detected: {pattern}")
                self.logger.warning(f"Suspicious input: {text[:100]}...")
                raise ValueError(f"Input contains potentially malicious content: {pattern}")
        
        # Context-specific validation
        if context == "trading":
            self._validate_trading_input(text)
        elif context == "sentiment":
            self._validate_sentiment_input(text)
        
        # Length limits to prevent DoS
        max_length = self._get_max_length_for_context(context)
        if len(text) > max_length:
            text = text[:max_length]
            self.logger.warning(f"Text truncated due to length limit ({max_length})")
        
        # Remove control characters but preserve basic formatting
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Basic content filtering
        text = self._apply_content_filters(text)
        
        # Log for pattern analysis
        input_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        self.input_patterns[input_hash] += 1
        
        # Alert on repeated identical inputs (possible bot)
        if self.input_patterns[input_hash] > 10:
            self.logger.warning(f"Repeated identical input detected: {input_hash}")
        
        return text
    
    def validate_ai_output(self, output: Dict[str, Any], context: str = "general") -> Tuple[bool, str]:
        """
        Validate AI model output for potential hallucinations and anomalies.
        
        Args:
            output: AI model output to validate
            context: Context of the output
        
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Basic structure validation
            if not isinstance(output, dict):
                return False, "Output must be a dictionary"
            
            # Validate sentiment scores
            if 'sentiment_score' in output:
                score = output['sentiment_score']
                if not isinstance(score, (int, float)):
                    return False, f"Invalid sentiment score type: {type(score)}"
                if not -1 <= score <= 1:
                    return False, f"Sentiment score out of range: {score}"
            
            # Validate confidence scores
            if 'confidence' in output:
                confidence = output['confidence']
                if not isinstance(confidence, (int, float)):
                    return False, f"Invalid confidence type: {type(confidence)}"
                if not 0 <= confidence <= 1:
                    return False, f"Confidence out of range: {confidence}"
                
                # Flag suspiciously high or low confidence
                if confidence < self.min_confidence_threshold:
                    self.logger.warning(f"Unusually low confidence: {confidence}")
                elif confidence > self.max_confidence_threshold:
                    self.logger.warning(f"Suspiciously high confidence: {confidence}")
            
            # Context-specific validation
            if context == "trading":
                return self._validate_trading_output(output)
            elif context == "sentiment":
                return self._validate_sentiment_output(output)
            
            # Track output patterns for anomaly detection
            self._track_output_patterns(output, context)
            
            return True, "Valid output"
            
        except Exception as e:
            self.logger.error(f"Error validating AI output: {e}")
            return False, f"Validation error: {str(e)}"
    
    def detect_model_poisoning(self, data_source: str, data_content: Dict[str, Any]) -> bool:
        """
        Detect potential model poisoning in training/input data.
        
        Args:
            data_source: Source of the data
            data_content: Content to analyze
        
        Returns:
            True if poisoning is detected
        """
        try:
            # Check data source reputation
            if data_source not in self.trusted_sources:
                self.logger.warning(f"Data from untrusted source: {data_source}")
                return True
            
            # Analyze content for suspicious patterns
            if 'title' in data_content:
                title = str(data_content['title'])
                
                # Check for manipulation keywords
                manipulation_keywords = [
                    'guaranteed', 'risk-free', 'insider', 'manipulation',
                    'pump', 'dump', 'scam', 'ponzi', 'scheme'
                ]
                
                for keyword in manipulation_keywords:
                    if keyword.lower() in title.lower():
                        self.logger.warning(f"Suspicious keyword in data: {keyword}")
                        return True
            
            # Check for data consistency
            if 'sentiment' in data_content and 'title' in data_content:
                title_sentiment = self._basic_sentiment_analysis(data_content['title'])
                reported_sentiment = data_content['sentiment']
                
                # Flag if reported sentiment contradicts title analysis
                if abs(title_sentiment - self._sentiment_to_score(reported_sentiment)) > 0.5:
                    self.logger.warning("Sentiment mismatch detected - possible poisoning")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in model poisoning detection: {e}")
            return True  # Err on the side of caution
    
    def apply_ai_rate_limiting(self, user_id: str, request_type: str = "general") -> bool:
        """
        Apply rate limiting for AI requests to prevent abuse.
        
        Args:
            user_id: User identifier
            request_type: Type of AI request
        
        Returns:
            True if request is allowed
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old requests
        user_key = f"{user_id}:{request_type}"
        self.ai_request_history[user_key] = [
            req_time for req_time in self.ai_request_history[user_key]
            if req_time > hour_ago
        ]
        
        # Check rate limit
        recent_requests = len(self.ai_request_history[user_key])
        if recent_requests >= self.max_ai_requests_per_hour:
            self.logger.warning(f"AI rate limit exceeded for user {user_id}: {recent_requests} requests")
            return False
        
        # Record this request
        self.ai_request_history[user_key].append(now)
        return True
    
    def _validate_trading_input(self, text: str):
        """Validate trading-specific input."""
        # Check for market manipulation language
        manipulation_patterns = [
            r'pump\s+(and\s+)?dump',
            r'buy\s+now\s+before',
            r'guaranteed\s+(profit|return)',
            r'insider\s+(info|information|tip)',
            r'manipulation\s+strategy'
        ]
        
        for pattern in manipulation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError(f"Trading manipulation language detected: {pattern}")
    
    def _validate_sentiment_input(self, text: str):
        """Validate sentiment analysis input."""
        # Check for sentiment manipulation
        if len(text) > 1000:
            raise ValueError("Sentiment input too long")
        
        # Check for repeated patterns (spam)
        words = text.lower().split()
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
            raise ValueError("Input appears to be spam or repetitive")
    
    def _validate_trading_output(self, output: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate trading-specific output."""
        # Check for unrealistic predictions
        if 'predicted_price' in output:
            price = output['predicted_price']
            if price <= 0:
                return False, "Invalid price prediction"
            
            # Check for unrealistic price movements
            if 'current_price' in output:
                current = output['current_price']
                change = abs(price - current) / current
                if change > 0.5:  # 50% change
                    return False, f"Unrealistic price prediction: {change:.2%} change"
        
        # Validate trading signals
        if 'signal' in output:
            valid_signals = ['buy', 'sell', 'hold', 'neutral']
            if output['signal'].lower() not in valid_signals:
                return False, f"Invalid trading signal: {output['signal']}"
        
        return True, "Valid trading output"
    
    def _validate_sentiment_output(self, output: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate sentiment analysis output."""
        # Check sentiment distribution
        if 'sentiment_distribution' in output:
            dist = output['sentiment_distribution']
            if isinstance(dist, dict):
                total = sum(dist.values())
                if abs(total - 1.0) > 0.1:  # Should sum to ~1.0
                    return False, f"Invalid sentiment distribution sum: {total}"
        
        # Validate article count
        if 'article_count' in output:
            count = output['article_count']
            if not isinstance(count, int) or count < 0:
                return False, f"Invalid article count: {count}"
            if count > 1000:  # Suspiciously high
                return False, f"Unrealistic article count: {count}"
        
        return True, "Valid sentiment output"
    
    def _get_max_length_for_context(self, context: str) -> int:
        """Get maximum allowed length for different contexts."""
        limits = {
            "trading": 500,
            "sentiment": 1000,
            "general": 2000
        }
        return limits.get(context, 1000)
    
    def _apply_content_filters(self, text: str) -> str:
        """Apply content filtering to remove harmful content."""
        # Remove URLs to prevent SSRF
        text = re.sub(r'https?://[^\s]+', '[URL_REMOVED]', text)
        
        # Remove potential code injection
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _basic_sentiment_analysis(self, text: str) -> float:
        """Basic sentiment analysis for consistency checking."""
        positive_words = ['good', 'great', 'excellent', 'positive', 'bullish', 'up', 'rise', 'gain']
        negative_words = ['bad', 'terrible', 'negative', 'bearish', 'down', 'fall', 'drop', 'loss']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment_score))
    
    def _sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment string to numeric score."""
        sentiment_map = {
            'positive': 0.5,
            'negative': -0.5,
            'neutral': 0.0,
            'bullish': 0.7,
            'bearish': -0.7
        }
        return sentiment_map.get(sentiment.lower(), 0.0)
    
    def _track_output_patterns(self, output: Dict[str, Any], context: str):
        """Track output patterns for anomaly detection."""
        # Create a fingerprint of the output
        output_str = json.dumps(output, sort_keys=True, default=str)
        output_hash = hashlib.sha256(output_str.encode()).hexdigest()[:16]
        
        # Track in time window
        now = datetime.now()
        self.output_anomalies[context].append({
            'hash': output_hash,
            'timestamp': now,
            'output': output
        })
        
        # Clean old entries (keep last 24 hours)
        day_ago = now - timedelta(days=1)
        self.output_anomalies[context] = [
            entry for entry in self.output_anomalies[context]
            if entry['timestamp'] > day_ago
        ]
        
        # Check for anomalies
        recent_hashes = [entry['hash'] for entry in self.output_anomalies[context][-10:]]
        if len(set(recent_hashes)) == 1 and len(recent_hashes) > 5:
            self.logger.warning(f"Identical outputs detected in {context} - possible model issue")


# Global AI security instance
ai_security_guard = AISecurityGuard()


# Decorator for AI-protected endpoints
def ai_security_protected(context: str = "general"):
    """Decorator to protect endpoints with AI security."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Apply rate limiting if user is available
            user_id = "anonymous"
            for arg in kwargs.values():
                if hasattr(arg, 'id'):
                    user_id = str(arg.id)
                    break
            
            if not ai_security_guard.apply_ai_rate_limiting(user_id, context):
                raise ValueError("AI request rate limit exceeded")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
