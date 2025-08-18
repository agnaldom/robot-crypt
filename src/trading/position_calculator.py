#!/usr/bin/env python3
"""
Sistema de cálculo de posição considerando limites do par
"""
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.trading.order_validator import OrderValidator


@dataclass
class PositionSize:
    """Resultado do cálculo de posição"""
    quantity: Decimal
    value: Decimal
    risk_percentage: Decimal
    is_valid: bool
    warnings: list = None
    adjusted_from_original: bool = False


class PositionCalculator:
    """Calculadora de posição que considera limites do par"""
    
    def __init__(self, binance_api):
        self.binance_api = binance_api
        self.logger = logging.getLogger(__name__)
        self.validator = OrderValidator(binance_api)
        
    def calculate_position(
        self, 
        symbol: str, 
        available_balance: Decimal, 
        price: Decimal,
        risk_percentage: Decimal = Decimal('0.01'),  # 1% default
        max_position_percentage: Decimal = Decimal('0.05')  # 5% max default
    ) -> PositionSize:
        """
        Calcula tamanho da posição considerando:
        1. Risco máximo por trade
        2. Limites máximos do par
        3. Valor mínimo notional
        4. Step size e tick size
        """
        warnings = []
        adjusted_from_original = False
        
        try:
            # 1. Cálculo inicial baseado no risco
            risk_value = available_balance * risk_percentage
            initial_quantity = risk_value / price
            
            # 2. Aplica limite máximo de posição
            max_position_value = available_balance * max_position_percentage
            if risk_value > max_position_value:
                risk_value = max_position_value
                initial_quantity = risk_value / price
                warnings.append(f"Valor limitado a {max_position_percentage*100:.1f}% do capital")
                adjusted_from_original = True
            
            # 3. Valida e ajusta com base nos limites do par
            validation_result = self.validator.validate_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=initial_quantity,
                price=price
            )
            
            if not validation_result.is_valid:
                self.logger.error(f"Não foi possível calcular posição válida para {symbol}: "
                                f"{'; '.join(validation_result.errors)}")
                return PositionSize(
                    quantity=Decimal('0'),
                    value=Decimal('0'),
                    risk_percentage=Decimal('0'),
                    is_valid=False,
                    warnings=validation_result.errors
                )
            
            # 4. Usa quantidade ajustada
            final_quantity = validation_result.adjusted_quantity
            final_value = final_quantity * price
            final_risk_percentage = final_value / available_balance
            
            # 5. Adiciona warnings da validação
            if validation_result.warnings:
                warnings.extend(validation_result.warnings)
                adjusted_from_original = True
            
            # 6. Verifica se o ajuste final ainda está dentro do risco aceitável
            if final_risk_percentage > max_position_percentage * Decimal('1.1'):  # 10% de tolerância
                self.logger.warning(f"Posição ajustada excede limite de risco para {symbol}")
                return PositionSize(
                    quantity=Decimal('0'),
                    value=Decimal('0'),
                    risk_percentage=Decimal('0'),
                    is_valid=False,
                    warnings=["Posição excede limite de risco após ajustes"]
                )
            
            self.logger.info(f"Posição calculada para {symbol}: "
                           f"qty={final_quantity}, value={final_value:.2f}, "
                           f"risk={final_risk_percentage*100:.2f}%")
            
            return PositionSize(
                quantity=final_quantity,
                value=final_value,
                risk_percentage=final_risk_percentage,
                is_valid=True,
                warnings=warnings,
                adjusted_from_original=adjusted_from_original
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular posição para {symbol}: {str(e)}")
            return PositionSize(
                quantity=Decimal('0'),
                value=Decimal('0'),
                risk_percentage=Decimal('0'),
                is_valid=False,
                warnings=[f"Erro no cálculo: {str(e)}"]
            )
    
    def get_position_recommendations(
        self, 
        symbol: str, 
        available_balance: Decimal, 
        price: Decimal
    ) -> Dict[str, PositionSize]:
        """
        Retorna recomendações de posição para diferentes estratégias
        """
        strategies = {
            'conservative': {
                'risk': Decimal('0.005'),  # 0.5%
                'max_position': Decimal('0.02')  # 2%
            },
            'moderate': {
                'risk': Decimal('0.01'),   # 1%
                'max_position': Decimal('0.05')  # 5%
            },
            'aggressive': {
                'risk': Decimal('0.02'),   # 2%
                'max_position': Decimal('0.10')  # 10%
            }
        }
        
        recommendations = {}
        
        for strategy_name, params in strategies.items():
            position = self.calculate_position(
                symbol=symbol,
                available_balance=available_balance,
                price=price,
                risk_percentage=params['risk'],
                max_position_percentage=params['max_position']
            )
            recommendations[strategy_name] = position
        
        return recommendations
    
    def calculate_stop_loss_position(
        self,
        symbol: str,
        available_balance: Decimal,
        entry_price: Decimal,
        stop_loss_price: Decimal,
        max_loss_percentage: Decimal = Decimal('0.01')  # 1% max loss
    ) -> PositionSize:
        """
        Calcula posição baseada no stop loss para limitar perda máxima
        """
        try:
            # Calcula a perda por unidade
            loss_per_unit = abs(entry_price - stop_loss_price)
            
            # Calcula quantidade máxima baseada na perda máxima aceitável
            max_loss_value = available_balance * max_loss_percentage
            max_quantity = max_loss_value / loss_per_unit
            
            # Valida com os limites do par
            validation_result = self.validator.validate_order(
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=max_quantity,
                price=entry_price
            )
            
            if not validation_result.is_valid:
                self.logger.error(f"Posição com stop loss inválida para {symbol}: "
                                f"{'; '.join(validation_result.errors)}")
                return PositionSize(
                    quantity=Decimal('0'),
                    value=Decimal('0'),
                    risk_percentage=Decimal('0'),
                    is_valid=False,
                    warnings=validation_result.errors
                )
            
            final_quantity = validation_result.adjusted_quantity
            final_value = final_quantity * entry_price
            final_risk_percentage = final_value / available_balance
            
            # Recalcula a perda real com a quantidade ajustada
            actual_max_loss = final_quantity * loss_per_unit
            actual_loss_percentage = actual_max_loss / available_balance
            
            warnings = []
            if validation_result.warnings:
                warnings.extend(validation_result.warnings)
            
            warnings.append(f"Perda máxima: {actual_loss_percentage*100:.2f}% "
                          f"(${actual_max_loss:.2f})")
            
            self.logger.info(f"Posição com stop loss para {symbol}: "
                           f"qty={final_quantity}, entrada=${entry_price}, "
                           f"stop=${stop_loss_price}, perda_max={actual_loss_percentage*100:.2f}%")
            
            return PositionSize(
                quantity=final_quantity,
                value=final_value,
                risk_percentage=final_risk_percentage,
                is_valid=True,
                warnings=warnings,
                adjusted_from_original=validation_result.adjusted_quantity != max_quantity
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular posição com stop loss para {symbol}: {str(e)}")
            return PositionSize(
                quantity=Decimal('0'),
                value=Decimal('0'),
                risk_percentage=Decimal('0'),
                is_valid=False,
                warnings=[f"Erro no cálculo: {str(e)}"]
            )
    
    def validate_position_size(
        self,
        symbol: str,
        quantity: Decimal,
        price: Decimal
    ) -> Tuple[bool, list]:
        """
        Valida se um tamanho de posição específico é válido
        """
        try:
            validation_result = self.validator.validate_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity,
                price=price
            )
            
            messages = []
            if validation_result.warnings:
                messages.extend([f"Warning: {w}" for w in validation_result.warnings])
            if validation_result.errors:
                messages.extend([f"Error: {e}" for e in validation_result.errors])
            
            return validation_result.is_valid, messages
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
