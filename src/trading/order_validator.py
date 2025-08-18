#!/usr/bin/env python3
"""
Sistema de validação de limites para ordens de trading
"""
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TradingLimits:
    """Limites de trading para um par específico"""
    min_quantity: Decimal
    max_quantity: Decimal
    step_size: Decimal
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal
    min_notional: Decimal
    max_notional: Optional[Decimal] = None


@dataclass
class OrderValidationResult:
    """Resultado da validação de ordem"""
    is_valid: bool
    adjusted_quantity: Optional[Decimal] = None
    adjusted_price: Optional[Decimal] = None
    errors: list = None
    warnings: list = None


class OrderValidator:
    """Validador de ordens com limites de trading"""
    
    def __init__(self, binance_api):
        self.binance_api = binance_api
        self.logger = logging.getLogger(__name__)
        self._limits_cache = {}
        
    def get_trading_limits(self, symbol: str) -> Optional[TradingLimits]:
        """
        Obtém os limites de trading para um símbolo específico
        """
        # Usa cache para evitar múltiplas chamadas à API
        if symbol in self._limits_cache:
            return self._limits_cache[symbol]
            
        try:
            symbol_info = self.binance_api.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.warning(f"Não foi possível obter informações para {symbol}")
                return None
                
            # Extrai filtros relevantes
            filters = {f['filterType']: f for f in symbol_info.get('filters', [])}
            
            # LOT_SIZE: define quantidade mínima, máxima e step size
            lot_size = filters.get('LOT_SIZE', {})
            min_quantity = Decimal(lot_size.get('minQty', '0'))
            max_quantity = Decimal(lot_size.get('maxQty', '9000000000'))
            step_size = Decimal(lot_size.get('stepSize', '0.00000001'))
            
            # PRICE_FILTER: define preço mínimo, máximo e tick size
            price_filter = filters.get('PRICE_FILTER', {})
            min_price = Decimal(price_filter.get('minPrice', '0'))
            max_price = Decimal(price_filter.get('maxPrice', '1000000'))
            tick_size = Decimal(price_filter.get('tickSize', '0.00000001'))
            
            # MIN_NOTIONAL: valor mínimo da ordem
            min_notional_filter = filters.get('MIN_NOTIONAL', {})
            min_notional = Decimal(min_notional_filter.get('minNotional', '0'))
            
            # MAX_NOTIONAL: valor máximo da ordem (se existir)
            max_notional_filter = filters.get('MAX_NOTIONAL', {})
            max_notional = None
            if max_notional_filter:
                max_notional = Decimal(max_notional_filter.get('maxNotional', '0'))
            
            limits = TradingLimits(
                min_quantity=min_quantity,
                max_quantity=max_quantity,
                step_size=step_size,
                min_price=min_price,
                max_price=max_price,
                tick_size=tick_size,
                min_notional=min_notional,
                max_notional=max_notional
            )
            
            # Cache os limites
            self._limits_cache[symbol] = limits
            
            self.logger.info(f"Limites obtidos para {symbol}: "
                           f"qty({min_quantity}-{max_quantity}), "
                           f"price({min_price}-{max_price}), "
                           f"notional(min:{min_notional})")
            
            return limits
            
        except Exception as e:
            self.logger.error(f"Erro ao obter limites para {symbol}: {str(e)}")
            return None
    
    def validate_order(self, symbol: str, side: str, order_type: str, 
                      quantity: Decimal, price: Optional[Decimal] = None) -> OrderValidationResult:
        """
        Valida uma ordem e ajusta parâmetros se necessário
        """
        errors = []
        warnings = []
        adjusted_quantity = quantity
        adjusted_price = price
        
        # Obtém limites do símbolo
        limits = self.get_trading_limits(symbol)
        if not limits:
            errors.append(f"Não foi possível obter limites para {symbol}")
            return OrderValidationResult(False, errors=errors)
        
        # 1. Validação de quantidade
        if quantity < limits.min_quantity:
            errors.append(f"Quantidade {quantity} abaixo do mínimo {limits.min_quantity}")
        elif quantity > limits.max_quantity:
            errors.append(f"Quantidade {quantity} acima do máximo {limits.max_quantity}")
        else:
            # Ajusta quantidade para o step size
            adjusted_quantity = self._adjust_to_step_size(quantity, limits.step_size)
            if adjusted_quantity != quantity:
                warnings.append(f"Quantidade ajustada de {quantity} para {adjusted_quantity}")
        
        # 2. Validação de preço (para ordens limit)
        if price and order_type.upper() in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
            if price < limits.min_price:
                errors.append(f"Preço {price} abaixo do mínimo {limits.min_price}")
            elif price > limits.max_price:
                errors.append(f"Preço {price} acima do máximo {limits.max_price}")
            else:
                # Ajusta preço para o tick size
                adjusted_price = self._adjust_to_tick_size(price, limits.tick_size)
                if adjusted_price != price:
                    warnings.append(f"Preço ajustado de {price} para {adjusted_price}")
        
        # 3. Validação de valor notional
        notional_value = adjusted_quantity * (adjusted_price or Decimal('0'))
        if adjusted_price and notional_value < limits.min_notional:
            # Tenta ajustar a quantidade para atingir o mínimo notional
            min_required_qty = limits.min_notional / adjusted_price
            adjusted_quantity = self._adjust_to_step_size(min_required_qty, limits.step_size)
            notional_value = adjusted_quantity * adjusted_price
            
            if notional_value < limits.min_notional:
                errors.append(f"Valor da ordem {notional_value} abaixo do mínimo {limits.min_notional}")
            else:
                warnings.append(f"Quantidade ajustada para {adjusted_quantity} para atingir valor mínimo")
        
        if limits.max_notional and adjusted_price and notional_value > limits.max_notional:
            errors.append(f"Valor da ordem {notional_value} acima do máximo {limits.max_notional}")
        
        is_valid = len(errors) == 0
        
        return OrderValidationResult(
            is_valid=is_valid,
            adjusted_quantity=adjusted_quantity,
            adjusted_price=adjusted_price,
            errors=errors,
            warnings=warnings
        )
    
    def calculate_max_position_size(self, symbol: str, available_balance: Decimal, 
                                  price: Decimal, risk_percentage: Decimal = Decimal('0.01')) -> Decimal:
        """
        Calcula o tamanho máximo da posição considerando limites e risco
        """
        limits = self.get_trading_limits(symbol)
        if not limits:
            self.logger.warning(f"Não foi possível calcular posição para {symbol}")
            return Decimal('0')
        
        # Calcula valor máximo baseado no risco
        max_risk_value = available_balance * risk_percentage
        
        # Calcula quantidade máxima baseada no preço
        max_quantity_by_price = max_risk_value / price
        
        # Aplica limites do símbolo
        max_quantity = min(max_quantity_by_price, limits.max_quantity)
        
        # Garante que não está abaixo do mínimo
        if max_quantity < limits.min_quantity:
            self.logger.warning(f"Quantidade calculada {max_quantity} abaixo do mínimo {limits.min_quantity}")
            return Decimal('0')
        
        # Ajusta para o step size
        adjusted_quantity = self._adjust_to_step_size(max_quantity, limits.step_size)
        
        # Verifica valor notional mínimo
        notional_value = adjusted_quantity * price
        if notional_value < limits.min_notional:
            min_required_qty = limits.min_notional / price
            adjusted_quantity = self._adjust_to_step_size(min_required_qty, limits.step_size)
            
            # Verifica se ainda está dentro dos limites após ajuste
            final_notional = adjusted_quantity * price
            if final_notional > max_risk_value:
                self.logger.warning(f"Valor mínimo notional excede risco máximo para {symbol}")
                return Decimal('0')
        
        self.logger.info(f"Posição calculada para {symbol}: {adjusted_quantity} "
                        f"(valor: {adjusted_quantity * price:.2f}, "
                        f"risco: {(adjusted_quantity * price / available_balance * 100):.2f}%)")
        
        return adjusted_quantity
    
    def _adjust_to_step_size(self, value: Decimal, step_size: Decimal) -> Decimal:
        """Ajusta valor para o step size usando arredondamento para baixo"""
        if step_size == 0:
            return value
        
        steps = value / step_size
        adjusted_steps = steps.quantize(Decimal('1'), rounding=ROUND_DOWN)
        return adjusted_steps * step_size
    
    def _adjust_to_tick_size(self, price: Decimal, tick_size: Decimal) -> Decimal:
        """Ajusta preço para o tick size"""
        if tick_size == 0:
            return price
        
        ticks = price / tick_size
        adjusted_ticks = ticks.quantize(Decimal('1'), rounding=ROUND_DOWN)
        return adjusted_ticks * tick_size
    
    def get_order_size_recommendations(self, symbol: str, balance: Decimal, 
                                     price: Decimal) -> Dict[str, Decimal]:
        """
        Retorna recomendações de tamanho de ordem para diferentes níveis de risco
        """
        recommendations = {}
        
        risk_levels = {
            'conservative': Decimal('0.005'),  # 0.5%
            'moderate': Decimal('0.01'),       # 1%
            'aggressive': Decimal('0.02')      # 2%
        }
        
        for level, risk in risk_levels.items():
            size = self.calculate_max_position_size(symbol, balance, price, risk)
            recommendations[level] = size
        
        return recommendations
    
    def clear_cache(self):
        """Limpa o cache de limites"""
        self._limits_cache.clear()
        self.logger.info("Cache de limites limpo")
