"""
Sistema de Treinamento de Trading com Integração PostgreSQL

Este módulo implementa um sistema de treinamento de machine learning
que utiliza PostgreSQL como banco de dados principal, integrando
completamente com o PostgresManager existente.
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib
import ta

from database.postgres_manager import PostgresManager


@dataclass
class TrainingFeatures:
    """Estrutura para armazenar features de treinamento"""
    symbol: str
    timestamp: datetime
    
    # Features técnicas
    price: float
    volume: float
    price_change_1h: float
    price_change_4h: float
    price_change_24h: float
    volume_change_24h: float
    volatility_24h: float
    
    # Indicadores técnicos
    sma_10: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    rsi_14: float
    macd: float
    macd_signal: float
    macd_hist: float
    bb_upper: float
    bb_lower: float
    bb_middle: float
    stoch_k: float
    stoch_d: float
    cci: float
    williams_r: float
    atr: float
    volume_sma: float
    
    # Features de sentimento
    news_sentiment: float
    social_sentiment: float
    fear_greed_index: float
    
    # Features de eventos
    upcoming_events: int
    event_impact: float


@dataclass
class TrainingSignal:
    """Estrutura para armazenar sinais de treinamento"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: Optional[str] = None


class PostgresTradingDataProcessor:
    """Processador de dados de trading usando PostgreSQL"""
    
    def __init__(self, postgres_manager: PostgresManager):
        self.postgres_manager = postgres_manager
        self.logger = logging.getLogger(__name__)
        
    async def save_training_features(self, features: TrainingFeatures) -> bool:
        """Salva features de treinamento no PostgreSQL"""
        try:
            features_dict = asdict(features)
            
            # Criar tabela de features se não existir
            self._create_features_table()
            
            # Inserir features
            query = """
            INSERT INTO training_features (
                symbol, timestamp, price, volume, price_change_1h, price_change_4h,
                price_change_24h, volume_change_24h, volatility_24h, sma_10, sma_20,
                sma_50, ema_12, ema_26, rsi_14, macd, macd_signal, macd_hist,
                bb_upper, bb_lower, bb_middle, stoch_k, stoch_d, cci, williams_r,
                atr, volume_sma, news_sentiment, social_sentiment, fear_greed_index,
                upcoming_events, event_impact
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """
            
            self.postgres_manager.execute_query(query, tuple(features_dict.values()))
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar features: {e}")
            return False
    
    async def save_training_signal(self, signal: TrainingSignal) -> bool:
        """Salva sinal de treinamento no PostgreSQL"""
        try:
            # Criar tabela de sinais se não existir
            self._create_signals_table()
            
            query = """
            INSERT INTO training_signals (
                symbol, timestamp, signal_type, confidence, price_target,
                stop_loss, take_profit, reasoning
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.postgres_manager.execute_query(query, (
                signal.symbol, signal.timestamp, signal.signal_type,
                signal.confidence, signal.price_target, signal.stop_loss,
                signal.take_profit, signal.reasoning
            ))
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar sinal: {e}")
            return False
    
    async def get_training_data(self, symbol: str, days: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Recupera dados de treinamento do PostgreSQL"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Buscar features
            features_query = """
            SELECT * FROM training_features 
            WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
            ORDER BY timestamp ASC
            """
            
            features_data = self.postgres_manager.fetch_all(
                features_query, (symbol, start_date, end_date)
            )
            
            # Buscar sinais
            signals_query = """
            SELECT * FROM training_signals 
            WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
            ORDER BY timestamp ASC
            """
            
            signals_data = self.postgres_manager.fetch_all(
                signals_query, (symbol, start_date, end_date)
            )
            
            # Converter para DataFrames
            if features_data:
                features_df = pd.DataFrame([dict(row) for row in features_data])
            else:
                features_df = pd.DataFrame()
            
            if signals_data:
                signals_df = pd.DataFrame([dict(row) for row in signals_data])
            else:
                signals_df = pd.DataFrame()
            
            return features_df, signals_df
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dados de treinamento: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    async def get_market_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Recupera dados de mercado do PostgreSQL"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT * FROM market_data 
            WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
            ORDER BY timestamp ASC
            """
            
            data = self.postgres_manager.fetch_all(
                query, (symbol, start_date, end_date)
            )
            
            if data:
                return pd.DataFrame([dict(row) for row in data])
            else:
                return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dados de mercado: {e}")
            return pd.DataFrame()
    
    async def save_training_log(self, model_type: str, metrics: Dict[str, float], 
                               symbol: str, timestamp: datetime) -> bool:
        """Salva log de treinamento"""
        try:
            log_data = {
                'model_type': model_type,
                'metrics': metrics,
                'symbol': symbol,
                'timestamp': timestamp.isoformat()
            }
            
            return await self.postgres_manager.save_log(
                'training',
                f"Treinamento concluído para {symbol} com {model_type}",
                json.dumps(log_data)
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de treinamento: {e}")
            return False
    
    def _create_features_table(self):
        """Cria tabela de features de treinamento"""
        query = """
        CREATE TABLE IF NOT EXISTS training_features (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            price DECIMAL(20,8) NOT NULL,
            volume DECIMAL(20,8) NOT NULL,
            price_change_1h DECIMAL(10,4),
            price_change_4h DECIMAL(10,4),
            price_change_24h DECIMAL(10,4),
            volume_change_24h DECIMAL(10,4),
            volatility_24h DECIMAL(10,4),
            sma_10 DECIMAL(20,8),
            sma_20 DECIMAL(20,8),
            sma_50 DECIMAL(20,8),
            ema_12 DECIMAL(20,8),
            ema_26 DECIMAL(20,8),
            rsi_14 DECIMAL(10,4),
            macd DECIMAL(20,8),
            macd_signal DECIMAL(20,8),
            macd_hist DECIMAL(20,8),
            bb_upper DECIMAL(20,8),
            bb_lower DECIMAL(20,8),
            bb_middle DECIMAL(20,8),
            stoch_k DECIMAL(10,4),
            stoch_d DECIMAL(10,4),
            cci DECIMAL(10,4),
            williams_r DECIMAL(10,4),
            atr DECIMAL(20,8),
            volume_sma DECIMAL(20,8),
            news_sentiment DECIMAL(5,4),
            social_sentiment DECIMAL(5,4),
            fear_greed_index DECIMAL(5,4),
            upcoming_events INTEGER,
            event_impact DECIMAL(5,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.postgres_manager.execute_query(query)
        
        # Índices para performance
        self.postgres_manager.execute_query(
            "CREATE INDEX IF NOT EXISTS idx_features_symbol_timestamp ON training_features(symbol, timestamp)"
        )
    
    def _create_signals_table(self):
        """Cria tabela de sinais de treinamento"""
        query = """
        CREATE TABLE IF NOT EXISTS training_signals (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            signal_type VARCHAR(10) NOT NULL,
            confidence DECIMAL(5,4) NOT NULL,
            price_target DECIMAL(20,8),
            stop_loss DECIMAL(20,8),
            take_profit DECIMAL(20,8),
            reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.postgres_manager.execute_query(query)
        
        # Índices para performance
        self.postgres_manager.execute_query(
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON training_signals(symbol, timestamp)"
        )
    
    def get_features_count(self) -> int:
        """Retorna contagem de features de treinamento"""
        try:
            result = self.postgres_manager.fetch_one("SELECT COUNT(*) FROM training_features")
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Erro ao contar features: {e}")
            return 0
    
    def get_signals_count(self) -> int:
        """Retorna contagem de sinais de treinamento"""
        try:
            result = self.postgres_manager.fetch_one("SELECT COUNT(*) FROM training_signals")
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Erro ao contar sinais: {e}")
            return 0
    
    def get_last_training_log(self) -> str:
        """Retorna o último log de treinamento"""
        try:
            result = self.postgres_manager.fetch_one(
                "SELECT message FROM trading_logs WHERE log_type = 'training' ORDER BY timestamp DESC LIMIT 1"
            )
            return result[0] if result else "Nenhum log de treinamento encontrado"
        except Exception as e:
            self.logger.error(f"Erro ao buscar último log: {e}")
            return "Erro ao buscar logs"


class PostgresMLModel:
    """Modelo de Machine Learning integrado com PostgreSQL"""
    
    def __init__(self, model_type: str = "random_forest", **kwargs):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.logger = logging.getLogger(__name__)
        
        # Configurar modelo baseado no tipo
        if model_type == "random_forest":
            self.model = RandomForestClassifier(**kwargs)
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(**kwargs)
        else:
            raise ValueError(f"Tipo de modelo não suportado: {model_type}")
    
    def prepare_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """Prepara features para treinamento"""
        if features_df.empty:
            return np.array([])
        
        # Remover colunas não-numéricas
        numeric_columns = features_df.select_dtypes(include=[np.number]).columns
        feature_columns = [col for col in numeric_columns if col not in ['id', 'timestamp']]
        
        self.feature_columns = feature_columns
        features_array = features_df[feature_columns].fillna(0).values
        
        return features_array
    
    def prepare_targets(self, signals_df: pd.DataFrame) -> np.ndarray:
        """Prepara targets para treinamento"""
        if signals_df.empty:
            return np.array([])
        
        # Debug: verificar colunas do DataFrame
        self.logger.info(f"Colunas do signals_df: {list(signals_df.columns)}")
        self.logger.info(f"Primeiras linhas: {signals_df.head()}")
        
        # Verificar se a coluna signal_type existe
        if 'signal_type' not in signals_df.columns:
            self.logger.error(f"Coluna 'signal_type' não encontrada. Colunas disponíveis: {list(signals_df.columns)}")
            return np.array([])
        
        # Mapear sinais para valores numéricos
        signal_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0}
        targets = signals_df['signal_type'].map(signal_map).fillna(0).values
        
        return targets
    
    async def train(self, features_df: pd.DataFrame, signals_df: pd.DataFrame) -> Dict[str, float]:
        """Treina o modelo"""
        try:
            # Preparar dados
            X = self.prepare_features(features_df)
            y = self.prepare_targets(signals_df)
            
            if len(X) == 0 or len(y) == 0:
                raise ValueError("Dados insuficientes para treinamento")
            
            # Normalizar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Dividir dados
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Treinar modelo
            self.model.fit(X_train, y_train)
            
            # Avaliar modelo
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)
            
            # Calcular métricas
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
            }
            
            # ROC AUC para classificação binária/multi-classe
            if len(np.unique(y)) > 2:
                metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            elif len(np.unique(y)) == 2:
                metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba[:, 1])
            
            # Validação cruzada (ajustar cv baseado no tamanho do dataset)
            n_samples = len(X_scaled)
            cv_folds = min(5, max(2, n_samples // 2))  # Mínimo 2, máximo 5
            
            if n_samples >= 4:  # Só fazer CV se tiver pelo menos 4 amostras
                cv_scores = cross_val_score(self.model, X_scaled, y, cv=cv_folds)
                metrics['cv_mean'] = cv_scores.mean()
                metrics['cv_std'] = cv_scores.std()
            else:
                self.logger.warning(f"Dataset muito pequeno ({n_samples} amostras) para validação cruzada")
                metrics['cv_mean'] = 0.0
                metrics['cv_std'] = 0.0
            
            self.logger.info(f"Treinamento concluído com sucesso: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro durante treinamento: {e}")
            raise
    
    async def predict(self, features_df: pd.DataFrame) -> List[TrainingSignal]:
        """Gera previsões"""
        try:
            if self.model is None:
                raise ValueError("Modelo não foi treinado")
            
            X = self.prepare_features(features_df)
            if len(X) == 0:
                return []
            
            X_scaled = self.scaler.transform(X)
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            
            # Mapear previsões para sinais
            signal_map = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}
            signals = []
            
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                signal_type = signal_map[pred]
                confidence = prob.max()
                
                # Criar sinal apenas se confiança for suficiente
                if confidence > 0.6:
                    signal = TrainingSignal(
                        symbol=features_df.iloc[i]['symbol'],
                        timestamp=features_df.iloc[i]['timestamp'],
                        signal_type=signal_type,
                        confidence=float(confidence),  # Converter numpy para float nativo
                        reasoning=f"ML prediction with {confidence:.2f} confidence"
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro durante previsão: {e}")
            return []
    
    async def save_model(self, path: str) -> bool:
        """Salva modelo treinado"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'model_type': self.model_type
            }
            
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model_data, path)
            
            self.logger.info(f"Modelo salvo em: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo: {e}")
            return False
    
    async def load_model(self, path: str) -> bool:
        """Carrega modelo treinado"""
        try:
            if not Path(path).exists():
                raise FileNotFoundError(f"Modelo não encontrado: {path}")
            
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_type = model_data['model_type']
            
            self.logger.info(f"Modelo carregado de: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo: {e}")
            return False


class PostgresTradingTrainer:
    """Coordenador de treinamento integrado com PostgreSQL"""
    
    def __init__(self, config_path: str = "config/training_config.yaml"):
        self.config = self._load_config(config_path)
        self.postgres_manager = None
        self.data_processor = None
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuração do arquivo YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return {}
    
    async def initialize(self):
        """Inicializa componentes do sistema"""
        try:
            # Inicializar PostgreSQL - usar variáveis de ambiente do .env
            self.postgres_manager = PostgresManager()
            
            self.postgres_manager.connect()
            
            # Inicializar processador de dados
            self.data_processor = PostgresTradingDataProcessor(self.postgres_manager)
            
            # Inicializar modelo
            model_config = self.config.get('model', {})
            model_type = model_config.get('type', 'random_forest')
            model_params = model_config.get(model_type, {})
            
            self.model = PostgresMLModel(model_type, **model_params)
            
            self.logger.info("Sistema inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")
            raise
    
    async def collect_and_process_data(self, symbols: List[str], days: int = 30):
        """Coleta e processa dados de mercado"""
        try:
            for symbol in symbols:
                self.logger.info(f"Processando dados para {symbol}")
                
                # Coletar dados de mercado
                market_data = await self.data_processor.get_market_data(symbol, days)
                
                if market_data.empty:
                    self.logger.warning(f"Nenhum dado encontrado para {symbol}")
                    continue
                
                # Calcular indicadores técnicos
                features_list = await self._calculate_features(market_data, symbol)
                
                # Salvar features
                for features in features_list:
                    await self.data_processor.save_training_features(features)
                
                # Gerar sinais baseados em estratégias
                signals = await self._generate_training_signals(features_list, symbol)
                
                # Salvar sinais
                for signal in signals:
                    await self.data_processor.save_training_signal(signal)
                
                self.logger.info(f"Dados processados para {symbol}: {len(features_list)} features, {len(signals)} sinais")
                
        except Exception as e:
            self.logger.error(f"Erro no processamento de dados: {e}")
            raise
    
    async def train_model(self, symbols: List[str], days: int = 30) -> Dict[str, float]:
        """Treina o modelo com dados consolidados"""
        try:
            all_features = []
            all_signals = []
            
            # Coletar dados de todos os símbolos
            for symbol in symbols:
                features_df, signals_df = await self.data_processor.get_training_data(symbol, days)
                
                if not features_df.empty and not signals_df.empty:
                    all_features.append(features_df)
                    all_signals.append(signals_df)
            
            if not all_features:
                raise ValueError("Nenhum dado de treinamento disponível")
            
            # Consolidar dados
            combined_features = pd.concat(all_features, ignore_index=True)
            combined_signals = pd.concat(all_signals, ignore_index=True)
            
            # Treinar modelo
            metrics = await self.model.train(combined_features, combined_signals)
            
            # Salvar modelo
            model_path = self.config.get('model', {}).get('model_path', 'models/trading_model.pkl')
            await self.model.save_model(model_path)
            
            # Salvar log de treinamento
            await self.data_processor.save_training_log(
                self.model.model_type, metrics, ','.join(symbols), datetime.now()
            )
            
            self.logger.info(f"Modelo treinado com sucesso: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro no treinamento: {e}")
            raise
    
    async def generate_signals(self, symbols: List[str]) -> List[TrainingSignal]:
        """Gera sinais de trading usando modelo treinado"""
        try:
            all_signals = []
            
            for symbol in symbols:
                # Obter features recentes
                features_df, _ = await self.data_processor.get_training_data(symbol, 1)
                
                if not features_df.empty:
                    # Gerar previsões
                    signals = await self.model.predict(features_df)
                    all_signals.extend(signals)
                    
                    # Salvar sinais gerados
                    for signal in signals:
                        await self.data_processor.save_training_signal(signal)
            
            return all_signals
            
        except Exception as e:
            self.logger.error(f"Erro na geração de sinais: {e}")
            return []
    
    async def _calculate_features(self, market_data: pd.DataFrame, symbol: str) -> List[TrainingFeatures]:
        """Calcula features técnicas dos dados de mercado"""
        # Implementar cálculo de indicadores técnicos usando biblioteca ta
        # Esta é uma implementação simplificada
        features_list = []
        
        # Adicionar indicadores técnicos
        market_data['sma_10'] = ta.trend.sma_indicator(market_data['close'], window=10)
        market_data['sma_20'] = ta.trend.sma_indicator(market_data['close'], window=20)
        market_data['sma_50'] = ta.trend.sma_indicator(market_data['close'], window=50)
        market_data['rsi_14'] = ta.momentum.rsi(market_data['close'], window=14)
        
        # Converter para lista de features
        for _, row in market_data.iterrows():
            features = TrainingFeatures(
                symbol=symbol,
                timestamp=row.get('timestamp', datetime.now()),
                price=row.get('close', 0),
                volume=row.get('volume', 0),
                price_change_1h=0,  # Calcular baseado em dados históricos
                price_change_4h=0,
                price_change_24h=0,
                volume_change_24h=0,
                volatility_24h=0,
                sma_10=row.get('sma_10', 0),
                sma_20=row.get('sma_20', 0),
                sma_50=row.get('sma_50', 0),
                ema_12=0,  # Implementar cálculos completos
                ema_26=0,
                rsi_14=row.get('rsi_14', 0),
                macd=0,
                macd_signal=0,
                macd_hist=0,
                bb_upper=0,
                bb_lower=0,
                bb_middle=0,
                stoch_k=0,
                stoch_d=0,
                cci=0,
                williams_r=0,
                atr=0,
                volume_sma=0,
                news_sentiment=0,
                social_sentiment=0,
                fear_greed_index=0,
                upcoming_events=0,
                event_impact=0
            )
            features_list.append(features)
        
        return features_list
    
    async def _generate_training_signals(self, features_list: List[TrainingFeatures], symbol: str) -> List[TrainingSignal]:
        """Gera sinais de treinamento baseados em estratégias"""
        signals = []
        
        for i, features in enumerate(features_list):
            # Estratégia simples baseada em RSI e SMA
            signal_type = 'HOLD'
            confidence = 0.5
            
            if features.rsi_14 < 30 and features.price > features.sma_20:
                signal_type = 'BUY'
                confidence = 0.75
            elif features.rsi_14 > 70 and features.price < features.sma_20:
                signal_type = 'SELL'
                confidence = 0.75
            
            signal = TrainingSignal(
                symbol=symbol,
                timestamp=features.timestamp,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=f"RSI: {features.rsi_14:.2f}, SMA20: {features.sma_20:.2f}"
            )
            signals.append(signal)
        
        return signals
    
    async def run_training_pipeline(self):
        """Executa pipeline completo de treinamento"""
        try:
            await self.initialize()
            
            symbols = self.config.get('data', {}).get('default_symbols', ['BTC/USDT'])
            days = self.config.get('data', {}).get('historical_days', 30)
            
            # Coletar e processar dados
            await self.collect_and_process_data(symbols, days)
            
            # Treinar modelo
            metrics = await self.train_model(symbols, days)
            
            # Gerar sinais
            signals = await self.generate_signals(symbols)
            
            self.logger.info(f"Pipeline concluído: {len(signals)} sinais gerados")
            return metrics, signals
            
        except Exception as e:
            self.logger.error(f"Erro no pipeline: {e}")
            raise
        finally:
            if self.postgres_manager:
                await self.postgres_manager.disconnect()


# Exemplo de uso
async def main():
    """Exemplo de uso do sistema de treinamento"""
    try:
        trainer = PostgresTradingTrainer()
        metrics, signals = await trainer.run_training_pipeline()
        
        print(f"Métricas do modelo: {metrics}")
        print(f"Sinais gerados: {len(signals)}")
        
        for signal in signals[:5]:  # Mostrar primeiros 5 sinais
            print(f"{signal.symbol}: {signal.signal_type} (confiança: {signal.confidence:.2f})")
            
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(main())
