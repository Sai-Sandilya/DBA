#!/bin/bash

# Production Deployment Script for DBA-GPT
# This script automates the production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="dba-gpt"
DOCKER_IMAGE="dba-gpt:production"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

echo -e "${BLUE}🚀 Starting DBA-GPT Production Deployment${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check prerequisites
print_info "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file $ENV_FILE not found!"
    print_info "Please copy env.production.template to $ENV_FILE and configure it."
    exit 1
fi

print_status "Prerequisites check passed"

# Load environment variables
print_info "Loading environment variables..."
source "$ENV_FILE"

# Validate critical environment variables
print_info "Validating environment variables..."

required_vars=(
    "MYSQL_HOST"
    "MYSQL_DATABASE"
    "MYSQL_USERNAME"
    "MYSQL_PASSWORD"
    "JWT_SECRET"
    "OPENAI_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_*" ]; then
        print_error "Required environment variable $var is not set or has default value"
        exit 1
    fi
done

print_status "Environment variables validated"

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs
mkdir -p cache
mkdir -p temp
mkdir -p nginx/ssl
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

print_status "Directories created"

# Generate SSL certificates (self-signed for testing, use Let's Encrypt for production)
if [ ! -f "nginx/ssl/dba-gpt.crt" ]; then
    print_warning "SSL certificates not found. Generating self-signed certificates for testing..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/dba-gpt.key \
        -out nginx/ssl/dba-gpt.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    print_status "Self-signed SSL certificates generated"
fi

# Build Docker image
print_info "Building Docker image..."
docker build -f Dockerfile.production -t "$DOCKER_IMAGE" .
print_status "Docker image built successfully"

# Stop existing containers if running
print_info "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
print_status "Existing containers stopped"

# Start services
print_info "Starting production services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Check service health
print_info "Checking service health..."

# Check DBA-GPT service
if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    print_status "DBA-GPT service is healthy"
else
    print_error "DBA-GPT service health check failed"
    docker-compose -f "$COMPOSE_FILE" logs dba-gpt
    exit 1
fi

# Check Redis service
if docker exec dba-gpt-redis redis-cli --raw incr ping >/dev/null 2>&1; then
    print_status "Redis service is healthy"
else
    print_error "Redis service health check failed"
    exit 1
fi

# Check Prometheus service
if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
    print_status "Prometheus service is healthy"
else
    print_error "Prometheus service health check failed"
    exit 1
fi

# Check Grafana service
if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
    print_status "Grafana service is healthy"
else
    print_error "Grafana service health check failed"
    exit 1
fi

print_status "All services are healthy!"

# Display deployment information
echo ""
echo -e "${GREEN}🎉 DBA-GPT Production Deployment Completed Successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service URLs:${NC}"
echo -e "  • DBA-GPT Web Interface: ${GREEN}http://localhost:8501${NC}"
echo -e "  • Prometheus Metrics: ${GREEN}http://localhost:9090${NC}"
echo -e "  • Grafana Dashboards: ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}🔐 Default Credentials:${NC}"
echo -e "  • Grafana: admin / ${GRAFANA_PASSWORD:-'password'} (change this!)"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo -e "  1. Access the web interface at http://localhost:8501"
echo -e "  2. Configure your production databases in the interface"
echo -e "  3. Set up monitoring dashboards in Grafana"
echo -e "  4. Configure alerting rules"
echo -e "  5. Set up SSL certificates for production domain"
echo -e "  6. Configure backup procedures"
echo ""
echo -e "${YELLOW}⚠️  Important Security Notes:${NC}"
echo -e "  • Change default passwords immediately"
echo -e "  • Configure proper SSL certificates for production"
echo -e "  • Set up firewall rules"
echo -e "  • Enable authentication if not already configured"
echo -e "  • Review and update security settings"
echo ""

# Show running containers
print_info "Running containers:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
print_status "Deployment completed! Check the logs if you encounter any issues:"
echo -e "  ${BLUE}docker-compose -f $COMPOSE_FILE logs -f${NC}"
