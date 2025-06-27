import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, message):
        """Envia uma mensagem para o chat do Telegram."""
        endpoint = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(endpoint, data=data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {e}")
            return False
    
    def notify_new_listing(self, listing_info):
        """Notifica sobre uma nova listagem detectada."""
        message = (
            f"🚨 <b>Nova listagem detectada!</b> 🚨\n\n"
            f"Moeda: {listing_info['symbol']}\n"
            f"Título: {listing_info['title']}\n"
            f"Data: {listing_info['date']}\n"
            f"Link: {listing_info['link']}\n\n"
            f"Bot está monitorando e vai entrar na operação em breve."
        )
        return self.send_message(message)
    
    def notify_buy_order(self, symbol, price, quantity, amount):
        """Notifica sobre uma ordem de compra executada."""
        message = (
            f"🟢 <b>Ordem de compra executada</b> 🟢\n\n"
            f"Moeda: {symbol}\n"
            f"Preço: {price}\n"
            f"Quantidade: {quantity}\n"
            f"Valor total: {amount}\n\n"
            f"Take Profit: {price * 1.1}\n"
            f"Stop Loss: {price * 0.95}"
        )
        return self.send_message(message)
    
    def notify_sell_order(self, symbol, buy_price, sell_price, quantity, profit_loss, reason):
        """Notifica sobre uma ordem de venda executada."""
        profit_percentage = ((sell_price / buy_price) - 1) * 100
        emoji = "🟢" if profit_percentage > 0 else "🔴"
        
        message = (
            f"{emoji} <b>Ordem de venda executada</b> {emoji}\n\n"
            f"Moeda: {symbol}\n"
            f"Preço de compra: {buy_price}\n"
            f"Preço de venda: {sell_price}\n"
            f"Quantidade: {quantity}\n"
            f"Lucro/Perda: {profit_loss} ({profit_percentage:.2f}%)\n"
            f"Motivo: {reason}"
        )
        return self.send_message(message)
    
    def notify_error(self, error_message):
        """Notifica sobre um erro ocorrido."""
        message = f"⚠️ <b>ERRO</b> ⚠️\n\n{error_message}"
        return self.send_message(message)
