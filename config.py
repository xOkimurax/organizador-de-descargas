import os
import json
from pathlib import Path
from typing import Dict, List, Any

class Config:
    """Maneja toda la configuración de la aplicación"""
    
    def __init__(self):
        self.app_name = "OrganizadorDescargas"
        self.version = "1.0.0"
        
        # Intentar crear directorio de configuración
        try:
            self.config_dir = Path.home() / f".{self.app_name.lower()}"
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback: usar directorio temporal
            import tempfile
            self.config_dir = Path(tempfile.gettempdir()) / f"{self.app_name.lower()}_config"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            print(f"⚠️  Usando directorio temporal para configuración: {self.config_dir}")
        
        self.config_file = self.config_dir / "config.json"
        
        # Configuración por defecto
        self.default_config = {
            "carpeta_origen": str(Path.home() / "Downloads"),
            "crear_subcarpetas_fecha": False,
            "crear_subcarpetas_origen": False,  # Nueva opción
            "confirmar_antes_mover": True,
            "monitoreo_automatico": False,
            "eliminar_carpetas_vacias": True,
            "hacer_backup": False,
            "modo_principiante": True,
            "accion_desconocidos": "preguntar",  # preguntar, otros, ignorar
            "categorias_activas": {  # Nueva opción: qué categorías organizar
                "Documentos": True,
                "Imágenes": True,
                "Audio": True,
                "Videos": True,
                "Programas": True,
                "Comprimidos": True,
                "Otros": True
            },
            "carpetas_destino": {
                "Documentos": str(Path.home() / "Downloads" / "Documentos"),
                "Imágenes": str(Path.home() / "Downloads" / "Imágenes"),
                "Audio": str(Path.home() / "Downloads" / "Audio"),
                "Videos": str(Path.home() / "Downloads" / "Videos"),
                "Programas": str(Path.home() / "Downloads" / "Programas"),
                "Comprimidos": str(Path.home() / "Downloads" / "Comprimidos"),
                "Otros": str(Path.home() / "Downloads" / "Otros")
            }
        }
        
        # Categorías por defecto
        self.categorias_default = {
            "Documentos": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xlsx", ".xls", 
                          ".ppt", ".pptx", ".odt", ".ods", ".odp"],
            "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", 
                        ".tiff", ".ico", ".raw"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", 
                      ".m4v", ".3gp"],
            "Programas": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".app", ".pkg"],
            "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"]
        }
        
        # Magic numbers para detección inteligente
        self.magic_numbers = {
            b'\x89PNG\r\n\x1a\n': 'png',
            b'\xff\xd8\xff': 'jpg',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
            b'%PDF': 'pdf',
            b'PK\x03\x04': 'zip',
            b'Rar!\x1a\x07\x00': 'rar',
            b'\x7fELF': 'elf',
            b'MZ': 'exe'
        }
        
        self.config = self.cargar_configuracion()
        self.categorias = self.cargar_categorias()
        self.reglas_personalizadas = self.cargar_reglas_personalizadas()
    
    def cargar_configuracion(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo o crea una nueva"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge con defaults para nuevas opciones
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return self.default_config.copy()
    
    def guardar_configuracion(self):
        """Guarda la configuración actual"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def cargar_categorias(self) -> Dict[str, List[str]]:
        """Carga categorías personalizadas o usa las por defecto"""
        categorias_file = self.config_dir / "categorias.json"
        try:
            if categorias_file.exists():
                with open(categorias_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.categorias_default.copy()
        except Exception:
            return self.categorias_default.copy()
    
    def guardar_categorias(self):
        """Guarda las categorías actuales"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            categorias_file = self.config_dir / "categorias.json"
            with open(categorias_file, 'w', encoding='utf-8') as f:
                json.dump(self.categorias, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando categorías: {e}")
    
    def cargar_reglas_personalizadas(self) -> Dict[str, str]:
        """Carga reglas aprendidas por el usuario"""
        reglas_file = self.config_dir / "reglas_personalizadas.json"
        try:
            if reglas_file.exists():
                with open(reglas_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception:
            return {}
    
    def guardar_reglas_personalizadas(self):
        """Guarda las reglas personalizadas"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            reglas_file = self.config_dir / "reglas_personalizadas.json"
            with open(reglas_file, 'w', encoding='utf-8') as f:
                json.dump(self.reglas_personalizadas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando reglas personalizadas: {e}")
    
    def agregar_regla_personalizada(self, extension: str, categoria: str):
        """Agrega una nueva regla personalizada"""
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        self.reglas_personalizadas[extension] = categoria
        self.guardar_reglas_personalizadas()
        
        # También agregar a las categorías si no existe
        if categoria in self.categorias:
            if extension not in self.categorias[categoria]:
                self.categorias[categoria].append(extension)
                self.guardar_categorias()
    
    def obtener_categoria_por_extension(self, extension: str) -> str:
        """Obtiene la categoría de una extensión"""
        extension = extension.lower()
        
        # Primero verificar reglas personalizadas
        if extension in self.reglas_personalizadas:
            categoria = self.reglas_personalizadas[extension]
            # Verificar si la categoría está activa
            if self.config.get("categorias_activas", {}).get(categoria, True):
                return categoria
        
        # Luego verificar categorías por defecto
        for categoria, extensiones in self.categorias.items():
            if extension in extensiones:
                # Verificar si la categoría está activa
                if self.config.get("categorias_activas", {}).get(categoria, True):
                    return categoria
        
        # Si no está activa o no se encontró, verificar si "Otros" está activo
        if self.config.get("categorias_activas", {}).get("Otros", True):
            return "Otros"
        else:
            return None  # No organizar si "Otros" está desactivado
    
    def es_primera_vez(self) -> bool:
        """Verifica si es la primera vez que se ejecuta la aplicación"""
        return not self.config_file.exists()
    
    def obtener_carpeta_destino(self, categoria: str, carpeta_origen: Path = None) -> Path:
        """Obtiene la carpeta destino para una categoría"""
        if categoria in self.config["carpetas_destino"]:
            carpeta_base = Path(self.config["carpetas_destino"][categoria])
        else:
            # Crear carpeta por defecto
            carpeta_origen_config = Path(self.config["carpeta_origen"])
            carpeta_base = carpeta_origen_config / categoria
        
        # Verificar si se deben crear subcarpetas por origen
        if self.config.get("crear_subcarpetas_origen", False) and carpeta_origen:
            nombre_origen = carpeta_origen.name.lower()
            subcarpeta_origen = f"{categoria.lower()}-{nombre_origen}"
            return carpeta_base / subcarpeta_origen
        
        # Verificar si se deben crear subcarpetas por fecha
        if self.config.get("crear_subcarpetas_fecha", False):
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%Y-%m")
            return carpeta_base / fecha_actual
        
        return carpeta_base
    
    def categoria_esta_activa(self, categoria: str) -> bool:
        """Verifica si una categoría está configurada para ser organizada"""
        return self.config.get("categorias_activas", {}).get(categoria, True)
    
    def activar_categoria(self, categoria: str, activa: bool):
        """Activa o desactiva una categoría para organización"""
        if "categorias_activas" not in self.config:
            self.config["categorias_activas"] = {}
        self.config["categorias_activas"][categoria] = activa
        self.guardar_configuracion()
    
    def obtener_categorias_activas(self) -> List[str]:
        """Obtiene la lista de categorías que están activas para organización"""
        categorias_activas = []
        for categoria in self.categorias.keys():
            if self.categoria_esta_activa(categoria):
                categorias_activas.append(categoria)
        return categorias_activas
    
    def actualizar_configuracion(self, nuevos_valores: Dict[str, Any]):
        """Actualiza la configuración con nuevos valores"""
        self.config.update(nuevos_valores)
        self.guardar_configuracion()

# Instancia global de configuración
config = Config()