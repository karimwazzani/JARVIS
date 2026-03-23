from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# Base de datos local SQLite temporal para desarrollo
DATABASE_URL = "sqlite:///jarvis_local.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True) # Ex: "gasto" o "ingreso"
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=datetime.now)

class Recordatorio(Base):
    __tablename__ = "recordatorios"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String) # Telegram Chat ID
    mensaje = Column(String)
    fecha_aviso = Column(DateTime)
    enviado = Column(Boolean, default=False)

class SensorAlert(Base):
    __tablename__ = "sensor_alertas"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String) # Ej: 'PIR_Sala'
    mensaje = Column(String)   # Ej: 'Movimiento Detectado'
    fecha = Column(DateTime, default=datetime.now)
    leido = Column(Boolean, default=False)

def init_db():
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine)
