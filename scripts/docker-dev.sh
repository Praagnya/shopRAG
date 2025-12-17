#!/bin/bash

# shopRAG Docker Development Helper Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|restart|logs|build|ingest|clean}"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services (backend, frontend, monitoring)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - Show logs from all services"
    echo "  build     - Rebuild all Docker images"
    echo "  ingest    - Run data ingestion script"
    echo "  clean     - Remove all containers, volumes, and images"
    exit 1
}

# Start services
start_services() {
    echo -e "${GREEN}Starting shopRAG services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Services started!${NC}"
    echo ""
    echo "Access points:"
    echo "  - Frontend: http://localhost:7860"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
}

# Stop services
stop_services() {
    echo -e "${YELLOW}Stopping shopRAG services...${NC}"
    docker-compose down
    echo -e "${GREEN}Services stopped!${NC}"
}

# Restart services
restart_services() {
    echo -e "${YELLOW}Restarting shopRAG services...${NC}"
    docker-compose restart
    echo -e "${GREEN}Services restarted!${NC}"
}

# Show logs
show_logs() {
    docker-compose logs -f
}

# Build images
build_images() {
    echo -e "${GREEN}Building Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}Build complete!${NC}"
}

# Run ingestion
run_ingestion() {
    echo -e "${GREEN}Running data ingestion...${NC}"
    docker-compose --profile ingest run --rm ingest
    echo -e "${GREEN}Ingestion complete!${NC}"
}

# Clean everything
clean_all() {
    echo -e "${RED}WARNING: This will remove all containers, volumes, and images!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}Cleaning up...${NC}"
        docker-compose down -v --rmi all
        echo -e "${GREEN}Cleanup complete!${NC}"
    else
        echo "Cleanup cancelled."
    fi
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    build)
        build_images
        ;;
    ingest)
        run_ingestion
        ;;
    clean)
        clean_all
        ;;
    *)
        usage
        ;;
esac
