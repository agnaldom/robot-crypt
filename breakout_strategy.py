import time
from src.api.bingx.futures_client import BingXFuturesClient

class BreakoutStrategy:
    def __init__(self, api_key, api_secret):
        self.client = BingXFuturesClient(api_key, api_secret)

    def identify_breakout(self, symbol):
        # Fetch kline/candlestick data
        klines = self.client.get_klines(symbol, '1h', limit=100)
        latest_kline = klines[-1]
        prev_kline = klines[-2]
        
        # Check if the latest close price is a breakout
        if latest_kline[4] > prev_kline[2]:  # close > previous high
            return 'LONG'
        elif latest_kline[4] < prev_kline[3]:  # close < previous low
            return 'SHORT'
        return None

    def confirm_with_order_book(self, symbol, direction):
        depth = self.client.get_depth(symbol)
        bids = sum([float(bid[1]) for bid in depth['data']['bids']])
        asks = sum([float(ask[1]) for ask in depth['data']['asks']])
        
        # Confirm breakout direction with order book imbalance
        if direction == 'LONG' and bids > asks:
            return True
        elif direction == 'SHORT' and asks > bids:
            return True
        return False

    def execute_trade(self, symbol, direction):
        leverage = 20
        self.client.set_leverage(symbol, leverage)
        
        if direction == 'LONG':
            self.client.create_order(symbol=symbol, side='BUY', position_side='LONG', order_type='MARKET', quantity=1)
        elif direction == 'SHORT':
            self.client.create_order(symbol=symbol, side='SELL', position_side='SHORT', order_type='MARKET', quantity=1)

    def run(self, symbol):
        direction = self.identify_breakout(symbol)
        if direction:
            if self.confirm_with_order_book(symbol, direction):
                self.execute_trade(symbol, direction)

if __name__ == "__main__":
    API_KEY = 'your_api_key'
    API_SECRET = 'your_api_secret'
    symbol = 'BTC-USDT'

    strategy = BreakoutStrategy(API_KEY, API_SECRET)
    while True:
        strategy.run(symbol)
        time.sleep(60 * 60)  # Run every hour

