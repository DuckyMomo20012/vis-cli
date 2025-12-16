.PHONY: format lint check fix install test clean

# Format code with ruff
format:
	ruff format .

# Lint code with ruff
lint:
	ruff check .

# Check both formatting and linting
check:
	ruff format --check .
	ruff check .

# Fix auto-fixable issues
fix:
	ruff check --fix .
	ruff format .

# Install all dependencies (including dev)
install:
	uv sync

# Run tests
test:
	pytest -v

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
