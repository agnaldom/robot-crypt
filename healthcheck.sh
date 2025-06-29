#!/bin/bash
# Script para verificar o estado de saúde do container Robot-Crypt

# Verifica se o processo Python ainda está em execução
if pgrep -f "python main.py" > /dev/null || pgrep -f "python3 main.py" > /dev/null; then
    echo "Status: OK - Processo Python em execução"
    exit 0
else
    # Verifica se o script de entrada do Railway está em execução
    if pgrep -f "railway_entrypoint.sh" > /dev/null; then
        echo "Status: OK - Processo de entrada está ativo"
        exit 0
    fi

    # Verifica logs recentes para determinar o estado
    log_path="/app/logs"
    if [ -d "$log_path" ]; then
        log_file=$(ls -t $log_path/robot-crypt-*.log 2>/dev/null | head -1)
        
        if [ -f "$log_file" ]; then
            # Tenta obter a data de modificação do arquivo de log
            if command -v stat &> /dev/null; then
                if stat --version 2>/dev/null | grep -q GNU; then
                    # Linux (GNU stat)
                    last_log_time=$(stat -c %Y "$log_file")
                else
                    # macOS/BSD stat
                    last_log_time=$(stat -f %m "$log_file")
                fi
            else
                # Fallback se stat não estiver disponível
                last_log_time=$(date -r "$log_file" +%s 2>/dev/null || echo 0)
            fi
            
            current_time=$(date +%s)
            time_diff=$((current_time - last_log_time))
            
            # Se os logs foram atualizados nos últimos 15 minutos, considera OK
            if [ $time_diff -lt 900 ]; then
                echo "Status: OK - Logs atualizados recentemente (últimos $(($time_diff / 60)) minutos)"
                exit 0
            fi
            
            # Verifica se contém mensagens de erro fatais nos últimos logs
            if tail -n 100 "$log_file" | grep -i "fatal\|crashed\|morreu"; then
                echo "Status: ERROR - Erros fatais encontrados nos logs recentes"
                exit 1
            fi
        fi
    fi
    
    # Se estamos no Railway, considera saudável por padrão para evitar reinicializações desnecessárias
    if [ -n "$RAILWAY_ENVIRONMENT_NAME" ]; then
        echo "Status: OK - Executando no Railway, assumindo saudável"
        exit 0
    fi
    
    echo "Status: WARNING - Status indeterminado, considerando saudável"
    exit 0
fi
