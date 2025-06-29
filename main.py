#!/usr/bin/env python3
"""
Robot-Crypt: Bot de Negociação para Binance
Estratégia de baixo risco e progressão sustentável
"""
import time
import logging
import json
import requests
from datetime import datetime, timedelta
from binance_api import BinanceAPI
from strategy import ScalpingStrategy, SwingTradingStrategy
from config import Config
from utils import setup_logger, save_state, load_state, filtrar_pares_por_liquidez
from telegram_notifier import TelegramNotifier
from db_manager import DBManager
from pathlib import Path

# Configuração de logging
logger = setup_logger()

def main():
    """Função principal do bot"""
    logger.info("Iniciando Robot-Crypt Bot")
    
    # Verifica e cria diretórios necessários
    for directory in ['data', 'logs', 'reports']:
        dir_path = Path(__file__).parent / directory
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"Diretório {directory} criado com sucesso")
    
    # Carrega configuração
    config = Config()
    
    # Debug para Telegram
    logger.info(f"Telegram Token disponível: {'Sim' if config.telegram_bot_token else 'Não'}")
    logger.info(f"Telegram Chat ID disponível: {'Sim' if config.telegram_chat_id else 'Não'}")
    logger.info(f"Notificações Telegram habilitadas: {'Sim' if config.notifications_enabled else 'Não'}")
    
    # Inicializa banco de dados SQLite
    db = DBManager()
    logger.info("Banco de dados SQLite inicializado com sucesso")
    
    # Inicializa notificador Telegram, se configurado
    notifier = None
    if config.notifications_enabled:
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    
    # Verifica se estamos em modo de simulação
    if config.simulation_mode:
        logger.info("MODO DE SIMULAÇÃO ATIVADO - Não será feita conexão real com a Binance")
        logger.info("Os dados de mercado e operações serão simulados")
        
        # Importa e inicializa o simulador 
        from binance_simulator import BinanceSimulator
        binance = BinanceSimulator()
        
        # Notifica sobre o modo de simulação
        if notifier:
            notifier.notify_status("Robot-Crypt iniciado em MODO DE SIMULAÇÃO! 🚀")
    else:
        # Inicializa API da Binance real
        binance = BinanceAPI(config.api_key, config.api_secret, testnet=config.use_testnet)
        
        # Log sobre o modo de operação
        if config.use_testnet:
            logger.info("MODO TESTNET ATIVADO - Conectando à TestNet da Binance (ambiente de teste)")
            logger.info("Atenção: Nem todos os pares estão disponíveis na TestNet")
        else:
            logger.info("MODO PRODUÇÃO ATIVADO - Conectando à API real da Binance com dinheiro real")
        
        # Notifica sobre o início do bot
        if notifier:
            msg = "Robot-Crypt iniciado em TESTNET! 🚀" if config.use_testnet else "Robot-Crypt iniciado em PRODUÇÃO! 🚀"
            notifier.notify_status(msg)
        
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
    
    # Log detalhado das informações da conta para depuração
    logger.info("Informações detalhadas da conta Binance:")
    if 'balances' in account_info:
        for balance in account_info['balances']:
            asset = balance.get('asset', '')
            free = float(balance.get('free', '0'))
            locked = float(balance.get('locked', '0'))
            total = free + locked
            if total > 0:
                logger.info(f"Moeda: {asset}, Livre: {free}, Bloqueado: {locked}, Total: {total}")
    
    # Obtém o saldo total da conta em BRL/USDT
    capital = config.get_balance(account_info)
    logger.info(f"Saldo total convertido: R${capital:.2f}")
    
    # Notifica saldo via Telegram
    if notifier:
        notifier.notify_status(f"Saldo atual: R${capital:.2f}")
    
    # Inicializa estratégia conforme o saldo disponível
    strategy = None
    pairs = []
    state_save_counter = 0
    start_time = datetime.now()
    
    # Carrega o estado anterior da aplicação
    previous_state = load_state()
    
    # Se não houver estado em arquivo, tenta carregar do banco de dados
    if not previous_state:
        logger.info("Nenhum arquivo de estado encontrado, tentando carregar do banco de dados...")
        previous_state = db.load_last_app_state()
        
        # Se encontrou no banco de dados, salva também como arquivo para compatibilidade
        if previous_state:
            logger.info("Estado carregado do banco de dados com sucesso")
            save_state(previous_state)
            logger.info("Estado migrado do banco de dados para arquivo JSON")
    
    # Inicializa estatísticas
    stats = {}
    
    if previous_state and 'stats' in previous_state:
        logger.info("Estado anterior encontrado. Retomando operação...")
        stats = previous_state['stats']
        
        # Migração de chaves antigas para novas
        # Isso garante compatibilidade com estados salvos antes da atualização
        key_mapping = {
            'trades_total': 'total_trades',
            'trades_win': 'winning_trades',
            'trades_loss': 'losing_trades'
        }
        
        # Migra chaves antigas para novas se necessário
        for old_key, new_key in key_mapping.items():
            if old_key in stats and new_key not in stats:
                logger.info(f"Migrando estatística: {old_key} -> {new_key}")
                stats[new_key] = stats[old_key]
        
        # Garante que todas as chaves estatísticas necessárias existam
        required_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'best_trade_profit': 0,
            'worst_trade_loss': 0,
            'initial_capital': capital,
            'current_capital': capital,
            'profit_history': []
        }
        
        for key, default_value in required_stats.items():
            if key not in stats:
                logger.warning(f"Chave {key} não encontrada nas estatísticas. Criando com valor padrão.")
                stats[key] = default_value
        
        # Converte a string de data de volta para datetime
        if 'start_time' in stats and isinstance(stats['start_time'], str):
            stats['start_time'] = datetime.fromisoformat(stats['start_time'])
        else:
            logger.warning("Chave start_time não encontrada nas estatísticas. Criando com valor atual.")
            stats['start_time'] = datetime.now()
        
        # Obtém hora da última verificação
        if 'last_check_time' in previous_state and isinstance(previous_state['last_check_time'], str):
            last_check_time = datetime.fromisoformat(previous_state['last_check_time'])
        else:
            last_check_time = datetime.now() - timedelta(hours=1)
        
        # Verifica se as posições abertas foram salvas
        if 'open_positions' in previous_state and hasattr(strategy, 'open_positions'):
            # Converte posições abertas de volta para o formato original
            open_positions = {}
            for key, position in previous_state['open_positions'].items():
                # Se a posição tiver um campo 'time' em formato ISO, converta de volta para datetime
                if 'time' in position and isinstance(position['time'], str):
                    position['time'] = datetime.fromisoformat(position['time'])
                open_positions[key] = position
                
            strategy.open_positions = open_positions
            logger.info(f"Carregadas {len(strategy.open_positions)} posições abertas do estado anterior")
        
        # Mantém o capital atual ao invés do salvo
        stats['current_capital'] = capital
        
        # Calcula quanto tempo passou desde o último check
        time_since_last_check = (datetime.now() - last_check_time).total_seconds() / 60  # em minutos
        logger.info(f"Estado anterior carregado - Última verificação: {time_since_last_check:.1f} minutos atrás")
        
        # Notifica retomada via Telegram
        if notifier:
            notifier.notify_status(f"🔄 Robot-Crypt retomando operações!\nÚltima verificação: {time_since_last_check:.1f} minutos atrás")
    else:
        # Inicializa novas estatísticas de trading
        stats = {
            'total_trades': 0,  # Renomeado de trades_total para corresponder ao DB
            'winning_trades': 0,  # Renomeado de trades_win para corresponder ao DB
            'losing_trades': 0,   # Renomeado de trades_loss para corresponder ao DB
            'initial_capital': capital,
            'current_capital': capital,
            'best_trade_profit': 0,
            'worst_trade_loss': 0,
            'start_time': datetime.now(),
            'profit_history': []
        }
        logger.info("Iniciando com novas estatísticas - Nenhum estado anterior encontrado")
    
    # Contador para salvar estado periodicamente
    state_save_counter = 0
    
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
                logger.info(f"Trades totais: {stats['total_trades']}")
                
                if stats['total_trades'] > 0:
                    win_rate = (stats['winning_trades'] / stats['total_trades']) * 100
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
                        f"📈 Trades: {stats['winning_trades']} ganhos, {stats['losing_trades']} perdas\n"
                        f"⏱️ Tempo de execução: {runtime:.1f} horas"
                    )
            
            # Analisa cada par configurado
            for pair in pairs[:]:  # Cria uma cópia para poder modificar a lista durante o loop
                logger.info(f"Analisando par {pair}")
                
                # Envia notificação que iniciou análise deste par
                if notifier:
                    notifier.notify_status(f"🔎 Iniciando análise do par {pair}")
                
                # Tenta analisar o mercado com tratamento de erros específicos
                try:
                    # Analisa mercado e executa ordens conforme a estratégia
                    should_trade, action, price = strategy.analyze_market(pair, notifier=notifier)
                except requests.exceptions.RequestException as e:
                    error_message = f"Erro na análise do par {pair}: {str(e)}"
                    logger.error(error_message)
                    
                    # Se for um erro 400 (Bad Request), provavelmente o par não existe
                    if hasattr(e, 'response') and e.response and e.response.status_code == 400:
                        logger.warning(f"Par {pair} não disponível. Removendo da lista de pares...")
                        pairs.remove(pair)
                        
                        # Notifica via Telegram
                        if notifier:
                            notifier.notify_status(f"⚠️ Par {pair} não está disponível e foi removido da lista")
                    continue  # Pula para o próximo par
                
                if should_trade:
                    if action == "buy":
                        success, order_info = strategy.execute_buy(pair, price)
                        
                        if success and notifier:
                            notifier.notify_trade(f"🛒 COMPRA de {pair}", f"Preço: {price:.8f}\nQuantidade: {order_info['quantity']:.8f}")
                            
                    elif action == "sell":
                        success, order_info = strategy.execute_sell(pair, price)
                        
                        if success:
                            # Atualiza estatísticas
                            stats['total_trades'] += 1
                            profit_percent = order_info['profit'] * 100
                            
                            if profit_percent > 0:
                                stats['winning_trades'] += 1
                                stats['best_trade_profit'] = max(stats['best_trade_profit'], profit_percent)
                            else:
                                stats['losing_trades'] += 1
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
                
                # Atualiza informações da conta para verificar saldos disponíveis
                account_info = binance.get_account_info()
                
                # Atualiza o capital total
                capital = config.get_balance(account_info)
                
                # Verifica saldos das moedas principais
                bnb_balance = 0
                usdt_balance = 0
                brl_balance = 0
                
                for balance in account_info.get('balances', []):
                    asset = balance['asset']
                    free_amount = float(balance['free'])
                    locked_amount = float(balance['locked'])
                    total_amount = free_amount + locked_amount
                    
                    if asset == 'BNB' and total_amount > 0:
                        bnb_balance = total_amount
                    elif asset == 'USDT' and total_amount > 0:
                        usdt_balance = total_amount
                    elif asset == 'BRL' and total_amount > 0:
                        brl_balance = total_amount
                
                logger.info(f"Saldos atualizados - BNB: {bnb_balance:.8f}, USDT: {usdt_balance:.2f}, BRL: {brl_balance:.2f}")
                
                # Verifica se estamos na fase correta com base no capital atual
                if capital < 300 and strategy.__class__.__name__ != "ScalpingStrategy":
                    logger.info("Migrando para estratégia de Scalping (capital < R$300)")
                    strategy = ScalpingStrategy(config, binance)
                    
                    # Define os pares iniciais baseados nos saldos disponíveis
                    pairs = []
                    
                    # Carrega pares de negociação da configuração, se disponível
                    config_pairs = config.trading_pairs if hasattr(config, 'trading_pairs') and config.trading_pairs else []
                    
                    # Se temos configuração explícita de pares, usamos ela
                    if config_pairs:
                        logger.info(f"Usando pares configurados: {config_pairs}")
                        pairs = config_pairs
                    # Caso contrário, definimos pares com base nas moedas disponíveis
                    else:
                        if config.use_testnet:
                            pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
                            logger.info("Usando pares compatíveis com testnet para scalping")
                        else:
                            # Adiciona pares com base nas moedas disponíveis
                            if usdt_balance > 0:
                                pairs.extend(["BTC/USDT", "ETH/USDT", "DOGE/USDT", "SHIB/USDT"])
                                logger.info(f"Adicionando pares USDT para negociação com saldo disponível de {usdt_balance:.2f} USDT")
                                
                            if brl_balance > 0:
                                pairs.extend(["BTC/BRL", "ETH/BRL"])
                                logger.info(f"Adicionando pares BRL para negociação com saldo disponível de {brl_balance:.2f} BRL")
                    
                    # Se tiver saldo de BNB, adiciona pares específicos para negociar BNB
                    if bnb_balance > 0.01:
                        logger.info(f"Adicionando pares de BNB para negociação com saldo disponível de {bnb_balance:.8f} BNB")
                        if usdt_balance > 0:
                            pairs.append("BNB/USDT")
                            
                        if config.use_testnet:
                            pairs.append("BNB/BTC")
                        else:
                            pairs.extend(["BNB/BTC", "BNB/ETH"])
                            if brl_balance > 0:
                                pairs.append("BNB/BRL")
                    
                elif capital >= 300 and strategy.__class__.__name__ != "SwingTradingStrategy":
                    logger.info("Migrando para estratégia de Swing Trading (capital >= R$300)")
                    strategy = SwingTradingStrategy(config, binance)
                    
                    # Define os pares baseados nos saldos disponíveis
                    pairs = []
                    
                    # Carrega pares de negociação da configuração, se disponível
                    config_pairs = config.trading_pairs if hasattr(config, 'trading_pairs') and config.trading_pairs else []
                    
                    # Se temos configuração explícita de pares, usamos ela
                    if config_pairs:
                        logger.info(f"Usando pares configurados: {config_pairs}")
                        pairs = config_pairs
                    # Caso contrário, definimos pares com base nas moedas disponíveis
                    else:
                        if config.use_testnet:
                            pairs = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BNB/USDT"]
                            logger.info("Usando pares compatíveis com testnet para swing trading")
                        else:
                            # Adiciona pares com base nas moedas disponíveis
                            if usdt_balance > 0:
                                pairs.extend(["BTC/USDT", "ETH/USDT", "DOGE/USDT", "SHIB/USDT", "FLOKI/USDT"])
                                logger.info(f"Adicionando pares USDT para negociação com saldo disponível de {usdt_balance:.2f} USDT")
                                
                            if brl_balance > 0:
                                pairs.extend(["SHIB/BRL", "FLOKI/BRL", "DOGE/BRL"])
                                logger.info(f"Adicionando pares BRL para negociação com saldo disponível de {brl_balance:.2f} BRL")
                    
                    # Se tiver saldo de BNB, adiciona pares específicos para negociar BNB
                    if bnb_balance > 0.01:
                        logger.info(f"Adicionando pares de BNB para negociação com saldo disponível de {bnb_balance:.8f} BNB")
                        if usdt_balance > 0:
                            pairs.append("BNB/USDT")
                            
                        if config.use_testnet:
                            pairs.extend(["BNB/BTC", "BNB/ETH"])
                        else:
                            pairs.extend(["BNB/BTC", "BNB/ETH"])
                            if brl_balance > 0:
                                pairs.append("BNB/BRL")
            
            # Incrementa contador de salvamento de estado
            state_save_counter += 1
            
            # Salva o estado a cada ciclo
            if state_save_counter >= 1:
                # Prepara o estado para ser salvo
                state_to_save = {
                    'stats': {
                        # Verifica se todas as chaves necessárias existem antes de salvar
                        'total_trades': stats.get('total_trades', 0),
                        'winning_trades': stats.get('winning_trades', 0),
                        'losing_trades': stats.get('losing_trades', 0),
                        'initial_capital': stats.get('initial_capital', config.get_balance(account_info)),
                        'current_capital': stats.get('current_capital', config.get_balance(account_info)),
                        'best_trade_profit': stats.get('best_trade_profit', 0),
                        'worst_trade_loss': stats.get('worst_trade_loss', 0),
                        'start_time': stats.get('start_time', datetime.now()).isoformat() if isinstance(stats.get('start_time', datetime.now()), datetime) else stats.get('start_time', datetime.now().isoformat()),
                        'profit_history': stats.get('profit_history', [])
                    },
                    'last_check_time': datetime.now().isoformat(),
                    'strategy_type': strategy.__class__.__name__,
                    'pairs': pairs
                }
                
                # Adiciona posições abertas se disponíveis
                if hasattr(strategy, 'open_positions'):
                    # Conversão de posições abertas para formato serializável
                    open_positions_serialized = {}
                    for key, position in strategy.open_positions.items():
                        # Se a posição tiver um campo 'time', converta de datetime para string
                        pos_copy = position.copy()
                        if 'time' in pos_copy and isinstance(pos_copy['time'], datetime):
                            pos_copy['time'] = pos_copy['time'].isoformat()
                        open_positions_serialized[key] = pos_copy
                    
                    state_to_save['open_positions'] = open_positions_serialized
                
                # Salva o estado no arquivo JSON (legado) e no banco de dados
                save_state(state_to_save)
                db.save_app_state(state_to_save)
                
                # Atualiza estatísticas diárias no banco de dados
                db.update_daily_stats(stats)
            
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
            # Prepara o estado para ser salvo
            state_to_save = {
                'stats': {
                    # Verifica se todas as chaves necessárias existem antes de salvar
                    'total_trades': stats.get('total_trades', 0),
                    'winning_trades': stats.get('winning_trades', 0),
                    'losing_trades': stats.get('losing_trades', 0),
                    'initial_capital': stats.get('initial_capital', 100.0),
                    'current_capital': stats.get('current_capital', 100.0),
                    'best_trade_profit': stats.get('best_trade_profit', 0),
                    'worst_trade_loss': stats.get('worst_trade_loss', 0),
                    'start_time': stats.get('start_time', datetime.now()).isoformat() if isinstance(stats.get('start_time', datetime.now()), datetime) else stats.get('start_time', datetime.now().isoformat()),
                    'profit_history': stats.get('profit_history', [])
                },
                'last_check_time': datetime.now().isoformat(),
                'strategy_type': getattr(strategy, '__class__', type(None)).__name__ if strategy else 'None',
                'pairs': pairs or []
            }
            
            # Adiciona posições abertas se disponíveis
            if hasattr(strategy, 'open_positions') and strategy.open_positions:
                # Conversão de posições abertas para formato serializável, se necessário
                open_positions_serialized = {}
                for key, position in strategy.open_positions.items():
                    # Se a posição tiver um campo 'time', converta de datetime para string
                    pos_copy = position.copy()
                    if 'time' in pos_copy and isinstance(pos_copy['time'], datetime):
                        pos_copy['time'] = pos_copy['time'].isoformat()
                    open_positions_serialized[key] = pos_copy
                
                state_to_save['open_positions'] = open_positions_serialized
                logger.info(f"Salvando {len(strategy.open_positions)} posições abertas para recuperação futura")
            
            # Salva o estado
            save_success = save_state(state_to_save, "app_state_final.json")
            if save_success:
                logger.info("Estado final salvo com sucesso para recuperação futura")
        
        except Exception as save_error:
            logger.error(f"Erro ao salvar estado: {str(save_error)}")
        
        # Notifica finalização via Telegram
        if notifier:
            notifier.notify_status("Robot-Crypt finalizado!")

if __name__ == "__main__":
    main()
