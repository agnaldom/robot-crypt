#!/usr/bin/env python3
"""
Módulo de estratégias de negociação para Robot-Crypt
"""
import time
import logging
import numpy as np
from datetime import datetime, timedelta

class TradingStrategy:
    """Classe base para estratégias de negociação"""
    
    def __init__(self, config, binance_api):
        """Inicializa a estratégia com configuração e API"""
        self.config = config
        self.binance = binance_api
        self.logger = logging.getLogger("robot-crypt")
        self.trades_today = 0
        self.last_trade_reset = datetime.now().date()
        self.consecutive_losses = 0  # Contador de perdas consecutivas
    
    def check_trade_limit(self):
        """Verifica se o limite diário de trades foi atingido"""
        today = datetime.now().date()
        
        # Reset contador de trades se for um novo dia
        if today > self.last_trade_reset:
            self.trades_today = 0
            self.last_trade_reset = today
        
        return self.trades_today < self.config.max_trades_per_day
    
    def record_trade(self):
        """Registra um novo trade no contador diário"""
        self.trades_today += 1
        self.logger.info(f"Trade realizado. {self.trades_today}/{self.config.max_trades_per_day} trades hoje.")
    
    def calculate_position_size(self, capital, price, risk_percentage):
        """Calcula o tamanho da posição baseado no capital e risco"""
        # Aplica redução de risco após perdas consecutivas
        adjusted_risk = risk_percentage
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            adjusted_risk = risk_percentage * self.config.risk_reduction_factor
            self.logger.warning(f"Reduzindo risco para {adjusted_risk*100:.2f}% após {self.consecutive_losses} perdas consecutivas")
        
        max_risk = capital * adjusted_risk
        
        # Também aplicar limitação de posição máxima
        max_position = capital * self.config.scalping["max_position_size"]
        
        # Quantidade baseada no menor valor entre risco e posição máxima
        quantity = min(max_risk, max_position) / price
        
        return quantity
    
    def analyze_market(self, symbol):
        """Método base para análise de mercado - deve ser implementado nas subclasses"""
        raise NotImplementedError("Método deve ser implementado na subclasse")
    
    def execute_buy(self, symbol, price):
        """Método base para executar compra - deve ser implementado nas subclasses"""
        raise NotImplementedError("Método deve ser implementado na subclasse")
    
    def execute_sell(self, symbol, price):
        """Método base para executar venda - deve ser implementado nas subclasses"""
        raise NotImplementedError("Método deve ser implementado na subclasse")


