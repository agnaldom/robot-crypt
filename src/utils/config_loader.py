"""
Utilitário para carregar e gerenciar configurações do sistema de treinamento.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """
    Classe para carregar e gerenciar configurações do sistema.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o carregador de configurações.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        if config_path is None:
            # Usa configuração padrão se não especificado
            self.config_path = self._get_default_config_path()
        else:
            self.config_path = Path(config_path)
        
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """
        Retorna o caminho padrão para o arquivo de configuração.
        """
        # Procura pelo arquivo de configuração na raiz do projeto
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        config_path = project_root / "config" / "training_config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {config_path}"
            )
        
        return config_path
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega o arquivo de configuração YAML.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            # Processa caminhos relativos
            config = self._process_paths(config)
            
            return config
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar configuração: {e}")
    
    def _process_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa caminhos relativos nas configurações.
        """
        project_root = self.config_path.parent.parent
        
        # Processa caminhos específicos
        path_keys = [
            ('data', 'database_path'),
            ('model', 'model_path'),
            ('training', 'training_history_path'),
            ('training', 'backup_path'),
            ('logging', 'files', 'training'),
            ('logging', 'files', 'data_collection'),
            ('logging', 'files', 'signals'),
            ('logging', 'files', 'errors'),
        ]
        
        for path_key in path_keys:
            self._process_path_key(config, path_key, project_root)
        
        return config
    
    def _process_path_key(self, config: Dict[str, Any], path_key: tuple, project_root: Path):
        """
        Processa uma chave de caminho específica.
        """
        try:
            current = config
            for key in path_key[:-1]:
                current = current[key]
            
            path_value = current[path_key[-1]]
            if isinstance(path_value, str) and not os.path.isabs(path_value):
                # Converte caminho relativo para absoluto
                current[path_key[-1]] = str(project_root / path_value)
        except KeyError:
            # Chave não existe na configuração
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor da configuração usando notação de ponto.
        
        Args:
            key: Chave da configuração (ex: 'data.database_path')
            default: Valor padrão se a chave não existir
        
        Returns:
            Valor da configuração
        """
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Define um valor na configuração usando notação de ponto.
        
        Args:
            key: Chave da configuração (ex: 'data.database_path')
            value: Novo valor
        """
        keys = key.split('.')
        current = self.config
        
        # Navega até o penúltimo nível
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Define o valor final
        current[keys[-1]] = value
    
    def get_data_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de dados.
        """
        return self.get('data', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """
        Retorna configurações do modelo.
        """
        return self.get('model', {})
    
    def get_features_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de features.
        """
        return self.get('features', {})
    
    def get_signals_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de sinais.
        """
        return self.get('signals', {})
    
    def get_training_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de treinamento.
        """
        return self.get('training', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de logging.
        """
        return self.get('logging', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de performance.
        """
        return self.get('performance', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de segurança.
        """
        return self.get('security', {})
    
    def get_notifications_config(self) -> Dict[str, Any]:
        """
        Retorna configurações de notificações.
        """
        return self.get('notifications', {})
    
    def create_directories(self):
        """
        Cria diretórios necessários baseados nas configurações.
        """
        directories = [
            self.get('data.database_path'),
            self.get('model.model_path'),
            self.get('training.training_history_path'),
            self.get('training.backup_path'),
            self.get('logging.files.training'),
            self.get('logging.files.data_collection'),
            self.get('logging.files.signals'),
            self.get('logging.files.errors'),
        ]
        
        for path in directories:
            if path:
                # Cria o diretório pai se não existir
                Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    def validate_config(self) -> bool:
        """
        Valida se a configuração está correta.
        
        Returns:
            True se a configuração é válida
        """
        required_keys = [
            'data.database_path',
            'model.model_path',
            'model.type',
            'training.min_samples',
            'signals.confidence_thresholds.buy',
            'signals.confidence_thresholds.sell',
            'logging.level',
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                print(f"Configuração obrigatória ausente: {key}")
                return False
        
        # Valida tipo de modelo
        valid_models = ['random_forest', 'gradient_boosting', 'neural_network']
        if self.get('model.type') not in valid_models:
            print(f"Tipo de modelo inválido: {self.get('model.type')}")
            return False
        
        # Valida limites de confiança
        buy_threshold = self.get('signals.confidence_thresholds.buy')
        sell_threshold = self.get('signals.confidence_thresholds.sell')
        
        if not (0 <= buy_threshold <= 1) or not (0 <= sell_threshold <= 1):
            print("Limites de confiança devem estar entre 0 e 1")
            return False
        
        return True
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Salva a configuração atual em um arquivo YAML.
        
        Args:
            output_path: Caminho de saída (usa o caminho original se não especificado)
        """
        if output_path is None:
            output_path = self.config_path
        else:
            output_path = Path(output_path)
        
        # Cria o diretório se não existir
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
    
    def __str__(self) -> str:
        """
        Representação string da configuração.
        """
        return f"ConfigLoader(config_path={self.config_path})"
    
    def __repr__(self) -> str:
        """
        Representação para debug.
        """
        return self.__str__()


# Instância global do carregador de configurações
config = ConfigLoader()


def get_config() -> ConfigLoader:
    """
    Retorna a instância global do carregador de configurações.
    
    Returns:
        Instância do ConfigLoader
    """
    return config


def reload_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Recarrega a configuração.
    
    Args:
        config_path: Novo caminho da configuração (opcional)
    
    Returns:
        Nova instância do ConfigLoader
    """
    global config
    config = ConfigLoader(config_path)
    return config
