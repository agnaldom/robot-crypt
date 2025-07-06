#!/usr/bin/env python3
"""
Script independente para sincronizar informações da carteira Binance com o banco de dados.
Esta versão não depende do pandas ou de outras bibliotecas complexas.
"""
import os
import sys
import logging
import json
import argparse
from datetime import datetime
import traceback

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("robot-crypt")

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv não está instalado. As variáveis de ambiente devem ser definidas manualmente.")

# Adiciona o diretório atual ao path para garantir que os imports funcionem
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def get_binance_account_info(api_key, api_secret, testnet=True):
    """
    Obtém informações da conta Binance diretamente, sem depender do WalletManager
    
    Args:
        api_key (str): Chave API da Binance
        api_secret (str): Secret da API da Binance
        testnet (bool): Se True, usa a testnet da Binance
        
    Returns:
        dict: Informações da conta ou None se ocorrer um erro
    """
    try:
        # Importa aqui para evitar dependências desnecessárias
        from binance_api import BinanceAPI
        
        # Inicializa API da Binance
        api = BinanceAPI(api_key=api_key, api_secret=api_secret, testnet=testnet)
        
        # Obtém informações da conta
        account_info = api.get_account_info()
        
        return account_info
    except Exception as e:
        logger.error(f"Erro ao obter informações da conta Binance: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def get_ticker_price(api_key, api_secret, symbol, testnet=True):
    """
    Obtém o preço atual de um símbolo
    
    Args:
        api_key (str): Chave API da Binance
        api_secret (str): Secret da API da Binance
        symbol (str): Símbolo para obter o preço (ex: BTCUSDT)
        testnet (bool): Se True, usa a testnet da Binance
        
    Returns:
        float: Preço atual ou 0 se ocorrer um erro
    """
    try:
        # Importa aqui para evitar dependências desnecessárias
        from binance_api import BinanceAPI
        
        # Inicializa API da Binance
        api = BinanceAPI(api_key=api_key, api_secret=api_secret, testnet=testnet)
        
        # Obtém o preço
        ticker = api.get_ticker_price(symbol)
        
        if ticker and 'price' in ticker:
            return float(ticker['price'])
        
        return 0
    except Exception as e:
        logger.error(f"Erro ao obter preço para {symbol}: {str(e)}")
        return 0

def store_wallet_data(postgres_manager, user_id, wallet_data):
    """
    Armazena os dados da carteira no banco de dados
    
    Args:
        postgres_manager: Instância do PostgresManager
        user_id (str): ID do usuário
        wallet_data (dict): Dados da carteira
        
    Returns:
        bool: True se o armazenamento foi bem-sucedido
    """
    try:
        # Verifica se a conexão está estabelecida
        postgres_manager.connect()
        
        if postgres_manager.conn and postgres_manager.cursor:
            # Garante que a tabela exista
            postgres_manager.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_wallet (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id VARCHAR(100) NOT NULL,
                    asset VARCHAR(20) NOT NULL,
                    free DECIMAL(24, 8) NOT NULL,
                    locked DECIMAL(24, 8) NOT NULL,
                    total DECIMAL(24, 8) NOT NULL,
                    usdt_value DECIMAL(24, 8),
                    total_balance DECIMAL(24, 8),
                    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar índices para melhorar a performance
            postgres_manager.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_wallet_user_asset 
                ON user_wallet(user_id, asset)
            """)
            
            postgres_manager.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_wallet_timestamp 
                ON user_wallet(timestamp)
            """)
            
            # Commit das alterações
            postgres_manager.conn.commit()
            
            # Hora atual
            now = datetime.now()
            
            # Remove registros antigos deste usuário
            postgres_manager.cursor.execute("""
                DELETE FROM user_wallet 
                WHERE user_id = %s
            """, (user_id,))
            
            # Insere os novos dados
            for balance in wallet_data['balances']:
                postgres_manager.cursor.execute("""
                    INSERT INTO user_wallet (
                        timestamp, user_id, asset, free, locked, total, usdt_value, total_balance, last_updated
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    now,
                    user_id,
                    balance['asset'],
                    balance['free'],
                    balance['locked'],
                    balance['total'],
                    balance['usdt_value'],
                    wallet_data['total_usdt_value'],  # Adicionando o saldo total em cada registro
                    now
                ))
            
            # Commit das alterações
            postgres_manager.conn.commit()
            
            logger.info(f"Dados de {len(wallet_data['balances'])} ativos armazenados para usuário {user_id}")
            return True
    except Exception as e:
        # Rollback em caso de erro
        if hasattr(postgres_manager, 'conn') and postgres_manager.conn:
            postgres_manager.conn.rollback()
        logger.error(f"Erro ao armazenar dados da carteira: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def sync_wallet_data(user_id="default_user", show_details=True):
    """
    Sincroniza os dados da carteira do usuário com o banco de dados
    
    Args:
        user_id (str): ID do usuário
        show_details (bool): Se True, mostra detalhes dos ativos
        
    Returns:
        dict: Dados da carteira sincronizados
    """
    try:
        # Importa o mínimo necessário para evitar dependências de pandas
        from config import Config
        from postgres_manager import PostgresManager
        
        # Inicializa a configuração
        config = Config()
        
        # Obtém chaves da API
        api_key = config.api_key
        api_secret = config.api_secret
        use_testnet = config.use_testnet
        
        if not api_key or not api_secret:
            logger.error("API Key ou Secret não configurados. Verifique seu arquivo .env")
            return None
        
        # Obtém informações da conta
        account_info = get_binance_account_info(api_key, api_secret, use_testnet)
        
        if not account_info or 'balances' not in account_info:
            logger.error("Não foi possível obter informações da conta")
            return None
        
        # Filtrar apenas ativos com saldo positivo
        balances = []
        total_usdt_value = 0.0
        currency = "USDT"  # Moeda base para conversão de valores
        
        for asset in account_info['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            total = free + locked
            
            if total > 0:
                # Tenta obter o preço em USDT deste ativo
                usdt_value = 0.0
                
                try:
                    if asset['asset'] == currency:
                        usdt_value = total
                    else:
                        # Tenta obter o preço deste ativo em USDT
                        symbol = f"{asset['asset']}{currency}"
                        price = get_ticker_price(api_key, api_secret, symbol, use_testnet)
                        usdt_value = total * price
                except Exception as e:
                    logger.warning(f"Erro ao obter preço para {asset['asset']}: {str(e)}")
                
                balances.append({
                    'asset': asset['asset'],
                    'free': free,
                    'locked': locked,
                    'total': total,
                    'usdt_value': usdt_value
                })
                
                total_usdt_value += usdt_value
        
        # Estrutura de retorno
        wallet_data = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'balances': balances,
            'total_usdt_value': total_usdt_value
        }
        
        # Inicializa o PostgresManager
        postgres_manager = PostgresManager()
        
        # Armazena os dados
        store_wallet_data(postgres_manager, user_id, wallet_data)
        
        if wallet_data:
            logger.info(f"Sincronização completa! Saldo total: {wallet_data['total_usdt_value']:.2f} USDT")
            logger.info(f"Ativos encontrados: {len(wallet_data['balances'])}")
            
            if show_details:
                logger.info("Detalhes dos ativos:")
                # Ordenar por valor USDT (do maior para o menor)
                sorted_assets = sorted(wallet_data['balances'], key=lambda x: x['usdt_value'], reverse=True)
                
                for asset in sorted_assets:
                    logger.info(f"  {asset['asset']}: {asset['total']} ({asset['usdt_value']:.2f} USDT)")
            
            return wallet_data
        else:
            logger.error("Não foi possível sincronizar os dados da carteira")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao sincronizar dados da carteira: {str(e)}")
        return None

def get_total_wallet_balance(user_id):
    """
    Obtém o saldo total da carteira do usuário em USDT
    
    Args:
        user_id (str): ID do usuário
            
    Returns:
        float: Saldo total em USDT
    """
    try:
        # Importa o PostgresManager
        from postgres_manager import PostgresManager
        
        # Inicializa o PostgresManager
        postgres_manager = PostgresManager()
        
        # Verificar se a conexão está estabelecida
        postgres_manager.connect()
        if postgres_manager.conn and postgres_manager.cursor:
            # Consulta o saldo total
            postgres_manager.cursor.execute("""
                SELECT 
                    total_balance
                FROM 
                    user_wallet 
                WHERE 
                    user_id = %s
                LIMIT 1
            """, (user_id,))
            
            result = postgres_manager.cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
                
    except Exception as e:
        logger.error(f"Erro ao obter saldo total: {str(e)}")
        return 0.0

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sincroniza dados da carteira Binance com o PostgreSQL")
    
    parser.add_argument(
        "--user-id", 
        dest="user_id",
        type=str, 
        default=os.environ.get("WALLET_USER_ID", "default_user"),
        help="ID do usuário para associar aos dados da carteira"
    )
    
    parser.add_argument(
        "--no-details",
        dest="no_details",
        action="store_true",
        help="Não mostrar detalhes dos ativos"
    )
    
    parser.add_argument(
        "--balance-only",
        dest="balance_only",
        action="store_true",
        help="Mostrar apenas o saldo total sem sincronizar"
    )
    
    args = parser.parse_args()
    
    # Se apenas o saldo for solicitado
    if args.balance_only:
        total_balance = get_total_wallet_balance(args.user_id)
        logger.info(f"Saldo total atual: {total_balance:.2f} USDT")
        return 0
    
    # Sincroniza os dados da carteira
    wallet_data = sync_wallet_data(
        user_id=args.user_id,
        show_details=not args.no_details
    )
    
    # Retorna código de status apropriado
    if wallet_data:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
