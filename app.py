from flask import Flask, render_template_string, jsonify
import subprocess
import psutil
import time
from datetime import datetime
import polars as pl
import os
import csv
import threading



CSV_RUTA = 'registro.csv'
aplicacion = Flask(__name__)


def crea_archivo_csv():
    """Crea el archivo CSV con las cabeceras si no existe"""
    if not os.path.exists(CSV_RUTA):
        # Crear un DataFrame con una fila vacía para que escriba las cabeceras
        df = pl.DataFrame({
            "marca_tiempo": [None],
            "uso_cpu": [None],
            "temp_cpu": [None],
            "uso_ram": [None],
            "ram_usada_gb": [None],
            "ram_total_gb": [None],
        })
        # Escribir el DataFrame con cabeceras
        df.write_csv(CSV_RUTA, include_header=True)
    else:
        # Verificar que el archivo existente tenga las cabeceras correctas
        try:
            with open(CSV_RUTA, 'r') as f:
                first_line = f.readline().strip()
                expected_headers = "marca_tiempo,uso_cpu,temp_cpu,uso_ram,ram_usada_gb,ram_total_gb"
                if first_line != expected_headers:
                    # Si las cabeceras no coinciden, recrear el archivo
                    df = pl.DataFrame({
                        "marca_tiempo": [None],
                        "uso_cpu": [None],
                        "temp_cpu": [None],
                        "uso_ram": [None],
                        "ram_usada_gb": [None],
                        "ram_total_gb": [None],
                    })
                    df.write_csv(CSV_RUTA, include_header=True)
        except Exception as e:
            print(f"Error verificando archivo CSV: {e}")
            # Si hay error al leer, recrear el archivo
            df = pl.DataFrame({
                "marca_tiempo": [None],
                "uso_cpu": [None],
                "temp_cpu": [None],
                "uso_ram": [None],
                "ram_usada_gb": [None],
                "ram_total_gb": [None],
            })
            df.write_csv(CSV_RUTA, include_header=True)

def guardar_fila_csv(datos):
    """Guarda una nueva fila en el CSV"""
    try:
        # Crear un DataFrame con los datos actuales
        fila = pl.DataFrame({
            "marca_tiempo": [datos['marca_tiempo']],
            "uso_cpu": [datos['procesador']['uso']],
            "temp_cpu": [datos['procesador']['temperatura']],
            "uso_ram": [datos['memoria']['uso']],
            "ram_usada_gb": [datos['memoria']['usada_gb']],
            "ram_total_gb": [datos['memoria']['total_gb']],
        })
        
        # Verificar si el archivo existe y tiene contenido
        file_exists = os.path.exists(CSV_RUTA) and os.path.getsize(CSV_RUTA) > 0
        
        # Escribir la fila (append si el archivo existe y no está vacío)
        fila.write_csv(
            CSV_RUTA,
            include_header=not file_exists,  # Solo incluir cabecera si el archivo no existe o está vacío
            separator=",",
            mode='a' if file_exists else 'w'
        )
    except Exception as e:
        print(f"Error al guardar en CSV: {e}")
        # Intentar recrear el archivo si hay error
        crea_archivo_csv()
        # Volver a intentar guardar
        fila.write_csv(CSV_RUTA, include_header=False, separator=",", mode='a')
def iniciar_registro_csv(intervalo=5):
    """Inicia un hilo que registra los datos en CSV cada intervalo"""
    def registrar():
        while True:
            datos = obtener_info_sistema()
            guardar_fila_csv(datos)
            time.sleep(intervalo)
    
    hilo = threading.Thread(target=registrar, daemon=True)
    hilo.start()
    

def obtener_info_gpu():
    try:
        resultado = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name', 
             '--format=csv,noheader,nounits'], 
            capture_output=True, text=True, timeout=3
        )
        if resultado.returncode == 0:
            gpus = []
            for linea in resultado.stdout.strip().split('\n'):
                if linea.strip():
                    partes = linea.split(', ')
                    if len(partes) >= 5:
                        gpus.append({
                            'uso': int(partes[0]),
                            'memoria_usada': int(partes[1]),
                            'memoria_total': int(partes[2]),
                            'temperatura': int(partes[3]),
                            'nombre': partes[4]
                        })
            return gpus
    except:
        pass
    return [{'uso': 0, 'memoria_usada': 0, 'memoria_total': 0, 'temperatura': 0, 'nombre': 'No disponible'}]

