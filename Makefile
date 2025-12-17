.PHONY: help build up down restart logs clean ingest health

# Default target
.DEFAULT_GOAL := help

# Load environment variables
-include .env
export

# Colors
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
NC     := \033[0m

help: ## Show this help message
	@echo "$(GREEN)shopRAG Docker Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build --no-cache

up: ## Start all services
	@echo "$(GREEN)Starting shopRAG services...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(GREEN)Services started!$(NC)"
	@echo "  Frontend:   http://localhost:7860"
	@echo "  Backend:    http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000 (admin/admin)"

down: ## Stop all services
	@echo "$(YELLOW)Stopping shopRAG services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)Restarting shopRAG services...$(NC)"
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs only
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	docker-compose logs -f frontend

ingest: ## Run data ingestion script
	@echo "$(GREEN)Running data ingestion...$(NC)"
	docker-compose --profile ingest run --rm ingest

health: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@curl -s http://localhost:8000/health || echo "Backend: $(RED)DOWN$(NC)"
	@echo ""
	@curl -s http://localhost:8000/api/status || echo "Backend API: $(RED)DOWN$(NC)"
	@echo ""
	@curl -s http://localhost:9090/-/healthy > /dev/null && echo "Prometheus: $(GREEN)UP$(NC)" || echo "Prometheus: $(RED)DOWN$(NC)"

clean: ## Remove all containers and volumes
	@echo "$(RED)Removing all containers and volumes...$(NC)"
	docker-compose down -v

clean-all: ## Remove everything including images
	@echo "$(RED)WARNING: This will remove all containers, volumes, and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --rmi all; \
		echo "$(GREEN)Cleanup complete!$(NC)"; \
	fi

ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/bash
