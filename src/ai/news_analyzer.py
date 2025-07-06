#!/usr/bin/env python3
"""
LLM-powered News Analyzer for Crypto Trading
Provides advanced sentiment analysis and event detection
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

from .llm_client import get_llm_client, LLMResponse
from src.ai_security.prompt_protection import ai_security_guard

logger = logging.getLogger(__name__)


@dataclass 
class NewsAnalysis:
    """Estrutura para análise de notícias"""
    sentiment_score: float  # -1 (bearish) to 1 (bullish)
    sentiment_label: str   # bearish, neutral, bullish
    confidence: float      # 0 to 1
    impact_level: str      # low, medium, high
    key_events: List[str]
    price_prediction: Optional[str]  # short_term_up, short_term_down, neutral
    reasoning: str
    article_count: int
    timestamp: datetime


@dataclass
class CryptoNewsItem:
    """Estrutura para item de notícia"""
    title: str
    content: str
    source: str
    published_at: datetime
    symbols_mentioned: List[str]
    url: Optional[str] = None
    author: Optional[str] = None


class LLMNewsAnalyzer:
    """Analisador de notícias baseado em LLM"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger("robot-crypt.news_analyzer")
        
        # Cache para evitar re-análise
        self.analysis_cache = {}
        self.cache_duration = timedelta(minutes=30)
        
        # System prompt para análise de notícias cripto
        self.system_prompt = """
        You are an expert cryptocurrency market analyst specializing in news sentiment analysis and market impact assessment.

        Your analysis should consider:
        1. Market sentiment and emotional tone
        2. Potential price impact (short-term and medium-term)
        3. Regulatory implications
        4. Technical developments and partnerships
        5. Market manipulation or pump/dump schemes
        6. Macroeconomic factors affecting crypto
        7. Institutional adoption signals

        Always provide balanced, objective analysis based on factual information.
        Be especially careful about identifying potential misinformation or market manipulation attempts.
        
        Response format: Always return valid JSON with the specified structure.
        """
    
    async def analyze_crypto_news(self, 
                                  news_items: List[CryptoNewsItem], 
                                  symbol: Optional[str] = None) -> NewsAnalysis:
        """
        Analisa notícias de criptomoedas usando LLM
        
        Args:
            news_items: Lista de itens de notícia
            symbol: Símbolo específico para análise (opcional)
            
        Returns:
            NewsAnalysis com análise completa
        """
        try:
            if not news_items:
                return self._create_neutral_analysis(0, "No news items provided")
            
            # Check cache
            cache_key = self._create_cache_key(news_items, symbol)
            cached_result = self._get_cached_analysis(cache_key)
            if cached_result:
                self.logger.info("Returning cached news analysis")
                return cached_result
            
            # Prepare news data for analysis
            news_text = self._prepare_news_text(news_items, symbol)
            
            # Sanitize input
            try:
                sanitized_text = ai_security_guard.sanitize_ai_input(news_text, "sentiment")
            except ValueError as e:
                self.logger.warning(f"News input rejected by security guard: {e}")
                return self._create_neutral_analysis(len(news_items), "Input rejected for security reasons")
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(sanitized_text, symbol)
            
            # Get LLM analysis
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt=self.system_prompt,
                schema=self._get_analysis_schema()
            )
            
            # Validate response
            is_valid, validation_error = ai_security_guard.validate_ai_output(response, "sentiment")
            if not is_valid:
                self.logger.warning(f"LLM output validation failed: {validation_error}")
                return self._create_neutral_analysis(len(news_items), f"Output validation failed: {validation_error}")
            
            # Convert to NewsAnalysis
            analysis = self._convert_response_to_analysis(response, len(news_items))
            
            # Cache result
            self._cache_analysis(cache_key, analysis)
            
            self.logger.info(f"Analyzed {len(news_items)} news items for {symbol or 'general'}: "
                           f"sentiment={analysis.sentiment_label}, confidence={analysis.confidence:.2f}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"News analysis failed: {e}")
            return self._create_neutral_analysis(len(news_items), f"Analysis failed: {str(e)}")
    
    async def analyze_single_article(self, article: CryptoNewsItem) -> Dict[str, Any]:
        """
        Analisa um único artigo em detalhe
        
        Args:
            article: Artigo para análise
            
        Returns:
            Análise detalhada do artigo
        """
        try:
            # Prepare article text
            article_text = f"Title: {article.title}\n"
            if article.content:
                article_text += f"Content: {article.content[:2000]}..."  # Limit content length
            article_text += f"\nSource: {article.source}"
            
            # Sanitize input
            sanitized_text = ai_security_guard.sanitize_ai_input(article_text, "sentiment")
            
            prompt = f"""
            Analyze this cryptocurrency news article in detail:
            
            {sanitized_text}
            
            Provide analysis for:
            1. Overall sentiment (-1 to 1, where -1 = very bearish, 1 = very bullish)
            2. Credibility assessment (0 to 1)
            3. Market impact potential (low/medium/high)
            4. Key topics/themes mentioned
            5. Potential price impact timeframe (immediate/short-term/medium-term/long-term)
            6. Risk factors identified
            7. Opportunities identified
            """
            
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt=self.system_prompt,
                schema={
                    "sentiment_score": "number",
                    "credibility_score": "number", 
                    "impact_level": "string",
                    "key_topics": "array",
                    "impact_timeframe": "string",
                    "risk_factors": "array",
                    "opportunities": "array",
                    "summary": "string"
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Single article analysis failed: {e}")
            return {
                "sentiment_score": 0.0,
                "credibility_score": 0.5,
                "impact_level": "low",
                "key_topics": [],
                "impact_timeframe": "unknown",
                "risk_factors": [],
                "opportunities": [],
                "summary": f"Analysis failed: {str(e)}"
            }
    
    async def detect_market_events(self, news_items: List[CryptoNewsItem]) -> List[Dict[str, Any]]:
        """
        Detecta eventos importantes do mercado nas notícias
        
        Args:
            news_items: Lista de notícias
            
        Returns:
            Lista de eventos detectados
        """
        try:
            if not news_items:
                return []
            
            # Prepare news summary
            news_summary = self._create_news_summary(news_items)
            sanitized_summary = ai_security_guard.sanitize_ai_input(news_summary, "sentiment")
            
            prompt = f"""
            Analyze these cryptocurrency news items and identify significant market events:
            
            {sanitized_summary}
            
            Look for:
            1. Regulatory announcements or changes
            2. Major partnerships or integrations
            3. Technical upgrades or launches
            4. Institutional adoption news
            5. Market manipulation or security issues
            6. Macroeconomic events affecting crypto
            7. Major exchange listings or delistings
            
            For each event, provide:
            - Event type and description
            - Potential market impact (1-10 scale)
            - Affected cryptocurrencies
            - Expected impact duration
            - Risk/opportunity assessment
            """
            
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt=self.system_prompt,
                schema={
                    "events": [
                        {
                            "event_type": "string",
                            "description": "string",
                            "impact_score": "number",
                            "affected_symbols": "array",
                            "impact_duration": "string",
                            "is_positive": "boolean",
                            "confidence": "number"
                        }
                    ]
                }
            )
            
            return response.get("events", [])
            
        except Exception as e:
            self.logger.error(f"Event detection failed: {e}")
            return []
    
    def _prepare_news_text(self, news_items: List[CryptoNewsItem], symbol: Optional[str]) -> str:
        """Prepara texto das notícias para análise"""
        if symbol:
            # Filter news relevant to symbol
            relevant_news = [
                item for item in news_items 
                if symbol.upper() in item.title.upper() or 
                   symbol.upper() in (item.content or "").upper() or
                   symbol in item.symbols_mentioned
            ]
            if relevant_news:
                news_items = relevant_news
        
        # Limit number of articles to avoid token limits
        news_items = news_items[:20]
        
        news_texts = []
        for i, item in enumerate(news_items, 1):
            news_text = f"{i}. Title: {item.title}\n"
            news_text += f"   Source: {item.source}\n"
            news_text += f"   Date: {item.published_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            if item.content:
                # Limit content length
                content = item.content[:500] + "..." if len(item.content) > 500 else item.content
                news_text += f"   Content: {content}\n"
            
            news_texts.append(news_text)
        
        return "\n".join(news_texts)
    
    def _create_news_summary(self, news_items: List[CryptoNewsItem]) -> str:
        """Cria resumo das notícias"""
        summaries = []
        for item in news_items[:10]:  # Limit for token efficiency
            summary = f"- {item.title} ({item.source}, {item.published_at.strftime('%m-%d %H:%M')})"
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def _create_analysis_prompt(self, news_text: str, symbol: Optional[str]) -> str:
        """Cria prompt para análise"""
        base_prompt = f"""
        Analyze the following cryptocurrency news and provide comprehensive sentiment analysis:
        
        {news_text}
        
        Focus on:
        1. Overall market sentiment for {"the specified symbol " + symbol if symbol else "the cryptocurrency market"}
        2. Potential short-term price impact (next 1-24 hours)
        3. Medium-term implications (next 1-7 days)
        4. Key events or announcements that could move markets
        5. Risk factors and opportunities
        
        Consider:
        - Source credibility and potential bias
        - Market context and current trends
        - Technical vs fundamental developments
        - Regulatory implications
        - Institutional vs retail sentiment
        """
        
        if symbol:
            base_prompt += f"\n\nPay special attention to news directly related to {symbol} and its ecosystem."
        
        return base_prompt
    
    def _get_analysis_schema(self) -> Dict[str, Any]:
        """Retorna schema esperado para análise"""
        return {
            "sentiment_score": "number",  # -1 to 1
            "sentiment_label": "string",  # bearish, neutral, bullish
            "confidence": "number",       # 0 to 1
            "impact_level": "string",     # low, medium, high
            "key_events": "array",
            "price_prediction": "string", # short_term_up, short_term_down, neutral
            "reasoning": "string",
            "risk_factors": "array",
            "opportunities": "array",
            "timeframe_analysis": {
                "immediate": "string",
                "short_term": "string", 
                "medium_term": "string"
            }
        }
    
    def _convert_response_to_analysis(self, response: Dict[str, Any], article_count: int) -> NewsAnalysis:
        """Converte resposta do LLM para NewsAnalysis"""
        return NewsAnalysis(
            sentiment_score=max(-1.0, min(1.0, response.get("sentiment_score", 0.0))),
            sentiment_label=response.get("sentiment_label", "neutral"),
            confidence=max(0.0, min(1.0, response.get("confidence", 0.5))),
            impact_level=response.get("impact_level", "medium"),
            key_events=response.get("key_events", []),
            price_prediction=response.get("price_prediction", "neutral"),
            reasoning=response.get("reasoning", "Analysis completed"),
            article_count=article_count,
            timestamp=datetime.now()
        )
    
    def _create_neutral_analysis(self, article_count: int, reason: str) -> NewsAnalysis:
        """Cria análise neutra para casos de erro"""
        return NewsAnalysis(
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.1,
            impact_level="low",
            key_events=[],
            price_prediction="neutral",
            reasoning=reason,
            article_count=article_count,
            timestamp=datetime.now()
        )
    
    def _create_cache_key(self, news_items: List[CryptoNewsItem], symbol: Optional[str]) -> str:
        """Cria chave de cache para as notícias"""
        # Create hash from titles and timestamps
        content_hash = hash(tuple(
            (item.title, item.published_at.isoformat()) 
            for item in news_items[:10]
        ))
        
        return f"news_analysis_{symbol or 'general'}_{content_hash}"
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[NewsAnalysis]:
        """Recupera análise do cache se ainda válida"""
        if cache_key in self.analysis_cache:
            cached_item = self.analysis_cache[cache_key]
            if datetime.now() - cached_item["timestamp"] < self.cache_duration:
                return cached_item["analysis"]
        
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: NewsAnalysis):
        """Armazena análise no cache"""
        self.analysis_cache[cache_key] = {
            "analysis": analysis,
            "timestamp": datetime.now()
        }
        
        # Clean old cache entries
        cutoff_time = datetime.now() - self.cache_duration
        self.analysis_cache = {
            k: v for k, v in self.analysis_cache.items()
            if v["timestamp"] > cutoff_time
        }
    
    async def get_market_sentiment_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Obtém resumo do sentimento geral do mercado
        
        Args:
            symbols: Lista de símbolos para análise
            
        Returns:
            Resumo do sentimento do mercado
        """
        try:
            # This would typically fetch recent news for each symbol
            # For now, we'll create a general market analysis prompt
            
            prompt = f"""
            Provide a comprehensive cryptocurrency market sentiment analysis for these symbols: {', '.join(symbols)}
            
            Consider:
            1. Current market conditions and trends
            2. Recent news and developments
            3. Technical analysis implications
            4. Institutional sentiment indicators
            5. Regulatory environment
            6. Macroeconomic factors
            
            Provide market sentiment for:
            - Overall crypto market
            - Individual symbols (if specific news available)
            - Risk assessment
            - Opportunity identification
            - Recommended strategies
            """
            
            response = await self.llm_client.analyze_json(
                prompt=prompt,
                system_prompt=self.system_prompt,
                schema={
                    "overall_sentiment": "string",
                    "market_phase": "string",
                    "sentiment_score": "number",
                    "individual_symbols": "object",
                    "key_factors": "array",
                    "risks": "array",
                    "opportunities": "array",
                    "recommended_strategy": "string"
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Market sentiment summary failed: {e}")
            return {
                "overall_sentiment": "neutral",
                "market_phase": "uncertain",
                "sentiment_score": 0.0,
                "individual_symbols": {},
                "key_factors": [],
                "risks": ["Analysis unavailable"],
                "opportunities": [],
                "recommended_strategy": "monitor and wait"
            }
