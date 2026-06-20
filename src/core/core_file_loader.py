from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


CORE_FILES_DIR = Path(__file__).resolve().parent.parent / "core_files"


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    manifest_path = CORE_FILES_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"agents": []}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_agent_core(agent_id: str) -> dict[str, str]:
    agent_dir = CORE_FILES_DIR / agent_id
    return {
        "identity": _read_text(agent_dir / "identity.md"),
        "rules": _read_text(agent_dir / "rules.md"),
        "memory": _read_text(agent_dir / "memory.md"),
    }

