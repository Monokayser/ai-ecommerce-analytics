"""Provider-independent five-interaction conversation memory."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(slots=True)
class Interaction:
    """Compact, explainable conversational record."""

    question: str
    interpreted_question: str
    query: str
    filters: dict[str, Any]
    result_summary: str
    answer: str


class ConversationMemory:
    """Bound conversation history to the last five interactions."""

    def __init__(self, records: Iterable[dict[str, Any]] | None = None) -> None:
        self._records: deque[Interaction] = deque(maxlen=5)
        for record in records or []:
            self._records.append(Interaction(**record))

    def append(self, interaction: Interaction) -> None:
        self._records.append(interaction)

    def clear(self) -> None:
        self._records.clear()

    def as_list(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self._records]

    def prompt_context(self) -> str:
        return "\n".join(f"Q: {item.question}\nQuery: {item.query}\nAnswer: {item.answer[:500]}" for item in self._records)
