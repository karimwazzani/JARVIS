import matplotlib
matplotlib.use('Agg') # Requerido para no usar interfaz gráfica
import matplotlib.pyplot as plt
import os
from src.database import SessionLocal, Transaccion
from sqlalchemy import func

def generar_grafico_balance(chat_id: str) -> str:
    db = SessionLocal()
    gastos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "gasto").scalar() or 0.0
    ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "ingreso").scalar() or 0.0
    db.close()
    
    if gastos == 0 and ingresos == 0:
        return ""
        
    labels = ['Ingresos', 'Gastos']
    sizes = [ingresos, gastos]
    colors = ['#4caf50', '#f44336']
    
    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Balance General: Ingresos vs Gastos')
    
    file_path = f"balance_{chat_id}.png"
    plt.savefig(file_path)
    plt.close()
    return file_path

def spotify_control(accion: str, query: str = "") -> str:
    """Mock/Stub para la integración con Spotify y servicios externos."""
    if accion == "reproducir_cancion":
        return f"Reproduciendo: '{query}' en Spotify (Integración API pendiente)."
    elif accion == "pausa":
        return "Música pausada en Spotify."
    elif accion == "modo_relajacion":
        return "Modo relajación activado: Volumen al 20%, luces atenuadas, playlist relax reproduciéndose."
    return "Comando multimedia no reconocido."

def tapo_snapshot(ip: str, usr: str, pwd: str, chat_id: str) -> str:
    """Invoca la transmisión RTSP de las cámaras TP-Link y extrae keyframes usando Open Source CV."""
    import cv2
    import os
    import urllib.parse
    
    try:
        if not os.path.exists("temp"): os.makedirs("temp")
        filepath = f"temp/tapo_shot_{chat_id}.jpg"
        
        # Encodear caracteres crudos del password hacia HTML Seguro
        safe_usr = urllib.parse.quote_plus(usr)
        safe_pwd = urllib.parse.quote_plus(pwd)
        rtsp_url = f"rtsp://{safe_usr}:{safe_pwd}@{ip}:554/stream1"
        
        cap = cv2.VideoCapture(rtsp_url)
        # Limpiar el bufer para forzar que el video envíe el frame de este preciso momento 
        for _ in range(7): cap.read()
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            cv2.imwrite(filepath, frame)
            return filepath
        else:
            return "Error Sensorial: Pude enrutar al dispositivo de red interna pero bloqueó la entrega de fotogramas (Privacy Mode activo o bug en red)."
    except Exception as e:
        return f"Error interceptando socket físico de video ({ip}): {str(e)}"
