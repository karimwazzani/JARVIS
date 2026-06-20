from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentContext:
    chat_id: str
    history: list[dict[str, str]]
    user_message: str
    memory_snapshot: str = ""
    core_identity: str = ""
    core_rules: str = ""
    core_memory: str = ""


@dataclass(slots=True)
class AgentResult:
    route: str
    response: str
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GuardianDecision:
    approved: bool
    requires_confirmation: bool
    rationale: str

