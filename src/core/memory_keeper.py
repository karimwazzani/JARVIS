from __future__ import annotations

from src.core.types import AgentContext, GuardianDecision
from src.database import (
    add_agent_memory,
    fetch_conversation_history,
    fetch_runtime_snapshot,
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
        snapshot = fetch_runtime_snapshot(chat_id)
        prefs = snapshot["preferences"]
        memories = snapshot["memories"]
        tasks = snapshot["tasks"]
        runs = snapshot["runs"]
        recent_messages = snapshot["messages"]

        pref_text = ", ".join(f"{p['clave']}={p['valor']}" for p in prefs) if prefs else "sin preferencias guardadas"
        memory_text = " | ".join(f"{m['categoria']}: {m['dato']}" for m in memories) if memories else "sin memoria de largo plazo"
        agent_memory_text = (
            " | ".join(m["dato"] for m in memories if str(m.get("categoria", "")).startswith("agent::"))
            if memories
            else "sin memoria agéntica"
        )
        task_text = (
            " | ".join(f"{t['titulo']} ({t['estado']})" for t in tasks)
            if tasks
            else "sin tareas pendientes"
        )
        run_text = (
            " | ".join(r["evento"][:120] for r in runs)
            if runs
            else "sin ejecuciones recientes"
        )
        msg_text = (
            " | ".join(f"{m['rol']}:{m['contenido'][:80]}" for m in reversed(recent_messages))
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
