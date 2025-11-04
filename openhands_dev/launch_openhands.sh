#!/bin/bash

# OpenHands API Server Launch Script
# This script provides multiple ways to launch the OpenHands API server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OPENHANDS_PORT=${OPENHANDS_PORT:-3000}
OPENHANDS_HOST=${OPENHANDS_HOST:-0.0.0.0}
WORKSPACE_DIR=$(pwd)

echo -e "${BLUE}🚀 OpenHands API Server Launch Script${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to check if port is available
check_port() {
    if lsof -Pi :$OPENHANDS_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $OPENHANDS_PORT is already in use${NC}"
        echo "Please stop the existing service or choose a different port:"
        echo "  export OPENHANDS_PORT=3001"
        echo "  $0"
        exit 1
    fi
}

# Function to check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker is not running${NC}"
        echo "Please start Docker daemon"
        exit 1
    fi
}

# Function to launch with Docker (recommended)
launch_docker() {
    echo -e "${GREEN}🐳 Launching OpenHands API with Docker...${NC}"
    
    check_docker
    check_port
    
    echo "Configuration:"
    echo "  Port: $OPENHANDS_PORT"
    echo "  Workspace: $WORKSPACE_DIR"
    echo "  Container: openhands-api-server"
    
    docker run -it --rm \
        --name openhands-api-server \
        -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.9-nikolaik \
        -e LOG_LEVEL=INFO \
        -e WORKSPACE_BASE=/workspace \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$WORKSPACE_DIR":/workspace \
        -p "$OPENHANDS_PORT":3000 \
        --add-host host.docker.internal:host-gateway \
        docker.all-hands.dev/all-hands-ai/openhands:0.9
}

# Function to launch with Docker Compose
launch_compose() {
    echo -e "${GREEN}🐳 Launching with Docker Compose...${NC}"
    
    check_docker
    
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ docker-compose.yml not found${NC}"
        exit 1
    fi
    
    echo "Available profiles:"
    echo "  - enhanced: Enhanced reviewer (99.77% match)"
    echo "  - api: API-based reviewer"
    echo "  - hybrid: Hybrid reviewer (Enhanced + API)"
    echo "  - test: Test suite"
    
    echo -e "${YELLOW}Starting OpenHands API server...${NC}"
    docker-compose up -d openhands-api
    
    echo -e "${GREEN}✅ OpenHands API server started${NC}"
    echo "Use these commands to run reviewers:"
    echo "  docker-compose --profile enhanced up enhanced-reviewer"
    echo "  docker-compose --profile api up api-reviewer"
    echo "  docker-compose --profile hybrid up hybrid-reviewer"
    echo "  docker-compose --profile test up test-runner"
}

# Function to launch with pip installation
launch_pip() {
    echo -e "${GREEN}📦 Launching OpenHands API with pip installation...${NC}"
    
    check_port
    
    # Check if openhands is installed
    if ! python -c "import openhands" 2>/dev/null; then
        echo -e "${YELLOW}Installing OpenHands...${NC}"
        pip install openhands-ai
    fi
    
    echo "Starting OpenHands API server..."
    echo "  Port: $OPENHANDS_PORT"
    echo "  Host: $OPENHANDS_HOST"
    echo "  Workspace: $WORKSPACE_DIR"
    
    cd "$WORKSPACE_DIR"
    openhands start --port "$OPENHANDS_PORT" --host "$OPENHANDS_HOST"
}

# Function to test API server
test_api() {
    echo -e "${BLUE}🧪 Testing OpenHands API server...${NC}"
    
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for API server to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$OPENHANDS_PORT/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API server is healthy!${NC}"
            
            # Test health endpoint
            echo "Health check response:"
            curl -s "http://localhost:$OPENHANDS_PORT/health" | python -m json.tool 2>/dev/null || echo "Non-JSON response"
            
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ API server failed to start or is not responding${NC}"
    return 1
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  docker     Launch with Docker (recommended)"
    echo "  compose    Launch with Docker Compose"
    echo "  pip        Launch with pip installation"
    echo "  test       Test API server connection"
    echo "  stop       Stop running containers"
    echo "  logs       Show API server logs"
    echo "  help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  OPENHANDS_PORT    Port for API server (default: 3000)"
    echo "  OPENHANDS_HOST    Host for API server (default: 0.0.0.0)"
    echo ""
    echo "Examples:"
    echo "  $0 docker                    # Launch with Docker"
    echo "  OPENHANDS_PORT=3001 $0 pip   # Launch on port 3001 with pip"
    echo "  $0 compose                   # Launch with Docker Compose"
}

# Function to stop containers
stop_containers() {
    echo -e "${YELLOW}🛑 Stopping OpenHands containers...${NC}"
    
    # Stop Docker container
    if docker ps -q -f name=openhands-api-server | grep -q .; then
        docker stop openhands-api-server
        echo "✅ Stopped openhands-api-server"
    fi
    
    # Stop Docker Compose services
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        echo "✅ Stopped Docker Compose services"
    fi
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 OpenHands API Server Logs${NC}"
    
    if docker ps -q -f name=openhands-api-server | grep -q .; then
        docker logs -f openhands-api-server
    elif [ -f "docker-compose.yml" ]; then
        docker-compose logs -f openhands-api
    else
        echo -e "${RED}❌ No running OpenHands containers found${NC}"
    fi
}

# Main script logic
case "${1:-docker}" in
    "docker")
        launch_docker
        ;;
    "compose")
        launch_compose
        ;;
    "pip")
        launch_pip
        ;;
    "test")
        test_api
        ;;
    "stop")
        stop_containers
        ;;
    "logs")
        show_logs
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_usage
        exit 1
        ;;
esac