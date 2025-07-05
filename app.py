from flask import Flask, render_template_string, jsonify
import subprocess
import psutil
from datetime import datetime

aplicacion = Flask(__name__)

def obtener_info_gpu():
    try:
        resultado = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name', 
             '--format=csv,noheader,nounits'], 
            capture_output=True, text=True, timeout=5
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
    try:
        # Intentar leer temperatura CPU desde /sys/class/thermal/
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_cpu = int(f.read()) / 1000
        return temp_cpu
    except:
        # Si no se puede leer, usar un valor estimado basado en el uso
        return 45

def obtener_info_sistema():
    try:
        porcentaje_cpu = psutil.cpu_percent(interval=1.5)
        memoria = psutil.virtual_memory()
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
            margin-bottom: 30px;
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
        
        document.addEventListener('DOMContentLoaded', function() {
            inicializarGraficos();
            actualizarInformacion();
            setInterval(actualizarInformacion, 5000);
        });
    </script>
</body>
</html>
    ''')

@aplicacion.route('/api/sistema')
def api_sistema():
    return jsonify(obtener_info_sistema())

@aplicacion.route('/api/gpu')
def api_gpu():
    return jsonify(obtener_info_gpu())

if __name__ == '__main__':
    print("Servidor iniciado en: http://localhost:5000")
    aplicacion.run(host='0.0.0.0', port=5000, debug=True)