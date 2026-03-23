import sys
import time
from database import SessionLocal, SensorAlert

def main():
    print("=== SIMULADOR DE HARDWARE IOT (JARVIS) ===")
    print("Este script simula ser un ESP32 o circuito remoto en el hogar.")
    print("-------------------------------------------------")
    print("1. Activar Sensor de Movimiento (PIR) en la Sala")
    print("2. Activar Alarma de Incendio (Humo) en la Cocina")
    print("3. Activar Apertura de Puerta Principal")
    print("4. Volver (Salir)")
    
    opcion = input("\nElige una opción para inyectar en la red de JARVIS (1-4): ")
    
    db = SessionLocal()
    if opcion == "1":
        alerta = SensorAlert(sensor_id="PIR_Sala", mensaje="¡Se ha detectado movimiento en la sala de estar!")
    elif opcion == "2":
        alerta = SensorAlert(sensor_id="MQ2_Cocina", mensaje="¡PELIGRO! Presencia de humo o gas detectada en la cocina.")
    elif opcion == "3":
        alerta = SensorAlert(sensor_id="PUERTA_Principal", mensaje="La puerta principal ha sido abierta.")
    else:
        print("Saliendo de la simulación...")
        db.close()
        return

    db.add(alerta)
    db.commit()
    print("\n✅ Señal inyectada a la Base de Datos Central.")
    print("JARVIS procesará el evento en los próximos 5 segundos y te enviará una notificación Push a Telegram.")
    db.close()

if __name__ == "__main__":
    main()
