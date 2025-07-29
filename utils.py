import os
import hashlib
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class FileUtils:
    """Utilidades para manejo de archivos"""
    
    @staticmethod
    def obtener_magic_number(archivo_path: Path, bytes_count: int = 10) -> bytes:
        """Lee los primeros bytes de un archivo para detectar su tipo"""
        try:
            with open(archivo_path, 'rb') as f:
                return f.read(bytes_count)
        except Exception:
            return b''
    
    @staticmethod
    def detectar_tipo_por_contenido(archivo_path: Path) -> Optional[str]:
        """Detecta el tipo de archivo analizando su contenido"""
        from config import config
        
        magic = FileUtils.obtener_magic_number(archivo_path)
        
        for signature, file_type in config.magic_numbers.items():
            if magic.startswith(signature):
                return file_type
        
        return None
    
    @staticmethod
    def es_archivo_en_uso(archivo_path: Path) -> bool:
        """Verifica si un archivo está siendo usado por otro proceso"""
        try:
            # Intenta abrir el archivo en modo exclusivo
            with open(archivo_path, 'r+b'):
                pass
            return False
        except (PermissionError, OSError):
            return True
    
    @staticmethod
    def calcular_hash_archivo(archivo_path: Path) -> str:
        """Calcula el hash MD5 de un archivo para detectar duplicados"""
        try:
            hash_md5 = hashlib.md5()
            with open(archivo_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def formatear_tamaño(tamaño_bytes: int) -> str:
        """Convierte bytes a formato legible (KB, MB, GB)"""
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamaño_bytes < 1024.0:
                return f"{tamaño_bytes:.1f} {unidad}"
            tamaño_bytes /= 1024.0
        return f"{tamaño_bytes:.1f} PB"
    
    @staticmethod
    def obtener_info_archivo(archivo_path: Path) -> Dict:
        """Obtiene información completa de un archivo"""
        try:
            stat = archivo_path.stat()
            return {
                'nombre': archivo_path.name,
                'extension': archivo_path.suffix.lower(),
                'tamaño': stat.st_size,
                'tamaño_legible': FileUtils.formatear_tamaño(stat.st_size),
                'fecha_modificacion': datetime.fromtimestamp(stat.st_mtime),
                'fecha_creacion': datetime.fromtimestamp(stat.st_ctime),
                'es_archivo': archivo_path.is_file(),
                'es_directorio': archivo_path.is_dir(),
                'ruta_completa': str(archivo_path),
                'en_uso': FileUtils.es_archivo_en_uso(archivo_path)
            }
        except Exception as e:
            return {
                'nombre': archivo_path.name,
                'extension': archivo_path.suffix.lower() if archivo_path.suffix else '',
                'tamaño': 0,
                'tamaño_legible': '0 B',
                'fecha_modificacion': datetime.now(),
                'fecha_creacion': datetime.now(),
                'es_archivo': archivo_path.is_file(),
                'es_directorio': archivo_path.is_dir(),
                'ruta_completa': str(archivo_path),
                'en_uso': False,
                'error': str(e)
            }
    
    @staticmethod
    def sanitizar_nombre_archivo(nombre: str) -> str:
        """Sanitiza nombres de archivos problemáticos"""
        import re
        
        # Caracteres no permitidos en Windows
        caracteres_invalidos = r'[<>:"/\\|?*]'
        
        # Reemplazar caracteres inválidos
        nombre_limpio = re.sub(caracteres_invalidos, '_', nombre)
        
        # Eliminar múltiples espacios
        nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)
        
        # Limitar longitud (mantener extensión)
        if len(nombre_limpio) > 200:
            partes = nombre_limpio.rsplit('.', 1)
            if len(partes) == 2:
                nombre_base, extension = partes
                nombre_limpio = nombre_base[:190] + '...' + '.' + extension
            else:
                nombre_limpio = nombre_limpio[:200] + '...'
        
        # Eliminar espacios al inicio y final
        nombre_limpio = nombre_limpio.strip()
        
        # Si queda vacío, usar nombre genérico
        if not nombre_limpio or nombre_limpio in ['.', '..']:
            import time
            timestamp = str(int(time.time()))
            nombre_limpio = f"archivo_{timestamp}"
        
        return nombre_limpio
    
    @staticmethod
    def mover_archivo_seguro(origen: Path, destino: Path) -> Tuple[bool, str]:
        """Mueve un archivo de forma segura manejando conflictos y nombres largos"""
        try:
            # Sanitizar el nombre del archivo destino
            nombre_sanitizado = FileUtils.sanitizar_nombre_archivo(destino.name)
            destino = destino.parent / nombre_sanitizado
            
            # Crear directorio destino si no existe
            destino.parent.mkdir(parents=True, exist_ok=True)
            
            # Verificar longitud de ruta (límite Windows: 260 caracteres)
            if len(str(destino)) > 250:  # Dejar margen de seguridad
                # Acortar el nombre del archivo manteniendo la extensión
                nombre_sin_ext = destino.stem
                extension = destino.suffix
                
                # Calcular cuántos caracteres podemos usar
                ruta_dir = str(destino.parent)
                espacio_disponible = 240 - len(ruta_dir) - len(extension) - 10  # Margen extra
                
                if espacio_disponible > 20:  # Mínimo razonable
                    nombre_corto = nombre_sin_ext[:espacio_disponible] + "..."
                    destino = destino.parent / (nombre_corto + extension)
                else:
                    # Si aún es muy largo, usar timestamp
                    import time
                    timestamp = str(int(time.time()))
                    nombre_corto = f"archivo_largo_{timestamp}"
                    destino = destino.parent / (nombre_corto + extension)
            
            # Si el archivo destino ya existe, generar nuevo nombre
            if destino.exists():
                contador = 1
                nombre_base = destino.stem
                extension = destino.suffix
                
                while destino.exists():
                    nuevo_nombre = f"{nombre_base} ({contador}){extension}"
                    destino_temporal = destino.parent / nuevo_nombre
                    
                    # Verificar que el nuevo nombre no sea muy largo
                    if len(str(destino_temporal)) > 250:
                        # Si es muy largo, usar nombre más corto
                        nombre_base_corto = nombre_base[:50] if len(nombre_base) > 50 else nombre_base
                        nuevo_nombre = f"{nombre_base_corto}_({contador}){extension}"
                        destino = destino.parent / nuevo_nombre
                    else:
                        destino = destino_temporal
                    
                    contador += 1
                    
                    # Evitar bucle infinito
                    if contador > 999:
                        import time
                        timestamp = str(int(time.time()))
                        nuevo_nombre = f"archivo_{timestamp}{extension}"
                        destino = destino.parent / nuevo_nombre
                        break
            
            # Mover el archivo
            shutil.move(str(origen), str(destino))
            return True, str(destino)
            
        except Exception as e:
            error_msg = str(e)
            # Ofrecer información más útil para errores de ruta
            if "WinError 3" in error_msg or "cannot find the path" in error_msg.lower():
                error_msg = f"Ruta demasiado larga o inválida. Archivo: {origen.name[:50]}..."
            elif "WinError 123" in error_msg:
                error_msg = f"Nombre de archivo contiene caracteres inválidos: {origen.name[:50]}..."
            elif "WinError 183" in error_msg:
                error_msg = f"El archivo ya existe en destino: {destino.name[:50]}..."
            
            return False, error_msg
    
    @staticmethod
    def es_archivo_temporal(archivo_path: Path) -> bool:
        """Detecta si un archivo es temporal y debería ser ignorado"""
        nombre = archivo_path.name.lower()
        extension = archivo_path.suffix.lower()
        
        # Extensiones temporales conocidas
        extensiones_temporales = ['.tmp', '.temp', '.crdownload', '.part', '.$$$']
        
        # Patrones de nombres temporales
        patrones_temporales = ['~', '.ds_store', 'thumbs.db', 'desktop.ini']
        
        # Verificar tamaño cero (archivos vacíos)
        try:
            es_vacio = archivo_path.stat().st_size == 0
        except:
            es_vacio = False
        
        return (extension in extensiones_temporales or 
                any(patron in nombre for patron in patrones_temporales) or
                nombre.startswith('~') or
                es_vacio)

