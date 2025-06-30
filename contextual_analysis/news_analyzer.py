import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging
from datetime import datetime
from .news_api_client import NewsApiClient

# Download recursos necessários do NLTK
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """Analisador de notícias para extrair informações relevantes para o mercado de criptomoedas"""
    
    def __init__(self, news_client=None):
        """Inicializa o analisador de notícias"""
        self.news_client = news_client or NewsApiClient()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.market_impact_keywords = {
            'alta_impacto': ['proibição', 'banimento', 'crash', 'colapso', 'fraude', 'regulação severa', 
                           'investigação', 'hackeado', 'manipulação'],
            'media_impacto': ['regulação', 'adoção', 'volatilidade', 'correção', 'institucional'],
            'baixa_impacto': ['desenvolvimento', 'atualização', 'parceria', 'integração']
        }
    
    def analyze_crypto_news(self, days_back=1):
        """
        Analisa notícias recentes de criptomoedas e retorna métricas de sentimento
        
        Args:
            days_back: Número de dias para analisar
            
        Returns:
            dict: Métricas de análise de sentimento e impacto no mercado
        """
        news_data = self.news_client.get_crypto_news(days_back=days_back)
        
        if news_data.get('status') != 'ok':
            logger.error(f"Erro ao obter notícias: {news_data.get('message')}")
            return {"sentiment_score": 0, "market_impact": "neutro", "alert_level": "baixo"}
        
        articles = news_data.get('articles', [])
        if not articles:
            return {"sentiment_score": 0, "market_impact": "neutro", "alert_level": "baixo"}
        
        # Análise de sentimento
        sentiments = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            content = f"{title}. {description}"
            sentiment = self.sentiment_analyzer.polarity_scores(content)
            sentiments.append(sentiment['compound'])
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Análise de impacto no mercado
        market_impact = self._assess_market_impact(articles)
        
        # Nível de alerta
        alert_level = self._calculate_alert_level(avg_sentiment, market_impact)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sentiment_score": avg_sentiment,
            "market_impact": market_impact,
            "alert_level": alert_level,
            "article_count": len(articles)
        }
    
    def _assess_market_impact(self, articles):
        """Avalia o impacto potencial das notícias no mercado"""
        impact_scores = {'alto': 0, 'médio': 0, 'baixo': 0}
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            # Verifica palavras-chave de impacto
            for keyword in self.market_impact_keywords['alta_impacto']:
                if keyword.lower() in content:
                    impact_scores['alto'] += 1
                    break
                    
            for keyword in self.market_impact_keywords['media_impacto']:
                if keyword.lower() in content:
                    impact_scores['médio'] += 1
                    break
                    
            for keyword in self.market_impact_keywords['baixa_impacto']:
                if keyword.lower() in content:
                    impact_scores['baixo'] += 1
                    break
        
        # Determina o impacto geral
        if impact_scores['alto'] > 0:
            return "alto"
        elif impact_scores['médio'] > impact_scores['baixo']:
            return "médio"
        else:
            return "baixo"
    
    def _calculate_alert_level(self, sentiment_score, market_impact):
        """Calcula o nível de alerta com base no sentimento e impacto"""
        if sentiment_score < -0.5 and market_impact == "alto":
            return "crítico"
        elif sentiment_score < -0.3 or market_impact == "alto":
            return "alto"
        elif sentiment_score < -0.1 or market_impact == "médio":
            return "médio"
        else:
            return "baixo"
