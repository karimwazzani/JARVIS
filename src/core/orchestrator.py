from __future__ import annotations

from src.agents.specialists import AGENTS, get_agent_registry
from src.core.guardian import Guardian
from src.core.memory_keeper import MemoryKeeper
from src.core.types import AgentResult


class JarvisOrchestrator:
    def __init__(self) -> None:
        self.memory_keeper = MemoryKeeper()
        self.guardian = Guardian()
        self.registry = get_agent_registry()

    def handle(
        self,
        history: list[dict[str, str]],
        chat_id: str,
        preferred_agent: str | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        context = self.memory_keeper.build_context(history=history, chat_id=chat_id)
        selected_agent = self._select_agent(context.user_message, preferred_agent)
        decision = self.guardian.evaluate(selected_agent.agent_id, context.user_message)

        if decision.requires_confirmation and not decision.approved:
            response = self._compose_confirmation_request(selected_agent.label, decision.rationale)
            updated_history = context.history + [{"role": "assistant", "content": response}]
            self.memory_keeper.capture_turn(
                chat_id=chat_id,
                route=selected_agent.agent_id,
                user_message=context.user_message,
                response=response,
                decision=decision,
                status="awaiting_confirmation",
            )
            return response, updated_history

        result = selected_agent.run(context)
        response = self._compose_response(result, decision.rationale if decision.requires_confirmation else "")
        updated_history = context.history + [{"role": "assistant", "content": response}]
        self.memory_keeper.capture_turn(
            chat_id=chat_id,
            route=result.route,
            user_message=context.user_message,
            response=response,
            decision=decision,
        )
        return response, updated_history

    def _select_agent(self, user_message: str, preferred_agent: str | None = None):
        if preferred_agent and preferred_agent in self.registry:
            return self.registry[preferred_agent]
        scored = sorted(
            ((agent.score(user_message), agent) for agent in AGENTS if agent.agent_id != "jarvis_orchestrator"),
            key=lambda item: item[0],
            reverse=True,
        )
        top_score, top_agent = scored[0]
        if top_score <= 0:
            return self.registry["jarvis_orchestrator"]
        return top_agent

    def _compose_response(self, result: AgentResult, guardian_note: str) -> str:
        agent_banner = f"[{result.route}]"
        if not guardian_note:
            return f"{agent_banner} {result.response}"
        return f"{agent_banner} {result.response}\n\n[Guardian] {guardian_note}"

    def _compose_confirmation_request(self, agent_label: str, rationale: str) -> str:
        return (
            f"[guardian] La solicitud quedo preparada para {agent_label}, "
            "pero la deje en espera.\n\n"
            f"{rationale}\n"
            "Si queres ejecutarla, mandame una confirmacion explicita en el mismo mensaje."
        )


_runtime = JarvisOrchestrator()


def run_jarvis_turn(
    history: list[dict[str, str]],
    chat_id: str,
    preferred_agent: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    return _runtime.handle(history=history, chat_id=chat_id, preferred_agent=preferred_agent)
