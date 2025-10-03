.PHONY: install run celery test lint format migrate redis-up redis-down save-log save-log-file save-log-commit

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

.PHONY: redis-up redis-down

redis-up:
        docker compose -f docker-compose.dev.yml up -d redis

redis-down:
        docker compose -f docker-compose.dev.yml down --remove-orphans

.PHONY: diag
diag:
        python manage.py diag_probe --md || true
        @echo "Report at .reports/diag.md (and JSON at .reports/diag.json). Copy STDOUT between markers here."

FILE_REQUIRED_MESSAGE := FILE variable is required. Usage: make save-log-file FILE=path/to/log.txt

save-log:
	python scripts/save_log.py $(if $(TAG),--tag "$(TAG)",)

save-log-file:
ifndef FILE
	$(error $(FILE_REQUIRED_MESSAGE))
endif
	python scripts/save_log.py --input "$(FILE)" $(if $(TAG),--tag "$(TAG)",)

save-log-commit:
	python scripts/save_log.py $(if $(TAG),--tag "$(TAG)",) --commit
