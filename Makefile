.PHONY: help install test lint format clean run validate docker-build docker-run

# Default Python and pip commands
PYTHON := python3.11
PIP := pip3.11
VENV_DIR := venv

help: ## Show this help message
	@echo "Cway MCP Server - Development Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install dependencies and setup development environment
	@echo "🔧 Setting up development environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(VENV_DIR)/bin/pip install pre-commit
	$(VENV_DIR)/bin/pre-commit install
	@echo "✅ Development environment ready!"

test: ## Run tests with coverage
	@echo "🧪 Running tests..."
	$(VENV_DIR)/bin/pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	@echo "👀 Running tests in watch mode..."
	$(VENV_DIR)/bin/pytest-watch tests/ -v --cov=src

lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	$(VENV_DIR)/bin/flake8 src tests
	$(VENV_DIR)/bin/mypy src

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	$(VENV_DIR)/bin/black src tests *.py
	$(VENV_DIR)/bin/isort src tests *.py

format-check: ## Check if code formatting is correct
	@echo "✅ Checking code formatting..."
	$(VENV_DIR)/bin/black --check src tests *.py
	$(VENV_DIR)/bin/isort --check-only src tests *.py

validate: ## Run all validation checks (lint, format, test)
	@echo "🚀 Running all validation checks..."
	$(MAKE) format-check
	$(MAKE) lint  
	$(MAKE) test
	@echo "✅ All checks passed!"

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf $(VENV_DIR)
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run: ## Run the MCP server
	@echo "🚀 Starting Cway MCP Server..."
	$(VENV_DIR)/bin/python run_server.py

validate-setup: ## Validate project setup and configuration
	@echo "🔧 Validating setup..."
	$(VENV_DIR)/bin/python validate_setup.py

explore-api: ## Explore the Cway GraphQL API
	@echo "🔍 Exploring Cway API..."
	$(VENV_DIR)/bin/python explore_api.py

test-api: ## Test API queries
	@echo "🧪 Testing API queries..."
	$(VENV_DIR)/bin/python test_correct_queries.py

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t cway-mcp-server .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run --env-file .env -p 8000:8000 cway-mcp-server

dev: install ## Setup development environment (alias for install)

ci: format-check lint test ## Run CI pipeline checks

# Development server with auto-reload
dev-server: ## Run development server with auto-reload
	@echo "🔥 Starting development server..."
	$(VENV_DIR)/bin/watchmedo auto-restart \
		--patterns="*.py" \
		--recursive \
		--signal SIGTERM \
		$(VENV_DIR)/bin/python run_server.py