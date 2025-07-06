#!/usr/bin/env python3
"""
Robot-Crypt: Bot de Negociação para Binance
Estratégia de baixo risco e progressão sustentável
"""
import time
import logging
from logging.handlers import RotatingFileHandler
import json
import requests
import signal
import sys
import os
import threading
import psutil
import gc
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
if __name__ == '__main__':
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    sys.path.insert(0, str(project_root))

from src.tools.health_monitor import check_system_health, log_process_tree

# Importações do pacote src
from src import (
    Config, BinanceAPI, ScalpingStrategy, SwingTradingStrategy,
    setup_logger, save_state, load_state, filtrar_pares_por_liquidez,
    TelegramNotifier, DBManager, PostgresManager,
    ExternalDataAnalyzer, AdaptiveRiskManager, WalletManager
)
# Dashboard será implementado como um projeto separado
# from dashboard import RobotCryptDashboard

# Configure logging
def setup_logging(log_level=logging.INFO):
    """Configura o sistema de logging"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'robot-crypt-{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configura o handler de arquivo
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    
    # Configura o handler de console
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formata as mensagens de log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

# Inicializa componentes
def init_components():
    """Inicializa os componentes do robô"""
    components = {}
    
    # Inicializa o analisador contextual
    from src.api.external.news_api_client import NewsAPIClient
    from src.analysis.news_analyzer import NewsAnalyzer
    news_client = NewsAPIClient()
    components['news_analyzer'] = NewsAnalyzer(news_client)
    
    # Inicializa o gerenciador de risco adaptativo
    from risk_management.adaptive_risk import AdaptiveRiskManager
    components['risk_manager'] = AdaptiveRiskManager()
    
    return components

# Dashboard removido - será implementado como um projeto separado

# Configuração de logging
logger = setup_logger()

# Variáveis globais para controle de sinal
SHOULD_EXIT = False
DASHBOARD_INSTANCE = None  # Para armazenar a instância do dashboard
BINANCE_INSTANCE = None    # Para armazenar a instância da API Binance

# Função para tratamento de sinais
def signal_handler(sig, frame):
    global SHOULD_EXIT
    logger.info(f"Sinal {sig} recebido, preparando para encerramento gracioso...")
    SHOULD_EXIT = True
    
    # Para o caso de SIGINT (Ctrl+C), damos 5 segundos para o encerramento e saímos
    if sig == signal.SIGINT:
        logger.info("Ctrl+C pressionado. Aguardando 5 segundos para operações de limpeza...")
        import threading
        timer = threading.Timer(5.0, lambda: sys.exit(0))
        timer.daemon = True
        timer.start()

# Registra handlers para sinais
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def check_postgres_requirements():
    """Verifica se os requisitos para o PostgreSQL estão disponíveis"""
    try:
        import psycopg2
        from psycopg2.extras import Json
        logger.info("Requisitos para PostgreSQL estão disponíveis")
        return True
    except ImportError:
        logger.warning("Pacote psycopg2 não encontrado. Algumas funcionalidades de banco de dados não estarão disponíveis.")
        logger.info("Para habilitar armazenamento PostgreSQL, instale: pip install psycopg2-binary")
        return False

def initialize_resources():
    """Inicializa recursos básicos do sistema"""
    logger.info("Iniciando inicialização do Robot-Crypt")
    
    # Verifica e cria diretórios necessários
    for directory in ['data', 'logs', 'reports', 'assets']:
        dir_path = Path(__file__).parent / directory
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"Diretório {directory} criado com sucesso")
    
    # Verifica requisitos para PostgreSQL
    postgres_available = check_postgres_requirements()
    
    # Carrega configuração
    config = Config()
    
    # Debug para Telegram
    logger.info(f"Telegram Token disponível: {'Sim' if config.telegram_bot_token else 'Não'}")
    logger.info(f"Telegram Chat ID disponível: {'Sim' if config.telegram_chat_id else 'Não'}")
    logger.info(f"Notificações Telegram habilitadas: {'Sim' if config.notifications_enabled else 'Não'}")
    
    # Inicializa banco de dados PostgreSQL para todos os dados
    try:
        pg_db = PostgresManager()
        # Testa a conexão explicitamente para garantir que funcione
        if pg_db._check_and_reconnect():
            logger.info("Banco de dados PostgreSQL inicializado com sucesso")
            # Usamos pg_db como o banco de dados principal
            db = pg_db
        else:
            raise Exception("Não foi possível estabelecer conexão com PostgreSQL")
    except Exception as e:
        logger.error(f"Erro ao inicializar PostgreSQL: {str(e)}")
        logger.warning("Tentando inicializar SQLite como backup...")
        # Inicializa banco de dados SQLite como fallback
        db = DBManager()
        logger.info("Banco de dados SQLite inicializado como fallback")
        pg_db = None
    
    # Inicializa analisador de dados externos
    try:
        external_data = ExternalDataAnalyzer(config)
        logger.info("Analisador de dados externos inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar analisador de dados externos: {str(e)}")
        external_data = None
    
    # Inicializa analisador de notícias (para análise contextual)
    try:
        from analysis.news_analyzer import NewsAnalyzer
        from api.external.news_api_client import NewsAPIClient
        news_client = NewsAPIClient()
        news_analyzer = NewsAnalyzer(news_client)
        logger.info("Analisador de notícias inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar analisador de notícias: {str(e)}")
        logger.info("Continuando sem análise de notícias")
        news_analyzer = None
        
    # Inicializa analisador de contexto avançado
    context_analyzer = None
    try:
        from contextual_analysis.advanced_context_analyzer import AdvancedContextAnalyzer
        context_analyzer = AdvancedContextAnalyzer(config=config, news_analyzer=news_analyzer)
        logger.info("Analisador de contexto avançado inicializado com sucesso")
    except ImportError as ie:
        logger.warning(f"Não foi possível importar AdvancedContextAnalyzer: {str(ie)}")
        logger.info("Continuando sem análise de contexto avançada")
    except Exception as e:
        logger.error(f"Erro ao inicializar analisador de contexto avançado: {str(e)}")
        logger.info("Continuando sem análise de contexto avançada")
    
    # Inicializa gerenciador de risco adaptativo com análise contextual
    try:
        risk_manager = AdaptiveRiskManager(db, config, context_analyzer, news_analyzer)
        logger.info("Gerenciador de risco adaptativo inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar gerenciador de risco adaptativo: {str(e)}")
        risk_manager = None
    
    # Inicializa dashboard se as dependências estiverem disponíveis
    global DASHBOARD_INSTANCE
    try:
        # Dashboard comentado pois será implementado como um projeto separado
        logger.info("Dashboard está desativado - será implementado como um projeto separado")
        DASHBOARD_INSTANCE = None
        
        # Código do dashboard comentado
        """
        # Tenta aplicar o patch para o Dash primeiro
        try:
            import dash_patch
            logger.info("Patch aplicado ao Dash para compatibilidade com Flask 2.0+")
        except Exception as patch_error:
            logger.warning(f"Erro ao aplicar patch ao Dash: {patch_error}")
        
        dashboard_port = int(os.environ.get("DASHBOARD_PORT", "8050"))
        dashboard = RobotCryptDashboard(db, config, port=dashboard_port, external_data=external_data)
        
        # Verifica se o dashboard está realmente disponível (para a classe substituta)
        if hasattr(dashboard, 'available') and dashboard.available is False:
            logger.warning("Dashboard não disponível devido à falta de dependências.")
            DASHBOARD_INSTANCE = None
        else:
            dashboard.start()
            DASHBOARD_INSTANCE = dashboard
            logger.info(f"Dashboard inicializado com sucesso na porta {dashboard_port}")
        """
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários para o dashboard: {str(e)}")
        logger.warning("Para habilitar o dashboard, instale as dependências com: pip install dash plotly")
        DASHBOARD_INSTANCE = None
    except Exception as e:
        logger.error(f"Erro ao inicializar dashboard: {str(e)}")
        DASHBOARD_INSTANCE = None
    
    # Inicializa notificador Telegram, se configurado
    notifier = None
    if config.notifications_enabled:
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    
    # Inicializa conexão com Binance
    global BINANCE_INSTANCE  # Para permitir que o dashboard acesse a mesma instância
    
    if config.simulation_mode:
        logger.info("MODO DE SIMULAÇÃO ATIVADO - Não será feita conexão real com a Binance")
        logger.info("Os dados de mercado e operações serão simulados")
        
        # Importa e inicializa o simulador 
        from binance_simulator import BinanceSimulator
        binance = BinanceSimulator()
        BINANCE_INSTANCE = binance  # Armazena globalmente para o dashboard
        
        # Notifica sobre o modo de simulação
        if notifier:
            notifier.notify_status("🔄 Robot-Crypt iniciado em MODO DE SIMULAÇÃO!")
    else:
        # Inicializa conexão real com a Binance
        logger.info("Conectando à API da Binance...")
        
        if config.use_testnet:
            logger.info("Usando Binance Testnet (ambiente de testes)")
            if notifier:
                notifier.notify_status("🔄 Robot-Crypt iniciado em MODO TESTNET!")
        else:
            logger.info("Conectando a Binance em modo de PRODUÇÃO!")
            logger.info("!!! ATENÇÃO !!! Operações com dinheiro real serão executadas!")
            if notifier:
                notifier.notify_status("⚠️ Robot-Crypt iniciado em MODO DE PRODUÇÃO!")
                
        # Inicializa API da Binance
        binance = BinanceAPI(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.use_testnet
        )
        BINANCE_INSTANCE = binance  # Armazena globalmente para o dashboard
        
        # Testa conexão
        logger.info("Testando conexão com a API da Binance...")
        connection_status = binance.test_connection()
        if connection_status:
            logger.info("Conexão com a Binance estabelecida com sucesso")
        else:
            logger.error("Falha ao conectar à API da Binance. Encerrando.")
            if notifier:
                notifier.notify_alert("❌ FALHA DE CONEXÃO com a Binance. Robot-Crypt não iniciado!")
            BINANCE_INSTANCE = None  # Limpa instância global
            return None, None, None, None

    logger.info("Inicialização concluída com sucesso")
    
    # Pausa para garantir que o container esteja estável
    logger.info("Aguardando 10 segundos antes de iniciar operações...")
    for i in range(10, 0, -1):
        if SHOULD_EXIT:
            logger.info("Encerramento solicitado durante a inicialização")
            return None, None, None, None
        logger.info(f"Iniciando operações em {i} segundos...")
        time.sleep(1)
    
    return config, binance, notifier, db

# A função check_system_health foi movida para o módulo health_monitor.py
# para eliminar duplicação e garantir consistência

def initialize_wallet_manager(binance, db, user_id="default_user"):
    """
    Inicializa o gerenciador de carteira e sincroniza os dados
    
    Args:
        binance (BinanceAPI): Instância da API da Binance
        db (PostgresManager): Instância do gerenciador de PostgreSQL
        user_id (str): ID do usuário para associar aos dados da carteira
        
    Returns:
        WalletManager: Instância do gerenciador de carteira
    """
    try:
        logger.info("Inicializando gerenciador de carteira...")
        wallet_manager = WalletManager(binance_api=binance, postgres_manager=db)
        
        # Sincroniza dados da carteira
        logger.info(f"Sincronizando dados da carteira para usuário {user_id}")
        wallet_data = wallet_manager.get_wallet_balance(user_id)
        
        if wallet_data:
            logger.info(f"Carteira sincronizada! Saldo total: {wallet_data['total_usdt_value']:.2f} USDT")
            logger.info(f"Ativos encontrados: {len(wallet_data['balances'])}")
            
            # Ordenar por valor USDT (do maior para o menor)
            sorted_assets = sorted(wallet_data['balances'], key=lambda x: x['usdt_value'], reverse=True)
            
            # Mostrar apenas os 5 principais ativos para não poluir o log
            top_assets = sorted_assets[:5]
            for asset in top_assets:
                logger.info(f"  {asset['asset']}: {asset['total']} ({asset['usdt_value']:.2f} USDT)")
                
            if len(sorted_assets) > 5:
                logger.info(f"  ... e mais {len(sorted_assets) - 5} outros ativos")
        else:
            logger.warning("Não foi possível sincronizar os dados da carteira")
            
        return wallet_manager
            
    except Exception as e:
        logger.error(f"Erro ao inicializar gerenciador de carteira: {str(e)}")
        return None

def main():
    """Função principal do bot"""
    logger.info("Iniciando Robot-Crypt Bot")
    
    # Fase de inicialização - estabelece conexões e prepara recursos
    config, binance, notifier, db = initialize_resources()
    
    # Verifica se a inicialização foi bem-sucedida
    if not config or not binance:
        logger.error("Falha na inicialização dos recursos necessários. Encerrando.")
        return
        
    # Verifica se o sinal de saída foi acionado durante a inicialização
    if SHOULD_EXIT:
        logger.info("Sinal de encerramento recebido durante a inicialização. Encerrando.")
        return
    
    # Inicializa o gerenciador de carteira com tratamento de erro robusto
    user_id = os.environ.get("WALLET_USER_ID", "default_user")
    wallet_manager = None
    
    try:
        wallet_manager = initialize_wallet_manager(binance, db, user_id)
        if wallet_manager:
            logger.info("Gerenciador de carteira inicializado com sucesso")
        else:
            logger.warning("Gerenciador de carteira retornou None - continuando sem sincronização")
    except Exception as wallet_error:
        logger.error(f"Erro ao inicializar gerenciador de carteira: {str(wallet_error)}")
        logger.info("Continuando execução sem sincronização de carteira")
        wallet_manager = None
        
    # A partir daqui, é o código original do main.py
    
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
    try:
        max_retries = 3
        retry_count = 0
        account_info = None
        
        # Implementa lógica de retry para lidar com timeouts
        while retry_count < max_retries:
            try:
                logger.info(f"Tentando obter informações da conta (tentativa {retry_count + 1}/{max_retries})...")
                account_info = binance.get_account_info()
                break  # Se bem-sucedido, sai do loop
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # Espera progressivamente mais tempo
                    logger.warning(f"Erro de conexão: {str(e)}. Tentando novamente em {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Falha após {max_retries} tentativas. Usando dados padrão.")
                    # Cria uma estrutura mínima para permitir que o programa continue
                    account_info = {"balances": []}
        
        # Log detalhado das informações da conta para depuração
        logger.info("Informações detalhadas da conta Binance:")
        if 'balances' in account_info and account_info['balances']:
            for balance in account_info['balances']:
                try:
                    asset = balance.get('asset', '')
                    free = float(balance.get('free', '0'))
                    locked = float(balance.get('locked', '0'))
                    total = free + locked
                    if total > 0:
                        logger.info(f"Moeda: {asset}, Livre: {free}, Bloqueado: {locked}, Total: {total}")
                except Exception as e:
                    logger.error(f"Erro ao processar saldo da moeda: {str(e)}")
        else:
            logger.warning("Dados da conta vazios ou não contêm o campo 'balances' com valores. Usando saldo padrão.")
            # Não mostra a estrutura JSON para evitar erro se account_info for None
        
        # Obtém o saldo total da conta em BRL/USDT ou usa valor padrão
        logger.info("Calculando saldo total convertido...")
        try:
            # Tenta obter o saldo real
            capital = config.get_balance(account_info) if account_info else 100.0
        except Exception:
            # Se falhar por qualquer motivo, usa valor padrão
            logger.warning("Erro ao calcular saldo. Usando valor padrão.")
            capital = 100.0
            
        logger.info(f"Saldo total convertido: R${capital:.2f}")
        
        # Notifica saldo via Telegram
        if notifier:
            try:
                notifier.notify_status(f"Saldo atual: R${capital:.2f}")
            except Exception as notify_error:
                logger.error(f"Erro ao enviar notificação sobre saldo: {str(notify_error)}")
                
    except Exception as e:
        logger.error(f"Erro ao obter informações da conta: {str(e)}")
        logger.error("Usando valor padrão para o capital")
        capital = 100.0
    
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
        
        # Se encontrou no banco de dados, apenas log
        if previous_state:
            logger.info("Estado carregado do banco de dados com sucesso")
    
    # Inicializa estatísticas
    stats = {}
    
    # Define a estratégia inicial e os pares com base no capital
    logger.info(f"Inicializando estratégia com capital de R${capital:.2f}")
    
    # Se temos configuração explícita de pares, usamos ela como base
    config_pairs = getattr(config, 'trading_pairs', [])
    if config_pairs:
        logger.info(f"Usando pares configurados: {config_pairs}")
        pairs = config_pairs
    
    # Importa estratégias aprimoradas
    try:
        from strategies.enhanced_strategy import create_enhanced_strategy
        use_enhanced_strategies = True
        logger.info("Estratégias aprimoradas com IA disponíveis")
    except ImportError as e:
        logger.warning(f"Estratégias aprimoradas não disponíveis: {str(e)}")
        logger.info("Usando estratégias tradicionais como fallback")
        use_enhanced_strategies = False
    
    # Seleciona estratégia baseada no capital
    if capital < 300:
        logger.info("Inicializando com estratégia de Scalping (capital < R$300)")
        
        if use_enhanced_strategies:
            try:
                strategy = create_enhanced_strategy('scalping', config, binance)
                logger.info("✅ Estratégia de Scalping APRIMORADA com IA inicializada")
            except Exception as e:
                logger.error(f"Erro ao criar estratégia aprimorada: {str(e)}")
                strategy = ScalpingStrategy(config, binance)
                logger.info("Usando estratégia de Scalping tradicional como fallback")
        else:
            strategy = ScalpingStrategy(config, binance)
        
        # Define pares padrão para Scalping se não tiver configuração explícita
        if not pairs:
            if config.use_testnet:
                pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
                logger.info("Usando pares padrão compatíveis com testnet para scalping")
            else:
                pairs = ["BTC/USDT", "ETH/USDT", "DOGE/USDT", "SHIB/USDT"]
                logger.info("Usando pares padrão para scalping")
    else:
        logger.info("Inicializando com estratégia de Swing Trading (capital >= R$300)")
        
        if use_enhanced_strategies:
            try:
                strategy = create_enhanced_strategy('swing', config, binance)
                logger.info("✅ Estratégia de Swing Trading APRIMORADA com IA inicializada")
            except Exception as e:
                logger.error(f"Erro ao criar estratégia aprimorada: {str(e)}")
                strategy = SwingTradingStrategy(config, binance)
                logger.info("Usando estratégia de Swing Trading tradicional como fallback")
        else:
            strategy = SwingTradingStrategy(config, binance)
        
        # Define pares padrão para Swing Trading se não tiver configuração explícita
        if not pairs:
            if config.use_testnet:
                pairs = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BNB/USDT"] 
                logger.info("Usando pares padrão compatíveis com testnet para swing trading")
            else:
                pairs = ["BTC/USDT", "ETH/USDT", "DOGE/USDT", "SHIB/USDT", "FLOKI/USDT"]
                # Remova ETH/BNB especificamente pois sabemos que causa erro
                if "ETH/BNB" in pairs:
                    pairs.remove("ETH/BNB")
                    logger.info("Removendo ETH/BNB pois causa erro na API")
                logger.info("Usando pares padrão para swing trading")
    
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
    
    # Variável para controlar tentativas e recuperação
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    # Loop principal
    try:
        while True:
            try:
                # Verifica se devemos encerrar o programa
                if SHOULD_EXIT:
                    logger.info("Sinal de encerramento detectado no loop principal. Preparando para sair...")
                    break
                
                # Bloco para relatório de performance
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
            except Exception as e:
                logger.error(f"Erro ao gerar relatório de desempenho: {str(e)}")
                logger.exception("Detalhes do erro:")
            
            # Início do bloco principal de execução
            # Sem bloco try aqui para evitar problemas com exceções não tratadas
            if not pairs:
                logger.warning("Nenhum par de trading disponível para análise!")
                
                # Tenta definir alguns pares padrão se não houver nenhum
                if config.use_testnet:
                    pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
                    logger.info("Definindo pares padrão para testnet: " + ", ".join(pairs))
                else:
                    pairs = ["BTC/USDT", "ETH/USDT", "DOGE/USDT", "SHIB/USDT"]
                    logger.info("Definindo pares padrão para produção: " + ", ".join(pairs))
                
                # Notifica via Telegram
                if notifier:
                    notifier.notify_status(f"⚠️ Nenhum par de trading encontrado. Definidos pares padrão: {', '.join(pairs)}")
            
            # Verifica se a estratégia foi inicializada
            if strategy is None:
                logger.warning("Estratégia não inicializada! Inicializando com base no capital...")
                
                # Inicializa a estratégia com base no capital
                if capital < 300:
                    logger.info("Inicializando estratégia de Scalping devido ao capital baixo")
                    strategy = ScalpingStrategy(config, binance)
                else:
                    logger.info("Inicializando estratégia de Swing Trading")
                    strategy = SwingTradingStrategy(config, binance)
                
                # Notifica via Telegram
                if notifier:
                    strategy_name = "Scalping" if capital < 300 else "Swing Trading"
                    notifier.notify_status(f"⚙️ Inicializando estratégia de {strategy_name}")
            
            # Analisa cada par configurado
            # Primeiro verifica e remove pares problemáticos conhecidos
            problematic_pairs = ["ETH/BNB"]
            for prob_pair in problematic_pairs:
                if prob_pair in pairs:
                    logger.warning(f"Removendo par problemático conhecido: {prob_pair}")
                    pairs.remove(prob_pair)
                    # Notifica via Telegram
                    if notifier:
                        notifier.notify_status(f"⚠️ Par {prob_pair} é conhecido por causar problemas e foi removido da lista")

            # Registra o horário de início da análise atual
            analysis_start_time = datetime.now()
            logger.info(f"==================== INICIANDO CICLO DE ANÁLISE ====================")
            logger.info(f"Iniciando ciclo de análise de mercado às {analysis_start_time.strftime('%H:%M:%S')}")
            logger.info(f"Número de pares a analisar: {len(pairs)}")
            logger.info(f"Pares para análise: {', '.join(pairs)}")
            
            # Identifica se está usando estratégias aprimoradas
            strategy_type = strategy.__class__.__name__
            if 'Enhanced' in strategy_type:
                ai_status = "✅ IA ATIVA" if hasattr(strategy, 'analysis_enabled') and strategy.analysis_enabled else "⚠️ IA INATIVA"
                logger.info(f"🤖 Usando estratégia aprimorada: {strategy_type} ({ai_status})")
            else:
                logger.info(f"📊 Usando estratégia tradicional: {strategy_type}")
            
            # Analisa cada par em sequência
            pair_count = 0
            for pair in pairs[:]:  # Cria uma cópia para poder modificar a lista durante o loop
                pair_count += 1
                logger.info(f"Analisando par {pair} ({pair_count}/{len(pairs)})")
                
                # Tenta analisar o mercado com tratamento de erros específicos
                try:
                    # Verifica se a estratégia tem o método necessário
                    if not hasattr(strategy, 'analyze_market') or not callable(getattr(strategy, 'analyze_market')):
                        logger.error(f"Estratégia não tem método 'analyze_market'. Tipo: {type(strategy)}")
                        continue
                    
                    # Registra início da análise deste par específico
                    pair_analysis_start = datetime.now()
                    
                    # Analisa mercado e executa ordens conforme a estratégia
                    should_trade, action, price = strategy.analyze_market(pair, notifier=notifier)
                    
                    # Registra resultado da análise
                    pair_analysis_duration = (datetime.now() - pair_analysis_start).total_seconds()
                    logger.info(f"Análise de {pair} concluída em {pair_analysis_duration:.2f}s - Resultado: {action if should_trade else 'sem ação'}")
                    
                    if should_trade:
                        logger.info(f"Sinal de {action.upper()} detectado para {pair} a {price:.8f}")
                        if action == "buy":
                            success, order_info = strategy.execute_buy(pair, price)
                            
                            if success:
                                logger.info(f"COMPRA de {pair} executada com sucesso: {order_info}")
                                if notifier:
                                    notifier.notify_trade(f"🛒 COMPRA de {pair}", f"Preço: {price:.8f}\nQuantidade: {order_info['quantity']:.8f}")
                                
                        elif action == "sell":
                            success, order_info = strategy.execute_sell(pair, price)
                            
                            if success:
                                logger.info(f"VENDA de {pair} executada com sucesso: {order_info}")
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
                                current_balance = config.get_balance(binance.get_account_info())
                                stats['current_capital'] = current_balance
                                stats['profit_history'].append(profit_percent)
                                
                                # Registra transação no PostgreSQL se disponível
                                if pg_db:
                                    try:
                                        # Estrutura os dados da transação
                                        transaction_data = {
                                            'symbol': pair,
                                            'operation_type': 'sell',
                                            'entry_price': float(order_info.get('entry_price', 0)),
                                            'exit_price': float(price),
                                            'quantity': float(order_info.get('quantity', 0)),
                                            'profit_loss': float(order_info.get('profit_amount', 0)),
                                            'profit_loss_percentage': profit_percent,
                                            'entry_time': order_info.get('entry_time', datetime.now() - timedelta(minutes=60)),
                                            'exit_time': datetime.now(),
                                            'strategy_used': strategy.__class__.__name__,
                                            'strategy_type': 'Scalping' if isinstance(strategy, ScalpingStrategy) else 'Swing Trading',
                                            'balance_before': float(order_info.get('balance_before', stats['current_capital'] - order_info.get('profit_amount', 0))),
                                            'balance_after': float(stats['current_capital'])
                                        }
                                        
                                        # Registra a transação
                                        tx_id = pg_db.record_transaction(transaction_data)
                                        
                                        # Registra atualização de capital
                                        if tx_id:
                                            logger.info(f"Transação registrada no PostgreSQL com ID: {tx_id}")
                                            pg_db.save_capital_update(
                                                balance=stats['current_capital'],
                                                change_amount=order_info.get('profit_amount', 0),
                                                change_percentage=profit_percent,
                                                trade_id=tx_id,
                                                event_type='sell',
                                                notes=f"Venda de {pair} com {profit_percent:+.2f}% de lucro/prejuízo"
                                            )
                                            
                                            # Calcular métricas de performance diárias
                                            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                                            yesterday = today - timedelta(days=1)
                                            pg_db.calculate_performance_metrics('daily', yesterday, today)
                                    except Exception as pg_error:
                                        logger.error(f"Erro ao registrar transação no PostgreSQL: {str(pg_error)}")
                                
                                # Notifica via Telegram
                                if notifier:
                                    emoji = "🟢" if profit_percent > 0 else "🔴"
                                    notifier.notify_trade(
                                        f"{emoji} VENDA de {pair}", 
                                        f"Preço: {price:.8f}\nLucro: {profit_percent:+.2f}%\nSaldo: R${stats['current_capital']:.2f}"
                                    )
                
                except requests.exceptions.RequestException as e:
                    error_message = f"Erro na análise do par {pair}: {str(e)}"
                    logger.error(error_message)
                    
                    # Se for um erro 400 (Bad Request), provavelmente o par não existe
                    if hasattr(e, 'response') and e.response and e.response.status_code == 400:
                        logger.warning(f"Par {pair} não disponível. Removendo da lista de pares...")
                        
                        # Tenta remover o par da lista com segurança
                        try:
                            pairs.remove(pair)
                        except ValueError:
                            logger.warning(f"Par {pair} já foi removido da lista")
                        
                        # Notifica via Telegram
                        if notifier:
                            notifier.notify_status(f"⚠️ Par {pair} não está disponível e foi removido da lista")
                            
                        # Verifica se é um par BNB e sugere inverter a ordem se for o caso
                        if '/BNB' in pair:
                            inverted_pair = f"BNB/{pair.split('/')[0]}"
                            logger.info(f"Tentando par invertido {inverted_pair} como alternativa...")
                            
                            # Notifica via Telegram sobre a tentativa de par invertido
                            if notifier:
                                notifier.notify_status(f"🔄 Tentando par invertido {inverted_pair} como alternativa")
                    continue  # Pula para o próximo par
                except Exception as e:
                    logger.error(f"Erro inesperado ao analisar par {pair}: {str(e)}")
                    logger.exception("Detalhes do erro:")
                    continue  # Pula para o próximo par
                
                # Pequena pausa entre análises para não sobrecarregar a API
                time.sleep(0.5)
            
            # Registra o fim da análise
            analysis_end_time = datetime.now()
            analysis_duration = (analysis_end_time - analysis_start_time).total_seconds()
            
            # Logs detalhados sobre a conclusão da análise
            logger.info(f"==================== CICLO DE ANÁLISE CONCLUÍDO ====================")
            logger.info(f"Ciclo de análise de mercado concluído em {analysis_duration:.2f} segundos")
            
            # Registra média de tempo por par
            if len(pairs) > 0:
                avg_time_per_pair = analysis_duration / len(pairs)
                logger.info(f"Tempo médio por par analisado: {avg_time_per_pair:.2f} segundos")
            
            # Calcula próximo ciclo de análise previsto
            next_analysis_time = datetime.now() + timedelta(seconds=config.check_interval)
            logger.info(f"Próximo ciclo de análise previsto para: {next_analysis_time.strftime('%H:%M:%S')} (em {config.check_interval} segundos)")
            
            # Incrementa contador de salvamento de estado
            state_save_counter += 1
            
            # Salva o estado a cada ciclo
            if state_save_counter >= 1:
                try:
                    # Verifica a saúde do sistema a cada 5 ciclos
                    if state_save_counter % 5 == 0:
                        logger.info("Executando verificação de saúde do sistema...")
                        # Usando a função importada de health_monitor
                        health_metrics = check_system_health()
                        if health_metrics and health_metrics.get('memory_percent', 0) > 80:
                            logger.warning(f"Uso de memória elevado: {health_metrics['memory_percent']}% - Coletando lixo")
                            gc.collect()
                    
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
                    # Salva o estado no banco de dados
                    save_success = db.save_app_state(state_to_save)
                    
                    # Verifica se estamos usando PostgreSQL e se é necessário fazer fallback para SQLite
                    if not save_success and pg_db and hasattr(pg_db, 'should_use_fallback'):
                        if pg_db.should_use_fallback():
                            logger.warning("Problemas persistentes com PostgreSQL detectados. Migrando para SQLite.")
                            # Inicializa SQLite como fallback
                            backup_db = DBManager()
                            # Salva o estado no SQLite
                            backup_db.save_app_state(state_to_save)
                            # Substitui o banco de dados principal
                            db = backup_db
                            pg_db = None
                            logger.info("Migração para SQLite concluída. Dados serão persistidos localmente.")
                            if notifier:
                                notifier.notify_status("⚠️ Problemas com banco de dados PostgreSQL detectados. Migrado para SQLite local.")
                    else:
                        logger.info("Estado salvo no banco de dados")
                    
                    # Atualiza estatísticas diárias no banco de dados se o método existir
                    if hasattr(db, 'update_daily_stats') and callable(getattr(db, 'update_daily_stats')):
                        try:
                            db.update_daily_stats(stats)
                        except Exception as stats_error:
                            logger.error(f"Erro ao atualizar estatísticas diárias: {str(stats_error)}")
                    else:
                        logger.warning("Método update_daily_stats não disponível no banco de dados atual")
                    if hasattr(db, 'update_daily_stats') and callable(getattr(db, 'update_daily_stats')):
                        db.update_daily_stats(stats)
                    else:
                        logger.warning("Método update_daily_stats não disponível no banco de dados atual")
                
                    # Resetamos contador de erros consecutivos quando completamos um ciclo com sucesso
                    consecutive_errors = 0
                    
                    # Verifica a saúde do sistema a cada 5 ciclos
                    if state_save_counter % 5 == 0:
                        logger.info("Executando verificação de saúde do sistema...")
                        try:
                            health_metrics = check_system_health(notifier.notify_status if notifier else None)
                            log_process_tree()
                            if health_metrics and health_metrics['memory_percent'] > 85:
                                logger.warning(f"Uso de memória alto: {health_metrics['memory_percent']}% - Forçando coleta de lixo")
                                import gc
                                gc.collect()
                        except Exception as e:
                            logger.error(f"Erro na verificação de saúde do sistema: {str(e)}")
                    
                    # Espera o intervalo configurado antes da próxima verificação
                    logger.info(f"Aguardando {config.check_interval} segundos até próxima verificação")
                    logger.info(f"Próxima análise prevista para: {(datetime.now() + timedelta(seconds=config.check_interval)).strftime('%H:%M:%S')}")
                    
                    # Em vez de um único sleep longo, usamos vários curtos para verificar SHOULD_EXIT
                    for _ in range(config.check_interval):
                        if SHOULD_EXIT:
                            logger.info("Sinal de encerramento detectado durante espera. Interrompendo ciclo...")
                            break
                        time.sleep(1)
                
                except requests.exceptions.RequestException as e:
                    consecutive_errors += 1
                    logger.error(f"Erro de conexão [{consecutive_errors}/{max_consecutive_errors}]: {str(e)}")
                    
                    # Determina tempo de espera baseado na quantidade de erros consecutivos
                    wait_time = min(60, 5 * (2 ** (consecutive_errors - 1)))  # 5, 10, 20, 40, 60 segundos
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Muitos erros consecutivos ({consecutive_errors}). Aplicando pausa longa.")
                        wait_time = 300  # 5 minutos de pausa após muitos erros
                        # Não reinicializa aqui, apenas espera mais tempo
                    
                    if hasattr(e, 'response') and e.response:
                        status_code = e.response.status_code
                        if status_code == 429:  # Rate limit
                            logger.error("Erro 429: Rate limit atingido. Pausa longa necessária.")
                            wait_time = max(wait_time, 120)  # Pelo menos 2 minutos para rate limit
                            logger.info(f"Próxima tentativa em {wait_time} segundos (aproximadamente {wait_time/60:.1f} minutos)")
                    
                    logger.warning(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                    logger.info("Retomando operações após pausa por erro")
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Erro inesperado no loop principal [{consecutive_errors}/{max_consecutive_errors}]: {str(e)}")
                    logger.exception("Detalhes do erro:")
                    
                    # Notifica via Telegram, mas continua a execução
                    if notifier:
                        try:
                            notifier.notify_error(f"Erro recuperável: {str(e)[:100]} - Tentativa {consecutive_errors}/{max_consecutive_errors}")
                        except:
                            logger.error("Falha ao enviar notificação de erro")
                    
                    # Pausa para recuperação
                    wait_time = min(120, 10 * consecutive_errors)
                    logger.warning(f"Aguardando {wait_time} segundos para recuperação...")
                    logger.info(f"Próxima tentativa em {wait_time} segundos (aproximadamente {wait_time/60:.1f} minutos)")
                    time.sleep(wait_time)
                    
                    # Se tivermos muitos erros consecutivos, tenta recuperar sem reinicializar completamente
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Limite de erros consecutivos atingido ({max_consecutive_errors}). " 
                                    f"Tentando recuperar conexões sem reinicializar.")
                        
                        # Tenta restaurar recursos críticos
                        try:
                            logger.info("Tentando restaurar conexão com a API...")
                            if not config.simulation_mode:
                                # Apenas testa a conexão em vez de reinicializar completamente
                                if binance.test_connection():
                                    logger.info("Conexão restaurada com sucesso")
                                    consecutive_errors = max(0, consecutive_errors - 2)  # Reduz o contador de erros
                                else:
                                    logger.error("Falha ao restaurar conexão")
                        except Exception as reinit_error:
                            logger.error(f"Erro ao restaurar recursos: {str(reinit_error)}")
                            logger.exception("Detalhes do erro de restauração:")
                
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
                logger.error(f"Erro {status_code}: Limite de requisições atingido. Este é um error fatal fora do loop principal.")
            elif status_code >= 500:
                logger.error(f"Erro {status_code}: Problema nos servidores da Binance. Este é um error fatal fora do loop principal.")
        
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
                'strategy_type': strategy.__class__.__name__,
                'pairs': pairs
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
            
            # Salva o estado no banco de dados
            save_success = db.save_app_state(state_to_save)
            if save_success:
                logger.info("Estado final salvo com sucesso no banco de dados para recuperação futura")
        
        except Exception as save_error:
            logger.error(f"Erro ao salvar estado: {str(save_error)}")
        
        # Notifica finalização via Telegram
        if notifier:
            notifier.notify_status("Robot-Crypt finalizado!")

# Código para executar a função main() quando o script for executado diretamente
if __name__ == "__main__":
    main()
