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
        import traceback
        try:
            print("--- INICIANDO CEREBRO DE JARVIS ---")
            init_db()
            print("Base de datos conectada correctamente.")
            application = create_app()
            print("Cerebro y Bot inicializados.")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"--- ERROR DETALLADO ---")
            print(error_details)
            print(f"--- FIN ERROR ---")
            raise e
    return application

async def bot_init():
    app_instance = get_app()
    if not app_instance.initialized:
        await app_instance.initialize()
    if not app_instance.post_init:
        # Algunos motores requieren un post-init para handlers
        pass 
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
