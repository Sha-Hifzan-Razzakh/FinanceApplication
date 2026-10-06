"""CS-022 DecisionPort."""

import inspect

from invoice_to_pay.application.ports import DecisionPort
from invoice_to_pay.contracts.decisions import DocumentClassification
from tests.fakes.decisions import ScriptedDecisions

ANSWER = DocumentClassification(doc_type="invoice", doc_type_p=0.95, readable_p=0.98)


def test_cs022_decision_port_is_a_protocol_with_an_async_decide() -> None:
    assert getattr(DecisionPort, "_is_protocol", False) is True
    assert inspect.iscoroutinefunction(DecisionPort.decide)
    assert list(inspect.signature(DecisionPort.decide).parameters) == ["self", "schema", "payload"]


async def test_cs022_a_fake_satisfies_the_port_and_returns_the_typed_answer() -> None:
    port: DecisionPort = ScriptedDecisions(ANSWER)
    result = await port.decide(DocumentClassification, "page 1 text")
    assert result == ANSWER
    assert isinstance(result, DocumentClassification)
