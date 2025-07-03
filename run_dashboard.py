#!/usr/bin/env python3
"""
Script para iniciar apenas o dashboard do Robot-Crypt
"""
import os
import sys
import logging
from pathlib import Path

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("dashboard-starter")

def main():
    """Função principal para iniciar o dashboard"""
    try:
        # Tenta importar dependências essenciais
        import dash
        from dash import dcc, html
        import plotly
        import pandas as pd
        import numpy as np
        
        logger.info(f"Dash versão: {dash.__version__}")
        logger.info(f"Plotly versão: {plotly.__version__}")
        logger.info(f"Pandas versão: {pd.__version__}")
        
        # Verifica se o módulo dashboard está presente
        from config import Config
        from db_manager import DBManager
        from dashboard import RobotCryptDashboard
        
        # Inicializa configuração e banco de dados
        config = Config()
        db = DBManager()
        
        # Define a porta
        dashboard_port = int(os.environ.get("DASHBOARD_PORT", "8050"))
        
        # Inicializa e inicia o dashboard
        logger.info(f"Iniciando dashboard na porta {dashboard_port}...")
        dashboard = RobotCryptDashboard(db, config, port=dashboard_port)
        
        if hasattr(dashboard, 'available') and not dashboard.available:
            logger.error("Dashboard não está disponível devido a dependências faltantes")
            return False
        
        # Configurar o servidor com o contexto de aplicação
        if hasattr(dashboard, 'app') and hasattr(dashboard.app, 'server'):
            # Em Flask 2.0+, before_first_request foi removido
            # Precisamos executar a configuração do servidor em um contexto de aplicação
            with dashboard.app.server.app_context():
                if hasattr(dashboard, '_setup_server'):
                    dashboard._setup_server()
        
        # Inicia o dashboard (bloqueante)
        # Não usa threads porque queremos que este script mantenha o dashboard rodando
        logger.info("Iniciando servidor dashboard...")
        dashboard.app.run_server(debug=False, host='0.0.0.0', port=dashboard_port)
        
        return True
        
    except ImportError as e:
        logger.error(f"Erro ao importar dependências: {e}")
        logger.error("Por favor, instale as dependências necessárias:")
        logger.error("pip install dash==2.6.0 dash-core-components==2.0.0 dash-html-components==2.0.0 dash-table==5.0.0 plotly==5.10.0 pandas numpy")
        return False
    except Exception as e:
        logger.error(f"Erro ao iniciar dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False
        
if __name__ == "__main__":
    main()
