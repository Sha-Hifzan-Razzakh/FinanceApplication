"""Language model access through LangChain (the only importer besides the prompt registry)."""

from collections.abc import Callable, Mapping
from typing import Any, Literal
from uuid import UUID

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult
from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer
from pydantic import BaseModel

from invoice_to_pay.application.ports import LLMPort, StructuredOutputError
from invoice_to_pay.config.settings import LLM_PROVIDERS
from invoice_to_pay.prompts.registry import PromptRegistry

UsageSink = Callable[[str, int, int], None]
"""(prompt_id, input_tokens, output_tokens); the budget meter plugs in here (T-211)."""


class OTelCallbackHandler(BaseCallbackHandler):
    """One 'llm.call' span per model call: ids, model and token counts, never text."""

    def __init__(self, tracer: Tracer | None = None) -> None:
        self._tracer = tracer or trace.get_tracer("invoice_to_pay.llm")
        self._spans: dict[UUID, Span] = {}

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Open the span; messages are deliberately not recorded."""
        metadata = metadata or {}
        span = self._tracer.start_span("llm.call", kind=SpanKind.CLIENT)
        for attribute, key in (
            ("llm.prompt_id", "prompt_id"),
            ("llm.prompt_version", "prompt_version"),
            ("llm.model", "ls_model_name"),
        ):
            if key in metadata:
                span.set_attribute(attribute, str(metadata[key]))
        self._spans[run_id] = span

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        """Close the span with the token counts."""
        span = self._spans.pop(run_id, None)
        if span is None:
            return
        usage = (
            _usage_of(getattr(response.generations[0][0], "message", None))
            if response.generations
            else None
        )
        if usage is not None:
            span.set_attribute("llm.tokens.input", usage[0])
            span.set_attribute("llm.tokens.output", usage[1])
        span.end()

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        """Close the span as failed; the exception type is recorded, not its message."""
        span = self._spans.pop(run_id, None)
        if span is None:
            return
        span.set_status(Status(StatusCode.ERROR, type(error).__name__))
        span.end()


def _usage_of(message: Any) -> tuple[int, int] | None:
    usage = getattr(message, "usage_metadata", None)
    if not usage:
        return None
    return int(usage["input_tokens"]), int(usage["output_tokens"])


class LangChainLLM(LLMPort):
    """init_chat_model for one role's provider:model id; structured replies as Pydantic."""

    def __init__(
        self,
        model_id: str,
        *,
        prompts: PromptRegistry,
        on_usage: UsageSink | None = None,
        method: Literal["function_calling", "json_schema"] | None = None,
        model_factory: Callable[..., Any] = init_chat_model,
    ) -> None:
        provider, _, model = model_id.partition(":")
        if provider not in LLM_PROVIDERS or not model:
            raise ValueError(f"model id must be provider:model with provider in {LLM_PROVIDERS}")
        self._prompts = prompts
        self._on_usage = on_usage
        self._method = method
        self._model = model_factory(model, model_provider=provider)
        self._bridge = OTelCallbackHandler()

    def prompt_version(self, prompt_id: str) -> str:
        """The version of prompt_id that structured() uses."""
        return self._prompts.version_of(prompt_id)

    async def structured[T: BaseModel](
        self, prompt_id: str, vars: Mapping[str, Any], schema: type[T]
    ) -> T:
        """Fill the prompt, call the model, return its reply as schema."""
        prompt_value = await self._prompts.get(prompt_id).ainvoke(dict(vars))
        # None keeps the provider's default. json_schema is opt-in: Anthropic's structured outputs
        # turn a free-key dict such as InvoiceDraft.field_quotes into an empty object.
        options: dict[str, Any] = {} if self._method is None else {"method": self._method}
        runnable = self._model.with_structured_output(schema, include_raw=True, **options)
        config = {
            "callbacks": [self._bridge],
            "metadata": {
                "prompt_id": prompt_id,
                "prompt_version": self._prompts.version_of(prompt_id),
            },
        }
        reply: dict[str, Any] = await runnable.ainvoke(prompt_value, config=config)
        raw = reply.get("raw")
        if self._on_usage is not None and isinstance(raw, AIMessage):
            usage = _usage_of(raw)
            if usage is not None:
                self._on_usage(prompt_id, *usage)
        if reply.get("parsing_error") is not None:
            raise StructuredOutputError(str(reply["parsing_error"]))
        parsed = reply.get("parsed")
        if not isinstance(parsed, schema):
            raise StructuredOutputError(f"the model reply did not fit {schema.__name__}")
        return parsed
