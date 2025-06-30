from .performance_metrics import PerformanceMetrics

try:
    from .robot_crypt_dashboard import RobotCryptDashboard
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Erro ao importar RobotCryptDashboard: {e}. O dashboard não estará disponível.")
    
    # Classe substituta para evitar erros quando o dash não está instalado
    class RobotCryptDashboard:
        def __init__(self, *args, **kwargs):
            self.available = False
            print("AVISO: Dashboard não disponível. O módulo 'dash' não está instalado.")
            
        def start(self):
            pass
            
        def update(self, *args, **kwargs):
            pass
