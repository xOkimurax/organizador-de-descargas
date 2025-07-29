#!/usr/bin/env python3
"""
Script de prueba para la ventana de archivo desconocido
Permite probar visualmente el diálogo sin ejecutar toda la aplicación
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple

# Simular ArchivoInfo
@dataclass
class ArchivoInfo:
    ruta_origen: Path
    nombre: str
    extension: str
    tamaño: int

# Simular config básico
class ConfigSimulado:
    categorias = {
        "Documentos": [".pdf", ".doc", ".docx", ".txt"],
        "Imágenes": [".jpg", ".jpeg", ".png", ".gif"],
        "Audio": [".mp3", ".wav", ".flac"],
        "Videos": [".mp4", ".avi", ".mkv"],
        "Programas": [".exe", ".msi", ".dmg"],
        "Comprimidos": [".zip", ".rar", ".7z"],
        "Otros": []
    }

config = ConfigSimulado()

# Simular FileUtils
class FileUtils:
    @staticmethod
    def formatear_tamaño(tamaño_bytes: int) -> str:
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if tamaño_bytes < 1024.0:
                return f"{tamaño_bytes:.1f} {unidad}"
            tamaño_bytes /= 1024.0
        return f"{tamaño_bytes:.1f} TB"

class DialogoArchivoDesconocido:
    """Diálogo para manejar archivos con extensiones desconocidas - VERSIÓN DE PRUEBA"""
    
    def __init__(self, parent, archivo: ArchivoInfo):
        self.archivo = archivo
        self.resultado = None
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Archivo Desconocido - PRUEBA")
        self.ventana.geometry("580x550")  # Aún más grande para prueba
        self.ventana.minsize(550, 500)  # Tamaño mínimo mayor
        self.ventana.resizable(True, True)
        self.ventana.grab_set()
        
        self.crear_widgets()
        
        # Centrar en pantalla
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (self.ventana.winfo_width() // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (self.ventana.winfo_height() // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        # Focus inicial
        self.ventana.focus_force()
        
        # Esperar resultado
        self.ventana.wait_window()
    
    def crear_widgets(self):
        """Crea los widgets del diálogo con layout mejorado"""
        # ESTRUCTURA PRINCIPAL: Usar grid para mejor control
        self.ventana.grid_rowconfigure(0, weight=1)
        self.ventana.grid_columnconfigure(0, weight=1)
        
        # Frame principal que ocupa toda la ventana
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configurar grid del frame principal
        main_frame.grid_rowconfigure(7, weight=1)  # Row de botones se mantiene abajo
        main_frame.grid_columnconfigure(0, weight=1)
        
        # === TÍTULO ===
        titulo_frame = ttk.Frame(main_frame)
        titulo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ttk.Label(
            titulo_frame, 
            text="🤔 Archivo Desconocido Encontrado", 
            font=('Arial', 14, 'bold')
        ).pack()
        
        # === INFORMACIÓN DEL ARCHIVO ===
        info_frame = ttk.LabelFrame(main_frame, text="📋 Información del Archivo", padding="15")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        info_texto = f"""📄 Nombre: {self.archivo.nombre}
