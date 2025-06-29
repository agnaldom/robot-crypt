#!/usr/bin/env python3
"""
Ferramenta de migração para converter arquivos de estado antigos para o novo formato
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path

# Configura logger simples
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("migrate-stats")

def setup_directories():
    """Garante que os diretórios necessários existam"""
    for directory in ['data', 'logs', 'reports']:
        dir_path = Path(__file__).parent / directory
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"Diretório {directory} criado com sucesso")

def migrate_state_files():
    """Migra arquivos de estado antigos para o novo formato"""
    data_dir = Path(__file__).parent / "data"
    
    # Lista arquivos de estado
    state_files = list(data_dir.glob("app_state*.json"))
    
    if not state_files:
        logger.info("Nenhum arquivo de estado encontrado para migração.")
        return
    
    logger.info(f"Encontrados {len(state_files)} arquivos de estado para migração.")
    
    for file_path in state_files:
        try:
            logger.info(f"Migrando arquivo: {file_path}")
            
            # Faz backup do arquivo antes da migração
            backup_path = file_path.with_suffix('.json.bak')
            if not backup_path.exists():
                with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"Backup criado: {backup_path}")
            
            # Carrega o estado
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            # Verifica se tem a seção de stats
            if 'stats' not in state:
                logger.warning(f"Arquivo {file_path} não contém seção 'stats'. Pulando.")
                continue
            
            stats = state['stats']
            modified = False
            
            # Mapeamento de chaves antigas para novas
            key_mapping = {
                'trades_total': 'total_trades',
                'trades_win': 'winning_trades',
                'trades_loss': 'losing_trades'
            }
            
            # Migra chaves antigas para novas
            for old_key, new_key in key_mapping.items():
                if old_key in stats and new_key not in stats:
                    stats[new_key] = stats[old_key]
                    logger.info(f"  - Migrado '{old_key}' para '{new_key}': {stats[old_key]}")
                    modified = True
            
            # Garante que todas as chaves necessárias existem
            required_stats = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'best_trade_profit': 0,
                'worst_trade_loss': 0,
                'initial_capital': 100.0,
                'current_capital': 100.0,
                'profit_history': []
            }
            
            for key, default_value in required_stats.items():
                if key not in stats:
                    stats[key] = default_value
                    logger.info(f"  - Adicionado chave ausente '{key}' com valor padrão: {default_value}")
                    modified = True
            
            # Verifica se a chave start_time existe e está em formato correto
            if 'start_time' not in stats:
                stats['start_time'] = datetime.now().isoformat()
                logger.info(f"  - Adicionado 'start_time' ausente com valor atual")
                modified = True
            
            # Salva o estado atualizado se foi modificado
            if modified:
                with open(file_path, 'w') as f:
                    json.dump(state, f, indent=4)
                logger.info(f"Arquivo {file_path} migrado com sucesso.")
            else:
                logger.info(f"Arquivo {file_path} já estava no formato correto.")
                
        except Exception as e:
            logger.error(f"Erro ao migrar arquivo {file_path}: {str(e)}")

def main():
    """Função principal"""
    logger.info("Iniciando migração de arquivos de estado")
    setup_directories()
    migrate_state_files()
    logger.info("Migração concluída")

if __name__ == "__main__":
    main()
