#!/usr/bin/env python3
"""
Módulo para gerenciar informações da carteira do usuário na Binance
"""
import os
import logging
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import Json, DictCursor
from src.api.binance_api import BinanceAPI
from src.database.postgres_manager import PostgresManager

class WalletManager:
    """Classe para gerenciar a carteira do usuário e sincronizar com o banco de dados"""
    
    def __init__(self, binance_api=None, postgres_manager=None):
        """
        Inicializa o gerenciador de carteira
        
        Args:
            binance_api (BinanceAPI): Instância da API da Binance
            postgres_manager (PostgresManager): Instância do gerenciador de PostgreSQL
        """
        self.logger = logging.getLogger("robot-crypt")
        self.binance_api = binance_api
        self.postgres_manager = postgres_manager
        
        # Inicializa as conexões se não foram fornecidas
        if not self.binance_api:
            api_key = os.environ.get("BINANCE_API_KEY", "")
            api_secret = os.environ.get("BINANCE_API_SECRET", "")
            
            # Verifica se deve usar testnet ou produção
            testnet_mode = os.environ.get("USE_TESTNET", "true").lower()
            use_testnet = testnet_mode in ["true", "1", "yes", "y", "sim", "s"]
            
            # Se estiver usando testnet, verificar se existem chaves específicas para testnet
            if use_testnet:
                testnet_key = os.environ.get("TESTNET_API_KEY")
                testnet_secret = os.environ.get("TESTNET_API_SECRET")
                
                if testnet_key and testnet_secret:
                    api_key = testnet_key
                    api_secret = testnet_secret
            
            self.binance_api = BinanceAPI(api_key=api_key, api_secret=api_secret, testnet=use_testnet)
            
        if not self.postgres_manager:
            self.postgres_manager = PostgresManager()
            
        self.logger.info("WalletManager inicializado com sucesso")
        
    def _create_wallet_table_if_not_exists(self):
        """Método obsoleto - agora usamos asset_balances table criada no PostgresManager"""
        # A tabela asset_balances já é criada no PostgresManager._setup_tables()
        # Este método é mantido apenas para compatibilidade
        self.logger.info("Usando tabela asset_balances gerenciada pelo PostgresManager")
        return True
    
    def get_wallet_balance(self, user_id, store=True):
        """
        Obtém o saldo da carteira do usuário na Binance e opcionalmente armazena no banco de dados
        
        Args:
            user_id (str): ID do usuário para associar aos dados da carteira
            store (bool): Se True, armazena os dados no banco de dados
            
        Returns:
            dict: Informações da carteira do usuário
        """
        try:
            # Obter informações da conta
            account_info = self.binance_api.get_account_info()
            if not account_info or 'balances' not in account_info:
                self.logger.error("Não foi possível obter informações da conta")
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
                            # Lista de símbolos conhecidos por causar problemas
                            problematic_assets = [
                                'ETHW', 'LUNA', 'UST', 'BTCST', 'BCC', 'SOLO', 'LUNC', 'USTC', 
                                'FTT', 'SRM', 'RAY', 'FIDA', 'KIN', 'MER', 'OXY', 'STEP', 'COPE',
                                'MAPS', 'TULIP', 'SLRS', 'LIKE', 'AURY', 'DXL', 'MNGO', 'PRT',
                                'WOOP', 'ALEPH', 'CCAI', 'BOBA', 'MULTI', 'TOKE', 'ORCA', 'SUNNY',
                                'ATLAS', 'POLIS', 'GOFX', 'DFL', 'SHIB1000', 'DOGE1000', 'ELON1000'
                            ]
                            
                            if asset['asset'] in problematic_assets:
                                self.logger.info(f"Pulando ativo problemático conhecido: {asset['asset']}")
                                usdt_value = 0.0
                            else:
                                # Tenta obter o preço deste ativo em USDT
                                symbol = f"{asset['asset']}{currency}"
                                ticker = self.binance_api.get_ticker_price(symbol)
                                if ticker:
                                    price = float(ticker.get('price', 0))
                                    usdt_value = total * price
                                else:
                                    self.logger.warning(f"Preço não encontrado para {symbol}")
                                    usdt_value = 0.0
                    except Exception as e:
                        # Log mais específico sobre o erro
                        if "400 Client Error" in str(e) and "Bad Request" in str(e):
                            self.logger.warning(f"Par de trading {asset['asset']}/USDT não existe na Binance")
                        else:
                            self.logger.warning(f"Erro ao obter preço para {asset['asset']}: {str(e)}")
                        usdt_value = 0.0
                    
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
            
            # Armazenar no banco de dados se solicitado
            if store:
                self._store_wallet_data(wallet_data)
                
            return wallet_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo da carteira: {str(e)}")
            return None
    
    def _store_wallet_data(self, wallet_data):
        """
        Armazena os dados da carteira no banco de dados usando asset_balances
        
        Args:
            wallet_data (dict): Dados da carteira para armazenar
        
        Returns:
            bool: True se o armazenamento foi bem-sucedido, False caso contrário
        """
        try:
            user_id = wallet_data['user_id']
            total_balance_usdt = wallet_data.get('total_usdt_value', 0)
            
            # Taxa de conversão aproximada BRL/USDT (você pode buscar de uma API)
            usd_to_brl = 5.0  # Valor aproximado, idealmente buscar de uma API
            total_balance_brl = total_balance_usdt * usd_to_brl
            
            # Prepara dados dos ativos para a nova estrutura
            balances_data = []
            for balance in wallet_data['balances']:
                asset_data = {
                    'asset': balance['asset'],
                    'free': balance['free'],
                    'locked': balance['locked'],
                    'total': balance['total'],
                    'usdt_value': balance['usdt_value'],
                    'brl_value': balance['usdt_value'] * usd_to_brl,
                    'market_price': balance.get('market_price', 0),
                    'source': 'binance',
                    'metadata': {
                        'sync_timestamp': datetime.now().isoformat(),
                        'api_source': 'binance_api'
                    }
                }
                balances_data.append(asset_data)
            
            # Usa o método melhorado do PostgresManager
            success = self.postgres_manager.save_asset_balances(
                user_id=user_id,
                balances_data=balances_data,
                total_balance_usdt=total_balance_usdt,
                total_balance_brl=total_balance_brl
            )
            
            if success:
                self.logger.info(f"Dados da carteira salvos com sucesso para usuário {user_id}")
                self.logger.info(f"Total: {total_balance_usdt:.2f} USDT ({total_balance_brl:.2f} BRL)")
                return True
            else:
                self.logger.error(f"Falha ao salvar dados da carteira para usuário {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao armazenar dados da carteira: {str(e)}")
            return False
    
    def get_wallet_history(self, user_id, days=30):
        """
        Obtém o histórico da carteira do usuário no banco de dados usando asset_balances
        
        Args:
            user_id (str): ID do usuário
            days (int): Número de dias para retornar no histórico
            
        Returns:
            list: Histórico da carteira
        """
        try:
            # Usa o método do PostgresManager para obter evolução do portfólio
            return self.postgres_manager.get_portfolio_evolution(user_id, days=days)
                    
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico da carteira: {str(e)}")
            return []
            
    def get_total_balance(self, user_id):
        """
        Obtém o saldo total da carteira do usuário em USDT usando asset_balances
        
        Args:
            user_id (str): ID do usuário
            
        Returns:
            float: Saldo total em USDT
        """
        try:
            # Usa o método do PostgresManager para obter saldo total atual
            total_balance = self.postgres_manager.get_user_total_balance(user_id)
            return total_balance.get('total_balance_usdt', 0.0)
                    
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo total: {str(e)}")
            return 0.0
    
    # =============================================
    # Novos métodos para asset_balances
    # =============================================
    
    def get_current_balances(self, user_id):
        """
        Obtém os saldos atuais da carteira usando asset_balances
        
        Args:
            user_id (str): ID do usuário
            
        Returns:
            list: Lista de saldos de ativos
        """
        return self.postgres_manager.get_user_asset_balances(user_id)
    
    def get_current_total_balance(self, user_id):
        """
        Obtém o saldo total atual da carteira
        
        Args:
            user_id (str): ID do usuário
            
        Returns:
            dict: Saldo total em USDT e BRL
        """
        return self.postgres_manager.get_user_total_balance(user_id)
    
    def get_portfolio_summary(self, user_id):
        """
        Obtém um resumo completo do portfólio
        
        Args:
            user_id (str): ID do usuário
            
        Returns:
            dict: Resumo do portfólio
        """
        try:
            # Obtém dados básicos
            balances = self.get_current_balances(user_id)
            total_balance = self.get_current_total_balance(user_id)
            top_assets = self.postgres_manager.get_top_assets_by_value(user_id, limit=5)
            evolution = self.postgres_manager.get_portfolio_evolution(user_id, days=7)
            
            # Calcula algumas métricas
            active_assets = len([b for b in balances if b['total'] > 0])
            
            return {
                'user_id': user_id,
                'total_balance_usdt': total_balance['total_balance_usdt'],
                'total_balance_brl': total_balance['total_balance_brl'],
                'active_assets_count': active_assets,
                'top_assets': top_assets,
                'recent_evolution': evolution,
                'last_update': total_balance['snapshot_date'],
                'all_balances': balances
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo do portfólio: {str(e)}")
            return None
    
    def sync_wallet_with_binance(self, user_id):
        """
        Sincroniza a carteira com a Binance e atualiza asset_balances
        
        Args:
            user_id (str): ID do usuário
            
        Returns:
            dict: Dados atualizados da carteira
        """
        try:
            # Obtém dados atuais da Binance
            wallet_data = self.get_wallet_balance(user_id, store=True)
            
            if wallet_data:
                self.logger.info(f"Carteira sincronizada para usuário {user_id}")
                return {
                    'success': True,
                    'total_balance_usdt': wallet_data['total_usdt_value'],
                    'assets_count': len(wallet_data['balances']),
                    'timestamp': wallet_data['timestamp']
                }
            else:
                self.logger.error(f"Falha ao sincronizar carteira para usuário {user_id}")
                return {'success': False, 'error': 'Failed to get wallet data from Binance'}
                
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar carteira: {str(e)}")
            return {'success': False, 'error': str(e)}


# Exemplo de uso do módulo
if __name__ == "__main__":
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    # Inicializar o gerenciador de carteira
    wallet_manager = WalletManager()
    
    # Obter e armazenar saldo da carteira
    user_id = "default_user"  # ID do usuário (pode ser configurado no .env)
    wallet_data = wallet_manager.get_wallet_balance(user_id)
    
    if wallet_data:
        print(f"Saldo total: {wallet_data['total_usdt_value']:.2f} USDT")
        print(f"Ativos: {len(wallet_data['balances'])}")
        
        for asset in wallet_data['balances']:
            print(f"{asset['asset']}: {asset['total']} ({asset['usdt_value']:.2f} USDT)")
    else:
        print("Não foi possível obter o saldo da carteira")
