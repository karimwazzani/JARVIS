
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres.zreywbdlhwlrlvinhlwk:Jarvis270502%21%21%2B@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE tareas ADD COLUMN fecha_limite TIMESTAMP;"))
        conn.commit()
        print("Columna 'fecha_limite' añadida exitosamente.")
    except Exception as e:
        print(f"Error al añadir columna (posiblemente ya existe): {e}")
