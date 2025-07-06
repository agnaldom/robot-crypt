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
        
        # Cost tracking
        self.costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1k tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-pro-vision": {"input": 0.00025, "output": 0.0005}
        }
        
        # Initialize clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize available LLM clients"""
        self.openai_client = None
        self.gemini_client = None
        
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                    if not self.model and self.provider in ["openai", "auto"]:
                        self.model = "gpt-4-turbo"
                    
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
                    self.gemini_client = genai.GenerativeModel('gemini-pro')
                    if not self.model and self.provider in ["gemini", "auto"]:
                        self.model = "gemini-pro"
                    
                    self.logger.info("Gemini client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Gemini: {e}")
        
        # Auto-select provider
        if self.provider == "auto":
            if self.openai_client:
                self.provider = "openai"
                self.model = self.model or "gpt-4-turbo"
            elif self.gemini_client:
                self.provider = "gemini" 
                self.model = self.model or "gemini-pro"
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
        """Gemini chat completion"""
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_gemini_prompt(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 1000
            )
            
            response = await asyncio.to_thread(
                self.gemini_client.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
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
    
    def _convert_messages_to_gemini_prompt(self, messages: List[Dict]) -> str:
        """Convert OpenAI-style messages to Gemini prompt"""
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
        else:  # gemini
            model_costs = self.costs.get(self.model, self.costs["gemini-pro"])
        
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost
    
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
            
            # Try to parse JSON
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                return json.loads(content)
                
        except Exception as e:
            self.logger.error(f"JSON analysis failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        
        if self.openai_client:
            models.extend(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        
        if self.gemini_client:
            models.extend(["gemini-pro", "gemini-pro-vision"])
        
        return models
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of LLM clients"""
        status = {
            "provider": self.provider,
            "model": self.model,
            "openai_available": bool(self.openai_client),
            "gemini_available": bool(self.gemini_client),
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
        llm_client = LLMClient()
    return llm_client
