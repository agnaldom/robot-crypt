import time
import logging
import sys
from datetime import datetime
from config import CHECK_INTERVAL
from binance_api import BinanceAPI
from listing_detector import ListingDetector
from telegram_notifier import TelegramNotifier
from trading_strategies import TradingStrategy

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Iniciando bot de trading para criptomoedas em lançamento...")
    
    # Inicializar componentes
    binance_api = BinanceAPI()
    telegram_notifier = TelegramNotifier()
    listing_detector = ListingDetector()
    trading_strategy = TradingStrategy(binance_api, telegram_notifier)
    
    # Enviar mensagem inicial
    telegram_notifier.send_message("🤖 Bot de trading iniciado! Monitorando novas listagens...")
    
    try:
        while True:
            logger.info(f"Verificando novas listagens... {datetime.now()}")
            
            # Verificar novas listagens
            new_listings = listing_detector.scan_new_listings()
            
            # Processar novas listagens
            for listing in new_listings:
                logger.info(f"Nova listagem detectada: {listing['symbol']}")
                telegram_notifier.notify_new_listing(listing)
                
                # Iniciar estratégia de trading
                trading_strategy.handle_new_listing(listing)
            
            # Verificar operações ativas
            trading_strategy.check_active_trades()
            
            # Aguardar até a próxima verificação
            logger.info(f"Aguardando {CHECK_INTERVAL} segundos até a próxima verificação...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário.")
        telegram_notifier.send_message("⚠️ Bot interrompido manualmente.")
    except Exception as e:
        logger.error(f"Erro não tratado: {e}", exc_info=True)
        telegram_notifier.notify_error(f"Erro crítico: {str(e)}")
        raise

if __name__ == "__main__":
    main()
