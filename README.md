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
