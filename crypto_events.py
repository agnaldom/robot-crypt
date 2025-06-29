#!/usr/bin/env python3
"""
Módulo para integração com APIs de eventos e catalisadores do mercado cripto
Suporta CryptoCompare, CoinMarketCal e CryptoPanic
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta

class CryptoEventMonitor:
    """Classe para monitorar eventos importantes do mercado de criptomoedas"""
    
    def __init__(self, config):
        """Inicializa o monitor de eventos
        
        Args:
            config: Configuração do bot que contém as API keys
        """
        self.config = config
        self.logger = logging.getLogger("robot-crypt")
        self.cache_file = "data/eventos_cache.json"
        self.cache_valid_hours = 8  # Cache válido por 8 horas
        self.events_cache = self._load_cache()
    
    def _load_cache(self):
        """Carrega cache de eventos do arquivo"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
                    
                    # Verifica se o cache ainda é válido
                    if datetime.now() - cache_time < timedelta(hours=self.cache_valid_hours):
                        self.logger.info(f"Usando cache de eventos válido (de {cache_time})")
                        return data
            
            # Se chegou aqui, cache inexistente ou inválido
            self.logger.info("Cache de eventos não encontrado ou expirado")
            return {'timestamp': datetime.now().isoformat(), 'events': {}}
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache de eventos: {str(e)}")
            return {'timestamp': datetime.now().isoformat(), 'events': {}}
    
    def _save_cache(self):
        """Salva cache de eventos em arquivo"""
        try:
            # Atualiza timestamp do cache
            self.events_cache['timestamp'] = datetime.now().isoformat()
            
            # Cria diretório se não existir
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            # Salva cache
            with open(self.cache_file, 'w') as f:
                json.dump(self.events_cache, f, indent=2)
            
            self.logger.info("Cache de eventos salvo com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache de eventos: {str(e)}")
            return False
    
    def checar_eventos_futuros(self, moeda, dias=5):
        """Verifica eventos importantes para uma criptomoeda nos próximos dias
        
        Args:
            moeda (str): Símbolo da criptomoeda (ex: BTC, ETH)
            dias (int): Número de dias a verificar
            
        Returns:
            list: Lista de eventos ordenados por importância
        """
        # Tenta usar cache primeiro
        moeda_upper = moeda.upper()
        if moeda_upper in self.events_cache['events']:
            eventos = self.events_cache['events'][moeda_upper]
            # Filtra apenas eventos futuros
            hoje = datetime.now().date()
            eventos_futuros = [
                e for e in eventos 
                if datetime.fromisoformat(e['date']).date() >= hoje
                and datetime.fromisoformat(e['date']).date() <= hoje + timedelta(days=dias)
            ]
            if eventos_futuros:
                self.logger.info(f"Encontrados {len(eventos_futuros)} eventos em cache para {moeda_upper}")
                return eventos_futuros
        
        # Se não há cache válido, consulta as APIs
        eventos = []
        
        # Tenta consultar CoinMarketCal
        cal_events = self._consultar_coinmarketcal(moeda_upper, dias)
        if cal_events:
            eventos.extend(cal_events)
        
        # Tenta consultar CryptoPanic
        panic_events = self._consultar_cryptopanic(moeda_upper, dias)
        if panic_events:
            eventos.extend(panic_events)
        
        # Salva no cache
        self.events_cache['events'][moeda_upper] = eventos
        self._save_cache()
        
        return eventos
    
    def _consultar_coinmarketcal(self, moeda, dias=5):
        """Consulta eventos futuros na API do CoinMarketCal"""
        eventos = []
        api_key = os.environ.get("COINMARKETCAL_API_KEY", "")
        
        if not api_key:
            self.logger.warning("API Key do CoinMarketCal não encontrada")
            return eventos
        
        try:
            # Calcula datas para filtro
            hoje = datetime.now().date()
            data_fim = (hoje + timedelta(days=dias)).isoformat()
            
            # API Endpoint
            url = "https://developers.coinmarketcal.com/v1/events"
            
            # Parâmetros de consulta
            params = {
                "max": 30,
                "dateRangeStart": hoje.isoformat(),
                "dateRangeEnd": data_fim,
                "coins": moeda
            }
            
            # Headers (autenticação)
            headers = {
                "x-api-key": api_key,
                "Accept": "application/json",
                "Accept-Encoding": "deflate, gzip"
            }
            
            # Faz a requisição
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('body', []):
                    evento = {
                        'title': item.get('title', ''),
                        'date': item.get('date_event', hoje.isoformat()),
                        'source': 'CoinMarketCal',
                        'url': item.get('proof', ''),
                        'description': item.get('description', ''),
                        'impact': self._avaliar_impacto(item)
                    }
                    eventos.append(evento)
                
                self.logger.info(f"Obtidos {len(eventos)} eventos do CoinMarketCal para {moeda}")
            else:
                self.logger.warning(f"Erro ao consultar CoinMarketCal: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Erro ao consultar CoinMarketCal: {str(e)}")
            
        return eventos
    
    def _consultar_cryptopanic(self, moeda, dias=5):
        """Consulta notícias e eventos na API do CryptoPanic"""
        eventos = []
        api_key = os.environ.get("CRYPTOPANIC_API_KEY", "")
        
        if not api_key:
            self.logger.warning("API Key do CryptoPanic não encontrada")
            return eventos
        
        try:
            # API Endpoint
            url = "https://cryptopanic.com/api/v1/posts/"
            
            # Parâmetros de consulta
            params = {
                "auth_token": api_key,
                "currencies": moeda,
                "filter": "important",
                "public": "true"
            }
            
            # Faz a requisição
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                hoje = datetime.now()
                limite = hoje + timedelta(days=dias)
                
                for item in data.get('results', []):
                    # Verifica se a notícia tem relação com eventos futuros
                    if any(keyword in item.get('title', '').lower() for keyword in 
                           ['launch', 'upcoming', 'release', 'update', 'fork', 'event', 
                            'listing', 'partnership', 'airdrop', 'mainnet']):
                        
                        # Cria um evento a partir da notícia
                        data_evento = hoje + timedelta(days=1)  # Assume evento próximo
                        evento = {
                            'title': item.get('title', ''),
                            'date': data_evento.isoformat(),
                            'source': 'CryptoPanic',
                            'url': item.get('url', ''),
                            'description': item.get('title', ''),  # Usa título como descrição
                            'impact': self._avaliar_impacto_texto(item.get('title', ''))
                        }
                        eventos.append(evento)
                
                self.logger.info(f"Obtidos {len(eventos)} eventos importantes do CryptoPanic para {moeda}")
                
        except Exception as e:
            self.logger.error(f"Erro ao consultar CryptoPanic: {str(e)}")
            
        return eventos
    
    def _avaliar_impacto(self, evento):
        """Avalia o impacto de um evento com base em seu tipo e características"""
        # Lista de palavras-chave que indicam alto impacto
        high_impact = ['mainnet', 'launch', 'major', 'fork', 'listing', 'halving', 'partnership', 'acquisition']
        
        # Lista de palavras-chave que indicam impacto médio
        medium_impact = ['update', 'release', 'event', 'integration', 'testnet']
        
        title = evento.get('title', '').lower()
        description = evento.get('description', '').lower()
        texto = title + ' ' + description
        
        # Avaliar impacto
        if any(keyword in texto for keyword in high_impact):
            return "Alto"
        elif any(keyword in texto for keyword in medium_impact):
            return "Médio"
        else:
            return "Baixo"
    
    def _avaliar_impacto_texto(self, texto):
        """Avalia o impacto com base no texto"""
        # Lista de palavras-chave que indicam alto impacto
        high_impact = ['mainnet', 'launch', 'major', 'fork', 'listing', 'halving', 'partnership', 'acquisition']
        
        # Lista de palavras-chave que indicam impacto médio
        medium_impact = ['update', 'release', 'event', 'integration', 'testnet']
        
        texto = texto.lower()
        
        # Avaliar impacto
        if any(keyword in texto for keyword in high_impact):
            return "Alto"
        elif any(keyword in texto for keyword in medium_impact):
            return "Médio"
        else:
            return "Baixo"
            
    def existe_evento_importante(self, moeda, dias=5):
        """Verifica se existe algum evento importante para a moeda
        
        Args:
            moeda (str): Símbolo da criptomoeda (ex: BTC, ETH)
            dias (int): Número de dias a verificar
            
        Returns:
            bool: True se existir algum evento de alto impacto, False caso contrário
        """
        eventos = self.checar_eventos_futuros(moeda, dias)
        return any(evento['impact'] == 'Alto' for evento in eventos)
