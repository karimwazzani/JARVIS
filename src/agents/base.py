from __future__ import annotations

from dataclasses import dataclass, field

from src.core.core_file_loader import load_agent_core
from src.core.legacy_bridge import run_with_legacy_engine
from src.core.types import AgentContext, AgentResult


@dataclass(slots=True)
class BaseAgent:
    agent_id: str
    label: str
    description: str
    keywords: tuple[str, ...] = field(default_factory=tuple)

    def score(self, user_message: str) -> int:
        text = user_message.lower()
        return sum(1 for keyword in self.keywords if keyword in text)

    def build_instruction(self, context: AgentContext) -> str:
        core = load_agent_core(self.agent_id)
        context.core_identity = core["identity"]
        context.core_rules = core["rules"]
        context.core_memory = core["memory"]
        return "\n\n".join(
            part for part in [core["identity"], core["rules"], core["memory"]] if part
        )

    def run(self, context: AgentContext) -> AgentResult:
        instruction = self.build_instruction(context)
        response = run_with_legacy_engine(
            history=context.history,
            chat_id=context.chat_id,
            agent_name=self.label,
            instruction=instruction,
            memory_snapshot=context.memory_snapshot,
        )
        return AgentResult(route=self.agent_id, response=response)

