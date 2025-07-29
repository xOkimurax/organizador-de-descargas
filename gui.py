import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from config import config
from core import OrganizadorCore, MonitorArchivos, ArchivoInfo, EstadoArchivo
from utils import FileUtils, logger, stats

class VentanaPrincipal:
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Organizador de Descargas v{config.version}")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Core components
        self.organizador = OrganizadorCore()
        self.monitor = MonitorArchivos(self.organizador)
        
        # Variables de control
        self.archivos_escaneados: List[ArchivoInfo] = []
        self.procesando = False
        self.monitoreando = False
        
        # Configurar callbacks
        self.organizador.set_callback_progreso(self.actualizar_progreso)
        self.organizador.set_callback_decision_usuario(self.mostrar_dialogo_archivo_desconocido)
        self.monitor.set_callback_archivo_detectado(self.on_archivo_detectado)
        
        # Configurar interfaz
        self.configurar_estilos()
        self.crear_widgets()
        self.cargar_configuracion_inicial()
        
        # Verificar si es primera vez
        if config.es_primera_vez():
            self.mostrar_setup_inicial()
    
    def configurar_estilos(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores personalizados
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # === HEADER ===
        self.crear_header(main_frame)
        
        # === LAYOUT PRINCIPAL (3 columnas) ===
        # Columna izquierda: Controles
        left_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Columna central: Vista principal
        center_frame = ttk.LabelFrame(main_frame, text="Vista Principal", padding="10")
        center_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Columna derecha: Estadísticas
        right_frame = ttk.LabelFrame(main_frame, text="Estadísticas", padding="10")
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # === FOOTER ===
        self.crear_footer(main_frame)
        
        # Crear contenido de cada sección
        self.crear_controles_izquierda(left_frame)
        self.crear_vista_central(center_frame)
        self.crear_estadisticas_derecha(right_frame)
        
        # Configurar pesos de columnas
        main_frame.columnconfigure(0, weight=0, minsize=200)  # Controles: fijo
        main_frame.columnconfigure(1, weight=1, minsize=400)  # Centro: expandible
        main_frame.columnconfigure(2, weight=0, minsize=200)  # Stats: fijo
    
    def crear_header(self, parent):
        """Crea la sección header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Título
        title_label = ttk.Label(
            header_frame, 
            text="🗂️ Organizador de Descargas", 
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Carpeta actual
        self.carpeta_label = ttk.Label(
            header_frame, 
            text=f"📁 Carpeta: {config.config['carpeta_origen']}"
        )
        self.carpeta_label.grid(row=1, column=0, sticky=tk.W)
        
        # Botón cambiar carpeta
        cambiar_btn = ttk.Button(
            header_frame, 
            text="Cambiar Carpeta", 
            command=self.cambiar_carpeta_origen
        )
        cambiar_btn.grid(row=0, column=1, rowspan=2, sticky=tk.E, padx=(10, 0))
        
        header_frame.columnconfigure(0, weight=1)
    
    def crear_controles_izquierda(self, parent):
        """Crea los controles del panel izquierdo"""
        
        # === ACCIONES PRINCIPALES ===
        ttk.Label(parent, text="Acciones", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.btn_escanear = ttk.Button(
            parent, 
            text="🔍 Escanear Archivos", 
            command=self.escanear_archivos,
            width=20
        )
        self.btn_escanear.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.btn_organizar = ttk.Button(
            parent, 
            text="⚡ Organizar Ahora", 
            command=self.organizar_ahora,
            width=20,
            state='disabled'
        )
        self.btn_organizar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.btn_vista_previa = ttk.Button(
            parent, 
            text="👁️ Vista Previa", 
            command=self.mostrar_vista_previa,
            width=20,
            state='disabled'
        )
        self.btn_vista_previa.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Separador
        ttk.Separator(parent, orient='horizontal').grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # === MONITOREO ===
        ttk.Label(parent, text="Monitoreo", style='Header.TLabel').grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.monitoreo_var = tk.BooleanVar(value=config.config.get('monitoreo_automatico', False))
        self.check_monitoreo = ttk.Checkbutton(
            parent, 
            text="Monitoreo Automático", 
            variable=self.monitoreo_var,
            command=self.toggle_monitoreo
        )
        self.check_monitoreo.grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # Estado del monitoreo
        self.estado_monitoreo_label = ttk.Label(parent, text="⚪ Inactivo")
        self.estado_monitoreo_label.grid(row=7, column=0, sticky=tk.W, pady=2)
        
        # Separador
        ttk.Separator(parent, orient='horizontal').grid(row=8, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # === CATEGORÍAS A ORGANIZAR ===
        ttk.Label(parent, text="Categorías", style='Header.TLabel').grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        
        # Frame para categorías con scroll
        cat_frame = ttk.Frame(parent)
        cat_frame.grid(row=10, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Variables para checkboxes de categorías
        self.categorias_vars = {}
        
        # Crear checkboxes para cada categoría
        for i, categoria in enumerate(config.categorias.keys()):
            var = tk.BooleanVar(value=config.categoria_esta_activa(categoria))
            self.categorias_vars[categoria] = var
            
            check = ttk.Checkbutton(
                cat_frame, 
                text=f"📁 {categoria}", 
                variable=var,
                command=lambda cat=categoria: self.toggle_categoria(cat)
            )
            check.grid(row=i, column=0, sticky=tk.W, pady=1)
        
        # Botones rápidos para categorías
        cat_buttons_frame = ttk.Frame(parent)
        cat_buttons_frame.grid(row=11, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(
            cat_buttons_frame, 
            text="✅ Todas", 
            command=lambda: self.set_todas_categorias(True),
            width=15
        ).grid(row=0, column=0, padx=(0, 2))
        
        ttk.Button(
            cat_buttons_frame, 
            text="❌ Ninguna", 
            command=lambda: self.set_todas_categorias(False),
            width=15
        ).grid(row=0, column=1)
        
        # Separador
        ttk.Separator(parent, orient='horizontal').grid(row=12, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # === CONFIGURACIÓN ===
        ttk.Label(parent, text="Configuración", style='Header.TLabel').grid(row=13, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Button(
            parent, 
            text="⚙️ Configuración", 
            command=self.abrir_configuracion,
            width=20
        ).grid(row=14, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(
            parent, 
            text="📊 Ver Estadísticas", 
            command=self.mostrar_estadisticas_detalle,
            width=20
        ).grid(row=15, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Configurar peso de la columna
        parent.columnconfigure(0, weight=1)
    
    def crear_vista_central(self, parent):
        """Crea la vista central con lista de archivos y log"""
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # === PESTAÑA: ARCHIVOS ===
        archivos_frame = ttk.Frame(self.notebook)
        self.notebook.add(archivos_frame, text="📁 Archivos")
        
        # Lista de archivos con scrollbar
        list_frame = ttk.Frame(archivos_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview para archivos
        columns = ('Nombre', 'Extensión', 'Tamaño', 'Categoría', 'Estado')
        self.tree_archivos = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.tree_archivos.heading('Nombre', text='Nombre del Archivo')
        self.tree_archivos.heading('Extensión', text='Ext.')
        self.tree_archivos.heading('Tamaño', text='Tamaño')
        self.tree_archivos.heading('Categoría', text='Categoría')
        self.tree_archivos.heading('Estado', text='Estado')
        
        self.tree_archivos.column('Nombre', width=200)
        self.tree_archivos.column('Extensión', width=50)
        self.tree_archivos.column('Tamaño', width=80)
        self.tree_archivos.column('Categoría', width=100)
        self.tree_archivos.column('Estado', width=100)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_archivos.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree_archivos.xview)
        self.tree_archivos.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Grid layout
        self.tree_archivos.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # === PESTAÑA: LOG ===
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="📝 Log de Actividad")
        
        # Text widget para log
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_text_frame, wrap=tk.WORD, height=20)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
        # Configurar weights
        archivos_frame.columnconfigure(0, weight=1)
        archivos_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
    
    def crear_estadisticas_derecha(self, parent):
        """Crea el panel de estadísticas"""
        
        # === ESTADÍSTICAS RÁPIDAS ===
        ttk.Label(parent, text="Sesión Actual", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.stats_labels = {}
        stats_items = [
            ('archivos_encontrados', 'Archivos encontrados: 0'),
            ('archivos_organizados', 'Organizados: 0'),
            ('tamaño_procesado', 'Tamaño procesado: 0 B'),
            ('tiempo_estimado', 'Tiempo estimado: --')
        ]
        
        for i, (key, texto) in enumerate(stats_items):
            label = ttk.Label(parent, text=texto)
            label.grid(row=i+1, column=0, sticky=tk.W, pady=1)
            self.stats_labels[key] = label
        
        # Label para categorías activas
        self.categorias_activas_label = ttk.Label(parent, text="Activas: Todas")
        self.categorias_activas_label.grid(row=5, column=0, sticky=tk.W, pady=1)
        
        # Separador
        ttk.Separator(parent, orient='horizontal').grid(row=6, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # === ESTADÍSTICAS HISTÓRICAS ===
        ttk.Label(parent, text="Histórico", style='Header.TLabel').grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        # Cargar estadísticas históricas
        self.actualizar_estadisticas_historicas()
        
        # Separador
        ttk.Separator(parent, orient='horizontal').grid(row=12, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # === RESUMEN RÁPIDO ===
        ttk.Label(parent, text="Estado", style='Header.TLabel').grid(row=13, column=0, sticky=tk.W, pady=(0, 5))
        
        self.estado_label = ttk.Label(parent, text="✅ Listo para organizar")
        self.estado_label.grid(row=14, column=0, sticky=tk.W, pady=2)
        
        # Configurar peso de la columna
        parent.columnconfigure(0, weight=1)
    
    def crear_footer(self, parent):
        """Crea la barra de estado y progreso"""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            footer_frame, 
            variable=self.progress_var, 
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Label de estado
        self.status_label = ttk.Label(footer_frame, text="Listo")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Botón cancelar (inicialmente oculto)
        self.btn_cancelar = ttk.Button(
            footer_frame, 
            text="❌ Cancelar", 
            command=self.cancelar_procesamiento
        )
        # No hacer grid inicialmente
        
        footer_frame.columnconfigure(0, weight=1)
    
    # ========================================
    # MÉTODOS DE FUNCIONALIDAD PRINCIPAL
    # ========================================
    
    def cargar_configuracion_inicial(self):
        """Carga la configuración inicial en la interfaz"""
        self.actualizar_carpeta_label()
        self.monitoreo_var.set(config.config.get('monitoreo_automatico', False))
    
    def actualizar_carpeta_label(self):
        """Actualiza el label de la carpeta actual"""
        carpeta = config.config['carpeta_origen']
        if len(carpeta) > 50:
            carpeta = "..." + carpeta[-47:]
        self.carpeta_label.config(text=f"📁 Carpeta: {carpeta}")
    
    def cambiar_carpeta_origen(self):
        """Permite cambiar la carpeta de origen"""
        nueva_carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de descargas",
            initialdir=config.config['carpeta_origen']
        )
        
        if nueva_carpeta:
            config.actualizar_configuracion({'carpeta_origen': nueva_carpeta})
            self.actualizar_carpeta_label()
            self.agregar_log(f"Carpeta origen cambiada a: {nueva_carpeta}")
            
            # Limpiar lista actual
            self.limpiar_lista_archivos()
    
    def escanear_archivos(self):
        """Escanea la carpeta en busca de archivos"""
        if self.procesando:
            return
        
        def escanear_thread():
            self.procesando = True
            self.actualizar_botones_estado()
            
            try:
                carpeta_origen = Path(config.config['carpeta_origen'])
                if not carpeta_origen.exists():
                    self.agregar_log("ERROR: La carpeta de origen no existe")
                    return
                
                self.agregar_log(f"Escaneando carpeta: {carpeta_origen}")
                self.archivos_escaneados = self.organizador.escanear_carpeta(carpeta_origen)
                
                # Actualizar interfaz en hilo principal
                self.root.after(0, self.actualizar_lista_archivos)
                self.root.after(0, self.actualizar_estadisticas_sesion)
                
                self.agregar_log(f"Escaneo completado: {len(self.archivos_escaneados)} archivos encontrados")
                
            except Exception as e:
                self.agregar_log(f"ERROR en escaneo: {e}")
            finally:
                self.procesando = False
                self.root.after(0, self.actualizar_botones_estado)
        
        threading.Thread(target=escanear_thread, daemon=True).start()
    
    def organizar_ahora(self):
        """Ejecuta la organización de archivos"""
        if not self.archivos_escaneados or self.procesando:
            return
        
        # Confirmar si está configurado
        if config.config.get('confirmar_antes_mover', True):
            respuesta = messagebox.askyesno(
                "Confirmar Organización",
                f"¿Organizar {len(self.archivos_escaneados)} archivos?\n\n"
                "Esta acción moverá los archivos a sus carpetas correspondientes."
            )
            if not respuesta:
                return
        
        def organizar_thread():
            self.procesando = True
            self.root.after(0, self.actualizar_botones_estado)
            self.root.after(0, lambda: self.btn_cancelar.grid(row=0, column=2))
            
            try:
                inicio = time.time()
                resultado = self.organizador.ejecutar_organizacion(self.archivos_escaneados)
                tiempo_transcurrido = time.time() - inicio
                
                # Actualizar interfaz
                self.root.after(0, lambda: self.mostrar_resultado_organizacion(resultado, tiempo_transcurrido))
                
            except Exception as e:
                self.agregar_log(f"ERROR en organización: {e}")
                messagebox.showerror("Error", f"Error durante la organización:\n{e}")
            finally:
                self.procesando = False
                self.root.after(0, self.actualizar_botones_estado)
                self.root.after(0, lambda: self.btn_cancelar.grid_remove())
        
        threading.Thread(target=organizar_thread, daemon=True).start()
    
    def mostrar_vista_previa(self):
        """Muestra una vista previa de la organización"""
        if not self.archivos_escaneados:
            return
        
        plan = self.organizador.generar_plan_organizacion(self.archivos_escaneados)
        VentanaVistaPrevia(self.root, plan, self.archivos_escaneados)
    
    def cancelar_procesamiento(self):
        """Cancela el procesamiento actual"""
        self.organizador.detener()
        self.agregar_log("Cancelación solicitada...")
    
    def toggle_monitoreo(self):
        """Activa o desactiva el monitoreo automático"""
        if self.monitoreo_var.get():
            self.iniciar_monitoreo()
        else:
            self.detener_monitoreo()
    
    def iniciar_monitoreo(self):
        """Inicia el monitoreo de archivos"""
        if self.monitoreando:
            return
        
        def monitoreo_thread():
            self.monitoreando = True
            self.root.after(0, lambda: self.estado_monitoreo_label.config(text="🟢 Monitoreando"))
            
            carpeta_origen = Path(config.config['carpeta_origen'])
            self.monitor.iniciar_monitoreo(carpeta_origen)
            
            self.monitoreando = False
            self.root.after(0, lambda: self.estado_monitoreo_label.config(text="⚪ Inactivo"))
        
        threading.Thread(target=monitoreo_thread, daemon=True).start()
        
        # Actualizar configuración
        config.actualizar_configuracion({'monitoreo_automatico': True})
    
    def detener_monitoreo(self):
        """Detiene el monitoreo de archivos"""
        self.monitor.detener_monitoreo()
        config.actualizar_configuracion({'monitoreo_automatico': False})
    
    def toggle_categoria(self, categoria: str):
        """Activa o desactiva una categoría"""
        activa = self.categorias_vars[categoria].get()
        config.activar_categoria(categoria, activa)
        
        estado = "✅ Activada" if activa else "❌ Desactivada"
        self.agregar_log(f"Categoría '{categoria}': {estado}")
        
        # Actualizar estadísticas si hay archivos escaneados
        if self.archivos_escaneados:
            self.actualizar_estadisticas_sesion()
    
    def set_todas_categorias(self, activas: bool):
        """Activa o desactiva todas las categorías"""
        for categoria, var in self.categorias_vars.items():
            var.set(activas)
            config.activar_categoria(categoria, activas)
        
        estado = "activadas" if activas else "desactivadas"
        self.agregar_log(f"Todas las categorías {estado}")
        
        # Actualizar estadísticas si hay archivos escaneados
        if self.archivos_escaneados:
            self.actualizar_estadisticas_sesion()
    
    def on_archivo_detectado(self, archivo: Path):
        """Callback cuando se detecta un archivo nuevo"""
        self.agregar_log(f"Archivo nuevo detectado: {archivo.name}")
        
        # Si el monitoreo automático está activado, organizar inmediatamente
        if config.config.get('monitoreo_automatico', False):
            archivo_info = self.organizador._analizar_archivo(archivo)
            if archivo_info.estado != EstadoArchivo.DESCONOCIDO:
                resultado = self.organizador.ejecutar_organizacion([archivo_info])
                if resultado['total_procesados'] > 0:
                    self.agregar_log(f"✅ {archivo.name} organizado automáticamente")
    
    # ========================================
    # MÉTODOS DE INTERFAZ Y ACTUALIZACIÓN
    # ========================================
    
    def actualizar_botones_estado(self):
        """Actualiza el estado de los botones según el contexto"""
        if self.procesando:
            self.btn_escanear.config(state='disabled')
            self.btn_organizar.config(state='disabled')
            self.btn_vista_previa.config(state='disabled')
        else:
            self.btn_escanear.config(state='normal')
            if self.archivos_escaneados:
                self.btn_organizar.config(state='normal')
                self.btn_vista_previa.config(state='normal')
            else:
                self.btn_organizar.config(state='disabled')
                self.btn_vista_previa.config(state='disabled')
    
    def actualizar_progreso(self, actual: int, total: int, mensaje: str):
        """Callback para actualizar barra de progreso"""
        if total > 0:
            porcentaje = (actual / total) * 100
            self.progress_var.set(porcentaje)
        
        self.status_label.config(text=mensaje)
        self.root.update_idletasks()
    
    def limpiar_lista_archivos(self):
        """Limpia la lista de archivos"""
        for item in self.tree_archivos.get_children():
            self.tree_archivos.delete(item)
        self.archivos_escaneados = []
        self.actualizar_estadisticas_sesion()
    
    def actualizar_lista_archivos(self):
        """Actualiza la lista de archivos en la interfaz"""
        # Limpiar lista actual
        for item in self.tree_archivos.get_children():
            self.tree_archivos.delete(item)
        
        # Agregar archivos escaneados
        for archivo in self.archivos_escaneados:
            estado_texto = archivo.estado.value
            if archivo.estado == EstadoArchivo.DESCONOCIDO:
                estado_texto = "❓ Desconocido"
            elif archivo.estado == EstadoArchivo.EN_USO:
                estado_texto = "🔒 En uso"
            elif archivo.estado == EstadoArchivo.IGNORADO:
                estado_texto = "⏭️ Ignorado"
            
            # Cambiar color para archivos ignorados
            tags = []
            if archivo.estado == EstadoArchivo.IGNORADO:
                tags = ['ignorado']
            
            item_id = self.tree_archivos.insert('', 'end', values=(
                archivo.nombre,
                archivo.extension,
                FileUtils.formatear_tamaño(archivo.tamaño),
                archivo.categoria_sugerida,
                estado_texto
            ), tags=tags)
        
        # Configurar tag para archivos ignorados
        self.tree_archivos.tag_configure('ignorado', foreground='gray')
    
    def actualizar_estadisticas_sesion(self):
        """Actualiza las estadísticas de la sesión actual"""
        # Filtrar solo archivos de categorías activas
        archivos_validos = [
            a for a in self.archivos_escaneados 
            if a.categoria_sugerida != "No organizar" and a.estado != EstadoArchivo.IGNORADO
        ]
        
        total_archivos = len(archivos_validos)
        total_tamaño = sum(a.tamaño for a in archivos_validos)
        
        # Contar por categorías activas
        categorias_activas = config.obtener_categorias_activas()
        archivos_por_categoria = {}
        for archivo in archivos_validos:
            cat = archivo.categoria_sugerida
            if cat in categorias_activas:
                archivos_por_categoria[cat] = archivos_por_categoria.get(cat, 0) + 1
        
        self.stats_labels['archivos_encontrados'].config(
            text=f"Archivos a organizar: {total_archivos}"
        )
        self.stats_labels['tamaño_procesado'].config(
            text=f"Tamaño total: {FileUtils.formatear_tamaño(total_tamaño)}"
        )
        
        # Mostrar categorías activas
        categorias_texto = ", ".join(categorias_activas) if categorias_activas else "Ninguna"
        if len(categorias_texto) > 25:
            categorias_texto = categorias_texto[:22] + "..."
        
        if hasattr(self, 'categorias_activas_label'):
            self.categorias_activas_label.config(text=f"Activas: {categorias_texto}")
        
        # Calcular tiempo estimado
        tiempo_estimado = total_archivos * 0.1
        if tiempo_estimado < 60:
            tiempo_texto = f"{tiempo_estimado:.1f} segundos"
        else:
            tiempo_texto = f"{tiempo_estimado/60:.1f} minutos"
        
        self.stats_labels['tiempo_estimado'].config(
            text=f"Tiempo estimado: {tiempo_texto}"
        )
    
    def actualizar_estadisticas_historicas(self):
        """Actualiza las estadísticas históricas"""
        resumen = stats.obtener_resumen()
        
        labels_historicos = [
            f"Total archivos: {resumen['total_archivos']}",
            f"Total procesado: {resumen['total_tamaño']}",
            f"Sesiones: {resumen['total_sesiones']}",
            f"Categoría favorita: {resumen['categoria_favorita']}",
            f"Extensiones nuevas: {resumen['extensiones_nuevas']}"
        ]
        
        for i, texto in enumerate(labels_historicos):
            label = ttk.Label(self.root.nametowidget(str(self.root.children['!frame'].children['!labelframe3'])), text=texto)
            label.grid(row=i+8, column=0, sticky=tk.W, pady=1)
    
    def agregar_log(self, mensaje: str):
        """Agrega un mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        linea_log = f"[{timestamp}] {mensaje}\n"
        
        def actualizar_log():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, linea_log)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        
        if threading.current_thread() == threading.main_thread():
            actualizar_log()
        else:
            self.root.after(0, actualizar_log)
    
    def mostrar_resultado_organizacion(self, resultado: dict, tiempo_transcurrido: float):
        """Muestra el resultado de la organización"""
        self.progress_var.set(0)
        self.status_label.config(text="Organización completada")
        
        # Actualizar estadísticas
        self.stats_labels['archivos_organizados'].config(
            text=f"Organizados: {resultado['total_procesados']}"
        )
        
        # Mensaje de resultado
        mensaje = f"""Organización Completada
        
✅ Archivos organizados: {resultado['total_procesados']}
❌ Errores: {resultado['total_errores']}
⏭️ Omitidos: {resultado['total_omitidos']}
💾 Tamaño procesado: {FileUtils.formatear_tamaño(resultado['tamaño_total_movido'])}
⏱️ Tiempo transcurrido: {tiempo_transcurrido:.1f} segundos"""
        
        messagebox.showinfo("Resultado", mensaje)
        
        # Actualizar estado
        self.estado_label.config(text="✅ Organización completada")
        
        # Limpiar lista para próximo escaneo
        self.limpiar_lista_archivos()
    
    # ========================================
    # VENTANAS SECUNDARIAS
    # ========================================
    
    def mostrar_setup_inicial(self):
        """Muestra el wizard de configuración inicial"""
        VentanaSetupInicial(self.root, self)
    
    def abrir_configuracion(self):
        """Abre la ventana de configuración"""
        VentanaConfiguracion(self.root, self)
    
    def mostrar_estadisticas_detalle(self):
        """Muestra estadísticas detalladas"""
        VentanaEstadisticas(self.root)
    
    def mostrar_dialogo_archivo_desconocido(self, archivo: ArchivoInfo) -> Optional[Tuple[str, bool]]:
        """Muestra diálogo para archivos desconocidos"""
        dialogo = DialogoArchivoDesconocido(self.root, archivo)
        return dialogo.resultado
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if self.monitoreando:
            self.detener_monitoreo()
        
        if self.procesando:
            respuesta = messagebox.askyesno(
                "Confirmar salida",
                "Hay un procesamiento en curso. ¿Desea salir de todas formas?"
            )
            if not respuesta:
                return
            self.organizador.detener()
        
        self.root.destroy()

