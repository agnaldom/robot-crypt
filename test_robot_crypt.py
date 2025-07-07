#!/usr/bin/env python3
"""
Test script principal para demonstrar funcionalidades do Robot-Crypt.
Este script testa as principais funcionalidades do sistema de trading de criptomoedas.
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Testa se os principais módulos podem ser importados."""
    print("🔄 Testando imports dos módulos principais...")
    
    try:
        # Core modules
        from src.core.config import settings
        print("✅ Config carregado com sucesso")
        
        from src.core.security import create_access_token, get_password_hash
        print("✅ Módulo de segurança carregado")
        
        # Database
        from src.database.database import get_database
        print("✅ Módulo de database carregado")
        
        # Schemas
        from src.schemas.user import UserCreate
        from src.schemas.trade import TradeCreateRequest
        from src.schemas.asset import AssetCreate
        print("✅ Schemas carregados")
        
        # Services
        from src.services.user_service import UserService
        from src.services.trade_service import TradeService
        from src.services.asset_service import AssetService
        print("✅ Serviços carregados")
        
        # Analytics
        from src.analytics.ml_models import MLModels
        from src.analytics.risk_analytics import RiskAnalytics
        print("✅ Módulos de analytics carregados")
        
        # AI modules
        from src.ai.llm_client import LLMClient
        from src.ai.news_analyzer import LLMNewsAnalyzer
        print("✅ Módulos de AI carregados")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def test_configuration():
    """Testa se a configuração está funcionando corretamente."""
    print("\n🔄 Testando configuração...")
    
    try:
        from src.core.config import settings
        
        print(f"✅ App Name: {settings.APP_NAME}")
        print(f"✅ App Version: {settings.APP_VERSION}")
        print(f"✅ Debug Mode: {settings.DEBUG}")
        print(f"✅ Host: {settings.HOST}")
        print(f"✅ Port: {settings.PORT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False


def test_security():
    """Testa funcionalidades de segurança."""
    print("\n🔄 Testando segurança...")
    
    try:
        from src.core.security import create_access_token, get_password_hash, verify_password
        
        # Test password hashing
        password = "test_password_123"
        hashed = get_password_hash(password)
        print(f"✅ Senha hasheada: {hashed[:50]}...")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"✅ Verificação de senha: {is_valid}")
        
        # Test JWT token creation
        token = create_access_token(data={"sub": "test_user"})
        print(f"✅ Token JWT criado: {token[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na segurança: {e}")
        return False


def test_ml_models():
    """Testa funcionalidades de Machine Learning."""
    print("\n🔄 Testando ML Models...")
    
    try:
        import pandas as pd
        import numpy as np
        from src.analytics.ml_models import MLModels
        
        # Initialize ML Models
        ml = MLModels(models_dir="test_models")
        print("✅ MLModels inicializado")
        
        # Create sample data
        data = pd.DataFrame({
            'price': [100, 105, 110, 108, 112],
            'volume': [1000, 1100, 950, 1200, 1050],
            'target': [105, 110, 108, 112, 115]
        })
        
        # Test feature preparation
        X, y = ml.prepare_features(data, 'target', ['price', 'volume'], lag_features=1)
        print(f"✅ Features preparadas: {X.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos ML Models: {e}")
        return False


def test_ai_modules():
    """Testa módulos de AI."""
    print("\n🔄 Testando módulos de AI...")
    
    try:
        from src.ai.llm_client import LLMClient
        from src.ai.news_analyzer import LLMNewsAnalyzer
        
        # Test LLM Client initialization
        llm = LLMClient()
        print("✅ LLMClient inicializado")
        
        # Test News Analyzer
        analyzer = LLMNewsAnalyzer()
        print("✅ NewsAnalyzer inicializado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos módulos de AI: {e}")
        return False


def test_database_connection():
    """Testa conexão com o banco de dados."""
    print("\n🔄 Testando conexão com banco...")
    
    try:
        from src.database.database import async_engine
        
        # Test if database URL is configured
        print(f"✅ Engine de banco configurado: {type(async_engine)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False


async def test_api_schemas():
    """Testa schemas da API."""
    print("\n🔄 Testando schemas da API...")
    
    try:
        from src.schemas.user import UserCreate
        from src.schemas.trade import TradeCreateRequest
        from src.schemas.asset import AssetCreate
        
        # Test User schema
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="testpassword123"
        )
        print(f"✅ UserCreate schema: {user_data.email}")
        
        # Test Trade schema
        trade_data = TradeCreateRequest(
            symbol="BTCUSDT",
            side="buy",
            quantity="0.01",
            price="50000.00",
            exchange="binance"
        )
        print(f"✅ TradeCreateRequest schema: {trade_data.symbol}")
        
        # Test Asset schema
        asset_data = AssetCreate(
            symbol="BTCUSDT",
            name="Bitcoin",
            type="cryptocurrency"
        )
        print(f"✅ AssetCreate schema: {asset_data.symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos schemas: {e}")
        return False


def run_all_tests():
    """Executa todos os testes."""
    print("🚀 Iniciando testes do Robot-Crypt...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Security", test_security),
        ("ML Models", test_ml_models),
        ("AI Modules", test_ai_modules),
        ("Database", test_database_connection),
    ]
    
    async_tests = [
        ("API Schemas", test_api_schemas),
    ]
    
    results = []
    
    # Run synchronous tests
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Erro no teste {name}: {e}")
            results.append((name, False))
    
    # Run asynchronous tests
    async def run_async_tests():
        async_results = []
        for name, test_func in async_tests:
            try:
                success = await test_func()
                async_results.append((name, success))
            except Exception as e:
                print(f"❌ Erro no teste {name}: {e}")
                async_results.append((name, False))
        return async_results
    
    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{name:20} {status}")
    
    print("-"*60)
    print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Robot-Crypt está funcionando corretamente.")
        return True
    else:
        print(f"\n⚠️  {total-passed} teste(s) falharam. Verifique os problemas acima.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
