import json
import logging
import subprocess
import warnings
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command

REPORT_DIR = Path(".reports")
DOC_PATH = Path("docs/DIAG.md")


class Command(BaseCommand):
    help = "Refresh diagnostic artifacts and write docs/DIAG.md (optionally committing the result)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Stage the generated files and create a local commit.",
        )

    def handle(self, *args, **options):
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        if hasattr(settings, "ALLOWED_HOSTS"):
            hosts = list(getattr(settings, "ALLOWED_HOSTS", []))
            if "testserver" not in hosts:
                hosts.append("testserver")
                settings.ALLOWED_HOSTS = hosts

        buffer = StringIO()
        warnings.filterwarnings(
            "ignore",
            message="No directory at: .*staticfiles/",
            category=UserWarning,
        )
        logging.disable(logging.CRITICAL)
        try:
            call_command("diag_probe", "--md", stdout=buffer, stderr=buffer)
        except SystemExit:
            # diag_probe exits non-zero when the system is degraded; we still continue.
            pass
        finally:
            logging.disable(logging.NOTSET)

        report_path = REPORT_DIR / "diag.json"
        data = {}
        try:
            data = json.loads(report_path.read_text())
        except Exception:
            data = {}

        generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        version = str(data.get("version") or "unknown")
        settings_module = str(
            data.get("settings")
            or getattr(settings, "DJANGO_SETTINGS_MODULE", None)
            or "unknown"
        )

        db_info = data.get("db") or {}
        db_connected = bool(db_info.get("connected")) if db_info else False

        migrations = data.get("migrations") or {}
        pending_total = migrations.get("pending_total")
        has_pending = isinstance(pending_total, int) and pending_total > 0

        endpoints = data.get("endpoints") or {}
        health_status = _extract_status(endpoints.get("/health"))
        ready_status = _extract_status(endpoints.get("/api/v1/system/ready"))

        coverage = data.get("coverage") or {}
        coverage_percent = coverage.get("total_percent")
        coverage_display = (
            f"{coverage_percent:.2f}" if isinstance(coverage_percent, (int, float)) else "?"
        )

        badge = "OK" if db_connected and ready_status == 200 and not has_pending else "DEGRADED"
        pending_display = (
            str(pending_total)
            if isinstance(pending_total, int)
            else ("?" if pending_total is None else str(pending_total))
        )

        DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

        flags_json = json.dumps(data.get("flags") or {}, indent=2, ensure_ascii=False, sort_keys=True)
        git_json = json.dumps(data.get("git") or {}, indent=2, ensure_ascii=False, sort_keys=True)
        raw_json = json.dumps(data or {}, indent=2, ensure_ascii=False, sort_keys=True)

        lines = [
            "# Helssa Diagnostics\n\n",
            f"> Status: **{badge}**\n\n",
            f"- Generated (UTC): `{generated}`\n",
            f"- Version: `{version}`\n",
            f"- Settings module: `{settings_module}`\n\n",
            "## Summary\n",
            "| Health | Ready | DB Connected | Pending Migrations | Coverage (%) |\n",
            "| --- | --- | --- | --- | --- |\n",
            f"| {health_status} | {ready_status} | {db_connected} | {pending_display} | {coverage_display} |\n\n",
            "## Flags\n",
            "```json\n",
            f"{flags_json}\n",
            "```\n\n",
            "## Git\n",
            "```json\n",
            f"{git_json}\n",
            "```\n\n",
            "<details>\n<summary>Raw diag.json</summary>\n\n",
            "```json\n",
            f"{raw_json}\n",
            "```\n\n",
            "</details>\n",
        ]

        DOC_PATH.write_text("".join(lines))

        if options.get("commit"):
            paths = [str(DOC_PATH)]
            if report_path.exists():
                paths.append(str(report_path))
            try:
                subprocess.check_call(["git", "add", *paths])
                subprocess.check_call([
                    "git",
                    "commit",
                    "-m",
                    "[skip ci] chore(diag): update DIAG.md",
                ])
            except subprocess.CalledProcessError:
                # Ignore git errors (e.g., nothing to commit) while keeping the command successful.
                pass

        self.stdout.write("Wrote docs/DIAG.md")

def _extract_status(endpoint_data):
    if isinstance(endpoint_data, dict):
        status = endpoint_data.get("status_code")
        return status if status is not None else "?"
    return "?"
