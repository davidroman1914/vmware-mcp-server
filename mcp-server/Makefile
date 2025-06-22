.PHONY: help install test run build docker-build docker-run clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

test: ## Run the test script
	python test_power_management.py

run: ## Run the server locally
	python server.py

build: ## Build the Docker image
	docker build -t vmware-mcp-server-clean .

docker-run: ## Run the server in Docker
	docker run --rm -it \
		-e VCENTER_HOST=$(VCENTER_HOST) \
		-e VCENTER_USER=$(VCENTER_USER) \
		-e VCENTER_PASSWORD=$(VCENTER_PASSWORD) \
		-e VCENTER_INSECURE=$(VCENTER_INSECURE) \
		vmware-mcp-server-clean

clean: ## Clean up generated files
	rm -rf __pycache__ *.pyc .pytest_cache 