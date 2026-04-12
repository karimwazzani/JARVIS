import logging
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
    application.run_polling()

if __name__ == '__main__':
    main()
