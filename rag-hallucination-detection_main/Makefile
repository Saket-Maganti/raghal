PYTHON ?= python3

.PHONY: help verify tests clean docker-build docker-run

help:
	@echo "make verify       Run lightweight artifact verification"
	@echo "make tests        Run smoke tests"
	@echo "make clean        Remove generated caches"
	@echo "make docker-build Build the verification image"
	@echo "make docker-run   Run verification in the image"

verify:
	bash run_all_analysis.sh

tests:
	$(PYTHON) -m pytest tests/ -v --tb=short

clean:
	find . -name ".DS_Store" -delete
	find . -name "._*" -delete
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} +

docker-build:
	docker build -t controlledrag-artifact:latest .

docker-run:
	docker run --rm controlledrag-artifact:latest
