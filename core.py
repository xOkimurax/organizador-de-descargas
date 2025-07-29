import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Importar configuración de forma segura
from config import config
from utils import FileUtils, logger, stats

class EstadoArchivo(Enum):
    """Estados posibles de un archivo durante el procesamiento"""
    PENDIENTE = "pendiente"
    PROCESADO = "procesado"
    ERROR = "error"
    IGNORADO = "ignorado"
    EN_USO = "en_uso"
    DESCONOCIDO = "desconocido"

@dataclass
class ArchivoInfo:
    """Información completa de un archivo a procesar"""
    ruta_origen: Path
    nombre: str
    extension: str
    tamaño: int
    categoria_sugerida: str
    ruta_destino: Optional[Path] = None
    estado: EstadoArchivo = EstadoArchivo.PENDIENTE
    razon_estado: str = ""
    es_duplicado: bool = False
    hash_archivo: str = ""
    fecha_modificacion: float = 0
    
    def __post_init__(self):
        if self.fecha_modificacion == 0:
            try:
                self.fecha_modificacion = self.ruta_origen.stat().st_mtime
            except:
                self.fecha_modificacion = time.time()

class OrganizadorCore:
    """Clase principal que maneja toda la lógica de organización"""
    
    def __init__(self):
        self.archivos_procesados: List[ArchivoInfo] = []
        self.callback_progreso: Optional[Callable[[int, int, str], None]] = None
        self.callback_decision_usuario: Optional[Callable[[ArchivoInfo], Tuple[str, bool]]] = None
        self.detener_procesamiento = False
        
    def set_callback_progreso(self, callback: Callable[[int, int, str], None]):
        """Establece callback para reportar progreso"""
        self.callback_progreso = callback
        
    def set_callback_decision_usuario(self, callback: Callable[[ArchivoInfo], Tuple[str, bool]]):
        """Establece callback para decisiones del usuario sobre archivos desconocidos"""
        self.callback_decision_usuario = callback
    
    def escanear_carpeta(self, carpeta_origen: Path = None) -> List[ArchivoInfo]:
        """Escanea una carpeta y analiza todos los archivos"""
        if carpeta_origen is None:
            carpeta_origen = Path(config.config["carpeta_origen"])
        
        if not carpeta_origen.exists():
            logger.error(f"La carpeta origen no existe: {carpeta_origen}")
            return []
        
        logger.info(f"Escaneando carpeta: {carpeta_origen}")
        archivos_encontrados = []
        
        try:
            # Obtener todos los archivos de la carpeta
            for item in carpeta_origen.iterdir():
                if self.detener_procesamiento:
                    break
                    
                if item.is_file():
                    # Filtrar archivos temporales
                    if FileUtils.es_archivo_temporal(item):
                        logger.info(f"Ignorando archivo temporal: {item.name}")
                        continue
                    
                    # Crear información del archivo
                    archivo_info = self._analizar_archivo(item)
                    
                    # Solo agregar si la categoría está activa o es para mostrar como ignorado
                    if archivo_info.categoria_sugerida == "No organizar":
                        # Agregar para mostrar en la lista pero marcado como ignorado
                        archivos_encontrados.append(archivo_info)
                        logger.info(f"Archivo ignorado (categoría desactivada): {item.name}")
                    elif archivo_info.categoria_sugerida and config.categoria_esta_activa(archivo_info.categoria_sugerida):
                        # Solo agregar si la categoría está activa
                        archivos_encontrados.append(archivo_info)
                    else:
                        # Archivo de categoría desactivada - crear entrada "ignorado"
                        archivo_info.estado = EstadoArchivo.IGNORADO
                        archivo_info.categoria_sugerida = "No organizar"
                        archivo_info.razon_estado = f"Categoría '{archivo_info.categoria_sugerida}' desactivada"
                        archivos_encontrados.append(archivo_info)
                        logger.info(f"Archivo ignorado (categoría desactivada): {item.name}")
                    
                    if self.callback_progreso:
                        self.callback_progreso(
                            len(archivos_encontrados), 
                            -1,  # -1 indica que aún estamos contando
                            f"Analizando: {item.name}"
                        )
        
        except Exception as e:
            logger.error(f"Error escaneando carpeta: {e}")
        
        logger.info(f"Encontrados {len(archivos_encontrados)} archivos para procesar")
        return archivos_encontrados
    
    def _analizar_archivo(self, ruta_archivo: Path) -> ArchivoInfo:
        """Analiza un archivo individual y determina su categoría"""
        info_archivo = FileUtils.obtener_info_archivo(ruta_archivo)
        extension = info_archivo['extension']
        
        # Sanitizar el nombre del archivo
        nombre_sanitizado = FileUtils.sanitizar_nombre_archivo(info_archivo['nombre'])
        
        # Verificar si el archivo está en uso
        if info_archivo.get('en_uso', False):
            archivo_info = ArchivoInfo(
                ruta_origen=ruta_archivo,
                nombre=nombre_sanitizado,
                extension=extension,
                tamaño=info_archivo['tamaño'],
                categoria_sugerida="",
                estado=EstadoArchivo.EN_USO,
                razon_estado="Archivo en uso por otro proceso"
            )
            return archivo_info
        
        # Determinar categoría (sin filtrar por activa aún)
        categoria_original = self._determinar_categoria_sin_filtro(ruta_archivo, extension)
        
        # Verificar si la categoría está activa
        if categoria_original and not config.categoria_esta_activa(categoria_original):
            # Categoría desactivada - marcar como ignorado
            archivo_info = ArchivoInfo(
                ruta_origen=ruta_archivo,
                nombre=nombre_sanitizado,
                extension=extension,
                tamaño=info_archivo['tamaño'],
                categoria_sugerida="No organizar",
                estado=EstadoArchivo.IGNORADO,
                razon_estado=f"Categoría '{categoria_original}' desactivada"
            )
            return archivo_info
        
        # Crear información del archivo con categoría activa
        archivo_info = ArchivoInfo(
            ruta_origen=ruta_archivo,
            nombre=nombre_sanitizado,
            extension=extension,
            tamaño=info_archivo['tamaño'],
            categoria_sugerida=categoria_original or "Otros",
            fecha_modificacion=info_archivo['fecha_modificacion'].timestamp()
        )
        
        # Determinar ruta destino solo si la categoría está activa
        if categoria_original and config.categoria_esta_activa(categoria_original):
            carpeta_destino = config.obtener_carpeta_destino(categoria_original, ruta_archivo.parent)
            archivo_info.ruta_destino = carpeta_destino / archivo_info.nombre
        
        # Marcar como desconocido si es necesario
        if categoria_original == "Otros" and extension not in config.reglas_personalizadas:
            # Verificar si realmente es desconocido o solo no categorizado
            es_extension_conocida = any(
                extension in extensiones 
                for extensiones in config.categorias.values()
            )
            
            if not es_extension_conocida and extension != "":
                archivo_info.estado = EstadoArchivo.DESCONOCIDO
                archivo_info.razon_estado = f"Extensión '{extension}' no reconocida"
                stats.registrar_extension_desconocida(extension)
        
        return archivo_info
    
    def _determinar_categoria_sin_filtro(self, ruta_archivo: Path, extension: str) -> str:
        """Determina la categoría de un archivo sin filtrar por categorías activas"""
        extension = extension.lower()
        
        # Primero verificar reglas personalizadas
        if extension in config.reglas_personalizadas:
            return config.reglas_personalizadas[extension]
        
        # Luego verificar categorías por defecto
        for categoria, extensiones in config.categorias.items():
            if extension in extensiones:
                return categoria
        
        # Si no se reconoce la extensión, intentar detección inteligente
        if extension != "":
            tipo_detectado = FileUtils.detectar_tipo_por_contenido(ruta_archivo)
            if tipo_detectado:
                # Mapear tipo detectado a categoría
                mapeo_tipos = {
                    'png': 'Imágenes',
                    'jpg': 'Imágenes', 
                    'gif': 'Imágenes',
                    'pdf': 'Documentos',
                    'zip': 'Comprimidos',
                    'rar': 'Comprimidos',
                    'exe': 'Programas'
                }
                categoria_detectada = mapeo_tipos.get(tipo_detectado, "Otros")
                
                if categoria_detectada != "Otros":
                    logger.info(f"Detectado tipo '{tipo_detectado}' para {ruta_archivo.name}")
                return categoria_detectada
        
        return "Otros"  # Categoría por defecto para desconocidos
    
    def generar_plan_organizacion(self, archivos: List[ArchivoInfo]) -> Dict[str, any]:
        """Genera un plan de organización antes de ejecutar"""
        plan = {
            'total_archivos': len(archivos),
            'archivos_por_categoria': {},
            'archivos_con_conflictos': [],
            'archivos_desconocidos': [],
            'archivos_en_uso': [],
            'tamaño_total': 0,
            'carpetas_a_crear': set(),
            'resumen': {}
        }
        
        for archivo in archivos:
            plan['tamaño_total'] += archivo.tamaño
            
            # Clasificar archivos según su estado
            if archivo.estado == EstadoArchivo.DESCONOCIDO:
                plan['archivos_desconocidos'].append(archivo)
            elif archivo.estado == EstadoArchivo.EN_USO:
                plan['archivos_en_uso'].append(archivo)
            else:
                categoria = archivo.categoria_sugerida
                
                # Contar archivos por categoría
                if categoria not in plan['archivos_por_categoria']:
                    plan['archivos_por_categoria'][categoria] = []
                plan['archivos_por_categoria'][categoria].append(archivo)
                
                # Verificar conflictos de nombres
                if archivo.ruta_destino and archivo.ruta_destino.exists():
                    plan['archivos_con_conflictos'].append(archivo)
                
                # Anotar carpetas que se necesitan crear
                if archivo.ruta_destino:
                    plan['carpetas_a_crear'].add(archivo.ruta_destino.parent)
        
        # Generar resumen
        plan['resumen'] = {
            'categorias_involucradas': len(plan['archivos_por_categoria']),
            'conflictos_nombres': len(plan['archivos_con_conflictos']),
            'archivos_desconocidos': len(plan['archivos_desconocidos']),
            'archivos_en_uso': len(plan['archivos_en_uso']),
            'carpetas_nuevas': len(plan['carpetas_a_crear']),
            'tamaño_legible': FileUtils.formatear_tamaño(plan['tamaño_total'])
        }
        
        return plan
    
    def ejecutar_organizacion(self, archivos: List[ArchivoInfo], 
                            solo_vista_previa: bool = False) -> Dict[str, any]:
        """Ejecuta la organización de archivos"""
        
        if solo_vista_previa:
            return self.generar_plan_organizacion(archivos)
        
        logger.info(f"Iniciando organización de {len(archivos)} archivos")
        self.archivos_procesados = []
        archivos_movidos = []
        archivos_con_error = []
        archivos_omitidos = []
        
        total_archivos = len(archivos)
        
        for i, archivo in enumerate(archivos):
            if self.detener_procesamiento:
                logger.info("Procesamiento detenido por el usuario")
                break
            
            # Omitir archivos ignorados (categorías desactivadas)
            if archivo.estado == EstadoArchivo.IGNORADO:
                archivos_omitidos.append(archivo)
                logger.info(f"Omitido: {archivo.nombre} - {archivo.razon_estado}")
                continue
            
            # Reportar progreso
            if self.callback_progreso:
                self.callback_progreso(
                    i + 1, 
                    total_archivos, 
                    f"Procesando: {archivo.nombre}"
                )
            
            # Procesar archivo individual
            resultado = self._procesar_archivo_individual(archivo)
            
            if resultado['exito']:
                archivos_movidos.append(resultado['archivo_info'])
                logger.success(f"Movido: {archivo.nombre} → {resultado['destino_final']}")
            elif resultado['omitido']:
                archivos_omitidos.append(resultado['archivo_info'])
                logger.info(f"Omitido: {archivo.nombre} - {resultado['razon']}")
            else:
                archivos_con_error.append(resultado['archivo_info'])
                logger.error(f"Error: {archivo.nombre} - {resultado['razon']}")
            
            # Pequeña pausa para no sobrecargar el sistema
            time.sleep(0.01)
        
        # Limpiar carpetas vacías si está configurado
        if config.config['eliminar_carpetas_vacias']:
            self._limpiar_carpetas_vacias(Path(config.config['carpeta_origen']))
        
        # Registrar estadísticas
        if archivos_movidos:
            stats.registrar_organizacion([
                {
                    'nombre': a.nombre,
                    'categoria': a.categoria_sugerida,
                    'tamaño': a.tamaño
                } for a in archivos_movidos
            ])
        
        # Generar resultado final
        resultado_final = {
            'total_procesados': len(archivos_movidos),
            'total_errores': len(archivos_con_error),
            'total_omitidos': len(archivos_omitidos),
            'archivos_movidos': archivos_movidos,
            'archivos_error': archivos_con_error,
            'archivos_omitidos': archivos_omitidos,
            'tamaño_total_movido': sum(a.tamaño for a in archivos_movidos),
            'tiempo_transcurrido': time.time()  # Se calculará en la GUI
        }
        
        logger.info(f"Organización completada: {resultado_final['total_procesados']} archivos movidos")
        return resultado_final
    
    def _procesar_archivo_individual(self, archivo: ArchivoInfo) -> Dict[str, any]:
        """Procesa un archivo individual"""
        
        # Verificar archivos en uso
        if archivo.estado == EstadoArchivo.EN_USO:
            return {
                'exito': False,
                'omitido': True,
                'archivo_info': archivo,
                'razon': 'Archivo en uso por otro proceso',
                'destino_final': None
            }
        
        # Manejar archivos desconocidos
        if archivo.estado == EstadoArchivo.DESCONOCIDO:
            decision_usuario = self._manejar_archivo_desconocido(archivo)
            if decision_usuario is None:
                return {
                    'exito': False,
                    'omitido': True,
                    'archivo_info': archivo,
                    'razon': 'Usuario canceló procesamiento',
                    'destino_final': None
                }
            
            nueva_categoria, recordar = decision_usuario
            archivo.categoria_sugerida = nueva_categoria
            
            # Guardar regla si el usuario lo solicita
            if recordar:
                config.agregar_regla_personalizada(archivo.extension, nueva_categoria)
                logger.info(f"Nueva regla guardada: {archivo.extension} → {nueva_categoria}")
            
            # Actualizar ruta destino
            carpeta_destino = config.obtener_carpeta_destino(nueva_categoria, archivo.ruta_origen.parent)
            archivo.ruta_destino = carpeta_destino / archivo.nombre
        
        # Verificar que tengamos una ruta destino válida
        if not archivo.ruta_destino:
            return {
                'exito': False,
                'omitido': False,
                'archivo_info': archivo,
                'razon': 'No se pudo determinar carpeta destino',
                'destino_final': None
            }
        
        # Mover el archivo
        exito, destino_o_error = FileUtils.mover_archivo_seguro(
            archivo.ruta_origen, 
            archivo.ruta_destino
        )
        
        if exito:
            archivo.estado = EstadoArchivo.PROCESADO
            archivo.ruta_destino = Path(destino_o_error)  # Ruta final real
            return {
                'exito': True,
                'omitido': False,
                'archivo_info': archivo,
                'razon': 'Movido exitosamente',
                'destino_final': destino_o_error
            }
        else:
            archivo.estado = EstadoArchivo.ERROR
            archivo.razon_estado = destino_o_error
            return {
                'exito': False,
                'omitido': False,
                'archivo_info': archivo,
                'razon': destino_o_error,
                'destino_final': None
            }
    
    def _manejar_archivo_desconocido(self, archivo: ArchivoInfo) -> Optional[Tuple[str, bool]]:
        """Maneja archivos con extensiones desconocidas"""
        
        # Verificar configuración de acción por defecto
        accion_default = config.config.get('accion_desconocidos', 'preguntar')
        
        if accion_default == 'otros':
            return ('Otros', False)
        elif accion_default == 'ignorar':
            return None
        
        # Si está configurado para preguntar o no hay callback, usar callback
        if self.callback_decision_usuario:
            return self.callback_decision_usuario(archivo)
        else:
            # Fallback: mover a "Otros"
            return ('Otros', False)
    
    def _limpiar_carpetas_vacias(self, directorio: Path):
        """Elimina carpetas vacías recursivamente"""
        try:
            for item in directorio.iterdir():
                if item.is_dir():
                    self._limpiar_carpetas_vacias(item)
                    try:
                        item.rmdir()  # Solo funciona si está vacía
                        logger.info(f"Carpeta vacía eliminada: {item}")
                    except OSError:
                        pass  # No está vacía, continuar
        except Exception as e:
            logger.warning(f"Error limpiando carpetas vacías: {e}")
    
    def detener(self):
        """Detiene el procesamiento actual"""
        self.detener_procesamiento = True
        logger.info("Solicitud de detener procesamiento recibida")
    
    def continuar(self):
        """Permite continuar el procesamiento"""
        self.detener_procesamiento = False

