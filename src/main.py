import logging
import os
from dotenv import load_dotenv
from src.database import init_db
from src.app_factory import create_app, setup_jobs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    load_dotenv()
    init_db()
    
    application = create_app()
    setup_jobs(application)

    print("JARVIS iniciado exitosamente (Modo Polling).")
    
    import time
    from telegram.error import Conflict
    while True:
        try:
            application.run_polling()
            break # Si sale limpiamente, rompemos el bucle
        except Conflict:
            print("Conflicto 409: El JARVIS anterior todavía no fue apagado por Railway. Esperando 10 segundos...")
            time.sleep(10)
        except Exception as e:
            print(f"Error inesperado en polling: {e}. Reintentando...")
            time.sleep(10)

if __name__ == '__main__':
    main()
