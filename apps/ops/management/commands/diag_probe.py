import json
import logging
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Dict, List

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.utils import timezone

try:
    from celery import current_app as celery_app
except Exception:  # pragma: no cover - celery not installed
    celery_app = None


log = logging.getLogger(__name__)
REPORT_DIR = pathlib.Path(".reports")


def _git(cmd: List[str], default: str = "") -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return default


def _git_tag() -> str:
    version = os.getenv("HELSSA_VERSION")
    if version:
        return version
    return _git(["git", "describe", "--tags", "--abbrev=0"], "v2.0.0")


def _migrations_summary() -> Dict[str, Any]:
    try:
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        pending = len(plan)
        per_app: Dict[str, int] = {}
        for migration, _ in plan:
            per_app[migration.app_label] = per_app.get(migration.app_label, 0) + 1
        top = dict(sorted(per_app.items(), key=lambda item: item[1], reverse=True)[:5])
        return {
            "pending_total": pending,
            "pending_by_app_top": top,
        }
    except Exception as exc:  # pragma: no cover - diagnostics only
        return {"error": str(exc)}


def _cache_probe() -> Dict[str, Any]:
    backend = settings.CACHES.get("default", {}).get("BACKEND", "?")
    try:
        key = "diag_probe_key"
        cache.set(key, "1", 2)
        ok = cache.get(key) == "1"
        return {"backend": backend, "ok": bool(ok)}
    except Exception as exc:  # pragma: no cover - diagnostics only
        return {"backend": backend, "ok": False, "error": str(exc)}


def _celery_ping() -> Dict[str, Any]:
    if not celery_app:
        return {"enabled": False}
    try:
        response = celery_app.control.ping(timeout=1.0)
        return {"enabled": True, "ok": bool(response), "workers": response}
    except Exception as exc:  # pragma: no cover - diagnostics only
        return {"enabled": True, "ok": False, "error": str(exc)}


def _endpoint(client: Client, path: str, staff: bool = False) -> Dict[str, Any]:
    try:
        if staff:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user, _ = User.objects.get_or_create(
                    username="diag_staff",
                    defaults={
                        "email": "diag@example.com",
                        "is_staff": True,
                        "is_superuser": False,
                    },
                )
                if not user.is_staff:
                    user.is_staff = True
                    user.save(update_fields=["is_staff"])
            client.force_login(user)
        response = client.get(path)
        try:
            body = response.json()
        except Exception:
            body = {}
        finally:
            if staff:
                client.logout()
        return {"status_code": response.status_code, "body": body}
    except Exception as exc:  # pragma: no cover - diagnostics only
        return {"error": str(exc)}


def _coverage() -> Dict[str, Any]:
    xml = pathlib.Path("coverage.xml")
    if xml.exists():
        text = xml.read_text(errors="ignore")
        match = re.search(r'line-rate="([0-9.]+)"', text)
        if match:
            try:
                pct = round(float(match.group(1)) * 100, 2)
                return {"total_percent": pct, "source": "coverage.xml"}
            except Exception:  # pragma: no cover - diagnostics only
                pass
    html = pathlib.Path("htmlcov/index.html")
    if html.exists():
        text = html.read_text(errors="ignore")
        match = re.search(r"Total[^%]*?(\d+(?:\.\d+)?)%", text, re.S)
        if match:
            try:
                return {"total_percent": float(match.group(1)), "source": "htmlcov"}
            except Exception:  # pragma: no cover - diagnostics only
                pass
    return {"total_percent": None, "source": None}


class Command(BaseCommand):
    help = "Prints a structured diagnostic report. Use --md to also write .reports/diag.md & .json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--md",
            action="store_true",
            help="Also write Markdown/JSON files into .reports/",
        )

    def handle(self, *args, **options):
        report_dir = REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = timezone.now().isoformat()
        client = Client()

        health = _endpoint(client, "/health")
        system_health = _endpoint(client, "/api/v1/system/health")
        ready = _endpoint(client, "/api/v1/system/ready", staff=True)

        db_info: Dict[str, Any] = {
            "engine": settings.DATABASES.get("default", {}).get("ENGINE", "?"),
        }
        try:
            connection.ensure_connection()
            db_info["connected"] = True
        except Exception as exc:  # pragma: no cover - diagnostics only
            db_info["connected"] = False
            db_info["error"] = str(exc)

        report = {
            "ts": timestamp,
            "version": _git_tag(),
            "python": sys.version.split()[0],
            "django": __import__("django").get_version(),
            "settings": os.getenv("DJANGO_SETTINGS_MODULE"),
            "debug": bool(getattr(settings, "DEBUG", False)),
            "flags": {
                "TELEMETRY_ENABLED": bool(getattr(settings, "TELEMETRY_ENABLED", True)),
                "KPI_API_ENABLED": bool(getattr(settings, "KPI_API_ENABLED", True)),
                "ENABLE_METRICS": os.getenv("ENABLE_METRICS", "false").lower() == "true",
            },
            "git": {
                "branch": _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], ""),
                "last_tag": _git_tag(),
                "last_commits": _git(
                    ["git", "log", "-n", "3", "--pretty=%h %s"],
                    "",
                ).splitlines(),
            },
            "db": db_info,
            "migrations": _migrations_summary(),
            "cache": _cache_probe(),
            "celery": _celery_ping(),
            "endpoints": {
                "/health": health,
                "/api/v1/system/health": system_health,
                "/api/v1/system/ready": ready,
            },
            "coverage": _coverage(),
        }

        self.stdout.write("===== BEGIN_HELSSA_DIAG =====")
        for key, value in report.items():
            if isinstance(value, (dict, list)):
                rendered = json.dumps(value, ensure_ascii=False)
            else:
                rendered = value
            self.stdout.write(f"{key}: {rendered}")
        self.stdout.write("===== END_HELSSA_DIAG =====")

        if options.get("md"):
            (report_dir / "diag.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2)
            )
            md_parts = [
                "# Helssa Diagnostic Report\n",
                f"- time: `{timestamp}`\n",
                f"- version: `{report['version']}`\n\n",
                "## Summary\n",
                f"- DB connected: **{report['db'].get('connected', False)}**\n",
                f"- Pending migrations: **{report['migrations'].get('pending_total', '?')}**\n",
                f"- Health status: **{health.get('status_code')}**\n",
                f"- Ready status: **{ready.get('status_code')}**\n",
                f"- Coverage: **{report['coverage'].get('total_percent')}%**\n\n",
                "## Flags\n",
                "```\n",
                json.dumps(report["flags"], indent=2),
                "\n```\n\n",
                "## Endpoints\n",
                "```\n",
                json.dumps(report["endpoints"], indent=2, ensure_ascii=False),
                "\n```\n\n",
                "## Git\n",
                "```\n",
                json.dumps(report["git"], indent=2, ensure_ascii=False),
                "\n```\n",
            ]
            (report_dir / "diag.md").write_text("".join(md_parts))

        exit_ok = (
            report["db"].get("connected", False)
            and report["migrations"].get("pending_total") == 0
            and report["endpoints"]["/api/v1/system/ready"].get("status_code") == 200
        )
        sys.exit(0 if exit_ok else 1)
