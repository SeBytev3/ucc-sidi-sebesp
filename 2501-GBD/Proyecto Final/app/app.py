import sys
import random
import time
import psycopg
from threading import Thread
from flask import Flask, render_template

# Desactivar el buffering de la salida estándar
sys.stdout.flush()

app = Flask(__name__)

# URI de conexión a PostgreSQL
DB_URI = "postgresql://postgres:postgres@postgres:5432/prestamos_db"

# Conexión con reintentos (máximo 30 segundos)
MAX_RETRIES = 10
WAIT_TIME = 3  # Espera de 3 segundos entre intentos

for i in range(MAX_RETRIES):
    try:
        conn = psycopg.connect(DB_URI, autocommit=True)
        print("✅ Conectado a PostgreSQL", flush=True)
        break  # Si la conexión es exitosa, salimos del ciclo
    except psycopg.OperationalError:
        print(f"⏳ Reintentando conexión a PostgreSQL ({i+1}/{MAX_RETRIES})...", flush=True)
        time.sleep(WAIT_TIME)
else:
    raise Exception("❌ No se pudo conectar a PostgreSQL después de 10 intentos.")

clientes_nombres = ['Juan Pérez', 'Ana García', 'Carlos López', 'María Fernández']
montos_prestamo = [1000, 2000, 3000, 4000, 5000]

# Función para generar un préstamo aleatorio
def generar_prestamo():
    nombre = random.choice(clientes_nombres)
    monto = random.choice(montos_prestamo)
    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Encriptación del monto
    monto_encriptado = f"pgp_sym_encrypt('{monto}', 'clave_secreta')"
    
    return (nombre, monto_encriptado, monto, fecha)

# Función para generar un pago aleatorio
def generar_pago(prestamo_id, monto_total):
    monto_pago = random.randint(100, int(monto_total))  # Aquí monto_total es un número
    fecha_pago = time.strftime('%Y-%m-%d %H:%M:%S')
    
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO pagos.pagos (prestamo_id, monto_pago, fecha_pago, metodo_pago) VALUES (%s, %s, %s, %s)",
            (prestamo_id, monto_pago, fecha_pago, "efectivo")
        )
        print(f"✅ Pago de ${monto_pago} registrado para préstamo {prestamo_id}", flush=True)

# Función para simular préstamos y pagos de manera continua en un hilo de ejecución
def simular_prestamos_y_pagos():
    with conn.cursor() as cursor:
        while True:
            nombre, monto_encriptado, monto, fecha = generar_prestamo()
            cursor.execute("SELECT cliente_id FROM clientes.clientes WHERE nombre = %s", (nombre,))
            result = cursor.fetchone()
            if not result:
                print(f"❌ Cliente no encontrado: {nombre}", flush=True)
                continue
            cliente_id = result[0]
            # Fecha de vencimiento aleatoria entre 30 y 180 días desde hoy
            fecha_vencimiento = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + random.randint(86400*30, 86400*180)))
            
            # Inserción de préstamo con monto encriptado
            cursor.execute(
                f"INSERT INTO prestamos.prestamos (cliente_id, monto, fecha_inicio, fecha_vencimiento, tasa_interes) "
                f"VALUES (%s, {monto_encriptado}, %s, %s, %s) RETURNING prestamo_id",
                (cliente_id, fecha, fecha_vencimiento, 5.0)
            )
            prestamo_id = cursor.fetchone()[0]
            print(f"💸 Préstamo generado para {nombre}: ${monto} con vencimiento {fecha_vencimiento}", flush=True)

            # Simula un pago aleatorio para ese préstamo
            generar_pago(prestamo_id, monto)

            # Espera aleatoria entre 3 y 6 segundos antes de generar el siguiente préstamo y pago
            time.sleep(random.randint(3, 6))

# Iniciar el hilo para la simulación de préstamos y pagos
Thread(target=simular_prestamos_y_pagos, daemon=True).start()

@app.route('/')
def index():
    return "✅ Sistema de Préstamos Personales en funcionamiento!"

@app.route('/consultar_prestamos', methods=['GET'])
def consultar_prestamos():
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT p.prestamo_id, 
                   p.cliente_id, 
                   pgp_sym_decrypt(p.monto, 'clave_secreta')::numeric AS monto,
                   p.fecha_inicio, 
                   p.fecha_vencimiento, 
                   p.tasa_interes 
            FROM prestamos.prestamos p
            JOIN clientes.clientes c ON p.cliente_id = c.cliente_id
            WHERE c.nombre = %s
        """, ('Juan Pérez',))  # El nombre puede ser elegido de estos: 'Juan Pérez', 'Ana García', 'Carlos López', 'María Fernández'
        prestamos = cursor.fetchall()
        return render_template('prestamos.html', prestamos=prestamos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