class MonitorArchivos:
    """Clase para monitoreo automático de la carpeta de descargas"""
    
    def __init__(self, organizador: OrganizadorCore):
        self.organizador = organizador
        self.monitoreando = False
        self.callback_archivo_detectado: Optional[Callable[[Path], None]] = None
        
    def set_callback_archivo_detectado(self, callback: Callable[[Path], None]):
        """Establece callback para cuando se detecta un archivo nuevo"""
        self.callback_archivo_detectado = callback
    
    def iniciar_monitoreo(self, carpeta: Path = None):
        """Inicia el monitoreo de la carpeta"""
        if carpeta is None:
            carpeta = Path(config.config["carpeta_origen"])
        
        if not carpeta.exists():
            logger.error(f"No se puede monitorear carpeta inexistente: {carpeta}")
            return False
        
        self.monitoreando = True
        logger.info(f"Iniciando monitoreo de: {carpeta}")
        
        # Obtener estado inicial
        archivos_iniciales = set(carpeta.glob("*"))
        
        while self.monitoreando:
            try:
                # Verificar nuevos archivos
                archivos_actuales = set(carpeta.glob("*"))
                archivos_nuevos = archivos_actuales - archivos_iniciales
                
                for archivo_nuevo in archivos_nuevos:
                    if archivo_nuevo.is_file() and not FileUtils.es_archivo_temporal(archivo_nuevo):
                        logger.info(f"Archivo nuevo detectado: {archivo_nuevo.name}")
                        
                        if self.callback_archivo_detectado:
                            self.callback_archivo_detectado(archivo_nuevo)
                        
                        # Organizar automáticamente si está configurado
                        if config.config.get('monitoreo_automatico', False):
                            archivos_info = [self.organizador._analizar_archivo(archivo_nuevo)]
                            self.organizador.ejecutar_organizacion(archivos_info)
                
                archivos_iniciales = archivos_actuales
                time.sleep(2)  # Verificar cada 2 segundos
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                time.sleep(5)  # Esperar más tiempo si hay error
        
        logger.info("Monitoreo detenido")
        return True
    
    def detener_monitoreo(self):
        """Detiene el monitoreo"""
        self.monitoreando = False