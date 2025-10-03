from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class ChatbotAdapter(ABC):
    @abstractmethod
    def reply(self, message: str, *, context: Mapping[str, Any] | None = None) -> str:
        raise NotImplementedError
