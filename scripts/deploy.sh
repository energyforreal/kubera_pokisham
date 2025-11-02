#!/bin/bash
# Deployment script for AI Trading Agent

set -e  # Exit on error

echo "🚀 AI Trading Agent - Production Deployment"
echo "==========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.docker.example...${NC}"
    if [ -f .env.docker.example ]; then
        cp .env.docker.example .env
        echo -e "${YELLOW}📝 Please edit .env file with your credentials:${NC}"
        echo "   - DELTA_API_KEY"
        echo "   - DELTA_API_SECRET"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - TELEGRAM_CHAT_ID"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        echo -e "${RED}❌ .env.docker.example not found${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Environment configuration found${NC}"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p models logs data monitoring/grafana/dashboards
chmod 777 logs data  # Ensure write permissions

# Pull latest images
echo "📥 Pulling Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building custom images..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

# Check if API is responding
echo ""
echo "🔍 Checking API health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
        echo -e "${GREEN}✓ API is healthy!${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ API failed to start. Check logs:${NC}"
        echo "   docker-compose logs api"
        exit 1
    fi
    
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Display access information
echo ""
echo "======================================"
echo -e "${GREEN}✅ Deployment Successful!${NC}"
echo "======================================"
echo ""
echo "🌐 Access Points:"
echo "   API:        http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3000 (admin/admin)"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:     docker-compose logs -f api"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart api"
echo ""
echo "📚 Documentation:"
echo "   Implementation Summary: ./IMPLEMENTATION_SUMMARY.md"
echo "   API Documentation: http://localhost:8000/docs"
echo ""


