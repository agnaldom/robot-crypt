#!/usr/bin/env python3
"""
Módulo de monitoramento de saúde para o Robot-Crypt
"""
import os
import gc
import logging
from datetime import datetime

# Tenta importar psutil, mas continua mesmo se não estiver disponível
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Aviso: O módulo 'psutil' não está disponível. As funcionalidades de monitoramento serão limitadas.")

# Configure logging
logger = logging.getLogger('robot-crypt')

def check_system_health(notify_function=None):
    """
    Verifica a saúde do sistema e registra informações relevantes
    
    Args:
        notify_function: Função opcional para enviar notificações em caso de alerta
    
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
        
        # Coleta informações de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Coleta informações de disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Registra informações de saúde
        logger.info("=== SISTEMA DE MONITORAMENTO DE SAÚDE ===")
        logger.info(f"Horário da verificação: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Uso de memória: {mem_usage_percent:.1f}% (Disponível: {mem_available_mb:.1f} MB)")
        logger.info(f"Uso de CPU: {cpu_percent:.1f}% (Núcleos: {cpu_count})")
        logger.info(f"Uso de disco: {disk_percent:.1f}% (Livre: {disk_free_gb:.1f} GB)")
        
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
