"""
Gerenciador de configurações do MeetAI
"""

import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "settings.json"
        self.api_keys_file = self.config_dir / "api_keys.json"
        
        # Criar diretório se não existir
        self.config_dir.mkdir(exist_ok=True)
        
        # Configurações padrão
        self.default_config = {
            "audio": {
                "sample_rate": 44100,
                "channels": 2,
                "chunk_size": 1024,
                "input_device": None
            },
            "ai": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 1500,
                "temperature": 0.3,
                "language": "pt"
            },
            "ui": {
                "theme": "clam",
                "window_size": "900x700",
                "auto_save": False
            },
            "output": {
                "format": "txt",
                "directory": "outputs",
                "include_timestamp": True
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self):
        """Carregar configurações do arquivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Mesclar com configurações padrão
                    return self._merge_config(self.default_config, config)
            else:
                # Criar arquivo com configurações padrão
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Salvar configurações no arquivo"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            return False
    
    def get(self, key_path, default=None):
        """Obter valor de configuração usando notação de ponto"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """Definir valor de configuração usando notação de ponto"""
        keys = key_path.split('.')
        config = self.config
        
        # Navegar até o último nível
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Definir o valor
        config[keys[-1]] = value
        
        # Salvar configurações
        return self.save_config()
    
    def load_api_keys(self):
        """Carregar chaves de API"""
        try:
            if self.api_keys_file.exists():
                with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erro ao carregar chaves API: {e}")
            return {}
    
    def save_api_keys(self, api_keys):
        """Salvar chaves de API"""
        try:
            with open(self.api_keys_file, 'w', encoding='utf-8') as f:
                json.dump(api_keys, f, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar chaves API: {e}")
            return False
    
    def get_api_key(self, service):
        """Obter chave de API específica"""
        api_keys = self.load_api_keys()
        return api_keys.get(f"{service}_api_key")
    
    def set_api_key(self, service, key):
        """Definir chave de API específica"""
        api_keys = self.load_api_keys()
        api_keys[f"{service}_api_key"] = key
        return self.save_api_keys(api_keys)
    
    def _merge_config(self, default, user):
        """Mesclar configuração do usuário com padrão"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def reset_to_defaults(self):
        """Restaurar configurações padrão"""
        self.config = self.default_config.copy()
        return self.save_config()
    
    def export_config(self, file_path):
        """Exportar configurações para arquivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar configurações: {e}")
            return False
    
    def import_config(self, file_path):
        """Importar configurações de arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validar e mesclar configurações
            self.config = self._merge_config(self.default_config, imported_config)
            return self.save_config()
        except Exception as e:
            print(f"Erro ao importar configurações: {e}")
            return False