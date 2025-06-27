import requests
from bs4 import BeautifulSoup
import re
import logging
import time
from datetime import datetime
from config import BINANCE_ANNOUNCEMENTS_URL

logger = logging.getLogger(__name__)

class ListingDetector:
    def __init__(self):
        self.announcements_url = BINANCE_ANNOUNCEMENTS_URL
        self.known_listings = set()
        
    def _parse_announcement_date(self, date_str):
        """Converte a string de data do anúncio para um objeto datetime."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.error(f"Formato de data inválido: {date_str}")
            return None
    
    def _extract_symbol_from_title(self, title):
        """Extrai o símbolo da moeda do título do anúncio."""
        # Padrões comuns para títulos de listagem
        patterns = [
            r"Binance Will List (\w+)",
            r"Binance Lists (\w+)",
            r"(\w+) Trading Now",
            r"(\w+) Now Available"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        return None
    
    def scan_new_listings(self):
        """Verifica novos anúncios de listagem no site da Binance."""
        try:
            response = requests.get(self.announcements_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            announcements = []
            
            # A estrutura HTML exata depende do site da Binance e pode mudar
            # Esta é uma implementação genérica que deve ser ajustada
            for announcement in soup.select('.announcement-item'):
                title_elem = announcement.select_one('.title')
                date_elem = announcement.select_one('.date')
                link_elem = announcement.select_one('a')
                
                if title_elem and date_elem and link_elem:
                    title = title_elem.text.strip()
                    date_str = date_elem.text.strip()
                    link = link_elem.get('href')
                    
                    # Verificar se é um anúncio de nova listagem
                    if "list" in title.lower() or "new" in title.lower():
                        symbol = self._extract_symbol_from_title(title)
                        if symbol:
                            announcements.append({
                                'title': title,
                                'date': self._parse_announcement_date(date_str),
                                'link': link,
                                'symbol': symbol
                            })
            
            # Filtra apenas anúncios novos
            new_listings = []
            for announcement in announcements:
                listing_id = f"{announcement['symbol']}_{announcement['date']}"
                if listing_id not in self.known_listings:
                    self.known_listings.add(listing_id)
                    new_listings.append(announcement)
            
            return new_listings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar o site da Binance: {e}")
            return []
