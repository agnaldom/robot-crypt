#!/usr/bin/env python3
"""
Módulo para enviar notificações localmente quando o Telegram estiver bloqueado
"""
import os
import logging
import time
from datetime import datetime
from pathlib import Path

class LocalNotifier:
    """Classe para enviar notificações localmente quando o Telegram estiver bloqueado"""
    
    def __init__(self):
        """Inicializa o notificador local"""
        self.logger = logging.getLogger("robot-crypt")
        self.notification_dir = Path(__file__).parent / "notifications"
        self.notification_dir.mkdir(exist_ok=True, parents=True)
        self.logger.info(f"Notificador local inicializado. Notificações serão salvas em: {self.notification_dir}")
    
    def _create_visual_separator(self):
        """Cria um separador visual para destacar a notificação no console"""
        separator = "=" * 80
        self.logger.info("\n" + separator)
        self.logger.info("🔔 NOTIFICAÇÃO LOCAL 🔔")
        self.logger.info(separator)
    
    def send_message(self, message):
        """Envia mensagem para o console e salva em arquivo"""
        try:
            # Exibe visualmente no console
            self._create_visual_separator()
            self.logger.info(message)
            self.logger.info("=" * 80 + "\n")
            
            # Salva a notificação em arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            notification_file = self.notification_dir / f"notification_{timestamp}.txt"
            
            with open(notification_file, 'w', encoding='utf-8') as f:
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mensagem: {message}\n")
                
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação local: {str(e)}")
            return False
    
    def notify_trade(self, title, detail_message=None):
        """
        Envia notificação sobre uma operação de trade
        
        Args:
            title (str): Título da notificação (ex: "COMPRA de BTC/USDT")
            detail_message (str): Detalhes da operação (ex: "Preço: 40000.00\nQuantidade: 0.001")
        """
        try:
            message = f"TRADE: {title}\n"
            if detail_message:
                message += detail_message
                
            self.logger.info(f"Enviando notificação local para trade: {title}")
            return self.send_message(message)
        except Exception as e:
            self.logger.error(f"Erro ao formatar notificação local de trade: {str(e)}")
            return False
    
    def notify_error(self, error_message):
        """Envia notificação sobre um erro"""
        message = f"ERRO: {error_message}"
        return self.send_message(message)
    
    def notify_status(self, status_message):
        """Envia notificação sobre status do bot"""
        message = f"STATUS: {status_message}"
        return self.send_message(message)
    
    def notify_portfolio_summary(self, initial_capital, current_capital, total_trades, profit_trades, loss_trades):
        """Envia resumo do desempenho do portfólio"""
        profit_percentage = ((current_capital / initial_capital) - 1) * 100
        profit_ratio = profit_trades / total_trades if total_trades > 0 else 0
        
        message = f"RESUMO DO PORTFÓLIO:\n\n"
        message += f"Capital inicial: R$ {initial_capital:.2f}\n"
        message += f"Capital atual: R$ {current_capital:.2f}\n"
        message += f"Desempenho: {profit_percentage:+.2f}%\n\n"
        message += f"Total de operações: {total_trades}\n"
        message += f"Operações com lucro: {profit_trades} ({profit_ratio*100:.1f}%)\n"
        message += f"Operações com prejuízo: {loss_trades} ({(1-profit_ratio)*100:.1f}%)\n"
        
        return self.send_message(message)
        
    def notify_market_alert(self, symbol, alert_type, message):
        """Envia alerta sobre condições de mercado"""
        formatted_message = f"ALERTA DE MERCADO - {symbol}\n{message}"
        return self.send_message(formatted_message)
        
    def notify_analysis(self, symbol, data_type, details):
        """
        Envia notificação sobre uma análise de mercado
        
        Args:
            symbol (str): O par de moedas analisado (ex: "BTC/USDT")
            data_type (str): Tipo de análise (ex: "Volume", "RSI", "MACD")
            details (str): Detalhes da análise
        """
        try:
            message = f"ANÁLISE - {symbol}\n"
            message += f"Tipo: {data_type}\n"
            message += f"{details}"
            
            return self.send_message(message)
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de análise: {str(e)}")
            return False
