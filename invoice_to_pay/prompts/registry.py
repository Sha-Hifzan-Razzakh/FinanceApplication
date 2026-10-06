"""Versioned prompts as data: prompts/<id>/v<N>.md, one folder per prompt id (CS-028)."""

import re
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

_PACKAGED = Path(__file__).parent
_VERSION = re.compile(r"v(\d+)\.md")
_SECTION = re.compile(r"^## (system|human)[ \t]*\n", re.MULTILINE)


class PromptRegistry:
    """Loads the newest version of a prompt; the id and version go to the ledger."""

    def __init__(self, root: Path = _PACKAGED) -> None:
        self._root = root

    def _latest(self, prompt_id: str) -> Path:
        folder = self._root / prompt_id
        if not prompt_id or prompt_id.startswith(".") or "/" in prompt_id or "\\" in prompt_id:
            raise KeyError(f"unknown prompt id: {prompt_id!r}")
        if not folder.is_dir():
            raise KeyError(f"unknown prompt id: {prompt_id!r}")
        versions = [
            (int(m.group(1)), path)
            for path in folder.glob("v*.md")
            if (m := _VERSION.fullmatch(path.name))
        ]
        if not versions:
            raise KeyError(f"prompt {prompt_id!r} has no versions")
        return max(versions)[1]

    def version_of(self, prompt_id: str) -> str:
        """The version label ('v1', 'v2', ...) that get() returns for this prompt."""
        return self._latest(prompt_id).stem

    def get(self, prompt_id: str) -> ChatPromptTemplate:
        """The newest version of the prompt as a chat template."""
        text = self._latest(prompt_id).read_text(encoding="utf-8")
        parts = _SECTION.split(text)  # ['', role, body, role, body, ...]
        messages = [
            (role, body.strip()) for role, body in zip(parts[1::2], parts[2::2], strict=True)
        ]
        if not any(role == "human" for role, _ in messages):
            raise ValueError(f"prompt {prompt_id!r} needs a '## human' section")
        return ChatPromptTemplate.from_messages(messages)
