#!/usr/bin/env python3
"""
Trading Bot Training System
Utiliza dados do MarketDataAggregator para treinar modelos de decisão.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import sqlite3
from dataclasses import dataclass, asdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import talib
import joblib
import os

from src.api.external.market_data_aggregator import MarketDataAggregator
from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TrainingFeature:
    """Estrutura para features de treinamento."""
    symbol: str
    timestamp: str
    # Preços e volumes
    price: float
    volume_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    high_24h: float
    low_24h: float
    
    # Indicadores técnicos
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    sma_20: float
    ema_12: float
    ema_26: float
    
    # Sentimento e notícias
    news_sentiment_score: float
    news_count: int
    overall_sentiment: str
    
    # Eventos
    upcoming_events_count: int
    high_importance_events: int
    
    # Target (para treinamento supervisionado)
    target: Optional[str] = None  # 'BUY', 'SELL', 'HOLD'
    future_return: Optional[float] = None  # Retorno futuro para validação


@dataclass
class TradingSignal:
    """Estrutura para sinais de trading."""
    symbol: str
    timestamp: str
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    price: float
    reasoning: str
    features_used: Dict[str, Any]


class TradingDataProcessor:
    """Processador de dados para treinamento."""
    
    def __init__(self, db_path: str = "data/trading_data.db"):
        """
        Inicializa o processador de dados.
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        self.db_path = db_path
        self.ensure_database_exists()
        
    def ensure_database_exists(self):
        """Garante que o banco de dados e tabelas existam."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para dados históricos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp TEXT,
                price REAL,
                volume_24h REAL,
                high_24h REAL,
                low_24h REAL,
                price_change_24h REAL,
                price_change_percentage_24h REAL,
                market_cap REAL,
                source TEXT,
                created_at TEXT
            )
        ''')
        
        # Tabela para features de treinamento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp TEXT,
                features TEXT,  -- JSON com todas as features
                target TEXT,
                future_return REAL,
                created_at TEXT
            )
        ''')
        
        # Tabela para sinais de trading
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp TEXT,
                signal TEXT,
                confidence REAL,
                price REAL,
                reasoning TEXT,
                features_used TEXT,  -- JSON
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_market_data(self, market_data: List[Dict[str, Any]]):
        """Salva dados de mercado no banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for data in market_data:
            cursor.execute('''
                INSERT INTO historical_data 
                (symbol, timestamp, price, volume_24h, high_24h, low_24h, 
                 price_change_24h, price_change_percentage_24h, market_cap, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'],
                data['timestamp'],
                data['price'],
                data['volume_24h'],
                data.get('high_24h'),
                data.get('low_24h'),
                data['price_change_24h'],
                data['price_change_percentage_24h'],
                data.get('market_cap'),
                data['source'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Salvou {len(market_data)} registros de dados de mercado")
    
    def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Recupera dados históricos do banco."""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM historical_data 
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        '''
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        df = pd.read_sql_query(query, conn, params=(symbol, cutoff_date))
        conn.close()
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos."""
        if len(df) < 26:  # Precisa de pelo menos 26 pontos para EMA
            logger.warning(f"Não há dados suficientes para calcular indicadores técnicos")
            return df
        
        # Converter preços para numpy array
        prices = df['price'].values
        high_prices = df['high_24h'].fillna(df['price']).values
        low_prices = df['low_24h'].fillna(df['price']).values
        volumes = df['volume_24h'].values
        
        # RSI
        df['rsi'] = talib.RSI(prices, timeperiod=14)
        
        # MACD
        macd, macd_signal, _ = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2)
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # Moving Averages
        df['sma_20'] = talib.SMA(prices, timeperiod=20)
        df['ema_12'] = talib.EMA(prices, timeperiod=12)
        df['ema_26'] = talib.EMA(prices, timeperiod=26)
        
        return df


class TradingModel:
    """Modelo de machine learning para decisões de trading."""
    
    def __init__(self, model_path: str = "models/trading_model.pkl"):
        """
        Inicializa o modelo de trading.
        
        Args:
            model_path: Caminho para salvar/carregar o modelo
        """
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.is_trained = False
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    def create_features_from_data(self, market_data: Dict[str, Any]) -> List[TrainingFeature]:
        """Cria features a partir dos dados do agregador."""
        features = []
        
        # Processar dados de mercado
        for data in market_data.get('market_data', []):
            # Calcular sentiment score das notícias
            news_sentiment_score = 0.0
            news_count = 0
            
            if 'news' in market_data:
                symbol_news = [
                    n for n in market_data['news'] 
                    if data['symbol'].split('/')[0] in n.get('currencies', [])
                ]
                if symbol_news:
                    news_sentiment_score = sum(n['sentiment_score'] for n in symbol_news) / len(symbol_news)
                    news_count = len(symbol_news)
            
            # Determinar sentimento geral
            overall_sentiment = "neutral"
            if news_sentiment_score > 0.2:
                overall_sentiment = "positive"
            elif news_sentiment_score < -0.2:
                overall_sentiment = "negative"
            
            # Contar eventos
            upcoming_events_count = 0
            high_importance_events = 0
            
            if 'events' in market_data:
                symbol_events = [
                    e for e in market_data['events']
                    if data['symbol'].split('/')[0] in e.get('currencies', [])
                ]
                upcoming_events_count = len(symbol_events)
                high_importance_events = len([e for e in symbol_events if e['importance'] == 'high'])
            
            # Criar feature (com indicadores técnicos vazios por enquanto)
            feature = TrainingFeature(
                symbol=data['symbol'],
                timestamp=data['timestamp'],
                price=data['price'],
                volume_24h=data['volume_24h'],
                price_change_24h=data['price_change_24h'],
                price_change_percentage_24h=data['price_change_percentage_24h'],
                high_24h=data.get('high_24h', data['price']),
                low_24h=data.get('low_24h', data['price']),
                rsi=50.0,  # Valores padrão - serão calculados com dados históricos
                macd=0.0,
                macd_signal=0.0,
                bb_upper=data['price'] * 1.02,
                bb_middle=data['price'],
                bb_lower=data['price'] * 0.98,
                sma_20=data['price'],
                ema_12=data['price'],
                ema_26=data['price'],
                news_sentiment_score=news_sentiment_score,
                news_count=news_count,
                overall_sentiment=overall_sentiment,
                upcoming_events_count=upcoming_events_count,
                high_importance_events=high_importance_events
            )
            
            features.append(feature)
        
        return features
    
    def create_training_targets(self, features: List[TrainingFeature]) -> List[TrainingFeature]:
        """Cria targets de treinamento baseado em regras simples."""
        
        for feature in features:
            # Regras básicas para criar targets
            signal = "HOLD"
            
            # Regra 1: RSI
            if feature.rsi < 30:  # Oversold
                signal = "BUY"
            elif feature.rsi > 70:  # Overbought
                signal = "SELL"
            
            # Regra 2: MACD
            if feature.macd > feature.macd_signal and feature.price_change_percentage_24h > 0:
                signal = "BUY"
            elif feature.macd < feature.macd_signal and feature.price_change_percentage_24h < 0:
                signal = "SELL"
            
            # Regra 3: Bollinger Bands
            if feature.price < feature.bb_lower:
                signal = "BUY"
            elif feature.price > feature.bb_upper:
                signal = "SELL"
            
            # Regra 4: Sentimento
            if feature.overall_sentiment == "positive" and feature.news_sentiment_score > 0.3:
                if signal == "HOLD":
                    signal = "BUY"
            elif feature.overall_sentiment == "negative" and feature.news_sentiment_score < -0.3:
                if signal == "HOLD":
                    signal = "SELL"
            
            # Regra 5: Eventos importantes
            if feature.high_importance_events > 0:
                if signal == "HOLD":
                    signal = "BUY"  # Assumir que eventos importantes são positivos
            
            feature.target = signal
        
        return features
    
    def prepare_training_data(self, features: List[TrainingFeature]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara dados para treinamento."""
        # Definir colunas de features
        feature_columns = [
            'price', 'volume_24h', 'price_change_24h', 'price_change_percentage_24h',
            'high_24h', 'low_24h', 'rsi', 'macd', 'macd_signal', 'bb_upper', 
            'bb_middle', 'bb_lower', 'sma_20', 'ema_12', 'ema_26',
            'news_sentiment_score', 'news_count', 'upcoming_events_count', 
            'high_importance_events'
        ]
        
        # Converter sentiment para numérico
        sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
        
        # Criar matriz de features
        X = []
        y = []
        
        for feature in features:
            if feature.target is None:
                continue
                
            row = []
            for col in feature_columns:
                if col == 'overall_sentiment':
                    row.append(sentiment_map[feature.overall_sentiment])
                else:
                    row.append(getattr(feature, col))
            
            X.append(row)
            y.append(feature.target)
        
        self.feature_columns = feature_columns + ['overall_sentiment_numeric']
        
        # Adicionar coluna de sentimento numérico
        for i, feature in enumerate(features):
            if feature.target is not None:
                X[i].append(sentiment_map[feature.overall_sentiment])
        
        return np.array(X), np.array(y)
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Treina o modelo de machine learning."""
        try:
            # Dividir dados em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Normalizar features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Treinar modelo
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Avaliar modelo
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Salvar modelo
            self.save_model()
            self.is_trained = True
            
            # Gerar relatório
            report = classification_report(y_test, y_pred, output_dict=True)
            
            training_report = {
                'accuracy': accuracy,
                'classification_report': report,
                'feature_importance': dict(zip(self.feature_columns, self.model.feature_importances_)),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Modelo treinado com acurácia: {accuracy:.3f}")
            return training_report
            
        except Exception as e:
            logger.error(f"Erro no treinamento: {e}")
            raise
    
    def predict_signal(self, features: List[TrainingFeature]) -> List[TradingSignal]:
        """Faz previsões com o modelo treinado."""
        if not self.is_trained:
            self.load_model()
        
        if not self.is_trained:
            logger.warning("Modelo não treinado, usando regras básicas")
            return self._predict_with_rules(features)
        
        signals = []
        
        try:
            # Preparar dados para previsão
            X, _ = self.prepare_training_data(features)
            
            if len(X) == 0:
                return signals
            
            # Normalizar
            X_scaled = self.scaler.transform(X)
            
            # Fazer previsões
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            
            # Criar sinais
            for i, feature in enumerate(features):
                if i < len(predictions):
                    signal = TradingSignal(
                        symbol=feature.symbol,
                        timestamp=feature.timestamp,
                        signal=predictions[i],
                        confidence=max(probabilities[i]),
                        price=feature.price,
                        reasoning=f"ML Model prediction with {max(probabilities[i]):.2f} confidence",
                        features_used={
                            'rsi': feature.rsi,
                            'macd': feature.macd,
                            'sentiment_score': feature.news_sentiment_score,
                            'price_change_24h': feature.price_change_percentage_24h
                        }
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Erro na previsão: {e}")
            return self._predict_with_rules(features)
    
    def _predict_with_rules(self, features: List[TrainingFeature]) -> List[TradingSignal]:
        """Fallback: previsão com regras básicas."""
        signals = []
        
        for feature in features:
            signal = "HOLD"
            confidence = 0.5
            reasoning = "Rule-based prediction: "
            
            # Aplicar regras básicas
            if feature.price_change_percentage_24h > 5 and feature.news_sentiment_score > 0.2:
                signal = "BUY"
                confidence = 0.7
                reasoning += "Strong positive momentum with good sentiment"
            elif feature.price_change_percentage_24h < -5 and feature.news_sentiment_score < -0.2:
                signal = "SELL"
                confidence = 0.7
                reasoning += "Strong negative momentum with bad sentiment"
            elif feature.high_importance_events > 0:
                signal = "BUY"
                confidence = 0.6
                reasoning += "Important upcoming events"
            else:
                reasoning += "No clear signal"
            
            trading_signal = TradingSignal(
                symbol=feature.symbol,
                timestamp=feature.timestamp,
                signal=signal,
                confidence=confidence,
                price=feature.price,
                reasoning=reasoning,
                features_used={
                    'price_change_24h': feature.price_change_percentage_24h,
                    'sentiment_score': feature.news_sentiment_score,
                    'events': feature.high_importance_events
                }
            )
            
            signals.append(trading_signal)
        
        return signals
    
    def save_model(self):
        """Salva o modelo treinado."""
        if self.model and self.scaler:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'timestamp': datetime.now().isoformat()
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"Modelo salvo em: {self.model_path}")
    
    def load_model(self):
        """Carrega o modelo treinado."""
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = True
                logger.info(f"Modelo carregado de: {self.model_path}")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}")


class TradingTrainer:
    """Classe principal para treinamento do robô de trading."""
    
    def __init__(self):
        """Inicializa o sistema de treinamento."""
        self.data_processor = TradingDataProcessor()
        self.model = TradingModel()
        self.aggregator = None
    
    async def collect_and_store_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Coleta dados das APIs e armazena no banco."""
        logger.info(f"Coletando dados para: {symbols}")
        
        async with MarketDataAggregator() as aggregator:
            # Coletar dados abrangentes
            market_analysis = await aggregator.get_comprehensive_market_analysis(
                symbols=symbols,
                include_news=True,
                include_events=True,
                include_sentiment=True
            )
            
            # Armazenar dados históricos
            if 'market_data' in market_analysis:
                self.data_processor.save_market_data(market_analysis['market_data'])
            
            return market_analysis
    
    async def train_model_with_latest_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Treina o modelo com os dados mais recentes."""
        logger.info("Iniciando treinamento do modelo")
        
        # Coletar dados atuais
        market_data = await self.collect_and_store_data(symbols)
        
        # Criar features
        features = self.model.create_features_from_data(market_data)
        
        # Criar targets (labels) baseado em regras
        features_with_targets = self.model.create_training_targets(features)
        
        # Preparar dados para treinamento
        X, y = self.model.prepare_training_data(features_with_targets)
        
        if len(X) == 0:
            logger.warning("Não há dados suficientes para treinamento")
            return {"error": "Insufficient data for training"}
        
        # Treinar modelo
        training_report = self.model.train_model(X, y)
        
        return {
            "training_report": training_report,
            "features_created": len(features),
            "symbols_analyzed": symbols,
            "market_data_summary": market_data.get('summary', {})
        }
    
    async def generate_trading_signals(self, symbols: List[str]) -> List[TradingSignal]:
        """Gera sinais de trading para os símbolos especificados."""
        logger.info(f"Gerando sinais para: {symbols}")
        
        # Coletar dados atuais
        market_data = await self.collect_and_store_data(symbols)
        
        # Criar features
        features = self.model.create_features_from_data(market_data)
        
        # Gerar sinais
        signals = self.model.predict_signal(features)
        
        return signals
    
    async def run_continuous_training(self, symbols: List[str], interval_hours: int = 24):
        """Executa treinamento contínuo."""
        logger.info(f"Iniciando treinamento contínuo a cada {interval_hours} horas")
        
        while True:
            try:
                # Treinar modelo
                result = await self.train_model_with_latest_data(symbols)
                logger.info(f"Treinamento concluído: {result.get('training_report', {}).get('accuracy', 'N/A')}")
                
                # Gerar sinais atuais
                signals = await self.generate_trading_signals(symbols)
                
                # Log dos sinais
                for signal in signals:
                    logger.info(f"Sinal: {signal.symbol} -> {signal.signal} (confiança: {signal.confidence:.2f})")
                
                # Aguardar próximo ciclo
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Erro no treinamento contínuo: {e}")
                await asyncio.sleep(3600)  # Aguardar 1 hora antes de tentar novamente


# Exemplo de uso
async def main():
    """Exemplo de uso do sistema de treinamento."""
    print("=== Sistema de Treinamento do Robô de Trading ===\n")
    
    # Símbolos para análise
    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
    
    # Inicializar trainer
    trainer = TradingTrainer()
    
    print("1. Coletando dados e treinando modelo...")
    training_result = await trainer.train_model_with_latest_data(symbols)
    
    print(f"Treinamento concluído!")
    print(f"Acurácia: {training_result.get('training_report', {}).get('accuracy', 'N/A')}")
    print(f"Features criadas: {training_result.get('features_created', 0)}")
    
    print("\n2. Gerando sinais de trading...")
    signals = await trainer.generate_trading_signals(symbols)
    
    print(f"\nSinais gerados:")
    for signal in signals:
        print(f"  {signal.symbol}: {signal.signal} (confiança: {signal.confidence:.2f})")
        print(f"    Preço: ${signal.price:.2f}")
        print(f"    Razão: {signal.reasoning}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
