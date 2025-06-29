#!/usr/bin/env python3
"""
Módulo para geração de relatórios gráficos para o Robot-Crypt
"""
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

class ReportGenerator:
    """Gerador de relatórios gráficos para o Robot-Crypt"""
    
    def __init__(self, db_manager=None):
        """Inicializa o gerador de relatórios
        
        Args:
            db_manager: Instância do DBManager para acessar dados históricos
        """
        self.logger = logging.getLogger("robot-crypt")
        self.db_manager = db_manager
        # Diretório onde os relatórios serão salvos
        self.report_dir = Path(__file__).parent / "reports"
        self.report_dir.mkdir(exist_ok=True, parents=True)
    
    def generate_capital_evolution_chart(self, data_range=30, save_path=None):
        """Gera um gráfico de evolução do capital
        
        Args:
            data_range (int): Quantidade de dias para o relatório
            save_path (str): Caminho onde salvar o gráfico. Se None, usa o padrão
            
        Returns:
            str: Caminho do arquivo salvo ou None se falhar
        """
        try:
            if not self.db_manager:
                self.logger.error("DBManager não disponível para gerar relatório")
                return None
                
            # Coleta dados históricos do banco de dados
            stats_history = self.db_manager.get_stats_history(data_range)
            
            if not stats_history:
                self.logger.warning("Sem dados históricos suficientes para gerar o relatório")
                return None
            
            # Prepara dados para o gráfico
            dates = [datetime.strptime(stat['date'], '%Y-%m-%d') for stat in stats_history]
            capital = [stat['final_capital'] for stat in stats_history]
            
            # Cria figura
            plt.figure(figsize=(10, 6))
            plt.plot(dates, capital, marker='o', linestyle='-', color='#1f77b4', linewidth=2, markersize=6)
            
            # Adiciona título e rótulos
            plt.title('Evolução do Capital', fontsize=16, pad=20)
            plt.xlabel('Data', fontsize=12)
            plt.ylabel('Capital (R$)', fontsize=12)
            
            # Formata eixo x para mostrar datas de forma legível
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, data_range // 10)))
            plt.gcf().autofmt_xdate()
            
            # Adiciona grade
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Adiciona anotação de rentabilidade total
            if len(capital) >= 2:
                rentabilidade = ((capital[0] / capital[-1]) - 1) * 100
                plt.annotate(f'Rentabilidade: {rentabilidade:.2f}%', 
                             xy=(0.05, 0.95), xycoords='axes fraction', 
                             fontsize=12, ha='left', va='top',
                             bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
            
            # Define caminho para salvar o gráfico
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.report_dir / f"capital_evolution_{timestamp}.png"
            
            # Salva o gráfico
            plt.tight_layout()
            plt.savefig(save_path, dpi=150)
            plt.close()
            
            self.logger.info(f"Gráfico de evolução de capital salvo em {save_path}")
            return str(save_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar gráfico de evolução de capital: {str(e)}")
            return None
    
    def generate_trade_performance_chart(self, data_range=30, save_path=None):
        """Gera um gráfico de desempenho das operações
        
        Args:
            data_range (int): Quantidade de dias para o relatório
            save_path (str): Caminho onde salvar o gráfico. Se None, usa o padrão
            
        Returns:
            str: Caminho do arquivo salvo ou None se falhar
        """
        try:
            if not self.db_manager:
                self.logger.error("DBManager não disponível para gerar relatório")
                return None
                
            # Coleta dados de operações do banco de dados
            operations = self.db_manager.get_operations_history(100)  # Últimas 100 operações
            
            if not operations:
                self.logger.warning("Sem dados de operações para gerar o relatório")
                return None
            
            # Filtra operações de venda (que têm lucro/prejuízo)
            sell_operations = [op for op in operations if op['operation_type'] == 'sell' and op['profit_percent'] is not None]
            
            if not sell_operations:
                self.logger.warning("Sem operações de venda para gerar o relatório")
                return None
            
            # Prepara dados para o gráfico
            profits = [op['profit_percent'] * 100 for op in sell_operations]  # Converte para porcentagem
            timestamps = [datetime.strptime(op['timestamp'], '%Y-%m-%d %H:%M:%S') for op in sell_operations]
            symbols = [op['symbol'] for op in sell_operations]
            
            # Cria figura com dois subplots (gráfico de barras e dispersão)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
            
            # Gráfico 1: Resultados de operações ao longo do tempo
            for i, (profit, timestamp, symbol) in enumerate(zip(profits, timestamps, symbols)):
                color = 'green' if profit >= 0 else 'red'
                ax1.bar(i, profit, color=color, alpha=0.7)
                
            # Adiciona linha horizontal em y=0
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Configuração do primeiro gráfico
            ax1.set_title('Resultados das Operações', fontsize=16)
            ax1.set_ylabel('Lucro/Prejuízo (%)', fontsize=12)
            ax1.set_xticks(range(len(profits)))
            ax1.set_xticklabels([f"{s.split('/')[0]}" for s in symbols], rotation=45, ha='right')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Gráfico 2: Distribuição de resultados
            positive = [p for p in profits if p >= 0]
            negative = [p for p in profits if p < 0]
            
            bins = np.linspace(min(profits), max(profits), 20)
            
            ax2.hist(positive, bins=bins, color='green', alpha=0.7, label='Lucro')
            ax2.hist(negative, bins=bins, color='red', alpha=0.7, label='Prejuízo')
            
            # Configuração do segundo gráfico
            ax2.set_title('Distribuição de Resultados', fontsize=16)
            ax2.set_xlabel('Lucro/Prejuízo (%)', fontsize=12)
            ax2.set_ylabel('Frequência', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.legend()
            
            # Estatísticas
            win_rate = len(positive) / len(profits) * 100 if len(profits) > 0 else 0
            avg_profit = sum(positive) / len(positive) if len(positive) > 0 else 0
            avg_loss = sum(negative) / len(negative) if len(negative) > 0 else 0
            
            stats_text = f"Win Rate: {win_rate:.2f}%\n" \
                        f"Média de Lucro: {avg_profit:.2f}%\n" \
                        f"Média de Perda: {avg_loss:.2f}%"
            
            # Adiciona estatísticas como texto
            fig.text(0.15, 0.01, stats_text, fontsize=12, 
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
            
            # Define caminho para salvar o gráfico
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.report_dir / f"trade_performance_{timestamp}.png"
            
            # Salva o gráfico
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)  # Ajusta para não cortar o texto de estatísticas
            plt.savefig(save_path, dpi=150)
            plt.close()
            
            self.logger.info(f"Gráfico de desempenho de operações salvo em {save_path}")
            return str(save_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar gráfico de desempenho: {str(e)}")
            return None
            
    def generate_complete_report(self):
        """Gera um relatório completo com todos os gráficos
        
        Returns:
            list: Lista de caminhos dos arquivos gerados
        """
        report_paths = []
        
        # Gera gráfico de evolução do capital
        capital_chart = self.generate_capital_evolution_chart()
        if capital_chart:
            report_paths.append(capital_chart)
        
        # Gera gráfico de desempenho das operações
        trade_chart = self.generate_trade_performance_chart()
        if trade_chart:
            report_paths.append(trade_chart)
        
        return report_paths
