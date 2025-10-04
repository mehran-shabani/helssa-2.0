# Helssa Diagnostic Report
- time: `2025-10-04T08:27:58.745792+00:00`
- version: `v2.0.0`

## Summary
- DB connected: **True**
- Pending migrations: **27**
- Health status: **200**
- Ready status: **403**
- Coverage: **87.0%**

## Flags
```
{
  "TELEMETRY_ENABLED": true,
  "KPI_API_ENABLED": true,
  "ENABLE_METRICS": false
}
```

## Endpoints
```
{
  "/health": {
    "status_code": 200,
    "body": {
      "status": "ok"
    }
  },
  "/api/v1/system/health": {
    "status_code": 200,
    "body": {
      "status": "ok",
      "time": "2025-10-04T08:27:58.760668+00:00",
      "version": "2.0.0"
    }
  },
  "/api/v1/system/ready": {
    "status_code": 403,
    "body": {
      "detail": "Authentication credentials were not provided."
    },
    "skipped_staff_due_to_pending_migrations": true
  }
}
```

## Git
```
{
  "branch": "work",
  "last_tag": "v2.0.0",
  "last_commits": [
    "59da705 Merge pull request #19 from mehran-shabani/codex/review-and-update-repo_structure.md",
    "82d4696 docs: refresh repository structure report",
    "7bbb4c4 Merge pull request #17 from mehran-shabani/codex/cleanup-repo-and-scaffold-new-apps"
  ]
}
```
