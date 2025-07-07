#!/usr/bin/env python3
"""
Módulo para análise de dados contextuais externos para o Robot-Crypt
Integra dados de notícias e eventos macroeconômicos globais para análise técnica
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta
import re
from pathlib import Path
from src.core.config import Config
import numpy as np
from src.utils.utils import setup_logger

class ExternalDataAnalyzer:
    """
    Classe para coletar e analisar dados contextuais externos que podem
    impactar o mercado de criptomoedas, como notícias econômicas, eventos 
    macroeconômicos, e alterações regulatórias.
    """
    
    def __init__(self, config=None):
        """Inicializa o analisador de dados externos
        
        Args:
            config: Configuração do bot que contém as API keys
        """
        self.config = config if config else Config()
        self.logger = logging.getLogger("robot-crypt")
        
        # API Keys
        self.newsapi_key = os.environ.get("NEWSAPI_KEY", "")
        
        # Diretório de cache para dados contextuais
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.news_cache_file = self.data_dir / "news_cache.json"
        
        # Configurações de cache
        self.cache_valid_hours = 6  # Cache válido por 6 horas
        
        # Carregar cache existente
        self.news_cache = self._load_cache(self.news_cache_file)
        
        # Palavras-chave para diferentes tipos de eventos
        self.keywords = {
            'economic': [
                'interest rate', 'inflation', 'gdp', 'economic growth', 'recession', 'fed', 
                'federal reserve', 'central bank', 'fiscal policy', 'monetary policy'
            ],
            'regulatory': [
                'regulation', 'ban', 'crypto law', 'compliance', 'sec', 'cftc', 'fca', 
                'regulatory approval', 'legal', 'government'
            ],
            'geopolitical': [
                'war', 'conflict', 'sanctions', 'trade war', 'elections', 'political crisis',
                'government collapse', 'civil unrest', 'protests', 'coup'
            ]
        }
        
        # Criticalidade de diferentes tipos de eventos para o mercado de criptomoedas (peso)
        self.event_weights = {
            'economic': 0.7,
            'regulatory': 0.9,
            'geopolitical': 0.5
        }

    def _load_cache(self, cache_file):
        """Carrega cache de dados do arquivo"""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
                    
                    # Verifica se o cache ainda é válido
                    if datetime.now() - cache_time < timedelta(hours=self.cache_valid_hours):
                        self.logger.info(f"Usando cache de dados válido (de {cache_time})")
                        return data
            
            # Se chegou aqui, cache inexistente ou inválido
            self.logger.info(f"Cache não encontrado ou expirado para {cache_file}")
            return {'timestamp': datetime.now().isoformat(), 'data': {}}
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache: {str(e)}")
            return {'timestamp': datetime.now().isoformat(), 'data': {}}
    
    def _save_cache(self, cache_data, cache_file):
        """Salva cache de dados em arquivo"""
        try:
            # Atualiza timestamp do cache
            cache_data['timestamp'] = datetime.now().isoformat()
            
            # Salva cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            self.logger.info(f"Cache salvo com sucesso em {cache_file}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {str(e)}")
            return False

    def fetch_economic_news(self, days=3, force_refresh=False):
        """Busca notícias econômicas e de criptomoedas relevantes
        
        Args:
            days (int): Número de dias para buscar notícias
            force_refresh (bool): Se True, ignora o cache e busca novamente
            
        Returns:
            list: Lista de notícias relevantes
        """
        # Verificar se temos notícias em cache e se ainda são válidas
        if not force_refresh and 'economic_news' in self.news_cache['data']:
            cache_time = datetime.fromisoformat(self.news_cache['timestamp'])
            if datetime.now() - cache_time < timedelta(hours=self.cache_valid_hours):
                self.logger.info("Usando notícias econômicas em cache")
                return self.news_cache['data']['economic_news']
        
        if not self.newsapi_key:
            self.logger.warning("API Key da NewsAPI não configurada")
            return []
            
        # Define query e parâmetros para NewsAPI
        queries = [
            'cryptocurrency OR bitcoin OR crypto',
            'economic crisis OR inflation OR recession',
            'central bank OR interest rate',
            'crypto regulation OR crypto law'
        ]
        
        all_articles = []
        for query in queries:
            try:
                url = "https://newsapi.org/v2/everything"
                today = datetime.now()
                from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
                
                params = {
                    'q': query,
                    'from': from_date,
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'pageSize': 10,
                    'apiKey': self.newsapi_key
                }
                
                self.logger.info(f"Buscando notícias para '{query}'")
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code != 200:
                    self.logger.error(f"Erro ao buscar notícias: {response.status_code} - {response.text}")
                    continue
                
                data = response.json()
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    self.logger.info(f"Encontrados {len(articles)} artigos para '{query}'")
                    all_articles.extend(articles)
                else:
                    self.logger.warning(f"Status não ok: {data.get('status')}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao buscar notícias: {str(e)}")
        
        # Processar e classificar notícias
        processed_news = []
        for article in all_articles:
            # Calcular relevância e classificar tipo de evento
            event_type, relevance_score = self._classify_news(article)
            
            # Formatar e adicionar à lista
            processed_article = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'published_at': article.get('publishedAt', ''),
                'event_type': event_type,
                'relevance_score': relevance_score,
                'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
            }
            processed_news.append(processed_article)
        
        # Ordenar por relevância
        processed_news.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Atualizar cache
        self.news_cache['data']['economic_news'] = processed_news
        self._save_cache(self.news_cache, self.news_cache_file)
        
        return processed_news

    def _classify_news(self, article):
        """Classifica o tipo de notícia e calcula sua relevância
        
        Args:
            article (dict): Artigo de notícia
            
        Returns:
            tuple: (tipo_evento, pontuação_relevância)
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower() if article.get('description') else ''
        content = title + ' ' + description
        
        # Verificar qual tipo de evento corresponde melhor
        event_scores = {}
        for event_type, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 1
            
            # Normalizar pontuação
            if score > 0:
                score = score / len(keywords) * self.event_weights.get(event_type, 0.5)
            event_scores[event_type] = score
        
        # Determinar tipo de evento e pontuação
        max_type = max(event_scores, key=event_scores.get)
        max_score = event_scores[max_type]
        
        # Se pontuação for muito baixa, considerar como "outro"
        if max_score < 0.3:
            return "other", max_score
        
        return max_type, max_score

    def _analyze_sentiment(self, text):
        """Análise básica de sentimento para texto
        
        Args:
            text (str): Texto para análise
            
        Returns:
            float: Pontuação de sentimento (-1.0 a 1.0)
        """
        # Palavras positivas e negativas para análise simplificada
        positive_words = [
            'bullish', 'growth', 'positive', 'gain', 'rally', 'surge', 'rise',
            'up', 'higher', 'success', 'profit', 'good', 'strong', 'opportunity',
            'recovery', 'breakthrough', 'adoption', 'support', 'advance'
        ]
        
        negative_words = [
            'bearish', 'crash', 'decline', 'drop', 'fall', 'loss', 'negative',
            'down', 'lower', 'fail', 'risk', 'bad', 'weak', 'threat', 'crisis',
            'recession', 'ban', 'sell-off', 'dump', 'bubble'
        ]
        
        # Contar ocorrências
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calcular sentimento normalizado
        total = positive_count + negative_count
        if total == 0:
            return 0.0
            
        sentiment = (positive_count - negative_count) / total
        return round(sentiment, 2)  # Normalizar para -1.0 a 1.0

    def fetch_macro_indicators(self):
        """Busca indicadores macroeconômicos atuais
        
        Returns:
            dict: Dicionário de indicadores macroeconômicos
        """
        # Esta função deveria se integrar com uma API de dados econômicos
        # Como AlphaVantage, FRED, World Bank, etc.
        # Por enquanto, retorna dados simulados
        
        self.logger.info("Usando dados macroeconômicos simulados")
        
        return {
            'inflation_rate': 4.3,  # %
            'interest_rate': 5.0,   # %
            'unemployment': 3.8,    # %
            'gdp_growth': 2.1,      # %
            'vix_index': 18.5,      # Índice de volatilidade
            'timestamp': datetime.now().isoformat()
        }

    def calculate_market_context_score(self, symbol=None):
        """Calcula uma pontuação de contexto de mercado baseada em dados externos
        
        Args:
            symbol (str, optional): Símbolo da criptomoeda
            
        Returns:
            dict: Pontuação de contexto com fatores detalhados
        """
        self.logger.info(f"Calculando pontuação de contexto para {symbol if symbol else 'mercado geral'}")
        
        # Busca notícias econômicas
        news = self.fetch_economic_news()
        
        # Calcular média de sentimento das notícias
        if news:
            sentiment_scores = [n['sentiment'] for n in news]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_sentiment = 0.0
            
        # Obter indicadores macroeconômicos
        macro = self.fetch_macro_indicators()
        
        # Calcular pontuação de pressão inflacionária (negativa para o mercado cripto)
        # - Alta inflação pode levar a políticas monetárias restritivas
        inflation_score = -0.5 * (macro['inflation_rate'] / 10)  # Normalizar para -0.5 a 0
        
        # Calcular pontuação de taxa de juros (negativa para o mercado cripto)
        # - Taxas altas tornam ativos de risco menos atraentes
        interest_score = -0.5 * (macro['interest_rate'] / 10)  # Normalizar para -0.5 a 0
        
        # Calcular pontuação de volatilidade (negativa para o mercado)
        # - VIX alto indica incerteza no mercado tradicional
        vix_score = -0.3 * (macro['vix_index'] / 40)  # Normalizar para -0.3 a 0
        
        # Calcular pontuação de crescimento econômico (positiva para o mercado)
        # - Crescimento forte é geralmente positivo para ativos de risco
        growth_score = 0.3 * (macro['gdp_growth'] / 5)  # Normalizar para 0 a 0.3
        
        # Calcular notícias específicas para o símbolo, se fornecido
        symbol_specific_score = 0.0
        if symbol:
            symbol_news = [n for n in news if symbol.lower() in (n['title'] + n['description']).lower()]
            if symbol_news:
                symbol_sentiments = [n['sentiment'] for n in symbol_news]
                symbol_specific_score = sum(symbol_sentiments) / len(symbol_sentiments)
            
        # Combinar pontuações em uma pontuação geral
        # - Notícias: 40%
        # - Indicadores macroeconômicos: 50%
        # - Específico do símbolo: 10% adicional
        market_context_score = (
            0.4 * avg_sentiment + 
            0.5 * (inflation_score + interest_score + vix_score + growth_score)
        )
        
        # Adicionar componente específico do símbolo, se disponível
        if symbol and symbol_specific_score != 0:
            market_context_score = 0.9 * market_context_score + 0.1 * symbol_specific_score
        
        # Limitar a pontuação ao intervalo de -1 a 1
        market_context_score = max(-1.0, min(1.0, market_context_score))
        
        # Definir nível de alerta baseado na pontuação
        alert_level = "normal"
        if market_context_score < -0.6:
            alert_level = "critical"
        elif market_context_score < -0.3:
            alert_level = "warning"
        elif market_context_score > 0.6:
            alert_level = "very_positive"
        elif market_context_score > 0.3:
            alert_level = "positive"
            
        # Preparar resultado
        result = {
            'market_context_score': round(market_context_score, 2),
            'sentiment_score': round(avg_sentiment, 2),
            'economic_indicators': {
                'inflation_impact': round(inflation_score, 2),
                'interest_rate_impact': round(interest_score, 2),
                'market_volatility_impact': round(vix_score, 2),
                'economic_growth_impact': round(growth_score, 2)
            },
            'alert_level': alert_level,
            'top_news': news[:5] if news else [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar dados específicos do símbolo, se disponível
        if symbol:
            result['symbol'] = symbol
            result['symbol_specific_score'] = round(symbol_specific_score, 2)
            
        return result
        
    def get_trading_adjustments(self, symbol, base_risk):
        """Retorna ajustes recomendados para parâmetros de trading baseados em contexto externo
        
        Args:
            symbol (str): Símbolo da criptomoeda
            base_risk (float): Risco base configurado para o par
            
        Returns:
            dict: Ajustes recomendados para parâmetros de trading
        """
        self.logger.info(f"Calculando ajustes de trading para {symbol}")
        
        # Obter contexto de mercado
        context = self.calculate_market_context_score(symbol)
        score = context['market_context_score']
        
        # Ajustar parâmetros baseado na pontuação de contexto
        if score < -0.6:  # Contexto muito negativo
            risk_adjustment = 0.4  # Reduzir risco em 60%
            position_adjustment = 0.3  # Reduzir tamanho de posição em 70%
            hold_time_adjustment = 0.7  # Reduzir tempo de retenção em 30%
            take_profit_adjustment = 0.7  # Reduzir objetivo de lucro em 30%
            stop_loss_adjustment = 0.9  # Apertar stop loss em 10%
            entry_condition = "extremely_strict"  # Condições de entrada muito estritas
        
        elif score < -0.3:  # Contexto negativo
            risk_adjustment = 0.6  # Reduzir risco em 40%
            position_adjustment = 0.5  # Reduzir tamanho de posição em 50%
            hold_time_adjustment = 0.8  # Reduzir tempo de retenção em 20%
            take_profit_adjustment = 0.8  # Reduzir objetivo de lucro em 20%
            stop_loss_adjustment = 0.95  # Apertar stop loss em 5%
            entry_condition = "strict"  # Condições de entrada estritas
        
        elif score < 0:  # Contexto levemente negativo
            risk_adjustment = 0.8  # Reduzir risco em 20%
            position_adjustment = 0.8  # Reduzir tamanho de posição em 20%
            hold_time_adjustment = 0.9  # Reduzir tempo de retenção em 10%
            take_profit_adjustment = 0.9  # Reduzir objetivo de lucro em 10%
            stop_loss_adjustment = 0.98  # Apertar stop loss em 2%
            entry_condition = "cautious"  # Condições de entrada cautelosas
            
        elif score > 0.6:  # Contexto muito positivo
            risk_adjustment = 1.2  # Aumentar risco em 20%
            position_adjustment = 1.3  # Aumentar tamanho de posição em 30%
            hold_time_adjustment = 1.3  # Aumentar tempo de retenção em 30%
            take_profit_adjustment = 1.2  # Aumentar objetivo de lucro em 20%
            stop_loss_adjustment = 1.05  # Relaxar stop loss em 5%
            entry_condition = "aggressive"  # Condições de entrada agressivas
            
        elif score > 0.3:  # Contexto positivo
            risk_adjustment = 1.1  # Aumentar risco em 10%
            position_adjustment = 1.2  # Aumentar tamanho de posição em 20%
            hold_time_adjustment = 1.2  # Aumentar tempo de retenção em 20%
            take_profit_adjustment = 1.1  # Aumentar objetivo de lucro em 10%
            stop_loss_adjustment = 1.03  # Relaxar stop loss em 3%
            entry_condition = "opportunistic"  # Condições de entrada oportunistas
            
        else:  # Contexto neutro
            risk_adjustment = 1.0  # Manter risco como está
            position_adjustment = 1.0  # Manter tamanho de posição
            hold_time_adjustment = 1.0  # Manter tempo de retenção
            take_profit_adjustment = 1.0  # Manter objetivo de lucro
            stop_loss_adjustment = 1.0  # Manter stop loss
            entry_condition = "normal"  # Condições de entrada normais
        
        # Calcular risco ajustado (limitado a uma redução máxima de 80% e aumento máximo de 30%)
        adjusted_risk = max(base_risk * 0.2, min(base_risk * 1.3, base_risk * risk_adjustment))
        
        # Preparar e retornar resultado
        result = {
            'base_risk': base_risk,
            'adjusted_risk': round(adjusted_risk, 4),
            'position_size_factor': round(position_adjustment, 2),
            'hold_time_factor': round(hold_time_adjustment, 2),
            'take_profit_factor': round(take_profit_adjustment, 2),
            'stop_loss_factor': round(stop_loss_adjustment, 2),
            'entry_condition': entry_condition,
            'market_context_score': context['market_context_score'],
            'alert_level': context['alert_level'],
            'reason': f"Ajustado com base no contexto de mercado (pontuação: {context['market_context_score']})",
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def fetch_recent_news(self):
        """Busca notícias recentes para análise em tempo real
        
        Returns:
            list: Lista de notícias recentes
        """
        if not self.newsapi_key:
            self.logger.warning("API Key da NewsAPI não configurada")
            return []
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'language': 'en',
                'pageSize': 10,
                'apiKey': self.newsapi_key
            }
            
            self.logger.info("Buscando notícias recentes")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Erro ao buscar notícias: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                self.logger.info(f"Encontrados {len(articles)} artigos recentes")
                return articles
            else:
                self.logger.warning(f"Status não ok: {data.get('status')}")
                return []
        except Exception as e:
            self.logger.error(f"Erro ao buscar notícias: {str(e)}")
            return []

    def get_market_impact_score(self):
        """Calcula o score de impacto no mercado com base nos dados externos
        
        Returns:
            dict: Score de impacto (0-1) e detalhes dos fatores considerados
        """
        news_data = self.fetch_recent_news()
        impact_scores = {
            'economic': self._analyze_news_category(news_data, 'economic'),
            'regulatory': self._analyze_news_category(news_data, 'regulatory'),
            'geopolitical': self._analyze_news_category(news_data, 'geopolitical')
        }
        
        # Calcula score final ponderado
        weighted_score = sum(
            score * self.event_weights[category]
            for category, score in impact_scores.items()
        ) / sum(self.event_weights.values())
        
        return {
            'overall_impact': round(weighted_score, 2),
            'category_scores': impact_scores,
            'risk_level': self._get_risk_level(weighted_score),
            'timestamp': datetime.now().isoformat()
        }

    def _analyze_news_category(self, news_data, category):
        """Analisa notícias de uma categoria específica
        
        Args:
            news_data: Lista de notícias
            category: Categoria de evento (economic/regulatory/geopolitical)
            
        Returns:
            float: Score de impacto (0-1) para a categoria
        """
        category_keywords = self.keywords[category]
        relevant_news = []
        
        for news in news_data:
            text = f"{news.get('title', '')} {news.get('description', '')}"
            if any(keyword.lower() in text.lower() for keyword in category_keywords):
                relevance = self._calculate_news_relevance(news)
                relevant_news.append((news, relevance))
        
        if not relevant_news:
            return 0.0
            
        # Retorna média ponderada das notícias mais relevantes
        scores = [relevance for _, relevance in relevant_news]
        return min(1.0, sum(scores) / len(scores))

    def _calculate_news_relevance(self, news):
        """Calcula relevância de uma notícia específica
        
        Args:
            news: Dicionário com dados da notícia
            
        Returns:
            float: Score de relevância (0-1)
        """
        # Fatores de relevância
        factors = {
            'recency': self._calculate_recency_score(news.get('publishedAt')),
            'source_quality': self._get_source_quality_score(news.get('source', {}).get('name')),
            'sentiment': self._analyze_sentiment(news.get('title', '') + news.get('description', ''))
        }
        
        # Pesos dos fatores
        weights = {'recency': 0.4, 'source_quality': 0.3, 'sentiment': 0.3}
        
        return sum(score * weights[factor] for factor, score in factors.items())

    def _calculate_recency_score(self, published_at):
        """Calcula score de recência da notícia"""
        if not published_at:
            return 0.0
            
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            hours_old = (datetime.now() - pub_date).total_seconds() / 3600
            
            # Score diminui linearmente até 24h
            return max(0.0, 1.0 - (hours_old / 24.0))
        except:
            return 0.0

    def _get_source_quality_score(self, source_name):
        """Score de qualidade da fonte de notícia"""
        # Lista de fontes confiáveis (pode ser expandida)
        trusted_sources = {
            'Reuters': 1.0,
            'Bloomberg': 1.0,
            'Financial Times': 0.9,
            'CNBC': 0.8,
            'CoinDesk': 0.8,
            'Cointelegraph': 0.7
        }
        return trusted_sources.get(source_name, 0.5)

    def _analyze_sentiment(self, text):
        """Análise básica de sentimento do texto
        Retorna score entre 0 (muito negativo) e 1 (muito positivo)
        """
        # Palavras-chave positivas e negativas
        positive_words = ['bullish', 'growth', 'positive', 'adoption', 'support']
        negative_words = ['bearish', 'ban', 'crash', 'risk', 'warning']
        
        text = text.lower()
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count + negative_count == 0:
            return 0.5
            
        return positive_count / (positive_count + negative_count)

    def _get_risk_level(self, impact_score):
        """Determina nível de risco com base no score de impacto"""
        if impact_score >= 0.8:
            return 'CRITICAL'
        elif impact_score >= 0.6:
            return 'HIGH'
        elif impact_score >= 0.4:
            return 'MODERATE'
        elif impact_score >= 0.2:
            return 'LOW'
        return 'MINIMAL'
        

# Teste simples como programa principal
if __name__ == "__main__":
    # Configurar logger
    logger = setup_logger()
    
    # Iniciar analisador
    analyzer = ExternalDataAnalyzer()
    
    # Testar análise
    btc_context = analyzer.calculate_market_context_score("BTC")
    print(json.dumps(btc_context, indent=2))
    
    # Testar ajustes de trading
    adjustments = analyzer.get_trading_adjustments("BTC", 0.01)
    print(json.dumps(adjustments, indent=2))
    
    # Testar análise de impacto de mercado
    impact_score = analyzer.get_market_impact_score()
    print(json.dumps(impact_score, indent=2))
