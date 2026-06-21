from __future__ import annotations

from src.core.types import GuardianDecision


class Guardian:
    """Human-in-the-loop guardrails for sensitive actions."""

    _confirmation_required_keywords = {
        "deploy",
        "production",
        "prod",
        "publica",
        "publicar",
        "postea",
        "postear",
        "elimina",
        "eliminar",
        "borrar",
        "borra",
        "transferi",
        "transferir",
        "paga",
        "pagar",
    }
    _confirmation_phrases = {
        "confirmo",
        "confirmá",
        "confirmar",
        "aprobado",
        "aproba",
        "dale",
        "hacelo",
        "ejecutalo",
        "si, ejecuta",
        "si ejecuta",
    }

    def evaluate(self, route: str, user_message: str) -> GuardianDecision:
        text = user_message.lower()
        matched = sorted(
            keyword for keyword in self._confirmation_required_keywords if keyword in text
        )
        if not matched:
            return GuardianDecision(
                approved=True,
                requires_confirmation=False,
                rationale="No se detectaron acciones sensibles.",
            )

        if any(phrase in text for phrase in self._confirmation_phrases):
            return GuardianDecision(
                approved=True,
                requires_confirmation=True,
                rationale=(
                    f"Accion sensible detectada para la ruta '{route}', "
                    "pero el mensaje ya trae confirmacion explicita."
                ),
            )

        return GuardianDecision(
            approved=False,
            requires_confirmation=True,
            rationale=(
                "Detecte una accion sensible en la ruta "
                f"'{route}' ({', '.join(matched)}). "
                "Antes de ejecutar cambios irreversibles necesito una confirmacion explicita."
            ),
        )
