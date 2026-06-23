COMPOSE := docker compose
BACKEND_SERVICE := backend
VIEWER_SERVICE := viewer

.PHONY: help local-build local-up local-down local-logs back-lint back-test back-coverage coverage-report front-lint front-test front-coverage data-build data-validate test lint coverage

help:
	@printf '%s\n' \
		'Targets:' \
		'  make local-build   Build developer containers' \
		'  make local-up      Start backend and viewer' \
		'  make local-down    Stop developer containers' \
		'  make local-logs    Follow container logs' \
		'  make back-lint     Run backend lint' \
		'  make back-test     Run backend tests' \
		'  make back-coverage Run backend coverage with inspector' \
		'  make front-lint    Run frontend type/lint checks' \
		'  make front-test    Run frontend tests' \
		'  make front-coverage Run frontend coverage' \
		'  make data-build    Build generated master data' \
		'  make data-validate Validate master data without changing output' \
		'  make coverage      Run backend and frontend coverage'

local-build:
	$(COMPOSE) build

local-up:
	$(COMPOSE) up -d

local-down:
	$(COMPOSE) down

local-logs:
	$(COMPOSE) logs -f

back-lint:
	$(COMPOSE) run --rm -e RUFF_CACHE_DIR=/tmp/lane-relay-ruff-cache $(BACKEND_SERVICE) ruff check src tests

back-test:
	$(COMPOSE) run --rm $(BACKEND_SERVICE) pytest -o cache_dir=/tmp/lane-relay-pytest-cache

back-coverage:
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage $(BACKEND_SERVICE) coverage erase
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage $(BACKEND_SERVICE) coverage run --source=src/lane_relay -m pytest -o cache_dir=/tmp/lane-relay-pytest-cache
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage $(BACKEND_SERVICE) coverage report --fail-under=85
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage $(BACKEND_SERVICE) python /workspace/tools/coverage_inspector.py

coverage-report:
	$(COMPOSE) run --rm -e COVERAGE_FILE=/workspace/.coverage $(BACKEND_SERVICE) python /workspace/tools/coverage_inspector.py

front-lint:
	$(COMPOSE) run --rm $(VIEWER_SERVICE) npm run lint

front-test:
	$(COMPOSE) run --rm $(VIEWER_SERVICE) npm run test

front-coverage:
	$(COMPOSE) run --rm $(VIEWER_SERVICE) npm run coverage

data-build:
	$(COMPOSE) run --rm $(BACKEND_SERVICE) python /workspace/tools/build_data.py --source /workspace/data/source --schemas /workspace/schemas --output /workspace/data/generated/game-data.json

data-validate:
	$(COMPOSE) run --rm $(BACKEND_SERVICE) python /workspace/tools/build_data.py --source /workspace/data/source --schemas /workspace/schemas --output /tmp/lane-relay-game-data.json

test: back-test front-test

lint: back-lint front-lint data-validate

coverage: back-coverage front-coverage