def obtener_temperatura_cpu():
    """Obtiene la temperatura de la CPU de múltiples fuentes"""
    try:
        # Método 1: Intentar con psutil.sensors_temperatures()
        try:
            temperaturas = psutil.sensors_temperatures()
            if 'coretemp' in temperaturas:
                # Intel CPUs
                return temperaturas['coretemp'][0].current
            elif 'k10temp' in temperaturas:
                # AMD CPUs
                return temperaturas['k10temp'][0].current
            elif 'cpu_thermal' in temperaturas:
                # ARM CPUs
                return temperaturas['cpu_thermal'][0].current
            elif temperaturas:
                # Cualquier otro sensor disponible
                for sensor_name, sensor_list in temperaturas.items():
                    if sensor_list:
                        return sensor_list[0].current
        except:
            pass

        # Método 2: Intentar leer desde /sys/class/thermal/
        try:
            # Buscar en diferentes thermal zones
            for i in range(10):  # Probar hasta thermal_zone9
                try:
                    with open(f'/sys/class/thermal/thermal_zone{i}/temp', 'r') as f:
                        temp = int(f.read()) / 1000
                        if 20 <= temp <= 100:  # Temperatura válida
                            return temp
                except:
                    continue
        except:
            pass

        # Método 3: Intentar con hwmon
        try:
            import glob
            hwmon_paths = glob.glob('/sys/class/hwmon/hwmon*/temp*_input')
            for path in hwmon_paths:
                try:
                    with open(path, 'r') as f:
                        temp = int(f.read()) / 1000
                        if 20 <= temp <= 100:  # Temperatura válida
                            return temp
                except:
                    continue
        except:
            pass

        # Método 4: Intentar con lm-sensors (
        try:
            resultado = subprocess.run(['sensors', '-j'], capture_output=True, text=True, timeout=3)
            if resultado.returncode == 0:
                import json
                datos = json.loads(resultado.stdout)
                for sensor in datos.values():
                    if isinstance(sensor, dict):
                        for key, value in sensor.items():
                            if 'temp' in key.lower() and 'input' in key:
                                if isinstance(value, (int, float)) and 20 <= value <= 100:
                                    return value
        except:
            pass

    except Exception as e:
        print(f"Error al obtener temperatura CPU: {e}")
    
    # Si no se puede obtener la temperatura real, estimar basado en el uso de CPU
    try:
        uso_cpu = psutil.cpu_percent(interval=0.1)
        # Estimación simple: temperatura base + factor por uso
        temp_estimada = 35 + (uso_cpu * 0.5)  # 35°C base + 0.5°C por % de uso
        return min(temp_estimada, 85)  # Máximo 85°C
    except:
        return 45  # Valor por defecto

def debug_temperatura():
    """Función para debug: muestra qué métodos de temperatura están disponibles"""
    print("=== DEBUG TEMPERATURA CPU ===")
    
    # Método 1: psutil.sensors_temperatures()
    try:
        temperaturas = psutil.sensors_temperatures()
        print(f"1. psutil.sensors_temperatures(): {temperaturas}")
        if temperaturas:
            for nombre, sensores in temperaturas.items():
                print(f"   - {nombre}: {sensores}")
    except Exception as e:
        print(f"1. psutil.sensors_temperatures(): Error - {e}")
    
    # Método 2: /sys/class/thermal/
    print("2. /sys/class/thermal/ zones:")
    for i in range(5):
        try:
            with open(f'/sys/class/thermal/thermal_zone{i}/temp', 'r') as f:
                temp = int(f.read()) / 1000
                print(f"   - thermal_zone{i}: {temp}°C")
        except:
            print(f"   - thermal_zone{i}: No disponible")
    
    # Método 3: hwmon
    try:
        import glob
        hwmon_paths = glob.glob('/sys/class/hwmon/hwmon*/temp*_input')
        print(f"3. hwmon paths encontrados: {hwmon_paths}")
        for path in hwmon_paths[:3]:  # Solo mostrar los primeros 3
            try:
                with open(path, 'r') as f:
                    temp = int(f.read()) / 1000
                    print(f"   - {path}: {temp}°C")
            except:
                print(f"   - {path}: Error al leer")
    except Exception as e:
        print(f"3. hwmon: Error - {e}")
    
    # Método 4: lm-sensors
    try:
        resultado = subprocess.run(['sensors', '-j'], capture_output=True, text=True, timeout=3)
        if resultado.returncode == 0:
            print(f"4. lm-sensors disponible: {len(resultado.stdout)} caracteres")
        else:
            print("4. lm-sensors: No disponible")
    except:
        print("4. lm-sensors: No instalado")
    
    print("=== FIN DEBUG ===")

