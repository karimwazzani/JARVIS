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

# Inicialización diferida (Lazy Loading)
application = None

def get_app():
    global application
    if application is None:
        print("Cargando cerebro de JARVIS...")
        init_db()
        application = create_app()
    return application

async def handle_update(update_json):
    """Procesa la actualización recibida de Telegram."""
    app_instance = get_app()
    async with app_instance:
        update = Update.de_json(data=update_json, bot=app_instance.bot)
        await app_instance.process_update(update)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update_json = request.get_json(force=True)
        asyncio.run(handle_update(update_json))
        return 'OK', 200
    return '<h1>JARVIS está en línea</h1><p>Sistema en espera de mensajes.</p>', 200
