#!/usr/bin/env python3
"""
Módulo de indicadores técnicos avançados para análise de mercado
"""
import numpy as np
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger("robot-crypt")

class TechnicalIndicators:
    """
    Classe para cálculo de indicadores técnicos avançados para análise de mercado
    """
    
    @staticmethod
    def prepare_data(klines):
        """
        Prepara os dados de velas da Binance para cálculo de indicadores
        
        Args:
            klines (list): Lista de velas no formato da API da Binance
            
        Returns:
            pandas.DataFrame: DataFrame com dados OHLCV
        """
        try:
            # Extrair dados das velas
            data = []
            for k in klines:
                # Formato padrão da API da Binance:
                # [open_time, open, high, low, close, volume, ...]
                data.append({
                    'timestamp': datetime.fromtimestamp(int(k[0]) / 1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            
            # Criar DataFrame
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Erro ao preparar dados para indicadores: {str(e)}")
            return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
    
    @staticmethod
    def calculate_rsi(df, period=14):
        """
        Calcula o Índice de Força Relativa (RSI)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            period (int): Período para cálculo do RSI
            
        Returns:
            pandas.Series: Série com os valores do RSI
        """
        try:
            # Calcula as diferenças entre preços de fechamento consecutivos
            delta = df['close'].diff()
            
            # Separa ganhos (ups) e perdas (downs)
            ups = delta.copy()
            downs = delta.copy()
            ups[ups < 0] = 0
            downs[downs > 0] = 0
            downs = abs(downs)
            
            # Calcula médias móveis de ganhos e perdas
            avg_ups = ups.rolling(window=period).mean()
            avg_downs = downs.rolling(window=period).mean()
            
            # Calcula RS (Relative Strength)
            rs = avg_ups / avg_downs
            
            # Calcula RSI
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {str(e)}")
            return pd.Series()  # Retorna série vazia em caso de erro
    
    @staticmethod
    def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
        """
        Calcula o MACD (Moving Average Convergence Divergence)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            fast_period (int): Período para EMA rápida
            slow_period (int): Período para EMA lenta
            signal_period (int): Período para linha de sinal
            
        Returns:
            tuple: (MACD, Signal, Histogram)
        """
        try:
            # Calcula EMAs
            ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
            ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
            
            # Calcula MACD
            macd = ema_fast - ema_slow
            
            # Calcula linha de sinal
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            
            # Calcula histograma
            histogram = macd - signal
            
            return macd, signal, histogram
        except Exception as e:
            logger.error(f"Erro ao calcular MACD: {str(e)}")
            return pd.Series(), pd.Series(), pd.Series()
    
    @staticmethod
    def calculate_bollinger_bands(df, period=20, std_dev=2):
        """
        Calcula as Bandas de Bollinger
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            period (int): Período para a média móvel
            std_dev (int): Número de desvios padrão
            
        Returns:
            tuple: (Upper Band, Middle Band, Lower Band)
        """
        try:
            # Calcula a média móvel simples
            middle_band = df['close'].rolling(window=period).mean()
            
            # Calcula o desvio padrão
            rolling_std = df['close'].rolling(window=period).std()
            
            # Calcula as bandas superior e inferior
            upper_band = middle_band + (rolling_std * std_dev)
            lower_band = middle_band - (rolling_std * std_dev)
            
            return upper_band, middle_band, lower_band
        except Exception as e:
            logger.error(f"Erro ao calcular Bandas de Bollinger: {str(e)}")
            return pd.Series(), pd.Series(), pd.Series()
    
    @staticmethod
    def calculate_stochastic_oscillator(df, k_period=14, d_period=3):
        """
        Calcula o Oscilador Estocástico (%K e %D)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            k_period (int): Período para %K
            d_period (int): Período para %D
            
        Returns:
            tuple: (%K, %D)
        """
        try:
            # Obtém máximos e mínimos do período
            low_min = df['low'].rolling(window=k_period).min()
            high_max = df['high'].rolling(window=k_period).max()
            
            # Calcula %K
            k = 100 * ((df['close'] - low_min) / (high_max - low_min))
            
            # Calcula %D
            d = k.rolling(window=d_period).mean()
            
            return k, d
        except Exception as e:
            logger.error(f"Erro ao calcular Oscilador Estocástico: {str(e)}")
            return pd.Series(), pd.Series()
    
    @staticmethod
    def calculate_ema(df, period=20):
        """
        Calcula a Média Móvel Exponencial (EMA)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            period (int): Período para a EMA
            
        Returns:
            pandas.Series: Série com os valores da EMA
        """
        try:
            ema = df['close'].ewm(span=period, adjust=False).mean()
            return ema
        except Exception as e:
            logger.error(f"Erro ao calcular EMA: {str(e)}")
            return pd.Series()
    
    @staticmethod
    def calculate_sma(df, period=20):
        """
        Calcula a Média Móvel Simples (SMA)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            period (int): Período para a SMA
            
        Returns:
            pandas.Series: Série com os valores da SMA
        """
        try:
            sma = df['close'].rolling(window=period).mean()
            return sma
        except Exception as e:
            logger.error(f"Erro ao calcular SMA: {str(e)}")
            return pd.Series()
    
    @staticmethod
    def calculate_atr(df, period=14):
        """
        Calcula o Average True Range (ATR)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            period (int): Período para o ATR
            
        Returns:
            pandas.Series: Série com os valores do ATR
        """
        try:
            # Calcula o True Range
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            
            # Calcula o ATR
            atr = true_range.rolling(window=period).mean()
            
            return atr
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {str(e)}")
            return pd.Series()
    
    @staticmethod
    def calculate_ichimoku(df, conversion_period=9, base_period=26, lagging_span2_period=52):
        """
        Calcula o Ichimoku Cloud
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            conversion_period (int): Período para Tenkan-sen (Conversion Line)
            base_period (int): Período para Kijun-sen (Base Line)
            lagging_span2_period (int): Período para Senkou Span B
            
        Returns:
            tuple: (Conversion Line, Base Line, Leading Span A, Leading Span B, Lagging Span)
        """
        try:
            # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
            conversion_line = (df['high'].rolling(window=conversion_period).max() + 
                            df['low'].rolling(window=conversion_period).min()) / 2
            
            # Kijun-sen (Base Line): (26-period high + 26-period low)/2
            base_line = (df['high'].rolling(window=base_period).max() + 
                        df['low'].rolling(window=base_period).min()) / 2
            
            # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
            leading_span_a = ((conversion_line + base_line) / 2).shift(base_period)
            
            # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
            leading_span_b = ((df['high'].rolling(window=lagging_span2_period).max() + 
                            df['low'].rolling(window=lagging_span2_period).min()) / 2).shift(base_period)
            
            # Chikou Span (Lagging Span): Close shifted back 26 periods
            lagging_span = df['close'].shift(-base_period)
            
            return conversion_line, base_line, leading_span_a, leading_span_b, lagging_span
        except Exception as e:
            logger.error(f"Erro ao calcular Ichimoku Cloud: {str(e)}")
            empty = pd.Series()
            return empty, empty, empty, empty, empty
    
    @staticmethod
    def calculate_volume_profile(df, price_range=10):
        """
        Calcula o Perfil de Volume (Volume Profile)
        
        Args:
            df (pandas.DataFrame): DataFrame com dados OHLCV
            price_range (int): Número de divisões de preço
            
        Returns:
            pandas.DataFrame: DataFrame com os dados do Perfil de Volume
        """
        try:
            min_price = df['low'].min()
            max_price = df['high'].max()
            
            # Cria intervalos de preço
            price_ranges = np.linspace(min_price, max_price, price_range + 1)
            
            # Cria DataFrame para armazenar dados do Perfil de Volume
            volume_profile = pd.DataFrame(index=range(price_range), 
                                        columns=['price_low', 'price_high', 'volume'])
            
            # Calcula volume para cada intervalo de preço
            for i in range(price_range):
                price_low = price_ranges[i]
                price_high = price_ranges[i + 1]
                
                # Seleciona velas onde o preço estava dentro do intervalo
                mask = ((df['low'] <= price_high) & (df['high'] >= price_low))
                
                # Calcula volume dentro do intervalo
                volume = df.loc[mask, 'volume'].sum()
                
                # Armazena dados
                volume_profile.iloc[i] = [price_low, price_high, volume]
            
            # Encontra o Point of Control (POC) - nível de preço com maior volume
            poc_index = volume_profile['volume'].idxmax()
            poc_price_low = volume_profile.loc[poc_index, 'price_low']
            poc_price_high = volume_profile.loc[poc_index, 'price_high']
            poc_price = (poc_price_low + poc_price_high) / 2
            
            # Adiciona POC ao DataFrame
            volume_profile['poc'] = False
            volume_profile.loc[poc_index, 'poc'] = True
            
            return volume_profile, poc_price
        except Exception as e:
            logger.error(f"Erro ao calcular Perfil de Volume: {str(e)}")
            return pd.DataFrame(), None
    
    @staticmethod
    def calculate_all_indicators(klines):
        """
        Calcula todos os indicadores técnicos disponíveis
        
        Args:
            klines (list): Lista de velas no formato da API da Binance
            
        Returns:
            dict: Dicionário com todos os indicadores calculados
        """
        try:
            # Prepara os dados
            df = TechnicalIndicators.prepare_data(klines)
            if df.empty:
                logger.warning("Dados vazios ou inválidos para cálculo de indicadores")
                return {}
            
            # Calcula indicadores
            rsi = TechnicalIndicators.calculate_rsi(df)
            macd, signal, histogram = TechnicalIndicators.calculate_macd(df)
            upper_band, middle_band, lower_band = TechnicalIndicators.calculate_bollinger_bands(df)
            stoch_k, stoch_d = TechnicalIndicators.calculate_stochastic_oscillator(df)
            ema_9 = TechnicalIndicators.calculate_ema(df, 9)
            ema_21 = TechnicalIndicators.calculate_ema(df, 21)
            sma_50 = TechnicalIndicators.calculate_sma(df, 50)
            sma_200 = TechnicalIndicators.calculate_sma(df, 200)
            atr = TechnicalIndicators.calculate_atr(df)
            
            # Obtém os valores mais recentes
            latest_data = {
                'timestamp': df.index[-1].isoformat(),
                'price': {
                    'open': float(df['open'].iloc[-1]),
                    'high': float(df['high'].iloc[-1]),
                    'low': float(df['low'].iloc[-1]),
                    'close': float(df['close'].iloc[-1]),
                    'volume': float(df['volume'].iloc[-1])
                },
                'indicators': {
                    'rsi': {
                        'current': float(rsi.iloc[-1]),
                        'previous': float(rsi.iloc[-2]),
                        'overbought': rsi.iloc[-1] > 70,
                        'oversold': rsi.iloc[-1] < 30,
                        'crossed_up_30': rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30,
                        'crossed_down_70': rsi.iloc[-2] > 70 and rsi.iloc[-1] < 70
                    },
                    'macd': {
                        'macd': float(macd.iloc[-1]),
                        'signal': float(signal.iloc[-1]),
                        'histogram': float(histogram.iloc[-1]),
                        'crossed_up': macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1],
                        'crossed_down': macd.iloc[-2] > signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]
                    },
                    'bollinger_bands': {
                        'upper': float(upper_band.iloc[-1]),
                        'middle': float(middle_band.iloc[-1]),
                        'lower': float(lower_band.iloc[-1]),
                        'bandwidth': float((upper_band.iloc[-1] - lower_band.iloc[-1]) / middle_band.iloc[-1]),
                        'above_upper': df['close'].iloc[-1] > upper_band.iloc[-1],
                        'below_lower': df['close'].iloc[-1] < lower_band.iloc[-1]
                    },
                    'stochastic': {
                        'k': float(stoch_k.iloc[-1]),
                        'd': float(stoch_d.iloc[-1]),
                        'overbought': stoch_k.iloc[-1] > 80,
                        'oversold': stoch_k.iloc[-1] < 20,
                        'crossed_up': stoch_k.iloc[-2] < stoch_d.iloc[-2] and stoch_k.iloc[-1] > stoch_d.iloc[-1],
                        'crossed_down': stoch_k.iloc[-2] > stoch_d.iloc[-2] and stoch_k.iloc[-1] < stoch_d.iloc[-1]
                    },
                    'moving_averages': {
                        'ema_9': float(ema_9.iloc[-1]),
                        'ema_21': float(ema_21.iloc[-1]),
                        'sma_50': float(sma_50.iloc[-1]),
                        'sma_200': float(sma_200.iloc[-1]),
                        'ema_9_crossed_up_ema_21': ema_9.iloc[-2] < ema_21.iloc[-2] and ema_9.iloc[-1] > ema_21.iloc[-1],
                        'ema_9_crossed_down_ema_21': ema_9.iloc[-2] > ema_21.iloc[-2] and ema_9.iloc[-1] < ema_21.iloc[-1],
                        'price_above_sma_200': df['close'].iloc[-1] > sma_200.iloc[-1],
                        'golden_cross': sma_50.iloc[-2] < sma_200.iloc[-2] and sma_50.iloc[-1] > sma_200.iloc[-1],
                        'death_cross': sma_50.iloc[-2] > sma_200.iloc[-2] and sma_50.iloc[-1] < sma_200.iloc[-1]
                    },
                    'atr': {
                        'current': float(atr.iloc[-1]),
                        'relative': float(atr.iloc[-1] / df['close'].iloc[-1])  # ATR relativo ao preço
                    }
                },
                'calculated_at': datetime.now().isoformat()
            }
            
            # Adiciona análise técnica agregada (possíveis sinais)
            latest_data['technical_signals'] = TechnicalIndicators.analyze_signals(latest_data)
            
            return latest_data
            
        except Exception as e:
            logger.error(f"Erro ao calcular todos os indicadores: {str(e)}")
            return {}
    
    @staticmethod
    def analyze_signals(data):
        """
        Analisa os valores dos indicadores e gera sinais técnicos
        
        Args:
            data (dict): Dicionário com indicadores técnicos
            
        Returns:
            dict: Dicionário com sinais técnicos
        """
        try:
            signals = {
                'buy_signals': [],
                'sell_signals': [],
                'overall_trend': 'neutral',
                'trend_strength': 0.0,
                'support_levels': [],
                'resistance_levels': []
            }
            
            indicators = data['indicators']
            price = data['price']['close']
            
            # Verifica sinais de compra
            if indicators['rsi']['oversold'] or indicators['rsi']['crossed_up_30']:
                signals['buy_signals'].append('RSI oversold or crossing up from oversold')
            
            if indicators['macd']['crossed_up']:
                signals['buy_signals'].append('MACD crossed above signal line')
            
            if indicators['bollinger_bands']['below_lower']:
                signals['buy_signals'].append('Price below lower Bollinger Band')
            
            if indicators['stochastic']['oversold'] and indicators['stochastic']['crossed_up']:
                signals['buy_signals'].append('Stochastic oversold and crossing up')
                
            if indicators['moving_averages']['ema_9_crossed_up_ema_21']:
                signals['buy_signals'].append('EMA9 crossed above EMA21')
                
            if indicators['moving_averages']['golden_cross']:
                signals['buy_signals'].append('Golden Cross (SMA50 crossed above SMA200)')
            
            # Verifica sinais de venda
            if indicators['rsi']['overbought'] or indicators['rsi']['crossed_down_70']:
                signals['sell_signals'].append('RSI overbought or crossing down from overbought')
            
            if indicators['macd']['crossed_down']:
                signals['sell_signals'].append('MACD crossed below signal line')
            
            if indicators['bollinger_bands']['above_upper']:
                signals['sell_signals'].append('Price above upper Bollinger Band')
            
            if indicators['stochastic']['overbought'] and indicators['stochastic']['crossed_down']:
                signals['sell_signals'].append('Stochastic overbought and crossing down')
                
            if indicators['moving_averages']['ema_9_crossed_down_ema_21']:
                signals['sell_signals'].append('EMA9 crossed below EMA21')
                
            if indicators['moving_averages']['death_cross']:
                signals['sell_signals'].append('Death Cross (SMA50 crossed below SMA200)')
            
            # Determina tendência geral
            trend_factors = []
            
            # RSI (acima de 50 = bullish, abaixo de 50 = bearish)
            rsi_factor = (indicators['rsi']['current'] - 50) / 50  # -1 a 1
            trend_factors.append(rsi_factor)
            
            # MACD (positivo = bullish, negativo = bearish)
            macd_factor = 1 if indicators['macd']['macd'] > 0 else -1
            trend_factors.append(macd_factor)
            
            # Médias móveis
            price_vs_ma_factor = 0
            if price > indicators['moving_averages']['ema_9'] > indicators['moving_averages']['ema_21']:
                price_vs_ma_factor = 1  # Forte tendência de alta
            elif price < indicators['moving_averages']['ema_9'] < indicators['moving_averages']['ema_21']:
                price_vs_ma_factor = -1  # Forte tendência de baixa
            trend_factors.append(price_vs_ma_factor)
            
            # Preço em relação à SMA200 (acima = bullish, abaixo = bearish)
            sma200_factor = 1 if indicators['moving_averages']['price_above_sma_200'] else -1
            trend_factors.append(sma200_factor)
            
            # Calcula a força média da tendência
            trend_strength = sum(trend_factors) / len(trend_factors)
            signals['trend_strength'] = round(trend_strength, 2)
            
            # Determina a tendência com base na força
            if trend_strength > 0.5:
                signals['overall_trend'] = 'strong_bullish'
            elif trend_strength > 0.2:
                signals['overall_trend'] = 'bullish'
            elif trend_strength < -0.5:
                signals['overall_trend'] = 'strong_bearish'
            elif trend_strength < -0.2:
                signals['overall_trend'] = 'bearish'
            else:
                signals['overall_trend'] = 'neutral'
                
            # Níveis de suporte e resistência
            signals['support_levels'].append(indicators['bollinger_bands']['lower'])
            signals['resistance_levels'].append(indicators['bollinger_bands']['upper'])
            
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao analisar sinais técnicos: {str(e)}")
            return {
                'buy_signals': [],
                'sell_signals': [],
                'overall_trend': 'unknown',
                'trend_strength': 0.0,
                'support_levels': [],
                'resistance_levels': []
            }
