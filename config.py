#!/usr/bin/env python3
"""
Módulo de configuração para Robot-Crypt
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Classe de configuração do bot"""
    
    def __init__(self, config_file=None):
        """Inicializa a configuração do bot"""
        # Valores padrão
        self.api_key = os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = os.environ.get("BINANCE_API_SECRET", "")
        
        # Verifica se deve usar testnet ou produção
        testnet_mode = os.environ.get("USE_TESTNET", "true").lower()
        self.use_testnet = testnet_mode in ["true", "1", "yes", "y", "sim", "s"]
        
        # Verifica se deve usar modo de simulação (sem API)
        simulation_mode = os.environ.get("SIMULATION_MODE", "false").lower()
        self.simulation_mode = simulation_mode in ["true", "1", "yes", "y", "sim", "s"]
        
        # Verifica se existem chaves específicas para testnet
        if self.use_testnet:
            testnet_key = os.environ.get("TESTNET_API_KEY")
            testnet_secret = os.environ.get("TESTNET_API_SECRET")
            
            if testnet_key and testnet_secret:
                self.api_key = testnet_key
                self.api_secret = testnet_secret
        self.check_interval = 300  # 5 minutos entre verificações
        self.max_trades_per_day = 3  # Máximo de 3 trades por dia (conforme plano)
        
        # Carrega configurações de notificação do Telegram
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.notifications_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        
        # Carrega configurações personalizadas de trading do arquivo .env, se disponíveis
        trade_amount = os.environ.get("TRADE_AMOUNT")
        take_profit_percentage = os.environ.get("TAKE_PROFIT_PERCENTAGE")
        stop_loss_percentage = os.environ.get("STOP_LOSS_PERCENTAGE")
        max_hold_time = os.environ.get("MAX_HOLD_TIME")
        entry_delay = os.environ.get("ENTRY_DELAY")  # Adicionado para corrigir erro
        
        # Carrega pares de trading do arquivo .env
        trading_pairs_str = os.environ.get("TRADING_PAIRS", "")
        self.trading_pairs = []
        
        # Lista de pares disponíveis na TestNet da Binance
        testnet_supported_pairs = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "TRX/USDT", "XRP/USDT", 
            "LTC/USDT", "BCH/USDT", "EOS/USDT", "ADA/USDT", "DOT/USDT",
            "LINK/USDT", "BTC/BUSD", "ETH/BUSD", "BNB/BUSD", "BTC/ETH",
            "BNB/BTC", "ETH/BTC"
        ]
        
        if trading_pairs_str:
            # Converte de BNBUSDT para BNB/USDT (formato aceito pela API)
            raw_pairs = trading_pairs_str.split(",")
            for pair in raw_pairs:
                pair = pair.strip()
                if len(pair) >= 6:  # Pelo menos 3 letras para cada símbolo
                    # Descobre o ponto de divisão (geralmente XXXYYY onde XXX é a base e YYY é a cotação)
                    for i in range(3, len(pair) - 2):
                        # Tenta fazer a divisão em pontos comuns (BTC, ETH, USDT, BRL, etc)
                        if pair[i:i+3] in ["BTC", "ETH", "USD", "BRL", "BNB", "EUR"]:
                            formatted_pair = f"{pair[:i]}/{pair[i:]}"
                            
                            # Se estiver em modo testnet, só adiciona pares suportados
                            if self.use_testnet:
                                if formatted_pair in testnet_supported_pairs:
                                    self.trading_pairs.append(formatted_pair)
                                else:
                                    print(f"Aviso: Par {formatted_pair} ignorado porque não é suportado na TestNet")
                            else:
                                self.trading_pairs.append(formatted_pair)
                            break
                    else:
                        # Se não conseguir dividir, usa o formato original
                        self.trading_pairs.append(pair)
        
        # Log dos pares de trading carregados
        if self.trading_pairs:
            print(f"Pares de trading carregados do .env: {self.trading_pairs}")
        
        # Estratégia de Scalping (Fase 2)
        self.scalping = {
            "risk_per_trade": 0.01,  # 1% de risco por operação
            "profit_target": float(take_profit_percentage) / 100 if take_profit_percentage else 0.02,   # Padrão: 2% 
            "stop_loss": float(stop_loss_percentage) / 100 if stop_loss_percentage else 0.005,      # Padrão: 0.5%
            "max_position_size": 0.05,  # Máximo 5% do capital por posição
            "trade_amount": float(trade_amount) if trade_amount else 100.0  # Valor padrão: R$100
        }
        
        # Estratégia de Swing Trading (Fase 3)
        self.swing_trading = {
            "min_volume_increase": 0.3,  # 30% acima da média diária
            "profit_target": float(take_profit_percentage) / 100 if take_profit_percentage else 0.08,  # Padrão: 8%
            "stop_loss": float(stop_loss_percentage) / 100 if stop_loss_percentage else 0.03,          # Padrão: 3%
            "max_hold_time": float(max_hold_time) / 3600 if max_hold_time else 48,  # Converter segundos para horas
            "max_position_size": 0.05,    # Máximo 5% do capital por posição
            "entry_delay": int(entry_delay) if entry_delay else 60  # Delay entre análise e execução (segundos)
        }
        
        # Carrega configuração de arquivo se fornecido
        if config_file:
            self._load_config(config_file)
        else:
            # Tenta carregar do arquivo padrão
            default_config = Path.home() / ".robot-crypt" / "config.json"
            if default_config.exists():
                self._load_config(default_config)
    
    def _load_config(self, config_file):
        """Carrega configuração de arquivo"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Atualiza atributos com valores do arquivo
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except Exception as e:
            print(f"Erro ao carregar arquivo de configuração: {str(e)}")
    
    def save_config(self, config_file=None):
        """Salva configuração em arquivo"""
        if not config_file:
            config_dir = Path.home() / ".robot-crypt"
            config_dir.mkdir(exist_ok=True, parents=True)
            config_file = config_dir / "config.json"
        
        try:
            # Cria dicionário de configuração
            config = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "use_testnet": self.use_testnet,
                "check_interval": self.check_interval,
                "max_trades_per_day": self.max_trades_per_day,
                "scalping": self.scalping,
                "swing_trading": self.swing_trading
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar arquivo de configuração: {str(e)}")
    
    def get_balance(self, account_info):
        """Calcula o saldo total em BRL ou equivalente"""
        balance = 0.0
        
        # Se não tivermos dados da conta, retorna o valor padrão para simulação
        if not account_info or not isinstance(account_info, dict):
            return 100.0  # Valor padrão para simulação
        
        # Taxas de conversão aproximadas para BRL
        conversion_rates = {
            'BRL': 1.0,
            'USDT': 5.0,       # 1 USDT ≈ 5 BRL
            'BTC': 150000.0,   # 1 BTC ≈ 150,000 BRL
            'ETH': 8500.0,     # 1 ETH ≈ 8,500 BRL
            'BNB': 2250.0      # 1 BNB ≈ 2,250 BRL
        }
        
        # Pega os saldos da conta
        if 'balances' in account_info:
            for asset in account_info['balances']:
                asset_name = asset['asset']
                asset_balance = float(asset['free']) + float(asset['locked'])
                
                # Só considera ativos com saldo positivo
                if asset_balance > 0:
                    # Se temos taxa de conversão para esse ativo
                    if asset_name in conversion_rates:
                        balance += asset_balance * conversion_rates[asset_name]
                        print(f"Saldo de {asset_name}: {asset_balance} = {asset_balance * conversion_rates[asset_name]} BRL")
                    # Para outros ativos, tentamos uma estimativa conservadora
                    elif asset_balance > 0:
                        # Assumimos um valor conservador de 1 BRL por unidade para ativos desconhecidos
                        # Se for um altcoin, isso pode estar subestimado, mas é melhor que ignorar
                        estimated_value = asset_balance * 1.0  # valor conservador
                        balance += estimated_value
                        print(f"Saldo de {asset_name}: {asset_balance} (valor estimado: {estimated_value} BRL)")
        
        # Se ainda não encontramos saldo, usar valor padrão para simulação
        if balance == 0:
            balance = 100.0
            print("Nenhum saldo detectado, usando valor padrão para simulação: 100.0 BRL")
            
        print(f"Saldo total estimado: {balance:.2f} BRL")
        return balance
