import os
import sys
import json
import asyncio
from flask import Flask, request
from telegram import Update

# Añadir el directorio raíz al path para que las importaciones de 'src' funcionen en Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_factory import create_app
from src.database import init_db

app = Flask(__name__)

# Inicializar base de datos y bot con manejo de errores para debug en Vercel
try:
    print("Iniciando JARVIS en la nube...")
    init_db()
    print("DB inicializada OK.")
    application = create_app()
    print("Bot instanciado OK.")
except Exception as e:
    print(f"CRITICAL ERROR DURANTE EL INICIO: {e}")
    application = None

async def handle_update(update_json):
    """Procesa la actualización recibida de Telegram."""
    async with application:
        update = Update.de_json(data=update_json, bot=application.bot)
        await application.process_update(update)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update_json = request.get_json(force=True)
        # Ejecutar el procesamiento de forma asíncrona
        asyncio.run(handle_update(update_json))
        return 'OK', 200
    return 'JARVIS está en línea y esperando webhooks.', 200

# Punto de entrada para Vercel
def handler(request_obj):
    return app(request_obj)
