import time
import logging
from datetime import datetime, timedelta
from config import (
    TRADE_AMOUNT, TAKE_PROFIT_PERCENTAGE, STOP_LOSS_PERCENTAGE,
    MAX_HOLD_TIME, ENTRY_DELAY
)

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, binance_api, telegram_notifier):
        self.binance_api = binance_api
        self.telegram_notifier = telegram_notifier
        self.active_trades = {}
    
    def handle_new_listing(self, listing_info):
        """Gerencia o processo de trading para uma nova listagem."""
        symbol = listing_info['symbol']
        
        # Verificar se o par de trading existe (normalmente será SYMBOL/USDT)
        trading_pair = f"{symbol}USDT"
        symbol_info = self.binance_api.get_symbol_info(trading_pair)
        
        if not symbol_info:
            logger.warning(f"Par de trading {trading_pair} não encontrado na Binance.")
            self.telegram_notifier.notify_error(f"Par de trading {trading_pair} não encontrado.")
            return False
        
        # Aguardar o tempo de entrada após a listagem
        logger.info(f"Aguardando {ENTRY_DELAY} segundos antes de entrar na operação...")
        time.sleep(ENTRY_DELAY)
        
        # Executar a ordem de compra
        return self.execute_buy_order(trading_pair)
    
    def execute_buy_order(self, symbol):
        """Executa uma ordem de compra."""
        # Obter o preço atual
        current_price = self.binance_api.get_latest_price(symbol)
        if not current_price:
            logger.error(f"Não foi possível obter o preço para {symbol}")
            self.telegram_notifier.notify_error(f"Falha ao obter preço para {symbol}")
            return False
        
        # Calcular a quantidade a ser comprada
        quantity = TRADE_AMOUNT / current_price
        
        # Ajustar a quantidade conforme as regras do par (step size)
        symbol_info = self.binance_api.get_symbol_info(symbol)
        for filter_item in symbol_info.get('filters', []):
            if filter_item['filterType'] == 'LOT_SIZE':
                step_size = float(filter_item['stepSize'])
                quantity = (quantity // step_size) * step_size
        
        # Executar a ordem
        order_result = self.binance_api.create_order(symbol, "BUY", quantity)
        
        if not order_result or 'status' not in order_result or order_result['status'] != 'FILLED':
            logger.error(f"Falha ao executar ordem de compra para {symbol}")
            self.telegram_notifier.notify_error(f"Falha na ordem de compra para {symbol}")
            return False
        
        # Calcular valores para monitoramento
        actual_quantity = float(order_result['executedQty'])
        actual_price = float(order_result['cummulativeQuoteQty']) / actual_quantity
        
        # Registrar a operação
        self.active_trades[symbol] = {
            'buy_price': actual_price,
            'quantity': actual_quantity,
            'buy_time': datetime.now(),
            'take_profit': actual_price * (1 + TAKE_PROFIT_PERCENTAGE / 100),
            'stop_loss': actual_price * (1 - STOP_LOSS_PERCENTAGE / 100)
        }
        
        # Notificar
        self.telegram_notifier.notify_buy_order(
            symbol, actual_price, actual_quantity, 
            actual_price * actual_quantity
        )
        
        logger.info(f"Ordem de compra executada para {symbol} a {actual_price}")
        return True
    
    def check_active_trades(self):
        """Verifica as operações ativas para possíveis saídas."""
        current_time = datetime.now()
        trades_to_remove = []
        
        for symbol, trade_info in self.active_trades.items():
            # Obter o preço atual
            current_price = self.binance_api.get_latest_price(symbol)
            if not current_price:
                logger.warning(f"Não foi possível obter o preço atual para {symbol}")
                continue
            
            buy_price = trade_info['buy_price']
            quantity = trade_info['quantity']
            buy_time = trade_info['buy_time']
            take_profit = trade_info['take_profit']
            stop_loss = trade_info['stop_loss']
            
            # Verificar condições de saída
            exit_reason = None
            
            # Take Profit
            if current_price >= take_profit:
                exit_reason = "Take Profit atingido"
            
            # Stop Loss
            elif current_price <= stop_loss:
                exit_reason = "Stop Loss atingido"
            
            # Tempo máximo de hold
            elif (current_time - buy_time).total_seconds() >= MAX_HOLD_TIME:
                exit_reason = "Tempo máximo de hold atingido"
            
            # Se alguma condição de saída foi atingida, executar a venda
            if exit_reason:
                sell_result = self.binance_api.create_order(symbol, "SELL", quantity)
                
                if sell_result and sell_result.get('status') == 'FILLED':
                    actual_sell_price = float(sell_result['cummulativeQuoteQty']) / float(sell_result['executedQty'])
                    profit_loss = (actual_sell_price - buy_price) * quantity
                    
                    self.telegram_notifier.notify_sell_order(
                        symbol, buy_price, actual_sell_price, 
                        quantity, profit_loss, exit_reason
                    )
                    
                    logger.info(f"Ordem de venda executada para {symbol}. Motivo: {exit_reason}")
                    trades_to_remove.append(symbol)
                else:
                    logger.error(f"Falha ao executar ordem de venda para {symbol}")
                    self.telegram_notifier.notify_error(f"Falha na ordem de venda para {symbol}")
        
        # Remover as operações concluídas
        for symbol in trades_to_remove:
            del self.active_trades[symbol]