# ========================================
# VENTANAS AUXILIARES
# ========================================

class VentanaSetupInicial:
    """Wizard de configuración inicial"""
    
    def __init__(self, parent, app_principal):
        self.parent = parent
        self.app_principal = app_principal
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Configuración Inicial")
        self.ventana.geometry("500x400")
        self.ventana.resizable(False, False)
        self.ventana.grab_set()  # Modal
        
        self.crear_widgets()
    
    def crear_widgets(self):
        """Crea los widgets del setup inicial"""
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título de bienvenida
        ttk.Label(
            main_frame, 
            text="🎉 Bienvenido al Organizador de Descargas", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Descripción
        descripcion = """Este asistente te ayudará a configurar la aplicación por primera vez.

El Organizador de Descargas puede:
• Organizar automáticamente tus archivos por tipo
• Monitorear tu carpeta de descargas en tiempo real
• Crear reglas personalizadas para nuevos tipos de archivo
• Generar estadísticas de uso"""
        
        ttk.Label(main_frame, text=descripcion, justify=tk.LEFT).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20)
        )
        
        # Configuración de carpeta
        ttk.Label(main_frame, text="Carpeta de Descargas:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        self.carpeta_var = tk.StringVar(value=config.config['carpeta_origen'])
        carpeta_frame = ttk.Frame(main_frame)
        carpeta_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Entry(carpeta_frame, textvariable=self.carpeta_var, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(carpeta_frame, text="Examinar", command=self.seleccionar_carpeta).grid(row=0, column=1, padx=(5, 0))
        
        # Configuraciones básicas
        ttk.Label(main_frame, text="Configuraciones:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        self.confirmar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame, 
            text="Confirmar antes de mover archivos", 
            variable=self.confirmar_var
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.monitoreo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame, 
            text="Activar monitoreo automático", 
            variable=self.monitoreo_var
        ).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(30, 0))
        
        ttk.Button(button_frame, text="Cancelar", command=self.cancelar).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Finalizar", command=self.finalizar).grid(row=0, column=1)
        
        # Configurar weights
        main_frame.columnconfigure(0, weight=1)
        carpeta_frame.columnconfigure(0, weight=1)
    
    def seleccionar_carpeta(self):
        """Permite seleccionar la carpeta de descargas"""
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de descargas",
            initialdir=self.carpeta_var.get()
        )
        if carpeta:
            self.carpeta_var.set(carpeta)
    
    def finalizar(self):
        """Guarda la configuración inicial"""
        nueva_config = {
            'carpeta_origen': self.carpeta_var.get(),
            'confirmar_antes_mover': self.confirmar_var.get(),
            'monitoreo_automatico': self.monitoreo_var.get(),
            'modo_principiante': True
        }
        
        config.actualizar_configuracion(nueva_config)
        self.app_principal.cargar_configuracion_inicial()
        
        messagebox.showinfo(
            "Configuración Guardada", 
            "¡Configuración inicial completada!\n\nYa puedes empezar a organizar tus archivos."
        )
        
        self.ventana.destroy()
    
    def cancelar(self):
        """Cancela el setup inicial"""
        self.ventana.destroy()

