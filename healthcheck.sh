#!/bin/bash
# Script para verificar o estado de saúde do container Robot-Crypt

# Verifica se o processo Python ainda está em execução
if pgrep -f "python main.py" > /dev/null; then
    echo "Status: OK - Processo Python em execução"
    exit 0
else
    # Verifica logs recentes para determinar o estado
    log_file=$(ls -t /app/logs/robot-crypt-*.log | head -1)
    
    if [ -f "$log_file" ]; then
        last_log_time=$(stat -c %Y "$log_file")
        current_time=$(date +%s)
        time_diff=$((current_time - last_log_time))
        
        # Se os logs foram atualizados nos últimos 10 minutos, pode estar funcionando corretamente
        if [ $time_diff -lt 600 ]; then
            echo "Status: WARNING - Processo Python não encontrado, mas logs recentes"
            exit 0
        fi
        
        # Verifica se contém mensagens de erro nos últimos logs
        if tail -n 50 "$log_file" | grep -i "erro\|error\|exception\|falha"; then
            echo "Status: ERROR - Erros encontrados nos logs recentes"
            exit 1
        fi
    fi
    
    echo "Status: UNKNOWN - Não foi possível determinar o estado"
    exit 1
fi
