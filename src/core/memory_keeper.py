from __future__ import annotations

from sqlalchemy import desc, or_

from src.core.types import AgentContext, GuardianDecision
from src.database import (
    AgentMemoryEntry,
    AgentRun,
    Conversacion,
    Memoria,
    PreferenciaUsuario,
    SessionLocal,
    Tarea,
    add_agent_memory,
    fetch_conversation_history,
    record_agent_run,
)


class MemoryKeeper:
    """Builds a compact memory snapshot and records each routed turn."""

    def build_context(self, history: list[dict[str, str]], chat_id: str) -> AgentContext:
        hydrated_history = history[-20:] if history else fetch_conversation_history(chat_id, limit=20)
        user_message = hydrated_history[-1]["content"] if hydrated_history else ""
        memory_snapshot = self._load_snapshot(chat_id)
        return AgentContext(
            chat_id=chat_id,
            history=hydrated_history,
            user_message=user_message,
            memory_snapshot=memory_snapshot,
        )

    def capture_turn(
        self,
        *,
        chat_id: str,
        route: str,
        user_message: str,
        response: str,
        decision: GuardianDecision,
        status: str = "completed",
    ) -> None:
        metadata = {
            "route": route,
            "guardian_rationale": decision.rationale,
        }
        record_agent_run(
            chat_id=chat_id,
            route=route,
            user_message=user_message,
            response_preview=response,
            status=status,
            requires_confirmation=decision.requires_confirmation,
            metadata=metadata,
        )

        if response and status == "completed":
            memory_line = (
                f"Ultimo trabajo para {route}: usuario='{user_message[:220]}' | "
                f"salida='{response[:280]}'"
            )
            add_agent_memory(chat_id, route, "turn_summary", memory_line)

    def _load_snapshot(self, chat_id: str) -> str:
        db = SessionLocal()
        try:
            prefs = (
                db.query(PreferenciaUsuario)
                .filter(
                    or_(
                        PreferenciaUsuario.chat_id == str(chat_id),
                        PreferenciaUsuario.chat_id == "general",
                    )
                )
                .order_by(PreferenciaUsuario.clave.asc())
                .all()
            )
            memories = db.query(Memoria).order_by(desc(Memoria.fecha_registro)).limit(6).all()
            agent_memories = (
                db.query(AgentMemoryEntry)
                .filter(AgentMemoryEntry.chat_id == str(chat_id))
                .order_by(desc(AgentMemoryEntry.created_at))
                .limit(6)
                .all()
            )
            pending_tasks = (
                db.query(Tarea)
                .filter(Tarea.chat_id == str(chat_id), Tarea.estado == "pendiente")
                .order_by(Tarea.fecha_creacion.desc())
                .limit(5)
                .all()
            )
            recent_runs = (
                db.query(AgentRun)
                .filter(AgentRun.chat_id == str(chat_id))
                .order_by(desc(AgentRun.created_at))
                .limit(5)
                .all()
            )
            recent_messages = (
                db.query(Conversacion)
                .filter(Conversacion.chat_id == str(chat_id))
                .order_by(desc(Conversacion.id))
                .limit(6)
                .all()
            )
        finally:
            db.close()

        pref_text = ", ".join(f"{p.clave}={p.valor}" for p in prefs) if prefs else "sin preferencias guardadas"
        memory_text = " | ".join(f"{m.categoria}: {m.dato}" for m in memories) if memories else "sin memoria de largo plazo"
        agent_memory_text = (
            " | ".join(f"{m.agent_id}/{m.category}: {m.content}" for m in agent_memories)
            if agent_memories
            else "sin memoria agéntica"
        )
        task_text = (
            " | ".join(f"{t.titulo} ({t.estado})" for t in pending_tasks)
            if pending_tasks
            else "sin tareas pendientes"
        )
        run_text = (
            " | ".join(f"{r.route}:{r.status}" for r in recent_runs)
            if recent_runs
            else "sin ejecuciones recientes"
        )
        msg_text = (
            " | ".join(f"{m.rol}:{m.contenido[:80]}" for m in reversed(recent_messages))
            if recent_messages
            else "sin historial reciente"
        )

        return (
            f"Preferencias: {pref_text}. "
            f"Memoria larga: {memory_text}. "
            f"Memoria de agentes: {agent_memory_text}. "
            f"Tareas: {task_text}. "
            f"Rutas recientes: {run_text}. "
            f"Conversacion reciente: {msg_text}."
        )
