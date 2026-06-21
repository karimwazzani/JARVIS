import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def get_now():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)


DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or "sqlite:////tmp/jarvis_local.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{sep}sslmode=require"

engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 5} if "postgresql" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True)
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=get_now)


class Recordatorio(Base):
    __tablename__ = "recordatorios"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String)
    mensaje = Column(String)
    fecha_aviso = Column(DateTime)
    enviado = Column(Boolean, default=False)


class Memoria(Base):
    __tablename__ = "memorias"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String)
    dato = Column(String)
    fecha_registro = Column(DateTime, default=get_now)


class SensorAlert(Base):
    __tablename__ = "sensor_alertas"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String)
    mensaje = Column(String)
    fecha = Column(DateTime, default=get_now)
    leido = Column(Boolean, default=False)


class Tarea(Base):
    __tablename__ = "tareas"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    titulo = Column(String)
    descripcion = Column(String, nullable=True)
    estado = Column(String, default="pendiente")
    fecha_limite = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=get_now)
    fecha_completada = Column(DateTime, nullable=True)


class PreferenciaUsuario(Base):
    __tablename__ = "preferencias_usuario"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    clave = Column(String, index=True)
    valor = Column(String)
    fecha_actualizacion = Column(DateTime, default=get_now, onupdate=get_now)


class HabitoYPatron(Base):
    __tablename__ = "habitos_y_patrones"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    patron = Column(String)
    confianza = Column(Float)
    fecha_deteccion = Column(DateTime, default=get_now)


class EventoCalendario(Base):
    __tablename__ = "eventos_calendario"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    titulo = Column(String)
    fecha_hora = Column(DateTime)
    ubicacion = Column(String, nullable=True)
    last_sync = Column(DateTime, default=get_now)
    fecha_deteccion = Column(DateTime, default=get_now)


class LogEvento(Base):
    __tablename__ = "log_eventos"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    evento = Column(String)
    fecha = Column(DateTime, default=get_now)


class Conversacion(Base):
    __tablename__ = "conversaciones"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    rol = Column(String)
    contenido = Column(String)
    fecha = Column(DateTime, default=get_now)


class PropuestaAutomatizacion(Base):
    __tablename__ = "propuestas_automatizacion"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    descripcion = Column(String)
    accion_tecnica = Column(String, nullable=True)
    estado = Column(String, default="pendiente")
    fecha_creacion = Column(DateTime, default=get_now)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    route = Column(String, index=True)
    user_message = Column(Text)
    response_preview = Column(Text)
    status = Column(String, default="completed")
    requires_confirmation = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_now)


class AgentMemoryEntry(Base):
    __tablename__ = "agent_memory_entries"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    agent_id = Column(String, index=True)
    category = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=get_now)


class AgentTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    agent_id = Column(String, index=True)
    title = Column(String)
    summary = Column(Text, nullable=True)
    status = Column(String, default="open")
    priority = Column(String, default="normal")
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_now)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now)


def init_db():
    print("DEBUG: Iniciando creacion de tablas...", flush=True)
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Tablas creadas/verificadas.", flush=True)


