import os

from crewai.memory.storage.lancedb_storage import LanceDBStorage
from crewai.memory.unified_memory import Memory

from agency.core.llm import get_llm

_STORAGE_DIR = os.path.join(os.path.dirname(__file__), ".memory_store")

# One flat, shared store — no per-department root_scope. CrewAI's
# auto-attached RecallMemoryTool calls memory.recall() with no scope
# override, so it's hard-limited to whatever root_scope this instance was
# built with. Nesting departments under their own scopes would silently wall
# them off from each other, defeating the point of sharing learnings across
# departments.
shared_memory = Memory(
    llm=get_llm("haiku"),
    storage=LanceDBStorage(path=_STORAGE_DIR),
    embedder={"provider": "sentence-transformer", "config": {"model_name": "all-MiniLM-L6-v2"}},
    root_scope=None,
)


def remember(summary: str, *, scope: str, categories: list[str], importance: float = 0.5) -> None:
    """Deterministic save after a skill completes.

    Passing scope/categories/importance explicitly skips memory's own
    LLM-analysis pass (embedding-only cost) — see crewai/memory/encoding_flow.py.
    Agents may *additionally* save mid-task via their own auto-attached
    RememberTool if they choose to; this call guarantees a record exists
    regardless of whether they did.
    """
    shared_memory.remember(summary, scope=scope, categories=categories, importance=importance)


def recall_context(query: str, *, limit: int = 5) -> str:
    """Deterministic pre-task recall, formatted for prepending to a Task description.

    Uses depth="shallow" to avoid the cost of the smarter multi-query
    RecallFlow — this is just quick context injection, not a research step.
    Returns "" when nothing relevant is found so callers can prepend it
    unconditionally without an extra empty-section check.
    """
    matches = shared_memory.recall(query, limit=limit, depth="shallow")
    if not matches:
        return ""
    lines = "\n".join(f"- {m.record.content}" for m in matches)
    return f"RELEVANT PAST LEARNINGS (from other agents/departments):\n{lines}\n"
