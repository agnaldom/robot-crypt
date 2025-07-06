#!/usr/bin/env python3
"""
Módulo de configuração para o script binance_data_sync_noprompt
Uma versão simplificada do Config para evitar o prompt do dotenv
"""
import os

class Config:
    """Versão simplificada da classe Config para sincronização de dados"""
    
    def __init__(self):
        """Inicializa a configuração"""
        # Valores da API Binance
        self.api_key = os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = os.environ.get("BINANCE_API_SECRET", "")
        
        # Modo de operação
        self.use_testnet = os.environ.get("USE_TESTNET", "false").lower() in ["true", "1", "yes", "y"]
        self.simulation_mode = os.environ.get("SIMULATION_MODE", "false").lower() in ["true", "1", "yes", "y"]
        
        # Pares de trading
        self.trading_pairs = os.environ.get("TRADING_PAIRS", "BTC/USDT,ETH/USDT")
        if self.trading_pairs:
            self.trading_pairs = [p.strip() for p in self.trading_pairs.split(",")]
        else:
            self.trading_pairs = ["BTC/USDT", "ETH/USDT"]
        
        # Intervalo de verificação
        self.check_interval = os.environ.get("CHECK_INTERVAL", "15m")
        self.check_interval_seconds = self._parse_interval(self.check_interval)
        
        # Log das configurações carregadas
        print(f"Pares de trading carregados do .env: {self.trading_pairs}")
    
    def _parse_interval(self, interval_str):
        """
        Converte uma string de intervalo (ex: '15m', '1h') para segundos
        """
        if not interval_str:
            return 60 * 15  # 15 minutos padrão
            
        value = int(''.join(filter(str.isdigit, interval_str)))
        unit = ''.join(filter(str.isalpha, interval_str)).lower()
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 60 * 60
        elif unit == 'd':
            return value * 60 * 60 * 24
        else:
            return value  # assume segundos se não houver unidade
