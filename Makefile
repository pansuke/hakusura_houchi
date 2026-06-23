COMPOSE := docker compose
BACKEND_SERVICE := backend
VIEWER_SERVICE := viewer

.PHONY: help local-build local-up local-down local-logs back-lint back-test front-lint front-test test lint

help:
	@printf '%s\n' \
		'Targets:' \
		'  make local-build   Build developer containers' \
		'  make local-up      Start backend and viewer' \
		'  make local-down    Stop developer containers' \
		'  make local-logs    Follow container logs' \
		'  make back-lint     Run backend lint' \
		'  make back-test     Run backend tests' \
		'  make front-lint    Run frontend type/lint checks' \
		'  make front-test    Run frontend tests'

local-build:
	$(COMPOSE) build

local-up:
	$(COMPOSE) up -d

local-down:
	$(COMPOSE) down

local-logs:
	$(COMPOSE) logs -f

back-lint:
	$(COMPOSE) run --rm $(BACKEND_SERVICE) ruff check src tests

back-test:
	$(COMPOSE) run --rm $(BACKEND_SERVICE) pytest

front-lint:
	$(COMPOSE) run --rm $(VIEWER_SERVICE) npm run lint

front-test:
	$(COMPOSE) run --rm $(VIEWER_SERVICE) npm run test

test: back-test front-test

lint: back-lint front-lint
