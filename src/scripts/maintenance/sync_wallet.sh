#!/bin/bash
# Script para configurar e sincronizar dados da carteira Binance

# Verifica se temos as variáveis de ambiente necessárias
if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_API_SECRET" ]; then
    echo "Erro: As variáveis BINANCE_API_KEY e BINANCE_API_SECRET devem estar definidas."
    echo "Você pode configurá-las no arquivo .env ou exportá-las antes de executar este script."
    exit 1
fi

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado, criando um novo..."
    touch .env
fi

# Verifica se temos Python instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não está instalado. Por favor, instale o Python 3 antes de continuar."
    exit 1
fi


# Verifica dependências mínimas necessárias
echo "Verificando dependências Python mínimas..."
pip3 install psycopg2-binary python-dotenv requests

# Executa um script para verificar e corrigir a estrutura da tabela (se necessário)
echo "Verificando estrutura da tabela user_wallet..."
python3 -c "
import sys
from postgres_manager import PostgresManager
try:
    pg = PostgresManager()
    pg.connect()
    if pg.conn and pg.cursor:
        # Verifica se a coluna total_balance existe
        pg.cursor.execute(\"\"\"
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='user_wallet' AND column_name='total_balance'
        \"\"\")
        if not pg.cursor.fetchone():
            print('Adicionando coluna total_balance à tabela user_wallet...')
            pg.cursor.execute(\"\"\"
                ALTER TABLE user_wallet 
                ADD COLUMN IF NOT EXISTS total_balance DECIMAL(24, 8)
            \"\"\")
            pg.conn.commit()
            print('Coluna total_balance adicionada com sucesso.')
except Exception as e:
    print(f'Erro ao verificar estrutura da tabela: {str(e)}')
    sys.exit(1)
"

# Executa o script de sincronização de carteira
echo "Iniciando sincronização da carteira..."
python3 sync_wallet.py $@

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Sincronização da carteira concluída com sucesso!"
else
    echo "❌ Erro na sincronização da carteira. Verifique os logs para mais detalhes."
fi

exit $exit_code
