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


#pendiente
def obtener_info_sistema():
    try:
        porcentaje_cpu = psutil.cpu_percent(interval=1)
        memoria = psutil.virtual_memory()
        
        return {
            'procesador': {
                'uso': porcentaje_cpu,
                'nucleos': psutil.cpu_count()
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
    <title>Monitor del Sistema</title>
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
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background-color: #2d2d2d;
            padding: 20px;
            border-radius: 5px;
            border: 1px solid #404040;
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
        
        .tabla {
            background-color: #2d2d2d;
            border-radius: 5px;
            border: 1px solid #404040;
            margin-bottom: 20px;
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
    </style>
</head>
<body>
    <div class="contenedor">
        <h1>Monitor del Sistema</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-title">Procesador</div>
                <div class="stat-value" id="uso-procesador">0%</div>
            </div>

            <div class="stat-card">
                <div class="stat-title">Memoria RAM</div>
                <div class="stat-value" id="uso-memoria">0%</div>
            </div>
        </div>

        <div class="tabla">
            <h2>Uso del Sistema</h2>
            <div style="width: 300px; height: 300px; margin: 20px auto;">
                <canvas id="grafico-pastel"></canvas>
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

        <button class="boton" onclick="actualizarDatos()">Actualizar Datos</button>

        <div class="actualizacion" id="ultima-actualizacion">
            Ultima actualizacion: Nunca
        </div>
    </div>

    <script>
        let graficoPastel;
        
        function crearGraficoPastel() {
            const ctx = document.getElementById('grafico-pastel').getContext('2d');
            graficoPastel = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['CPU Libre', 'CPU Usado', 'RAM Libre', 'RAM Usada'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#4caf50', '#ff5722', '#2196f3', '#ff9800']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });
        }
        
        function actualizarGraficoPastel(datos) {
            const cpuLibre = 100 - datos.procesador.uso;
            const cpuUsado = datos.procesador.uso;
            const ramLibre = 100 - datos.memoria.uso;
            const ramUsada = datos.memoria.uso;
            
            graficoPastel.data.datasets[0].data = [cpuLibre, cpuUsado, ramLibre, ramUsada];
            graficoPastel.update();
        }
        
        function actualizarInformacion() {
            fetch('/api/sistema')
                .then(respuesta => respuesta.json())
                .then(datos => {
                    document.getElementById('uso-procesador').textContent = datos.procesador.uso.toFixed(1) + '%';
                    document.getElementById('uso-memoria').textContent = datos.memoria.uso.toFixed(1) + '%';
                    
                    actualizarGraficoPastel(datos);
                    actualizarTabla(datos);
                    
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
            
            datos.gpus.forEach((gpu, indice) => {
                const estadoGpu = gpu.uso > 80 ? 'alto' : 'normal';
                tbody.innerHTML += `
                    <tr>
                        <td>GPU ${indice + 1}</td>
                        <td>${gpu.uso}%</td>
                        <td>${gpu.nombre} - ${gpu.temperatura}°C</td>
                        <td><span class="status ${estadoGpu}"></span>${estadoGpu === 'normal' ? 'Normal' : 'Alto uso'}</td>
                    </tr>
                `;
            });
        }
        
        function actualizarDatos() {
            actualizarInformacion();
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            crearGraficoPastel();
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