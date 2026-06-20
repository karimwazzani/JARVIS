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

    def handle(self, history: list[dict[str, str]], chat_id: str) -> tuple[str, list[dict[str, str]]]:
        context = self.memory_keeper.build_context(history=history, chat_id=chat_id)
        selected_agent = self._select_agent(context.user_message)
        decision = self.guardian.evaluate(selected_agent.agent_id, context.user_message)

        result = selected_agent.run(context)
        response = self._compose_response(result, decision.rationale if decision.requires_confirmation else "")
        updated_history = history + [{"role": "assistant", "content": response}]
        return response, updated_history

    def _select_agent(self, user_message: str):
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
        if not guardian_note:
            return result.response
        return f"{result.response}\n\n[Guardian] {guardian_note}"


_runtime = JarvisOrchestrator()


def run_jarvis_turn(history: list[dict[str, str]], chat_id: str) -> tuple[str, list[dict[str, str]]]:
    return _runtime.handle(history=history, chat_id=chat_id)
