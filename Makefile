# Makefile for Rate Limiter API

.PHONY: help run test load-test build run-docker docker-up docker-down clean install deps

# Default values
PORT ?= 8000
REDIS_HOST ?= localhost
REDIS_PORT ?= 6379

help:
	@echo "Available commands:"
	@echo "  make install/deps   - Install Python dependencies with uv"
	@echo "  make run            - Run the FastAPI server"
	@echo "  make test           - Run the limiter tests"
	@echo "  make load-test      - Run Locust load tests"
	@echo "  make build          - Build Docker image"
	@echo "  make run-docker     - Run the API in Docker"
	@echo "  make docker-up      - Start API and Redis in Docker Compose"
	@echo "  make docker-down    - Stop Docker Compose services"
	@echo "  make clean          - Clean up build artifacts"

install deps:
	@echo "Installing dependencies with uv..."
	uv sync

run:
	@echo "Starting FastAPI server on port $(PORT)..."
	@REDIS_HOST=$(REDIS_HOST) REDIS_PORT=$(REDIS_PORT) \
	uv run python -m uvicorn main:app --host 0.0.0.0 --port $(PORT) --reload

test:
	@echo "Running limiter tests..."
	@echo "Make sure Redis is running at $(REDIS_HOST):$(REDIS_PORT)"
	uv run python test_limiter.py

load-test:
	@echo "Starting Locust load test UI..."
	@echo "Open http://localhost:8089 in your browser"
	uv run locust -f locust_load_test.py --host http://localhost:$(PORT)

load-test-headless:
	@echo "Running headless load test..."
	uv run locust -f locust_load_test.py --host http://localhost:$(PORT) \
		--users 100 --spawn-rate 10 --run-time 60s --csv results

build:
	@echo "Building Docker image..."
	docker build -t rate-limiter-api:latest .

run-docker: build
	@echo "Running API container..."
	@docker run -it --rm \
		-p $(PORT):8000 \
		-e REDIS_HOST=$(REDIS_HOST) \
		-e REDIS_PORT=$(REDIS_PORT) \
		--network host \
		rate-limiter-api:latest

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker Compose services..."
	docker-compose down

clean:
	@echo "Cleaning up..."
	rm -rf .venv __pycache__ .pytest_cache *.pyc
	rm -rf results.csv stats.csv history.csv
	@echo "Cleanup complete"

redis-check:
	@echo "Checking Redis connection..."
	@redis-cli -h $(REDIS_HOST) -p $(REDIS_PORT) ping && echo "Redis is running" || echo "Redis is not running"

.PHONY: venv
venv:
	@echo "Creating virtual environment with uv..."
	uv venv && uv sync
