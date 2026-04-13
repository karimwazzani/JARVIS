import os
import sys
import json
import traceback

from flask import Flask, request as flask_request

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# ====================================================================
# CAPA 1: Funciones ultra-ligeras (NO importan nada pesado)
# ====================================================================

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def tg_send(chat_id, text, parse_mode=None):
    """Envía un mensaje vía HTTP puro. Sin librerías pesadas."""
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        r = requests.post(url, json=payload, timeout=8)
        print(f"DEBUG: tg_send status={r.status_code}", flush=True)
    except Exception as e:
        print(f"ERROR tg_send: {e}", flush=True)

def tg_send_action(chat_id, action="typing"):
    """Envía una acción de chat (typing...) vía HTTP puro."""
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = TELEGRAM_API.format(token=token, method="sendChatAction")
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
    except:
        pass

# ====================================================================
# CAPA 2: Inicialización pesada (SOLO se carga cuando es necesario)
# ====================================================================

_db_initialized = False

def ensure_db():
    """Inicializa la base de datos (lazy)."""
    global _db_initialized
    if not _db_initialized:
        print("DEBUG: Inicializando base de datos...", flush=True)
        from src.database import init_db
        init_db()
        _db_initialized = True
        print("DEBUG: Base de datos lista.", flush=True)

def process_text_message(chat_id, text):
    """Procesa un mensaje de texto con el agente de IA."""
    print("DEBUG: Cargando módulo de IA...", flush=True)
    
    # Inicializar DB
    ensure_db()
    
    # Importar el agente de IA (pesado, pero solo cuando se necesita)
    from src.ai_agent import get_ai_response
    from src.database import SessionLocal, LogEvento
    
    print("DEBUG: Módulos cargados. Procesando mensaje...", flush=True)
    
    # Registrar evento
    try:
        db = SessionLocal()
        db.add(LogEvento(chat_id=str(chat_id), evento=f"Texto: {text}"))
        db.commit()
        db.close()
    except Exception as e:
        print(f"WARN: No se pudo registrar evento: {e}", flush=True)
    
    # Historial simple (sin persistencia entre invocaciones en serverless)
    historial = [{"role": "user", "content": text}]
    
    # Obtener respuesta de OpenAI
    print("DEBUG: Enviando a OpenAI...", flush=True)
    response_text, _ = get_ai_response(historial, str(chat_id))
    print(f"DEBUG: Respuesta recibida ({len(response_text)} chars)", flush=True)
    
    return response_text

# ====================================================================
# CAPA 3: Webhook principal (Ultra-ligero)
# ====================================================================

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask_request.method == 'GET':
        return '<h1>JARVIS Online</h1><p>Sistema operativo.</p>', 200

    # --- POST: Procesar update de Telegram ---
    try:
        update = flask_request.get_json(force=True)
        print(f"DEBUG: Update {update.get('update_id')} recibido", flush=True)
        
        # Extraer datos del mensaje
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id:
            print("DEBUG: Update sin chat_id, ignorando.", flush=True)
            return 'OK', 200
        
        print(f"DEBUG: Chat={chat_id}, Texto='{text[:50]}'", flush=True)
        
        # --- PING (prueba de conectividad) ---
        if text.lower() == 'ping':
            tg_send(chat_id, "PONG! 🚀 JARVIS conectado.")
            return 'OK', 200
        
        # --- COMANDO /start ---
        if text == '/start':
            tg_send(chat_id, 
                "¡Hola! Soy JARVIS, tu asistente analítico.\n\n"
                "Puedes hablarme, enviarme audios o usar comandos manuales.\n"
                "Usa /ayuda para más info.")
            return 'OK', 200
        
        # --- COMANDO /ayuda ---
        if text == '/ayuda':
            tg_send(chat_id,
                "🧠 Notas de Voz y Texto (IA):\n"
                "Solo escríbeme lo que necesitas.\n\n"
                "💸 Comandos Manuales:\n"
                "• /gasto 1500 café\n"
                "• /ingreso 50000 sueldo\n"
                "• /resumen")
            return 'OK', 200
        
        # --- COMANDO /resumen ---
        if text == '/resumen':
            try:
                ensure_db()
                from src.database import SessionLocal, Transaccion
                from sqlalchemy import func
                db = SessionLocal()
                gastos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "gasto").scalar() or 0.0
                ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "ingreso").scalar() or 0.0
                db.close()
                tg_send(chat_id, f"📊 Balance\nIngresos: ${ingresos:,.2f}\nGastos: ${gastos:,.2f}\nSaldo: ${ingresos - gastos:,.2f}")
            except Exception as e:
                tg_send(chat_id, f"Error al obtener resumen: {e}")
            return 'OK', 200
        
        # --- COMANDO /gasto ---
        if text.startswith('/gasto'):
            try:
                parts = text.split(maxsplit=2)
                if len(parts) < 3:
                    tg_send(chat_id, "❌ Uso: /gasto [monto] [descripción]")
                    return 'OK', 200
                monto = float(parts[1])
                desc = parts[2]
                ensure_db()
                from src.database import SessionLocal, Transaccion
                db = SessionLocal()
                db.add(Transaccion(tipo="gasto", monto=monto, descripcion=desc))
                db.commit()
                db.close()
                tg_send(chat_id, f"💸 Gasto: ${monto:,.2f} ({desc})")
            except ValueError:
                tg_send(chat_id, "❌ El monto necesita ser un número.")
            except Exception as e:
                tg_send(chat_id, f"Error: {e}")
            return 'OK', 200
        
        # --- COMANDO /ingreso ---
        if text.startswith('/ingreso'):
            try:
                parts = text.split(maxsplit=2)
                if len(parts) < 3:
                    tg_send(chat_id, "❌ Uso: /ingreso [monto] [descripción]")
                    return 'OK', 200
                monto = float(parts[1])
                desc = parts[2]
                ensure_db()
                from src.database import SessionLocal, Transaccion
                db = SessionLocal()
                db.add(Transaccion(tipo="ingreso", monto=monto, descripcion=desc))
                db.commit()
                db.close()
                tg_send(chat_id, f"💰 Ingreso: ${monto:,.2f} ({desc})")
            except ValueError:
                tg_send(chat_id, "❌ El monto necesita ser un número.")
            except Exception as e:
                tg_send(chat_id, f"Error: {e}")
            return 'OK', 200
        
        # --- MENSAJE DE TEXTO LIBRE (IA) ---
        if text and not text.startswith('/'):
            tg_send_action(chat_id, "typing")
            try:
                response = process_text_message(chat_id, text)
                tg_send(chat_id, response)
                print("DEBUG: Respuesta enviada al usuario.", flush=True)
            except Exception as e:
                print(f"ERROR procesando texto: {traceback.format_exc()}", flush=True)
                tg_send(chat_id, f"⚠️ Error interno: {str(e)[:200]}")
            return 'OK', 200
        
        # Si no es nada de lo anterior, ignorar
        print(f"DEBUG: Mensaje no procesable, ignorando.", flush=True)
        return 'OK', 200
        
    except Exception as e:
        print(f"❌ ERROR FATAL EN WEBHOOK:\n{traceback.format_exc()}", flush=True)
        return 'OK', 200
