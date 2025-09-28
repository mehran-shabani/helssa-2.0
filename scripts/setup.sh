#!/usr/bin/env bash
set -euo pipefail

# Python env
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip

# Create project from files provided by the patch (after you apply them)
pip install -e .
pip install pre-commit
pre-commit install

# Django initial setup
export DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py migrate
python manage.py check

# Seed baseline tag v2.0.0 if none exists
if ! git describe --tags --abbrev=0 >/dev/null 2>&1; then
  git add -A
  git commit -m "chore: bootstrap helssa backend (v2.0.0 seed)"
  git tag v2.0.0
  git push --tags || true
fi

echo "Bootstrap complete. Next merge to main will release v2.1.0."
