#!/usr/bin/env python3
import pathlib
import re
import subprocess
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
DEFAULT_BASE_TAG = "v2.2.0"


def _candidate_tags() -> Iterable[str]:
    try:
        output = subprocess.check_output(
            ["git", "tag", "--list", "v[0-9]*.[0-9]*.[0-9]*"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def latest_released_tag() -> str | None:
    parsed: list[tuple[int, int, int, str]] = []
    for tag in _candidate_tags():
        match = VERSION_RE.fullmatch(tag)
        if match:
            major, minor, patch = map(int, match.groups())
            parsed.append((major, minor, patch, tag))
    if not parsed:
        return None
    return max(parsed, key=lambda item: (item[0], item[1], item[2]))[3]


def latest_tag() -> str:
    return latest_released_tag() or DEFAULT_BASE_TAG

def bump_minor(tag: str) -> str:
    m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not m:
        raise SystemExit(f"Bad tag: {tag}")
    major, minor = int(m.group(1)), int(m.group(2)) + 1
    return f"v{major}.{minor}.0"

def set_pyproject_version(v: str):
    txt = PYPROJECT.read_text()
    txt = re.sub(r'(?m)^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"', f'version = "{v[1:]}"', txt)
    PYPROJECT.write_text(txt)

def main():
    cur = latest_tag()
    nxt = bump_minor(cur)
    set_pyproject_version(nxt)
    print(nxt)

if __name__ == "__main__":
    main()
