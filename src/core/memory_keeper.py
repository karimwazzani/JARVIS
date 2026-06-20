from __future__ import annotations

from sqlalchemy import desc

from src.core.types import AgentContext
from src.database import Memoria, PreferenciaUsuario, SessionLocal


class MemoryKeeper:
    """Builds a compact memory snapshot for agent routing and response quality."""

    def build_context(self, history: list[dict[str, str]], chat_id: str) -> AgentContext:
        user_message = history[-1]["content"] if history else ""
        memory_snapshot = self._load_snapshot(chat_id)
        return AgentContext(
            chat_id=chat_id,
            history=history,
            user_message=user_message,
            memory_snapshot=memory_snapshot,
        )

    def _load_snapshot(self, chat_id: str) -> str:
        db = SessionLocal()
        try:
            prefs = (
                db.query(PreferenciaUsuario)
                .filter(PreferenciaUsuario.chat_id == str(chat_id))
                .order_by(PreferenciaUsuario.clave.asc())
                .all()
            )
            memories = (
                db.query(Memoria)
                .filter(Memoria.chat_id == str(chat_id))
                .order_by(desc(Memoria.fecha))
                .limit(8)
                .all()
            )
        finally:
            db.close()

        pref_text = ", ".join(f"{p.clave}={p.valor}" for p in prefs) if prefs else "sin preferencias guardadas"
        memory_text = " | ".join(f"{m.categoria}: {m.dato}" for m in memories) if memories else "sin memoria persistente"
        return f"Preferencias: {pref_text}. Memoria reciente: {memory_text}."

