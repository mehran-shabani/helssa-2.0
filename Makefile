.PHONY: install run celery test lint format migrate redis-up redis-down save-log save-log-file save-log-commit repo-struct repo-struct-out

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
        DJANGO_SETTINGS_MODULE=config.settings.test BITPAY_WEBHOOK_SECRET=test pytest

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

.PHONY: diag diag-commit
diag:
        python manage.py diag_write

diag-commit:
        python manage.py diag_write --commit

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

repo-struct:
	python scripts/repo_tree_report.py

repo-struct-out:
	python scripts/repo_tree_report.py --out docs/REPO_STRUCTURE.md
