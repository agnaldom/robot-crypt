#!/usr/bin/env python3
"""
Script de Limpeza Automatizada do Robot-Crypt
Este script executa as ações de limpeza recomendadas pela análise.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class AutoCleanup:
    def __init__(self, project_root=".", dry_run=True):
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.actions_log = []
        self.backup_dir = self.project_root / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_action(self, action, path="", details=""):
        """Registra ação executada"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'path': path,
            'details': details,
            'dry_run': self.dry_run
        }
        self.actions_log.append(entry)
        
        status = "[DRY RUN]" if self.dry_run else "[EXECUTADO]"
        print(f"{status} {action}: {path} - {details}")
    
    def create_backup(self, file_path):
        """Cria backup de arquivo antes de remover"""
        if self.dry_run:
            return
            
        try:
            # Cria diretório de backup se não existir
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Calcula caminho relativo e cria estrutura no backup
            rel_path = file_path.relative_to(self.project_root)
            backup_path = self.backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia arquivo
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path)
                
            self.log_action("BACKUP_CRIADO", str(file_path), f"Backup em {backup_path}")
            
        except Exception as e:
            self.log_action("ERRO_BACKUP", str(file_path), f"Erro: {e}")
    
    def remove_unused_files(self):
        """Remove arquivos não utilizados identificados"""
        unused_files = [
            "migrate_stats.py",
            "update_simulation_field.py", 
            "populate_database.py",
            "maintenance_tool.py",
            "binance_data_sync.py",
            "simple_test.py",
            "test_execution.py", 
            "test_imports.py",
            "test_postgres.py",
            "test_startup.py"
        ]
        
        for file_name in unused_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                self.create_backup(file_path)
                
                if not self.dry_run:
                    file_path.unlink()
                    
                self.log_action("ARQUIVO_REMOVIDO", str(file_path), "Arquivo não utilizado removido")
    
    def consolidate_setup_scripts(self):
        """Consolida scripts de setup em um único arquivo"""
        setup_scripts = [
            "setup_real_account.sh",
            "setup_real.sh", 
            "setup_testnet.sh",
            "setup_real_advanced.sh"
        ]
        
        # Cria script consolidado
        consolidated_content = """#!/bin/bash
# Script de Setup Consolidado do Robot-Crypt
# Gerado automaticamente pela limpeza do projeto

set -e

show_help() {
    echo "Uso: $0 [modo]"
    echo ""
    echo "Modos disponíveis:"
    echo "  simulation  - Configura modo de simulação (padrão)"
    echo "  testnet     - Configura para Binance TestNet"
    echo "  production  - Configura para produção (conta real)"
    echo "  help        - Mostra esta ajuda"
    echo ""
}

setup_simulation() {
    echo "🔄 Configurando modo de simulação..."
    export SIMULATION_MODE=true
    export USE_TESTNET=false
    echo "SIMULATION_MODE=true" >> .env
    echo "USE_TESTNET=false" >> .env
    echo "✅ Modo de simulação configurado!"
}

setup_testnet() {
    echo "🧪 Configurando modo TestNet..."
    echo "⚠️  Você precisará de credenciais específicas da TestNet"
    echo "📖 Obtenha em: https://testnet.binance.vision/"
    
    read -p "Digite sua TestNet API Key: " TESTNET_API_KEY
    read -s -p "Digite sua TestNet Secret Key: " TESTNET_SECRET_KEY
    echo ""
    
    echo "TESTNET_API_KEY=$TESTNET_API_KEY" >> .env
    echo "TESTNET_SECRET_KEY=$TESTNET_SECRET_KEY" >> .env
    echo "USE_TESTNET=true" >> .env
    echo "SIMULATION_MODE=false" >> .env
    echo "✅ Modo TestNet configurado!"
}

setup_production() {
    echo "🚨 ATENÇÃO: Configurando modo de PRODUÇÃO com dinheiro real!"
    echo "⚠️  Certifique-se de que você entende os riscos"
    
    read -p "Você tem certeza? (digite 'SIM' para continuar): " confirm
    if [ "$confirm" != "SIM" ]; then
        echo "❌ Configuração cancelada"
        exit 1
    fi
    
    read -p "Digite sua API Key de produção: " PROD_API_KEY
    read -s -p "Digite sua Secret Key de produção: " PROD_SECRET_KEY
    echo ""
    
    echo "BINANCE_API_KEY=$PROD_API_KEY" >> .env
    echo "BINANCE_API_SECRET=$PROD_SECRET_KEY" >> .env
    echo "USE_TESTNET=false" >> .env
    echo "SIMULATION_MODE=false" >> .env
    echo "✅ Modo de produção configurado!"
    echo "🚨 CUIDADO: O bot agora operará com dinheiro real!"
}

# Função principal
main() {
    local mode=${1:-simulation}
    
    case $mode in
        "simulation"|"sim")
            setup_simulation
            ;;
        "testnet"|"test")
            setup_testnet
            ;;
        "production"|"prod"|"real")
            setup_production
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "❌ Modo inválido: $mode"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
"""
        
        consolidated_path = self.project_root / "setup.sh"
        
        # Faz backup dos scripts originais
        for script_name in setup_scripts:
            script_path = self.project_root / script_name
            if script_path.exists():
                self.create_backup(script_path)
                
                if not self.dry_run:
                    script_path.unlink()
                    
                self.log_action("SCRIPT_REMOVIDO", str(script_path), "Script de setup consolidado")
        
        # Cria script consolidado
        if not self.dry_run:
            with open(consolidated_path, 'w') as f:
                f.write(consolidated_content)
            consolidated_path.chmod(0o755)  # Torna executável
            
        self.log_action("SCRIPT_CRIADO", str(consolidated_path), "Script de setup consolidado criado")
    
    def clean_notification_files(self):
        """Limpa arquivos de notificação antigos, mantendo apenas os 5 mais recentes"""
        notifications_dir = self.project_root / "notifications"
        
        if not notifications_dir.exists():
            return
            
        notification_files = list(notifications_dir.glob("notification_*.txt"))
        
        if len(notification_files) <= 5:
            self.log_action("NOTIFICACOES_OK", str(notifications_dir), f"Apenas {len(notification_files)} arquivos, nenhuma limpeza necessária")
            return
        
        # Ordena por data de modificação e mantém apenas os 5 mais recentes
        sorted_files = sorted(notification_files, key=lambda x: x.stat().st_mtime, reverse=True)
        files_to_keep = sorted_files[:5]
        files_to_remove = sorted_files[5:]
        
        # Cria backup e remove arquivos antigos
        for file_path in files_to_remove:
            self.create_backup(file_path)
            
            if not self.dry_run:
                file_path.unlink()
                
        self.log_action("NOTIFICACOES_LIMPAS", str(notifications_dir), 
                       f"Removidos {len(files_to_remove)} arquivos antigos, mantidos {len(files_to_keep)} recentes")
    
    def remove_backend_directory(self):
        """Remove diretório backend/ completo"""
        backend_dir = self.project_root / "backend"
        
        if not backend_dir.exists():
            self.log_action("BACKEND_NAO_ENCONTRADO", str(backend_dir), "Diretório backend/ não existe")
            return
        
        # Cria backup completo do diretório
        self.create_backup(backend_dir)
        
        # Remove diretório
        if not self.dry_run:
            shutil.rmtree(backend_dir)
            
        self.log_action("BACKEND_REMOVIDO", str(backend_dir), "Diretório backend/ removido completamente")
    
    def create_tools_directory(self):
        """Move scripts de manutenção para diretório tools/"""
        tools_dir = self.project_root / "tools"
        
        maintenance_scripts = [
            "maintenance_tool.sh",
            "postgres_checker.py",
            "health_monitor.py",
            "cleanup_analysis.py",
            "auto_cleanup.py"
        ]
        
        # Cria diretório tools se não existir
        if not self.dry_run:
            tools_dir.mkdir(exist_ok=True)
            
        self.log_action("DIRETORIO_CRIADO", str(tools_dir), "Diretório tools/ criado")
        
        # Move scripts de manutenção
        for script_name in maintenance_scripts:
            script_path = self.project_root / script_name
            if script_path.exists():
                target_path = tools_dir / script_name
                
                if not self.dry_run:
                    shutil.move(str(script_path), str(target_path))
                    
                self.log_action("ARQUIVO_MOVIDO", f"{script_path} -> {target_path}", "Script movido para tools/")
    
    def clean_venv_references(self):
        """Remove referências incorretas ao venv no projeto"""
        # Remove diretório venv se existir (deve ser .venv)
        venv_dir = self.project_root / "venv"
        if venv_dir.exists():
            self.create_backup(venv_dir)
            
            if not self.dry_run:
                shutil.rmtree(venv_dir)
                
            self.log_action("VENV_REMOVIDO", str(venv_dir), "Diretório venv/ incorreto removido (use .venv)")
    
    def update_gitignore(self):
        """Atualiza .gitignore com entradas apropriadas"""
        gitignore_path = self.project_root / ".gitignore"
        
        new_entries = [
            "",
            "# Limpeza automática",
            "cleanup_backup/",
            "cleanup_report.json",
            "*.log",
            "logs/",
            "notifications/*.txt",
            "",
            "# Ambientes virtuais",
            "venv/",
            ".venv/", 
            "",
            "# Arquivos de configuração local",
            ".env.local",
            ".env.*.local",
            "",
            "# Dados temporários",
            "data/*.bak",
            "*.tmp"
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                current_content = f.read()
        else:
            current_content = ""
        
        # Adiciona novas entradas se não existirem
        new_content = current_content
        for entry in new_entries:
            if entry and entry not in current_content:
                new_content += f"\n{entry}"
        
        if not self.dry_run and new_content != current_content:
            with open(gitignore_path, 'w') as f:
                f.write(new_content)
                
        self.log_action("GITIGNORE_ATUALIZADO", str(gitignore_path), "Entradas de limpeza adicionadas")
    
    def run_cleanup(self):
        """Executa limpeza completa"""
        print("🧹 Iniciando limpeza automatizada do Robot-Crypt...")
        print(f"Modo: {'DRY RUN (simulação)' if self.dry_run else 'EXECUÇÃO REAL'}")
        print("="*80)
        
        # 1. Remove arquivos não utilizados
        print("\n1️⃣ Removendo arquivos não utilizados...")
        self.remove_unused_files()
        
        # 2. Consolida scripts de setup
        print("\n2️⃣ Consolidando scripts de setup...")
        self.consolidate_setup_scripts()
        
        # 3. Limpa arquivos de notificação
        print("\n3️⃣ Limpando arquivos de notificação...")
        self.clean_notification_files()
        
        # 4. Remove diretório backend/
        print("\n4️⃣ Removendo diretório backend/...")
        self.remove_backend_directory()
        
        # 5. Cria diretório tools/
        print("\n5️⃣ Organizando scripts de manutenção...")
        self.create_tools_directory()
        
        # 6. Limpa referências incorretas ao venv
        print("\n6️⃣ Limpando referências incorretas...")
        self.clean_venv_references()
        
        # 7. Atualiza .gitignore
        print("\n7️⃣ Atualizando .gitignore...")
        self.update_gitignore()
        
        print("\n" + "="*80)
        print("✅ Limpeza concluída!")
        
        # Salva log de ações
        log_path = self.project_root / "cleanup_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.actions_log, f, indent=2)
        
        print(f"📄 Log de ações salvo em: {log_path}")
        
        if self.dry_run:
            print("\n⚠️  ESTE FOI UM DRY RUN - Nenhuma alteração foi feita!")
            print("Execute novamente com --execute para aplicar as mudanças.")
        else:
            print(f"📁 Backup criado em: {self.backup_dir}")
            print("🔄 Alterações aplicadas com sucesso!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpeza automatizada do Robot-Crypt')
    parser.add_argument('--execute', action='store_true', 
                       help='Executa as alterações (padrão: dry run)')
    parser.add_argument('--project-root', default='.', 
                       help='Diretório raiz do projeto')
    
    args = parser.parse_args()
    
    cleanup = AutoCleanup(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
