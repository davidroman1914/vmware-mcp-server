# VMware vSphere VM List Makefile

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file. Please edit it with your vCenter credentials."; \
	else \
		echo ".env file already exists."; \
	fi

.PHONY: build
build: ## Build Docker image
	docker-compose build

.PHONY: run
run: ## Run the VM list script (standalone)
	docker-compose up vmware-vm-list --abort-on-container-exit

.PHONY: run-mcp
run-mcp: ## Run the MCP server
	docker-compose up vmware-mcp-server --abort-on-container-exit

.PHONY: test-script
test-script: ## Test standalone script in container
	docker-compose run --rm vmware-vm-list python scripts/test_connection.py

.PHONY: shell
shell: ## Open shell in container
	docker-compose run --rm vmware-vm-list /bin/bash

.PHONY: clean
clean: ## Clean up Docker resources
	docker-compose down --rmi all

.PHONY: all
all: setup build run ## Setup, build, and run standalone script 