class VentanaVistaPrevia:
    """Ventana que muestra vista previa de la organización"""
    
    def __init__(self, parent, plan: dict, archivos: List[ArchivoInfo]):
        self.plan = plan
        self.archivos = archivos
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Vista Previa de Organización")
        self.ventana.geometry("900x600")  # Aumenté ancho para ver rutas completas
        self.ventana.grab_set()
        
        self.crear_widgets()
    
    def crear_widgets(self):
        """Crea los widgets de la vista previa"""
        main_frame = ttk.Frame(self.ventana, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Resumen con tipo de organización
        resumen_frame = ttk.LabelFrame(main_frame, text="Resumen y Configuración", padding="10")
        resumen_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Mostrar tipo de organización activa
        tipo_organizacion = self._obtener_tipo_organizacion_texto()
        
        resumen_texto = f"""📁 Total de archivos: {self.plan['total_archivos']}
💾 Tamaño total: {self.plan['resumen']['tamaño_legible']}
📂 Categorías involucradas: {self.plan['resumen']['categorias_involucradas']}
⚠️ Conflictos de nombres: {self.plan['resumen']['conflictos_nombres']}
❓ Archivos desconocidos: {self.plan['resumen']['archivos_desconocidos']}
🔒 Archivos en uso: {self.plan['resumen']['archivos_en_uso']}

🎯 Tipo de organización: {tipo_organizacion}"""
        
        ttk.Label(resumen_frame, text=resumen_texto, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        
        # Lista detallada
        lista_frame = ttk.LabelFrame(main_frame, text="Vista Previa Detallada - Destinos Exactos", padding="10")
        lista_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview para vista previa con columna de destino completo
        columns = ('Archivo', 'Tamaño', 'Destino_Completo')
        self.tree_preview = ttk.Treeview(lista_frame, columns=columns, show='tree headings', height=15)
        
        # Configurar columnas
        self.tree_preview.heading('#0', text='Categoría')
        self.tree_preview.heading('Archivo', text='Archivo')
        self.tree_preview.heading('Tamaño', text='Tamaño')
        self.tree_preview.heading('Destino_Completo', text='Ruta Destino Completa')
        
        self.tree_preview.column('#0', width=150)
        self.tree_preview.column('Archivo', width=200)
        self.tree_preview.column('Tamaño', width=80)
        self.tree_preview.column('Destino_Completo', width=400)  # Más ancho para ruta completa
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree_preview.yview)
        scrollbar_h = ttk.Scrollbar(lista_frame, orient=tk.HORIZONTAL, command=self.tree_preview.xview)
        self.tree_preview.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.tree_preview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Poblar el treeview
        self.poblar_tree_preview()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cerrar", command=self.ventana.destroy).grid(row=0, column=0)
        
        # Configurar weights
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        lista_frame.columnconfigure(0, weight=1)
        lista_frame.rowconfigure(0, weight=1)
    
    def _obtener_tipo_organizacion_texto(self) -> str:
        """Obtiene una descripción del tipo de organización configurado"""
        from config import config
        
        crear_fecha = config.config.get('crear_subcarpetas_fecha', False)
        crear_origen = config.config.get('crear_subcarpetas_origen', False)
        
        if crear_fecha and crear_origen:
            return "📅📍 Subcarpetas por fecha Y origen (ej: Documentos/2025-01/documentos-downloads/)"
        elif crear_fecha:
            return "📅 Subcarpetas por fecha (ej: Documentos/2025-01/)"
        elif crear_origen:
            return "📍 Subcarpetas por origen (ej: Documentos/documentos-downloads/)"
        else:
            return "📁 Organización simple (ej: Documentos/)"
    
    def poblar_tree_preview(self):
        """Llena el treeview con los datos de vista previa mostrando rutas exactas"""
        # Agrupar por categoría
        for categoria, archivos in self.plan['archivos_por_categoria'].items():
            # Insertar nodo de categoría
            categoria_node = self.tree_preview.insert('', 'end', text=f"📁 {categoria} ({len(archivos)})")
            
            # Insertar archivos de la categoría
            for archivo in archivos[:15]:  # Mostrar hasta 15 para no saturar
                # Mostrar la ruta destino completa real
                if archivo.ruta_destino:
                    ruta_completa = str(archivo.ruta_destino)
                    # Acortar solo si es muy larga
                    if len(ruta_completa) > 60:
                        ruta_mostrar = "..." + ruta_completa[-57:]
                    else:
                        ruta_mostrar = ruta_completa
                else:
                    ruta_mostrar = "⚠️ No determinado"
                
                self.tree_preview.insert(categoria_node, 'end', values=(
                    archivo.nombre,
                    FileUtils.formatear_tamaño(archivo.tamaño),
                    ruta_mostrar
                ))
            
            if len(archivos) > 15:
                self.tree_preview.insert(categoria_node, 'end', text=f"... y {len(archivos) - 15} archivos más")
        
        # Expandir todas las categorías para mejor visualización
        for item in self.tree_preview.get_children():
            self.tree_preview.item(item, open=True)

class DialogoArchivoDesconocido:
    """Diálogo para manejar archivos con extensiones desconocidas"""
    
    def __init__(self, parent, archivo: ArchivoInfo):
        self.archivo = archivo
        self.resultado = None
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Archivo Desconocido")
        self.ventana.geometry("650x600")  # Ventana más grande
        self.ventana.minsize(600, 550)  
        self.ventana.resizable(True, True)
        self.ventana.grab_set()
        
        # Configurar colores uniformes
        self.ventana.configure(bg='#f0f0f0')
        
        self.crear_widgets()
        
        # Centrar en pantalla
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (self.ventana.winfo_width() // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (self.ventana.winfo_height() // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        # Esperar resultado
        self.ventana.wait_window()
    
    def crear_widgets(self):
        """Crea los widgets del diálogo"""
        # Configurar grid para distribución uniforme
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        
        # Frame principal que ocupa toda la ventana
        main_frame = ttk.Frame(self.ventana, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid del frame principal
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # El frame de opciones será expansible
        
        # === TÍTULO ===
        titulo_label = ttk.Label(
            main_frame, 
            text="🤔 Archivo Desconocido Encontrado",
            style='Title.TLabel'
        )
        titulo_label.grid(row=0, column=0, pady=(0, 25))
        
        # === INFORMACIÓN DEL ARCHIVO ===
        info_frame = ttk.LabelFrame(main_frame, text=" Información del Archivo ", padding="20")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 25))
        
        info_texto = f"""📄 Nombre: {self.archivo.nombre}
📝 Extensión: {self.archivo.extension or '(sin extensión)'}
💾 Tamaño: {FileUtils.formatear_tamaño(self.archivo.tamaño)}
📍 Ubicación: {self.archivo.ruta_origen.parent}"""
        
        ttk.Label(info_frame, text=info_texto, justify=tk.LEFT).pack(anchor='w')
        
        # === PREGUNTA ===
        pregunta_label = ttk.Label(
            main_frame, 
            text="¿Dónde quieres mover este archivo?",
            style='Header.TLabel'
        )
        pregunta_label.grid(row=2, column=0, pady=(0, 20))
        
        # === OPCIONES DE CATEGORÍAS ===
        opciones_frame = ttk.LabelFrame(main_frame, text=" Seleccionar Categoría ", padding="20")
        opciones_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 25))
        
        # Configurar grid del frame de opciones
        opciones_frame.columnconfigure(0, weight=1)
        opciones_frame.columnconfigure(1, weight=1)
        
        # Variable para la categoría seleccionada
        self.categoria_var = tk.StringVar(value="Documentos")  # Documentos por defecto para CSV
        
        categorias = list(config.categorias.keys())
        
        # Crear radiobuttons en grid 2 columnas
        for i, categoria in enumerate(categorias):
            row = i // 2
            col = i % 2
            
            radio = ttk.Radiobutton(
                opciones_frame, 
                text=f"📁 {categoria}", 
                variable=self.categoria_var, 
                value=categoria
            )
            radio.grid(row=row, column=col, sticky=tk.W, pady=8, padx=(0, 30))
        
        # Opción "Crear nueva..." en nueva fila
        next_row = (len(categorias) + 1) // 2
        ttk.Radiobutton(
            opciones_frame, 
            text="📁 Crear nueva categoría...", 
            variable=self.categoria_var, 
            value="Crear nueva..."
        ).grid(row=next_row, column=0, sticky=tk.W, pady=8, columnspan=2)
        
        # === OPCIONES ADICIONALES ===
        extras_frame = ttk.Frame(main_frame)
        extras_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 25))
        
        # Tip informativo
        tip_label = ttk.Label(
            extras_frame,
            text="💡 Tip: Los archivos CSV suelen ir en Documentos",
            foreground='blue'
        )
        tip_label.pack(pady=(0, 15))
        
        # Checkbox para recordar decisión
        self.recordar_var = tk.BooleanVar(value=True)
        recordar_check = ttk.Checkbutton(
            extras_frame, 
            text=f"✅ Recordar para futuros archivos {self.archivo.extension}", 
            variable=self.recordar_var
        )
        recordar_check.pack(pady=(0, 10))
        
        # Checkbox para omitir todos los desconocidos
        self.omitir_todos_var = tk.BooleanVar(value=False)
        omitir_todos_check = ttk.Checkbutton(
            extras_frame, 
            text="⏭️ Omitir TODOS los archivos desconocidos (cualquier extensión)", 
            variable=self.omitir_todos_var
        )
        omitir_todos_check.pack(pady=(0, 15))
        
        # === SEPARADOR ===
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # === FRAME DE BOTONES ===
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=6, column=0, pady=(0, 10))
        
        # Descripción de botones
        desc_label = ttk.Label(
            botones_frame,
            text="⏭️ Omitir: No mover este archivo  |  ✅ Aplicar: Mover a la categoría seleccionada",
            foreground='gray'
        )
        desc_label.pack(pady=(0, 15))
        
        # Contenedor para centrar los botones
        buttons_container = ttk.Frame(botones_frame)
        buttons_container.pack()
        
        # Botones principales
        btn_omitir = ttk.Button(
            buttons_container, 
            text="⏭️ Omitir Archivo", 
            command=self.omitir,
            width=18
        )
        btn_omitir.pack(side=tk.LEFT, padx=(0, 20))
        
        btn_aplicar = ttk.Button(
            buttons_container, 
            text="✅ Aplicar Selección", 
            command=self.aplicar,
            width=18
        )
        btn_aplicar.pack(side=tk.LEFT)
        
        # Configurar teclas de acceso rápido
        self.ventana.bind('<Return>', lambda e: self.aplicar())
        self.ventana.bind('<Escape>', lambda e: self.omitir())
        
        # Focus en el botón aplicar
        btn_aplicar.focus_set()
        
        # Configurar weights para distribución
        main_frame.columnconfigure(0, weight=1)
    
    def aplicar(self):
        """Aplica la decisión del usuario"""
        # Verificar si se seleccionó omitir todos los desconocidos
        if self.omitir_todos_var.get():
            # Configurar para ignorar todos los archivos desconocidos
            config.actualizar_configuracion({'accion_desconocidos': 'ignorar'})
            self.resultado = None  # Omitir este archivo
            self.ventana.destroy()
            return
        
        categoria = self.categoria_var.get()
        
        if categoria == "Crear nueva...":
            nueva_categoria = simpledialog.askstring(
                "Nueva Categoría",
                "Nombre de la nueva categoría:",
                parent=self.ventana
            )
            if nueva_categoria:
                categoria = nueva_categoria
                # Crear la nueva categoría en config
                if categoria not in config.categorias:
                    config.categorias[categoria] = []
                    # Crear carpeta destino
                    carpeta_destino = Path(config.config['carpeta_origen']) / categoria
                    config.config['carpetas_destino'][categoria] = str(carpeta_destino)
                    config.guardar_configuracion()
                    config.guardar_categorias()
            else:
                return  # Usuario canceló
        
        self.resultado = (categoria, self.recordar_var.get())
        self.ventana.destroy()
    
    def omitir(self):
        """Omite el archivo"""
        self.resultado = None
        self.ventana.destroy()

