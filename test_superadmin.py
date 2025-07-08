#!/usr/bin/env python3
"""
Script para testar a criação do superadmin e gerar token JWT.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from src.core.startup import create_superadmin
from src.core.config import settings
from src.core.security import create_access_token, authenticate_user
from src.services.user_service import UserService
from src.database.database import async_session_maker
from datetime import timedelta


async def test_and_generate_token():
    """Testa a criação do superadmin e gera um token."""
    print("=" * 60)
    print("🤖 Robot-Crypt - Teste de Superadmin e Token")
    print("=" * 60)
    
    print(f"\n📋 Configurações do usuário:")
    print(f"   Email: {settings.USER_EMAIL}")
    print(f"   Nome: {settings.USER_NAME}")
    print(f"   Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Local'}")
    
    # Criar superadmin
    print(f"\n🚀 Criando/verificando superadmin...")
    superadmin = await create_superadmin()
    
    if not superadmin:
        print("❌ Falha ao criar superadmin. Abortando.")
        return
    
    print(f"✅ Superadmin: {superadmin.email} (ID: {superadmin.id})")
    
    # Testar autenticação
    print(f"\n🔐 Testando autenticação...")
    
    try:
        async with async_session_maker() as db:
            user_service = UserService(db)
            
            authenticated_user = await authenticate_user(
                user_service,
                settings.USER_EMAIL,
                settings.USER_PASSWORD
            )
            
            if authenticated_user:
                print(f"✅ Autenticação bem-sucedida: {authenticated_user.email}")
                
                # Gerar token JWT
                print(f"\n🎫 Gerando token JWT...")
                
                access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": str(authenticated_user.id)},
                    expires_delta=access_token_expires
                )
                
                print(f"✅ Token gerado com sucesso!")
                print(f"   Expira em: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos")
                
                print(f"\n" + "=" * 60)
                print(f"🔑 CREDENCIAIS DE ACESSO:")
                print(f"   Email: {settings.USER_EMAIL}")
                print(f"   Senha: {settings.USER_PASSWORD}")
                print(f"\n🎫 TOKEN JWT:")
                print(f"   {access_token}")
                
                print(f"\n📝 EXEMPLO DE USO:")
                print(f"   # Login via API:")
                print(f"   curl -X POST 'http://localhost:8000/auth/login' \\")
                print(f"        -H 'Content-Type: application/x-www-form-urlencoded' \\")
                print(f"        -d 'username={settings.USER_EMAIL}&password={settings.USER_PASSWORD}'")
                
                print(f"\n   # Usar token nas requisições:")
                print(f"   curl -H 'Authorization: Bearer {access_token}' \\")
                print(f"        http://localhost:8000/auth/me")
                
                print(f"\n   # Testar portfolio:")
                print(f"   curl -H 'Authorization: Bearer {access_token}' \\")
                print(f"        http://localhost:8000/portfolio")
                
                print("=" * 60)
                
            else:
                print("❌ Falha na autenticação!")
                
    except Exception as e:
        print(f"❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_and_generate_token())
