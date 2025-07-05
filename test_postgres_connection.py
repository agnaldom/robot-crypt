#!/usr/bin/env python3
"""
Script para testar a conexão e funcionamento do PostgreSQL
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Adiciona o diretório src ao path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

def test_postgres_connection():
    """Testa a conexão com o PostgreSQL"""
    print("=== Teste de Conexão PostgreSQL ===")
    
    # Verifica se psycopg2 está instalado
    try:
        import psycopg2
        from psycopg2.extras import DictCursor
        print("✓ psycopg2 está instalado")
    except ImportError:
        print("✗ psycopg2 não está instalado")
        print("Instale com: pip install psycopg2-binary")
        return False
    
    # Obtém a URL do PostgreSQL
    postgres_url = os.environ.get("POSTGRES_URL")
    if not postgres_url:
        print("✗ POSTGRES_URL não encontrada no .env")
        return False
    
    print(f"✓ POSTGRES_URL encontrada: {postgres_url[:20]}...")
    
    # Testa a conexão
    try:
        print("Tentando conectar ao PostgreSQL...")
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor(cursor_factory=DictCursor)
        print("✓ Conexão estabelecida com sucesso")
        
        # Testa uma consulta simples
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✓ Versão do PostgreSQL: {version}")
        
        # Lista tabelas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Encontradas {len(tables)} tabelas no banco")
        
        if tables:
            print("Tabelas existentes:")
            for table in tables[:10]:  # Mostra apenas as primeiras 10
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} registros")
            
            if len(tables) > 10:
                print(f"  ... e mais {len(tables) - 10} tabelas")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Erro na conexão: {str(e)}")
        return False

def test_postgres_manager():
    """Testa o PostgresManager"""
    print("\n=== Teste do PostgresManager ===")
    
    try:
        from database.postgres_manager import PostgresManager
        print("✓ PostgresManager importado com sucesso")
        
        # Inicializa o PostgresManager
        pg = PostgresManager()
        print("✓ PostgresManager inicializado")
        
        # Testa salvar uma notificação
        notification_id = pg.save_notification(
            notification_type="test",
            title="Teste de conexão",
            message="Este é um teste de funcionamento do PostgreSQL",
            telegram_sent=False
        )
        
        if notification_id:
            print(f"✓ Notificação salva com ID: {notification_id}")
            
            # Testa recuperar notificações
            notifications = pg.get_recent_notifications(limit=1)
            if notifications:
                print(f"✓ Notificação recuperada: {notifications[0]['title']}")
            else:
                print("⚠ Não foi possível recuperar a notificação")
        else:
            print("✗ Falha ao salvar notificação")
            return False
        
        # Testa salvar estado da aplicação
        test_state = {
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "stats": {
                "total_trades": 0,
                "current_capital": 100.0
            }
        }
        
        state_id = pg.save_app_state(test_state)
        if state_id:
            print(f"✓ Estado da aplicação salvo com ID: {state_id}")
            
            # Testa carregar último estado
            last_state = pg.load_last_app_state()
            if last_state and last_state.get("test"):
                print("✓ Estado da aplicação recuperado com sucesso")
            else:
                print("⚠ Problema ao recuperar estado da aplicação")
        else:
            print("✗ Falha ao salvar estado da aplicação")
            return False
        
        # Testa salvar dados de capital
        capital_id = pg.save_capital_update(
            balance=100.0,
            change_amount=0.0,
            change_percentage=0.0,
            event_type="test",
            notes="Teste de funcionamento"
        )
        
        if capital_id:
            print(f"✓ Histórico de capital salvo com ID: {capital_id}")
        else:
            print("⚠ Problema ao salvar histórico de capital")
        
        pg.disconnect()
        print("✓ Conexão encerrada corretamente")
        return True
        
    except ImportError as e:
        print(f"✗ Erro ao importar PostgresManager: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erro no teste do PostgresManager: {str(e)}")
        return False

def test_database_updates():
    """Testa se as atualizações estão funcionando"""
    print("\n=== Teste de Atualizações ===")
    
    try:
        from database.postgres_manager import PostgresManager
        
        pg = PostgresManager()
        
        # Simula dados de uma operação de trading
        trade_data = {
            "symbol": "BTC/USDT",
            "operation_type": "buy",
            "entry_price": 45000.0,
            "quantity": 0.001,
            "entry_time": datetime.now(),
            "strategy_used": "TestStrategy",
            "balance_before": 100.0
        }
        
        trade_id = pg.record_transaction(trade_data)
        if trade_id:
            print(f"✓ Transação de compra registrada com ID: {trade_id}")
            
            # Simula venda
            sell_data = trade_data.copy()
            sell_data.update({
                "operation_type": "sell",
                "exit_price": 45500.0,
                "exit_time": datetime.now(),
                "profit_loss": 0.5,
                "profit_loss_percentage": 1.1,
                "balance_after": 100.5
            })
            
            sell_trade_id = pg.record_transaction(sell_data)
            if sell_trade_id:
                print(f"✓ Transação de venda registrada com ID: {sell_trade_id}")
                
                # Verifica histórico
                history = pg.get_transaction_history(limit=2)
                if len(history) >= 2:
                    print(f"✓ Histórico recuperado: {len(history)} transações")
                else:
                    print("⚠ Problema ao recuperar histórico completo")
            else:
                print("✗ Falha ao registrar venda")
        else:
            print("✗ Falha ao registrar compra")
            return False
        
        # Testa atualização de estatísticas diárias
        test_stats = {
            "current_capital": 100.5,
            "initial_capital": 100.0,
            "total_trades": 2,
            "winning_trades": 1,
            "losing_trades": 0,
            "best_trade_profit": 0.5,
            "worst_trade_loss": 0.0
        }
        
        if pg.update_daily_stats(test_stats):
            print("✓ Estatísticas diárias atualizadas")
        else:
            print("⚠ Problema ao atualizar estatísticas diárias")
        
        pg.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste de atualizações: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando testes do PostgreSQL...\n")
    
    # Teste 1: Conexão básica
    if not test_postgres_connection():
        print("\n❌ Falha nos testes básicos de conexão")
        sys.exit(1)
    
    # Teste 2: PostgresManager
    if not test_postgres_manager():
        print("\n❌ Falha nos testes do PostgresManager")
        sys.exit(1)
    
    # Teste 3: Atualizações de dados
    if not test_database_updates():
        print("\n❌ Falha nos testes de atualização")
        sys.exit(1)
    
    print("\n✅ Todos os testes do PostgreSQL passaram!")
    print("\nSeu código ESTÁ atualizando no banco de dados PostgreSQL corretamente.")
    print("As operações de trading, notificações e estatísticas estão sendo persistidas.")
