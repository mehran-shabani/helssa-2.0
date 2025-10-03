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

### API Docs

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Make targets
- `make install` – install dependencies and set up git hooks
- `make run` – start the Django development server
- `make celery` – launch the Celery worker
- `make lint` – run Ruff and isort checks
- `make format` – auto-format imports via isort
- `make test` – run the pytest suite
- `make migrate` – apply database migrations

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
