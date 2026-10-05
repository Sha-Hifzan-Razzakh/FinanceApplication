# Make targets (Commands sheet). Variables from .env are exported to every command.
-include .env
export

.PHONY: setup dev worker erp-mcp lint typecheck test-unit test-int test-scenarios eval redteam e2e migrate gate

setup:
	uv sync && uv run playwright install chromium && docker compose up -d && uv run alembic upgrade head

dev:
	uv run fastapi dev invoice_to_pay/main.py

worker:
	uv run arq invoice_to_pay.workers.settings.WorkerSettings

erp-mcp:
	uv run python -m invoice_to_pay.mcp_servers.erp

lint:
	uv run ruff check . && uv run ruff format --check . && uv run lint-imports

typecheck:
	uv run mypy invoice_to_pay

test-unit:
	uv run pytest tests/unit -q

test-int:
	uv run pytest tests/integration -q

test-scenarios:
	uv run pytest tests/scenarios -q

eval:
	uv run deepeval test run evals/deepeval && uv run pytest evals/ragas -q

redteam:
	npx promptfoo@latest eval -c evals/promptfoo/promptfooconfig.yaml

e2e:
	uv run pytest tests/e2e -q

migrate:
	uv run alembic upgrade head

gate:
	$(MAKE) lint typecheck test-unit test-int test-scenarios eval redteam e2e
