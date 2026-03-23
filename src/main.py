import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_handlers import (
    start_handler, help_handler, text_handler,
    gasto_handler, ingreso_handler, resumen_handler, check_reminders, check_sensores
)
from database import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    init_db()
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "tu_token_aqui_obtenido_de_botfather":
        print("ERROR: Token de Telegram inválido.")
        return

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('ayuda', help_handler))
    
    application.add_handler(CommandHandler('gasto', gasto_handler))
    application.add_handler(CommandHandler('ingreso', ingreso_handler))
    application.add_handler(CommandHandler('resumen', resumen_handler))
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    # Tarea en segundo plano para verificar recordatorios cada 30 segundos
    application.job_queue.run_repeating(check_reminders, interval=30, first=5)
    # Tarea para monitorear los sensores IoT casi en tiempo real (cada 5 seg)
    application.job_queue.run_repeating(check_sensores, interval=5, first=2)

    print("JARVIS iniciado exitosamente. Módulo de Recordatorios e IoT ACTIVOS.")
    application.run_polling()

if __name__ == '__main__':
    main()
