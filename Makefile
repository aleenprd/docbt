.PHONY: help build run stop clean test dev prod lint format check ci install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Development
install: ## Install dependencies with uv
	uv pip install -e ".[all-providers,dev]"

env: ## Create .env file from .env.example (keeping section headers)
	@if [ -f .env ]; then \
		echo "⚠️  .env file already exists!"; \
		printf "Do you want to overwrite it? [y/N] "; \
		read reply; \
		case "$$reply" in \
			[Yy]*) \
				awk '/^###/ {print; next} /^#/ {next} /^$$/ {next} {sub(/ *#.*/, ""); if (length($$0) > 0) print}' .env.example > .env; \
				echo "✅ .env file created from .env.example (section headers preserved)"; \
				echo "📝 Please edit .env and add your credentials"; \
				;; \
			*) \
				echo "❌ Skipped. Existing .env file preserved."; \
				;; \
		esac \
	else \
		awk '/^###/ {print; next} /^#/ {next} /^$$/ {next} {sub(/ *#.*/, ""); if (length($$0) > 0) print}' .env.example > .env; \
		echo "✅ .env file created from .env.example (section headers preserved)"; \
		echo "📝 Please edit .env and add your credentials"; \
	fi

lint: ## Run ruff linter
	ruff check .

format: ## Format code with ruff
	ruff format .

format-check: ## Check code formatting
	ruff format --check .

check: format-check lint ## Run all checks (format + lint)

test: ## Run tests with pytest
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=src/docbt --cov-report=term --cov-report=html

ci: check test-cov ## Run all CI checks locally

pre-commit: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

# Docker


build: ## Build base Docker image
	docker build --target base -t docbt:base .

build-nocache: ## Build base Docker image without cache
	docker build --no-cache --target base -t docbt:base .

build-prod: ## Build production Docker image
	docker build --target production -t docbt:production .

build-prod-nocache: ## Build production Docker image without cache
	docker build --no-cache --target production -t docbt:production .

build-dev: ## Build development Docker image
	docker build --target development -t docbt:dev .

build-dev-nocache: ## Build development Docker image without cache
	docker build --no-cache --target development -t docbt:dev .

rebuild: ## Rebuild base image with latest code (no cache)
	@echo "🔨 Rebuilding Docker image with latest code..."
	docker build --no-cache --target base -t docbt:base .
	@echo "✅ Rebuild complete! Use 'make run' to start the container."

rebuild-prod: ## Rebuild production image with latest code (no cache)
	@echo "🔨 Rebuilding production Docker image with latest code..."
	docker build --no-cache --target production -t docbt:production .
	@echo "✅ Rebuild complete!"

rebuild-dev: ## Rebuild development image with latest code (no cache)
	@echo "🔨 Rebuilding development Docker image with latest code..."
	docker build --no-cache --target development -t docbt:dev .
	@echo "✅ Rebuild complete!"

rebuild-run: ## Rebuild and run (stops old container, rebuilds, starts new one)
	@echo "🛑 Stopping existing containers..."
	-docker compose down
	@echo "🔨 Rebuilding with latest code (no cache)..."
	docker build --no-cache --target base -t docbt:base .
	@echo "🚀 Starting container with fresh image..."
	docker compose up docbt

run: ## Run docbt with docker-compose (rebuilds if needed)
	docker compose up --build docbt

run-bg: ## Run docbt in background
	docker compose up -d docbt

prod: ## Run production version
	docker compose --profile production up docbt-production

prod-bg: ## Run production in background
	docker compose --profile production up -d docbt-production

dev: ## Run development version
	docker compose --profile dev up docbt-dev

stop: ## Stop all running containers
	docker compose down

restart: ## Restart containers
	docker compose restart

logs: ## Show container logs
	docker compose logs -f docbt

clean: ## Remove containers and images
	docker compose down
	docker rmi docbt:base docbt:production docbt:dev || true

clean-all: ## Remove everything including volumes
	docker compose down -v
	docker rmi docbt:base docbt:production docbt:dev || true
	docker system prune -f

test-docker: ## Run tests in container
	docker run --rm docbt:dev pytest

shell: ## Open shell in container
	docker run --rm -it docbt:base /bin/bash

inspect: ## Inspect base image
	docker inspect docbt:base

size: ## Show image sizes
	docker images | grep docbt

health: ## Check container health
	docker inspect --format='{{.State.Health.Status}}' docbt || echo "Container not running"

# Package building
build-package: ## Build Python package
	uv build

check-package: ## Check package with twine
	uv pip install --system twine
	twine check dist/*

clean-package: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info

# Version management
version: ## Show current version
	@bump-my-version show current_version

version-info: ## Show detailed version information
	@bump-my-version show-bump

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	bump-my-version bump patch

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	bump-my-version bump minor

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	bump-my-version bump major

bump-dry-run: ## Dry run version bump (usage: make bump-dry-run PART=patch)
	@if [ -z "$(PART)" ]; then \
		echo "Usage: make bump-dry-run PART=patch|minor|major"; \
		exit 1; \
	fi
	bump-my-version bump $(PART) --dry-run --verbose
