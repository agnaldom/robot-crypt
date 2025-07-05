#!/usr/bin/env python3
"""
Script de Análise de Código Não Utilizado
Robot-Crypt Cleanup Analysis

Este script analisa o projeto para identificar arquivos, dependências e código não utilizados.
"""

import os
import ast
import json
import glob
from pathlib import Path
from collections import defaultdict

class CleanupAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        self.unused_files = []
        self.unused_imports = []
        self.duplicate_code = []
        self.backend_references = []
        self.recommendations = []
        
    def analyze_python_files(self):
        """Analisa arquivos Python para imports e dependências"""
        python_files = list(self.project_root.glob("**/*.py"))
        # Exclui arquivos em .venv, backend/, e backend_new/
        python_files = [f for f in python_files if not any(
            part.startswith('.') or part in ['backend', 'backend_new', '__pycache__']
            for part in f.parts
        )]
        
        imports_by_file = {}
        all_imports = set()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST para encontrar imports
                tree = ast.parse(content)
                file_imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_imports.append(alias.name)
                            all_imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_imports.append(node.module)
                            all_imports.add(node.module)
                
                imports_by_file[file_path] = file_imports
                
            except Exception as e:
                print(f"Erro ao analisar {file_path}: {e}")
        
        return imports_by_file, all_imports
    
    def find_unused_files(self):
        """Identifica arquivos potencialmente não utilizados"""
        # Arquivos que parecem não ser usados pelo projeto principal
        potential_unused = []
        
        # Scripts de setup e teste que podem ser consolidados
        setup_scripts = list(self.project_root.glob("setup*.sh")) + list(self.project_root.glob("setup*.py"))
        test_scripts = list(self.project_root.glob("test_*.py"))
        
        # Arquivos de migração e manutenção antigos
        migration_files = [
            "migrate_stats.py",
            "update_simulation_field.py",
            "populate_database.py",
            "maintenance_tool.py",
            "binance_data_sync.py"
        ]
        
        # Scripts duplicados ou obsoletos
        duplicate_scripts = [
            "dashboard.py",  # parece não existir mais
            "run_dashboard.py",
            "start_dashboard.sh",
            "simple_test.py",
            "test_execution.py",
            "test_imports.py",
            "test_postgres.py",
            "test_startup.py"
        ]
        
        for file_pattern in migration_files + duplicate_scripts:
            file_path = self.project_root / file_pattern
            if file_path.exists():
                potential_unused.append(file_path)
        
        # Analisa scripts de setup
        for script in setup_scripts:
            if "real" in script.name or "testnet" in script.name:
                potential_unused.append(script)
        
        # Analisa scripts de teste isolados
        for script in test_scripts:
            if script.name not in ["test_strategy.py", "test_simulator.py"]:
                potential_unused.append(script)
        
        return potential_unused
    
    def analyze_backend_references(self):
        """Verifica se há referências ao diretório backend/"""
        backend_refs = []
        
        # Busca por imports ou referências ao backend antigo
        for py_file in self.project_root.glob("**/*.py"):
            if any(part in ['backend', 'backend_new', '.venv', '__pycache__'] for part in py_file.parts):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Procura por referências ao backend
                if 'backend/' in content or 'from backend' in content or 'import backend' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'backend' in line and ('import' in line or 'from' in line):
                            backend_refs.append({
                                'file': py_file,
                                'line': i + 1,
                                'content': line.strip()
                            })
            except Exception as e:
                print(f"Erro ao analisar {py_file}: {e}")
        
        return backend_refs
    
    def analyze_notifications_spam(self):
        """Analisa arquivos de notificação duplicados"""
        notifications_dir = self.project_root / "notifications"
        if notifications_dir.exists():
            notification_files = list(notifications_dir.glob("notification_*.txt"))
            return len(notification_files), notification_files
        return 0, []
    
    def check_duplicate_functionality(self):
        """Verifica funcionalidades duplicadas"""
        duplicates = []
        
        # Dashboard duplicado
        dashboard_files = []
        for pattern in ["dashboard*.py", "dashboard/*", "robot_crypt_dashboard.py"]:
            dashboard_files.extend(list(self.project_root.glob(pattern)))
        
        if len(dashboard_files) > 1:
            duplicates.append({
                'type': 'dashboard',
                'files': dashboard_files,
                'description': 'Múltiplas implementações de dashboard encontradas'
            })
        
        # Simuladores duplicados
        simulator_files = list(self.project_root.glob("*simulator*.py"))
        if len(simulator_files) > 1:
            duplicates.append({
                'type': 'simulator',
                'files': simulator_files,
                'description': 'Múltiplos simuladores encontrados'
            })
        
        # APIs Binance duplicadas
        binance_files = list(self.project_root.glob("binance*.py"))
        if len(binance_files) > 2:  # main + simulator é ok
            duplicates.append({
                'type': 'binance_api',
                'files': binance_files,
                'description': 'Múltiplas implementações da API Binance'
            })
        
        return duplicates
    
    def generate_cleanup_plan(self):
        """Gera plano detalhado de limpeza"""
        plan = {
            'files_to_remove': [],
            'files_to_consolidate': [],
            'directories_to_clean': [],
            'code_to_refactor': [],
            'estimated_space_savings': 0
        }
        
        # Analisa arquivos não utilizados
        unused_files = self.find_unused_files()
        for file_path in unused_files:
            try:
                size = file_path.stat().st_size
                plan['files_to_remove'].append({
                    'path': str(file_path.relative_to(self.project_root)),
                    'size_bytes': size,
                    'reason': 'Aparenta não ser usado pelo projeto principal'
                })
                plan['estimated_space_savings'] += size
            except:
                pass
        
        # Analisa notificações em massa
        notif_count, notif_files = self.analyze_notifications_spam()
        if notif_count > 10:
            # Remove arquivos antigos, mantém apenas os últimos 5
            files_to_keep = sorted(notif_files, key=lambda x: x.stat().st_mtime)[-5:]
            files_to_remove = [f for f in notif_files if f not in files_to_keep]
            
            total_size = sum(f.stat().st_size for f in files_to_remove)
            plan['files_to_remove'].append({
                'path': 'notifications/',
                'count': len(files_to_remove),
                'size_bytes': total_size,
                'reason': f'Limpeza de {len(files_to_remove)} arquivos de notificação antigos'
            })
            plan['estimated_space_savings'] += total_size
        
        # Analisa duplicatas
        duplicates = self.check_duplicate_functionality()
        for duplicate in duplicates:
            plan['files_to_consolidate'].append({
                'type': duplicate['type'],
                'files': [str(f) for f in duplicate['files']],
                'description': duplicate['description']
            })
        
        # Diretório backend/ completo
        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            try:
                # Calcula tamanho do diretório backend
                total_size = sum(f.stat().st_size for f in backend_dir.rglob("*") if f.is_file())
                plan['directories_to_clean'].append({
                    'path': 'backend/',
                    'size_bytes': total_size,
                    'reason': 'Migração para backend_new/ concluída'
                })
                plan['estimated_space_savings'] += total_size
            except:
                pass
        
        return plan
    
    def run_analysis(self):
        """Executa análise completa"""
        print("🔍 Iniciando análise de limpeza do Robot-Crypt...")
        
        # 1. Analisa imports e dependências
        print("📦 Analisando imports e dependências...")
        imports_by_file, all_imports = self.analyze_python_files()
        
        # 2. Encontra arquivos não utilizados
        print("🗑️ Identificando arquivos não utilizados...")
        unused_files = self.find_unused_files()
        
        # 3. Verifica referências ao backend antigo
        print("🔗 Verificando referências ao backend antigo...")
        backend_refs = self.analyze_backend_references()
        
        # 4. Analisa notificações em massa
        print("📢 Analisando arquivos de notificação...")
        notif_count, notif_files = self.analyze_notifications_spam()
        
        # 5. Verifica duplicatas
        print("👥 Verificando funcionalidades duplicadas...")
        duplicates = self.check_duplicate_functionality()
        
        # 6. Gera plano de limpeza
        print("📋 Gerando plano de limpeza...")
        cleanup_plan = self.generate_cleanup_plan()
        
        return {
            'summary': {
                'total_python_files': len(imports_by_file),
                'unused_files_count': len(unused_files),
                'backend_references': len(backend_refs),
                'notification_files': notif_count,
                'duplicate_groups': len(duplicates),
                'estimated_space_savings_mb': cleanup_plan['estimated_space_savings'] / (1024 * 1024)
            },
            'unused_files': [str(f.relative_to(self.project_root)) for f in unused_files],
            'backend_references': backend_refs,
            'notification_analysis': {
                'count': notif_count,
                'recommendation': 'Manter apenas os 5 mais recentes' if notif_count > 10 else 'OK'
            },
            'duplicates': duplicates,
            'cleanup_plan': cleanup_plan
        }

