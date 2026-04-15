import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.bot_handlers import (
    start_handler, help_handler, text_handler, voice_handler, location_handler,
    gasto_handler, ingreso_handler, resumen_handler, check_reminders, check_sensores,
    check_bienestar, reporte_semanal, analisis_predictivo, proactive_morning_briefing
)
from src.learning_engine import run_learning_engine

def create_app():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('ayuda', help_handler))
    
    application.add_handler(CommandHandler('gasto', gasto_handler))
    application.add_handler(CommandHandler('ingreso', ingreso_handler))
    application.add_handler(CommandHandler('resumen', resumen_handler))
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(MessageHandler(filters.LOCATION, location_handler))

    return application

def setup_jobs(application):
    from datetime import time
    from zoneinfo import ZoneInfo
    # Desactivamos el Job Queue en Vercel porque las lambdas mueren rápido
    # y esto solo retrasa el tiempo de respuesta
    if os.getenv("VERCEL"):
        print("Vercel detectado: Saltando Job Queue")
        return
        
    # Tarea en segundo plano para verificar recordatorios cada 30 segundos
    application.job_queue.run_repeating(check_reminders, interval=30, first=5)
    
    # Análisis de bienestar y actividad continua (cada hora)
    application.job_queue.run_repeating(check_bienestar, interval=3600, first=10)
    
    # Reportes estadísticos y envío predictivo (cada 24hs)
    application.job_queue.run_repeating(reporte_semanal, interval=86400, first=20)
    
    # Análisis predictivo a primera hora del día
    application.job_queue.run_repeating(analisis_predictivo, interval=86400, first=30)

    # Configuración de Machine Learning de Comportamientos
    application.job_queue.run_repeating(run_learning_engine, interval=86400, first=60)

    # Monitoreo IoT (solo para entornos persistentes)
    application.job_queue.run_repeating(check_sensores, interval=3, first=2)

    # Reporte Matutino Diario (08:30 AM Buenos Aires)
    application.job_queue.run_daily(
        proactive_morning_briefing, 
        time=time(8, 30, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    )
