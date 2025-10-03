from __future__ import annotations

import logging
import textwrap

from django.core.management.base import BaseCommand
from django.db import connections

logger = logging.getLogger(__name__)


def _shorten(query: str) -> str:
    return textwrap.shorten(" ".join(query.split()), width=200, placeholder="…")


class Command(BaseCommand):
    help = "Report slow logs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset pg_stat_statements after reporting.",
        )

    def handle(self, *args, **options):
        connection = connections["default"]
        if connection.vendor != "postgresql":
            self.stdout.write(
                "pg_stat_statements requires PostgreSQL; current backend is not supported."
            )
            return

        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT query, calls, total_time, mean_time
                    FROM pg_stat_statements
                    WHERE query NOT ILIKE '%%pg_stat_statements%%'
                    ORDER BY total_time DESC
                    LIMIT 10
                    """
                )
                top_total = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                top_total = [dict(zip(columns, row, strict=True)) for row in top_total]

                cursor.execute(
                    """
                    SELECT query, calls, total_time, mean_time
                    FROM pg_stat_statements
                    WHERE query NOT ILIKE '%%pg_stat_statements%%'
                    ORDER BY mean_time DESC
                    LIMIT 10
                    """
                )
                top_mean = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                top_mean = [dict(zip(columns, row, strict=True)) for row in top_mean]
            except Exception as exc:
                self.stdout.write(
                    "pg_stat_statements extension is unavailable or cannot be queried: "
                    f"{exc}.\n"
                    "Ensure it is installed with 'CREATE EXTENSION pg_stat_statements;'"
                )
                logger.info("pg_stat_statements unavailable", exc_info=exc)
                return

        def _render(title: str, rows: list[dict]) -> str:
            lines = [title]
            if not rows:
                lines.append("(no rows)")
            for idx, row in enumerate(rows, start=1):
                lines.append(
                    f"{idx:02d}. total={row['total_time']:.2f}ms "
                    f"mean={row['mean_time']:.2f}ms calls={row['calls']}:"
                )
                lines.append(f"    {_shorten(row['query'])}")
            return "\n".join(lines)

        self.stdout.write(_render("Top 10 by total time:", top_total))
        self.stdout.write("")
        self.stdout.write(_render("Top 10 by mean time:", top_mean))

        if options["reset"]:
            with connection.cursor() as cursor:
                try:
                    cursor.execute("SELECT pg_stat_statements_reset()")
                    self.stdout.write("pg_stat_statements reset.")
                except Exception as exc:
                    logger.warning("pg_stat_statements_reset failed", exc_info=exc)
