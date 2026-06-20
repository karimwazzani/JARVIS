from __future__ import annotations

from src.core.types import GuardianDecision


class Guardian:
    """Human-in-the-loop guardrails for sensitive actions."""

    _sensitive_keywords = {
        "deploy",
        "production",
        "prod",
        "publica",
        "publicar",
        "postea",
        "postear",
        "elimina",
        "borrar",
        "borra",
        "transferi",
        "paga",
        "pagar",
        "credencial",
        "password",
        "token",
        "apikey",
        "api key",
    }

    def evaluate(self, route: str, user_message: str) -> GuardianDecision:
        text = user_message.lower()
        matched = sorted(keyword for keyword in self._sensitive_keywords if keyword in text)
        if not matched:
            return GuardianDecision(
                approved=True,
                requires_confirmation=False,
                rationale="No se detectaron acciones sensibles.",
            )

        return GuardianDecision(
            approved=True,
            requires_confirmation=True,
            rationale=(
                "Se detecto una accion sensible para la ruta "
                f"'{route}': {', '.join(matched)}. Requiere confirmacion humana antes de ejecutar cambios irreversibles."
            ),
        )

