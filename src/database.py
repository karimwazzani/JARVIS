import os
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_now():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)

# Prioridad de variables de entorno (Vercel usa POSTGRES_URL, otros usan DATABASE_URL)
# Si es SQLite, usamos /tmp/ para evitar errores de solo lectura en Vercel
DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or "sqlite:////tmp/jarvis_local.db"

# Corrección de protocolo y SSL para SQLAlchemy (Postgres en la nube suele usar postgres://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Forzar SSL para Supabase/Neon si no está presente
if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{sep}sslmode=require"

# Timeout de conexión para evitar bloqueos en Vercel
engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 5} if "postgresql" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True) # Ex: "gasto" o "ingreso"
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=get_now)

class Recordatorio(Base):
    __tablename__ = "recordatorios"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String) # Telegram Chat ID
    mensaje = Column(String)
    fecha_aviso = Column(DateTime)
    enviado = Column(Boolean, default=False)

class Memoria(Base):
    """Guarda contexto persistente, hechos, rutinas o cualquier dato importante categorizado."""
    __tablename__ = "memorias"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String)
    dato = Column(String)
    fecha_registro = Column(DateTime, default=get_now)

class SensorAlert(Base):
    __tablename__ = "sensor_alertas"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String) # Ej: 'PIR_Sala'
    mensaje = Column(String)   # Ej: 'Movimiento Detectado'
    fecha = Column(DateTime, default=get_now)
    leido = Column(Boolean, default=False)

class Tarea(Base):
    """Guarda tareas específicas y seguimiento de actividades."""
    __tablename__ = "tareas"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    titulo = Column(String)
    descripcion = Column(String, nullable=True)
    estado = Column(String, default="pendiente") # "pendiente", "en_progreso", "completada"
    fecha_limite = Column(DateTime, nullable=True) # Nueva columna para agendar
    fecha_creacion = Column(DateTime, default=get_now)
    fecha_completada = Column(DateTime, nullable=True)

class PreferenciaUsuario(Base):
    """Guarda configuración personalizada de alertas, prioridades y modos."""
    __tablename__ = "preferencias_usuario"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    clave = Column(String, index=True) # Ej: "modo_noche_inicio"
    valor = Column(String)             # Ej: "22:00"
    fecha_actualizacion = Column(DateTime, default=get_now, onupdate=get_now)

class HabitoYPatron(Base):
    """Registro de comportamientos detectados por JARVIS."""
    __tablename__ = "habitos_y_patrones"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    descripcion = Column(String) # Ej: "Suele pedir resumen financiero los viernes"
    confianza = Column(Float, default=1.0) # Nivel de certeza de JARVIS
    fecha_deteccion = Column(DateTime, default=get_now)

class LogEvento(Base):
    """Telemetría para análisis predictivo (qué hace el usuario y cuándo)."""
    __tablename__ = "log_eventos"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    evento = Column(String)
    fecha = Column(DateTime, default=get_now)

class PropuestaAutomatizacion(Base):
    """Reglas propuestas por el LLM en base a los LogEventos."""
    __tablename__ = "propuestas_automatizacion"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    descripcion = Column(String)
    accion_tecnica = Column(String, nullable=True) 
    estado = Column(String, default="pendiente") # "pendiente", "aprobada", "rechazada"
    fecha_creacion = Column(DateTime, default=get_now)

def init_db():
    # Crea las tablas si no existen
    print("DEBUG: Iniciando creación de tablas...", flush=True)
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Tablas creadas/verificadas.", flush=True)
