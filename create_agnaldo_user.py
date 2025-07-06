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
from src.database.database import async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def create_superuser():
    """Create specific superuser using raw SQL."""
    print("🔐 Criando usuário superuser...")
    
    # Dados do usuário
    email = "agnaldo@qonnect.com.br"
    password = "@G071290nm"
    full_name = "Agnaldo Marinho"
    
    # Criptografar a senha
    hashed_password = get_password_hash(password)
    
    async with AsyncSession(async_engine) as session:
        try:
            # Verificar se o usuário já existe
            result = await session.execute(
                text("SELECT id, email, is_superuser FROM users WHERE email = :email"),
                {"email": email}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"⚠️  Usuário {email} já existe!")
                print("Deseja atualizar a senha e tornar superuser? (s/n): ", end="")
                choice = input().lower()
                
                if choice in ['s', 'sim', 'y', 'yes']:
                    # Atualizar senha e tornar superuser
                    await session.execute(
                        text("""
                            UPDATE users 
                            SET hashed_password = :password,
                                is_superuser = true,
                                is_active = true,
                                full_name = :full_name,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE email = :email
                        """),
                        {
                            "password": hashed_password,
                            "full_name": full_name,
                            "email": email
                        }
                    )
                    
                    await session.commit()
                    
                    print("✅ Usuário atualizado com sucesso!")
                    print(f"   Email: {email}")
                    print(f"   Nome: {full_name}")
                    print(f"   Superuser: True")
                    print(f"   Ativo: True")
                else:
                    print("❌ Operação cancelada.")
                return
            
            # Criar novo usuário superuser
            await session.execute(
                text("""
                    INSERT INTO users (
                        email, 
                        hashed_password, 
                        full_name, 
                        is_active, 
                        is_superuser, 
                        preferences,
                        created_at,
                        updated_at
                    ) VALUES (
                        :email,
                        :password,
                        :full_name,
                        true,
                        true,
                        :preferences,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                """),
                {
                    "email": email,
                    "password": hashed_password,
                    "full_name": full_name,
                    "preferences": '{"theme": "dark", "notifications": true, "role": "superuser", "timezone": "America/Sao_Paulo"}'
                }
            )
            
            await session.commit()
            
            # Buscar o usuário criado para mostrar os dados
            result = await session.execute(
                text("SELECT id, email, full_name, is_superuser, is_active, created_at FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            
            print("✅ Usuário superuser criado com sucesso!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nome: {user.full_name}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Ativo: {user.is_active}")
            print(f"   Criado em: {user.created_at}")
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
