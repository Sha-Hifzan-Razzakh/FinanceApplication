"""An LLMPort fake that answers each structured() call from a prepared queue."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel


class ScriptedLLM:
    """LLMPort fake: replies are models or exceptions, consumed in order."""

    def __init__(self, *replies: BaseModel | Exception, version: str = "v1") -> None:
        self._replies = list(replies)
        self._version = version
        self.calls: list[tuple[str, dict[str, Any], type[BaseModel]]] = []

    async def structured[T: BaseModel](
        self, prompt_id: str, vars: Mapping[str, Any], schema: type[T]
    ) -> T:
        self.calls.append((prompt_id, dict(vars), schema))
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        assert isinstance(reply, schema)
        return reply

    def prompt_version(self, prompt_id: str) -> str:
        return self._version
