# Monitor del Sistema

Un monitor simple para ver el uso de CPU, RAM y GPU en tiempo real.

## Que hace

- Muestra el uso del procesador en porcentaje
- Muestra el uso de memoria RAM en porcentaje  
- Muestra informacion de las tarjetas graficas NVIDIA
- Actualiza los datos cada 5 segundos
- Tiene una grafica de pastel que muestra el uso del sistema

## Requisitos

- Python 3.7 o mas nuevo
- Linux (probado en Ubuntu)
- Tarjeta grafica NVIDIA con drivers instalados
- El comando nvidia-smi debe funcionar

## Instalacion

1. Descarga o clona este proyecto
2. Ve a la carpeta del proyecto
3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Como usar

1. Ejecuta el servidor:
```bash
python app.py
```

2. Abre tu navegador y ve a:
```
http://localhost:5000
```

3. Para acceder desde otra computadora usa:
```
http://[IP-DEL-SERVIDOR]:5000
```

## APIs disponibles

- `/api/sistema` - Informacion completa del sistema
- `/api/gpu` - Solo informacion de tarjetas graficas

## Ejemplo de respuesta de la API

```json
{
  "procesador": {
    "uso": 25.3,
    "nucleos": 8
  },
  "memoria": {
    "uso": 45.2,
    "usada_gb": 7,
    "total_gb": 16
  },
  "gpus": [
    {
      "uso": 15,
      "memoria_usada": 2048,
      "memoria_total": 8192,
      "temperatura": 45,
      "nombre": "NVIDIA GeForce RTX 3080"
    }
  ],
  "marca_tiempo": "2024-01-15T10:30:45.123456"
}
```

## Tecnologias usadas

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Graficas: Chart.js
- Monitoreo: psutil, nvidia-smi

## Problemas comunes

### No encuentra la GPU
- Verifica que nvidia-smi funcione en la terminal
- Asegurate de tener los drivers NVIDIA instalados
- Ejecuta nvidia-smi manualmente para verificar

### Error de permisos
- Asegurate de que tu usuario pueda ejecutar nvidia-smi
- En algunos casos necesitas ejecutar con sudo

### Puerto ocupado
- Cambia el puerto en la ultima linea de app.py
- Cambia port=5000 por port=5001 o otro numero

## Licencia

Este proyecto es de codigo abierto.

## Contribuciones

Las contribuciones son bienvenidas. Puedes abrir un issue o hacer un pull request.
