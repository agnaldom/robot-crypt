import requests
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NewsApiClient:
    """Cliente para obtenção de notícias financeiras e de criptomoedas da NewsAPI"""
    
    def __init__(self, api_key=None):
        """Inicializa o cliente da NewsAPI com a chave de API"""
        self.api_key = api_key or os.environ.get('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("API key para NewsAPI não encontrada")
        self.base_url = "https://newsapi.org/v2"
        
    def get_crypto_news(self, keywords=None, days_back=1, language="pt", sort_by="publishedAt"):
        """
        Obtém notícias relacionadas a criptomoedas
        
        Args:
            keywords: Lista de palavras-chave para filtrar notícias (default: criptomoedas, bitcoin, ethereum)
            days_back: Quantos dias para trás buscar notícias
            language: Idioma das notícias
            sort_by: Critério de ordenação
            
        Returns:
            dict: Resposta da API com as notícias
        """
        if keywords is None:
            keywords = ["criptomoeda", "bitcoin", "ethereum", "mercado digital", "blockchain"]
            
        query = " OR ".join(keywords)
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        params = {
            "q": query,
            "from": from_date,
            "sortBy": sort_by,
            "language": language,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter notícias: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_economic_news(self, keywords=None, days_back=1, language="pt"):
        """
        Obtém notícias relacionadas a eventos econômicos globais
        
        Args:
            keywords: Lista de palavras-chave para filtrar notícias
            days_back: Quantos dias para trás buscar notícias
            language: Idioma das notícias
            
        Returns:
            dict: Resposta da API com as notícias
        """
        if keywords is None:
            keywords = ["banco central", "inflação", "taxa de juros", "economia global", 
                       "regulação financeira", "mercado financeiro"]
            
        return self.get_crypto_news(keywords, days_back, language)
