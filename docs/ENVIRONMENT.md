# Environment
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

## Local services
| Service | Image / command | Port | Purpose | First needed in |
|---|---|---|---|---|
| postgres | pgvector/pgvector:pg16 | 5432 | Records, ledger, checkpoints, vectors | T-101 |
| redis | redis:7 | 6379 | Counters, idempotency, attempts, Arq | T-108 |
| minio | minio/minio | 9000 / 9001 | Local S3-compatible object storage | T-106 |
| vault | hashicorp/vault (dev mode) | 8200 | Local secrets | T-202 |
| otel-collector | otel/opentelemetry-collector | 4317 | Receives traces and metrics | T-105 |
| erp-stub | uv run python -m tests.fakes.erp_api | 8081 | Fake ERP REST API behind the ERP MCP server | T-201 |
| erp-mcp | uv run python -m invoice_to_pay.mcp_servers.erp | 8100 | ERP MCP server (Streamable HTTP) | T-201 |
| mail-mcp | chosen mail MCP server | 8101 | Mailbox and sending | T-502 |
| api | uv run fastapi dev invoice_to_pay/main.py | 8000 | The FastAPI app | T-101 |
| worker | uv run arq invoice_to_pay.workers.settings.WorkerSettings | — | Background jobs | T-108 |

## Environment variables
| Variable | Type | Default | Constraints | Meaning |
|---|---|---|---|---|
| ITP_DATABASE_URL | PostgresDsn | required |  |  |
| ITP_REDIS_URL | RedisDsn | required |  |  |
| ITP_OBJECT_BUCKET | str | required |  |  |
| ITP_VAULT_URL | HttpUrl | required |  |  |
| ITP_ERP_MCP_URL | HttpUrl | required |  |  |
| ITP_MAIL_MCP_URL | HttpUrl | required |  |  |
| ITP_LLM_EXTRACT_MODEL | str | required |  | Pinned id |
| ITP_LLM_REASON_MODEL | str | required |  | Pinned id |
| ITP_JEV_MODEL | str | required | not 'jev-latest' | Pinned version |
| ITP_EMBEDDING_MODEL | str | required |  | Pinned; stored with every vector |
| ITP_POST_ALONE_MAX_AED | Decimal | Decimal('25000') | gt=0 |  |
| ITP_TWO_APPROVER_MIN_AED | Decimal | Decimal('250000') | gt=0 |  |
| ITP_DAILY_AUTONOMOUS_CAP_AED | Decimal | Decimal('500000') | gt=0 |  |
| ITP_DOC_TYPE_THRESHOLD | float | 0.9 |  |  |
| ITP_LINE_MAP_THRESHOLD | float | 0.9 |  |  |
| ITP_NEAR_DUPLICATE_THRESHOLD | float | 0.7 |  |  |
| ITP_APPROVAL_TTL_HOURS | int | 24 |  |  |
| ITP_OTEL_ENDPOINT | HttpUrl \| None | None |  |  |
| ITP_AUTH_ISSUER | str | required |  | Expected iss claim of bearer tokens |
| ITP_AUTH_AUDIENCE | str | required |  | Expected aud claim of bearer tokens |
| ITP_AUTH_PUBLIC_KEY | str | required | PEM; \n escapes accepted | Public key that verifies RS256 tokens |
| ITP_AGENT_SUBJECT | str | 'agent:invoice-to-pay' |  | Principal subject the agent runs as |

## Commands
| Target | Command | What it does |
|---|---|---|
| setup | uv sync && uv run playwright install chromium && docker compose up -d && uv run alembic upgrade head | First-time setup |
| dev | uv run fastapi dev invoice_to_pay/main.py | API with reload |
| worker | uv run arq invoice_to_pay.workers.settings.WorkerSettings | Background worker |
| erp-mcp | uv run python -m invoice_to_pay.mcp_servers.erp | ERP MCP server |
| lint | uv run ruff check . && uv run ruff format --check . && uv run lint-imports | Lint, format, import rules |
| typecheck | uv run mypy invoice_to_pay | Static types |
| test-unit | uv run pytest tests/unit -q | Unit tests, no network |
| test-int | uv run pytest tests/integration -q | Integration tests against the local stack |
| test-scenarios | uv run pytest tests/scenarios -q | End-to-end scenarios with the stub ERP |
| eval | uv run deepeval test run evals/deepeval && uv run pytest evals/ragas -q | Model-quality suites |
| redteam | npx promptfoo@latest eval -c evals/promptfoo/promptfooconfig.yaml | Adversarial suite |
| e2e | uv run pytest tests/e2e -q | Playwright end-to-end |
| migrate | uv run alembic upgrade head | Apply migrations |
| gate | make lint typecheck test-unit test-int test-scenarios eval redteam e2e | Everything the release gate runs |
| docs | uv run python spec/build_repo_docs.py --repo . | Rebuild generated docs and task specs (never touches living docs) |
| docs-check | python3 scripts/progress.py check | Check PROGRESS.md against task specs, groups and dependencies |
| progress | python3 scripts/progress.py summary | Three-line status: counts, current group, next group and its model |

## Bootstrap files
| Path | Created in | Purpose | Content |
|---|---|---|---|
| pyproject.toml | T-101 | Project metadata, dependencies, tool config | [project] deps from the Stack sheet, each added by the task that first needs it; [tool.ruff], [tool.mypy] strict for domain/contracts/control/application, [tool.pytest.ini_options] asyncio_mode='auto', [tool.importlinter] contracts from Framework Rules |
| uv.lock | T-101 | Locked versions | Committed; copy resolved versions into the Stack sheet |
| CLAUDE.md | T-101 | Standing instructions for Claude Code | Generated with this workbook (claude_code_pack/CLAUDE.md) |
| tasks/T-xxx.md | T-101 | One prompt per task | Generated with this workbook (claude_code_pack/tasks/) |
| docker-compose.yml | T-101 | Local services | Services from the Environment sheet |
| .env.example | T-101 | Every ITP_ setting with a safe placeholder | From the Settings contract; no real secrets |
| Makefile | T-101 | Command targets | Targets from the Commands sheet |
| alembic.ini, migrations/ | T-104 | Schema migrations | One revision per table group |
| prompts/<id>/v1.md | T-111 | Versioned prompts | From the Prompt Registry sheet |
| tests/fixtures/seed.py | T-201 | Seed data for the stub ERP and scenarios | From the Fixtures sheet |
| .github/workflows/release-gate.yml | T-605 | CI gate | Runs `make gate` |
| .claude/settings.json | T-101 | Claude Code permissions for this repo | Allow: uv run, pytest, ruff, mypy, docker compose ps/logs, alembic; deny: network writes outside localhost, rm -rf, git push --force |
