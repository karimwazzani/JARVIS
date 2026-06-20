from __future__ import annotations

from src.ai_agent import get_ai_response


def run_with_legacy_engine(
    history: list[dict[str, str]],
    chat_id: str,
    agent_name: str,
    instruction: str,
    memory_snapshot: str = "",
) -> str:
    if history:
        base_history = history[:-1]
        user_message = history[-1]["content"]
    else:
        base_history = []
        user_message = ""

    directive = (
        f"[RUTA_ACTIVA:{agent_name}]\n"
        f"[MEMORIA:{memory_snapshot or 'sin memoria adicional'}]\n"
        f"{instruction}\n\n"
        f"Solicitud original del usuario:\n{user_message}"
    )
    temp_history = base_history + [{"role": "user", "content": directive}]
    response, _ = get_ai_response(temp_history, chat_id)
    return response

