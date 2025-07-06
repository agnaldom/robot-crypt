#!/usr/bin/env python3
"""
Módulo de monitoramento de saúde para o Robot-Crypt
"""
import os
import gc
import logging
from datetime import datetime, timedelta

# Tenta importar psutil, mas continua mesmo se não estiver disponível
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Aviso: O módulo 'psutil' não está disponível. As funcionalidades de monitoramento serão limitadas.")

# Configure logging
logger = logging.getLogger('robot-crypt')

def check_system_health(notify_function=None, mem_threshold_pct=85, trigger_gc_at_pct=80):
    """
    Verifica a saúde do sistema e registra informações relevantes
    
    Args:
        notify_function: Função opcional para enviar notificações em caso de alerta
        mem_threshold_pct: Porcentagem de uso de memória a partir da qual emitir alertas
        trigger_gc_at_pct: Porcentagem de uso de memória a partir da qual acionar coleta de lixo
    
    Returns:
        dict: Dicionário com métricas de saúde do sistema ou None se psutil não estiver disponível
    """
    # Verifica se psutil está disponível
    if not PSUTIL_AVAILABLE:
        logger.warning("Não é possível verificar a saúde do sistema: módulo psutil não está disponível")
        if notify_function:
            try:
                notify_function("⚠️ Monitoramento limitado: módulo psutil não disponível")
            except Exception as e:
                logger.error(f"Erro ao enviar notificação: {str(e)}")
        return None
        
    try:
        # Coleta informações de memória
        memory = psutil.virtual_memory()
        mem_usage_percent = memory.percent
        mem_available_mb = memory.available / (1024 * 1024)
        
        # Se o uso de memória ultrapassou o limite para coleta de lixo, acione o GC
        if mem_usage_percent >= trigger_gc_at_pct:
            logger.warning(f"Uso de memória alto ({mem_usage_percent}%). Acionando coleta de lixo.")
            gc_collected = gc.collect(generation=2)  # Forçar coleta completa
            logger.info(f"Coletados {gc_collected} objetos durante a coleta de lixo")
            
            # Refaz a medição após a coleta
            memory = psutil.virtual_memory()
            mem_usage_percent = memory.percent
            mem_available_mb = memory.available / (1024 * 1024)
            
            logger.info(f"Uso de memória após coleta: {mem_usage_percent}%")
        
        # Coleta informações de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Coleta informações de disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Verifica espaço para logs
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(log_dir):
            # Obtém o tamanho total de todos os arquivos de log
            log_size_mb = sum(os.path.getsize(os.path.join(log_dir, f)) for f in os.listdir(log_dir) 
                             if os.path.isfile(os.path.join(log_dir, f))) / (1024 * 1024)
                             
            # Rotaciona logs se necessário (mais de 500MB de logs)
            if log_size_mb > 500:
                logger.warning(f"Diretório de logs muito grande ({log_size_mb:.1f} MB). Verificar rotacionamento.")
                if notify_function:
                    try:
                        notify_function(f"⚠️ Atenção: Diretório de logs ocupando {log_size_mb:.1f} MB")
                    except Exception as e:
                        logger.error(f"Erro ao enviar notificação: {str(e)}")
        
        # Registra informações de saúde
        logger.info("=== SISTEMA DE MONITORAMENTO DE SAÚDE ===")
        logger.info(f"Horário da verificação: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Uso de memória: {mem_usage_percent:.1f}% (Disponível: {mem_available_mb:.1f} MB)")
        logger.info(f"Uso de CPU: {cpu_percent:.1f}% (Núcleos: {cpu_count})")
        logger.info(f"Uso de disco: {disk_percent:.1f}% (Livre: {disk_free_gb:.1f} GB)")
        
        # Alerta se o disco estiver muito cheio
        if disk_percent > 90:
            logger.warning(f"Disco quase cheio! {disk_percent}% usado, apenas {disk_free_gb:.1f} GB livre")
            if notify_function:
                try:
                    notify_function(f"🚨 CRÍTICO: Disco quase cheio! {disk_percent}% usado, apenas {disk_free_gb:.1f} GB livre")
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação: {str(e)}")
        
        # Verifica se há processos consumindo muita CPU ou memória
        high_usage_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cpu_percent'] > 50 or proc.info['memory_percent'] > 20:
                    high_usage_procs.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if high_usage_procs:
            logger.info(f"Processos com alto consumo detectados: {len(high_usage_procs)}")
            for proc in high_usage_procs[:3]:  # Limita a 3 processos para não sobrecarregar os logs
                logger.info(f"  PID: {proc['pid']}, Nome: {proc['name']}, CPU: {proc['cpu']:.1f}%, Memória: {proc['memory']:.1f}%")
        
        # Verifica se há problemas graves
        alerts = []
        if mem_usage_percent > 90:
            msg = "ALERTA DE SAÚDE: Uso de memória muito alto (>90%)!"
            logger.warning(msg)
            alerts.append(msg)
        if cpu_percent > 90:
            msg = "ALERTA DE SAÚDE: Uso de CPU muito alto (>90%)!"
            logger.warning(msg)
            alerts.append(msg)
        if disk_percent > 90:
            msg = "ALERTA DE SAÚDE: Uso de disco muito alto (>90%)!"
            logger.warning(msg)
            alerts.append(msg)
            
        # Notifica problemas se a função de notificação foi fornecida
        if alerts and notify_function:
            try:
                alert_message = "⚠️ ALERTAS DE SAÚDE DO SISTEMA:\n" + "\n".join(alerts)
                notify_function(alert_message)
            except Exception as e:
                logger.error(f"Erro ao enviar notificação de saúde: {str(e)}")
            
        # Força coleta de lixo para liberar memória
        collected = gc.collect()
        logger.info(f"Objetos coletados pelo garbage collector: {collected}")
        
        return {
            'memory_percent': mem_usage_percent,
            'memory_available_mb': mem_available_mb,
            'cpu_percent': cpu_percent,
            'disk_percent': disk_percent,
            'disk_free_gb': disk_free_gb,
            'timestamp': datetime.now().isoformat(),
            'high_usage_processes': len(high_usage_procs)
        }
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do sistema: {str(e)}")
        return None

