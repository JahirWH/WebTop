# 🖥️ Monitor de GPU - Linux Server

Un monitor de sistema en tiempo real que muestra información de GPU, CPU y RAM en un servidor Linux.

## 🚀 Características

- **Monitoreo en tiempo real** de GPU, CPU y RAM
- **Interfaz web moderna** con diseño responsive
- **APIs REST** para obtener datos del sistema
- **Actualización automática** cada 5 segundos
- **Soporte para múltiples GPUs** NVIDIA
- **Indicadores de estado** visuales

## 📋 Requisitos

- Python 3.7+
- Linux (probado en Ubuntu/Debian)
- NVIDIA GPU con drivers instalados
- `nvidia-smi` disponible en el sistema

## 🔧 Instalación

1. **Clonar el repositorio:**
```bash
git clone <tu-repositorio>
cd WebTop
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Verificar que nvidia-smi funciona:**
```bash
nvidia-smi
```

## 🚀 Uso

1. **Ejecutar el servidor:**
```bash
python app.py
```

2. **Acceder a la interfaz web:**
   - Abrir navegador en: `http://localhost:5000`
   - Para acceso remoto: `http://[IP-DEL-SERVIDOR]:5000`

## 📊 APIs Disponibles

- **`GET /`** - Interfaz web principal
- **`GET /api/system-info`** - Información completa del sistema (CPU, RAM, GPU)
- **`GET /api/gpu-info`** - Solo información de GPU

### Ejemplo de respuesta de la API:

```json
{
  "cpu": {
    "usage": 25.3,
    "cores": 8
  },
  "ram": {
    "usage": 45.2,
    "used_gb": 7,
    "total_gb": 16
  },
  "gpu": [
    {
      "utilization": 15,
      "memory_used": 2048,
      "memory_total": 8192,
      "temperature": 45,
      "name": "NVIDIA GeForce RTX 3080"
    }
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Monitoreo**: psutil, nvidia-smi
- **Diseño**: CSS Grid, Flexbox, Gradientes

## 🔍 Solución de Problemas

### GPU no detectada
- Verificar que `nvidia-smi` esté instalado
- Comprobar que los drivers NVIDIA estén actualizados
- Ejecutar `nvidia-smi` manualmente para verificar

### Error de permisos
- Asegurar que el usuario tenga permisos para ejecutar `nvidia-smi`
- En algunos casos, ejecutar con `sudo python app.py`

### Puerto ocupado
- Cambiar el puerto en `app.py` línea final: `app.run(host='0.0.0.0', port=5001)`

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.
