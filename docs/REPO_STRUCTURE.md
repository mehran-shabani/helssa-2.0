# Repository Structure Report (2025-10-03 20:15:49Z)

- **Version:** v0.0.0
- **Branch:** work
- **Recent commits:**
  - 7bbb4c4 Merge pull request #17 from mehran-shabani/codex/cleanup-repo-and-scaffold-new-apps
  - 63b1bc6 Update tests/domains/test_doctor_online_api.py
  - a93af14 Update tests/domains/test_certificate_api.py
  - 1916d21 Update tests/domains/test_doctor_online_api.py
  - 8a53a0c Update sub/api.py

## Summary
| Metric | Value |
| --- | --- |
| Total files | 120 |
| Total size | 123.8 KB |
| Total LOC | 3646 |
| Python files | 100 |
| Test files | 13 |

## Tree View
```text
helssa-2.0
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── task.yml
│   ├── workflows
│   │   ├── ci.yml
│   │   └── release.yml
│   ├── dependabot.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── analytics
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_event_stats_indexes.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── apps.py
│   └── models.py
├── apps
│   ├── common
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   └── views.py
│   ├── ops
│   │   ├── management
│   │   │   ├── commands
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bootstrap_dev.py
│   │   │   │   └── diag_probe.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── apps.py
│   └── system
│       ├── __init__.py
│       └── views.py
├── certificate
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── apps.py
│   └── models.py
├── chatbot
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── apps.py
│   └── services.py
├── config
│   ├── settings
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── core
│   ├── middleware
│   │   └── request_id.py
│   ├── __init__.py
│   └── logging.py
├── docs
│   └── REPO_STRUCTURE.md
├── doctor_online
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── apps.py
│   └── models.py
├── down
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── apps.py
│   └── models.py
├── perf
│   ├── management
│   │   ├── commands
│   │   │   ├── __init__.py
│   │   │   └── perf_slowlog.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── apps.py
│   ├── metrics.py
│   ├── tasks.py
│   └── views.py
├── scripts
│   ├── bump_version.py
│   ├── changelog.py
│   ├── repo_tree_report.py
│   ├── save_log.py
│   └── setup.sh
├── sub
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── apps.py
│   └── models.py
├── telemedicine
│   ├── gateway
│   │   ├── __init__.py
│   │   ├── bitpay.py
│   │   └── signature.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_transaction_indexes.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   └── views.py
├── tests
│   ├── api
│   │   ├── test_analytics_endpoints.py
│   │   └── test_system_endpoints.py
│   ├── domains
│   │   ├── test_certificate_api.py
│   │   ├── test_doctor_online_api.py
│   │   └── test_sub_api.py
│   ├── payments
│   │   ├── __init__.py
│   │   ├── test_idempotency.py
│   │   └── test_signature_and_errors.py
│   ├── test_analytics_models.py
│   ├── test_health.py
│   ├── test_perf.py
│   └── test_request_id_mw.py
├── .cz.yaml
├── .editorconfig
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── docker-compose.dev.yml
├── Makefile
├── manage.py
├── pyproject.toml
├── pytest.ini
└── README.md
```

