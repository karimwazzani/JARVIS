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
    delivery_contract: str = ""
    operating_focus: str = ""

    def score(self, user_message: str) -> int:
        text = user_message.lower()
        return sum(1 for keyword in self.keywords if keyword in text)

    def build_instruction(self, context: AgentContext) -> str:
        core = load_agent_core(self.agent_id)
        context.core_identity = core["identity"]
        context.core_rules = core["rules"]
        context.core_memory = core["memory"]

        contract = self.delivery_contract.strip()
        focus = self.operating_focus.strip()
        contract_block = f"FOCO OPERATIVO:\n{focus}\n\nFORMATO DE ENTREGA OBLIGATORIO:\n{contract}" if (focus or contract) else ""

        return "\n\n".join(
            part for part in [core["identity"], core["rules"], core["memory"], contract_block] if part
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


@dataclass(slots=True)
class SpecialistAgent(BaseAgent):
    capability_summary: str = ""

    def build_instruction(self, context: AgentContext) -> str:
        base_instruction = super().build_instruction(context)
        capability_block = (
            f"CAPACIDAD ESPECIAL:\n{self.capability_summary}\n"
            "No respondas de forma genérica. Entrega un resultado accionable, concreto y con decisión."
            if self.capability_summary
            else ""
        )
        return "\n\n".join(part for part in [base_instruction, capability_block] if part)
