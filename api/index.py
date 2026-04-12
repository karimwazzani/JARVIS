import os
import sys
import json
import asyncio
from flask import Flask, request
from telegram import Update

# Asegurar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_factory import create_app
from src.database import init_db

app = Flask(__name__)

# Inicialización diferida (Lazy Loading) con Logs Extremos
application = None

def get_app():
    global application
    if application is None:
        try:
            print("--- INICIANDO CEREBRO DE JARVIS ---", flush=True)
            # Inicializamos la App antes que la DB para agilizar
            application = create_app()
            print("Cerebro y Bot inicializados.", flush=True)
            
            # DB al final
            print("Conectando con base de datos...", flush=True)
            init_db()
            print("Base de datos lista.", flush=True)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ ERROR CRÍTICO EN ARRANQUE:\n{error_details}", flush=True)
            raise e
    return application

async def bot_init():
    app_instance = get_app()
    if not app_instance.initialized:
        print("DEBUG: Inicializando application...", flush=True)
        await app_instance.initialize()
    return app_instance

async def handle_update(update_json):
    """Procesa la actualización recibida de Telegram."""
    print(f"DEBUG: Procesando update tipo {update_json.get('update_id')}", flush=True)
    app_instance = await bot_init()
    update = Update.de_json(data=update_json, bot=app_instance.bot)
    await app_instance.process_update(update)
    print("DEBUG: Update procesado con éxito", flush=True)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update_json = request.get_json(force=True)
        try:
            # Usamos asyncio.run para asegurar que el loop se cierre correctamente en cada lambda
            asyncio.run(handle_update(update_json))
        except Exception as e:
            print(f"❌ Error procesando update: {e}", flush=True)
        return 'OK', 200
    return '<h1>JARVIS está en línea</h1><p>Sistema en espera de mensajes.</p>', 200