@aplicacion.route('/debug')
def debug_route():
    """Ruta para debug de temperatura"""
    debug_temperatura()
    return jsonify({
        'temperatura_actual': obtener_temperatura_cpu(),
        'mensaje': 'Revisa la consola del servidor para ver el debug completo'
    })

def obtener_info_sistema():
    try:
        porcentaje_cpu = psutil.cpu_percent(interval=1.5)
        memoria = psutil.virtual_memory()
        time.sleep(1)
        temp_cpu = obtener_temperatura_cpu()
            
        
        return {
            'procesador': {
                'uso': porcentaje_cpu,
                'nucleos': psutil.cpu_count(),
                'temperatura': temp_cpu
            },
            'memoria': {
                'uso': memoria.percent,
                'usada_gb': memoria.used // (1024**3),
                'total_gb': memoria.total // (1024**3)
            },
            'gpus': obtener_info_gpu(),
            'marca_tiempo': datetime.now().isoformat()
        }
    except Exception as error:
        return {'error': str(error), 'marca_tiempo': datetime.now().isoformat()}

@aplicacion.route('/')
# appi para la ruta principal
def pagina_principal():
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }
        .contenedor {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #ffffff;
            margin-bottom: 0px;
            margin:0px  ;
        }
        .grid-principal {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        @media (max-width: 900px) {
            .grid-principal {
                grid-template-columns: 1fr;
            }
        }
        .stat-card, .tabla {
            background-color: #2d2d2d;
            padding: 20px;
            border-radius: 5px;
            border: 1px solid #404040;
            margin-bottom: 0;
        }
        .stat-title {
            font-size: 14px;
            color: #b0b0b0;
            margin-bottom: 10px;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
        }
        .tabla h2 {
            color: #ffffff;
            margin: 0;
            padding: 15px 20px;
            border-bottom: 1px solid #404040;
            font-size: 18px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        .tabla_temp{
        width: fit-content;
        margin: auto;
        margin-right: auto;
        margin-right: 0px;
        transform: scale(0.7);
                                  
                                  }
        th, td {
            padding: 12px 20px;
            text-align: left;
            border-bottom: 1px solid #404040;
        }
        th {
            background-color: #3a3a3a;
            color: #ffffff;
            font-weight: bold;
        }
        tr:last-child td {
            border-bottom: none;
        }
        .status {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .normal { background-color: #4caf50; }
        .alto { background-color: #ff9800; }
        .temp-baja { 
            background-color: #27ae60; 
            color: white; 
            padding: 4px 8px;
            border-radius: 4px;
        }
        .temp-media { 
            background-color: #f39c12; 
            color: white; 
            padding: 4px 8px;
            border-radius: 4px;
        }
        .temp-alta { 
            background-color: #e74c3c; 
            color: white; 
            padding: 4px 8px;
            border-radius: 4px;
        }
        .boton {
            background-color: #404040;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            margin: 10px auto;
            display: block;
        }
        .boton:hover {
            background-color: #505050;
        }
        .actualizacion {
            text-align: center;
            color: #b0b0b0;
            margin-top: 20px;
            font-size: 12px;
        }
        .divisor{
        display:flex;
        }
    </style>
</head>
<body>

    <div class="contenedor">
        <h1>Webtop</h1>
        <div class="tabla_temp">
                <table id="table-temp-cpu">
                    <thead>
                        <tr>
                            <th>Temperatura</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody id="cuerpo-temp-cpu">
                    </tbody>
                </table>
            </div>
        
                                  
        <div class="grid-principal">
            <div class="stat-card">
                <div class="stat-title">Procesador</div>
                <div class="stat-value" id="uso-procesador">0%</div>
                <div style="height: 180px; margin-top: 20px;">
                    <canvas id="grafico-procesador"></canvas>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Memoria RAM</div>
                <div class="stat-value" id="uso-memoria">0%</div>
                <div style="height: 180px; margin-top: 20px;">
                    <canvas id="grafico-memoria"></canvas>
                </div>
            </div>
            <div class="tabla">
                <h2>Detalles del Sistema</h2>
                <table id="tabla-sistema">
                    <thead>
                        <tr>
                            <th>Componente</th>
                            <th>Uso</th>
                            <th>Detalles</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody id="cuerpo-tabla">
                    </tbody>
                </table>
            </div>
            <div class="tabla">
                <h2>GPUs</h2>
                <table id="tabla-gpu">
                    <thead>
                        <tr>
                            <th>GPU</th>
                            <th>Uso</th>
                            <th>Memoria</th>
                            <th>Temperatura</th>
                        </tr>
                    </thead>
                    <tbody id="cuerpo-gpu">
                    </tbody>
                </table>
            </div>
            
        </div>
        <button class="boton" onclick="actualizarDatos()">Actualizar Datos</button>
        <div class="actualizacion" id="ultima-actualizacion">
            Ultima actualizacion: Nunca
        </div>
    </div>
    <script>
        let graficoProcesador, graficoMemoria;
        let datosProcesador = [], datosMemoria = [];
        let etiquetas = [];
        
        function inicializarGraficos() {
            const ctx1 = document.getElementById('grafico-procesador').getContext('2d');
            const ctx2 = document.getElementById('grafico-memoria').getContext('2d');
            
            graficoProcesador = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Uso CPU (%)',
                        data: datosProcesador,
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76,175,80,0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, max: 100 }, x: { display: false } },
                    elements: { point: { radius: 0 } }
                }
            });
            
            graficoMemoria = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Uso RAM (%)',
                        data: datosMemoria,
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255,152,0,0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, max: 100 }, x: { display: false } },
                    elements: { point: { radius: 0 } }
                }
            });
        }
        
        function actualizarGraficos(usoProcesador, usoMemoria) {
            const ahora = new Date().toLocaleTimeString();
            etiquetas.push(ahora);
            datosProcesador.push(usoProcesador);
            datosMemoria.push(usoMemoria);
            
            if (etiquetas.length > 90) {
                etiquetas.shift();
                datosProcesador.shift();
                datosMemoria.shift();
            }
            
            graficoProcesador.data.labels = etiquetas;
            graficoProcesador.data.datasets[0].data = datosProcesador;
            graficoProcesador.update('none');
            
            graficoMemoria.data.labels = etiquetas;
            graficoMemoria.data.datasets[0].data = datosMemoria;
            graficoMemoria.update('none');
        }
        
        function actualizarTemperaturaCPU(tempCPU) {
            const tbody = document.getElementById('cuerpo-temp-cpu');
            tbody.innerHTML = '';
            
            let estado = '';
            let claseEstado = '';
            
            if (tempCPU < 50) {
                estado = 'Normal';
                claseEstado = 'temp-baja';
            } else if (tempCPU < 70) {
                estado = 'Media';
                claseEstado = 'temp-media';
            } else {
                estado = 'Alta';
                claseEstado = 'temp-alta';
            }
            
            tbody.innerHTML = `
                <tr>
                    <td>${tempCPU.toFixed(1)}°C</td>
                    <td><span class="${claseEstado}">${estado}</span></td>
                </tr>
            `;
        }
        
        function actualizarInformacion() {
            fetch('/api/sistema')
                .then(respuesta => respuesta.json())
                .then(datos => {
                    document.getElementById('uso-procesador').textContent = datos.procesador.uso.toFixed(1) + '%';
                    document.getElementById('uso-memoria').textContent = datos.memoria.uso.toFixed(1) + '%';
                    
                    actualizarGraficos(datos.procesador.uso, datos.memoria.uso);
                    actualizarTabla(datos);
                    actualizarTablaGpu(datos.gpus);
                    actualizarTemperaturaCPU(datos.procesador.temperatura);
                    
                    const tiempo = new Date(datos.marca_tiempo);
                    document.getElementById('ultima-actualizacion').textContent = 
                        'Ultima actualizacion: ' + tiempo.toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('ultima-actualizacion').textContent = 'Error al obtener datos';
                });
        }
        
        function actualizarTabla(datos) {
            const tbody = document.getElementById('cuerpo-tabla');
            tbody.innerHTML = '';
            
            const estadoProcesador = datos.procesador.uso > 80 ? 'alto' : 'normal';
            tbody.innerHTML += `
                <tr>
                    <td>Procesador</td>
                    <td>${datos.procesador.uso.toFixed(1)}%</td>
                    <td>${datos.procesador.nucleos} nucleos</td>
                    <td><span class="status ${estadoProcesador}"></span>${estadoProcesador === 'normal' ? 'Normal' : 'Alto uso'}</td>
                </tr>
            `;
            
            const estadoMemoria = datos.memoria.uso > 80 ? 'alto' : 'normal';
            tbody.innerHTML += `
                <tr>
                    <td>Memoria RAM</td>
                    <td>${datos.memoria.uso.toFixed(1)}%</td>
                    <td>${datos.memoria.usada_gb}/${datos.memoria.total_gb} GB</td>
                    <td><span class="status ${estadoMemoria}"></span>${estadoMemoria === 'normal' ? 'Normal' : 'Alto uso'}</td>
                </tr>
            `;
        }
        
        function actualizarTablaGpu(gpus) {
            const tbody = document.getElementById('cuerpo-gpu');
            tbody.innerHTML = '';
            
            gpus.forEach((gpu, indice) => {
                tbody.innerHTML += `
                    <tr>
                        <td>${gpu.nombre}</td>
                        <td>${gpu.uso}%</td>
                        <td>${gpu.memoria_usada}/${gpu.memoria_total} MB</td>
                        <td>${gpu.temperatura}°C</td>
                    </tr>
                `;
            });
        }
        
        function actualizarDatos() {
            actualizarInformacion();
        }
        
        function actualizarSoloTemperatura() {
            fetch('/api/temperatura')
                .then(respuesta => respuesta.json())
                .then(datos => {
                    if (datos.temperatura) {
                        actualizarTemperaturaCPU(datos.temperatura);
                    }
                })
                .catch(error => {
                    console.error('Error al obtener temperatura:', error);
                });
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            inicializarGraficos();
            actualizarInformacion();
            setInterval(actualizarInformacion, 3000); // Datos completos cada 5 segundos
            setInterval(actualizarSoloTemperatura, 1000); // Temperatura cada segundo
        });
    </script>
</body>
</html>
    ''')

@aplicacion.route('/api/temperatura')
def api_temperatura():
    """API solo para temperatura CPU"""
    try:
        temp_cpu = obtener_temperatura_cpu()
        return jsonify({
            'temperatura': temp_cpu,
            'marca_tiempo': datetime.now().isoformat()
        })
    except Exception as error:
        return jsonify({'error': str(error), 'marca_tiempo': datetime.now().isoformat()})

@aplicacion.route('/api/sistema')
def api_sistema():
    return jsonify(obtener_info_sistema())

@aplicacion.route('/api/gpu')
def api_gpu():
    return jsonify(obtener_info_gpu())

# @aplicacion.route('/api/csv')
# def api_csv():
#     "Api para hacer graficas"
#     return jsonify(csv())
 
if __name__ == '__main__':
    print("Servidor iniciado en: http://localhost:5000")
    crea_archivo_csv()
    iniciar_registro_csv(intervalo=5)
    aplicacion.run(host='0.0.0.0', port=5000, debug=True)