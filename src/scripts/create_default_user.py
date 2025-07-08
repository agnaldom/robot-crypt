#!/usr/bin/env python3
"""
Script para criar usuário padrão do Robot-Crypt.
Lê as configurações do .env e cria o usuário no banco de dados.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.core.security import get_password_hash
from src.database.database import get_database, async_session_factory
from src.models.user import User
from src.schemas.user import UserCreate
from src.services.user_service import UserService


async def create_default_user():
    """Cria o usuário padrão se não existir."""
    print("🚀 Iniciando criação de usuário padrão...")
    
    try:
        # Usar session factory diretamente
        async with async_session_factory() as db:
            user_service = UserService(db)
            
            # Verificar se o usuário já existe
            existing_user = await user_service.get_by_email(settings.DEFAULT_USER_EMAIL)
            
            if existing_user:
                print(f"✅ Usuário '{settings.DEFAULT_USER_EMAIL}' já existe!")
                print(f"   Nome: {existing_user.full_name}")
                print(f"   Superusuário: {existing_user.is_superuser}")
                print(f"   Ativo: {existing_user.is_active}")
                return existing_user
            
            # Criar novo usuário
            user_data = UserCreate(
                email=settings.DEFAULT_USER_EMAIL,
                password=settings.DEFAULT_USER_PASSWORD,
                full_name=settings.DEFAULT_USER_NAME,
                is_superuser=settings.DEFAULT_USER_IS_SUPERUSER,
                is_active=True
            )
            
            print(f"📧 Criando usuário: {settings.DEFAULT_USER_EMAIL}")
            print(f"👤 Nome: {settings.DEFAULT_USER_NAME}")
            print(f"🔑 Superusuário: {settings.DEFAULT_USER_IS_SUPERUSER}")
            
            new_user = await user_service.create(user_data)
            
            print("✅ Usuário criado com sucesso!")
            print(f"   ID: {new_user.id}")
            print(f"   Email: {new_user.email}")
            print(f"   Nome: {new_user.full_name}")
            
            return new_user
            
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_login():
    """Testa o login do usuário criado."""
    print("\n🔐 Testando login...")
    
    try:
        async with async_session_factory() as db:
            user_service = UserService(db)
            
            # Importar authenticate_user
            from src.core.security import authenticate_user
            
            user = await authenticate_user(
                user_service, 
                settings.DEFAULT_USER_EMAIL, 
                settings.DEFAULT_USER_PASSWORD
            )
            
            if user:
                print("✅ Login testado com sucesso!")
                print(f"   Usuário autenticado: {user.email}")
                return True
            else:
                print("❌ Falha no teste de login!")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste de login: {str(e)}")
        return False


async def generate_token():
    """Gera um token JWT para o usuário."""
    print("\n🎫 Gerando token JWT...")
    
    try:
        async with async_session_factory() as db:
            user_service = UserService(db)
            user = await user_service.get_by_email(settings.DEFAULT_USER_EMAIL)
            
            if not user:
                print("❌ Usuário não encontrado!")
                return None
            
            from src.core.security import create_access_token
            from datetime import timedelta
            
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id)}, 
                expires_delta=access_token_expires
            )
            
            print("✅ Token JWT gerado com sucesso!")
            print(f"   Token: {access_token}")
            print(f"   Expira em: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos")
            print(f"\n📋 Para usar nas requisições:")
            print(f"   Authorization: Bearer {access_token}")
            
            return access_token
            
    except Exception as e:
        print(f"❌ Erro ao gerar token: {str(e)}")
        return None


async def main():
    """Função principal."""
    print("=" * 60)
    print("🤖 Robot-Crypt - Criação de Usuário Padrão")
    print("=" * 60)
    
    print(f"\n📋 Configurações carregadas:")
    print(f"   Email: {settings.DEFAULT_USER_EMAIL}")
    print(f"   Nome: {settings.DEFAULT_USER_NAME}")
    print(f"   Superusuário: {settings.DEFAULT_USER_IS_SUPERUSER}")
    print(f"   Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Local'}")
    
    # Criar usuário
    user = await create_default_user()
    if not user:
        print("\n❌ Falha na criação do usuário. Abortando.")
        return
    
    # Testar login
    login_success = await test_login()
    if not login_success:
        print("\n⚠️  Usuário criado mas login falhou.")
        return
    
    # Gerar token
    token = await generate_token()
    
    print("\n" + "=" * 60)
    print("✅ Processo concluído com sucesso!")
    print("\n🔑 Credenciais de acesso:")
    print(f"   Email: {settings.DEFAULT_USER_EMAIL}")
    print(f"   Senha: {settings.DEFAULT_USER_PASSWORD}")
    
    if token:
        print(f"\n🎫 Token JWT gerado:")
        print(f"   {token}")
        
        print(f"\n📝 Exemplo de uso com curl:")
        print(f"   curl -H 'Authorization: Bearer {token}' \\")
        print(f"        http://localhost:8000/auth/me")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
