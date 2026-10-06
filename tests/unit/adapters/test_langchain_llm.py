"""CS-027 LangChainLLM: structured output per role, usage reporting, OpenTelemetry bridge."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel

from invoice_to_pay.adapters.langchain_llm import LangChainLLM, OTelCallbackHandler
from invoice_to_pay.application.ports import LLMPort, StructuredOutputError
from invoice_to_pay.prompts.registry import PromptRegistry


class Answer(BaseModel):
    text: str


class Seen:
    """What the fake model was asked."""

    def __init__(self) -> None:
        self.factory_calls: list[tuple[str, dict[str, Any]]] = []
        self.structured_kwargs: dict[str, Any] = {}
        self.schema: Any = None
        self.messages: Any = None
        self.config: RunnableConfig | None = None


def _factory(seen: Seen, reply: dict[str, Any]) -> Callable[..., Any]:
    class FakeChat:
        def with_structured_output(self, schema: Any, **kwargs: Any) -> Runnable[Any, Any]:
            seen.schema = schema
            seen.structured_kwargs = kwargs

            def call(messages: Any, config: RunnableConfig | None = None) -> dict[str, Any]:
                seen.messages = messages
                seen.config = config
                return reply

            return RunnableLambda(call)

    def factory(model: str, **kwargs: Any) -> FakeChat:
        seen.factory_calls.append((model, kwargs))
        return FakeChat()

    return factory


def _reply(
    parsed: Any = None, error: Exception | None = None, usage: bool = True
) -> dict[str, Any]:
    raw = AIMessage(
        content="",
        usage_metadata={"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
        if usage
        else None,
    )
    return {"raw": raw, "parsed": parsed, "parsing_error": error}


@pytest.fixture
def seen() -> Seen:
    return Seen()


async def test_cs027_structured_returns_the_schema_instance(seen: Seen) -> None:
    llm = LangChainLLM(
        "anthropic:claude-sonnet-5-5",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    result = await llm.structured("extract_invoice", {"document": "INV-1"}, Answer)
    assert result == Answer(text="ok")
    assert seen.schema is Answer
    assert seen.structured_kwargs["include_raw"] is True


async def test_cs027_prompt_is_filled_from_the_registry(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    await llm.structured("extract_invoice", {"document": "INV-1 total 100"}, Answer)
    flattened = " ".join(str(m.content) for m in seen.messages.to_messages())
    assert "INV-1 total 100" in flattened


async def test_cs027_model_is_built_from_the_provider_prefixed_id(seen: Seen) -> None:
    llm = LangChainLLM(
        "deepseek:deepseek-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    model, kwargs = seen.factory_calls[0]
    assert model == "deepseek-test"
    assert kwargs["model_provider"] == "deepseek"


@pytest.mark.parametrize("model_id", ["anthropic:claude-sonnet-5-5", "openai:gpt-test"])
async def test_cs027_output_method_is_the_provider_default_unless_set(
    seen: Seen, model_id: str
) -> None:
    llm = LangChainLLM(
        model_id, prompts=PromptRegistry(), model_factory=_factory(seen, _reply(Answer(text="a")))
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert "method" not in seen.structured_kwargs


async def test_cs027_output_method_can_be_pinned(seen: Seen) -> None:
    llm = LangChainLLM(
        "anthropic:claude-sonnet-5-5",
        prompts=PromptRegistry(),
        method="json_schema",
        model_factory=_factory(seen, _reply(Answer(text="a"))),
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert seen.structured_kwargs["method"] == "json_schema"


@pytest.mark.parametrize("model_id", ["mistral:large", "no-provider", "anthropic:"])
def test_cs027_unknown_providers_are_refused(model_id: str, seen: Seen) -> None:
    with pytest.raises(ValueError, match="provider:model"):
        LangChainLLM(model_id, prompts=PromptRegistry(), model_factory=_factory(seen, {}))


async def test_cs027_usage_goes_to_the_callback_with_the_prompt_id(seen: Seen) -> None:
    usage: list[tuple[str, int, int]] = []
    llm = LangChainLLM(
        "anthropic:claude-sonnet-5-5",
        prompts=PromptRegistry(),
        on_usage=lambda prompt_id, tokens_in, tokens_out: usage.append(
            (prompt_id, tokens_in, tokens_out)
        ),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert usage == [("extract_invoice", 120, 30)]


async def test_cs027_missing_usage_metadata_reports_nothing(seen: Seen) -> None:
    usage: list[tuple[str, int, int]] = []
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        on_usage=lambda *args: usage.append(args),
        model_factory=_factory(seen, _reply(Answer(text="ok"), usage=False)),
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert usage == []


async def test_cs027_usage_is_reported_even_when_the_reply_does_not_parse(seen: Seen) -> None:
    usage: list[tuple[str, int, int]] = []
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        on_usage=lambda *args: usage.append(args),
        model_factory=_factory(seen, _reply(None, ValueError("bad json"))),
    )
    with pytest.raises(StructuredOutputError, match="bad json"):
        await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert usage == [("extract_invoice", 120, 30)]


async def test_cs027_no_parsed_output_is_a_structured_output_error(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(None, None)),
    )
    with pytest.raises(StructuredOutputError):
        await llm.structured("extract_invoice", {"document": "x"}, Answer)


async def test_cs027_prompt_variables_must_match(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    with pytest.raises(KeyError):
        await llm.structured("extract_invoice", {"wrong": "x"}, Answer)


async def test_cs027_unknown_prompt_id_is_a_key_error(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    with pytest.raises(KeyError):
        await llm.structured("nope", {}, Answer)


def test_cs027_prompt_version_comes_from_the_registry(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test", prompts=PromptRegistry(), model_factory=_factory(seen, {})
    )
    assert llm.prompt_version("extract_invoice") == "v1"


def test_cs027_is_an_llm_port(seen: Seen) -> None:
    llm: LLMPort = LangChainLLM(
        "openai:gpt-test", prompts=PromptRegistry(), model_factory=_factory(seen, {})
    )
    assert llm is not None


async def test_cs027_call_carries_the_otel_bridge_and_prompt_metadata(seen: Seen) -> None:
    llm = LangChainLLM(
        "openai:gpt-test",
        prompts=PromptRegistry(),
        model_factory=_factory(seen, _reply(Answer(text="ok"))),
    )
    await llm.structured("extract_invoice", {"document": "x"}, Answer)
    assert seen.config is not None
    assert seen.config["metadata"]["prompt_id"] == "extract_invoice"
    assert seen.config["metadata"]["prompt_version"] == "v1"


# OpenTelemetry bridge


@pytest.fixture
def spans() -> tuple[OTelCallbackHandler, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return OTelCallbackHandler(tracer=provider.get_tracer("test")), exporter


def _result(tokens_in: int = 10, tokens_out: int = 5) -> LLMResult:
    message = AIMessage(
        content="reply",
        usage_metadata={
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
        },
    )
    return LLMResult(generations=[[ChatGeneration(message=message)]])


def test_cs027_bridge_records_one_span_per_model_call(
    spans: tuple[OTelCallbackHandler, InMemorySpanExporter],
) -> None:
    handler, exporter = spans
    run_id = uuid4()
    handler.on_chat_model_start(
        {"name": "ChatOpenAI"},
        [[]],
        run_id=run_id,
        metadata={"prompt_id": "extract_invoice", "prompt_version": "v1", "ls_model_name": "m"},
    )
    handler.on_llm_end(_result(), run_id=run_id)
    (span,) = exporter.get_finished_spans()
    assert span.name == "llm.call"
    assert span.attributes is not None
    assert span.attributes["llm.prompt_id"] == "extract_invoice"
    assert span.attributes["llm.prompt_version"] == "v1"
    assert span.attributes["llm.model"] == "m"
    assert span.attributes["llm.tokens.input"] == 10
    assert span.attributes["llm.tokens.output"] == 5


def test_cs027_bridge_never_records_prompt_or_reply_text(
    spans: tuple[OTelCallbackHandler, InMemorySpanExporter],
) -> None:
    handler, exporter = spans
    run_id = uuid4()
    handler.on_chat_model_start({}, [[]], run_id=run_id, metadata={})
    handler.on_llm_end(_result(), run_id=run_id)
    (span,) = exporter.get_finished_spans()
    assert "reply" not in str(dict(span.attributes or {}))


def test_cs027_bridge_marks_a_failed_call_as_an_error(
    spans: tuple[OTelCallbackHandler, InMemorySpanExporter],
) -> None:
    handler, exporter = spans
    run_id = uuid4()
    handler.on_chat_model_start({}, [[]], run_id=run_id, metadata={})
    handler.on_llm_error(RuntimeError("boom"), run_id=run_id)
    (span,) = exporter.get_finished_spans()
    assert span.status.status_code.name == "ERROR"


def test_cs027_bridge_ignores_an_end_it_never_saw_start(
    spans: tuple[OTelCallbackHandler, InMemorySpanExporter],
) -> None:
    handler, exporter = spans
    handler.on_llm_end(_result(), run_id=uuid4())
    handler.on_llm_error(RuntimeError("x"), run_id=uuid4())
    assert exporter.get_finished_spans() == ()
