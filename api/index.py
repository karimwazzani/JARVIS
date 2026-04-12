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

# Inicializar base de datos y bot
try:
    init_db()
    application = create_app()
except Exception as e:
    print(f"Error al iniciar app: {e}")
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
        asyncio.run(handle_update(update_json))
        return 'OK', 200
    return '<h1>JARVIS está en línea</h1><p>Memoria y Cerebro activos en la nube.</p>', 200
