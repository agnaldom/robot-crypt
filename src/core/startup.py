"""
Módulo de inicialização do Robot-Crypt.
Responsável por configurar o sistema na inicialização, incluindo a criação do superadmin.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from src.core.config import settings
from src.database.database import async_session_maker
from src.models.user import User
from src.schemas.user import UserCreate
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


async def create_superadmin() -> Optional[User]:
    """
    Cria o superadmin do sistema se não existir.
    
    Returns:
        User: O usuário superadmin criado ou existente, ou None em caso de erro.
    """
    try:
        async with async_session_maker() as db:
            user_service = UserService(db)
            
            # Verificar se o superadmin já existe
            existing_user = await user_service.get_by_email(settings.USER_EMAIL)
            
            if existing_user:
                logger.info(f"Superadmin já existe: {settings.USER_EMAIL}")
                
                # Verificar se é superuser, caso contrário, promover
                if not existing_user.is_superuser:
                    existing_user.is_superuser = True
                    await db.commit()
                    await db.refresh(existing_user)
                    logger.info(f"Usuário {settings.USER_EMAIL} promovido a superadmin")
                
                return existing_user
            
            # Criar novo superadmin
            logger.info(f"Criando superadmin: {settings.USER_EMAIL}")
            
            user_data = UserCreate(
                email=settings.USER_EMAIL,
                password=settings.USER_PASSWORD,
                full_name=settings.USER_NAME,
                is_superuser=True,
                is_active=True
            )
            
            new_user = await user_service.create(user_data)
            
            logger.info(f"Superadmin criado com sucesso: {new_user.email} (ID: {new_user.id})")
            
            return new_user
            
    except IntegrityError as e:
        logger.warning(f"Superadmin já existe (constraint violation): {str(e)}")
        # Tentar buscar o usuário existente
        try:
            async with async_session_maker() as db:
                user_service = UserService(db)
                return await user_service.get_by_email(settings.USER_EMAIL)
        except Exception:
            return None
            
    except Exception as e:
        logger.error(f"Erro ao criar superadmin: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def initialize_database():
    """
    Inicializa o banco de dados com dados essenciais.
    """
    logger.info("Inicializando banco de dados...")
    
    try:
        # Verificar se o banco está acessível
        async with async_session_maker() as db:
            # Teste simples de conectividade
            await db.execute(text("SELECT 1"))
            logger.info("Conexão com banco de dados estabelecida")
        
        # Criar superadmin
        superadmin = await create_superadmin()
        if superadmin:
            logger.info("Inicialização do banco concluída com sucesso")
        else:
            logger.warning("Falha ao criar/verificar superadmin")
            
    except Exception as e:
        logger.error(f"Erro na inicialização do banco de dados: {str(e)}")
        raise


async def startup_sequence():
    """
    Sequência completa de inicialização do sistema.
    """
    logger.info("=" * 50)
    logger.info("🚀 Iniciando Robot-Crypt API")
    logger.info("=" * 50)
    
    try:
        # Verificar configurações essenciais
        logger.info("📋 Verificando configurações...")
        
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY não configurada")
        
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL não configurada")
            
        logger.info("✅ Configurações verificadas")
        
        # Inicializar banco de dados
        await initialize_database()
        
        # Log das configurações importantes (sem dados sensíveis)
        logger.info("🔧 Configurações do sistema:")
        logger.info(f"   App: {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"   Host: {settings.HOST}:{settings.PORT}")
        logger.info(f"   Debug: {settings.DEBUG}")
        logger.info(f"   Database: {'PostgreSQL' if 'postgresql' in settings.DATABASE_URL else 'Outro'}")
        logger.info(f"   Superadmin: {settings.USER_EMAIL}")
        logger.info(f"   CORS Origins: {len(settings.ALLOWED_ORIGINS)} configuradas")
        logger.info(f"   Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos")
        
        logger.info("=" * 50)
        logger.info("✅ Sistema inicializado com sucesso!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ Falha na inicialização do sistema!")
        logger.error(f"Erro: {str(e)}")
        logger.error("=" * 50)
        raise


def run_startup():
    """
    Executa a sequência de inicialização de forma síncrona.
    Para ser chamada em contextos síncronos.
    """
    try:
        asyncio.run(startup_sequence())
    except Exception as e:
        logger.error(f"Erro crítico na inicialização: {str(e)}")
        raise


# Função de conveniência para FastAPI
async def startup_event():
    """
    Evento de inicialização para FastAPI.
    """
    await startup_sequence()
