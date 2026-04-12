import serial
import time
from database import SessionLocal, SensorAlert

# CONFIGURACIÓN IMPORTANTE: 
# Averigua qué puerto usa el Arduino Nano en tu Windows (lo dice en el IDE de Arduino)
# Cámbialo acá abajo (Ej. 'COM3', 'COM4', 'COM5')
PUERTO_SERIAL = "COM4" 
BAUD_RATE = 9600

def run_listener():
    try:
        ser = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=1)
        print(f"📡 JARVIS Listener: Escuchando hardware en el puerto {PUERTO_SERIAL}...")
    except serial.SerialException as e:
        print(f"❌ Error crítico abriendo puerto serial {PUERTO_SERIAL}: {e}")
        print(f"Por favor abre el IDE de Arduino y verifica que puerto usa el Arduino Nano, luego cámbialo en arduino_listener.py.")
        return

    db = SessionLocal()
    
    try:
        while True:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if "ALERTA: MOVIMIENTO_DETECTADO" in linea:
                    print("⚠️ Modulo Físico: ¡Movimiento detectado! Cruzando a base de datos...")
                    
                    # Se inyecta la alerta en SQLite silenciosamente (¡0 Tokens gastados!)
                    alerta = SensorAlert(
                        sensor_id="PIR_Centinela_Habitacion", 
                        mensaje="¡Ojo de Halcón ha detectado movimiento en el cuarto!"
                    )
                    db.add(alerta)
                    db.commit()
                    print("✅ Alerta subida. JARVIS telegram bot la captará en el próximo ciclo de 5 segundos.")

            # Dormir el loop una fracción para no ahogar la CPU
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("🛑 Listener cerrado por el usuario.")
    except Exception as e:
        print(f"⚠️ Error procesando flujo serial: {e}")
    finally:
        db.close()
        ser.close()

if __name__ == "__main__":
    run_listener()
