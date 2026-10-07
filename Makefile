.PHONY: help up down test lint format

help:
	@echo "Commands:"
	@echo "  make up      : Start all Docker microservices"
	@echo "  make down    : Stop all containers"
	@echo "  make test    : Run pytest suite"
	@echo "  make lint    : Run code linting"
	@echo "  make format  : Auto-format Python code"

up:
	docker-compose up -d --build

down:
	docker-compose down

test:
	pytest tests/ -v

lint:
	flake8 shared_lib services tests

format:
	black shared_lib services tests
