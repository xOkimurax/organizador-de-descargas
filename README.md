# Organizador de Descargas v1.0

## 📋 Descripción

Organizador de Descargas es una aplicación de escritorio desarrollada en Python que permite organizar automáticamente los archivos en tu carpeta de descargas. La aplicación clasifica los archivos por tipo (documentos, imágenes, audio, videos, etc.) y los mueve a carpetas específicas de forma inteligente.

## ✨ Características principales

- **Organización automática**: Clasifica archivos por tipo usando extensiones y análisis de contenido
- **Interfaz gráfica intuitiva**: Fácil de usar con Tkinter
- **Monitoreo en tiempo real**: Detecta y organiza archivos nuevos automáticamente
- **Reglas personalizables**: Configura tus propias categorías y extensiones
- **Detección inteligente**: Usa "magic numbers" para identificar tipos de archivo
- **Manejo de duplicados**: Detecta y maneja archivos duplicados
- **Estadísticas de uso**: Lleva registro de archivos organizados
- **Vista previa**: Muestra qué archivos se moverán antes de ejecutar
- **Modo seguro**: Confirmación antes de mover archivos

## 📁 Categorías soportadas

- **Documentos**: PDF, DOC, DOCX, TXT, RTF, XLS, XLSX, PPT, PPTX, ODT, ODS, ODP
- **Imágenes**: JPG, JPEG, PNG, GIF, BMP, SVG, WEBP, TIFF, ICO, RAW
- **Audio**: MP3, WAV, FLAC, AAC, OGG, WMA, M4A
- **Videos**: MP4, AVI, MKV, MOV, WMV, FLV, WEBM, M4V, 3GP
- **Programas**: EXE, MSI, DMG, DEB, RPM, APP, PKG
- **Comprimidos**: ZIP, RAR, 7Z, TAR, GZ, BZ2, XZ
- **Otros**: Archivos que no encajan en las categorías anteriores

## 🔧 Requisitos del sistema

### Requisitos mínimos
- **Sistema operativo**: Windows 7/8/10/11, macOS 10.12+, o Linux
- **Python**: 3.7 o superior
- **RAM**: 512 MB mínimo
- **Espacio en disco**: 50 MB para la aplicación + espacio para organizar archivos

### Dependencias
La aplicación utiliza únicamente librerías estándar de Python:
- `tkinter` (interfaz gráfica - incluida en Python)
- `pathlib` (manejo de rutas)
- `threading` (procesamiento en segundo plano)
- `json` (configuración)
- `hashlib` (detección de duplicados)
- `shutil` (operaciones de archivos)

## 🚀 Instalación y ejecución

### Opción 1: Ejecutar desde código fuente

1. **Clona o descarga el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/organizador-descargas.git
   cd organizador-descargas
   ```

2. **Verifica que tienes Python instalado**:
   ```bash
   python --version
   ```
   Debe mostrar Python 3.7 o superior.

3. **Ejecuta la aplicación**:
   ```bash
   python main.py
   ```

### Opción 2: Usar el ejecutable (Windows)

Si tienes el archivo ejecutable compilado:

1. Navega a la carpeta `dist/`
2. Ejecuta `Organizador.exe` o `gui.exe`

## 📖 Cómo usar

### Primera ejecución
1. Al ejecutar por primera vez, aparecerá un asistente de configuración
2. Selecciona tu carpeta de descargas (por defecto: `~/Downloads`)
3. Configura las carpetas de destino para cada categoría
4. Elige si quieres activar el monitoreo automático

### Uso básico
1. **Escanear archivos**: Haz clic en "Escanear" para ver qué archivos se pueden organizar
2. **Vista previa**: Usa "Vista Previa" para ver dónde se moverá cada archivo
3. **Organizar**: Haz clic en "Organizar Ahora" para mover los archivos
4. **Monitoreo**: Activa "Monitoreo Automático" para organizar archivos nuevos en tiempo real

### Configuración avanzada
- **Categorías personalizadas**: Agrega nuevas extensiones a categorías existentes
- **Rutas personalizadas**: Cambia las carpetas de destino para cada categoría
- **Reglas especiales**: Define reglas para extensiones específicas

## 🎯 Archivos principales

- **`main.py`**: Archivo principal para ejecutar la aplicación
- **`gui.py`**: Interfaz gráfica de usuario
- **`core.py`**: Lógica principal de organización
- **`config.py`**: Manejo de configuración
- **`utils.py`**: Utilidades y funciones auxiliares

## ⚙️ Opciones de línea de comandos

```bash
# Mostrar ayuda
python main.py --help

# Mostrar versión
python main.py --version

# Verificar sistema
python main.py --check
```

## 📊 Características técnicas

- **Detección inteligente**: Usa magic numbers para identificar tipos de archivo más allá de la extensión
- **Manejo seguro**: Verifica permisos y archivos en uso antes de mover
- **Logging**: Registra todas las operaciones para debugging
- **Estadísticas**: Lleva registro de archivos organizados y extensiones encontradas
- **Configuración persistente**: Guarda preferencias en `~/.organizadordescargas/`

## 🔒 Seguridad

- La aplicación **NO** elimina archivos, solo los mueve
- Verifica permisos antes de realizar operaciones
- Detecta archivos en uso para evitar corrupción
- Opción de confirmación antes de mover archivos
- Manejo inteligente de nombres duplicados

## 🐛 Solución de problemas

### Error: "No se puede importar tkinter"
- **Windows**: Reinstala Python desde python.org asegurándote de marcar "tcl/tk and IDLE"
- **Linux**: Instala `python3-tk`: `sudo apt-get install python3-tk`
- **macOS**: Tkinter viene incluido con Python oficial

### Error: "Permisos insuficientes"
- Ejecuta como administrador (Windows) o con `sudo` (Linux/macOS)
- Verifica que tienes permisos de escritura en las carpetas de destino

### La aplicación no detecta archivos nuevos
- Verifica que el monitoreo automático esté activado
- Comprueba que la carpeta de origen sea correcta
- Reinicia la aplicación si el problema persiste

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Si encuentras algún problema o tienes sugerencias:
- Abre un issue en GitHub
- Describe el problema con el mayor detalle posible
- Incluye tu sistema operativo y versión de Python

---

**¡Mantén tu carpeta de descargas siempre organizada! 📁✨**