class VentanaConfiguracion:
    """Ventana de configuración avanzada"""
    
    def __init__(self, parent, app_principal):
        self.parent = parent
        self.app_principal = app_principal
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Configuración")
        self.ventana.geometry("700x650")  # Aumenté considerablemente el tamaño
        self.ventana.minsize(650, 600)  # Tamaño mínimo más grande
        self.ventana.grab_set()
        
        self.crear_widgets()
    
    def crear_widgets(self):
        """Crea los widgets de configuración"""
        # Configurar la ventana principal
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        
        # Frame principal que ocupa toda la ventana
        main_frame = ttk.Frame(self.ventana, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid del main_frame 
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)  # Notebook expansible
        main_frame.rowconfigure(1, weight=0)  # Botones fijos
        
        # Notebook para pestañas (área expansible)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Crear pestañas
        self.crear_pestana_general(notebook)
        self.crear_pestana_categorias(notebook)
        self.crear_pestana_avanzado(notebook)
        
        # Cargar valores actuales
        self.cargar_valores_actuales()
        
        # Frame para botones (área fija en la parte inferior)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Separador visual
        ttk.Separator(button_frame, orient='horizontal').pack(fill='x', pady=(0, 15))
        
        # Contenedor para centrar los botones
        buttons_container = ttk.Frame(button_frame)
        buttons_container.pack()
        
        # Botones principales
        ttk.Button(
            buttons_container, 
            text="Cancelar", 
            command=self.ventana.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=(15, 0))
        
        ttk.Button(
            buttons_container, 
            text="Guardar", 
            command=self.guardar_configuracion,
            width=15
        ).pack(side=tk.RIGHT)
    
    def crear_pestana_general(self, notebook):
        """Crea la pestaña de configuración general"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="General")
        
        # Carpeta origen
        ttk.Label(frame, text="Carpeta de origen:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        carpeta_frame = ttk.Frame(frame)
        carpeta_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.carpeta_var = tk.StringVar(value=config.config['carpeta_origen'])
        ttk.Entry(carpeta_frame, textvariable=self.carpeta_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(carpeta_frame, text="Examinar", command=self.seleccionar_carpeta).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Opciones generales
        ttk.Label(frame, text="Opciones:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.confirmar_var = tk.BooleanVar(value=config.config.get('confirmar_antes_mover', True))
        ttk.Checkbutton(frame, text="Confirmar antes de mover archivos", variable=self.confirmar_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.eliminar_vacias_var = tk.BooleanVar(value=config.config.get('eliminar_carpetas_vacias', True))
        ttk.Checkbutton(frame, text="Eliminar carpetas vacías", variable=self.eliminar_vacias_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.hacer_backup_var = tk.BooleanVar(value=config.config.get('hacer_backup', False))
        ttk.Checkbutton(frame, text="Hacer backup antes de organizar", variable=self.hacer_backup_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Opciones de subcarpetas
        ttk.Label(frame, text="Organización:", font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(15, 5))
        
        self.subcarpetas_fecha_var = tk.BooleanVar(value=config.config.get('crear_subcarpetas_fecha', False))
        ttk.Checkbutton(frame, text="Crear subcarpetas por fecha (ej: 2025-01)", variable=self.subcarpetas_fecha_var).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.subcarpetas_origen_var = tk.BooleanVar(value=config.config.get('crear_subcarpetas_origen', False))
        ttk.Checkbutton(frame, text="Crear subcarpetas por origen (ej: documentos-Downloads)", variable=self.subcarpetas_origen_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Acción para archivos desconocidos
        ttk.Label(frame, text="Archivos desconocidos:", font=('Arial', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(15, 5))
        
        self.accion_desconocidos_var = tk.StringVar(value=config.config.get('accion_desconocidos', 'preguntar'))
        
        opciones_desconocidos = [
            ("Preguntar siempre", "preguntar"),
            ("Mover a 'Otros'", "otros"),
            ("Ignorar", "ignorar")
        ]
        
        for i, (texto, valor) in enumerate(opciones_desconocidos):
            ttk.Radiobutton(frame, text=texto, variable=self.accion_desconocidos_var, value=valor).grid(row=10+i, column=0, sticky=tk.W, pady=2)
        
        frame.columnconfigure(0, weight=1)
    
    def crear_pestana_categorias(self, notebook):
        """Crea la pestaña de configuración de categorías"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Categorías")
        
        # Crear notebook secundario para separar extensiones y rutas
        self.sub_notebook = ttk.Notebook(frame)
        self.sub_notebook.pack(fill='both', expand=True)
        
        # === PESTAÑA: EXTENSIONES ===
        ext_frame = ttk.Frame(self.sub_notebook, padding="5")
        self.sub_notebook.add(ext_frame, text="📝 Extensiones")
        
        # Lista de categorías y extensiones
        ttk.Label(ext_frame, text="Categorías y extensiones:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Treeview para categorías
        tree_frame = ttk.Frame(ext_frame)
        tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.tree_categorias = ttk.Treeview(tree_frame, height=12)
        self.tree_categorias.pack(side='left', fill='both', expand=True)
        
        # Scrollbar para categorías
        scrollbar_cat = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_categorias.yview)
        scrollbar_cat.pack(side='right', fill='y')
        self.tree_categorias.configure(yscrollcommand=scrollbar_cat.set)
        
        # Poblar treeview de categorías
        self.poblar_tree_categorias()
        
        # Botones de categorías
        cat_buttons_frame = ttk.Frame(ext_frame)
        cat_buttons_frame.pack(pady=(10, 0))
        
        ttk.Button(cat_buttons_frame, text="Agregar Categoría", command=self.agregar_categoria).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cat_buttons_frame, text="Agregar Extensión", command=self.agregar_extension).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cat_buttons_frame, text="Eliminar", command=self.eliminar_seleccionado).pack(side=tk.LEFT)
        
        # === PESTAÑA: RUTAS DE DESTINO ===
        rutas_frame = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(rutas_frame, text="📁 Rutas de Destino")
        
        # Título con instrucciones
        titulo_frame = ttk.Frame(rutas_frame)
        titulo_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(titulo_frame, text="Carpetas de destino para cada categoría:").pack(anchor='w')
        ttk.Label(titulo_frame, text="💡 Configura dónde se guardarán los archivos de cada tipo", foreground='blue').pack(anchor='w', pady=(2, 0))
        
        # Frame principal con grid para mejor organización
        main_rutas_frame = ttk.Frame(rutas_frame)
        main_rutas_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Variables para las rutas
        self.rutas_vars = {}
        
        # Crear controles en grid 2 columnas
        self.crear_controles_rutas_mejorado(main_rutas_frame)
        
        # Frame para botones con mejor distribución
        botones_frame = ttk.Frame(rutas_frame)
        botones_frame.pack(fill='x')
        
        # Separador
        ttk.Separator(botones_frame, orient='horizontal').pack(fill='x', pady=(0, 10))
        
        # Botones organizados mejor
        btn_frame = ttk.Frame(botones_frame)
        btn_frame.pack()
        
        ttk.Button(
            btn_frame, 
            text="🔄 Restaurar por Defecto", 
            command=self.restaurar_rutas_default,
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame, 
            text="📂 Seleccionar Base", 
            command=self.copiar_base_todas,
            width=20
        ).pack(side=tk.LEFT)
        
        # Información adicional
        info_frame = ttk.Frame(botones_frame)
        info_frame.pack(fill='x', pady=(10, 0))
        
        info_text = """🔄 Restaurar: Vuelve a [Carpeta Origen]/[Categoría]
📂 Seleccionar Base: Elige una carpeta y crea subcarpetas para todas las categorías"""
        
        ttk.Label(info_frame, text=info_text, foreground='gray', justify='left').pack(anchor='w')
    
    def crear_controles_rutas_mejorado(self, parent_frame):
        """Crea los controles para configurar rutas con mejor diseño"""
        
        categorias = list(config.categorias.keys())
        
        # Organizar en 2 columnas
        for i, categoria in enumerate(categorias):
            row = i // 2
            col = i % 2
            
            # Frame para cada categoría
            cat_frame = ttk.LabelFrame(parent_frame, text=f"📁 {categoria}", padding="8")
            cat_frame.grid(row=row, column=col, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5)
            
            # Ruta actual
            ruta_actual = config.config.get("carpetas_destino", {}).get(categoria, "")
            if not ruta_actual:
                ruta_actual = str(Path(config.config["carpeta_origen"]) / categoria)
            
            self.rutas_vars[categoria] = tk.StringVar(value=ruta_actual)
            
            # Entry para la ruta con mejor diseño
            ruta_frame = ttk.Frame(cat_frame)
            ruta_frame.pack(fill='x', pady=(0, 8))
            
            ruta_entry = ttk.Entry(ruta_frame, textvariable=self.rutas_vars[categoria])
            ruta_entry.pack(side='left', fill='x', expand=True)
            
            btn_examinar = ttk.Button(
                ruta_frame, 
                text="📂", 
                width=4,
                command=lambda cat=categoria: self.seleccionar_ruta_categoria(cat)
            )
            btn_examinar.pack(side='right', padx=(5, 0))
            
            # Información de extensiones más compacta
            extensiones = config.categorias.get(categoria, [])
            if extensiones:
                ext_texto = f"{len(extensiones)} tipos: {', '.join(extensiones[:3])}"
                if len(extensiones) > 3:
                    ext_texto += f" +{len(extensiones) - 3}"
            else:
                ext_texto = "Sin extensiones definidas"
            
            ttk.Label(cat_frame, text=ext_texto, foreground='gray').pack(anchor='w')
        
        # Configurar pesos de columnas para que se distribuyan bien
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=1)
    
    def seleccionar_ruta_categoria(self, categoria: str):
        """Permite seleccionar una nueva ruta para una categoría"""
        ruta_actual = self.rutas_vars[categoria].get()
        
        nueva_ruta = filedialog.askdirectory(
            title=f"Seleccionar carpeta para {categoria}",
            initialdir=ruta_actual if ruta_actual else config.config["carpeta_origen"]
        )
        
        if nueva_ruta:
            self.rutas_vars[categoria].set(nueva_ruta)
    
    def restaurar_rutas_default(self):
        """Restaura las rutas por defecto basadas en la carpeta origen"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            "¿Restaurar todas las rutas a los valores por defecto?\n\n"
            "Se usará: [Carpeta Origen]/[Categoría]"
        )
        
        if respuesta:
            carpeta_origen = Path(self.carpeta_var.get())
            for categoria in config.categorias.keys():
                ruta_default = str(carpeta_origen / categoria)
                self.rutas_vars[categoria].set(ruta_default)
    
    def copiar_base_todas(self):
        """Copia una ruta base para todas las categorías"""
        ruta_base = filedialog.askdirectory(
            title="Seleccionar carpeta base para todas las categorías",
            initialdir=config.config["carpeta_origen"]
        )
        
        if ruta_base:
            respuesta = messagebox.askyesno(
                "Confirmar",
                f"¿Configurar todas las categorías en:\n{ruta_base}/[Categoría]?"
            )
            
            if respuesta:
                for categoria in config.categorias.keys():
                    nueva_ruta = str(Path(ruta_base) / categoria)
                    self.rutas_vars[categoria].set(nueva_ruta)
    
    def crear_pestana_avanzado(self, notebook):
        """Crea la pestaña de configuración avanzada"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Avanzado")
        
        # Estadísticas
        ttk.Label(frame, text="Datos y estadísticas:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Button(frame, text="Limpiar estadísticas", command=self.limpiar_estadisticas).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Button(frame, text="Exportar configuración", command=self.exportar_configuracion).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Button(frame, text="Importar configuración", command=self.importar_configuracion).grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # Información del sistema
        ttk.Label(frame, text="Información:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        resumen_stats = stats.obtener_resumen()
        info_texto = f"""Versión: {config.version}
Archivos organizados: {resumen_stats['total_archivos']}
Tamaño procesado: {resumen_stats['total_tamaño']}
Extensiones aprendidas: {len(config.reglas_personalizadas)}
Carpeta de configuración: {config.config_dir}"""
        
        ttk.Label(frame, text=info_texto, justify=tk.LEFT).grid(row=5, column=0, sticky=tk.W, pady=5)
    
    def poblar_tree_categorias(self):
        """Llena el treeview con las categorías actuales"""
        for item in self.tree_categorias.get_children():
            self.tree_categorias.delete(item)
        
        for categoria, extensiones in config.categorias.items():
            categoria_node = self.tree_categorias.insert('', 'end', text=f"📁 {categoria}", open=True)
            for ext in extensiones:
                self.tree_categorias.insert(categoria_node, 'end', text=f"  📄 {ext}")
    
    def seleccionar_carpeta(self):
        """Permite seleccionar carpeta de origen"""
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de descargas",
            initialdir=self.carpeta_var.get()
        )
        if carpeta:
            self.carpeta_var.set(carpeta)
    
    def agregar_categoria(self):
        """Agrega una nueva categoría"""
        nueva_categoria = simpledialog.askstring(
            "Nueva Categoría",
            "Nombre de la nueva categoría:",
            parent=self.ventana
        )
        if nueva_categoria and nueva_categoria not in config.categorias:
            config.categorias[nueva_categoria] = []
            # Crear carpeta destino
            carpeta_destino = Path(config.config['carpeta_origen']) / nueva_categoria
            config.config['carpetas_destino'][nueva_categoria] = str(carpeta_destino)
            self.poblar_tree_categorias()
    
    def agregar_extension(self):
        """Agrega una nueva extensión a una categoría"""
        seleccion = self.tree_categorias.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una categoría primero")
            return
        
        item = self.tree_categorias.item(seleccion[0])
        categoria = None
        
        # Determinar si es categoría o extensión
        if item['text'].startswith('📁'):
            categoria = item['text'][2:]  # Quitar emoji
        else:
            # Es una extensión, obtener la categoría padre
            parent = self.tree_categorias.parent(seleccion[0])
            categoria = self.tree_categorias.item(parent)['text'][2:]
        
        if categoria:
            nueva_extension = simpledialog.askstring(
                "Nueva Extensión",
                f"Extensión para '{categoria}' (ej: .txt):",
                parent=self.ventana
            )
            if nueva_extension:
                if not nueva_extension.startswith('.'):
                    nueva_extension = '.' + nueva_extension
                
                if nueva_extension not in config.categorias[categoria]:
                    config.categorias[categoria].append(nueva_extension)
                    self.poblar_tree_categorias()
    
    def eliminar_seleccionado(self):
        """Elimina el elemento seleccionado"""
        seleccion = self.tree_categorias.selection()
        if not seleccion:
            return
        
        item = self.tree_categorias.item(seleccion[0])
        
        if item['text'].startswith('📁'):
            # Es una categoría
            categoria = item['text'][2:]
            respuesta = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Eliminar la categoría '{categoria}' y todas sus extensiones?"
            )
            if respuesta:
                del config.categorias[categoria]
                if categoria in config.config['carpetas_destino']:
                    del config.config['carpetas_destino'][categoria]
                self.poblar_tree_categorias()
        else:
            # Es una extensión
            extension = item['text'].strip()[2:]  # Quitar emoji y espacios
            parent = self.tree_categorias.parent(seleccion[0])
            categoria = self.tree_categorias.item(parent)['text'][2:]
            
            config.categorias[categoria].remove(extension)
            self.poblar_tree_categorias()
    
    def limpiar_estadisticas(self):
        """Limpia todas las estadísticas"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            "¿Estás seguro de que quieres limpiar todas las estadísticas?"
        )
        if respuesta:
            stats.stats = stats.cargar_estadisticas()  # Resetear a valores por defecto
            stats.guardar_estadisticas()
            messagebox.showinfo("Completado", "Estadísticas limpiadas")
    
    def exportar_configuracion(self):
        """Exporta la configuración actual"""
        archivo = filedialog.asksaveasfilename(
            title="Exportar configuración",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if archivo:
            try:
                import json
                configuracion_export = {
                    'config': config.config,
                    'categorias': config.categorias,
                    'reglas_personalizadas': config.reglas_personalizadas
                }
                with open(archivo, 'w', encoding='utf-8') as f:
                    json.dump(configuracion_export, f, indent=2, ensure_ascii=False, default=str)
                messagebox.showinfo("Completado", "Configuración exportada exitosamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando configuración: {e}")
    
    def importar_configuracion(self):
        """Importa configuración desde archivo"""
        archivo = filedialog.askopenfilename(
            title="Importar configuración",
            filetypes=[("JSON files", "*.json")]
        )
        if archivo:
            try:
                import json
                with open(archivo, 'r', encoding='utf-8') as f:
                    configuracion_import = json.load(f)
                
                # Actualizar configuraciones
                if 'config' in configuracion_import:
                    config.config.update(configuracion_import['config'])
                if 'categorias' in configuracion_import:
                    config.categorias.update(configuracion_import['categorias'])
                if 'reglas_personalizadas' in configuracion_import:
                    config.reglas_personalizadas.update(configuracion_import['reglas_personalizadas'])
                
                # Guardar
                config.guardar_configuracion()
                config.guardar_categorias()
                config.guardar_reglas_personalizadas()
                
                messagebox.showinfo("Completado", "Configuración importada exitosamente")
                
                # Actualizar interfaz
                self.cargar_valores_actuales()
                self.poblar_tree_categorias()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error importando configuración: {e}")
    
    def cargar_valores_actuales(self):
        """Carga los valores actuales en la interfaz"""
        try:
            self.carpeta_var.set(config.config['carpeta_origen'])
            self.confirmar_var.set(config.config.get('confirmar_antes_mover', True))
            self.eliminar_vacias_var.set(config.config.get('eliminar_carpetas_vacias', True))
            self.hacer_backup_var.set(config.config.get('hacer_backup', False))
            self.subcarpetas_fecha_var.set(config.config.get('crear_subcarpetas_fecha', False))
            self.subcarpetas_origen_var.set(config.config.get('crear_subcarpetas_origen', False))
            self.accion_desconocidos_var.set(config.config.get('accion_desconocidos', 'preguntar'))
            
            # Cargar rutas de destino
            if hasattr(self, 'rutas_vars'):
                for categoria, var in self.rutas_vars.items():
                    ruta_actual = config.config.get("carpetas_destino", {}).get(categoria, "")
                    if not ruta_actual:
                        ruta_actual = str(Path(config.config["carpeta_origen"]) / categoria)
                    var.set(ruta_actual)
        except Exception as e:
            logger.error(f"Error cargando valores en configuración: {e}")
    
    def guardar_configuracion(self):
        """Guarda toda la configuración"""
        try:
            # Actualizar configuración general
            config.actualizar_configuracion({
                'carpeta_origen': self.carpeta_var.get(),
                'confirmar_antes_mover': self.confirmar_var.get(),
                'eliminar_carpetas_vacias': self.eliminar_vacias_var.get(),
                'hacer_backup': self.hacer_backup_var.get(),
                'crear_subcarpetas_fecha': self.subcarpetas_fecha_var.get(),
                'crear_subcarpetas_origen': self.subcarpetas_origen_var.get(),
                'accion_desconocidos': self.accion_desconocidos_var.get()
            })
            
            # Guardar rutas de destino
            carpetas_destino = {}
            for categoria, var in self.rutas_vars.items():
                ruta = var.get().strip()
                if ruta:
                    # Validar que la ruta sea válida
                    try:
                        Path(ruta)  # Validar sintaxis
                        carpetas_destino[categoria] = ruta
                    except Exception as e:
                        messagebox.showerror(
                            "Error en ruta", 
                            f"Ruta inválida para {categoria}:\n{ruta}\n\nError: {e}"
                        )
                        return
            
            # Actualizar carpetas destino en configuración
            config.config['carpetas_destino'] = carpetas_destino
            config.guardar_configuracion()
            
            # Guardar categorías
            config.guardar_categorias()
            
            messagebox.showinfo("Completado", "Configuración guardada exitosamente")
            
            # Actualizar aplicación principal
            self.app_principal.cargar_configuracion_inicial()
            
            self.ventana.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {e}")

class VentanaEstadisticas:
    """Ventana de estadísticas detalladas"""
    
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Estadísticas Detalladas")
        self.ventana.geometry("500x400")
        self.ventana.grab_set()
        
        self.crear_widgets()
    
    def crear_widgets(self):
        """Crea los widgets de estadísticas"""
        main_frame = ttk.Frame(self.ventana, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        ttk.Label(main_frame, text="📊 Estadísticas Detalladas", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Obtener estadísticas
        resumen = stats.obtener_resumen()
        
        # Estadísticas generales
        stats_frame = ttk.LabelFrame(main_frame, text="Resumen General", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_texto = f"""Total de archivos organizados: {resumen['total_archivos']}