class SystemUtils:
    """Utilidades del sistema"""
    
    @staticmethod
    def obtener_carpeta_downloads() -> Path:
        """Obtiene la carpeta de descargas del sistema operativo"""
        sistema = platform.system()
        
        if sistema == "Windows":
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                    return Path(downloads_path)
            except:
                return Path.home() / "Downloads"
        
        elif sistema == "Darwin":  # macOS
            return Path.home() / "Downloads"
        
        else:  # Linux y otros Unix
            # Intentar obtener de XDG
            xdg_config = Path.home() / ".config" / "user-dirs.dirs"
            if xdg_config.exists():
                try:
                    with open(xdg_config) as f:
                        for line in f:
                            if "XDG_DOWNLOAD_DIR" in line:
                                path = line.split('=')[1].strip().strip('"')
                                path = path.replace('$HOME', str(Path.home()))
                                return Path(path)
                except:
                    pass
            
            return Path.home() / "Downloads"
    
    @staticmethod
    def verificar_permisos_escritura(directorio: Path) -> bool:
        """Verifica si se tienen permisos de escritura en un directorio"""
        try:
            archivo_test = directorio / ".test_permisos"
            archivo_test.touch()
            archivo_test.unlink()
            return True
        except Exception:
            return False
    
    @staticmethod
    def obtener_espacio_disponible(directorio: Path) -> int:
        """Obtiene el espacio disponible en bytes en un directorio"""
        try:
            stat = shutil.disk_usage(directorio)
            return stat.free
        except Exception:
            return 0

