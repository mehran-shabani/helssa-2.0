#!/usr/bin/env python3
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"

def latest_tag() -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return "v2.0.0"

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
