#!/usr/bin/env python3
"""
Módulo avançado para análise de contexto de mercado integrando múltiplas fontes de dados
incluindo notícias, eventos macroeconômicos, tendências sociais e indicadores técnicos.
"""
import os
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Configuração de logging
logger = logging.getLogger(__name__)

class AdvancedContextAnalyzer:
    """
    Analisador de contexto avançado que integra múltiplas fontes de dados para
    fornecer uma visão holística do ambiente de mercado de criptomoedas.
    """
    
    def __init__(self, config=None, news_analyzer=None):
        """
        Inicializa o analisador de contexto avançado
        
        Args:
            config: Objeto de configuração do robô
            news_analyzer: Instância do analisador de notícias
        """
        self.config = config
        self.news_analyzer = news_analyzer
        
        # Inicializar o analisador de sentimento se necessário
        try:
            import nltk
            try:
                nltk.data.find('vader_lexicon')
            except LookupError:
                nltk.download('vader_lexicon')
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except ImportError:
            logger.warning("NLTK não disponível. Análise de sentimento limitada.")
            self.sentiment_analyzer = None
            
        # Configuração de fontes de dados externas
        self.apis = {
            'news': {
                'url': 'https://newsapi.org/v2',
                'key': os.environ.get('NEWS_API_KEY')
            },
            'economic': {
                'url': 'https://api.tradingeconomics.com/data',
                'key': os.environ.get('TRADING_ECONOMICS_KEY')
            },
            'social': {
                'url': 'https://api.social-pulse.com/v1',  # API fictícia para exemplo
                'key': os.environ.get('SOCIAL_PULSE_KEY')
            }
        }
        
        # Diretório para cache e dados históricos
        self.data_dir = Path(__file__).parent.parent / "data" / "contextual"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Parâmetros do modelo
        self.model = None
        self.scaler = StandardScaler()
        self.model_ready = False
        self.load_or_initialize_model()
        
    def load_or_initialize_model(self):
        """Carrega o modelo existente ou inicializa um novo"""
        model_path = self.data_dir / "context_model.pkl"
        
        if model_path.exists():
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Modelo de análise contextual carregado com sucesso")
                self.model_ready = True
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {str(e)}")
                self.initialize_new_model()
        else:
            self.initialize_new_model()
            
    def initialize_new_model(self):
        """Inicializa um novo modelo de análise contextual"""
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        logger.info("Novo modelo de análise contextual inicializado")
        self.model_ready = False  # Marcado como não treinado
        
    def save_model(self):
        """Salva o modelo treinado em disco"""
        if not self.model_ready:
            logger.warning("Modelo não está pronto para ser salvo (não treinado)")
            return False
            
        try:
            import pickle
            model_path = self.data_dir / "context_model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info("Modelo de análise contextual salvo com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {str(e)}")
            return False
            
    def get_economic_indicators(self):
        """
        Obtém indicadores econômicos atuais
        
        Returns:
            dict: Dicionário com indicadores econômicos relevantes
        """
        # Em um ambiente de produção, esta função deveria se conectar a uma 
        # API de dados econômicos real. Por enquanto, simulamos dados.
        
        cache_file = self.data_dir / "economic_indicators_cache.json"
        
        # Verificar se temos dados em cache recentes (menos de 6 horas)
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    timestamp = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
                    
                    if datetime.now() - timestamp < timedelta(hours=6):
                        logger.info("Usando dados econômicos em cache")
                        return data
            except Exception as e:
                logger.error(f"Erro ao ler cache de indicadores econômicos: {str(e)}")
        
        # Se não temos cache ou está desatualizado, obter novos dados
        try:
            # Aqui em um ambiente real faríamos uma chamada à API
            # Como exemplo, usamos dados simulados com alguma variação
            
            # Base values representando a situação econômica atual
            base_inflation = 4.2 + np.random.normal(0, 0.2)
            base_interest = 5.25 + np.random.normal(0, 0.1)
            base_unemployment = 3.7 + np.random.normal(0, 0.1)
            base_gdp_growth = 2.3 + np.random.normal(0, 0.3)
            base_dollar_index = 103.5 + np.random.normal(0, 0.5)
            base_sp500_change = 0.4 + np.random.normal(0, 0.2)
            base_vix = 16.5 + np.random.normal(0, 1.0)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'indicators': {
                    'inflation_rate': max(0, round(base_inflation, 2)),
                    'interest_rate': max(0, round(base_interest, 2)),
                    'unemployment': max(0, round(base_unemployment, 2)),
                    'gdp_growth': round(base_gdp_growth, 2),
                    'dollar_index': max(0, round(base_dollar_index, 2)),
                    'sp500_change': round(base_sp500_change, 2),
                    'vix_index': max(0, round(base_vix, 2))
                },
                'trends': {
                    'inflation': 'rising' if base_inflation > 4.3 else 'stable',
                    'interest_rates': 'stable',
                    'economic_growth': 'slowing' if base_gdp_growth < 2.0 else 'stable',
                    'market_stress': 'elevated' if base_vix > 20 else 'normal'
                }
            }
            
            # Salvar em cache
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            return data
            
        except Exception as e:
            logger.error(f"Erro ao obter indicadores econômicos: {str(e)}")
            # Retornar valores padrão em caso de erro
            return {
                'timestamp': datetime.now().isoformat(),
                'indicators': {
                    'inflation_rate': 4.2,
                    'interest_rate': 5.25,
                    'unemployment': 3.7,
                    'gdp_growth': 2.0,
                    'dollar_index': 103.5,
                    'sp500_change': 0.0,
                    'vix_index': 18.0
                },
                'trends': {
                    'inflation': 'stable',
                    'interest_rates': 'stable',
                    'economic_growth': 'stable',
                    'market_stress': 'normal'
                }
            }
    
    def get_social_sentiment(self, cryptocurrency=None):
        """
        Obtém o sentimento social sobre criptomoedas de plataformas como Twitter/X, Reddit, etc.
        
        Args:
            cryptocurrency (str, optional): Símbolo da criptomoeda específica
            
        Returns:
            dict: Dados de sentimento social
        """
        # Neste exemplo, simulamos dados de sentimento social
        # Em um ambiente real, isso conectaria a APIs como Twitter, Reddit, etc.
        
        crypto_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binance',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba'
        }
        
        cache_file = self.data_dir / "social_sentiment_cache.json"
        
        # Verificar se temos dados em cache recentes (menos de 2 horas)
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    timestamp = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
                    
                    if datetime.now() - timestamp < timedelta(hours=2):
                        logger.info("Usando dados de sentimento social em cache")
                        if cryptocurrency:
                            # Se buscando uma crypto específica, filtrar resultados
                            crypto_name = crypto_map.get(cryptocurrency, cryptocurrency.lower())
                            if crypto_name in data['sentiments']:
                                return {
                                    'timestamp': data['timestamp'],
                                    'sentiments': {crypto_name: data['sentiments'][crypto_name]},
                                    'overall_sentiment': data['sentiments'][crypto_name]['sentiment_score']
                                }
                        return data
            except Exception as e:
                logger.error(f"Erro ao ler cache de sentimento social: {str(e)}")
        
        # Gerar dados simulados
        sentiments = {}
        overall_volume = 0
        overall_sentiment = 0
        
        for symbol, name in crypto_map.items():
            # Volume de menções (ajustado para dar mais peso a BTC e ETH)
            if symbol in ['BTC', 'ETH']:
                volume = np.random.randint(5000, 20000)
            elif symbol in ['BNB', 'XRP', 'ADA', 'SOL']:
                volume = np.random.randint(1000, 5000)
            else:
                volume = np.random.randint(100, 2000)
                
            # Sentimento (-1 a 1)
            # Adiciona alguma correlação entre criptos
            base_sentiment = np.random.normal(0.1, 0.2)  # Ligeiramente positivo em média
            sentiment = max(-1, min(1, base_sentiment + np.random.normal(0, 0.3)))
            
            # Calcular o momentum (taxa de mudança)
            momentum = np.random.uniform(-0.5, 0.5)
            
            sentiments[name] = {
                'mentions': volume,
                'sentiment_score': round(sentiment, 2),
                'momentum': round(momentum, 2),
                'bullish_percentage': round(50 + (sentiment * 50), 1),
                'bearish_percentage': round(50 - (sentiment * 50), 1)
            }
            
            overall_volume += volume
            overall_sentiment += sentiment * volume
        
        # Calcular sentimento geral ponderado pelo volume
        if overall_volume > 0:
            overall_sentiment = overall_sentiment / overall_volume
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'sentiments': sentiments,
            'overall_sentiment': round(overall_sentiment, 2),
            'trending_topics': [
                'bitcoin etf',
                'ethereum updates',
                'regulations',
                'defi',
                'nft market'
            ]
        }
        
        # Salvar em cache
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        # Se buscando uma crypto específica, filtrar resultados
        if cryptocurrency:
            crypto_name = crypto_map.get(cryptocurrency, cryptocurrency.lower())
            if crypto_name in sentiments:
                return {
                    'timestamp': data['timestamp'],
                    'sentiments': {crypto_name: sentiments[crypto_name]},
                    'overall_sentiment': sentiments[crypto_name]['sentiment_score']
                }
        
        return data
    
    def get_regulatory_events(self):
        """
        Obtém eventos regulatórios recentes que podem impactar o mercado de criptomoedas
        
        Returns:
            list: Lista de eventos regulatórios
        """
        # Para um exemplo real, aqui você conectaria a uma API de notícias
        # e filtraria por tópicos regulatórios, ou usaria uma API especializada
        
        # Por enquanto, retornamos dados simulados
        current_date = datetime.now()
        
        # Lista de possíveis eventos regulatórios (simulados)
        possible_events = [
            {
                'title': 'SEC anuncia novas diretrizes para ETFs de Bitcoin',
                'authority': 'SEC',
                'region': 'Estados Unidos',
                'impact': 'medium',
                'sentiment': 'positive',
                'date': (current_date - timedelta(days=3)).isoformat()
            },
            {
                'title': 'União Europeia avança em regulamentação MiCA',
                'authority': 'European Commission',
                'region': 'Europa',
                'impact': 'high',
                'sentiment': 'neutral',
                'date': (current_date - timedelta(days=7)).isoformat()
            },
            {
                'title': 'Banco Central do Brasil publica novas regras para exchanges',
                'authority': 'Banco Central',
                'region': 'Brasil',
                'impact': 'medium',
                'sentiment': 'neutral',
                'date': (current_date - timedelta(days=5)).isoformat()
            },
            {
                'title': 'China reforça proibição de mineração de criptomoedas',
                'authority': 'PBOC',
                'region': 'China',
                'impact': 'high',
                'sentiment': 'negative',
                'date': (current_date - timedelta(days=10)).isoformat()
            },
            {
                'title': 'Japão simplifica processo de listagem de criptomoedas',
                'authority': 'FSA',
                'region': 'Japão',
                'impact': 'low',
                'sentiment': 'positive',
                'date': (current_date - timedelta(days=12)).isoformat()
            }
        ]
        
        # Determinamos de forma pseudo-aleatória quais eventos estão "ativos"
        # com base no dia atual (para manter consistência entre chamadas)
        day_seed = current_date.day + current_date.month
        np.random.seed(day_seed)
        
        # Seleciona alguns eventos aleatórios
        num_events = np.random.randint(1, 4)  # 1 a 3 eventos ativos
        selected_indices = np.random.choice(range(len(possible_events)), size=num_events, replace=False)
        
        events = [possible_events[i] for i in selected_indices]
        
        # Adiciona probabilisticamente um evento "breaking" mais recente
        if np.random.random() < 0.2:  # 20% de chance
            breaking_events = [
                {
                    'title': 'BREAKING: Novo projeto de lei sobre criptomoedas proposto no Senado',
                    'authority': 'US Senate',
                    'region': 'Estados Unidos',
                    'impact': 'high',
                    'sentiment': np.random.choice(['positive', 'negative', 'neutral']),
                    'date': current_date.isoformat(),
                    'breaking': True
                },
                {
                    'title': 'BREAKING: G20 anuncia framework global para regulação de criptomoedas',
                    'authority': 'G20',
                    'region': 'Global',
                    'impact': 'high',
                    'sentiment': np.random.choice(['positive', 'negative', 'neutral']),
                    'date': current_date.isoformat(),
                    'breaking': True
                }
            ]
            events.append(np.random.choice(breaking_events))
        
        return sorted(events, key=lambda x: x['date'], reverse=True)
    
    def analyze_all_context_factors(self, cryptocurrency=None):
        """
        Realiza uma análise completa de todos os fatores contextuais
        
        Args:
            cryptocurrency (str, optional): Símbolo da criptomoeda específica
            
        Returns:
            dict: Análise completa do contexto de mercado
        """
        # Obtém todos os dados contextuais
        economic_data = self.get_economic_indicators()
        social_data = self.get_social_sentiment(cryptocurrency)
        regulatory_events = self.get_regulatory_events()
        
        # Obtém notícias e análise de sentimento se tivermos um analisador disponível
        news_sentiment = {}
        if self.news_analyzer:
            try:
                news_sentiment = self.news_analyzer.analyze_crypto_news(days_back=2)
            except Exception as e:
                logger.error(f"Erro ao analisar notícias: {str(e)}")
                news_sentiment = {"sentiment_score": 0, "market_impact": "neutro", "alert_level": "baixo"}
        
        # Calcular o score de contexto geral
        context_scores = {
            'economic': self._calculate_economic_context_score(economic_data),
            'social': social_data.get('overall_sentiment', 0),
            'news': news_sentiment.get('sentiment_score', 0),
            'regulatory': self._calculate_regulatory_context_score(regulatory_events)
        }
        
        # Calcular o score geral - ponderação:
        # - Econômico: 40%
        # - Social: 25%
        # - Notícias: 20%
        # - Regulatório: 15%
        overall_context_score = (
            0.40 * context_scores['economic'] +
            0.25 * context_scores['social'] +
            0.20 * context_scores['news'] +
            0.15 * context_scores['regulatory']
        )
        
        # Limitar o score ao intervalo de -1 a 1
        overall_context_score = max(-1.0, min(1.0, overall_context_score))
        
        # Determinar o nível de impacto no mercado
        if overall_context_score < -0.6:
            market_impact = 'extremely_negative'
            alert_level = 'critical'
            risk_adjustment = 0.5  # Reduzir risco em 50%
            trading_advice = "Considerar pausar novas operações e reduzir exposição"
        elif overall_context_score < -0.3:
            market_impact = 'negative'
            alert_level = 'high'
            risk_adjustment = 0.7  # Reduzir risco em 30%
            trading_advice = "Reduzir tamanho das posições e aumentar stop-loss"
        elif overall_context_score < -0.1:
            market_impact = 'slightly_negative'
            alert_level = 'moderate'
            risk_adjustment = 0.9  # Reduzir risco em 10%
            trading_advice = "Cautela adicional, stop-loss mais próximos"
        elif overall_context_score <= 0.1:
            market_impact = 'neutral'
            alert_level = 'low'
            risk_adjustment = 1.0  # Manter risco normal
            trading_advice = "Manter estratégia regular"
        elif overall_context_score <= 0.3:
            market_impact = 'slightly_positive'
            alert_level = 'low'
            risk_adjustment = 1.0  # Manter risco normal
            trading_advice = "Manter estratégia regular com viés positivo"
        elif overall_context_score <= 0.6:
            market_impact = 'positive'
            alert_level = 'opportunity'
            risk_adjustment = 1.1  # Aumentar risco em 10%
            trading_advice = "Considerar oportunidades de entrada mais agressivas"
        else:
            market_impact = 'extremely_positive'
            alert_level = 'opportunity'
            risk_adjustment = 1.2  # Aumentar risco em 20%
            trading_advice = "Ambiente favorável para aumentar posições"
        
        # Criar resposta detalhada
        response = {
            'timestamp': datetime.now().isoformat(),
            'cryptocurrency': cryptocurrency,
            'overall_context_score': round(overall_context_score, 2),
            'market_impact': market_impact,
            'alert_level': alert_level,
            'risk_adjustment': risk_adjustment,
            'trading_advice': trading_advice,
            'component_scores': {
                'economic': round(context_scores['economic'], 2),
                'social': round(context_scores['social'], 2),
                'news': round(context_scores['news'], 2),
                'regulatory': round(context_scores['regulatory'], 2)
            },
            'details': {
                'economic_indicators': economic_data['indicators'],
                'economic_trends': economic_data['trends'],
                'social_sentiment': social_data.get('sentiments', {}),
                'regulatory_events': regulatory_events[:3],  # Top 3 mais recentes
                'news_sentiment': news_sentiment
            }
        }
        
        # Adicionar fatores específicos para a criptomoeda, se disponíveis
        if cryptocurrency:
            crypto_specific = self._get_cryptocurrency_specific_factors(cryptocurrency)
            response['crypto_specific_factors'] = crypto_specific
        
        return response
    
    def _calculate_economic_context_score(self, economic_data):
        """
        Calcula o score de contexto econômico baseado nos indicadores
        
        Args:
            economic_data (dict): Dados econômicos
            
        Returns:
            float: Score de contexto econômico (-1 a 1)
        """
        indicators = economic_data.get('indicators', {})
        
        # Fatores que tendem a afetar o mercado de criptomoedas
        # - Taxa de juros alta: negativa (investidores preferem renda fixa)
        # - Inflação alta: tradicionalmente positiva (hedge contra inflação)
        # - VIX alto: negativo (aversão a risco)
        # - Crescimento PIB alto: positivo (maior investimento em ativos de risco)
        
        interest_score = -0.5 * (indicators.get('interest_rate', 5.0) / 10.0)  # Normalizado
        inflation_score = 0.2 * (indicators.get('inflation_rate', 4.0) / 10.0)  # Normalizado
        vix_score = -0.4 * (indicators.get('vix_index', 20.0) / 40.0)  # Normalizado
        gdp_score = 0.3 * (indicators.get('gdp_growth', 2.0) / 4.0)  # Normalizado
        dollar_score = -0.2 * ((indicators.get('dollar_index', 100.0) - 90) / 30.0)  # Normalizado
        
        # Combinação ponderada
        economic_score = (
            interest_score + 
            inflation_score + 
            vix_score + 
            gdp_score + 
            dollar_score
        )
        
        # Normalizar para -1 a 1
        economic_score = max(-1.0, min(1.0, economic_score))
        
        return economic_score
    
    def _calculate_regulatory_context_score(self, regulatory_events):
        """
        Calcula o score de contexto regulatório baseado em eventos recentes
        
        Args:
            regulatory_events (list): Lista de eventos regulatórios
            
        Returns:
            float: Score de contexto regulatório (-1 a 1)
        """
        if not regulatory_events:
            return 0.0
            
        # Pontuação inicial
        score = 0.0
        
        # Pesos para diferentes níveis de impacto
        impact_weights = {
            'high': 0.5,
            'medium': 0.3,
            'low': 0.1
        }
        
        # Pesos para diferentes sentimentos
        sentiment_values = {
            'positive': 0.5,
            'neutral': 0.0,
            'negative': -0.5
        }
        
        # Considera o tempo do evento (eventos mais recentes têm mais peso)
        now = datetime.now()
        
        for event in regulatory_events:
            # Calcula a idade do evento em dias
            event_date = datetime.fromisoformat(event['date'].split('T')[0])
            days_old = (now - event_date).days
            
            # Fator de decaimento temporal (eventos mais antigos têm menos impacto)
            time_factor = max(0.1, 1.0 - (days_old / 30.0))  # Até 30 dias, depois mínimo de 0.1
            
            # Fator de "breaking news" - eventos marcados como "breaking" têm mais impacto
            breaking_factor = 1.5 if event.get('breaking', False) else 1.0
            
            # Score do evento individual
            impact = impact_weights.get(event['impact'], 0.2)
            sentiment = sentiment_values.get(event['sentiment'], 0.0)
            
            event_score = sentiment * impact * time_factor * breaking_factor
            
            # Acumula no score total
            score += event_score
        
        # Normaliza para o número de eventos considerados
        if regulatory_events:
            score = score / len(regulatory_events)
        
        # Limita ao intervalo -1 a 1
        score = max(-1.0, min(1.0, score))
        
        return score
    
    def _get_cryptocurrency_specific_factors(self, cryptocurrency):
        """
        Obtém fatores específicos para uma criptomoeda
        
        Args:
            cryptocurrency (str): Símbolo da criptomoeda
            
        Returns:
            dict: Fatores específicos da criptomoeda
        """
        # Aqui em um ambiente real, você buscaria informações específicas sobre
        # o projeto, como atualizações recentes, eventos de desenvolvimento, etc.
        
        # Para fins de demonstração, criamos alguns dados simulados
        
        # Mapeamento de nomes por símbolo
        crypto_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'Binance Coin',
            'XRP': 'Ripple',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'SHIB': 'Shiba Inu'
        }
        
        name = crypto_names.get(cryptocurrency, cryptocurrency)
        
        # Alguns eventos específicos possíveis (simulados)
        possible_events = [
            {
                'type': 'development',
                'title': f'Nova atualização de protocolo para {name}',
                'impact': 'medium',
                'sentiment': 'positive'
            },
            {
                'type': 'partnership',
                'title': f'{name} anuncia parceria com empresa de pagamentos',
                'impact': 'medium',
                'sentiment': 'positive'
            },
            {
                'type': 'adoption',
                'title': f'Grande empresa adiciona {name} ao seu balanço',
                'impact': 'high',
                'sentiment': 'positive'
            },
            {
                'type': 'security',
                'title': f'Vulnerabilidade descoberta em carteiras de {name}',
                'impact': 'medium',
                'sentiment': 'negative'
            },
            {
                'type': 'market',
                'title': f'Aumento na liquidez de mercado para {name}',
                'impact': 'low',
                'sentiment': 'positive'
            }
        ]
        
        # Selecionar alguns eventos aleatórios baseados no símbolo para consistência
        seed = sum(ord(c) for c in cryptocurrency) + datetime.now().day
        np.random.seed(seed)
        
        num_events = np.random.randint(0, 3)  # 0 a 2 eventos
        events = []
        
        if num_events > 0:
            event_indices = np.random.choice(range(len(possible_events)), size=num_events, replace=False)
            events = [possible_events[i] for i in event_indices]
        
        # Calcular um score de desenvolvimento relativo
        dev_activity = {
            'BTC': np.random.uniform(0.7, 1.0),  # Bitcoin tem desenvolvimento constante
            'ETH': np.random.uniform(0.8, 1.0),  # Ethereum tem muito desenvolvimento
            'ADA': np.random.uniform(0.6, 0.9),  # Cardano tem bom desenvolvimento
            'SOL': np.random.uniform(0.7, 0.9),  # Solana tem bom desenvolvimento
        }.get(cryptocurrency, np.random.uniform(0.3, 0.8))  # Para outras moedas
        
        # Calcular correlação com Bitcoin (todas têm alguma correlação)
        btc_correlation = 0.8  # Valor padrão
        if cryptocurrency in ['BTC']:
            btc_correlation = 1.0  # Bitcoin tem correlação perfeita consigo mesmo
        elif cryptocurrency in ['ETH', 'BNB']:
            btc_correlation = np.random.uniform(0.7, 0.9)  # Alta correlação
        elif cryptocurrency in ['ADA', 'SOL', 'XRP']:
            btc_correlation = np.random.uniform(0.5, 0.8)  # Correlação média
        elif cryptocurrency in ['DOGE', 'SHIB']:
            btc_correlation = np.random.uniform(0.3, 0.7)  # Menor correlação (meme coins)
        
        # Retornar fatores específicos
        return {
            'name': name,
            'symbol': cryptocurrency,
            'development_activity': round(dev_activity, 2),
            'btc_correlation': round(btc_correlation, 2),
            'current_sentiment': round(np.random.uniform(-1, 1), 2),
            'recent_events': events
        }
    
    def get_trading_adjustments(self, cryptocurrency, base_risk):
        """
        Calcula ajustes de trading recomendados com base no contexto atual
        
        Args:
            cryptocurrency (str): Símbolo da criptomoeda
            base_risk (float): Risco base configurado
            
        Returns:
            dict: Ajustes de parâmetros de trading recomendados
        """
        # Obter análise contextual completa
        context = self.analyze_all_context_factors(cryptocurrency)
        
        # Obter o score de contexto global e o ajuste de risco recomendado
        context_score = context['overall_context_score']
        risk_adjustment = context['risk_adjustment']
        
        # Calcular ajustes específicos para diferentes parâmetros
        # - stop_loss: mais apertado em mercados negativos, mais solto em positivos
        # - take_profit: mais próximo em mercados negativos, mais distante em positivos
        # - position_size: menor em mercados negativos, maior em positivos
        # - max_hold_time: menor em mercados negativos, maior em positivos
        
        # Ajustar stop loss (inverso do risk_adjustment)
        if context_score < -0.3:
            stop_loss_factor = max(0.7, 1.0 - (abs(context_score) * 0.5))  # Mais apertado (0.7 a 1.0)
        elif context_score > 0.3:
            stop_loss_factor = min(1.3, 1.0 + (context_score * 0.3))  # Mais solto (1.0 a 1.3)
        else:
            stop_loss_factor = 1.0  # Neutro
            
        # Ajustar take profit
        if context_score < -0.3:
            take_profit_factor = max(0.7, 1.0 - (abs(context_score) * 0.4))  # Mais próximo (0.7 a 1.0)
        elif context_score > 0.3:
            take_profit_factor = min(1.5, 1.0 + (context_score * 0.6))  # Mais distante (1.0 a 1.5)
        else:
            take_profit_factor = 1.0  # Neutro
            
        # Ajustar tamanho da posição (baseado no risk_adjustment)
        position_size_factor = risk_adjustment
        
        # Ajustar tempo máximo de retenção
        if context_score < -0.3:
            hold_time_factor = max(0.5, 1.0 - (abs(context_score) * 0.7))  # Menor (0.5 a 1.0)
        elif context_score > 0.3:
            hold_time_factor = min(2.0, 1.0 + (context_score * 1.0))  # Maior (1.0 a 2.0)
        else:
            hold_time_factor = 1.0  # Neutro
            
        # Ajustar estratégia recomendada
        if context_score < -0.5:
            strategy_recommendation = "defensive"
            entry_condition = "very_strict"
        elif context_score < -0.2:
            strategy_recommendation = "cautious"
            entry_condition = "strict"
        elif context_score < 0.2:
            strategy_recommendation = "neutral"
            entry_condition = "normal"
        elif context_score < 0.5:
            strategy_recommendation = "growth"
            entry_condition = "flexible"
        else:
            strategy_recommendation = "aggressive"
            entry_condition = "opportunistic"
            
        # Montar resposta
        result = {
            'cryptocurrency': cryptocurrency,
            'base_risk': base_risk,
            'adjusted_risk': round(base_risk * risk_adjustment, 4),
            'context_score': context['overall_context_score'],
            'market_impact': context['market_impact'],
            'alert_level': context['alert_level'],
            'adjustments': {
                'stop_loss_factor': round(stop_loss_factor, 2),
                'take_profit_factor': round(take_profit_factor, 2),
                'position_size_factor': round(position_size_factor, 2),
                'hold_time_factor': round(hold_time_factor, 2)
            },
            'recommendations': {
                'strategy': strategy_recommendation,
                'entry_condition': entry_condition,
                'trading_advice': context['trading_advice']
            },
            'factors_considered': {
                'economic': context['component_scores']['economic'],
                'social': context['component_scores']['social'],
                'news': context['component_scores']['news'],
                'regulatory': context['component_scores']['regulatory']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def train_model_with_historical_data(self, min_samples=50):
        """
        Treina o modelo de análise contextual com dados históricos
        
        Args:
            min_samples (int): Número mínimo de amostras para treinar
            
        Returns:
            bool: True se o modelo foi treinado com sucesso
        """
        # Em um ambiente real, aqui você carregaria dados históricos de:
        # 1. Indicadores econômicos passados
        # 2. Sentimento social histórico
        # 3. Eventos regulatórios passados
        # 4. Desempenho de mercado resultante
        
        # Para exemplo, simulamos um conjunto de dados de treinamento
        try:
            # Criar dataframe de treinamento simulado
            n_samples = max(min_samples, 100)  # Pelo menos 100 amostras
            
            # Features simuladas
            np.random.seed(42)  # Para reprodutibilidade
            
            # Cria dados históricos simulados
            data = {
                'interest_rate': np.random.uniform(0, 7, n_samples),
                'inflation_rate': np.random.uniform(1, 8, n_samples),
                'vix_index': np.random.uniform(10, 30, n_samples),
                'gdp_growth': np.random.uniform(-2, 5, n_samples),
                'social_sentiment': np.random.uniform(-1, 1, n_samples),
                'news_sentiment': np.random.uniform(-1, 1, n_samples),
                'regulatory_score': np.random.uniform(-1, 1, n_samples),
            }
            
            # Target: influência no mercado de criptomoedas (simulada como uma função das features)
            # Com algum ruído aleatório
            market_impact = (
                -0.4 * data['interest_rate'] / 7 + 
                0.2 * data['inflation_rate'] / 8 +
                -0.3 * data['vix_index'] / 30 +
                0.3 * data['gdp_growth'] / 5 +
                0.3 * data['social_sentiment'] +
                0.2 * data['news_sentiment'] +
                0.15 * data['regulatory_score'] +
                np.random.normal(0, 0.2, n_samples)  # Ruído
            )
            
            # Limitar ao intervalo -1 a 1
            market_impact = np.clip(market_impact, -1, 1)
            
            # Criar dataframe
            data['market_impact'] = market_impact
            df = pd.DataFrame(data)
            
            # Dividir features e target
            X = df.drop('market_impact', axis=1)
            y = df['market_impact']
            
            # Normalizar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Treinar modelo
            self.model.fit(X_scaled, y)
            
            # Marcar como treinado
            self.model_ready = True
            
            # Salvar modelo
            self.save_model()
            
            logger.info("Modelo de análise contextual treinado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo: {str(e)}")
            self.model_ready = False
            return False
    
