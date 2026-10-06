"""CS-028 PromptRegistry: versioned prompts as data."""

from pathlib import Path

import pytest
from langchain_core.prompts import ChatPromptTemplate

from invoice_to_pay.prompts.registry import PromptRegistry


def _write(root: Path, prompt_id: str, version: str, body: str) -> None:
    folder = root / prompt_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{version}.md").write_text(body)


def test_cs028_get_returns_a_chat_prompt_with_system_and_human_messages(tmp_path: Path) -> None:
    _write(tmp_path, "greet", "v1", "## system\nBe brief.\n\n## human\nHello {name}\n")
    prompt = PromptRegistry(tmp_path).get("greet")
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.format_messages(name="Ada")
    assert [m.type for m in messages] == ["system", "human"]
    assert messages[0].content == "Be brief."
    assert messages[1].content == "Hello Ada"


def test_cs028_latest_version_wins_and_is_reported(tmp_path: Path) -> None:
    _write(tmp_path, "greet", "v1", "## human\nold {name}\n")
    _write(tmp_path, "greet", "v2", "## human\nnew {name}\n")
    _write(tmp_path, "greet", "v10", "## human\nnewest {name}\n")
    registry = PromptRegistry(tmp_path)
    assert registry.version_of("greet") == "v10"
    assert registry.get("greet").format_messages(name="x")[0].content == "newest x"


def test_cs028_unknown_prompt_id_is_a_key_error(tmp_path: Path) -> None:
    with pytest.raises(KeyError, match="nope"):
        PromptRegistry(tmp_path).get("nope")


@pytest.mark.parametrize("bad", ["../escape", "a/b", "", ".."])
def test_cs028_prompt_ids_cannot_leave_the_prompt_folder(tmp_path: Path, bad: str) -> None:
    with pytest.raises(KeyError):
        PromptRegistry(tmp_path).get(bad)


def test_cs028_file_without_a_human_section_is_refused(tmp_path: Path) -> None:
    _write(tmp_path, "broken", "v1", "## system\nOnly a system message\n")
    with pytest.raises(ValueError, match="human"):
        PromptRegistry(tmp_path).get("broken")


def test_cs028_packaged_extraction_prompts_exist_with_their_variables() -> None:
    registry = PromptRegistry()
    first = registry.get("extract_invoice")
    retry = registry.get("extract_invoice_retry")
    assert set(first.input_variables) == {"document"}
    assert set(retry.input_variables) == {"document", "errors"}
    assert registry.version_of("extract_invoice") == "v1"


def test_cs028_extraction_prompts_treat_the_document_as_data() -> None:
    text = PromptRegistry().get("extract_invoice").format_messages(document="INVOICE 1")
    system = str(text[0].content).lower()
    assert "data" in system and "instruction" in system
    assert "iban" in system  # printed bank details are read, never acted on


@pytest.mark.parametrize("prompt_id", ["extract_invoice", "extract_invoice_retry"])
def test_cs028_extraction_prompts_ask_for_the_structured_reply_not_prose(prompt_id: str) -> None:
    registry = PromptRegistry()
    variables = dict.fromkeys(registry.get(prompt_id).input_variables, "x")
    system = str(registry.get(prompt_id).format_messages(**variables)[0].content).lower()
    assert "tool" in system and "prose" in system
