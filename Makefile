VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install test lint typecheck format up down logs clean

help:
	@echo 'Available commands:'
	@echo '  make install    - create venv and install dependencies'
	@echo '  make test       - run pytest'
	@echo '  make lint       - run ruff'
	@echo '  make typecheck  - run mypy'
	@echo '  make format     - format code with ruff'
	@echo '  make up         - docker compose up'
	@echo '  make down       - docker compose down'
	@echo '  make logs       - docker compose logs'

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

format: install
	$(VENV)/bin/ruff format backend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f app db

clean:
	rm -rf .venv
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
