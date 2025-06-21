# WARNING: All commands must run inside Docker containers via docker-compose!
.PHONY: help build build-base test up down clean

help:
	@echo "Available commands:"
	@echo "  build-base - Build the base Docker image with dependencies (build once)"
	@echo "  build      - Build the application Docker image (fast, uses base)"
	@echo "  build-full - Build everything from scratch (slow, no cache)"
	@echo "  up         - Start the server in a container"
	@echo "  down       - Stop and clean up containers"
	@echo "  test       - Run the test suite in a container"
	@echo "  clean      - Remove containers, images, and volumes"

build-base:
	@echo "Building base image with dependencies..."
	docker build -f Dockerfile.base -t vmware-mcp-server-base:latest .
	@echo "Base image built successfully!"

build:
	@echo "Building application image (using base image)..."
	@echo "Removing existing latest tag to ensure fresh build..."
	-docker rmi vmware-mcp-server-vmware-mcp-server:latest 2>/dev/null || true
	docker build -t vmware-mcp-server-vmware-mcp-server:latest .
	@echo "Application image built successfully!"

build-full:
	@echo "Building everything from scratch (no cache)..."
	@echo "Removing existing latest tag to ensure fresh build..."
	-docker rmi vmware-mcp-server-vmware-mcp-server:latest 2>/dev/null || true
	docker build --no-cache -t vmware-mcp-server-vmware-mcp-server:latest .
	@echo "Full build completed!"

up:
	docker-compose up -d

down:
	docker-compose down --remove-orphans

test:
	docker-compose --profile test run test

clean:
	docker-compose down --rmi all --volumes --remove-orphans 