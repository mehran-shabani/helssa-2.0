# Helssa 2.0

[![CI](https://github.com/helssa/helssa-2.0/actions/workflows/ci.yml/badge.svg)](https://github.com/helssa/helssa-2.0/actions/workflows/ci.yml)
[![Release](https://github.com/helssa/helssa-2.0/actions/workflows/release.yml/badge.svg)](https://github.com/helssa/helssa-2.0/actions/workflows/release.yml)

Helssa 2.0 is the next-generation backend stack for the Helssa platform. It ships with Django 5, Django REST Framework, Celery, Redis wiring, JSON logging with request tracing, and automated release tooling.

## Requirements
- Python 3.12+
- Redis (for Celery broker/backing store)
- PostgreSQL (production), SQLite supported locally

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Visit [`/health`](http://localhost:8000/health) for a readiness probe.

### Dev Bootstrap

```bash
python manage.py bootstrap_dev
python manage.py diag_probe --md || true
# Optional for Celery ping:
make redis-up
```

## Endpoints

- `GET /health` → fast path (no database access)
- `GET /api/v1/system/health` → public status with version metadata
- `GET /api/v1/system/ready` → readiness check for DB/cache/Celery (staff-only)
- `GET /api/v1/analytics/daily` → paginated daily aggregates (staff-only)
- `GET /api/v1/analytics/events` → paginated analytics events (staff-only)

## New domain APIs

- `GET /api/v1/doctor/visits/` → staff-only visit log (read-only)
- `GET /api/v1/certificates/` → authenticated; staff see all, others only their certificates
- `GET /api/v1/down/apk-stats/` → staff-only APK download counters (read-only)
- `GET /api/v1/subscriptions/me` → authenticated users read their subscription and balance snapshot

### API Docs

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Chatbot API

Helssa ships with a single multimodal medical Q&A endpoint that proxies to OpenAI models.

### Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key passed to the OpenAI SDK | `""` |
| `OPENAI_BASE_URL` | Optional override for the OpenAI base URL | unset |
| `OPENAI_ORG` | Optional OpenAI organization id | unset |
| `CHATBOT_DEFAULT_MODEL` | Model for plain text questions | `gpt-4o-mini` |
| `CHATBOT_VISION_MODEL` | Model for requests with images | `CHATBOT_DEFAULT_MODEL` |
| `CHATBOT_REASONING_MODEL` | Model when PDF text context is supplied | `CHATBOT_DEFAULT_MODEL` |
| `CHATBOT_MAX_TOKENS` | Max output tokens per response | `1024` |
| `CHATBOT_REQUEST_TIMEOUT` | OpenAI client timeout in seconds | `20` |

Set these in the environment (or `.env`) that loads the Django settings module.

### Example requests

Plain JSON request:

```bash
curl -sS -X POST http://localhost:8000/api/v1/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"سرفه خشک دارم، چه عللی ممکنه داشته باشه؟"}'
```

Multipart with vision + PDF context:

```bash
curl -sS -X POST http://localhost:8000/api/v1/chatbot/ask \
  -F 'message=سلام، خلاصه آزمایش رو می‌دی؟' \
  -F 'images=@/path/to/scan.png' \
  -F 'pdfs=@/path/to/report.pdf'
```

Streaming (Server-Sent Events):

```bash
curl -N -X POST 'http://localhost:8000/api/v1/chatbot/ask?stream=true' \
  -H "Content-Type: application/json" \
  -d '{"message":"نتیجه آزمایش را خلاصه کن"}'
```

Responses always append a short disclaimer reminding users that the assistant does **not** provide diagnoses or prescriptions and that urgent issues require professional medical care.

### Smart storage

When `SMART_STORAGE_ENABLED=true` the chatbot stores conversations selectively based on consent, intent, and clinical urgency. The following environment flags fine-tune retention:

| Variable | Purpose | Default |
| --- | --- | --- |
| `SMART_STORAGE_ENABLED` | Master switch for smart storage | `true` |
| `SMART_STORAGE_REQUIRE_CONSENT` | Skip persistence unless consent is recorded | `true` |
| `SMART_STORAGE_DEFAULT_MODE` | Baseline mode when `store="auto"` | `summary` |
| `SMART_STORAGE_TTL_DAYS` | Database retention period for stored notes | `30` |
| `SMART_STORAGE_CACHE_TTL_SECONDS` | Cache duration for policy decisions | `86400` |
| `SMART_STORAGE_MAX_TURNS` | Maximum stored turns per conversation before pruning | `8` |
| `SMART_STORAGE_MAX_TOKENS` | Approximate cap (characters) before demoting `full` storage | `3000` |
| `SMART_STORAGE_CLASSIFY_WITH_LLM` | Enable LLM-backed classification fallback | `false` |
| `SMART_STORAGE_SUMMARIZE_WITH_LLM` | Enable LLM-generated summaries | `false` |

Give consent or revoke it inline via the single `/api/v1/chatbot/ask` endpoint. The same endpoint also supports targeted purge operations for stored notes:

```bash
# give consent inline and ask
curl -sX POST http://localhost:8000/api/v1/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"سرفه خشک ۲ هفته","consent":true,"store":"auto","conversation_id":"<uuid>"}'

# reset/purge notes for a conversation
curl -sX POST http://localhost:8000/api/v1/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<uuid>","purge":true,"message":"سلام"}'
```

Stored notes expire automatically. Run the sweep command manually or wire it into Celery beat:

```bash
python manage.py chatbot_sweep

# Example Celery beat entry (add to CELERY_BEAT_SCHEDULE)
# "chatbot-smart-storage" : {
#     "task": "chatbot_sweep",
#     "schedule": crontab(hour=2, minute=0),
# }
```

## Make targets
- `make install` – install dependencies and set up git hooks
- `make run` – start the Django development server
- `make celery` – launch the Celery worker
- `make lint` – run Ruff and isort checks
- `make format` – auto-format imports via isort
- `make test` – run the pytest suite
- `make migrate` – apply database migrations

## Diagnostics & Coverage

- `make diag` regenerates `.reports/diag.json` and writes the curated summary to `docs/DIAG.md`.
- `make diag-commit` optionally stages `.reports/diag.json` and `docs/DIAG.md` and creates a local commit.
- Continuous integration enforces at least **80%** test coverage and publishes the HTML report artifact when pipelines run.

## Observability
All HTTP responses carry `X-Request-ID` and `X-Response-Time-ms` headers. Structured logs are emitted in JSON with PII masking for sensitive keys (`password`, `token`, `otp`, `national_code`).

…  
structured logs are emitted in JSON with PII masking for sensitive keys (`password`, `token`, `otp`, `national_code`).

## Log capture

Use `scripts/save_log.py` to archive diagnostics without touching runtime behavior. Each run appends a timestamped entry to `docs/PROJECT_LOG.md` and stores the raw text under `project_logs/`.

Examples:

```bash
echo "my log text" | python scripts/save_log.py --tag "phase note"
printf "my log text\n" | make save-log TAG="phase note"
make save-log-file FILE=path/to/log.txt TAG="perf review"
echo "ready to commit" | make save-log-commit TAG="triage"
```

`make save-log-commit` (or the `--commit` flag) creates a local `[skip ci] chore(log): update PROJECT_LOG.md` commit when Git is available.


## Performance
The backend includes opt-in hooks for database tuning and runtime metrics:
…  

- **Slow query reports** rely on PostgreSQL's `pg_stat_statements` extension. Enable it once with:

  ```sql
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
  ```

  Then run `python manage.py perf_slowlog` to print the top queries by total and mean execution time. Add `--reset` to clear the statistics afterwards. The command gracefully explains how to enable the extension when it's missing.

- **Prometheus metrics** become available at `/metrics` when `ENABLE_METRICS=true` is exported before starting Django. The endpoint responds with `text/plain; version=0.0.4` content and performs lightweight counts at request time only.

- **Celery beat (optional)** gains a weekly job when `ENABLE_PERF_SLOWLOG_BEAT=true` is set. The job logs the slow query report to stdout so operators can archive it from worker logs. It is disabled by default for production deployments.

## Celery
Celery is configured with Redis by default. Update `CELERY_BROKER_URL` in your environment to point to your broker. Celery auto-discovers tasks from Django apps.

```bash
make celery
```

## Releases
Merges to `main` trigger the release workflow which bumps the minor version (starting at `v2.0.0`), generates a changelog grouped by Conventional Commit types, tags the commit, and publishes a GitHub Release.

To prepare the repo locally:
```bash
./scripts/setup.sh
```

## Contributing
- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Ensure `pre-commit` hooks are installed (`pre-commit install`)
- Run `make lint test` before pushing

## License
MIT

## Payments Hardening

BitPay integrations are secured with idempotency keys, signature verification, and strict timeouts.

- Configure the following environment variables:
  - `PAYMENT_GATEWAY` (default: `bitpay`)
  - `BITPAY_WEBHOOK_SECRET`
  - `BITPAY_SIGNATURE_HEADER` (default: `X-Signature`)
  - `BITPAY_TIMESTAMP_HEADER` (default: `X-Timestamp`)
  - `PAY_SIG_MAX_SKEW_SECONDS` (default: `300`)
  - `BITPAY_VERIFY_URL`
- Duplicate webhook or verify requests short-circuit via idempotency keys and emit
  `pay_webhook_duplicate` analytics events (scoped via event props).
- Invalid signatures are rejected with HTTP 400 and recorded via `pay_webhook_bad_sig`.
- External BitPay verify requests use strict timeouts and emit `ext_error` telemetry on failures.
- Successful payment transitions emit a `pay_success` analytics event capturing turnaround time
  (TAT) and amount metadata.
