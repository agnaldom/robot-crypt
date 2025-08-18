"""
Harmonic Pattern Detector for identifying Butterfly patterns in market data.
"""
from typing import List, Dict, Any
import numpy as np

class HarmonicPatternDetector:
    """
    Class for detecting Harmonic Butterfly patterns in candlestick data.
    """
    @staticmethod
    def calculate_fibonacci_ratios(points: List[float]) -> Dict[str, float]:
        """
        Calculate Fibonacci ratios between given points.

        Args:
            points (List[float]): List of price points (X, A, B, C, D)
        
        Returns:
            Dict[str, float]: Calculated Fibonacci ratios
        """
        X, A, B, C, D = points
        return {
            'AB': abs((B - A) / (A - X)),
            'BC': abs((C - B) / (B - A)),
            'CD': abs((D - C) / (C - B)),
            'XA': abs((A - X) / (D - X))
        }

    def detect_butterfly_pattern(self, klines: List[List[float]]) -> List[Dict[str, Any]]:
        """
        Detect potential Butterfly patterns in candlestick data.

        Args:
            klines (List[List[float]]): List of candlestick data

        Returns:
            List[Dict[str, Any]]: List of detected patterns with their indices
        """
        detected_patterns = []
        closes = np.array([k[4] for k in klines])  # Using closing prices

        # Pattern detection logic
        for i in range(4, len(closes)):
            X, A, B, C, D = closes[i-4:i+1]
            ratios = self.calculate_fibonacci_ratios([X, A, B, C, D])
            
            if self.is_butterfly_pattern(ratios):
                detected_patterns.append({
                    'pattern': 'Butterfly',
                    'index': i,
                    'points': [X, A, B, C, D]
                })

        return detected_patterns

    @staticmethod
    def is_butterfly_pattern(ratios: Dict[str, float]) -> bool:
        """
        Validate Butterfly pattern based on Fibonacci ratios.

        Args:
            ratios (Dict[str, float]): Fibonacci ratios for pattern validation

        Returns:
            bool: True if valid Butterfly pattern, False otherwise
        """
        return (
            0.786 < ratios['AB'] < 0.886 and
            0.382 < ratios['BC'] < 0.886 and
            1.618 < ratios['CD'] < 2.618 and
            1.272 < ratios['XA'] < 1.618
        )