def _supabase_enabled() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _supabase_headers() -> dict[str, str]:
    token = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return {
        "apikey": token,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _supabase_rest_request(method: str, table: str, *, params: dict | None = None, payload: object | None = None):
    response = requests.request(
        method,
        f"{os.getenv('SUPABASE_URL', '').rstrip('/')}/rest/v1/{table}",
        headers=_supabase_headers(),
        params=params,
        json=payload,
        timeout=12,
    )
    response.raise_for_status()
    if not response.content:
        return None
    return response.json()


def _iso_now() -> str:
    return get_now().isoformat()


def store_conversation_message(chat_id: str, role: str, content: str) -> None:
    if _supabase_enabled():
        _supabase_rest_request(
            "POST",
            "conversaciones",
            payload={"chat_id": str(chat_id), "rol": role, "contenido": content},
        )
        return

    db = SessionLocal()
    try:
        db.add(Conversacion(chat_id=str(chat_id), rol=role, contenido=content))
        db.commit()
    finally:
        db.close()


def fetch_conversation_history(chat_id: str, limit: int = 20) -> list[dict[str, str]]:
    if _supabase_enabled():
        rows = _supabase_rest_request(
            "GET",
            "conversaciones",
            params={
                "chat_id": f"eq.{chat_id}",
                "select": "rol,contenido,id",
                "order": "id.desc",
                "limit": str(limit),
            },
        ) or []
        rows.reverse()
        return [{"role": row["rol"], "content": row["contenido"]} for row in rows]

    db = SessionLocal()
    try:
        rows = (
            db.query(Conversacion)
            .filter(Conversacion.chat_id == str(chat_id))
            .order_by(Conversacion.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()

    rows.reverse()
    return [{"role": row.rol, "content": row.contenido} for row in rows]


def record_agent_run(
    chat_id: str,
    route: str,
    user_message: str,
    response_preview: str,
    *,
    status: str = "completed",
    requires_confirmation: bool = False,
    metadata: dict | None = None,
) -> None:
    if _supabase_enabled():
        payload = {
            "route": route,
            "status": status,
            "requires_confirmation": requires_confirmation,
            "user_message": user_message[:240],
            "response_preview": response_preview[:280],
            "metadata": metadata or {},
        }
        _supabase_rest_request(
            "POST",
            "log_eventos",
            payload={
                "chat_id": str(chat_id),
                "evento": f"[AGENT_RUN] {json.dumps(payload, ensure_ascii=False)}",
                "fecha": _iso_now(),
            },
        )
        return

    db = SessionLocal()
    try:
        db.add(
            AgentRun(
                chat_id=str(chat_id),
                route=route,
                user_message=user_message,
                response_preview=response_preview[:1200],
                status=status,
                requires_confirmation=requires_confirmation,
                metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            )
        )
        db.commit()
    finally:
        db.close()


def add_agent_memory(chat_id: str, agent_id: str, category: str, content: str) -> None:
    if _supabase_enabled():
        _supabase_rest_request(
            "POST",
            "memorias",
            payload={
                "categoria": f"agent::{agent_id}::{category}",
                "dato": f"[chat:{chat_id}] {content[:1800]}",
                "fecha_registro": _iso_now(),
            },
        )
        return

    db = SessionLocal()
    try:
        db.add(
            AgentMemoryEntry(
                chat_id=str(chat_id),
                agent_id=agent_id,
                category=category,
                content=content[:2000],
            )
        )
        db.commit()
    finally:
        db.close()


def fetch_runtime_snapshot(chat_id: str) -> dict[str, list[dict]]:
    if _supabase_enabled():
        return {
            "preferences": _supabase_rest_request(
                "GET",
                "preferencias_usuario",
                params={
                    "or": f"(chat_id.eq.{chat_id},chat_id.eq.general)",
                    "select": "chat_id,clave,valor",
                    "order": "clave.asc",
                },
            ) or [],
            "memories": _supabase_rest_request(
                "GET",
                "memorias",
                params={
                    "or": f"(dato.ilike.*[chat:{chat_id}]*,categoria.not.like.agent::*)",
                    "select": "categoria,dato,fecha_registro",
                    "order": "fecha_registro.desc",
                    "limit": "8",
                },
            ) or [],
            "tasks": _supabase_rest_request(
                "GET",
                "tareas",
                params={
                    "chat_id": f"eq.{chat_id}",
                    "estado": "eq.pendiente",
                    "select": "titulo,estado,fecha_creacion",
                    "order": "fecha_creacion.desc",
                    "limit": "5",
                },
            ) or [],
            "runs": _supabase_rest_request(
                "GET",
                "log_eventos",
                params={
                    "chat_id": f"eq.{chat_id}",
                    "evento": "like.[AGENT_RUN]%",
                    "select": "evento,fecha",
                    "order": "fecha.desc",
                    "limit": "5",
                },
            ) or [],
            "messages": _supabase_rest_request(
                "GET",
                "conversaciones",
                params={
                    "chat_id": f"eq.{chat_id}",
                    "select": "rol,contenido,id",
                    "order": "id.desc",
                    "limit": "6",
                },
            ) or [],
        }

    db = SessionLocal()
    try:
        preferences = (
            db.query(PreferenciaUsuario)
            .filter(PreferenciaUsuario.chat_id.in_([str(chat_id), "general"]))
            .order_by(PreferenciaUsuario.clave.asc())
            .all()
        )
        memories = db.query(Memoria).order_by(Memoria.fecha_registro.desc()).limit(8).all()
        tasks = (
            db.query(Tarea)
            .filter(Tarea.chat_id == str(chat_id), Tarea.estado == "pendiente")
            .order_by(Tarea.fecha_creacion.desc())
            .limit(5)
            .all()
        )
        runs = (
            db.query(AgentRun)
            .filter(AgentRun.chat_id == str(chat_id))
            .order_by(AgentRun.created_at.desc())
            .limit(5)
            .all()
        )
        messages = (
            db.query(Conversacion)
            .filter(Conversacion.chat_id == str(chat_id))
            .order_by(Conversacion.id.desc())
            .limit(6)
            .all()
        )
    finally:
        db.close()

    return {
        "preferences": [{"chat_id": p.chat_id, "clave": p.clave, "valor": p.valor} for p in preferences],
        "memories": [{"categoria": m.categoria, "dato": m.dato, "fecha_registro": m.fecha_registro.isoformat() if m.fecha_registro else ""} for m in memories],
        "tasks": [{"titulo": t.titulo, "estado": t.estado, "fecha_creacion": t.fecha_creacion.isoformat() if t.fecha_creacion else ""} for t in tasks],
        "runs": [{"evento": f"[AGENT_RUN] route={r.route} status={r.status}", "fecha": r.created_at.isoformat() if r.created_at else ""} for r in runs],
        "messages": [{"rol": m.rol, "contenido": m.contenido, "id": m.id} for m in messages],
    }


def create_finance_transaction(tipo: str, monto: float, descripcion: str) -> None:
    if _supabase_enabled():
        _supabase_rest_request(
            "POST",
            "transacciones",
            payload={
                "tipo": tipo,
                "monto": monto,
                "descripcion": descripcion,
                "fecha": _iso_now(),
            },
        )
        return

    db = SessionLocal()
    try:
        db.add(Transaccion(tipo=tipo, monto=monto, descripcion=descripcion))
        db.commit()
    finally:
        db.close()


def fetch_finance_summary() -> dict[str, float]:
    if _supabase_enabled():
        rows = _supabase_rest_request("GET", "transacciones", params={"select": "tipo,monto"}) or []
        ingresos = sum(float(row["monto"]) for row in rows if row["tipo"] == "ingreso")
        gastos = sum(float(row["monto"]) for row in rows if row["tipo"] == "gasto")
        return {"ingresos": ingresos, "gastos": gastos, "saldo": ingresos - gastos}

    db = SessionLocal()
    try:
        rows = db.query(Transaccion).all()
    finally:
        db.close()
    ingresos = sum(row.monto for row in rows if row.tipo == "ingreso")
    gastos = sum(row.monto for row in rows if row.tipo == "gasto")
    return {"ingresos": ingresos, "gastos": gastos, "saldo": ingresos - gastos}
