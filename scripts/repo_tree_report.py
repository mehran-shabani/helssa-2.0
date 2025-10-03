#!/usr/bin/env python3
"""Generate a repository structure report in Markdown."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess

IGNORE_DIRS = {".git", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules", "dist", "build", "htmlcov", ".reports", "project_logs", ".pytest_cache", ".venv", "venv"}
KIND_MAP = {".py": "Python", ".md": "Markdown", ".rst": "ReST", ".txt": "Text", ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".ini": "INI", ".cfg": "Config", ".env": "Env", ".sh": "Shell"}
NOTABLE_CONFIGS = ["pyproject.toml", "README.md", "Dockerfile", "Makefile", "pytest.ini", "ruff.toml", ".editorconfig", ".env.example"]
URL_REGEX = re.compile(r"(?:path|re_path)\(\s*[rR]?[\"']([^\"']+)")

def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            yield Path(dirpath) / name

def human_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{value:.1f} GB"

def build_tree(root, max_depth):
    def walk(path, prefix, depth, out):
        if depth >= max_depth:
            return
        entries = sorted([p for p in path.iterdir() if p.name not in IGNORE_DIRS], key=lambda p: (p.is_file(), p.name.lower()))
        for idx, entry in enumerate(entries):
            branch = "└── " if idx == len(entries) - 1 else "├── "
            out.append(f"{prefix}{branch}{entry.name}")
            if entry.is_dir():
                walk(entry, prefix + ("    " if idx == len(entries) - 1 else "│   "), depth + 1, out)

    lines = [root.name or "."]
    walk(root, "", 0, lines)
    return "\n".join(lines)

def run_cmd(args):
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip()
    except OSError:
        return 1, ""

def git_info(root):
    version = os.getenv("HELSSA_VERSION")
    branch = "unknown"
    commits = []
    if not version:
        code, out = run_cmd(["git", "-C", str(root), "describe", "--tags", "--abbrev=0"])
        if code == 0 and out:
            version = out
        else:
            code, out = run_cmd(["git", "-C", str(root), "tag", "--sort=-creatordate"])
            version = out.splitlines()[0] if code == 0 and out else "v0.0.0"
    code, out = run_cmd(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0 and out:
        branch = out
    code, out = run_cmd(["git", "-C", str(root), "log", "-5", "--pretty=format:%h %s"])
    if code == 0 and out:
        commits = out.splitlines()
    return version or "v0.0.0", branch, commits

def truncate(text, width=80):
    if len(text) <= width:
        return text
    keep = width - 3
    left = keep // 2
    right = keep - left
    return f"{text[:left]}...{text[-right:]}"

def collect_data(root):
    files = []
    summary = {"total_files": 0, "total_size": 0, "total_loc": 0, "python_files": 0, "test_files": 0}
    url_map = {}
    for abs_path in iter_files(root):
        rel = abs_path.relative_to(root).as_posix()
        try:
            size = abs_path.stat().st_size
        except OSError:
            continue
        kind = KIND_MAP.get(abs_path.suffix.lower(), abs_path.suffix[1:].upper() if abs_path.suffix else "Other")
        try:
            text = abs_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = None
        loc = text.count("\n") + (1 if text and not text.endswith("\n") else 0) if text else 0
        note = ""
        if text:
            if kind == "Python":
                try:
                    doc = ast.get_docstring(ast.parse(text))
                    if doc:
                        note = " ".join(doc.split())
                    else:
                        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
                        note = first.lstrip("# ") if first.startswith("#") else ""
                except SyntaxError:
                    pass
            elif kind == "Markdown":
                heading = next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("#")), "")
                if heading:
                    note = heading.lstrip("# ").strip()
            elif kind in {"YAML", "TOML", "INI", "Config"}:
                comment = next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("#")), "")
                if comment:
                    note = comment.lstrip("# ")
            if abs_path.name == "urls.py":
                matches = URL_REGEX.findall(text)
                if matches:
                    url_map[rel] = matches
        files.append((rel, kind, loc, size, note))
        summary["total_files"] += 1
        summary["total_size"] += size
        summary["total_loc"] += loc
        if kind == "Python":
            summary["python_files"] += 1
            if "test" in rel.lower():
                summary["test_files"] += 1
    return files, summary, url_map

def generate_report(root, out_path, max_depth, limit, sort_key, show_tree, show_table):
    files, summary, url_map = collect_data(root)
    version, branch, commits = git_info(root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [f"# Repository Structure Report ({timestamp})", "", f"- **Version:** {version}", f"- **Branch:** {branch}"]
    if commits:
        lines.append("- **Recent commits:**")
        lines.extend(f"  - {c}" for c in commits)
    lines.extend(["", "## Summary", "| Metric | Value |", "| --- | --- |", f"| Total files | {summary['total_files']} |", f"| Total size | {human_size(summary['total_size'])} |", f"| Total LOC | {summary['total_loc']} |", f"| Python files | {summary['python_files']} |", f"| Test files | {summary['test_files']} |"])
    if show_tree:
        lines.extend(["", "## Tree View", "```text", build_tree(root, max_depth), "```"])
    if show_table:
        key_funcs = {
            "path": lambda item: item[0],
            "loc": lambda item: (-item[2], item[0]),
            "size": lambda item: (-item[3], item[0]),
        }
        ordered = sorted(files, key=key_funcs[sort_key])
        truncated = len(ordered) > limit
        rows = ordered[:limit]
        lines.extend(["", "## Files", "| Path | Kind | LOC | Size | Note |", "| --- | --- | --- | --- | --- |"])
        for rel, kind, loc, size, note in rows:
            lines.append(f"| {truncate(rel)} | {kind} | {loc} | {human_size(size)} | {truncate(note)} |")
        if truncated:
            lines.extend(["", f"_Table truncated to first {limit} files._"])
    configs = [cfg for cfg in NOTABLE_CONFIGS if (root / cfg).exists()]
    workflows = root / ".github" / "workflows"
    if workflows.exists():
        configs += [str(p.relative_to(root)) for p in workflows.glob("*.yml")]
    configs += [str(p.relative_to(root)) for p in root.glob("docker-compose*.yml")]
    if configs:
        lines.append("")
        lines.append("## Notable Configs")
        for cfg in sorted(configs):
            lines.append(f"- `{cfg}`")
    if url_map:
        lines.append("")
        lines.append("## URL Patterns (Quick Scan)")
        for rel in sorted(url_map):
            lines.append(f"- `{rel}`")
            for pattern in url_map[rel]:
                lines.append(f"  - `{pattern}`")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate repository structure report")
    parser.add_argument("--out", default="docs/REPO_STRUCTURE.md", help="Output Markdown path")
    parser.add_argument("--max-depth", type=int, default=6, help="Maximum depth for tree view")
    parser.add_argument("--limit", type=int, default=2000, help="Maximum number of files in table")
    parser.add_argument("--sort", choices=["path", "loc", "size"], default="path", help="Sort column for file table")
    parser.add_argument("--no-tree", action="store_true", help="Disable tree view")
    parser.add_argument("--no-table", action="store_true", help="Disable file table")
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    root = Path.cwd()
    generate_report(root, root / args.out, args.max_depth, args.limit, args.sort, not args.no_tree, not args.no_table)


if __name__ == "__main__":
    main()
