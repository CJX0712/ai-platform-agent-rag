# 作者：晨星
# 注意：Windows 使用 .venv/Scripts/python，Linux/macOS 使用 .venv/bin/python

PY ?= .venv/Scripts/python
IMAGE ?= ai-platform-agent-rag:0.1.0

.PHONY: install lint test run smoke docker-build docker-up docker-down clean

install:
	python -m venv .venv
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements.txt pytest==8.3.4 ruff==0.8.4
	$(PY) -m pip freeze > requirements.lock

lint:
	$(PY) -m ruff check ai_platform apps tests

test:
	$(PY) -m pytest -q

run:
	$(PY) -m apps.api.main

smoke:
	$(PY) - <<'EOF'
import urllib.request, urllib.error
print(urllib.request.urlopen("http://127.0.0.1:8000/health").read().decode())
EOF

docker-build:
	docker build -t $(IMAGE) .

docker-up:
	docker compose -f deploy/docker-compose.yml up -d --build

docker-down:
	docker compose -f deploy/docker-compose.yml down

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
