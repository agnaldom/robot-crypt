#!/usr/bin/env python3
"""
Análise completa de cobertura de testes do Robot-Crypt
"""

import os
import re
from pathlib import Path

def get_source_modules():
    """Obtém lista de todos os módulos de código fonte"""
    src_files = []
    
    for root, dirs, files in os.walk('src'):
        # Pular diretórios de cache
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
        
        for file in files:
            if (file.endswith('.py') and 
                not file.startswith('__') and 
                file != '__init__.py'):
                
                rel_path = os.path.relpath(os.path.join(root, file), 'src')
                src_files.append(rel_path)
    
    return sorted(src_files)

def get_test_modules():
    """Obtém lista de módulos que têm testes"""
    test_files = []
    
    for file in os.listdir('tests'):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(file)
    
    return test_files

def categorize_modules(src_files):
    """Categoriza módulos por tipo/diretório"""
    categories = {
        'API Clients': [],
        'AI & ML': [],
        'Core System': [],
        'Database': [],
        'Trading Engine': [],
        'Analytics': [],
        'Services': [],
        'Models': [],
        'Schemas': [],
        'Utils & Tools': [],
        'Scripts': [],
        'Other': []
    }
    
    for src_file in src_files:
        if src_file.startswith('ai/') or src_file.startswith('ml/'):
            categories['AI & ML'].append(src_file)
        elif src_file.startswith('api/'):
            categories['API Clients'].append(src_file)
        elif src_file.startswith('core/'):
            categories['Core System'].append(src_file)
        elif src_file.startswith('database/') or src_file.startswith('persistence/'):
            categories['Database'].append(src_file)
        elif (src_file.startswith('strategies/') or 
              src_file.startswith('trading/') or 
              src_file.startswith('risk_management/')):
            categories['Trading Engine'].append(src_file)
        elif src_file.startswith('analytics/') or src_file.startswith('analysis/'):
            categories['Analytics'].append(src_file)
        elif src_file.startswith('services/'):
            categories['Services'].append(src_file)
        elif src_file.startswith('models/'):
            categories['Models'].append(src_file)
        elif src_file.startswith('schemas/'):
            categories['Schemas'].append(src_file)
        elif (src_file.startswith('utils/') or 
              src_file.startswith('tools/') or
              src_file.startswith('middleware/')):
            categories['Utils & Tools'].append(src_file)
        elif src_file.startswith('scripts/'):
            categories['Scripts'].append(src_file)
        else:
            categories['Other'].append(src_file)
    
    return categories

def analyze_test_coverage():
    """Análise principal de cobertura"""
    
    print("📊 ANÁLISE DE COBERTURA DE TESTES - ROBOT-CRYPT")
    print("=" * 60)
    
    # Obter listas
    src_files = get_source_modules()
    test_files = get_test_modules()
    
    print(f"\n📁 Total de módulos fonte: {len(src_files)}")
    print(f"🧪 Total de arquivos de teste: {len(test_files)}")
    
    # Extrair módulos testados
    tested_modules = set()
    for test_file in test_files:
        module = test_file.replace('test_', '').replace('.py', '')
        tested_modules.add(module)
    
    print(f"🎯 Módulos com testes: {tested_modules}")
    
    # Categorizar módulos
    categories = categorize_modules(src_files)
    
    # Identificar módulos sem testes
    missing_tests = []
    
    for src_file in src_files:
        module_name = os.path.splitext(os.path.basename(src_file))[0]
        module_dir = os.path.dirname(src_file).split('/')[0] if '/' in src_file else ''
        
        # Verificar se tem teste
        has_test = False
        for tested in tested_modules:
            if (tested in module_name or 
                module_name in tested or 
                tested in module_dir or
                tested == 'real_apis' and 'api' in module_dir):
                has_test = True
                break
        
        if not has_test:
            missing_tests.append(src_file)
    
    print(f"\n❌ Módulos SEM testes: {len(missing_tests)}")
    print(f"✅ Módulos COM testes: {len(src_files) - len(missing_tests)}")
    print(f"📈 Cobertura atual: {((len(src_files) - len(missing_tests)) / len(src_files) * 100):.1f}%")
    
    # Apresentar por categoria
    print("\n" + "=" * 60)
    print("📋 MÓDULOS SEM TESTES POR CATEGORIA")
    print("=" * 60)
    
    for category, modules in categories.items():
        missing_in_category = [m for m in modules if m in missing_tests]
        
        if missing_in_category:
            print(f"\n🔶 {category.upper()} ({len(missing_in_category)}/{len(modules)} sem testes)")
            for module in missing_in_category:
                print(f"   ❌ {module}")
    
    # Resumo de prioridades
    print("\n" + "=" * 60)
    print("🎯 PRIORIDADES PARA DESENVOLVIMENTO DE TESTES")
    print("=" * 60)
    
    priority_categories = {
        'ALTA': ['Core System', 'Trading Engine', 'Database'],
        'MÉDIA': ['API Clients', 'Services', 'Analytics'],
        'BAIXA': ['AI & ML', 'Utils & Tools', 'Scripts', 'Schemas']
    }
    
    for priority, cats in priority_categories.items():
        print(f"\n🎲 PRIORIDADE {priority}:")
        for cat in cats:
            missing_count = len([m for m in categories[cat] if m in missing_tests])
            total_count = len(categories[cat])
            if missing_count > 0:
                print(f"   • {cat}: {missing_count}/{total_count} módulos sem testes")

if __name__ == "__main__":
    analyze_test_coverage()
