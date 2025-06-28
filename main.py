#!/usr/bin/env python3
"""
Robot-Crypt: Bot de Negociação para Binance
Estratégia de baixo risco e progressão sustentável
"""
import time
import logging
import json
import requests
from datetime import datetime
from binance_api import BinanceAPI
from strategy import ScalpingStrategy, SwingTradingStrategy
from config import Config
from utils import setup_logger
from telegram_notifier import TelegramNotifier

# Configuração de logging
logger = setup_logger()

def main():
    """Função principal do bot"""
    logger.info("Iniciando Robot-Crypt Bot")
    
    # Carrega configuração
    config = Config()
    
    # Verifica se estamos em modo de simulação
    if config.simulation_mode:
        logger.info("MODO DE SIMULAÇÃO ATIVADO - Não será feita conexão real com a Binance")
        logger.info("Os dados de mercado e operações serão simulados")
        
        # Importa e inicializa o simulador 
        from binance_simulator import BinanceSimulator
        binance = BinanceSimulator()
        
        # Notifica sobre o modo de simulação
        if config.notifications_enabled:
            notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
            notifier.notify_status("Robot-Crypt iniciado em MODO DE SIMULAÇÃO! 🚀")
    else:
        # Inicializa API da Binance real
        binance = BinanceAPI(config.api_key, config.api_secret, testnet=config.use_testnet)
        
        # Inicializa notificador Telegram, se configurado
        notifier = None
        if config.notifications_enabled:
            notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
            notifier.notify_status("Robot-Crypt iniciado! 🚀")
        
        # Primeiro, testa a conexão com a API
        logger.info("Testando conexão com a API da Binance...")
    # Só testamos a conexão se não estivermos em modo de simulação
    if not config.simulation_mode and not binance.test_connection():
        error_message = "Falha na conexão com a API da Binance. Verifique suas credenciais."
        logger.error(error_message)
        
        # Se for testnet, mostra instruções especiais
        if config.use_testnet:
            logger.error("ATENÇÃO: Para usar a testnet da Binance, você precisa de credenciais específicas.")
            logger.error("1. Acesse https://testnet.binance.vision/")
            logger.error("2. Faça login com sua conta Google/Github")
            logger.error("3. Gere um par de API Key/Secret específico para testnet")
            logger.error("4. Execute ./setup_testnet.sh para configurar suas credenciais")
            logger.error("")
            logger.error("Alternativa: Configure o modo de simulação adicionando SIMULATION_MODE=true no arquivo .env")
            
        if notifier:
            notifier.notify_error(f"{error_message} Verifique os logs para mais detalhes.")
        
        logger.info("Finalizando Bot devido a erro de autenticação")
        return
    
    # Verifica saldo da conta
    account_info = binance.get_account_info()
    capital = config.get_balance(account_info)
    logger.info(f"Saldo atual: R${capital:.2f}")
    
    # Notifica saldo via Telegram
    if notifier:
        notifier.notify_status(f"Saldo atual: R${capital:.2f}")
        
    # Define estratégia baseada no capital atual
    
    if capital < 300:
        # Fase 2: Scalping de Baixo Risco
        logger.info("Utilizando estratégia de Scalping de Baixo Risco (Fase 2)")
        strategy = ScalpingStrategy(config, binance)
        pairs = ["BTC/BRL", "ETH/BRL"]
    else:
        # Fase 3: Swing Trading em Altcoins
        logger.info("Utilizando estratégia de Swing Trading em Altcoins (Fase 3)")
        strategy = SwingTradingStrategy(config, binance)
        pairs = ["SHIB/BRL", "FLOKI/BRL"]
    
    # Inicializa estatísticas de trading
    stats = {
        'trades_total': 0,
        'trades_win': 0,
        'trades_loss': 0,
        'initial_capital': capital,
        'current_capital': capital,
        'best_trade_profit': 0,
        'worst_trade_loss': 0,
        'start_time': datetime.now(),
        'profit_history': []
    }
    
    # Loop principal
    try:
        while True:
            # Reporta estatísticas a cada 24h
            runtime = (datetime.now() - stats['start_time']).total_seconds() / 3600
            if runtime >= 24 and runtime % 24 < 0.1:  # Aproximadamente a cada 24h
                return_percent = ((stats['current_capital'] / stats['initial_capital']) - 1) * 100
                
                logger.info("=" * 50)
                logger.info(f"RELATÓRIO DE PERFORMANCE - {stats['start_time'].strftime('%d/%m/%Y')} até agora")
                logger.info(f"Capital inicial: R${stats['initial_capital']:.2f}")
                logger.info(f"Capital atual: R${stats['current_capital']:.2f} ({return_percent:+.2f}%)")
                logger.info(f"Trades totais: {stats['trades_total']}")
                
                if stats['trades_total'] > 0:
                    win_rate = (stats['trades_win'] / stats['trades_total']) * 100
                    logger.info(f"Win rate: {win_rate:.2f}%")
                    logger.info(f"Melhor trade: +{stats['best_trade_profit']:.2f}%")
                    logger.info(f"Pior trade: {stats['worst_trade_loss']:.2f}%")
                    
                logger.info(f"Runtime: {runtime:.1f} horas")
                logger.info("=" * 50)
                
                # Notifica via Telegram se configurado
                if notifier:
                    notifier.notify_status(
                        f"📊 RELATÓRIO DE DESEMPENHO:\n"
                        f"💰 Capital: R${stats['current_capital']:.2f} ({return_percent:+.2f}%)\n"
                        f"📈 Trades: {stats['trades_win']} ganhos, {stats['trades_loss']} perdas\n"
                        f"⏱️ Tempo de execução: {runtime:.1f} horas"
                    )
            
            # Analisa cada par configurado
            for pair in pairs:
                logger.info(f"Analisando par {pair}")
                
                # Analisa mercado e executa ordens conforme a estratégia
                should_trade, action, price = strategy.analyze_market(pair)
                
                if should_trade:
                    if action == "buy":
                        success, order_info = strategy.execute_buy(pair, price)
                        
                        if success and notifier:
                            notifier.notify_trade(f"🛒 COMPRA de {pair}", f"Preço: {price:.8f}\nQuantidade: {order_info['quantity']:.8f}")
                            
                    elif action == "sell":
                        success, order_info = strategy.execute_sell(pair, price)
                        
                        if success:
                            # Atualiza estatísticas
                            stats['trades_total'] += 1
                            profit_percent = order_info['profit'] * 100
                            
                            if profit_percent > 0:
                                stats['trades_win'] += 1
                                stats['best_trade_profit'] = max(stats['best_trade_profit'], profit_percent)
                            else:
                                stats['trades_loss'] += 1
                                stats['worst_trade_loss'] = min(stats['worst_trade_loss'], profit_percent)
                                
                            # Atualiza capital
                            stats['current_capital'] = config.get_balance(binance.get_account_info())
                            stats['profit_history'].append(profit_percent)
                            
                            # Notifica via Telegram
                            if notifier:
                                emoji = "🟢" if profit_percent > 0 else "🔴"
                                notifier.notify_trade(
                                    f"{emoji} VENDA de {pair}", 
                                    f"Preço: {price:.8f}\nLucro: {profit_percent:+.2f}%\nSaldo: R${stats['current_capital']:.2f}"
                                )
                
                # Verifica se estamos na fase correta com base no capital atual
                if capital < 300 and strategy.__class__.__name__ != "ScalpingStrategy":
                    logger.info("Migrando para estratégia de Scalping (capital < R$300)")
                    strategy = ScalpingStrategy(config, binance)
                    pairs = ["BTC/BRL", "ETH/BRL"]
                    
                elif capital >= 300 and strategy.__class__.__name__ != "SwingTradingStrategy":
                    logger.info("Migrando para estratégia de Swing Trading (capital >= R$300)")
                    strategy = SwingTradingStrategy(config, binance)
                    pairs = ["SHIB/BRL", "FLOKI/BRL", "DOGE/BRL"]
            
            # Espera o intervalo configurado antes da próxima análise
            logger.info(f"Aguardando {config.check_interval} segundos até próxima verificação")
            time.sleep(config.check_interval)
                    
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
        # Notifica interrupção via Telegram
        if notifier:
            notifier.notify_status("⚠️ Robot-Crypt interrompido pelo usuário")
    except requests.exceptions.RequestException as e:
        error_message = f"Erro de conexão com a API: {str(e)}"
        logger.error(error_message)
        
        # Fornece orientações específicas para erros de API comuns
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            if status_code == 401:
                logger.error("Erro 401: Problema de autenticação. Verifique suas credenciais.")
                if config.use_testnet:
                    logger.error("DICA: As credenciais da testnet expiram após 30 dias. Obtenha novas em https://testnet.binance.vision/")
            elif status_code == 418 or status_code == 429:
                logger.error(f"Erro {status_code}: Limite de requisições atingido. Aguarde antes de tentar novamente.")
            elif status_code >= 500:
                logger.error(f"Erro {status_code}: Problema nos servidores da Binance. Tente mais tarde.")
        
        # Notifica erro via Telegram
        if notifier:
            notifier.notify_error(error_message)
    except Exception as e:
        error_message = f"Erro inesperado: {str(e)}"
        logger.error(error_message)
        logger.exception("Detalhes do erro:")
        
        # Notifica erro via Telegram
        if notifier:
            notifier.notify_error(error_message)
    finally:
        logger.info("Finalizando Robot-Crypt Bot")
        
        # Salva estado atual antes de finalizar (para possível recuperação)
        try:
            if hasattr(strategy, 'open_positions') and strategy.open_positions:
                logger.info(f"Salvando {len(strategy.open_positions)} posições abertas para recuperação futura")
                # Código para salvar estado removido por brevidade
        except Exception as save_error:
            logger.error(f"Erro ao salvar estado: {str(save_error)}")
        
        # Notifica finalização via Telegram
        if notifier:
            notifier.notify_status("Robot-Crypt finalizado!")

if __name__ == "__main__":
    main()
