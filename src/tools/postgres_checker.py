#!/usr/bin/env python3
"""
Script simplificado para verificar e preencher tabelas do PostgreSQL
"""
import os
import sys
import logging
import argparse
from datetime import datetime
import json
import random

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("db-fixer")

def check_postgres_tables():
    """Verifica as tabelas do PostgreSQL"""
    try:
        # Importação dinâmica para evitar erros se psycopg2 não estiver instalado
        import psycopg2
        from psycopg2.extras import DictCursor
    except ImportError:
        logger.error("O módulo psycopg2 não está instalado. Execute: pip install psycopg2-binary")
        return False

    # Obter credenciais do arquivo .env
    postgres_url = None
    try:
        with open(".env", "r") as env_file:
            for line in env_file:
                if line.strip().startswith("POSTGRES_URL="):
                    postgres_url = line.strip().split("=", 1)[1].strip()
                    # Remover aspas se existirem
                    if postgres_url.startswith('"') and postgres_url.endswith('"'):
                        postgres_url = postgres_url[1:-1]
                    break
    except Exception as e:
        logger.error(f"Erro ao ler arquivo .env: {str(e)}")
        return False

    if not postgres_url:
        logger.error("POSTGRES_URL não encontrada no arquivo .env")
        return False

    conn = None
    cursor = None
    try:
        # Conectar ao PostgreSQL
        logger.info(f"Conectando ao PostgreSQL...")
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Listar tabelas
        cursor.execute("""
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Encontradas {len(tables)} tabelas no banco de dados:")
        for table in sorted(tables):
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Verificar tamanho aproximado
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size
            """)
            size = cursor.fetchone()[0]
            
            logger.info(f"- {table}: {count} registros ({size})")
        
        # Verificar quais tabelas estão vazias
        empty_tables = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count == 0:
                empty_tables.append(table)
        
        if empty_tables:
            logger.warning(f"As seguintes tabelas estão vazias: {', '.join(empty_tables)}")
            
            # Perguntar ao usuário se deseja preencher tabelas vazias
            print("\nDeseja preencher as tabelas vazias com dados de exemplo? (s/n)")
            choice = input().lower()
            
            if choice == 's':
                for table in empty_tables:
                    fill_table_with_sample_data(conn, cursor, table)
        else:
            logger.info("Todas as tabelas contêm dados!")
            
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar tabelas PostgreSQL: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fill_table_with_sample_data(conn, cursor, table_name):
    """Preenche uma tabela com dados de exemplo"""
    try:
        logger.info(f"Preenchendo tabela {table_name} com dados de exemplo...")
        
        # Obter estrutura da tabela
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """)
        columns = cursor.fetchall()
        
        if not columns:
            logger.error(f"Não foi possível obter estrutura da tabela {table_name}")
            return False
            
        # Número de registros a inserir
        num_records = 5
            
        # Para cada registro a ser inserido
        for i in range(num_records):
            # Gerar dados para cada coluna
            data = {}
            for column in columns:
                col_name = column[0]
                col_type = column[1]
                
                # Pular colunas de ID que são autoincrement
                if col_name.lower() == 'id':
                    continue
                    
                # Gerar valor conforme o tipo de dados
                if 'timestamp' in col_type or 'date' in col_type:
                    data[col_name] = datetime.now().isoformat()
                elif 'int' in col_type:
                    data[col_name] = random.randint(1, 100)
                elif 'float' in col_type or 'numeric' in col_type or 'double' in col_type or 'real' in col_type:
                    data[col_name] = round(random.uniform(1, 100), 2)
                elif 'json' in col_type:
                    data[col_name] = json.dumps({"value": f"sample-{i+1}"})
                elif 'bool' in col_type:
                    data[col_name] = random.choice([True, False])
                else:  # string, text, etc.
                    data[col_name] = f"sample-{table_name}-{i+1}"
                    
            # Preparar SQL
            columns_to_insert = list(data.keys())
            values_to_insert = [data[col] for col in columns_to_insert]
            
            if not columns_to_insert:
                logger.warning(f"Não foi possível determinar colunas para inserir em {table_name}")
                continue
                
            placeholders = ", ".join(["%s"] * len(columns_to_insert))
            
            # SQL para inserir dados
            sql = f"""
                INSERT INTO {table_name} ({', '.join(columns_to_insert)})
                VALUES ({placeholders})
            """
            
            # Executar inserção
            cursor.execute(sql, values_to_insert)
            
        # Commit das alterações
        conn.commit()
        logger.info(f"✓ Tabela {table_name} preenchida com {num_records} registros de exemplo")
        return True
            
    except Exception as e:
        logger.error(f"Erro ao preencher tabela {table_name}: {str(e)}")
        conn.rollback()
        return False

if __name__ == "__main__":
    print("=== Verificador de Tabelas PostgreSQL ===")
    check_postgres_tables()
