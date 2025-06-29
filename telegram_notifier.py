#!/usr/bin/env python3
"""
Módulo para enviar notificações via Telegram
"""
import requests
import logging

class TelegramNotifier:
    """Classe para enviar notificações via Telegram"""
    
    def __init__(self, bot_token, chat_id):
        """Inicializa o notificador Telegram"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger("robot-crypt")
    
    def send_message(self, message):
        """Envia mensagem para o chat configurado"""
        try:
            # Sanitiza a mensagem para evitar problemas com caracteres especiais
            # quando usando parse_mode Markdown
            sanitized_message = self._sanitize_markdown(message)
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": sanitized_message,
                "parse_mode": "Markdown"  # Suporte para formatação básica
            }
            self.logger.info(f"Enviando mensagem para Telegram - URL: {url}")
            self.logger.info(f"Dados: chat_id={self.chat_id}, texto={sanitized_message[:50]}...")
            
            # Adiciona mecanismo de retry para problemas de rede
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, data=data, timeout=30)
                    self.logger.info(f"Status code resposta: {response.status_code}")
                    self.logger.info(f"Resposta: {response.text[:100]}")
                    
                    if response.status_code == 400:
                        # Se houver erro de formatação, tenta enviar sem parse_mode
                        self.logger.warning("Erro 400 ao enviar mensagem. Tentando sem formatação Markdown...")
                        data["parse_mode"] = ""
                        data["text"] = self._strip_markdown(message)  # Remove marcações de markdown
                        response = requests.post(url, data=data, timeout=30)
                        self.logger.info(f"Novo status code: {response.status_code}")
                    
                    response.raise_for_status()
                    self.logger.info("Mensagem enviada com sucesso!")
                    return True
                except requests.exceptions.Timeout:
                    wait_time = 2 ** attempt  # Backoff exponencial: 1, 2, 4 segundos
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Timeout ao enviar mensagem. Tentativa {attempt+1}/{max_retries}. Aguardando {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error("Todas as tentativas de envio falharam por timeout.")
                        return False
                except Exception as req_error:
                    self.logger.error(f"Erro na tentativa {attempt+1}: {str(req_error)}")
                    if attempt >= max_retries - 1:
                        raise
            
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação Telegram: {str(e)}")
            return False
    
    def _sanitize_markdown(self, text):
        """
        Sanitiza texto para uso com Markdown no Telegram
        Escapa caracteres especiais que podem causar problemas
        """
        if not text:
            return ""
            
        # Caracteres que precisam ser escapados no modo Markdown
        special_chars = ['_', '*', '`', '[']
        result = str(text)  # Converte para string caso não seja
        
        # Limita o tamanho da mensagem
        if len(result) > 4000:
            result = result[:3997] + "..."
        
        # Escapa caracteres especiais
        for char in special_chars:
            result = result.replace(char, f"\\{char}")
            
        return result
    
    def _strip_markdown(self, text):
        """Remove marcações de markdown do texto"""
        if not text:
            return ""
            
        result = str(text)  # Converte para string caso não seja
        
        # Remove marcações comuns de markdown
        result = result.replace("*", "")
        result = result.replace("_", "")
        result = result.replace("`", "")
        
        # Limita o tamanho da mensagem
        if len(result) > 4000:
            result = result[:3997] + "..."
            
        return result
    
    def notify_trade(self, title, detail_message=None):
        """
        Envia notificação sobre uma operação de trade
        
        Args:
            title (str): Título da notificação (ex: "� COMPRA de BTC/USDT")
            detail_message (str): Detalhes da operação (ex: "Preço: 40000.00\nQuantidade: 0.001")
        """
        try:
            message = f"*{title}*\n"
            if detail_message:
                message += detail_message
                
            self.logger.info(f"Enviando notificação Telegram: {title}")
            return self.send_message(message)
        except Exception as e:
            self.logger.error(f"Erro ao formatar notificação de trade: {str(e)}")
            return False
    
    def notify_error(self, error_message):
        """Envia notificação sobre um erro"""
        # Limita o tamanho da mensagem de erro para evitar problemas
        if error_message and len(error_message) > 200:
            short_error = error_message[:197] + "..."
        else:
            short_error = error_message
            
        message = f"❗ *ERRO*\n{short_error}"
        return self.send_message(message)
    
    def notify_status(self, status_message):
        """Envia notificação sobre status do bot"""
        message = f"ℹ️ *STATUS*\n{status_message}"
        return self.send_message(message)
    
    def notify_portfolio_summary(self, initial_capital, current_capital, total_trades, profit_trades, loss_trades):
        """Envia resumo do desempenho do portfólio"""
        profit_percentage = ((current_capital / initial_capital) - 1) * 100
        profit_ratio = profit_trades / total_trades if total_trades > 0 else 0
        
        message = f"📊 *RESUMO DO PORTFÓLIO*\n\n"
        message += f"Capital inicial: R$ {initial_capital:.2f}\n"
        message += f"Capital atual: R$ {current_capital:.2f}\n"
        message += f"Desempenho: {profit_percentage:+.2f}%\n\n"
        message += f"Total de operações: {total_trades}\n"
        message += f"Operações com lucro: {profit_trades} ({profit_ratio*100:.1f}%)\n"
        message += f"Operações com prejuízo: {loss_trades} ({(1-profit_ratio)*100:.1f}%)\n"
        
        return self.send_message(message)
    
    def notify_market_alert(self, symbol, alert_type, message):
        """Envia alerta sobre condições de mercado"""
        alert_emoji = "🔔"
        if alert_type.lower() == "bullish":
            alert_emoji = "🟢"
        elif alert_type.lower() == "bearish":
            alert_emoji = "🔴"
        elif alert_type.lower() == "volatility":
            alert_emoji = "⚡"
            
        formatted_message = f"{alert_emoji} *ALERTA DE MERCADO - {symbol}*\n{message}"
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
            emoji = "🔍"
            if data_type.lower() == "volume":
                emoji = "📊"
            elif data_type.lower() == "price":
                emoji = "💲"
            elif data_type.lower() == "indicator":
                emoji = "📈"
                
            message = f"{emoji} *ANÁLISE - {symbol}*\n"
            message += f"*Tipo*: {data_type}\n"
            message += f"{details}"
            
            return self.send_message(message)
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de análise: {str(e)}")
            return False
