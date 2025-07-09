#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas de autenticação no Robot-Crypt.
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings
from src.core.security import get_password_hash, create_access_token, verify_password
from datetime import timedelta

API_BASE_URL = "http://localhost:8000"

async def check_database_connection():
    """Verifica se a conexão com o banco de dados está funcionando."""
    print("🔍 Verificando conexão com o banco de dados...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Conexão com banco de dados OK")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com banco de dados: {e}")
        return False

async def check_users_table():
    """Verifica se a tabela users existe e tem dados."""
    print("🔍 Verificando tabela de usuários...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            # Verifica se a tabela existe
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("❌ Tabela 'users' não existe")
                return False
            
            # Verifica quantos usuários existem
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            
            print(f"✅ Tabela 'users' existe com {user_count} usuários")
            
            # Lista os usuários
            result = await conn.execute(text("SELECT id, email, full_name, is_active, is_superuser FROM users"))
            users = result.fetchall()
            
            print("👥 Usuários encontrados:")
            for user in users:
                print(f"  - ID: {user[0]}, Email: {user[1]}, Nome: {user[2]}, Ativo: {user[3]}, Superuser: {user[4]}")
            
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar tabela users: {e}")
        return False

async def create_test_user():
    """Cria um usuário de teste se não existir."""
    print("🔍 Criando/verificando usuário de teste...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            # Verifica se o usuário de teste existe
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "test@test.com"}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print("✅ Usuário test@test.com já existe")
                return True
            
            # Cria o usuário de teste
            hashed_password = get_password_hash("test123")
            await conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
                    VALUES (:email, :password, :name, :active, :superuser)
                """),
                {
                    "email": "test@test.com",
                    "password": hashed_password,
                    "name": "Test User",
                    "active": True,
                    "superuser": False
                }
            )
            print("✅ Usuário test@test.com criado com sucesso")
            
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Erro ao criar usuário de teste: {e}")
        return False

def test_api_server():
    """Testa se o servidor da API está rodando."""
    print("🔍 Testando servidor da API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor da API está rodando")
            return True
        else:
            print(f"❌ Servidor da API retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com servidor da API: {e}")
        print("💡 Certifique-se de que o servidor está rodando com: python -m src.main")
        return False

def test_login_endpoint():
    """Testa o endpoint de login."""
    print("🔍 Testando endpoint de login...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "test@test.com",
                "password": "test123"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login bem-sucedido")
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            return data.get('access_token')
        else:
            print(f"❌ Login falhou com status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erro: {error_data.get('detail', 'Erro desconhecido')}")
            except:
                print(f"Resposta: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao testar login: {e}")
        return None

def test_authenticated_endpoints(token):
    """Testa endpoints autenticados."""
    print("🔍 Testando endpoints autenticados...")
    
    if not token:
        print("❌ Token não disponível para testes")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "/auth/me",
        "/portfolio/metrics",
        "/trades?limit=10",
        "/portfolio/wallet/value-history?currency=USD&period=month"
    ]
    
    success_count = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
                success_count += 1
            elif response.status_code == 401:
                print(f"❌ {endpoint}: Erro de autenticação (401)")
            elif response.status_code == 429:
                print(f"⚠️ {endpoint}: Rate limit excedido (429)")
            else:
                print(f"❌ {endpoint}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Erro de conexão - {e}")
    
    print(f"📊 Sucesso: {success_count}/{len(endpoints)} endpoints")
    return success_count == len(endpoints)

async def check_jwt_config():
    """Verifica configurações do JWT."""
    print("🔍 Verificando configurações JWT...")
    
    try:
        print(f"SECRET_KEY: {'*' * 20} (definida: {bool(settings.SECRET_KEY)})")
        print(f"ALGORITHM: {settings.ALGORITHM}")
        print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        
        # Testa criação de token
        test_token = create_access_token(
            data={"sub": "test_user"},
            expires_delta=timedelta(minutes=30)
        )
        
        print(f"✅ Token de teste criado: {test_token[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Erro nas configurações JWT: {e}")
        return False

async def main():
    """Função principal de diagnóstico."""
    print("🚀 Iniciando diagnóstico de autenticação Robot-Crypt\n")
    
    # Verifica configurações
    await check_jwt_config()
    print()
    
    # Verifica banco de dados
    if not await check_database_connection():
        print("❌ Falha crítica: Não foi possível conectar ao banco de dados")
        return
    print()
    
    # Verifica tabela de usuários
    if not await check_users_table():
        print("❌ Falha crítica: Problemas com a tabela de usuários")
        return
    print()
    
    # Cria usuário de teste
    if not await create_test_user():
        print("❌ Falha crítica: Não foi possível criar usuário de teste")
        return
    print()
    
    # Testa servidor da API
    if not test_api_server():
        print("❌ Falha crítica: Servidor da API não está rodando")
        return
    print()
    
    # Testa login
    token = test_login_endpoint()
    print()
    
    # Testa endpoints autenticados
    if token:
        test_authenticated_endpoints(token)
    else:
        print("❌ Não foi possível testar endpoints autenticados (sem token)")
    
    print("\n🎯 Diagnóstico concluído!")
    
    if not token:
        print("\n💡 Possíveis soluções:")
        print("1. Verificar se o usuário existe no banco de dados")
        print("2. Verificar se a senha está correta")
        print("3. Verificar configurações do JWT")
        print("4. Verificar se o servidor está rodando corretamente")
        print("5. Executar: python create_test_user.py")

if __name__ == "__main__":
    asyncio.run(main())
