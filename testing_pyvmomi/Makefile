# pyvmomi Testing Makefile

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

.PHONY: build
build: ## Build Docker image for pyvmomi testing
	docker build -t pyvmomi-test .

.PHONY: test
test: build ## Test VM operations with pyvmomi
	@echo "🔍 Running pyvmomi VM operations test..."
	docker run --rm \
		--env-file ../.env \
		pyvmomi-test:latest

.PHONY: test-real
test-real: build ## Test VM operations with real vCenter (update credentials in Makefile)
	@echo "🔍 Running pyvmomi VM operations test with real vCenter..."
	docker run --rm \
		-e VCENTER_HOST=your-vcenter-ip-here \
		-e VCENTER_USER=your-username-here \
		-e VCENTER_PASSWORD=your-password-here \
		-e VCENTER_INSECURE=true \
		pyvmomi-test:latest

.PHONY: shell
shell: build ## Start a shell in the pyvmomi container
	docker run --rm -it \
		--env-file ../.env \
		pyvmomi-test:latest /bin/bash

.PHONY: clean
clean: ## Clean up Docker resources
	docker rmi pyvmomi-test:latest 2>/dev/null || true 