def log_process_tree():
    """
    Registra a árvore de processos Python em execução
    """
    # Verifica se psutil está disponível
    if not PSUTIL_AVAILABLE:
        logger.warning("Não é possível registrar árvore de processos: módulo psutil não está disponível")
        return
        
    try:
        current_process = psutil.Process(os.getpid())
        logger.info(f"Processo atual: PID {current_process.pid}, Nome: {current_process.name()}")
        
        # Registra os processos filhos
        children = current_process.children(recursive=True)
        if children:
            logger.info(f"Processos filhos detectados: {len(children)}")
            for i, child in enumerate(children):
                try:
                    logger.info(f"  Filho {i+1}: PID {child.pid}, Nome: {child.name()}, Status: {child.status()}")
                except psutil.NoSuchProcess:
                    logger.info(f"  Filho {i+1}: Processo não encontrado (já encerrado)")
        else:
            logger.info("Nenhum processo filho detectado")
    except Exception as e:
        logger.error(f"Erro ao registrar árvore de processos: {str(e)}")

def clean_old_log_files(max_days_to_keep=30, max_total_size_mb=500):
    """
    Remove arquivos de log antigos para liberar espaço em disco
    
    Args:
        max_days_to_keep (int): Número máximo de dias para manter logs
        max_total_size_mb (float): Tamanho máximo total permitido para logs em MB
        
    Returns:
        tuple: (int, float) - Quantidade de arquivos removidos e espaço liberado em MB
    """
    logger.info(f"Verificando logs antigos para limpeza (>={max_days_to_keep} dias ou >={max_total_size_mb} MB total)")
    
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        logger.warning(f"Diretório de logs não encontrado: {log_dir}")
        return 0, 0
    
    # Data limite para manter logs
    cutoff_date = datetime.now() - timedelta(days=max_days_to_keep)
    
    # Lista todos os arquivos de log com suas informações
    log_files = []
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path) and filename.startswith("robot-crypt-"):
            try:
                size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                log_files.append((file_path, size, datetime.fromtimestamp(mtime)))
            except Exception as e:
                logger.error(f"Erro ao obter informações do arquivo {file_path}: {str(e)}")
    
    # Ordena por data (mais antigo primeiro)
    log_files.sort(key=lambda x: x[2])
    
    # Calcula o tamanho total
    total_size = sum(f[1] for f in log_files) / (1024 * 1024)  # MB
    
    # Se o tamanho total for menor que o limite e não houver arquivos antigos, não faz nada
    if total_size <= max_total_size_mb and all(f[2] >= cutoff_date for f in log_files):
        logger.info(f"Nenhum log antigo para remover. Tamanho total: {total_size:.2f} MB")
        return 0, 0
    
    # Remove arquivos antigos e/ou reduz o tamanho total
    removed_files = 0
    freed_space = 0
    
    for file_path, size, mtime in log_files:
        # Se já atingimos os requisitos de tamanho e não há mais arquivos antigos, paramos
        current_total = total_size - (freed_space / (1024 * 1024))
        if current_total <= max_total_size_mb and mtime >= cutoff_date:
            break
            
        # Remove o arquivo se for antigo ou se ainda precisamos liberar espaço
        if mtime < cutoff_date or current_total > max_total_size_mb:
            try:
                os.remove(file_path)
                removed_files += 1
                freed_space += size
                logger.info(f"Removido log antigo: {os.path.basename(file_path)} ({size / (1024 * 1024):.2f} MB)")
            except Exception as e:
                logger.error(f"Erro ao remover arquivo {file_path}: {str(e)}")
    
    freed_space_mb = freed_space / (1024 * 1024)
    logger.info(f"Limpeza de logs concluída: {removed_files} arquivos removidos, {freed_space_mb:.2f} MB liberados")
    return removed_files, freed_space_mb
