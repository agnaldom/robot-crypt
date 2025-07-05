#!/usr/bin/env python3
"""
Script para limpeza final do projeto Robot-Crypt
Remove arquivos duplicados e redundantes após reorganização modular
"""

import os
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Executa a limpeza final do projeto"""
    
    # Diretório do projeto
    project_dir = Path("/Users/agnaldo.marinho/projetos/robot-crypt")
    
    # Arquivos duplicados que existem na raiz mas já estão organizados em src/
    duplicate_files = [
        "binance_api.py",  # já existe em src/api/binance_api.py
        "binance_simulator.py",  # já existe em src/api/binance_simulator.py
        "config.py",  # já existe em src/core/config.py
        "crypto_events.py",  # já existe em src/analysis/crypto_events.py
        "db_manager.py",  # já existe em src/database/db_manager.py
        "external_data_analyzer.py",  # já existe em src/analysis/external_data_analyzer.py
        "health_monitor.py",  # já existe em tools/health_monitor.py
        "local_notifier.py",  # já existe em src/notifications/local_notifier.py
        "postgres_manager.py",  # já existe em src/database/postgres_manager.py
        "report_generator.py",  # já existe em src/trading/report_generator.py
        "strategy.py",  # já existe em src/strategies/strategy.py
        "technical_indicators.py",  # já existe em src/analysis/technical_indicators.py
        "telegram_notifier.py",  # já existe em src/notifications/telegram_notifier.py
        "utils.py",  # já existe em src/utils/utils.py
        "adaptive_risk_manager.py",  # já existe em src/risk_management/adaptive_risk_manager.py
    ]
    
    # Diretórios duplicados que existem na raiz mas já estão organizados em src/
    duplicate_dirs = [
        "adaptive_risk",  # já existe em src/risk_management/
        "contextual_analysis",  # já existe em src/analysis/
        "dashboard",  # arquivos independentes
        "strategies",  # já existe em src/strategies/
        "wallets",  # vazio
    ]
    
    # Scripts duplicados na raiz que já estão em scripts/
    duplicate_scripts = [
        "setup.sh",  # já existe em scripts/setup/setup.sh
        "setup_simulation.py",  # já existe em scripts/setup/setup_simulation.py
        "setup_simulation.sh",  # já existe em scripts/setup/setup_simulation.sh
        "healthcheck.sh",  # já existe em scripts/deployment/healthcheck.sh
        "railway_entrypoint.sh",  # já existe em scripts/deployment/railway_entrypoint.sh
        "run_performance_test.sh",  # já existe em scripts/maintenance/run_performance_test.sh
        "pg_example.py",  # já existe em scripts/maintenance/pg_example.py
        "maintenance_tool.sh",  # já existe em tools/maintenance_tool.sh
    ]
    
    # Arquivos de configuração duplicados na raiz
    duplicate_configs = [
        "railway.toml",  # já existe em config/railway.toml
        ".env.example",  # já existe em config/environments/.env.example
        ".env.example.real",  # já existe em config/environments/.env.example.real
    ]
    
    # Arquivos obsoletos ou não utilizados
    obsolete_files = [
        "main.py.backup",
        "migrate_stats.py",
        "run_dashboard.py",
        "setup_real.sh",
        "setup_real_account.sh", 
        "setup_real_advanced.sh",
        "setup_testnet.sh",
        "start_dashboard.sh",
        "test_execution.py",
        "docker-run.sh",
        "docker-start.sh",
    ]
    
    # Combinar todas as listas
    all_files_to_remove = duplicate_files + duplicate_scripts + duplicate_configs + obsolete_files
    all_dirs_to_remove = duplicate_dirs
    
    logger.info("=== LIMPEZA FINAL DO PROJETO ROBOT-CRYPT ===")
    logger.info(f"Diretório do projeto: {project_dir}")
    
    # Remover arquivos duplicados
    logger.info("\n1. Removendo arquivos duplicados...")
    for file_name in all_files_to_remove:
        file_path = project_dir / file_name
        if file_path.exists():
            logger.info(f"  Removendo: {file_name}")
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"  Erro ao remover {file_name}: {e}")
        else:
            logger.info(f"  Não encontrado: {file_name}")
    
    # Remover diretórios duplicados
    logger.info("\n2. Removendo diretórios duplicados...")
    for dir_name in all_dirs_to_remove:
        dir_path = project_dir / dir_name
        if dir_path.exists():
            logger.info(f"  Removendo diretório: {dir_name}")
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                logger.error(f"  Erro ao remover {dir_name}: {e}")
        else:
            logger.info(f"  Não encontrado: {dir_name}")
    
    # Limpeza do diretório de notificações
    logger.info("\n3. Limpando diretório de notificações...")
    notifications_dir = project_dir / "notifications"
    if notifications_dir.exists():
        notification_files = list(notifications_dir.glob("*.txt"))
        logger.info(f"  Encontrados {len(notification_files)} arquivos de notificação")
        
        if len(notification_files) > 10:
            # Manter apenas os 10 mais recentes
            notification_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            files_to_remove = notification_files[10:]
            
            logger.info(f"  Removendo {len(files_to_remove)} arquivos antigos de notificação")
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"  Erro ao remover {file_path.name}: {e}")
        else:
            logger.info(f"  Mantendo {len(notification_files)} arquivos de notificação")
    
    # Verificar arquivos restantes na raiz
    logger.info("\n4. Verificando arquivos restantes na raiz...")
    root_files = [f for f in project_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    logger.info(f"  Arquivos restantes na raiz: {len(root_files)}")
    
    for file_path in root_files:
        logger.info(f"    {file_path.name}")
    
    # Verificar diretórios restantes na raiz
    logger.info("\n5. Verificando diretórios restantes na raiz...")
    root_dirs = [d for d in project_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    logger.info(f"  Diretórios restantes na raiz: {len(root_dirs)}")
    
    for dir_path in root_dirs:
        logger.info(f"    {dir_path.name}/")
    
    logger.info("\n=== LIMPEZA FINAL CONCLUÍDA ===")
    logger.info("Projeto Robot-Crypt limpo e organizado na estrutura modular!")

if __name__ == "__main__":
    main()