## Files
| Path | Kind | LOC | Size | Note |
| --- | --- | --- | --- | --- |
| .cz.yaml | YAML | 7 | 162 B |  |
| .editorconfig | Other | 12 | 187 B |  |
| .env.example | EXAMPLE | 15 | 520 B |  |
| .github/ISSUE_TEMPLATE/bug_report.yml | YAML | 18 | 538 B |  |
| .github/ISSUE_TEMPLATE/feature_request.yml | YAML | 11 | 313 B |  |
| .github/ISSUE_TEMPLATE/task.yml | YAML | 8 | 170 B |  |
| .github/PULL_REQUEST_TEMPLATE.md | Markdown | 17 | 224 B | Summary |
| .github/dependabot.yml | YAML | 10 | 197 B |  |
| .github/workflows/ci.yml | YAML | 27 | 676 B |  |
| .github/workflows/release.yml | YAML | 36 | 1.1 KB |  |
| .gitignore | Other | 26 | 296 B |  |
| .pre-commit-config.yaml | YAML | 15 | 366 B |  |
| CHANGELOG.md | Markdown | 4 | 57 B | Changelog |
| Makefile | Other | 59 | 1.5 KB |  |
| README.md | Markdown | 141 | 5.6 KB | Helssa 2.0 |
| analytics/__init__.py | Python | 1 | 31 B | Analytics domain models. |
| analytics/admin.py | Python | 16 | 417 B |  |
| analytics/api.py | Python | 105 | 4.2 KB |  |
| analytics/apps.py | Python | 6 | 150 B |  |
| analytics/migrations/0001_initial.py | Python | 62 | 2.1 KB |  |
| analytics/migrations/0002_event_stats_indexes.py | Python | 25 | 581 B |  |
| analytics/migrations/__init__.py | Python | 0 | 0 B |  |
| analytics/models.py | Python | 26 | 971 B |  |
| apps/common/__init__.py | Python | 1 | 28 B | Common utilities app. |
| apps/common/apps.py | Python | 6 | 149 B |  |
| apps/common/views.py | Python | 5 | 102 B |  |
| apps/ops/__init__.py | Python | 0 | 0 B |  |
| apps/ops/apps.py | Python | 6 | 125 B |  |
| apps/ops/management/__init__.py | Python | 0 | 0 B |  |
| apps/ops/management/commands/__init__.py | Python | 0 | 0 B |  |
| apps/ops/management/commands/bootstrap_dev.py | Python | 37 | 1.4 KB |  |
| apps/ops/management/commands/diag_probe.py | Python | 252 | 8.9 KB |  |
| apps/system/__init__.py | Python | 0 | 0 B |  |
| apps/system/views.py | Python | 143 | 6.8 KB |  |
| certificate/__init__.py | Python | 0 | 0 B |  |
| certificate/admin.py | Python | 5 | 100 B |  |
| certificate/api.py | Python | 31 | 1.5 KB |  |
| certificate/apps.py | Python | 6 | 154 B |  |
| certificate/migrations/0001_initial.py | Python | 30 | 972 B |  |
| certificate/migrations/__init__.py | Python | 0 | 0 B |  |
| certificate/models.py | Python | 9 | 336 B |  |
| chatbot/__init__.py | Python | 0 | 0 B |  |
| chatbot/apps.py | Python | 6 | 146 B |  |
| chatbot/migrations/0001_initial.py | Python | 9 | 137 B |  |
| chatbot/migrations/__init__.py | Python | 0 | 0 B |  |
| chatbot/services.py | Python | 20 | 1.0 KB |  |
| config/__init__.py | Python | 3 | 65 B |  |
| config/asgi.py | Python | 9 | 226 B |  |
| config/celery.py | Python | 8 | 225 B |  |
| config/settings/base.py | Python | 167 | 5.0 KB |  |
| config/settings/dev.py | Python | 5 | 129 B |  |
| config/settings/prod.py | Python | 10 | 334 B |  |
| config/settings/test.py | Python | 17 | 520 B |  |
| config/urls.py | Python | 50 | 2.0 KB |  |
| config/wsgi.py | Python | 9 | 227 B |  |
| core/__init__.py | Python | 1 | 37 B | Core infrastructure utilities. |
| core/logging.py | Python | 38 | 1.3 KB |  |
| core/middleware/request_id.py | Python | 20 | 657 B |  |
| docker-compose.dev.yml | YAML | 9 | 165 B |  |
| docs/REPO_STRUCTURE.md | Markdown | 330 | 12.1 KB | Repository Structure Report (2025-10-03 20:15:35Z) |
| doctor_online/__init__.py | Python | 0 | 0 B |  |
| doctor_online/admin.py | Python | 5 | 88 B |  |
| doctor_online/api.py | Python | 17 | 514 B |  |
| doctor_online/apps.py | Python | 6 | 157 B |  |
| doctor_online/migrations/0001_initial.py | Python | 31 | 976 B |  |
| doctor_online/migrations/__init__.py | Python | 0 | 0 B |  |
| doctor_online/models.py | Python | 10 | 322 B |  |
| down/__init__.py | Python | 0 | 0 B |  |
| down/admin.py | Python | 5 | 108 B |  |
| down/api.py | Python | 17 | 550 B |  |
| down/apps.py | Python | 6 | 140 B |  |
| down/migrations/0001_initial.py | Python | 19 | 590 B |  |
| down/migrations/__init__.py | Python | 0 | 0 B |  |
| down/models.py | Python | 7 | 227 B |  |
| manage.py | Python | 14 | 286 B | !/usr/bin/env python |
| perf/__init__.py | Python | 0 | 0 B |  |
| perf/apps.py | Python | 6 | 140 B |  |
| perf/management/__init__.py | Python | 0 | 0 B |  |
| perf/management/commands/__init__.py | Python | 0 | 0 B |  |
| perf/management/commands/perf_slowlog.py | Python | 92 | 3.3 KB |  |
| perf/metrics.py | Python | 41 | 1.1 KB |  |
| perf/tasks.py | Python | 15 | 359 B |  |
| perf/views.py | Python | 12 | 297 B |  |
| pyproject.toml | TOML | 61 | 1.2 KB |  |
| pytest.ini | INI | 4 | 121 B |  |
| scripts/bump_version.py | Python | 36 | 951 B | !/usr/bin/env python3 |
| scripts/changelog.py | Python | 57 | 1.9 KB | !/usr/bin/env python3 |
| scripts/repo_tree_report.py | Python | 193 | 8.5 KB | Generate a repository structure report in Markdown. |
| scripts/save_log.py | Python | 117 | 3.5 KB | Save diagnostic logs to docs/PROJECT_LOG.md and project_logs/. |
| scripts/setup.sh | Shell | 27 | 667 B |  |
| sub/__init__.py | Python | 0 | 0 B |  |
| sub/admin.py | Python | 6 | 142 B |  |
| sub/api.py | Python | 32 | 1.7 KB |  |
| sub/apps.py | Python | 6 | 138 B |  |
| sub/migrations/0001_initial.py | Python | 44 | 1.5 KB |  |
| sub/migrations/__init__.py | Python | 0 | 0 B |  |
| sub/models.py | Python | 14 | 508 B |  |
| telemedicine/__init__.py | Python | 0 | 0 B |  |
| telemedicine/admin.py | Python | 16 | 445 B |  |
| telemedicine/apps.py | Python | 6 | 156 B |  |
| telemedicine/gateway/__init__.py | Python | 0 | 0 B |  |
| telemedicine/gateway/bitpay.py | Python | 19 | 492 B |  |
| telemedicine/gateway/signature.py | Python | 30 | 1.1 KB |  |
| telemedicine/migrations/0001_initial.py | Python | 30 | 852 B |  |
| telemedicine/migrations/0002_transaction_indexes.py | Python | 54 | 1.3 KB |  |
| telemedicine/migrations/__init__.py | Python | 0 | 0 B |  |
| telemedicine/models.py | Python | 15 | 378 B |  |
| telemedicine/views.py | Python | 170 | 5.9 KB |  |
| tests/api/test_analytics_endpoints.py | Python | 54 | 2.2 KB |  |
| tests/api/test_system_endpoints.py | Python | 89 | 3.5 KB |  |
| tests/domains/test_certificate_api.py | Python | 51 | 2.4 KB |  |
| tests/domains/test_doctor_online_api.py | Python | 41 | 1.6 KB |  |
| tests/domains/test_sub_api.py | Python | 15 | 512 B |  |
| tests/payments/__init__.py | Python | 0 | 0 B |  |
| tests/payments/test_idempotency.py | Python | 53 | 2.0 KB |  |
| tests/payments/test_signature_and_errors.py | Python | 82 | 2.6 KB |  |
| tests/test_analytics_models.py | Python | 23 | 664 B |  |
| tests/test_health.py | Python | 13 | 345 B |  |
| tests/test_perf.py | Python | 68 | 1.9 KB |  |
| tests/test_request_id_mw.py | Python | 28 | 783 B |  |

## Notable Configs
- `.editorconfig`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `Makefile`
- `README.md`
- `docker-compose.dev.yml`
- `pyproject.toml`
- `pytest.ini`

## URL Patterns (Quick Scan)
- `config/urls.py`
  - `admin/`
  - `health`
  - `api/v1/system/health`
  - `api/v1/system/ready`
  - `api/v1/subscriptions/me`
  - `api/v1/`
  - `api/schema/`
  - `api/docs/`
  - `telemedicine/pay/webhook`
  - `telemedicine/pay/verify`
  - `metrics`
