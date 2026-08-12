# AnyFactor — common development tasks
#
# Usage:
#   make help
#   make install
#   make backend          # Flask on :5000 (uses backend/venv)
#   make frontend         # React on :3000
#   make dev              # both (parallel)

ROOT        := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BACKEND     := $(ROOT)/backend
FRONTEND    := $(ROOT)/frontend
VENV        := $(BACKEND)/venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
PY          := python3

.DEFAULT_GOAL := help

.PHONY: help install install-backend install-frontend env backend frontend dev clean

help: ## Show available targets
	@echo "AnyFactor"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Create venv + install backend & frontend deps

install-backend: ## Create backend/venv and pip install requirements
	@if [ ! -x "$(PYTHON)" ]; then \
		echo "Creating virtualenv at $(VENV)"; \
		$(PY) -m venv "$(VENV)"; \
	fi
	"$(PIP)" install --upgrade pip
	"$(PIP)" install -r "$(BACKEND)/requirements.txt"
	@echo "Backend ready → $(PYTHON)"

install-frontend: ## npm install in frontend/
	cd "$(FRONTEND)" && npm install

env: ## Copy .env.example files if missing (does not overwrite)
	@if [ ! -f "$(BACKEND)/.env" ]; then \
		cp "$(BACKEND)/.env.example" "$(BACKEND)/.env"; \
		echo "Created backend/.env — edit API keys before running"; \
	else \
		echo "backend/.env already exists"; \
	fi
	@if [ ! -f "$(FRONTEND)/.env" ]; then \
		printf '%s\n' \
			'REACT_APP_API_URL=http://localhost:5000' \
			'REACT_APP_EXTRACT_API_KEY=' \
			> "$(FRONTEND)/.env"; \
		echo "Created frontend/.env — set REACT_APP_EXTRACT_API_KEY to match EXTRACT_API_KEY"; \
	else \
		echo "frontend/.env already exists"; \
	fi

backend: ## Run Flask API (http://127.0.0.1:5000)
	@test -x "$(PYTHON)" || (echo "Missing venv. Run: make install-backend" && exit 1)
	cd "$(BACKEND)" && "$(PYTHON)" app.py

frontend: ## Run React dev server (http://localhost:3000)
	cd "$(FRONTEND)" && npm start

dev: ## Run backend + frontend together
	@test -x "$(PYTHON)" || (echo "Missing venv. Run: make install" && exit 1)
	@$(MAKE) -j2 backend frontend

clean: ## Remove Python caches and frontend build output
	find "$(BACKEND)" -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf "$(FRONTEND)/build"
