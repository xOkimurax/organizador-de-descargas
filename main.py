#!/usr/bin/env python3
"""
Organizador de Descargas v1.0
=============================

Aplicación para organizar automáticamente archivos en la carpeta de descargas.

Características principales:
- Organización automática por tipo de archivo
- Interfaz gráfica intuitiva
- Monitoreo en tiempo real
- Reglas personalizables
- Estadísticas de uso
- Manejo inteligente de archivos desconocidos

Autor: Tu nombre aquí
Licencia: MIT
"""

import sys
import os
import traceback
from pathlib import Path

# Agregar el directorio actual al path para importaciones
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def verificar_dependencias():
    """Verifica que todas las dependencias estén disponibles"""
    dependencias_faltantes = []
    
    # Tkinter (incluido en Python estándar)
    try:
        import tkinter
    except ImportError:
        dependencias_faltantes.append("tkinter")
    
    # Verificar módulos del sistema
    modulos_requeridos = [
        'os', 'sys', 'pathlib', 'threading', 'time', 'json', 
        'hashlib', 'shutil', 'platform', 'datetime'
    ]
    
    for modulo in modulos_requeridos:
        try:
            __import__(modulo)
        except ImportError:
            dependencias_faltantes.append(modulo)
    
    if dependencias_faltantes:
        print("❌ ERROR: Dependencias faltantes:")
        for dep in dependencias_faltantes:
            print(f"  - {dep}")
        print("\nInstala las dependencias faltantes y vuelve a ejecutar.")
        return False
    
    return True

def verificar_permisos():
    """Verifica permisos de escritura en directorios necesarios"""
    from utils import SystemUtils
    
    # Verificar carpeta home
    home_dir = Path.home()
    if not SystemUtils.verificar_permisos_escritura(home_dir):
        print("⚠️  ADVERTENCIA: Sin permisos de escritura en directorio home")
        print("   La aplicación puede no funcionar correctamente")
        return False
    
    # Verificar carpeta Downloads
    downloads_dir = SystemUtils.obtener_carpeta_downloads()
    if not downloads_dir.exists():
        print(f"⚠️  ADVERTENCIA: Carpeta Downloads no encontrada: {downloads_dir}")
        print("   Puedes configurar una carpeta diferente en la aplicación")
        return False
    
    if not SystemUtils.verificar_permisos_escritura(downloads_dir):
        print(f"⚠️  ADVERTENCIA: Sin permisos de escritura en: {downloads_dir}")
        print("   Puede que necesites ejecutar como administrador")
        return False
    
    return True

def configurar_logging():
    """Configura el sistema de logging"""
    try:
        from utils import logger
        logger.info("=== Iniciando Organizador de Descargas v1.0 ===")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Plataforma: {sys.platform}")
        logger.info(f"Directorio de trabajo: {os.getcwd()}")
        return True
    except Exception as e:
        print(f"❌ Error configurando logging: {e}")
        return False

def mostrar_informacion_inicio():
    """Muestra información de inicio en consola"""
    print("🗂️  Organizador de Descargas v1.0")
    print("=" * 40)
    print("✅ Verificando sistema...")
    
    # Verificar dependencias
    if not verificar_dependencias():
        return False
    
    print("✅ Dependencias verificadas")
    
    # Configurar logging
    if not configurar_logging():
        return False
    
    print("✅ Logging configurado")
    
    # Verificar permisos
    permisos_ok = verificar_permisos()
    if permisos_ok:
        print("✅ Permisos verificados")
    else:
        print("⚠️  Advertencias de permisos (ver arriba)")
    
    print("🚀 Iniciando interfaz gráfica...")
    return True