Tamaño total procesado: {resumen['total_tamaño']}
Número de sesiones: {resumen['total_sesiones']}
Categoría más usada: {resumen['categoria_favorita']}
Extensiones nuevas descubiertas: {resumen['extensiones_nuevas']}

Primera organización: {resumen['primera_vez'] or 'Nunca'}
Última organización: {resumen['ultima_vez'] or 'Nunca'}"""
        
        ttk.Label(stats_frame, text=stats_texto, justify=tk.LEFT).pack(anchor='w')
        
        # Categorías más usadas
        if stats.stats['categorias_mas_usadas']:
            cat_frame = ttk.LabelFrame(main_frame, text="Categorías Más Usadas", padding="10")
            cat_frame.pack(fill='x', pady=(0, 10))
            
            categorias_ordenadas = sorted(
                stats.stats['categorias_mas_usadas'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            for categoria, cantidad in categorias_ordenadas:
                ttk.Label(cat_frame, text=f"📁 {categoria}: {cantidad} archivos").pack(anchor='w')
        
        # Extensiones desconocidas
        if stats.stats['extensiones_desconocidas']:
            ext_frame = ttk.LabelFrame(main_frame, text="Extensiones Más Frecuentes", padding="10")
            ext_frame.pack(fill='x', pady=(0, 10))
            
            extensiones_ordenadas = sorted(
                stats.stats['extensiones_desconocidas'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for extension, cantidad in extensiones_ordenadas:
                ttk.Label(ext_frame, text=f"📄 {extension}: {cantidad} veces").pack(anchor='w')
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", command=self.ventana.destroy).pack(pady=(20, 0))