.DEFAULT_GOAL := help

PYTHON := python
PYTEST := pytest
MKDOCS := mkdocs

.PHONY: help clean test coverage figures docs site env

help: ## Show available make targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean: ## Remove caches and generated artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov site figures .coverage .coverage.*
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

test: ## Run the test suite
	$(PYTEST)

coverage: ## Run tests with a coverage report
	$(PYTEST) --cov=lorenzsw --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml

figures: ## Generate paper figures
	$(PYTHON) scripts/generate_all_figures.py

docs: ## Build the docs site into site/
	$(MKDOCS) build

site: docs ## Alias for docs

env: ## Create the conda environment from environment.yml
	conda env create -f environment.yml