def main():
    """Función principal de la aplicación"""
    
    # Verificaciones iniciales
    if not mostrar_informacion_inicio():
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    try:
        # Importar después de verificaciones
        from gui import VentanaPrincipal
        from utils import logger
        
        # Crear y ejecutar aplicación
        logger.info("Creando ventana principal")
        app = VentanaPrincipal()
        
        logger.info("Iniciando bucle principal de la aplicación")
        app.ejecutar()
        
        logger.info("Aplicación cerrada normalmente")
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación interrumpida por el usuario")
        sys.exit(0)
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Verifica que todos los archivos estén en el mismo directorio:")
        print("  - main.py")
        print("  - config.py")
        print("  - core.py")
        print("  - gui.py")
        print("  - utils.py")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("\nDetalles técnicos:")
        print("-" * 50)
        traceback.print_exc()
        print("-" * 50)
        
        # Intentar guardar error en log
        try:
            from utils import logger
            logger.error(f"Error crítico: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        except:
            pass
        
        print("\nSi el error persiste, por favor:")
        print("1. Verifica que tienes Python 3.8+ instalado")
        print("2. Asegúrate de que todos los archivos estén presentes")
        print("3. Ejecuta como administrador si hay problemas de permisos")
        print("4. Revisa el archivo de log para más detalles")
        
        input("\nPresiona Enter para salir...")
        sys.exit(1)

def mostrar_ayuda():
    """Muestra información de ayuda"""
    ayuda = """
🗂️  Organizador de Descargas v1.0 - Ayuda
==========================================

DESCRIPCIÓN:
Organiza automáticamente los archivos de tu carpeta de descargas
agrupándolos por tipo en subcarpetas.

USO:
    python main.py              # Ejecuta la aplicación normalmente
    python main.py --help       # Muestra esta ayuda
    python main.py --version    # Muestra la versión
    python main.py --check      # Verifica el sistema sin abrir GUI

CARACTERÍSTICAS:
✅ Organización automática por tipo de archivo
✅ Interfaz gráfica intuitiva
✅ Monitoreo en tiempo real de nuevos archivos
✅ Reglas personalizables para extensiones
✅ Estadísticas de uso y rendimiento
✅ Manejo inteligente de archivos desconocidos
✅ Vista previa antes de organizar
✅ Configuración de carpetas destino

TIPOS DE ARCHIVO SOPORTADOS:
📄 Documentos: PDF, DOC, TXT, XLS, PPT, etc.
🖼️  Imágenes: JPG, PNG, GIF, BMP, SVG, etc.
🎵 Audio: MP3, WAV, FLAC, AAC, OGG, etc.
🎬 Videos: MP4, AVI, MKV, MOV, WMV, etc.
💾 Programas: EXE, MSI, DMG, DEB, APP, etc.
📦 Comprimidos: ZIP, RAR, 7Z, TAR, GZ, etc.

CONFIGURACIÓN:
La configuración se guarda en:
- Windows: %USERPROFILE%\\.organizadordescargas\\
- macOS/Linux: ~/.organizadordescargas/

ARCHIVOS DE CONFIGURACIÓN:
- config.json: Configuración general
- categorias.json: Categorías personalizadas
- reglas_personalizadas.json: Reglas aprendidas
- estadisticas.json: Datos de uso
- logs/: Archivos de registro

SOLUCIÓN DE PROBLEMAS:
1. Si no aparece la ventana, verifica que tengas tkinter instalado
2. Si hay errores de permisos, ejecuta como administrador
3. Si falla el escaneo, verifica que la carpeta Downloads existe
4. Para reportar bugs, revisa los logs en la carpeta de configuración

LICENCIA:
MIT License - Libre para uso personal y comercial

CONTACTO:
GitHub: [tu-usuario]/organizador-descargas
Email: [tu-email]@example.com
"""
    print(ayuda)

def verificar_sistema():
    """Modo de verificación del sistema sin abrir GUI"""
    print("🔍 Verificación del Sistema")
    print("=" * 30)
    
    # Información de Python
    print(f"Python: {sys.version}")
    print(f"Plataforma: {sys.platform}")
    print(f"Arquitectura: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
    
    # Verificar dependencias
    print("\n📦 Dependencias:")
    if verificar_dependencias():
        print("  ✅ Todas las dependencias están disponibles")
    else:
        print("  ❌ Faltan dependencias (ver arriba)")
        return False
    
    # Verificar permisos
    print("\n🔐 Permisos:")
    if verificar_permisos():
        print("  ✅ Permisos de escritura verificados")
    else:
        print("  ⚠️  Advertencias de permisos detectadas")
    
    # Verificar configuración
    print("\n⚙️  Configuración:")
    try:
        from config import config
        print(f"  ✅ Configuración cargada desde: {config.config_file}")
        print(f"  📁 Carpeta origen: {config.config['carpeta_origen']}")
        print(f"  📊 Categorías definidas: {len(config.categorias)}")
        print(f"  🎯 Reglas personalizadas: {len(config.reglas_personalizadas)}")
    except Exception as e:
        print(f"  ❌ Error cargando configuración: {e}")
        return False
    
    # Verificar estadísticas
    print("\n📈 Estadísticas:")
    try:
        from utils import stats
        resumen = stats.obtener_resumen()
        print(f"  📊 Total archivos organizados: {resumen['total_archivos']}")
        print(f"  💾 Tamaño total procesado: {resumen['total_tamaño']}")
        print(f"  🔄 Sesiones de organización: {resumen['total_sesiones']}")
    except Exception as e:
        print(f"  ❌ Error cargando estadísticas: {e}")
    
    # Prueba de funcionalidad core
    print("\n🧪 Prueba de funcionalidad:")
    try:
        from core import OrganizadorCore
        from pathlib import Path
        
        organizador = OrganizadorCore()
        carpeta_test = Path(config.config['carpeta_origen'])
        
        if carpeta_test.exists():
            # Hacer escaneo de prueba (sin procesar)
            archivos = organizador.escanear_carpeta(carpeta_test)
            print(f"  ✅ Escaneo de prueba exitoso: {len(archivos)} archivos encontrados")
        else:
            print(f"  ⚠️  Carpeta de origen no existe: {carpeta_test}")
            
    except Exception as e:
        print(f"  ❌ Error en prueba de funcionalidad: {e}")
        return False
    
    print("\n🎉 Verificación completada")
    print("  El sistema está listo para ejecutar el Organizador de Descargas")
    return True

if __name__ == "__main__":
    # Manejar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            mostrar_ayuda()
            sys.exit(0)
            
        elif arg in ['--version', '-v', 'version']:
            try:
                from config import config
                print(f"Organizador de Descargas v{config.version}")
            except:
                print("Organizador de Descargas v1.0")
            sys.exit(0)
            
        elif arg in ['--check', '-c', 'check']:
            if verificar_sistema():
                sys.exit(0)
            else:
                sys.exit(1)
                
        else:
            print(f"❌ Argumento desconocido: {arg}")
            print("Usa --help para ver las opciones disponibles")
            sys.exit(1)
    
    # Ejecutar aplicación normal
    main()