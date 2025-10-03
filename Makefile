.PHONY: install run celery test lint format migrate

install:
	python -m pip install --upgrade pip
	pip install -e .[dev]
	pip install pre-commit
	pre-commit install

run:
	DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver 0.0.0.0:8000

celery:
	celery -A config.celery:app worker -l info

test:
	DJANGO_SETTINGS_MODULE=config.settings.test pytest -q

lint:
	ruff check .
	isort --check-only .

format:
	isort .

migrate:
        DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py migrate

.PHONY: diag
diag:
	python manage.py diag_probe --md || true
	@echo "Report at .reports/diag.md (and JSON at .reports/diag.json). Copy STDOUT between markers here."