class LogUtils:
    """Utilidades para logging y seguimiento"""
    
    def __init__(self, archivo_log: Optional[Path] = None):
        from config import config
        
        if archivo_log is None:
            try:
                log_dir = config.config_dir / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                archivo_log = log_dir / f"organizador_{datetime.now().strftime('%Y%m%d')}.log"
            except Exception as e:
                # Fallback: usar directorio temporal si no se puede crear en home
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "organizador_descargas" / "logs"
                temp_dir.mkdir(parents=True, exist_ok=True)
                archivo_log = temp_dir / f"organizador_{datetime.now().strftime('%Y%m%d')}.log"
                print(f"⚠️  Usando directorio temporal para logs: {temp_dir}")
        
        self.archivo_log = archivo_log
    
    def log(self, mensaje: str, nivel: str = "INFO"):
        """Registra un mensaje en el log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea_log = f"[{timestamp}] {nivel}: {mensaje}\n"
        
        try:
            with open(self.archivo_log, 'a', encoding='utf-8') as f:
                f.write(linea_log)
        except Exception:
            pass  # Fallar silenciosamente si no se puede escribir el log
        
        # También imprimir en consola para desarrollo
        print(f"{nivel}: {mensaje}")
    
    def info(self, mensaje: str):
        self.log(mensaje, "INFO")
    
    def warning(self, mensaje: str):
        self.log(mensaje, "WARNING")
    
    def error(self, mensaje: str):
        self.log(mensaje, "ERROR")
    
    def success(self, mensaje: str):
        self.log(mensaje, "SUCCESS")

class EstadisticasUtils:
    """Utilidades para manejo de estadísticas"""
    
    def __init__(self):
        from config import config
        self.stats_file = config.config_dir / "estadisticas.json"
        self.stats = self.cargar_estadisticas()
    
    def cargar_estadisticas(self) -> Dict:
        """Carga las estadísticas desde archivo"""
        try:
            if self.stats_file.exists():
                import json
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {
            'archivos_organizados_total': 0,
            'bytes_organizados_total': 0,
            'sesiones_organizacion': 0,
            'categorias_mas_usadas': {},
            'extensiones_desconocidas': {},
            'fecha_primera_organizacion': None,
            'fecha_ultima_organizacion': None
        }
    
    def guardar_estadisticas(self):
        """Guarda las estadísticas actuales"""
        try:
            import json
            from config import config
            config.config_dir.mkdir(exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            pass
    
    def registrar_organizacion(self, archivos_movidos: List[Dict]):
        """Registra una sesión de organización"""
        now = datetime.now().isoformat()
        
        if self.stats['fecha_primera_organizacion'] is None:
            self.stats['fecha_primera_organizacion'] = now
        
        self.stats['fecha_ultima_organizacion'] = now
        self.stats['sesiones_organizacion'] += 1
        self.stats['archivos_organizados_total'] += len(archivos_movidos)
        
        for archivo_info in archivos_movidos:
            # Contar bytes
            self.stats['bytes_organizados_total'] += archivo_info.get('tamaño', 0)
            
            # Contar categorías
            categoria = archivo_info.get('categoria', 'Otros')
            if categoria not in self.stats['categorias_mas_usadas']:
                self.stats['categorias_mas_usadas'][categoria] = 0
            self.stats['categorias_mas_usadas'][categoria] += 1
        
        self.guardar_estadisticas()
    
    def registrar_extension_desconocida(self, extension: str):
        """Registra una extensión desconocida"""
        if extension not in self.stats['extensiones_desconocidas']:
            self.stats['extensiones_desconocidas'][extension] = 0
        self.stats['extensiones_desconocidas'][extension] += 1
        self.guardar_estadisticas()
    
    def obtener_resumen(self) -> Dict:
        """Obtiene un resumen de las estadísticas"""
        return {
            'total_archivos': self.stats['archivos_organizados_total'],
            'total_tamaño': FileUtils.formatear_tamaño(self.stats['bytes_organizados_total']),
            'total_sesiones': self.stats['sesiones_organizacion'],
            'categoria_favorita': max(self.stats['categorias_mas_usadas'].items(), 
                                    key=lambda x: x[1], default=('Ninguna', 0))[0],
            'extensiones_nuevas': len(self.stats['extensiones_desconocidas']),
            'primera_vez': self.stats['fecha_primera_organizacion'],
            'ultima_vez': self.stats['fecha_ultima_organizacion']
        }

# Instancias globales
logger = LogUtils()
stats = EstadisticasUtils()