📝 Extensión: {self.archivo.extension or '(sin extensión)'}
💾 Tamaño: {FileUtils.formatear_tamaño(self.archivo.tamaño)}
📍 Ubicación: {self.archivo.ruta_origen.parent}"""
        
        ttk.Label(info_frame, text=info_texto, justify=tk.LEFT, font=('Arial', 10)).pack(anchor='w')
        
        # === PREGUNTA ===
        pregunta_frame = ttk.Frame(main_frame)
        pregunta_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        
        ttk.Label(
            pregunta_frame, 
            text="❓ ¿Dónde quieres mover este archivo?", 
            font=('Arial', 11, 'bold')
        ).pack()
        
        # === OPCIONES DE CATEGORÍA ===
        opciones_frame = ttk.LabelFrame(main_frame, text="📁 Selecciona una categoría", padding="15")
        opciones_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        
        # Grid interno para opciones
        opciones_frame.grid_columnconfigure(0, weight=1)
        opciones_frame.grid_columnconfigure(1, weight=1)
        
        self.categoria_var = tk.StringVar(value="Otros")
        
        categorias = list(config.categorias.keys())
        
        # Organizar en 2 columnas con mejor espaciado
        for i, categoria in enumerate(categorias):
            row = i // 2
            col = i % 2
            
            radio = ttk.Radiobutton(
                opciones_frame, 
                text=f"📁 {categoria}", 
                variable=self.categoria_var, 
                value=categoria,
                font=('Arial', 10)
            )
            radio.grid(row=row, column=col, sticky="w", pady=6, padx=10)
        
        # Opción "Crear nueva..." en nueva fila
        next_row = (len(categorias) + 1) // 2
        ttk.Radiobutton(
            opciones_frame, 
            text="✨ Crear nueva categoría...", 
            variable=self.categoria_var, 
            value="Crear nueva...",
            font=('Arial', 10)
        ).grid(row=next_row, column=0, sticky="w", pady=6, padx=10, columnspan=2)
        
        # === TIP INFORMATIVO ===
        tip_frame = ttk.Frame(main_frame)
        tip_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        
        ttk.Label(
            tip_frame,
            text="💡 La categoría seleccionada determinará dónde se guardará este tipo de archivo",
            font=('Arial', 9),
            foreground='blue'
        ).pack()
        
        # === CHECKBOX RECORDAR ===
        recordar_frame = ttk.Frame(main_frame)
        recordar_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        
        self.recordar_var = tk.BooleanVar(value=True)
        recordar_check = ttk.Checkbutton(
            recordar_frame, 
            text=f"✅ Recordar esta decisión para futuros archivos {self.archivo.extension}", 
            variable=self.recordar_var,
            font=('Arial', 10)
        )
        recordar_check.pack(anchor='w')
        
        # === SEPARADOR ===
        separador_frame = ttk.Frame(main_frame)
        separador_frame.grid(row=6, column=0, sticky="ew", pady=(10, 15))
        
        ttk.Separator(separador_frame, orient='horizontal').pack(fill='x')
        
        # === FRAME DE BOTONES (SIEMPRE AL FONDO) ===
        botones_container = ttk.Frame(main_frame)
        botones_container.grid(row=7, column=0, sticky="ew")
        
        # Descripción de botones
        desc_frame = ttk.Frame(botones_container)
        desc_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(
            desc_frame,
            text="⏭️ Omitir = No mover este archivo  •  ✅ Aplicar = Mover a la categoría seleccionada",
            font=('Arial', 9),
            foreground='gray'
        ).pack()
        
        # Botones principales
        botones_frame = ttk.Frame(botones_container)
        botones_frame.pack()
        
        self.btn_omitir = ttk.Button(
            botones_frame, 
            text="⏭️ Omitir Archivo", 
            command=self.omitir,
            width=20,
            style='Warning.TButton'
        )
        self.btn_omitir.pack(side=tk.LEFT, padx=(0, 20))
        
        self.btn_aplicar = ttk.Button(
            botones_frame, 
            text="✅ Aplicar Selección", 
            command=self.aplicar,
            width=20
        )
        self.btn_aplicar.pack(side=tk.LEFT)
        
        # === CONFIGURAR EVENTOS ===
        self.ventana.bind('<Return>', lambda e: self.aplicar())
        self.ventana.bind('<Escape>', lambda e: self.omitir())
        
        # Focus en el botón aplicar
        self.btn_aplicar.focus_set()
        
        # Agregar indicador visual de que los botones están listos
        self.ventana.after(100, self.resaltar_botones)
    
    def resaltar_botones(self):
        """Resalta brevemente los botones para confirmar que están visibles"""
        # Cambiar color temporalmente para confirmar visibilidad
        original_bg = self.btn_aplicar.cget('style')
        
        # Crear un estilo temporal
        style = ttk.Style()
        style.configure('Highlight.TButton', background='lightgreen')
        
        self.btn_aplicar.configure(style='Highlight.TButton')
        self.ventana.after(1000, lambda: self.btn_aplicar.configure(style=''))
    
    def aplicar(self):
        """Aplica la decisión del usuario"""
        categoria = self.categoria_var.get()
        
        if categoria == "Crear nueva...":
            nueva_categoria = simpledialog.askstring(
                "Nueva Categoría",
                "Nombre de la nueva categoría:",
                parent=self.ventana
            )
            if nueva_categoria:
                categoria = nueva_categoria
                # Simular creación de nueva categoría
                config.categorias[categoria] = []
            else:
                return  # Usuario canceló
        
        self.resultado = (categoria, self.recordar_var.get())
        print(f"✅ RESULTADO: Archivo '{self.archivo.nombre}' → Categoría: '{categoria}', Recordar: {self.recordar_var.get()}")
        self.ventana.destroy()
    
    def omitir(self):
        """Omite el archivo"""
        self.resultado = None
        print(f"⏭️ OMITIDO: Archivo '{self.archivo.nombre}' no será movido")
        self.ventana.destroy()

class TestApp:
    """Aplicación de prueba para probar los diálogos"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧪 Prueba de Diálogos - Organizador de Descargas")
        self.root.geometry("400x300")
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea la interfaz de prueba"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        ttk.Label(
            main_frame, 
            text="🧪 Prueba de Ventanas", 
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))
        
        # Descripción
        descripcion = """Esta aplicación te permite probar las ventanas
del Organizador de Descargas sin ejecutar
la aplicación completa.

Haz clic en los botones para abrir las ventanas:"""
        
        ttk.Label(main_frame, text=descripcion, justify=tk.CENTER).pack(pady=(0, 30))
        
        # Botones de prueba
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack()
        
        # Botón para archivo con extensión conocida
        ttk.Button(
            botones_frame,
            text="📄 Probar archivo .xyz (desconocido)",
            command=self.probar_archivo_desconocido_1,
            width=35
        ).pack(pady=5)
        
        ttk.Button(
            botones_frame,
            text="🎵 Probar archivo .unknown (sin extensión)",
            command=self.probar_archivo_sin_extension,
            width=35
        ).pack(pady=5)
        
        ttk.Button(
            botones_frame,
            text="📊 Probar archivo .datos (personalizado)",
            command=self.probar_archivo_personalizado,
            width=35
        ).pack(pady=5)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Instrucciones
        instrucciones = """💡 Instrucciones:
• Prueba si los botones se ven correctamente
• Verifica que la ventana tenga el tamaño adecuado
• Confirma que no necesitas redimensionar manualmente
• Presiona Enter para Aplicar o Escape para Omitir"""
        
        ttk.Label(
            main_frame, 
            text=instrucciones, 
            justify=tk.LEFT,
            font=('Arial', 9),
            foreground='blue'
        ).pack()
        
        # Botón salir
        ttk.Button(
            main_frame,
            text="❌ Salir",
            command=self.root.quit,
            width=15
        ).pack(side='bottom', pady=(20, 0))
    
    def probar_archivo_desconocido_1(self):
        """Prueba con archivo .xyz"""
        archivo = ArchivoInfo(
            ruta_origen=Path("C:/Users/Usuario/Downloads/documento.xyz"),
            nombre="documento.xyz",
            extension=".xyz",
            tamaño=2048576  # 2MB
        )
        
        dialogo = DialogoArchivoDesconocido(self.root, archivo)
        if dialogo.resultado:
            print(f"Resultado: {dialogo.resultado}")
    
    def probar_archivo_sin_extension(self):
        """Prueba con archivo sin extensión"""
        archivo = ArchivoInfo(
            ruta_origen=Path("C:/Users/Usuario/Downloads/archivo_sin_extension"),
            nombre="archivo_sin_extension",
            extension="",
            tamaño=1024000  # 1MB
        )
        
        dialogo = DialogoArchivoDesconocido(self.root, archivo)
        if dialogo.resultado:
            print(f"Resultado: {dialogo.resultado}")
    
    def probar_archivo_personalizado(self):
        """Prueba con archivo de extensión personalizada"""
        archivo = ArchivoInfo(
            ruta_origen=Path("E:/Descargas/base_datos.datos"),
            nombre="base_datos.datos",
            extension=".datos",
            tamaño=52428800  # 50MB
        )
        
        dialogo = DialogoArchivoDesconocido(self.root, archivo)
        if dialogo.resultado:
            print(f"Resultado: {dialogo.resultado}")
    
    def ejecutar(self):
        """Ejecuta la aplicación de prueba"""
        print("🧪 Iniciando aplicación de prueba...")
        print("📝 Los resultados se mostrarán en la consola")
        print("-" * 50)
        
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit)
        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SCRIPT DE PRUEBA - DIÁLOGO ARCHIVO DESCONOCIDO")
    print("=" * 60)
    print()
    
    app = TestApp()
    app.ejecutar()
    
    print()
    print("=" * 60)
    print("✅ Prueba completada")
    print("=" * 60)