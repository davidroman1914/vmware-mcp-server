# WARNING: All commands must run inside Docker containers via docker-compose!
.PHONY: help build test up down clean

help:
	@echo "Available commands:"
	@echo "  build   - Build Docker images"
	@echo "  up      - Start the server in a container"
	@echo "  down    - Stop and clean up containers"
	@echo "  test    - Run the test suite in a container"
	@echo "  clean   - Remove containers, images, and volumes"

build:
	docker-compose build --no-cache

up:
	docker-compose up -d

down:
	docker-compose down --remove-orphans

test:
	docker-compose --profile test run test

clean:
	docker-compose down --rmi all --volumes --remove-orphans 