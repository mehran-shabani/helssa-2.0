#!/usr/bin/env python3
import datetime
import pathlib
import re
import subprocess
from collections.abc import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

def last_tag() -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return ""

def commits_since(tag: str) -> list[str]:
    command = ["git", "log", "--pretty=%s"]
    if tag:
        command.append(f"{tag}..")
    out = subprocess.check_output(command, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]

def group(commits: Iterable[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "feat": [],
        "fix": [],
        "chore": [],
        "docs": [],
        "test": [],
        "other": [],
    }
    for commit in commits:
        match = re.match(r"^(\w+)(\(.+\))?:\s*(.+)", commit)
        key = match.group(1) if match else "other"
        categories.get(key, categories["other"]).append(commit)
    return categories

def write_section(version: str, groups: dict[str, list[str]]) -> None:
    date = datetime.date.today().isoformat()
    lines = [f"## {version} - {date}\n"]
    for section in ["feat", "fix", "chore", "docs", "test", "other"]:
        commits = groups.get(section, [])
        if commits:
            lines.append(f"### {section}\n")
            for commit in commits:
                lines.append(f"- {commit}\n")
            lines.append("\n")
    content = "".join(lines)
    previous = CHANGELOG.read_text() if CHANGELOG.exists() else "# Changelog\n\n"
    CHANGELOG.write_text(previous + content)

if __name__ == "__main__":
    tag = last_tag()
    grouped = group(commits_since(tag))
    ver = subprocess.check_output(["python", "scripts/bump_version.py"], text=True).strip()
    write_section(ver, grouped)