class ScalpingStrategy(TradingStrategy):
    """Implementação da estratégia de Scalping de Baixo Risco (Fase 2)
    
    Foco em pares líquidos (BTC/BRL, ETH/BRL) para minimizar riscos
    Objetivos: Ganhos de 1-3% por operação
    Gestão de Risco: 1% do capital em risco por operação
    """
    
    def __init__(self, config, binance_api):
        """Inicializa a estratégia de scalping"""
        super().__init__(config, binance_api)
        self.open_positions = {}  # Rastreia posições abertas
    
    def identify_support_resistance(self, symbol, period="1h", lookback=24):
        """Identifica níveis de suporte e resistência
        
        Analisa as últimas 24 velas de 1 hora para identificar:
        - Suporte (níveis onde o preço tende a subir)
        - Resistência (níveis onde o preço tende a cair)
        - Tendência de curto prazo
        """
        try:
            # Formata o símbolo corretamente para a API
            api_symbol = symbol.replace('/', '')  # Remove a barra (ex: "BTC/USDT" -> "BTCUSDT")
            
            # Registra o símbolo que está sendo consultado para depuração
            self.logger.info(f"Consultando dados para o símbolo {api_symbol} (período: {period}, lookback: {lookback})")
            
            # Obtém dados de velas do período especificado
            klines = self.binance.get_klines(api_symbol, period, lookback)
            
            # Extrai preços de fechamento
            closes = [float(k[4]) for k in klines]
            lows = [float(k[3]) for k in klines]
            highs = [float(k[2]) for k in klines]
            
            # Verificar se estamos lidando com uma criptomoeda de valor muito baixo (como SHIB, FLOKI)
            is_micro_value = max(closes) < 0.01
            
            # Calcula a média móvel das últimas 8 velas para tendência
            short_ma = sum(closes[-8:]) / 8
            
            # Calcula a variação percentual da última hora
            hourly_change = ((closes[-1] / closes[-2]) - 1) * 100 if len(closes) > 1 else 0
            
            # Cálculo de suporte (mínimo recente)
            support = min(lows[-5:])  # Últimas 5 velas
            
            # Cálculo de resistência (máximo recente)
            resistance = max(highs[-5:])  # Últimas 5 velas
            
            # Preço atual
            current_price = closes[-1]
            
            # Para moedas com valores muito pequenos, formatamos a saída de modo diferente
            # para evitar mostrar apenas zeros
            if is_micro_value:
                # Determine o número de casas decimais necessárias
                decimal_places = 8  # Padrão para valores muito pequenos
                
                # Log formatado apropriadamente para valores micro
                self.logger.info(f"{symbol} - Variação 1h: {hourly_change:.2f}% | Suporte: {support:.{decimal_places}f} | Resistência: {resistance:.{decimal_places}f}")
            else:
                # Log padrão para outros valores
                self.logger.info(f"{symbol} - Variação 1h: {hourly_change:.2f}% | Suporte: {support:.2f} | Resistência: {resistance:.2f}")
            
            return {
                'support': support,
                'resistance': resistance,
                'current_price': current_price,
                'short_ma': short_ma,
                'hourly_change': hourly_change,
                'is_micro_value': is_micro_value  # Adicionamos esta flag para uso em outros métodos
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular suporte/resistência para {symbol}: {str(e)}")
            return None
    
    def is_near_support(self, price_data, threshold=0.015):
        """Verifica se o preço atual está próximo do suporte (1.5% de queda)"""
        if not price_data:
            return False
            
        # Calcula diferença percentual do preço atual para o suporte
        current = price_data['current_price']
        support = price_data['support']
        
        # Tratamento especial para valores muito pequenos para evitar erros de precisão
        if current < 0.0000001 or support < 0.0000001:  # Valor muito próximo de zero
            self.logger.warning(f"Valores muito próximos de zero detectados: current={current}, support={support}")
            return False
        
        # Se estivermos lidando com valores muito pequenos, usamos um threshold ajustado
        adjusted_threshold = threshold
        if 'is_micro_value' in price_data and price_data['is_micro_value']:
            # Para micro-valores, podemos precisar de um threshold mais sensível
            # porque mesmo pequenas flutuações absolutas podem representar grandes variações %
            self.logger.debug(f"Usando threshold ajustado para micro-valor: {adjusted_threshold}")
        
        percent_to_support = (current - support) / current
        
        # Está próximo do suporte se a diferença for menor que o threshold
        return percent_to_support <= adjusted_threshold and percent_to_support >= 0
    
    def analyze_market(self, symbol, notifier=None):
        """Analisa o mercado usando estratégia de scalping
        
        Implementa os critérios da Fase 2 (R$100 → R$300):
        
        Args:
            symbol (str): O par de moedas para análise
            notifier (TelegramNotifier, optional): Notificador Telegram para enviar alertas
        - Compra quando BTC/ETH cai -1.5% em 1h e está em suporte diário
        - Vende com lucro de 2-3%
        - Stop loss em 0.5% abaixo do suporte
        """
        # Verifica limite diário de trades
        if not self.check_trade_limit():
            self.logger.info(f"Limite diário de trades atingido ({self.config.max_trades_per_day})")
            return False, None, None
            
        # Verifica se tivemos 2 prejuízos consecutivos (regra de ouro)
        if self.consecutive_losses >= 2:
            self.logger.warning(f"Pausando operações após {self.consecutive_losses} prejuízos consecutivos")
            return False, None, None
        
        # Obtém dados de suporte/resistência
        price_data = self.identify_support_resistance(symbol, period="1h", lookback=24)
        if not price_data:
            return False, None, None
        
        current_price = price_data['current_price']
        hourly_change = price_data['hourly_change']
        
        # Verifica se já temos posição aberta neste símbolo
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            entry_time = position['entry_time']
            time_held = (datetime.now() - entry_time).total_seconds() / 3600  # em horas
            
            # Calcula lucro percentual
            profit_percent = (current_price - position['entry_price']) / position['entry_price']
            
            # Calcula o custo das taxas (0.1% na compra e 0.1% na venda)
            fee_cost = 0.001 * 2
            
            # Se atingiu alvo de lucro (considerando as taxas), vende
            if profit_percent >= (self.config.scalping['profit_target'] + fee_cost):
                self.logger.info(f"{symbol} atingiu alvo de lucro: {profit_percent:.2%}")
                return True, "sell", current_price
                
            # Se atingiu stop loss, vende para proteger capital
            elif profit_percent <= -self.config.scalping['stop_loss']:
                self.logger.info(f"{symbol} atingiu stop loss: {profit_percent:.2%}")
                return True, "sell", current_price
                
        else:
            # Critérios de entrada:
            # 1. Preço próximo do suporte
            # 2. Queda recente de pelo menos 1.5% em 1h (indicando possível reversão)
            if self.is_near_support(price_data) and hourly_change <= -1.5:
                self.logger.info(f"{symbol} queda de {hourly_change:.2f}% e próximo do suporte, buscando entrada")
                return True, "buy", current_price
        
        return False, None, None
    
    def execute_buy(self, symbol, price):
        """Executa ordem de compra usando estratégia de scalping
        
        Implementa o cálculo correto de risco por operação:
        - Risco máximo de 1% do capital por operação
        - Calcula corretamente o tamanho da posição e taxas
        """
        try:
            # Obtém saldo da conta
            account_info = self.binance.get_account_info()
            capital = self.config.get_balance(account_info)
            
            # Calcula valor de entrada com base em 1% do capital
            risk_per_trade = self.config.scalping['risk_per_trade']
            entrada = capital * risk_per_trade
            
            # Limita a 5% do capital total (regra de ouro)
            max_position = capital * self.config.scalping['max_position_size']
            position_value = min(entrada, max_position)
            
            # Calcula a quantidade considerando as taxas
            fee_cost = 0.001  # 0.1% de taxa na Binance
            available_for_purchase = position_value * (1 - fee_cost)
            quantity = available_for_purchase / price
            
            # Ajusta a precisão da quantidade com base no preço da moeda
            # Moedas de micro-valor precisam de mais casas decimais
            if price < 0.000001:  # Valores extremamente pequenos (ex: SHIB)
                quantity = round(quantity, 0)  # Sem casas decimais para valores muito pequenos
            elif price < 0.001:   # Valores muito pequenos
                quantity = round(quantity, 0)  # Geralmente sem casas decimais
            elif price < 0.01:    # Valores pequenos
                quantity = round(quantity, 2)  # 2 casas decimais
            elif price < 1:       # Valores médios
                quantity = round(quantity, 4)  # 4 casas decimais
            else:                 # Valores altos
                quantity = round(quantity, 6)  # 6 casas decimais padrão
            
            # Executa ordem de compra
            self.logger.info(f"Comprando {quantity:.8f} de {symbol} a {price:.8f}")
            self.logger.info(f"Valor: R${position_value:.2f} | Capital: R${capital:.2f} | Taxas: R${position_value * fee_cost:.2f}")
            
            # Formata o símbolo para a API
            api_symbol = symbol.replace('/', '')
            
            # Coloca ordem LIMIT com GTC (Good Till Cancelled)
            order = self.binance.create_order(
                symbol=api_symbol,
                side="BUY",
                type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force="GTC"
            )
            
            # Registra posição aberta
            self.open_positions[symbol] = {
                'entry_price': price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'entry_time': datetime.now()
            }
            
            # Atualiza contador de trades
            self.record_trade()
            
            # Retorna sucesso e informações da ordem
            return True, {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'order_id': order['orderId']
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao executar compra de {symbol}: {str(e)}")
            return False, None
    
    def execute_sell(self, symbol, price):
        """Executa ordem de venda usando estratégia de scalping
        
        Implementa:
        - Cálculo correto de lucro após taxas
        - Registro de perdas consecutivas para pausa após 2 perdas (regra de ouro)
        """
        try:
            if symbol not in self.open_positions:
                self.logger.error(f"Tentativa de venda sem posição aberta para {symbol}")
                return False, None
            
            position = self.open_positions[symbol]
            quantity = position['quantity']
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            hold_time_hours = (datetime.now() - entry_time).total_seconds() / 3600
            
            # Executa ordem de venda
            self.logger.info(f"Vendendo {quantity:.8f} de {symbol} a {price:.2f}")
            
            # Formata o símbolo para a API
            api_symbol = symbol.replace('/', '')
            
            # Coloca ordem LIMIT com GTC (Good Till Cancelled)
            order = self.binance.create_order(
                symbol=api_symbol,
                side="SELL",
                type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force="GTC"
            )
            
            # Calcula resultado do trade
            profit_percent = (price - entry_price) / entry_price
            
            # Considera taxas (0.1% na compra + 0.1% na venda)
            fee_cost = 0.001 * 2
            net_profit_percent = profit_percent - fee_cost
            
            # Calcula estatísticas completas do trade
            from utils import calculate_profit
            profit_stats = calculate_profit(
                entry_price=entry_price,
                exit_price=price,
                quantity=quantity
            )
            
            # Verifica se foi lucro ou prejuízo
            if net_profit_percent > 0:
                self.logger.info(f"Trade de {symbol} finalizado com LUCRO: {net_profit_percent:.2%} (após taxas)")
                self.consecutive_losses = 0  # Reseta contador de perdas consecutivas
            else:
                self.logger.warning(f"Trade de {symbol} finalizado com PREJUÍZO: {net_profit_percent:.2%} (após taxas)")
                self.consecutive_losses += 1
                self.logger.warning(f"Perdas consecutivas: {self.consecutive_losses}")
                
                # Se atingiu 2 perdas consecutivas, notifica
                if self.consecutive_losses >= 2:
                    self.logger.warning("Atingido limite de 2 perdas consecutivas. Pausando operações conforme regra de ouro.")
            
            self.logger.info(f"Lucro líquido: R${profit_stats['net_profit']:.2f} (após taxas de R${profit_stats['total_fees']:.2f})")
            self.logger.info(f"Tempo de posição: {hold_time_hours:.2f} horas")
            
            # Remove posição aberta
            del self.open_positions[symbol]
            
            # Retorna sucesso e informações da ordem
            return True, {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'profit': profit_percent,
                'profit_stats': profit_stats
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao executar venda de {symbol}: {str(e)}")
            return False, None


class SwingTradingStrategy(TradingStrategy):
    """Implementação da estratégia de Swing Trading em Altcoins (Fase 3)
    
    Estratégia da Fase 3 (R$300 → R$1.000):
    - Foco: Swing Trade em altcoins com preço < R$1.00
    - Critérios: Volume >30% da média diária, novas listagens
    - Saída: 7-10% de lucro ou após 48h
    """
    
    def __init__(self, config, binance_api):
        """Inicializa a estratégia de swing trading"""
        super().__init__(config, binance_api)
        self.open_positions = {}  # Rastreia posições abertas
        
        # Lista de moedas monitoradas para a estratégia
        self.altcoins_under_1_brl = []
        self.update_altcoins_list()
    
    def update_altcoins_list(self):
        """Atualiza a lista de altcoins abaixo de R$1.00 com boa liquidez"""
        try:
            # Verifica se estamos usando testnet
            is_testnet = hasattr(self.config, 'use_testnet') and self.config.use_testnet
            
            if is_testnet:
                # Para testnet, usamos pares disponíveis com USDT
                self.altcoins_under_1_brl = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BNB/USDT"]
                self.logger.info(f"Lista de altcoins para testnet atualizada: {len(self.altcoins_under_1_brl)} moedas")
            else:
                # Na implementação real, isso consultaria a API da Binance
                # e filtraria moedas abaixo de R$1.00 com volume mínimo
                # Para demonstração, listamos algumas moedas populares
                self.altcoins_under_1_brl = ["SHIB/BRL", "FLOKI/BRL", "DOGE/BRL", "XRP/BRL", "ADA/BRL"]
                self.logger.info(f"Lista de altcoins atualizada: {len(self.altcoins_under_1_brl)} moedas")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar lista de altcoins: {str(e)}")
    
    def check_volume_increase(self, symbol, threshold=0.30, notifier=None):
        """Verifica se o volume da moeda aumentou acima do threshold (30% por padrão)
        
        Args:
            symbol (str): Par de trading para verificar
            threshold (float): Percentual mínimo de aumento (0.30 = 30%)
            notifier (TelegramNotifier, optional): Notificador Telegram para enviar alertas
        
        Returns:
            bool: True se o volume aumentou mais que o threshold, False caso contrário
        """
        start_time = datetime.now()
        self.logger.info(f"Verificando aumento de volume para {symbol} (threshold: {threshold:.2%})")
        
        # Validação de entrada
        if not symbol or not isinstance(symbol, str):
            self.logger.error(f"Símbolo inválido: {symbol}")
            return False
            
        if threshold < 0:
            self.logger.warning(f"Threshold negativo ({threshold:.2%}) para {symbol}. Usando valor absoluto.")
            threshold = abs(threshold)
        
        try:
            # Obter dados de volume usando abstração para testes
            volume_data = self.get_volume_data(symbol, notifier=notifier)
            
            # Validação dos dados recebidos
            if not volume_data:
                self.logger.warning(f"Nenhum dado de volume disponível para {symbol}")
                return False
                
            # Diferentes formas de obter o aumento de volume
            if 'volume_increase' in volume_data:
                # Caso 1: O aumento já está calculado (útil para testes mockados)
                volume_increase = volume_data['volume_increase']
                self.logger.debug(f"{symbol} - Usando volume_increase pré-calculado: {volume_increase:.2%}")
                
            # Caso 2: Temos média e volume atual para calcular o aumento
            elif 'avg_volume' in volume_data and 'current_volume' in volume_data:
                avg_volume = volume_data['avg_volume']
                current_volume = volume_data['current_volume']
                
                # Proteção contra divisão por zero
                if avg_volume <= 0:
                    self.logger.warning(f"{symbol} - Volume médio é zero ou negativo: {avg_volume}")
                    return False
                
                volume_increase = (current_volume - avg_volume) / avg_volume
                self.logger.debug(f"{symbol} - Volume atual: {current_volume:.2f}, Média: {avg_volume:.2f}")
                
            else:
                self.logger.error(f"Dados de volume insuficientes para {symbol}. Chaves disponíveis: {list(volume_data.keys())}")
                return False
                
            # Verificação do critério
            result = volume_increase >= threshold
            
            # Log com mais detalhes para análise
            elapsed = (datetime.now() - start_time).total_seconds() * 1000  # em ms
            if result:
                self.logger.info(f"{symbol} - ✅ Aumento significativo de volume detectado: {volume_increase:.2%} (limite: {threshold:.2%}) em {elapsed:.1f}ms")
            else:
                self.logger.info(f"{symbol} - ❌ Aumento de volume insuficiente: {volume_increase:.2%} (limite: {threshold:.2%}) em {elapsed:.1f}ms")
                
            return result
            
        except ZeroDivisionError:
            self.logger.error(f"Erro de divisão por zero ao calcular aumento de volume para {symbol}")
            return False
        except TypeError as e:
            self.logger.error(f"Erro de tipo ao processar dados de volume para {symbol}: {str(e)}")
            return False
        except KeyError as e:
            self.logger.error(f"Chave não encontrada nos dados de volume para {symbol}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro não esperado ao verificar aumento de volume para {symbol}: {str(e)}")
            return False
    
    def analyze_volume(self, symbol, period="1d", lookback=10, notifier=None):
        """Analisa volume de negociação para identificar aumento 
        
        Procura por moedas com aumento de volume >30% em relação à média,
        indicando possível movimento de preço significativo
        
        Args:
            symbol (str): O par de moedas para análise
            period (str): Período das velas (ex: "1d", "4h")
            lookback (int): Número de períodos para calcular a média
            notifier (TelegramNotifier, optional): Notificador Telegram para enviar alertas
        """
        try:
            # Formata o símbolo corretamente para a API
            api_symbol = symbol.replace('/', '')  # Remove a barra (ex: "BTC/USDT" -> "BTCUSDT")
            
            # Obtém dados de velas do período especificado
            klines = self.binance.get_klines(api_symbol, period, lookback + 1)
            
            # Extrai volumes
            volumes = [float(k[5]) for k in klines]
            
            # Calcula média de volume dos últimos 'lookback' dias
            avg_volume = np.mean(volumes[:-1])
            
            # Volume atual (último fechamento)
            current_volume = volumes[-1]
            
            # Calcula aumento percentual
            volume_increase = (current_volume - avg_volume) / avg_volume
            
            # Log para debug
            analysis_message = f"{symbol} - Volume: aumento de {volume_increase:.2%} | " \
                             f"Atual: {current_volume:.2f} | Média: {avg_volume:.2f}"
            self.logger.info(analysis_message)
            
            # Envia notificação se o notificador for fornecido
            if notifier:
                details = f"Aumento de volume: {volume_increase:.2%}\n" \
                         f"Volume atual: {current_volume:.2f}\n" \
                         f"Volume médio: {avg_volume:.2f} (últimos {lookback} períodos)"
                notifier.notify_analysis(symbol, "Volume", details)
            
            return {
                'avg_volume': avg_volume,
                'current_volume': current_volume,
                'volume_increase': volume_increase
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar volume para {symbol}: {str(e)}")
            return None
            
    def check_new_listing(self, symbol):
        """Verifica se é uma nova listagem na Binance ou outras exchanges"""
        # Na implementação real, usaria API para verificar listagens recentes
        # Para demonstração, simulamos uma verificação
        try:
            # Aqui seria implementada uma lógica para verificar novas listagens
            # Por exemplo, consultando CoinMarketCal ou Binance Announcements
            return False
        except Exception as e:
            self.logger.error(f"Erro ao verificar nova listagem: {str(e)}")
            return False
    
    def get_volume_data(self, symbol, notifier=None):
        """Obtém dados de volume para o par especificado
        
        Args:
            symbol (str): O par de moedas para análise
            notifier (TelegramNotifier, optional): Notificador Telegram para enviar alertas
        """
        # Este método é abstraído para facilitar os testes com mock
        return self.analyze_volume(symbol, notifier=notifier)
    
    def analyze_market(self, symbol, notifier=None):
        """Analisa o mercado usando estratégia de swing trading
        
        Critérios de entrada:
        - Volume >30% acima da média diária
        - Preço abaixo de R$1.00
        - Nova listagem (opcional)
        
        Args:
            symbol (str): O par de moedas para análise
            notifier (TelegramNotifier, optional): Notificador Telegram para enviar alertas
        """
        # Verifica limite diário de trades
        if not self.check_trade_limit():
            self.logger.info(f"Limite diário de trades atingido ({self.config.max_trades_per_day})")
            return False, None, None
        
        # Verifica se tivemos 2 prejuízos consecutivos (regra de ouro)
        if self.consecutive_losses >= 2:
            self.logger.warning(f"Pausando operações após {self.consecutive_losses} prejuízos consecutivos")
            return False, None, None
        
        # Formata o símbolo corretamente para a API
        api_symbol = symbol.replace('/', '')  # Remove a barra (ex: "BTC/USDT" -> "BTCUSDT")
        
        # Obtém preço atual
        current_price_data = self.binance.get_ticker_price(api_symbol)
        if not current_price_data:
            self.logger.warning(f"Não foi possível obter preço para {symbol} (API: {api_symbol})")
            return False, None, None
            
        current_price = float(current_price_data['price'])
        
        # Verifica se já temos posição aberta neste símbolo
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            entry_time = position['entry_time']
            time_held = (datetime.now() - entry_time).total_seconds() / 3600  # em horas
            
            # Calcula lucro percentual
            profit_percent = (current_price - position['entry_price']) / position['entry_price']
            
            # Calcula o custo das taxas (0.1% na compra e 0.1% na venda)
            fee_cost = 0.001 * 2
            net_profit_percent = profit_percent - fee_cost
            
            # Se atingiu alvo de lucro de 7-10% (considerando taxas), vende
            if net_profit_percent >= self.config.swing_trading['profit_target']:
                self.logger.info(f"{symbol} atingiu alvo de lucro: {net_profit_percent:.2%}")
                return True, "sell", current_price
                
            # Se atingiu stop loss, vende para proteger capital
            elif net_profit_percent <= -self.config.swing_trading['stop_loss']:
                self.logger.info(f"{symbol} atingiu stop loss: {net_profit_percent:.2%}")
                return True, "sell", current_price
                
            # Saída por tempo - vende após 48h independente do resultado
            elif time_held >= self.config.swing_trading['max_hold_time']:
                self.logger.info(f"{symbol} atingiu tempo máximo de posição: {time_held:.1f}h")
                return True, "sell", current_price
                
        else:
            # Verificar se o preço está abaixo de R$1.00 (filtro da fase 3)
            if current_price > 1.00 and 'BRL' in symbol:
                self.logger.info(f"Ignorando {symbol} - preço acima de R$1.00 (R${current_price:.2f})")
                return False, None, None
            
            # Analisa volume para possível entrada
            volume_data = self.analyze_volume(symbol, notifier=notifier)
            if not volume_data:
                return False, None, None
                
            # Critério 1: Volume aumentou significativamente (>30%)
            volume_increase = volume_data['volume_increase']
            has_volume_increase = volume_increase >= self.config.swing_trading['min_volume_increase']
            
            # Critério 2: Verifica se é uma nova listagem
            is_new_listing = self.check_new_listing(symbol)
            
            # Log para análise
            if has_volume_increase:
                self.logger.info(f"{symbol} - Volume aumentou {volume_increase:.2%} (>30% necessário)")
            
            if is_new_listing:
                self.logger.info(f"{symbol} - Nova listagem detectada!")
                
            # Toma decisão com base nos critérios
            if has_volume_increase or is_new_listing:
                # Esperar o tempo configurado antes de executar a entrada
                entry_delay = self.config.swing_trading['entry_delay']
                if entry_delay > 0:
                    self.logger.info(f"Aguardando {entry_delay}s antes de confirmar entrada em {symbol}")
                    time.sleep(entry_delay)
                    
                    # Verificar preço novamente para evitar mudanças drásticas durante o delay
                    updated_price_data = self.binance.get_ticker_price(symbol)
                    if updated_price_data:
                        current_price = float(updated_price_data['price'])
                
                self.logger.info(f"Entrada confirmada para {symbol} a {current_price:.8f}")
                return True, "buy", current_price
        
        return False, None, None
    
    def execute_buy(self, symbol, price):
        """Executa ordem de compra usando estratégia de swing trading
        
        Para a Fase 3 (R$300 → R$1.000):
        - Aloca no máximo 5% do capital por operação
        - Foco em altcoins com valor abaixo de R$1.00
        - Calcula taxas e registra posição para acompanhamento
        """
        try:
            # Obtém saldo da conta
            account_info = self.binance.get_account_info()
            capital = self.config.get_balance(account_info)
            
            # Limitação de posição máxima (5% do capital)
            max_position = capital * self.config.swing_trading['max_position_size']
            
            # Calcula valor de entrada considerando o stop loss
            # - Podemos perder no máximo 3% neste trade
            # - Portanto, alocamos de forma a limitar perda absoluta
            entry_value = max_position
            
            # Calcula quantidade considerando as taxas
            fee_cost = 0.001  # 0.1% de taxa na Binance
            available_for_purchase = entry_value * (1 - fee_cost)
            quantity = available_for_purchase / price
            
            # Arredonda quantidade para formato correto (depende da moeda)
            # Altcoins geralmente permitem mais casas decimais
            if price < 0.01:  # Moedas muito baratas (ex: SHIB)
                quantity = round(quantity, 0)  # Sem casas decimais
            elif price < 1:   # Moedas baratas (ex: DOGE)
                quantity = round(quantity, 2)
            else:
                quantity = round(quantity, 6)
            
            # Executa ordem de compra
            self.logger.info(f"[SWING] Comprando {quantity:.8f} de {symbol} a {price:.8f}")
            self.logger.info(f"Valor: R${entry_value:.2f} | Capital: R${capital:.2f}")
            self.logger.info(f"Alvo: +{self.config.swing_trading['profit_target']*100:.1f}% | Stop: -{self.config.swing_trading['stop_loss']*100:.1f}% | Máx: {self.config.swing_trading['max_hold_time']}h")
            
            # Formata o símbolo para a API
            api_symbol = symbol.replace('/', '')
            
            # Coloca ordem MARKET para entrada rápida (swing trading menos sensível a preço de entrada)
            order = self.binance.create_order(
                symbol=api_symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
            
            # Registra posição aberta com todos os detalhes necessários
            entry_time = datetime.now()
            expiration_time = entry_time + timedelta(hours=self.config.swing_trading['max_hold_time'])
            
            self.open_positions[symbol] = {
                'entry_price': price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'entry_time': entry_time,
                'expiration_time': expiration_time,
                'target_price': price * (1 + self.config.swing_trading['profit_target']),
                'stop_price': price * (1 - self.config.swing_trading['stop_loss'])
            }
            
            # Atualiza contador de trades
            self.record_trade()
            
            # Retorna sucesso e informações da ordem
            return True, {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'expiration_time': expiration_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao executar compra de {symbol}: {str(e)}")
            return False, None
    
    def execute_sell(self, symbol, price):
        """Executa ordem de venda usando estratégia de swing trading
        
        Para a Fase 3 (R$300 → R$1.000):
        - Vende quando atinge alvo de 7-10% de lucro
        - Ou vende após 48h (mesmo sem lucro)
        - Ou vende se atingir stop loss para proteger capital
        """
        try:
            if symbol not in self.open_positions:
                self.logger.error(f"Tentativa de venda sem posição aberta para {symbol}")
                return False, None
            
            position = self.open_positions[symbol]
            quantity = position['quantity']
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            held_time_hours = (datetime.now() - entry_time).total_seconds() / 3600
            
            # Executa ordem de venda
            self.logger.info(f"[SWING] Vendendo {quantity:.8f} de {symbol} a {price:.8f}")
            
            # Formata o símbolo para a API
            api_symbol = symbol.replace('/', '')
            
            # Coloca ordem MARKET para saída rápida
            order = self.binance.create_order(
                symbol=api_symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
            
            # Calcula resultado do trade
            profit_percent = (price - entry_price) / entry_price
            
            # Considera taxas (0.1% na compra + 0.1% na venda)
            fee_cost = 0.001 * 2
            net_profit_percent = profit_percent - fee_cost
            
            # Calcula estatísticas completas do trade
            from utils import calculate_profit
            profit_stats = calculate_profit(
                entry_price=entry_price,
                exit_price=price,
                quantity=quantity
            )
            
            # Verifica se foi lucro ou prejuízo
            if net_profit_percent > 0:
                self.logger.info(f"Trade de {symbol} finalizado com LUCRO: {net_profit_percent:.2%} (após taxas)")
                self.consecutive_losses = 0  # Reseta contador de perdas consecutivas
            else:
                self.logger.warning(f"Trade de {symbol} finalizado com PREJUÍZO: {net_profit_percent:.2%} (após taxas)")
                self.consecutive_losses += 1
                self.logger.warning(f"Perdas consecutivas: {self.consecutive_losses}")
                
                # Se atingiu 2 perdas consecutivas, notifica
                if self.consecutive_losses >= 2:
                    self.logger.warning("Atingido limite de 2 perdas consecutivas. Pausando operações conforme regra de ouro.")
            
            self.logger.info(f"Lucro líquido: R${profit_stats['net_profit']:.2f} (após taxas de R${profit_stats['total_fees']:.2f})")
            self.logger.info(f"Tempo de posição: {held_time_hours:.2f} horas")
            
            # Remove posição aberta
            del self.open_positions[symbol]
            
            # Retorna sucesso e informações da ordem
            return True, {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'profit': profit_percent,
                'profit_stats': profit_stats
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao executar venda de {symbol}: {str(e)}")
            return False, None
