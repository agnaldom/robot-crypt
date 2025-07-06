#!/usr/bin/env python3
"""
Advanced Pattern Detector using LLM
Detects complex patterns that traditional ML might miss
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .llm_client import get_llm_client
from src.ai_security.prompt_protection import ai_security_guard

logger = logging.getLogger(__name__)


class AdvancedPatternDetector:
    """Detector de padrões avançados usando LLM"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger("robot-crypt.pattern_detector")
        
        # Cache para padrões detectados
        self.pattern_cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    async def detect_complex_patterns(self, 
                                    price_data: List[Dict[str, Any]], 
                                    volume_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detecta padrões complexos que ML tradicional pode perder
        
        Args:
            price_data: Dados de preço OHLCV
            volume_data: Dados de volume
            
        Returns:
            Lista de padrões detectados
        """
        try:
            if not price_data or len(price_data) < 20:
                self.logger.warning("Dados insuficientes para detecção de padrões")
                return []
            
            # Check cache
            cache_key = self._create_cache_key(price_data)
            cached_patterns = self._get_cached_patterns(cache_key)
            if cached_patterns:
                self.logger.info("Retornando padrões do cache")
                return cached_patterns
            
            # Converte dados para formato textual para o LLM
            chart_description = self._generate_chart_description(price_data, volume_data)
            
            # Sanitiza input
            try:
                sanitized_description = ai_security_guard.sanitize_ai_input(chart_description, "trading")
            except ValueError as e:
                self.logger.warning(f"Chart description rejected by security: {e}")
                return []
            
            # Cria prompt para análise
            prompt = self._create_pattern_analysis_prompt(sanitized_description)
            
            # Obtém análise do LLM
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt=self._get_pattern_system_prompt(),
                schema=self._get_pattern_schema()
            )
            
            # Valida resposta
            is_valid, validation_error = ai_security_guard.validate_ai_output(response, "trading")
            if not is_valid:
                self.logger.warning(f"Pattern analysis validation failed: {validation_error}")
                return []
            
            # Processa padrões detectados
            patterns = self._process_detected_patterns(response)
            
            # Cache resultado
            self._cache_patterns(cache_key, patterns)
            
            self.logger.info(f"Detected {len(patterns)} complex patterns")
            return patterns
            
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")
            return []
    
    async def analyze_breakout_probability(self, 
                                         price_data: List[Dict[str, Any]], 
                                         symbol: str) -> Dict[str, Any]:
        """
        Analisa probabilidade de breakout/breakdown
        
        Args:
            price_data: Dados de preço
            symbol: Símbolo do ativo
            
        Returns:
            Análise de probabilidade de breakout
        """
        try:
            if len(price_data) < 30:
                return {"probability": 0.5, "direction": "uncertain", "confidence": 0.1}
            
            # Calcula estatísticas básicas
            prices = [float(data['close']) for data in price_data[-30:]]
            volumes = [float(data['volume']) for data in price_data[-30:]]
            
            recent_high = max(prices[-20:])
            recent_low = min(prices[-20:])
            current_price = prices[-1]
            avg_volume = np.mean(volumes[-10:])
            recent_volume = volumes[-1]
            
            # Cria contexto para análise
            context = f"""
            Symbol: {symbol}
            Recent High (20 periods): {recent_high:.6f}
            Recent Low (20 periods): {recent_low:.6f}
            Current Price: {current_price:.6f}
            Price position: {((current_price - recent_low) / (recent_high - recent_low) * 100):.1f}% of range
            Recent Volume: {recent_volume:.2f}
            Average Volume: {avg_volume:.2f}
            Volume Ratio: {(recent_volume / avg_volume):.2f}x
            
            Price trend last 5 periods: {self._calculate_trend(prices[-5:])}
            Volatility: {self._calculate_volatility(prices[-10:]):.2%}
            """
            
            prompt = f"""
            Analyze the breakout probability for this cryptocurrency:
            
            {context}
            
            Consider:
            1. Price position within recent range
            2. Volume patterns
            3. Consolidation duration
            4. Support/resistance levels
            5. Market momentum
            
            Provide:
            - Breakout probability (0-1)
            - Most likely direction (up/down/sideways)
            - Confidence level (0-1)
            - Key levels to watch
            - Risk factors
            """
            
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt="You are a technical analysis expert specializing in breakout detection.",
                schema={
                    "breakout_probability": "number",
                    "direction": "string",
                    "confidence": "number", 
                    "key_levels": "array",
                    "risk_factors": "array",
                    "reasoning": "string"
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Breakout analysis failed: {e}")
            return {
                "breakout_probability": 0.5,
                "direction": "uncertain", 
                "confidence": 0.1,
                "key_levels": [],
                "risk_factors": ["Analysis failed"],
                "reasoning": f"Error: {str(e)}"
            }
    
    def _generate_chart_description(self, 
                                  price_data: List[Dict[str, Any]], 
                                  volume_data: List[Dict[str, Any]]) -> str:
        """Gera descrição textual dos dados do gráfico"""
        try:
            # Limita dados para evitar tokens excessivos
            recent_data = price_data[-50:] if len(price_data) > 50 else price_data
            
            description_parts = []
            
            # Descrição geral
            first_price = float(recent_data[0]['close'])
            last_price = float(recent_data[-1]['close'])
            price_change = ((last_price - first_price) / first_price) * 100
            
            description_parts.append(f"Price movement over {len(recent_data)} periods:")
            description_parts.append(f"From {first_price:.6f} to {last_price:.6f} ({price_change:+.2f}%)")
            
            # Pontos importantes (máximas e mínimas recentes)
            prices = [float(d['close']) for d in recent_data]
            highs = [float(d['high']) for d in recent_data]
            lows = [float(d['low']) for d in recent_data]
            
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
            highest_point = max(highs)
            lowest_point = min(lows)
            
            description_parts.append(f"Recent range: {recent_low:.6f} - {recent_high:.6f}")
            description_parts.append(f"Period range: {lowest_point:.6f} - {highest_point:.6f}")
            
            # Padrões de movimento
            if len(recent_data) >= 10:
                recent_trend = self._describe_trend(prices[-10:])
                description_parts.append(f"Recent trend: {recent_trend}")
            
            # Volume (se disponível)
            if volume_data and len(volume_data) >= 10:
                volumes = [float(d['volume']) for d in volume_data[-10:]]
                avg_volume = np.mean(volumes[:-1])
                current_volume = volumes[-1]
                volume_change = ((current_volume - avg_volume) / avg_volume) * 100
                description_parts.append(f"Volume: {volume_change:+.1f}% vs average")
            
            # Pontos de reversão
            reversal_points = self._find_reversal_points(prices)
            if reversal_points:
                description_parts.append(f"Key reversal points at: {reversal_points}")
            
            return "\n".join(description_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating chart description: {e}")
            return "Unable to generate chart description"
    
    def _describe_trend(self, prices: List[float]) -> str:
        """Descreve a tendência dos preços"""
        if len(prices) < 3:
            return "insufficient data"
        
        first_third = np.mean(prices[:len(prices)//3])
        last_third = np.mean(prices[-len(prices)//3:])
        
        change = ((last_third - first_third) / first_third) * 100
        
        if change > 2:
            return f"uptrend (+{change:.1f}%)"
        elif change < -2:
            return f"downtrend ({change:.1f}%)"
        else:
            return f"sideways ({change:+.1f}%)"
    
    def _find_reversal_points(self, prices: List[float]) -> List[str]:
        """Encontra pontos de reversão importantes"""
        if len(prices) < 5:
            return []
        
        reversal_points = []
        
        # Procura por picos e vales
        for i in range(2, len(prices) - 2):
            # Pico
            if (prices[i] > prices[i-1] and prices[i] > prices[i+1] and 
                prices[i] > prices[i-2] and prices[i] > prices[i+2]):
                reversal_points.append(f"peak at {prices[i]:.6f}")
            
            # Vale
            elif (prices[i] < prices[i-1] and prices[i] < prices[i+1] and 
                  prices[i] < prices[i-2] and prices[i] < prices[i+2]):
                reversal_points.append(f"valley at {prices[i]:.6f}")
        
        return reversal_points[-5:]  # Últimos 5 pontos
    
    def _calculate_trend(self, prices: List[float]) -> str:
        """Calcula tendência simples"""
        if len(prices) < 2:
            return "flat"
        
        change = ((prices[-1] - prices[0]) / prices[0]) * 100
        
        if change > 1:
            return "rising"
        elif change < -1:
            return "falling"
        else:
            return "flat"
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calcula volatilidade simples"""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        return np.std(returns)
    
    def _create_pattern_analysis_prompt(self, chart_description: str) -> str:
        """Cria prompt para análise de padrões"""
        return f"""
        Analyze this cryptocurrency price chart and identify significant patterns:
        
        {chart_description}
        
        Look for:
        1. Chart patterns (Head & Shoulders, Triangles, Flags, Wedges, Double tops/bottoms)
        2. Divergences between price and volume
        3. Accumulation/distribution formations
        4. Support and resistance levels
        5. Breakout/breakdown patterns
        6. Consolidation patterns
        
        For each pattern identified, provide:
        - Pattern name and description
        - Confidence level (0-100%)
        - Expected direction (bullish/bearish/neutral)
        - Target levels (if applicable)
        - Pattern invalidation level
        - Time horizon for completion
        """
    
    def _get_pattern_system_prompt(self) -> str:
        """System prompt para análise de padrões"""
        return """
        You are an expert technical analyst specializing in cryptocurrency chart pattern recognition.
        
        Your analysis should be:
        1. Objective and based on established technical analysis principles
        2. Conservative in confidence levels for complex patterns
        3. Clear about pattern invalidation conditions
        4. Focused on actionable insights
        
        Always consider:
        - Pattern completeness and maturity
        - Volume confirmation
        - Market context and overall trend
        - False breakout potential
        - Risk/reward ratios
        """
    
    def _get_pattern_schema(self) -> Dict[str, Any]:
        """Schema para resposta de padrões"""
        return {
            "patterns": [
                {
                    "name": "string",
                    "description": "string", 
                    "confidence": "number",
                    "direction": "string",
                    "target_levels": "array",
                    "invalidation_level": "number",
                    "time_horizon": "string",
                    "volume_confirmation": "boolean"
                }
            ],
            "overall_assessment": "string",
            "key_levels": {
                "support": "array",
                "resistance": "array"
            },
            "risk_factors": "array"
        }
    
    def _process_detected_patterns(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa padrões detectados da resposta do LLM"""
        patterns = response.get("patterns", [])
        
        # Filtra padrões por confiança mínima
        filtered_patterns = [
            pattern for pattern in patterns 
            if pattern.get("confidence", 0) >= 50  # 50% confiança mínima
        ]
        
        # Ordena por confiança
        filtered_patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
        
        return filtered_patterns
    
    def _create_cache_key(self, price_data: List[Dict[str, Any]]) -> str:
        """Cria chave de cache para os dados"""
        # Usa timestamp do último dado e hash dos últimos preços
        if not price_data:
            return "empty_data"
        
        last_timestamp = price_data[-1].get('timestamp', datetime.now().isoformat())
        recent_prices = [float(d['close']) for d in price_data[-10:]]
        price_hash = hash(tuple(recent_prices))
        
        return f"patterns_{last_timestamp}_{price_hash}"
    
    def _get_cached_patterns(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Recupera padrões do cache se válidos"""
        if cache_key in self.pattern_cache:
            cached_item = self.pattern_cache[cache_key]
            if datetime.now() - cached_item["timestamp"] < self.cache_duration:
                return cached_item["patterns"]
        
        return None
    
    def _cache_patterns(self, cache_key: str, patterns: List[Dict[str, Any]]):
        """Armazena padrões no cache"""
        self.pattern_cache[cache_key] = {
            "patterns": patterns,
            "timestamp": datetime.now()
        }
        
        # Limpa cache antigo
        cutoff_time = datetime.now() - self.cache_duration
        self.pattern_cache = {
            k: v for k, v in self.pattern_cache.items()
            if v["timestamp"] > cutoff_time
        }
