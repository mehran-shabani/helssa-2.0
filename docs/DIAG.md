# Helssa Diagnostics

> Status: **DEGRADED**

- Generated (UTC): `2025-10-04T08:28:04Z`
- Version: `v2.0.0`
- Settings module: `config.settings.test`

## Summary
| Health | Ready | DB Connected | Pending Migrations | Coverage (%) |
| --- | --- | --- | --- | --- |
| 200 | 403 | True | 27 | 87.00 |

## Flags
```json
{
  "ENABLE_METRICS": false,
  "KPI_API_ENABLED": true,
  "TELEMETRY_ENABLED": true
}
```

## Git
```json
{
  "branch": "work",
  "last_commits": [
    "59da705 Merge pull request #19 from mehran-shabani/codex/review-and-update-repo_structure.md",
    "82d4696 docs: refresh repository structure report",
    "7bbb4c4 Merge pull request #17 from mehran-shabani/codex/cleanup-repo-and-scaffold-new-apps"
  ],
  "last_tag": "v2.0.0"
}
```

<details>
<summary>Raw diag.json</summary>

```json
{
  "cache": {
    "backend": "django.core.cache.backends.locmem.LocMemCache",
    "ok": true
  },
  "celery": {
    "enabled": true,
    "error": "Error 111 connecting to localhost:6379. Connection refused.",
    "ok": false
  },
  "coverage": {
    "source": "htmlcov",
    "total_percent": 87.0
  },
  "db": {
    "connected": true,
    "engine": "django.db.backends.sqlite3"
  },
  "debug": false,
  "django": "5.2.7",
  "endpoints": {
    "/api/v1/system/health": {
      "body": {
        "status": "ok",
        "time": "2025-10-04T08:27:58.760668+00:00",
        "version": "2.0.0"
      },
      "status_code": 200
    },
    "/api/v1/system/ready": {
      "body": {
        "detail": "Authentication credentials were not provided."
      },
      "skipped_staff_due_to_pending_migrations": true,
      "status_code": 403
    },
    "/health": {
      "body": {
        "status": "ok"
      },
      "status_code": 200
    }
  },
  "flags": {
    "ENABLE_METRICS": false,
    "KPI_API_ENABLED": true,
    "TELEMETRY_ENABLED": true
  },
  "git": {
    "branch": "work",
    "last_commits": [
      "59da705 Merge pull request #19 from mehran-shabani/codex/review-and-update-repo_structure.md",
      "82d4696 docs: refresh repository structure report",
      "7bbb4c4 Merge pull request #17 from mehran-shabani/codex/cleanup-repo-and-scaffold-new-apps"
    ],
    "last_tag": "v2.0.0"
  },
  "migrations": {
    "pending_by_app_top": {
      "admin": 3,
      "analytics": 2,
      "auth": 12,
      "contenttypes": 2,
      "telemedicine": 2
    },
    "pending_total": 27
  },
  "python": "3.12.10",
  "settings": "config.settings.test",
  "ts": "2025-10-04T08:27:58.745792+00:00",
  "version": "v2.0.0"
}
```

</details>
