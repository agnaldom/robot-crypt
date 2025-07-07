#!/usr/bin/env python3
"""
Módulo de conversão de tipos para Robot-Crypt
Fornece utilitários para converter tipos numpy e outras estruturas de dados
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Union
import logging
from dataclasses import asdict, is_dataclass

logger = logging.getLogger("robot-crypt")


def convert_numpy_types(obj: Any) -> Any:
    """
    Converte tipos numpy para tipos nativos do Python recursivamente
    
    Args:
        obj: Objeto a ser convertido
        
    Returns:
        Objeto com tipos convertidos
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif pd.isna(obj) or (isinstance(obj, float) and np.isnan(obj)):
        return None
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif is_dataclass(obj):
        return convert_numpy_types(asdict(obj))
    else:
        return obj


def convert_numpy_output(data: Any) -> Any:
    """
    Converte saída de funções que podem retornar tipos numpy
    
    Args:
        data: Dados a serem convertidos
        
    Returns:
        Dados convertidos para tipos nativos
    """
    return convert_numpy_types(data)


def fix_analysis_data(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corrige dados de análise convertendo tipos numpy para tipos nativos
    
    Args:
        analysis_data: Dicionário com dados de análise
        
    Returns:
        Dicionário com tipos convertidos
    """
    try:
        # Conversão recursiva de todos os dados
        fixed_data = convert_numpy_types(analysis_data)
        
        # Verificações específicas para estruturas de dados comuns
        if 'market_data' in fixed_data and isinstance(fixed_data['market_data'], dict):
            # Converte dados de mercado
            market_data = fixed_data['market_data']
            for key, value in market_data.items():
                if isinstance(value, (pd.Series, pd.DataFrame)):
                    market_data[key] = convert_numpy_types(value)
        
        if 'signals' in fixed_data and isinstance(fixed_data['signals'], list):
            # Converte lista de sinais (incluindo dataclasses)
            fixed_data['signals'] = convert_numpy_types(fixed_data['signals'])
        
        if 'indicators_data' in fixed_data:
            # Converte dados de indicadores
            fixed_data['indicators_data'] = convert_numpy_types(fixed_data['indicators_data'])
        
        return fixed_data
        
    except Exception as e:
        logger.error(f"Erro ao corrigir dados de análise: {str(e)}")
        # Retorna os dados originais em caso de erro
        return analysis_data


def clean_financial_data(data: Union[Dict, List, pd.DataFrame, pd.Series]) -> Any:
    """
    Limpa dados financeiros removendo valores infinitos e NaN
    
    Args:
        data: Dados financeiros a serem limpos
        
    Returns:
        Dados limpos
    """
    try:
        if isinstance(data, pd.DataFrame):
            # Para DataFrames, replace inf e -inf com NaN, depois dropna
            data = data.replace([np.inf, -np.inf], np.nan)
            return data.dropna()
        
        elif isinstance(data, pd.Series):
            # Para Series, similar ao DataFrame
            data = data.replace([np.inf, -np.inf], np.nan)
            return data.dropna()
        
        elif isinstance(data, dict):
            # Para dicionários, limpa recursivamente
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if np.isfinite(value) and not pd.isna(value):
                        cleaned[key] = value
                    else:
                        cleaned[key] = None
                else:
                    cleaned[key] = clean_financial_data(value)
            return cleaned
        
        elif isinstance(data, list):
            # Para listas, limpa cada elemento
            cleaned = []
            for item in data:
                if isinstance(item, (int, float)):
                    if np.isfinite(item) and not pd.isna(item):
                        cleaned.append(item)
                    else:
                        cleaned.append(None)
                else:
                    cleaned.append(clean_financial_data(item))
            return cleaned
        
        elif isinstance(data, (int, float)):
            # Para números individuais
            if np.isfinite(data) and not pd.isna(data):
                return data
            else:
                return None
        
        else:
            return data
            
    except Exception as e:
        logger.error(f"Erro ao limpar dados financeiros: {str(e)}")
        return data


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formata um valor como percentual
    
    Args:
        value: Valor decimal (0.05 = 5%)
        decimals: Número de casas decimais
        
    Returns:
        String formatada como percentual
    """
    try:
        if pd.isna(value) or not np.isfinite(value):
            return "N/A"
        return f"{value * 100:.{decimals}f}%"
    except:
        return "N/A"


def format_currency(value: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    Formata um valor como moeda
    
    Args:
        value: Valor numérico
        currency: Código da moeda
        decimals: Número de casas decimais
        
    Returns:
        String formatada como moeda
    """
    try:
        if pd.isna(value) or not np.isfinite(value):
            return f"N/A {currency}"
        
        if currency.upper() == "USD":
            return f"${value:,.{decimals}f}"
        elif currency.upper() == "BRL":
            return f"R$ {value:,.{decimals}f}"
        else:
            return f"{value:,.{decimals}f} {currency}"
    except:
        return f"N/A {currency}"


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Divisão segura que trata divisão por zero
    
    Args:
        a: Numerador
        b: Denominador
        default: Valor padrão para divisão por zero
        
    Returns:
        Resultado da divisão ou valor padrão
    """
    try:
        if b == 0 or pd.isna(b) or not np.isfinite(b):
            return default
        if pd.isna(a) or not np.isfinite(a):
            return default
        
        result = a / b
        if not np.isfinite(result):
            return default
        
        return result
    except:
        return default


def normalize_data(data: Union[List, np.ndarray, pd.Series], method: str = "minmax") -> Union[List, np.ndarray]:
    """
    Normaliza dados numéricos
    
    Args:
        data: Dados a serem normalizados
        method: Método de normalização ('minmax', 'zscore')
        
    Returns:
        Dados normalizados
    """
    try:
        # Converte para numpy array
        if isinstance(data, pd.Series):
            arr = data.values
        elif isinstance(data, list):
            arr = np.array(data)
        else:
            arr = data
        
        # Remove valores NaN e infinitos
        arr = arr[np.isfinite(arr)]
        
        if len(arr) == 0:
            return []
        
        if method == "minmax":
            # Normalização Min-Max (0-1)
            min_val = np.min(arr)
            max_val = np.max(arr)
            if max_val == min_val:
                return np.ones_like(arr) * 0.5  # Retorna 0.5 se todos valores são iguais
            return (arr - min_val) / (max_val - min_val)
        
        elif method == "zscore":
            # Normalização Z-score (média 0, desvio 1)
            mean_val = np.mean(arr)
            std_val = np.std(arr)
            if std_val == 0:
                return np.zeros_like(arr)  # Retorna zeros se não há variação
            return (arr - mean_val) / std_val
        
        else:
            logger.warning(f"Método de normalização não reconhecido: {method}")
            return arr
            
    except Exception as e:
        logger.error(f"Erro ao normalizar dados: {str(e)}")
        return data


def validate_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida dados financeiros verificando consistência e sanidade
    
    Args:
        data: Dados financeiros a serem validados
        
    Returns:
        Dados validados com flags de qualidade
    """
    try:
        validated_data = data.copy()
        validation_flags = {
            'has_negative_prices': False,
            'has_zero_volumes': False,
            'has_missing_data': False,
            'data_quality_score': 1.0
        }
        
        # Verifica preços negativos
        for key in ['open', 'high', 'low', 'close', 'price']:
            if key in data:
                value = data[key]
                if isinstance(value, (list, np.ndarray, pd.Series)):
                    if any(v < 0 for v in value if np.isfinite(v)):
                        validation_flags['has_negative_prices'] = True
                        validation_flags['data_quality_score'] -= 0.2
                elif isinstance(value, (int, float)) and value < 0:
                    validation_flags['has_negative_prices'] = True
                    validation_flags['data_quality_score'] -= 0.2
        
        # Verifica volumes zero
        if 'volume' in data:
            volume = data['volume']
            if isinstance(volume, (list, np.ndarray, pd.Series)):
                zero_count = sum(1 for v in volume if v == 0)
                if zero_count > len(volume) * 0.1:  # Mais de 10% de volumes zero
                    validation_flags['has_zero_volumes'] = True
                    validation_flags['data_quality_score'] -= 0.1
            elif isinstance(volume, (int, float)) and volume == 0:
                validation_flags['has_zero_volumes'] = True
                validation_flags['data_quality_score'] -= 0.1
        
        # Verifica dados faltantes
        for key, value in data.items():
            if value is None:
                validation_flags['has_missing_data'] = True
                validation_flags['data_quality_score'] -= 0.1
            elif isinstance(value, (list, np.ndarray, pd.Series)):
                if any(pd.isna(v) for v in value):
                    validation_flags['has_missing_data'] = True
                    validation_flags['data_quality_score'] -= 0.1
        
        # Garante que o score não seja negativo
        validation_flags['data_quality_score'] = max(0.0, validation_flags['data_quality_score'])
        
        validated_data['_validation'] = validation_flags
        return validated_data
        
    except Exception as e:
        logger.error(f"Erro ao validar dados financeiros: {str(e)}")
        data['_validation'] = {'data_quality_score': 0.0, 'validation_error': str(e)}
        return data


def convert_timeframe_to_seconds(timeframe: str) -> int:
    """
    Converte timeframe para segundos
    
    Args:
        timeframe: String do timeframe (ex: '1m', '5m', '1h', '1d')
        
    Returns:
        Número de segundos correspondente
    """
    timeframe_map = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '6h': 21600,
        '8h': 28800,
        '12h': 43200,
        '1d': 86400,
        '3d': 259200,
        '1w': 604800,
        '1M': 2592000  # Aproximado para 30 dias
    }
    
    return timeframe_map.get(timeframe, 3600)  # Default: 1 hora


def ensure_json_serializable(data: Any) -> Any:
    """
    Garante que os dados sejam serializáveis em JSON
    
    Args:
        data: Dados a serem verificados
        
    Returns:
        Dados serializáveis em JSON
    """
    try:
        import json
        
        # Primeiro, converte tipos numpy
        converted = convert_numpy_types(data)
        
        # Testa se é serializável
        json.dumps(converted, default=str)
        
        return converted
        
    except TypeError as e:
        logger.warning(f"Dados não são completamente serializáveis: {str(e)}")
        # Fallback: converte tudo para string
        return str(data)
    except Exception as e:
        logger.error(f"Erro ao garantir serialização JSON: {str(e)}")
        return None
