VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install test lint typecheck coverage format up down logs clean lighthouse

help:
	@echo 'Available commands:'
	@echo '  make install    - create venv and install dependencies'
	@echo '  make test       - run pytest'
	@echo '  make lint       - run ruff'
	@echo '  make typecheck  - run mypy'
	@echo '  make coverage   - run tests with coverage (>= 80%)'
	@echo '  make format     - format code with ruff'
	@echo '  make up         - docker compose up'
	@echo '  make down       - docker compose down'
	@echo '  make logs       - docker compose logs'
	@echo '  make lighthouse - frontend perf audit (Lighthouse; stack up on :3071)'

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

install: $(VENV)/bin/activate

test: install
	$(VENV)/bin/pytest backend/tests -q

lint: install
	$(VENV)/bin/ruff check backend

typecheck: install
	$(VENV)/bin/mypy backend/app

coverage: install
	$(VENV)/bin/pytest backend/tests --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=0.8 -q

format: install
	$(VENV)/bin/ruff format backend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f app db

lighthouse:
	cd tests/performance/lighthouse && npx --yes @lhci/cli@0.14.0 --config=lighthouserc.json autorun

clean:
	rm -rf .venv
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
