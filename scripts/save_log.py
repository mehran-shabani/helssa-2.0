#!/usr/bin/env python3
"""Save diagnostic logs to docs/PROJECT_LOG.md and project_logs/."""

from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture logs into docs/PROJECT_LOG.md and project_logs/.")
    parser.add_argument("--tag", help="Optional short label for the log section.")
    parser.add_argument("--input", help="Read log content from a file instead of STDIN.")
    parser.add_argument("--commit", action="store_true", help="Create a local git commit after saving the log.")
    return parser.parse_args()


def read_content(input_path: str | None) -> str | None:
    if input_path:
        path = Path(input_path)
        if not path.exists():
            print(f"Input file not found: {input_path}", file=sys.stderr)
            return None
        return path.read_text(encoding="utf-8")

    data = sys.stdin.read()
    if data == "":
        return None
    return data


def normalize_newlines(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def ensure_directories() -> tuple[Path, Path]:
    docs_dir = Path("docs")
    logs_dir = Path("project_logs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir, logs_dir


def append_markdown(doc_path: Path, timestamp: str, tag: str, content: str) -> None:
    header = f"## {timestamp} — {tag or 'log'}\n"
    block = f"```text\n{content}\n```\n"

    needs_separator = doc_path.exists() and doc_path.stat().st_size > 0
    with doc_path.open("a", encoding="utf-8") as doc:
        if needs_separator:
            doc.write("\n\n")
        doc.write(header)
        doc.write(block)


def write_raw_log(logs_dir: Path, timestamp: _dt.datetime, content: str) -> Path:
    filename = f"log_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    raw_path = logs_dir / filename
    raw_path.write_text(content, encoding="utf-8")
    return raw_path


def maybe_commit(paths: list[Path]) -> None:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Skipping git commit: not inside a git repository or git not installed.", file=sys.stderr)
        return

    files = [str(path) for path in paths]
    subprocess.run(["git", "add", *files], check=False)
    subprocess.run(
        ["git", "commit", "-m", "[skip ci] chore(log): update PROJECT_LOG.md"],
        check=False,
    )


def main() -> int:
    args = parse_args()
    content = read_content(args.input)

    if content in (None, ""):
        if content is None and args.input:
            return 1
        source = "STDIN or --input file"
        print(f"No log content received. Provide input via {source}.", file=sys.stderr)
        return 1

    content = normalize_newlines(content)

    docs_dir, logs_dir = ensure_directories()
    doc_path = docs_dir / "PROJECT_LOG.md"

    timestamp_dt = _dt.datetime.now(tz=_dt.timezone.utc)
    timestamp_str = timestamp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    append_markdown(doc_path, timestamp_str, args.tag or "log", content)
    raw_path = write_raw_log(logs_dir, timestamp_dt, content)

    print(f"Log saved to {doc_path} and {raw_path}")

    if args.commit:
        maybe_commit([doc_path, raw_path])

    return 0


if __name__ == "__main__":
    sys.exit(main())
