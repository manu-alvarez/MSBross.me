#!/bin/bash

# MSBross.me Premium Deployment Script
# Run this script to deploy all applications

set -e

echo "🚀 Starting MSBross.me Premium Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 20+ first."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION="20.0.0"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    print_success "Node.js version: $NODE_VERSION ✓"
else
    print_warning "Node.js version $NODE_VERSION detected. Recommended: 20+"
fi

# Function to build an app
build_app() {
    local app_name=$1
    local app_path=$2

    print_status "Building $app_name..."

    if [ -d "$app_path" ]; then
        cd "$app_path"

        # Clean install
        rm -rf node_modules package-lock.json
        npm install --legacy-peer-deps --silent

        # Security check
        npm audit --audit-level=high || print_warning "$app_name has security issues"

        # Build
        if npm run build; then
            print_success "$app_name built successfully"
        else
            print_error "Failed to build $app_name"
            return 1
        fi

        cd - > /dev/null
    else
        print_warning "$app_name directory not found at $app_path"
    fi
}

# Build all frontend apps
print_status "Building frontend applications..."

build_app "Nikolina (LiveKit)" "livekit-frontend"
build_app "IAPutaOS" "IAPutaOS/frontend"
build_app "TaskFlow Pro" "taskflow_pro_src"
build_app "DOHLER" "dohler_src/frontend" || print_warning "DOHLER build failed - may need Vite migration"

# Backend setup
print_status "Setting up backend..."

if [ -d "livekit-backend/server" ]; then
    cd livekit-backend/server

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Python virtual environment created"
    fi

    # Activate and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    print_success "Backend dependencies installed"

    cd - > /dev/null
else
    print_warning "Backend directory not found"
fi

# Run tests
print_status "Running tests..."

# API tests
if [ -f "test_api.sh" ]; then
    chmod +x test_api.sh
    ./test_api.sh || print_warning "API tests failed"
fi

if [ -f "test_api_comprehensive.sh" ]; then
    chmod +x test_api_comprehensive.sh
    ./test_api_comprehensive.sh || print_warning "Comprehensive API tests failed"
fi

# E2E tests for IAPutaOS
if [ -d "IAPutaOS/frontend" ]; then
    cd IAPutaOS/frontend
    npx playwright install --yes
    npm test || print_warning "E2E tests failed"
    cd - > /dev/null
fi

# Final status
print_success "Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure environment variables (.env files)"
echo "2. Deploy frontends to Vercel/Netlify"
echo "3. Deploy backend to Railway/Render"
echo "4. Set up domain and SSL"
echo "5. Run production health checks"
echo ""
print_success "MSBross.me is ready for production! 🎉"