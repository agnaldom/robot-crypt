#!/usr/bin/env python3
"""
Módulo para enviar notificações via Telegram
"""
import requests
import logging
import urllib3
import os
import json
from datetime import datetime

# Configurando verificação SSL de forma mais segura
import certifi

# Importa o notificador local como fallback
try:
    from .local_notifier import LocalNotifier
except ImportError:
    LocalNotifier = None

# Importa o gerenciador PostgreSQL se estiver disponível
try:
    from ..database.postgres_manager import PostgresManager
    postgres_available = True
except ImportError:
    postgres_available = False

class TelegramNotifier:
    """Classe para enviar notificações via Telegram"""
    
    def __init__(self, bot_token, chat_id):
        """Inicializa o notificador Telegram"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger("robot-crypt")
        
        # Inicializa o notificador local como fallback
        self.use_fallback = False
        self.telegram_available = True
        
        # Inicializa o notificador local
        try:
            if LocalNotifier:
                self.local_notifier = LocalNotifier()
                self.logger.info("Notificador local inicializado como fallback para Telegram")
            else:
                self.local_notifier = None
                self.logger.warning("LocalNotifier não disponível, fallback não será usado")
        except Exception as e:
            self.local_notifier = None
            self.logger.error(f"Erro ao inicializar notificador local: {str(e)}")
            
        # Inicializa o PostgresManager para persistência se disponível
        self.postgres = None
        if postgres_available:
            try:
                self.postgres = PostgresManager()
                self.logger.info("PostgresManager inicializado para armazenamento de notificações e análises")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar PostgresManager: {str(e)}")
                self.logger.warning("Armazenamento em PostgreSQL não estará disponível")
        
        # Informação sobre a configuração SSL
        self.logger.info("Configuração SSL utilizando certificados do certifi para requisições ao Telegram")
    
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
                    # Usando o caminho para os certificados CA confiáveis do certifi
                    response = requests.post(url, data=data, timeout=30, verify=certifi.where())
                    self.logger.info(f"Status code resposta: {response.status_code}")
                    self.logger.info(f"Resposta: {response.text[:100]}")
                    
                    if response.status_code == 400:
                        # Se houver erro de formatação, tenta enviar sem parse_mode
                        self.logger.warning("Erro 400 ao enviar mensagem. Tentando sem formatação Markdown...")
                        data["parse_mode"] = ""
                        data["text"] = self._strip_markdown(message)  # Remove marcações de markdown
                        response = requests.post(url, data=data, timeout=30, verify=certifi.where())
                        self.logger.info(f"Novo status code: {response.status_code}")
                    
                    response.raise_for_status()
                    
                    # Verifica se a resposta contém indicação de bloqueio do Cloudflare
                    # ou se não é uma resposta JSON válida da API do Telegram
                    try:
                        json_response = response.json()
                        if "Blocked by Cloudflare Gateway" in response.text or not json_response.get("ok"):
                            self.logger.warning("Cloudflare Gateway está bloqueando o acesso à API do Telegram")
                            self.logger.warning("O status da requisição foi 200, mas o conteúdo está sendo bloqueado")
                            self.logger.warning("Verificação de rede falhou, usando notificador local como fallback")
                            self.use_fallback = True
                            self.telegram_available = False
                            
                            # Usa fallback para notificação local
                            if self.local_notifier:
                                self.logger.info("Usando notificador local como fallback")
                                return self.local_notifier.send_message(self._strip_markdown(message))
                            return False
                    except ValueError:
                        self.logger.warning("A resposta da API do Telegram não é um JSON válido")
                        self.logger.warning("Isto pode indicar um bloqueio de rede ou firewall")
                        self.use_fallback = True
                        self.telegram_available = False
                        
                        # Usa fallback para notificação local
                        if self.local_notifier:
                            self.logger.info("Usando notificador local como fallback")
                            return self.local_notifier.send_message(self._strip_markdown(message))
                        return False
                        
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
            
            # Usar fallback local se o Telegram falhou
            self.use_fallback = True
            self.telegram_available = False
            if self.local_notifier:
                self.logger.info("Usando notificador local como fallback após falhas repetidas")
                return self.local_notifier.send_message(self._strip_markdown(message))
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação Telegram: {str(e)}")
            # Usar fallback local em caso de exceção
            self.use_fallback = True
            if self.local_notifier:
                self.logger.info("Usando notificador local como fallback após exceção")
                return self.local_notifier.send_message(self._strip_markdown(message))
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
    
    def notify_trade(self, title, detail_message=None, trade_data=None):
        """
        Envia notificação sobre uma operação de trade com formatação rica e estruturada
        
        Args:
            title (str): Título da notificação (ex: "COMPRA de BTC/USDT")
            detail_message (str): Detalhes da operação (opcional)
            trade_data (dict): Dicionário com dados adicionais da operação (opcional)
                Pode incluir: symbol, price, quantity, order_type, side, profit_loss, 
                reason, indicators, risk_reward_ratio, timeframe, strategy_name, etc.
        """
        try:
            # Determina emoji baseado no tipo de operação
            emoji = "🔄"  # Padrão para operações genéricas
            if "COMPRA" in title.upper():
                emoji = "🟢" # Verde para compras
            elif "VENDA" in title.upper():
                emoji = "🔴" # Vermelho para vendas
            elif "ERRO" in title.upper():
                emoji = "⚠️" # Aviso para erros
            elif "CANCELAMENTO" in title.upper():
                emoji = "🚫" # Cancelamento de ordem
            elif "LIMITE" in title.upper():
                emoji = "⏳" # Ordem limite
            
            # Formata o título com data/hora
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            message = f"{emoji} *{title}* - {current_time}\n\n"
            
            # Adiciona detalhes formatados se fornecidos
            if detail_message:
                message += f"{detail_message}\n\n"
                
            # Adiciona informações estruturadas se trade_data for fornecido
            if trade_data and isinstance(trade_data, dict):
                # Seção de dados principais da operação
                message += "🔹 *DETALHES DA OPERAÇÃO* 🔹\n"
                
                # Dados essenciais da operação
                if 'symbol' in trade_data:
                    message += f"📊 *Par:* `{trade_data['symbol']}`\n"
                if 'price' in trade_data:
                    message += f"💰 *Preço:* `{trade_data['price']}`\n"
                if 'quantity' in trade_data:
                    message += f"🔢 *Quantidade:* `{trade_data['quantity']}`\n"
                if 'order_type' in trade_data:
                    message += f"📋 *Tipo:* `{trade_data['order_type']}`\n"
                if 'timeframe' in trade_data:
                    message += f"⏱️ *Timeframe:* `{trade_data['timeframe']}`\n"
                if 'strategy_name' in trade_data:
                    message += f"🧠 *Estratégia:* `{trade_data['strategy_name']}`\n"
                message += "\n"
                
                # Dados de P&L se disponíveis
                if 'profit_loss' in trade_data:
                    pl = trade_data['profit_loss']
                    pl_emoji = "✅" if pl > 0 else "❌" if pl < 0 else "➖"
                    
                    # Barra de progresso visual para o P&L
                    progress_bar = ""
                    if pl > 0:
                        bars = min(int(pl / 2), 10) if pl < 20 else 10
                        progress_bar = "🟩" * bars + "⬜" * (10 - bars)
                    elif pl < 0:
                        bars = min(int(abs(pl) / 2), 10) if abs(pl) < 20 else 10
                        progress_bar = "🟥" * bars + "⬜" * (10 - bars)
                    else:
                        progress_bar = "⬜" * 10
                        
                    message += f"💹 *P&L:* {pl_emoji} `{pl:.2f}%`\n{progress_bar}\n\n"
                
                # Razão da operação
                if 'reason' in trade_data:
                    message += "🔍 *RAZÃO DA OPERAÇÃO*\n"
                    message += f"`{trade_data['reason']}`\n\n"
                
                # Dados de indicadores técnicos usados
                if 'indicators' in trade_data and trade_data['indicators']:
                    message += "📈 *INDICADORES TÉCNICOS*\n"
                    for indicator, value in trade_data['indicators'].items():
                        message += f"• *{indicator}:* `{value}`\n"
                    message += "\n"
                
                # Proporção risco/recompensa
                if 'risk_reward_ratio' in trade_data:
                    message += "⚖️ *ANÁLISE DE RISCO*\n"
                    message += f"• *Risco/Recompensa:* `{trade_data['risk_reward_ratio']}`\n\n"
            
            # Salvar no PostgreSQL se disponível
            if self.postgres:
                full_message = detail_message if detail_message else ""
                notification_sent = False  # Será atualizado após tentativa de envio
                notification_id = self.postgres.save_notification("trade", title, full_message, notification_sent)
                self.logger.info(f"Notificação de trade salva no PostgreSQL (ID: {notification_id})")
            
            # Se o Telegram já foi identificado como indisponível, usa direto o fallback
            if self.use_fallback and self.local_notifier:
                self.logger.info(f"Usando notificador local para trade: {title}")
                result = self.local_notifier.notify_trade(title, detail_message)
                
                # Atualiza status no PostgreSQL se disponível
                # Esta funcionalidade ainda seria implementada no PostgresManager
                
                return result
            
            self.logger.info(f"Enviando notificação Telegram: {title}")
            result = self.send_message(message)
            
            # Atualiza status da notificação no PostgreSQL
            # Esta funcionalidade ainda seria implementada no PostgresManager
            
            return result
        except Exception as e:
            self.logger.error(f"Erro ao formatar notificação de trade: {str(e)}")
            # Tenta usar o notificador local como fallback
            if self.local_notifier:
                return self.local_notifier.notify_trade(title, detail_message)
            return False
    
    def notify_error(self, error_message, error_traceback=None, component=None):
        """Envia notificação sobre um erro com informações detalhadas
        
        Args:
            error_message (str): Mensagem principal do erro
            error_traceback (str, optional): Traceback completo do erro
            component (str, optional): Componente do sistema onde ocorreu o erro
        """
        # Limita o tamanho da mensagem de erro para evitar problemas
        if error_message and len(error_message) > 200:
            short_error = error_message[:197] + "..."
        else:
            short_error = error_message
        
        # Se o Telegram já foi identificado como indisponível, usa direto o fallback
        if self.use_fallback and self.local_notifier:
            self.logger.info("Usando notificador local para erro")
            return self.local_notifier.notify_error(short_error, error_traceback, component)
        
        # Formata a hora atual    
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Prepara a mensagem formatada
        message = f"❗ *ERRO DETECTADO* - {current_time}\n\n"
        
        # Adiciona o componente se fornecido
        if component:
            message += f"🔧 *Componente:* `{component}`\n\n"
            
        # Adiciona a mensagem de erro principal
        message += f"⚠️ *Mensagem:* `{short_error}`\n"
        
        # Adiciona traceback limitado se fornecido
        if error_traceback:
            # Limita o traceback para não exceder limites do Telegram
            if len(error_traceback) > 500:
                short_traceback = error_traceback[:497] + "..."
            else:
                short_traceback = error_traceback
                
            message += f"\n📋 *Stack Trace:*\n`{short_traceback}`\n"
        
        # Adiciona nota sobre ações sendo tomadas
        message += "\n🛠️ *Ação:* O sistema continuará tentando operar. Verifique os logs para mais detalhes."
        
        return self.send_message(message)
    
    def notify_status(self, status_message, status_details=None, status_type="info"):
        """Envia notificação sobre status do bot com informações detalhadas
        
        Args:
            status_message (str): Mensagem principal de status
            status_details (dict, optional): Detalhes adicionais do status
            status_type (str, optional): Tipo de status ("info", "warning", "success")
        """
        # Se o Telegram já foi identificado como indisponível, usa direto o fallback
        if self.use_fallback and self.local_notifier:
            self.logger.info("Usando notificador local para status")
            return self.local_notifier.notify_status(status_message, status_details, status_type)
        
        # Seleciona emoji com base no tipo de status
        status_emoji = "ℹ️" # info (padrão)
        if status_type.lower() == "warning":
            status_emoji = "⚠️" # warning
        elif status_type.lower() == "success":
            status_emoji = "✅" # success
        elif status_type.lower() == "update":
            status_emoji = "🔄" # update
        elif status_type.lower() == "system":
            status_emoji = "🖥️" # system
            
        # Formata a hora atual
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Cria a mensagem formatada
        message = f"{status_emoji} *STATUS DO SISTEMA* - {current_time}\n\n"
        message += f"{status_message}\n"
        
        # Adiciona detalhes se fornecidos
        if status_details and isinstance(status_details, dict):
            message += "\n📊 *Detalhes:*\n"
            
            for key, value in status_details.items():
                # Formata diferentes tipos de campos
                if key.lower() in ["uptime", "tempo", "duração"]:
                    message += f"⏱️ *{key}:* `{value}`\n"
                elif key.lower() in ["memória", "memory", "ram"]:
                    message += f"💾 *{key}:* `{value}`\n"
                elif key.lower() in ["cpu", "processador"]:
                    message += f"🔄 *{key}:* `{value}`\n"
                elif key.lower() in ["operações", "trades", "orders"]:
                    message += f"📈 *{key}:* `{value}`\n"
                elif key.lower() in ["conexão", "connection", "latência", "latency"]:
                    message += f"🌐 *{key}:* `{value}`\n"
                else:
                    message += f"• *{key}:* `{value}`\n"
        
        return self.send_message(message)
    
    def notify_portfolio_summary(self, initial_capital, current_capital, total_trades, profit_trades, loss_trades, additional_metrics=None):
        """Envia resumo do desempenho do portfólio com visualização melhorada
        
        Args:
            initial_capital (float): Capital inicial
            current_capital (float): Capital atual
            total_trades (int): Total de operações realizadas
            profit_trades (int): Número de operações lucrativas
            loss_trades (int): Número de operações com prejuízo
            additional_metrics (dict, optional): Métricas adicionais a serem exibidas
        """
        # Cálculo de métricas básicas
        profit_percentage = ((current_capital / initial_capital) - 1) * 100
        profit_ratio = profit_trades / total_trades if total_trades > 0 else 0
        
        # Formata a hora atual
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Define o emoji principal com base no desempenho
        main_emoji = "📊" if profit_percentage >= 0 else "📉"
        
        # Cria a mensagem formatada
        message = f"{main_emoji} *RESUMO DO PORTFÓLIO* - {current_time}\n\n"
        
        # Seção de capital
        message += "💰 *CAPITAL*\n"
        message += f"• *Inicial:* `R$ {initial_capital:.2f}`\n"
        message += f"• *Atual:* `R$ {current_capital:.2f}`\n"
        
        # Barra de progresso visual para o desempenho
        if profit_percentage >= 0:
            bars = min(int(profit_percentage / 2), 10) if profit_percentage < 20 else 10
            progress_bar = "🟩" * bars + "⬜" * (10 - bars)
            performance_emoji = "✅"
        else:
            bars = min(int(abs(profit_percentage) / 2), 10) if abs(profit_percentage) < 20 else 10
            progress_bar = "🟥" * bars + "⬜" * (10 - bars)
            performance_emoji = "❌"
            
        message += f"• *Desempenho:* {performance_emoji} `{profit_percentage:+.2f}%`\n"
        message += f"{progress_bar}\n\n"
        
        # Seção de estatísticas de trades
        message += "📈 *ESTATÍSTICAS DE TRADES*\n"
        message += f"• *Total de operações:* `{total_trades}`\n"
        
        # Gráfico visual da proporção de trades com lucro/prejuízo
        if total_trades > 0:
            profit_blocks = int((profit_trades / total_trades) * 10)
            loss_blocks = 10 - profit_blocks
            win_loss_chart = "🟢" * profit_blocks + "🔴" * loss_blocks
            
            message += f"• *Operações lucrativas:* `{profit_trades} ({profit_ratio*100:.1f}%)`\n"
            message += f"• *Operações com prejuízo:* `{loss_trades} ({(1-profit_ratio)*100:.1f}%)`\n"
            message += f"{win_loss_chart}\n\n"
        else:
            message += "• *Nenhuma operação realizada*\n\n"
        
        # Adiciona métricas adicionais se fornecidas
        if additional_metrics and isinstance(additional_metrics, dict):
            message += "📊 *MÉTRICAS ADICIONAIS*\n"
            
            for key, value in additional_metrics.items():
                # Formata diferentes tipos de métricas
                if key.lower() in ["drawdown", "drawdown_máximo"]:
                    message += f"• *{key}:* `{value:.2f}%`\n"
                elif key.lower() in ["sharpe_ratio", "índice_sharpe"]:
                    message += f"• *{key}:* `{value:.2f}`\n"
                elif key.lower() in ["tempo_médio_trade", "duração_média"]:
                    message += f"• *{key}:* `{value}`\n"
                else:
                    message += f"• *{key}:* `{value}`\n"
                    
            message += "\n"
        
        return self.send_message(message)
    
    def notify_market_alert(self, symbol, alert_type, message, alert_data=None):
        """Envia alerta sobre condições de mercado com detalhes formatados
        
        Args:
            symbol (str): Par de trading (ex: "BTC/USDT")
            alert_type (str): Tipo de alerta ("bullish", "bearish", "volatility", "breakout", etc)
            message (str): Descrição principal do alerta
            alert_data (dict, optional): Dados adicionais sobre o alerta (preços, indicadores, etc)
        """
        # Determina o emoji baseado no tipo de alerta
        alert_emoji = "🔔" # Padrão
        if alert_type.lower() == "bullish":
            alert_emoji = "🟢" # Tendência de alta
        elif alert_type.lower() == "bearish":
            alert_emoji = "🔴" # Tendência de baixa
        elif alert_type.lower() == "volatility":
            alert_emoji = "⚡" # Alta volatilidade
        elif alert_type.lower() == "breakout":
            alert_emoji = "💥" # Rompimento de nível
        elif alert_type.lower() == "reversal":
            alert_emoji = "🔄" # Reversão de tendência
        elif alert_type.lower() == "consolidation":
            alert_emoji = "⏸️" # Consolidação
        
        # Formata a hora atual
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Cria a mensagem formatada
        formatted_message = f"{alert_emoji} *ALERTA DE MERCADO - {symbol}* - {current_time}\n\n"
        formatted_message += f"*Tipo:* {alert_type.upper()}\n\n"
        formatted_message += f"{message}\n"
        
        # Adiciona dados adicionais se fornecidos
        if alert_data and isinstance(alert_data, dict):
            formatted_message += "\n📊 *DADOS TÉCNICOS*\n"
            
            # Formata diferentes tipos de dados
            if 'price' in alert_data:
                formatted_message += f"• *Preço atual:* `{alert_data['price']}`\n"
            
            if 'volume' in alert_data:
                formatted_message += f"• *Volume:* `{alert_data['volume']}`\n"
                
            if 'resistance' in alert_data and 'support' in alert_data:
                formatted_message += f"• *Resistência:* `{alert_data['resistance']}`\n"
                formatted_message += f"• *Suporte:* `{alert_data['support']}`\n"
                
            # Adiciona outros indicadores técnicos relevantes
            for key, value in alert_data.items():
                if key not in ['price', 'volume', 'resistance', 'support']:
                    formatted_message += f"• *{key}:* `{value}`\n"
                    
            formatted_message += "\n"
            
            # Adiciona níveis de ação recomendados se disponíveis
            if 'action_levels' in alert_data and isinstance(alert_data['action_levels'], dict):
                formatted_message += "🎯 *NÍVEIS DE AÇÃO RECOMENDADOS*\n"
                
                if 'entry' in alert_data['action_levels']:
                    formatted_message += f"• *Entrada:* `{alert_data['action_levels']['entry']}`\n"
                    
                if 'take_profit' in alert_data['action_levels']:
                    formatted_message += f"• *Take Profit:* `{alert_data['action_levels']['take_profit']}`\n"
                    
                if 'stop_loss' in alert_data['action_levels']:
                    formatted_message += f"• *Stop Loss:* `{alert_data['action_levels']['stop_loss']}`\n"
        
        return self.send_message(formatted_message)
        
    def notify_analysis(self, symbol, data_type, details, chart_data=None, timeframe=None):
        """
        Envia notificação sobre uma análise de mercado com detalhes formatados
        
        Args:
            symbol (str): O par de moedas analisado (ex: "BTC/USDT")
            data_type (str): Tipo de análise (ex: "Volume", "RSI", "MACD")
            details (str): Detalhes da análise
            chart_data (dict, optional): Dados de gráficos e indicadores para visualização
            timeframe (str, optional): Timeframe da análise (ex: "1h", "4h", "1d")
        """
        try:
            # Seleciona emoji baseado no tipo de análise
            emoji = "🔍" # Padrão para análises genéricas
            if data_type.lower() == "volume":
                emoji = "📊" # Volume
            elif data_type.lower() == "price":
                emoji = "💲" # Preço
            elif data_type.lower() == "indicator" or data_type.lower() == "indicador":
                emoji = "📈" # Indicador técnico
            elif data_type.lower() == "pattern" or data_type.lower() == "padrão":
                emoji = "📋" # Padrão gráfico
            elif data_type.lower() == "sentiment" or data_type.lower() == "sentimento":
                emoji = "🧠" # Análise de sentimento
            elif data_type.lower() == "fundamental":
                emoji = "📑" # Análise fundamentalista
            
            # Formata a hora atual
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Formata o timeframe se fornecido
            timeframe_str = f" ({timeframe})" if timeframe else ""
            
            # Cria a mensagem formatada
            message = f"{emoji} *ANÁLISE TÉCNICA - {symbol}{timeframe_str}* - {current_time}\n\n"
            message += f"*Tipo de análise:* {data_type}\n\n"
            message += f"{details}\n"
            
            # Salvar análise no PostgreSQL se disponível
            analysis_data = {
                'symbol': symbol,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            if hasattr(self, 'postgres_manager') and self.postgres_manager:
                try:
                    analysis_id = self.postgres_manager.save_analysis(
                        symbol=symbol,
                        analysis_type=data_type,
                        data=analysis_data
                    )
                    if analysis_id:
                        self.logger.info(f"Análise de {symbol} ({data_type}) salva no PostgreSQL (ID: {analysis_id})")
                except Exception as db_err:
                    self.logger.error(f"Erro ao salvar análise no PostgreSQL: {str(db_err)}")
                    
            # Adiciona dados do gráfico/indicadores se fornecidos
            if chart_data and isinstance(chart_data, dict):
                message += "\n📊 *DADOS TÉCNICOS*\n"
                
                # Processa diferentes tipos de dados técnicos
                if 'price_data' in chart_data:
                    price_data = chart_data['price_data']
                    message += f"• *Preço atual:* `{price_data.get('current', 'N/A')}`\n"
                    message += f"• *Variação 24h:* `{price_data.get('change_24h', 'N/A')}%`\n"
                    
                    if 'high_low' in price_data:
                        message += f"• *Máxima/Mínima:* `{price_data['high_low'].get('high', 'N/A')}/{price_data['high_low'].get('low', 'N/A')}`\n"
                
                # Adiciona indicadores técnicos
                if 'indicators' in chart_data and isinstance(chart_data['indicators'], dict):
                    message += "\n📈 *INDICADORES*\n"
                    for indicator, value in chart_data['indicators'].items():
                        # Formata com base no tipo de indicador
                        if indicator.lower() in ["rsi", "stoch", "cci"]:
                            # Adiciona emojis baseados em condições de sobrecompra/sobrevenda
                            indicator_value = float(value) if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()) else 0
                            emoji = "➖"
                            if indicator.lower() == "rsi":
                                emoji = "⤴️" if indicator_value > 70 else "⤵️" if indicator_value < 30 else "➖"
                            elif indicator.lower() == "stoch":
                                emoji = "⤴️" if indicator_value > 80 else "⤵️" if indicator_value < 20 else "➖"
                            message += f"• *{indicator}:* {emoji} `{value}`\n"
                        else:
                            message += f"• *{indicator}:* `{value}`\n"
                            
                # Adiciona níveis técnicos importantes
                if 'key_levels' in chart_data and isinstance(chart_data['key_levels'], dict):
                    message += "\n🎯 *NÍVEIS TÉCNICOS*\n"
                    if 'resistance' in chart_data['key_levels']:
                        message += f"• *Resistência:* `{chart_data['key_levels']['resistance']}`\n"
                    if 'support' in chart_data['key_levels']:
                        message += f"• *Suporte:* `{chart_data['key_levels']['support']}`\n"
                    if 'pivot' in chart_data['key_levels']:
                        message += f"• *Pivot:* `{chart_data['key_levels']['pivot']}`\n"
                        
                # Adiciona sinais e recomendações se disponíveis
                if 'signals' in chart_data and isinstance(chart_data['signals'], dict):
                    # Determina a força do sinal
                    signal_strength = chart_data['signals'].get('strength', 0)
                    signal_direction = chart_data['signals'].get('direction', 'neutral')
                    
                    signal_emoji = "➖" # neutro
                    if signal_direction.lower() == 'buy':
                        signal_emoji = "🟢" # compra
                        strength_bar = "🟩" * min(int(signal_strength), 5) + "⬜" * (5 - min(int(signal_strength), 5))
                    elif signal_direction.lower() == 'sell':
                        signal_emoji = "🔴" # venda
                        strength_bar = "🟥" * min(int(signal_strength), 5) + "⬜" * (5 - min(int(signal_strength), 5))
                    else:
                        strength_bar = "⬜" * 5
                        
                    message += "\n⚡ *SINAIS TÉCNICOS*\n"
                    message += f"• *Direção:* {signal_emoji} `{signal_direction.upper()}`\n"
                    message += f"• *Força do sinal:* {strength_bar} (`{signal_strength}/5`)\n"
                    
                    if 'recommendation' in chart_data['signals']:
                        message += f"• *Recomendação:* `{chart_data['signals']['recommendation']}`\n"
            
            # Tentar enviar pelo Telegram
            telegram_sent = self.send_message(message)
            
            # Se falhar, tentar enviar pelo notificador local se disponível
            if not telegram_sent and hasattr(self, 'local_notifier') and self.local_notifier:
                self.logger.info("Enviando notificação de análise por fallback local")
                self.local_notifier.notify_analysis(symbol, data_type, details, chart_data, timeframe)
                
            # Atualizar status de envio no PostgreSQL se disponível
            if hasattr(self, 'postgres_manager') and self.postgres_manager and analysis_id:
                try:
                    self.postgres_manager.update_analysis_status(analysis_id, telegram_sent)
                except Exception as update_err:
                    self.logger.error(f"Erro ao atualizar status da análise no PostgreSQL: {str(update_err)}")
            
            return telegram_sent
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de análise: {str(e)}")
            return False
            
    def send_inline_keyboard(self, message, buttons, chat_id=None):
        """
        Envia uma mensagem com botões inline interativos no Telegram
        
        Args:
            message (str): Texto da mensagem principal
            buttons (list): Lista de dicionários com os botões no formato:
                [{"text": "Label do botão", "callback_data": "dados_callback"}]
                Pode ser estruturada em linhas: [[btn1, btn2], [btn3, btn4]]
            chat_id (str, optional): ID do chat para envio. Se não fornecido, usa o padrão.
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            # Usa o chat_id padrão se não especificado
            if not chat_id:
                chat_id = self.chat_id
                
            # Sanitiza a mensagem para evitar problemas com formatação Markdown
            sanitized_message = self._sanitize_markdown(message)
            
            # Prepara o teclado inline
            markup = {"inline_keyboard": []}
            
            # Processa os botões - aceita tanto formato simples quanto por linhas
            if buttons and isinstance(buttons, list):
                if all(isinstance(btn, dict) for btn in buttons):
                    # Formato simples: todos os botões em uma linha
                    markup["inline_keyboard"].append(buttons)
                elif all(isinstance(row, list) for row in buttons):
                    # Formato por linhas: cada sublist é uma linha de botões
                    markup["inline_keyboard"] = buttons
                    
            # Prepara a requisição
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": sanitized_message,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(markup)
            }
            
            self.logger.info(f"Enviando mensagem com teclado inline para Telegram - URL: {url}")
            
            # Envia a requisição com verificação SSL usando certifi
            response = requests.post(url, data=data, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem com teclado inline: {str(e)}")
            return False
            
    def send_trade_confirmation(self, trade_info, require_confirmation=True):
        """
        Envia uma notificação de trade com botões de confirmação
        
        Args:
            trade_info (dict): Informações sobre o trade proposto
            require_confirmation (bool): Se True, adiciona botões de confirmação
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            # Prepara a mensagem de trade
            title = f"PROPOSTA DE {trade_info.get('side', '').upper()} - {trade_info.get('symbol', 'N/A')}"
            
            # Determina emoji baseado no tipo de operação
            emoji = "🔄"  # Padrão
            if trade_info.get('side', '').upper() == "COMPRA":
                emoji = "🟢"
            elif trade_info.get('side', '').upper() == "VENDA":
                emoji = "🔴"
                
            # Formata a hora atual
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            message = f"{emoji} *{title}* - {current_time}\n\n"
            
            # Adiciona dados do trade
            message += "🔹 *DETALHES DA OPERAÇÃO PROPOSTA* 🔹\n"
            message += f"📊 *Par:* `{trade_info.get('symbol', 'N/A')}`\n"
            message += f"💰 *Preço:* `{trade_info.get('price', 'N/A')}`\n"
            message += f"🔢 *Quantidade:* `{trade_info.get('quantity', 'N/A')}`\n"
            
            if 'reason' in trade_info:
                message += f"\n🔍 *Razão:* `{trade_info['reason']}`\n"
                
            # Adiciona dados de risco
            if 'risk_info' in trade_info and isinstance(trade_info['risk_info'], dict):
                message += "\n⚠️ *INFORMAÇÕES DE RISCO*\n"
                risk_info = trade_info['risk_info']
                
                if 'stop_loss' in risk_info:
                    message += f"• *Stop Loss:* `{risk_info['stop_loss']}`\n"
                if 'take_profit' in risk_info:
                    message += f"• *Take Profit:* `{risk_info['take_profit']}`\n"
                if 'risk_reward' in risk_info:
                    message += f"• *Risco/Recompensa:* `{risk_info['risk_reward']}`\n"
                    
            # Adiciona mensagem de ação requerida se confirmação for necessária
            if require_confirmation:
                message += "\n⚡ *AÇÃO REQUERIDA*\n"
                message += "Por favor confirme ou cancele esta operação usando os botões abaixo.\n"
                
                # Prepara os botões
                confirm_button = {"text": "✅ Confirmar", "callback_data": f"confirm_trade_{trade_info.get('id', 'default')}"}
                cancel_button = {"text": "❌ Cancelar", "callback_data": f"cancel_trade_{trade_info.get('id', 'default')}"}
                buttons = [[confirm_button, cancel_button]]
                
                # Envia a mensagem com os botões
                return self.send_inline_keyboard(message, buttons)
            else:
                # Envia mensagem normal sem botões
                return self.send_message(message)
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar confirmação de trade: {str(e)}")
            return False