def main():
    analyzer = CleanupAnalyzer()
    results = analyzer.run_analysis()
    
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE ANÁLISE DE LIMPEZA - ROBOT-CRYPT")
    print("="*80)
    
    summary = results['summary']
    print(f"""
📈 RESUMO:
  • Arquivos Python analisados: {summary['total_python_files']}
  • Arquivos não utilizados: {summary['unused_files_count']}
  • Referências ao backend antigo: {summary['backend_references']}
  • Arquivos de notificação: {summary['notification_files']}
  • Grupos de duplicatas: {summary['duplicate_groups']}
  • Economia estimada: {summary['estimated_space_savings_mb']:.2f} MB
""")
    
    if results['unused_files']:
        print("\n🗑️ ARQUIVOS POTENCIALMENTE NÃO UTILIZADOS:")
        for file_path in results['unused_files']:
            print(f"  • {file_path}")
    
    if results['backend_references']:
        print("\n⚠️ REFERÊNCIAS AO BACKEND ANTIGO ENCONTRADAS:")
        for ref in results['backend_references']:
            print(f"  • {ref['file']}:{ref['line']} - {ref['content']}")
    
    if results['notification_analysis']['count'] > 10:
        print(f"\n📢 LIMPEZA DE NOTIFICAÇÕES RECOMENDADA:")
        print(f"  • Encontrados {results['notification_analysis']['count']} arquivos de notificação")
        print(f"  • Recomendação: {results['notification_analysis']['recommendation']}")
    
    if results['duplicates']:
        print("\n👥 FUNCIONALIDADES DUPLICADAS:")
        for dup in results['duplicates']:
            print(f"  • Tipo: {dup['type']}")
            print(f"    Descrição: {dup['description']}")
            print(f"    Arquivos: {', '.join([str(f) for f in dup['files']])}")
    
    print("\n" + "="*80)
    print("🎯 RECOMENDAÇÕES DE LIMPEZA:")
    print("="*80)
    
    recommendations = [
        "1. REMOVER diretório backend/ completo (migração para backend_new/ concluída)",
        "2. CONSOLIDAR scripts de setup em um único script",
        "3. LIMPAR arquivos de notificação antigos (manter apenas os 5 mais recentes)",
        "4. REMOVER scripts de teste isolados que não são mais utilizados",
        "5. VERIFICAR se os módulos de dashboard duplicados podem ser unificados",
        "6. ATUALIZAR imports que ainda referenciam o backend antigo",
        "7. CONSIDERAR mover scripts de manutenção para um diretório separado 'tools/'",
        "8. VERIFICAR se requirements.txt contém dependências não utilizadas"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\n💾 Economia estimada total: {summary['estimated_space_savings_mb']:.2f} MB")
    print("\n✅ Análise concluída! Execute as ações recomendadas conforme necessário.")
    
    # Salva relatório em arquivo
    report_path = Path("cleanup_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Relatório detalhado salvo em: {report_path}")

if __name__ == "__main__":
    main()
