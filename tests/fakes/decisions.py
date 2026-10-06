"""A DecisionPort fake that answers each decision schema from a prepared model."""

from pydantic import BaseModel


class ScriptedDecisions:
    """DecisionPort fake: returns the prepared answer for the requested schema."""

    def __init__(self, *answers: BaseModel) -> None:
        self._answers = {type(a): a for a in answers}
        self.questions: list[tuple[type[BaseModel], str]] = []

    async def decide[T: BaseModel](self, schema: type[T], payload: str) -> T:
        self.questions.append((schema, payload))
        answer = self._answers[schema]
        assert isinstance(answer, schema)
        return answer
