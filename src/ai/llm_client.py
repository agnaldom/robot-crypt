#!/usr/bin/env python3
"""
Unified LLM Client for Robot-Crypt
Supports OpenAI GPT and Google Gemini models
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
import tiktoken

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from src.core.config import settings

# DeepSeek uses OpenAI-compatible API
DEEPSEEK_AVAILABLE = OPENAI_AVAILABLE

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Estrutura padronizada para respostas dos LLMs"""
    content: str
    model: str
    provider: str
    tokens_used: int
    cost_estimate: float
    timestamp: datetime
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMClient:
    """Cliente unificado para múltiplos provedores de LLM"""
    
    def __init__(self, provider: str = None):
        """
        Initialize LLM client
        
        Args:
            provider: 'openai', 'gemini', or 'auto' for automatic selection
        """
        self.logger = logging.getLogger("robot-crypt.llm_client")
        
        # Determine provider
        self.provider = provider or os.getenv("AI_PROVIDER", "auto")
        self.model = os.getenv("AI_MODEL", "")
        
        # Token counting
        self.token_counter = None
        
        # Safety settings for Gemini (configurable via environment variables)
        self.gemini_safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": os.getenv("GEMINI_SAFETY_HARASSMENT", "BLOCK_ONLY_HIGH")
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": os.getenv("GEMINI_SAFETY_HATE_SPEECH", "BLOCK_ONLY_HIGH")
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": os.getenv("GEMINI_SAFETY_SEXUALLY_EXPLICIT", "BLOCK_ONLY_HIGH")
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": os.getenv("GEMINI_SAFETY_DANGEROUS_CONTENT", "BLOCK_ONLY_HIGH")
            }
        ]
        
        # Cost tracking
        self.costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1k tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-pro-vision": {"input": 0.00025, "output": 0.0005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},  # Similar to 1.5-flash
            "deepseek-chat": {"input": 0.0001, "output": 0.0002},  # DeepSeek costs
            "deepseek-coder": {"input": 0.0001, "output": 0.0002}
        }
        
        # Initialize clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize available LLM clients"""
        self.openai_client = None
        self.gemini_client = None
        self.deepseek_client = None
        
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                    if not self.model and self.provider in ["openai", "auto"]:
                        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
                    
                    # Initialize token counter
                    try:
                        self.token_counter = tiktoken.encoding_for_model("gpt-4")
                    except:
                        self.token_counter = tiktoken.get_encoding("cl100k_base")
                    
                    self.logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI: {e}")
        
        # Initialize Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                    # Initialize without safety settings to avoid overly restrictive filtering
                    self.gemini_client = genai.GenerativeModel(gemini_model)
                    if not self.model and self.provider in ["gemini", "auto"]:
                        self.model = gemini_model
                    
                    self.logger.info("Gemini client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Gemini: {e}")
        
        # Initialize DeepSeek
        if DEEPSEEK_AVAILABLE:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            if api_key:
                try:
                    self.deepseek_client = openai.AsyncOpenAI(
                        api_key=api_key, 
                        base_url=base_url
                    )
                    if not self.model and self.provider in ["deepseek", "auto"]:
                        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
                    self.logger.info("DeepSeek client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize DeepSeek: {e}")
        
        # Auto-select provider
        if self.provider == "auto":
            if self.openai_client:
                self.provider = "openai"
                self.model = self.model or os.getenv("OPENAI_MODEL", "gpt-4-turbo")
            elif self.gemini_client:
                self.provider = "gemini" 
                self.model = self.model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            elif self.deepseek_client:
                self.provider = "deepseek"
                self.model = self.model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            else:
                raise ValueError("No LLM providers available. Please configure API keys.")
        
        self.logger.info(f"LLM Client configured: {self.provider} with model {self.model}")
    
    async def chat(self, 
                   messages: Union[str, List[Dict[str, str]]], 
                   system_prompt: Optional[str] = None,
                   temperature: float = 0.1,
                   max_tokens: Optional[int] = None) -> LLMResponse:
        """
        Send chat completion request
        
        Args:
            messages: Message string or list of messages
            system_prompt: Optional system prompt
            temperature: Model temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse object
        """
        try:
            # Prepare messages
            if isinstance(messages, str):
                formatted_messages = []
                if system_prompt:
                    formatted_messages.append({"role": "system", "content": system_prompt})
                formatted_messages.append({"role": "user", "content": messages})
            else:
                formatted_messages = messages.copy()
                if system_prompt and (not formatted_messages or formatted_messages[0]["role"] != "system"):
                    formatted_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Route to appropriate provider
            if self.provider == "openai" and self.openai_client:
                return await self._openai_chat(formatted_messages, temperature, max_tokens)
            elif self.provider == "gemini" and self.gemini_client:
                return await self._gemini_chat(formatted_messages, temperature, max_tokens)
            elif self.provider == "deepseek" and self.deepseek_client:
                return await self._deepseek_chat(formatted_messages, temperature, max_tokens)
            else:
                raise ValueError(f"Provider {self.provider} not available")
                
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            raise
    
    async def _openai_chat(self, messages: List[Dict], temperature: float, max_tokens: Optional[int]) -> LLMResponse:
        """OpenAI chat completion"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 1000
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Estimate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost("openai", input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="openai",
                tokens_used=tokens_used,
                cost_estimate=cost,
                timestamp=datetime.now(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI request failed: {e}")
            raise
    
    async def _gemini_chat(self, messages: List[Dict], temperature: float, max_tokens: Optional[int]) -> LLMResponse:
        """Gemini chat completion with safety filter handling"""
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_gemini_prompt(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 1000
            )
            
            # First attempt with default safety settings
            response = await self._try_gemini_request(prompt, generation_config, self.gemini_safety_settings)
            
            # If blocked by safety filters, try with relaxed settings
            if response is None:
                self.logger.info("Retrying with relaxed safety settings...")
                relaxed_safety_settings = self._get_relaxed_safety_settings()
                response = await self._try_gemini_request(prompt, generation_config, relaxed_safety_settings)
            
            # If still blocked, try with minimal safety settings
            if response is None:
                self.logger.info("Retrying with minimal safety settings...")
                minimal_safety_settings = self._get_minimal_safety_settings()
                response = await self._try_gemini_request(prompt, generation_config, minimal_safety_settings)
            
            # If all attempts fail, create a fallback response
            if response is None:
                self.logger.warning("All Gemini safety attempts failed, creating fallback response")
                return self._create_safety_fallback_response(prompt)
            
            content, finish_reason = self._extract_gemini_content(response)
            
            if content is None or content.strip() == "":
                error_message = f"Response text is empty or invalid (finish_reason: {finish_reason})"
                self.logger.error(error_message)
                
                # Log the specific finish_reason for debugging
                self.logger.warning(f"Gemini response blocked or failed (finish_reason: {finish_reason})")
                raise ValueError(f"Gemini completion failed: {error_message}")
            
            # Estimate tokens (Gemini doesn't return token count directly)
            tokens_used = self._estimate_tokens(prompt + content)
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = tokens_used - input_tokens
            
            cost = self._calculate_cost("gemini", input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="gemini",
                tokens_used=tokens_used,
                cost_estimate=cost,
                timestamp=datetime.now(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "safety_ratings": getattr(response, 'prompt_feedback', None)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Gemini request failed: {e}")
            raise
    
    async def _try_gemini_request(self, prompt: str, generation_config, safety_settings) -> Optional[Any]:
        """Try Gemini request with specific safety settings"""
        try:
            # Create a new client with specific safety settings
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            client = genai.GenerativeModel(
                model_name=gemini_model,
                safety_settings=safety_settings
            )
            
            response = await asyncio.to_thread(
                client.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            # Check if response was blocked
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                
                # Check for safety-related blocking
                if finish_reason in [2, 3, 4, 5]:  # SAFETY, RECITATION, OTHER, BLOCKED
                    self.logger.warning(f"Gemini response blocked by safety filters (finish_reason: {finish_reason})")
                    return None
            
            return response
            
        except Exception as e:
            self.logger.warning(f"Gemini request with safety settings failed: {e}")
            return None
    
    def _get_relaxed_safety_settings(self) -> List[Dict]:
        """Get relaxed safety settings for retry attempts"""
        return [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def _get_minimal_safety_settings(self) -> List[Dict]:
        """Get minimal safety settings for final retry attempt"""
        return [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    
    def _extract_gemini_content(self, response) -> tuple[Optional[str], Optional[str]]:
        """Extract content and finish reason from Gemini response"""
        content = None
        finish_reason = None
        
        # Check if response has candidates and they contain valid content
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', 'unknown')
            self.logger.debug(f"Gemini candidate finish_reason: {finish_reason} (type: {type(finish_reason)})")
            
            # Check if candidate has content parts
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if hasattr(part, 'text'):
                        content = part.text
                    else:
                        self.logger.warning(f"Gemini candidate part has no text attribute")
                else:
                    self.logger.warning(f"Gemini candidate content has no parts")
            else:
                self.logger.warning(f"Gemini candidate has no content")
        else:
            self.logger.warning(f"Gemini response has no candidates")
        
        # Fallback to try response.text if available
        if content is None:
            try:
                content = response.text
                self.logger.debug(f"Successfully got response.text: {content[:100]}...")
            except Exception as text_error:
                self.logger.warning(f"Failed to get response.text: {text_error}")
                self.logger.debug(f"Response object attributes: {dir(response)}")
                if hasattr(response, 'candidates') and response.candidates:
                    self.logger.debug(f"Candidate attributes: {dir(response.candidates[0])}")
        
        return content, finish_reason
    
    def _create_safety_fallback_response(self, prompt: str) -> LLMResponse:
        """Create a fallback response when all safety attempts fail"""
        fallback_content = json.dumps({
            "error": "blocked_by_safety_filters",
            "message": "Analysis blocked by safety filters - using fallback response",
            "timestamp": datetime.now().isoformat(),
            "sentiment_score": 0.0,
            "confidence": 0.1,
            "impact_level": "unknown",
            "reasoning": "Unable to analyze due to safety filter restrictions"
        })
        
        return LLMResponse(
            content=fallback_content,
            model=self.model,
            provider="gemini",
            tokens_used=self._estimate_tokens(prompt + fallback_content),
            cost_estimate=0.0,
            timestamp=datetime.now(),
            metadata={
                "safety_blocked": True,
                "fallback_used": True
            }
        )

    async def _deepseek_chat(self, messages: List[Dict], temperature: float, max_tokens: Optional[int]) -> LLMResponse:
        """DeepSeek chat completion"""
        try:
            response = await self.deepseek_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 1000
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Estimate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost("deepseek", input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="deepseek",
                tokens_used=tokens_used,
                cost_estimate=cost,
                timestamp=datetime.now(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            self.logger.error(f"DeepSeek request failed: {e}")
            raise
    
    def _convert_messages_to_gemini_prompt(self, messages: List[Dict]) -> str:
        """Convert OpenAI-style messages to Gemini prompt"""
        # For simple single-user messages, just return the content directly
        if len(messages) == 1 and messages[0]["role"] == "user":
            return messages[0]["content"]
        
        # For more complex conversations, combine them into a single prompt
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.token_counter:
            return len(self.token_counter.encode(text))
        else:
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def _calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for the request"""
        if provider == "openai":
            model_costs = self.costs.get(self.model, self.costs["gpt-4"])
        elif provider == "gemini":
            model_costs = self.costs.get(self.model, self.costs["gemini-pro"])
        elif provider == "deepseek":
            model_costs = self.costs.get(self.model, self.costs["deepseek-chat"])
        else:
            # Default fallback
            model_costs = {"input": 0.001, "output": 0.002}
        
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost
    
    def _fix_json_formatting(self, content: str) -> str:
        """Fix common JSON formatting issues"""
        import re
        
        # Remove any text before the first {
        first_brace = content.find('{')
        if first_brace != -1:
            content = content[first_brace:]
        
        # Remove any text after the last }
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]
        
        # Fix unquoted property names (common issue)
        # Match patterns like: word: "value" and convert to "word": "value"
        content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        
        # Fix single quotes to double quotes
        content = content.replace("'", '"')
        
        # Fix trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # Fix multiple consecutive commas
        content = re.sub(r',+', ',', content)
        
        # Fix missing commas between properties
        content = re.sub(r'"\s*"([a-zA-Z_])', r'", "\1', content)
        
        # Fix boolean values
        content = re.sub(r':\s*true\b', ': true', content)
        content = re.sub(r':\s*false\b', ': false', content)
        content = re.sub(r':\s*null\b', ': null', content)
        
        return content.strip()
    
    async def analyze_json(self, 
                          prompt: str, 
                          system_prompt: Optional[str] = None,
                          schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Request structured JSON response
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            schema: Expected JSON schema
            
        Returns:
            Parsed JSON response
        """
        try:
            # Add JSON instruction to system prompt
            json_instruction = "Always respond with valid JSON format. Do not include any text outside the JSON structure."
            if schema:
                json_instruction += f"\n\nExpected schema: {json.dumps(schema, indent=2)}"
            
            full_system_prompt = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
            
            response = await self.chat(
                messages=prompt,
                system_prompt=full_system_prompt,
                temperature=0.1
            )
            
            # Check if response was blocked by safety filters
            if response.metadata and response.metadata.get('safety_blocked'):
                try:
                    # The content should already be a JSON string with error info
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "error": "blocked_by_safety_filters",
                        "message": "Response blocked by safety filters",
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Try to parse JSON
            try:
                return json.loads(response.content)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Initial JSON parsing failed: {e}")
                # Try to extract and clean JSON from response
                content = response.content.strip()
                
                # Remove markdown code blocks
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                
                if content.endswith("```"):
                    content = content[:-3]
                
                content = content.strip()
                
                # Try to fix common JSON formatting issues
                content = self._fix_json_formatting(content)
                
                # Try to find JSON within the content
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError as e2:
                        self.logger.warning(f"Extracted JSON parsing failed: {e2}")
                        # Try to fix the extracted JSON
                        fixed_json = self._fix_json_formatting(json_content)
                        try:
                            return json.loads(fixed_json)
                        except json.JSONDecodeError as e3:
                            self.logger.error(f"All JSON parsing attempts failed. Content: {json_content[:200]}...")
                            pass
                
                # If all else fails, try to parse the original content
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e4:
                    self.logger.error(f"Final JSON parsing failed: {e4}")
                    # Return a fallback response
                    return {
                        "error": "json_parsing_failed",
                        "message": "Unable to parse LLM response as JSON",
                        "raw_content": response.content[:500] + "..." if len(response.content) > 500 else response.content
                    }
                
        except ValueError as e:
            # Handle safety filter blocking specifically
            if "safety filters" in str(e).lower():
                self.logger.warning(f"JSON analysis blocked by safety filters: {e}")
                # Return a safe default response
                return {
                    "error": "blocked_by_safety_filters",
                    "message": "Analysis blocked by safety filters",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.error(f"JSON analysis failed: {e}")
                raise
        except Exception as e:
            self.logger.error(f"JSON analysis failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        
        if self.openai_client:
            models.extend(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        
        if self.gemini_client:
            models.extend(["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash", "gemini-1.5-pro"])
        
        if self.deepseek_client:
            models.extend(["deepseek-chat", "deepseek-coder"])
        
        return models
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of LLM clients"""
        status = {
            "provider": self.provider,
            "model": self.model,
            "openai_available": bool(self.openai_client),
            "gemini_available": bool(self.gemini_client),
            "deepseek_available": bool(self.deepseek_client),
            "status": "unknown"
        }
        
        try:
            # Test with simple request
            response = await self.chat("Test connection. Respond with 'OK'.")
            if "OK" in response.content.upper():
                status["status"] = "healthy"
            else:
                status["status"] = "degraded"
                
        except Exception as e:
            status["status"] = "unhealthy"
            status["error"] = str(e)
        
        return status


# Global instance
llm_client = None

def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global llm_client
    if llm_client is None:
        llm_client = LLMClient(provider="gemini")
    return llm_client

def reset_llm_client():
    """Reset the global LLM client instance"""
    global llm_client
    llm_client = None
