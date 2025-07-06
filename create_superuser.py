#!/usr/bin/env python3
"""
Script para criar usuário superuser específico no Robot-Crypt.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.config import settings
from src.core.security import get_password_hash
from src.database.database import async_engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func


# Definir modelo User diretamente para evitar problemas de dependência
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


async def create_superuser():
    """Create specific superuser."""
    print("🔐 Criando usuário superuser...")
    
    # Dados do usuário
    email = "agnaldo@qonnect.com.br"
    password = "@G071290nm"
    full_name = "Agnaldo Marinho"
    
    async with AsyncSession(async_engine) as session:
        try:
            # Verificar se o usuário já existe
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Usuário {email} já existe!")
                print("Deseja atualizar a senha? (s/n): ", end="")
                choice = input().lower()
                
                if choice in ['s', 'sim', 'y', 'yes']:
                    # Atualizar senha e tornar superuser
                    existing_user.hashed_password = get_password_hash(password)
                    existing_user.is_superuser = True
                    existing_user.is_active = True
                    existing_user.full_name = full_name
                    
                    await session.commit()
                    await session.refresh(existing_user)
                    
                    print("✅ Usuário atualizado com sucesso!")
                    print(f"   Email: {email}")
                    print(f"   Nome: {full_name}")
                    print(f"   Superuser: {existing_user.is_superuser}")
                    print(f"   Ativo: {existing_user.is_active}")
                else:
                    print("❌ Operação cancelada.")
                return
            
            # Criar novo usuário superuser
            superuser = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                is_active=True,
                is_superuser=True,
                preferences={
                    "theme": "dark",
                    "notifications": True,
                    "role": "superuser",
                    "timezone": "America/Sao_Paulo"
                }
            )
            
            session.add(superuser)
            await session.commit()
            await session.refresh(superuser)
            
            print("✅ Usuário superuser criado com sucesso!")
            print(f"   ID: {superuser.id}")
            print(f"   Email: {email}")
            print(f"   Nome: {full_name}")
            print(f"   Superuser: {superuser.is_superuser}")
            print(f"   Ativo: {superuser.is_active}")
            print(f"   Criado em: {superuser.created_at}")
            print()
            print("🔒 Senha criptografada e armazenada com segurança!")
            print()
            print("Agora você pode fazer login com:")
            print(f"   Email: {email}")
            print(f"   Senha: [sua senha]")
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário: {e}")
            await session.rollback()
            sys.exit(1)


async def main():
    """Função principal."""
    print("🚀 Robot-Crypt - Criação de Usuário Superuser")
    print(f"Database URL: {settings.DATABASE_URL}")
    print()
    
    try:
        await create_superuser()
        print()
        print("🎉 Processo concluído!")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
