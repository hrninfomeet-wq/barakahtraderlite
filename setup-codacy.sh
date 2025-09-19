#!/bin/bash

# Codacy Environment Setup Script
echo "Setting up Codacy environment variables..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Codacy Configuration
CODACY_API_TOKEN=your_codacy_api_token_here
CODACY_ORGANIZATION_PROVIDER=gh
CODACY_USERNAME=hrninfomeet-wq
CODACY_PROJECT_NAME=barakahtraderlite

# Trading API Keys (for future use)
FLATTRADE_API_KEY=your_flattrade_api_key
FLATTRADE_API_SECRET=your_flattrade_api_secret
FYERS_API_KEY=your_fyers_api_key
FYERS_API_SECRET=your_fyers_api_secret
UPSTOX_API_KEY=your_upstox_api_key
UPSTOX_API_SECRET=your_upstox_api_secret
ALICE_BLUE_API_KEY=your_alice_blue_api_key
ALICE_BLUE_API_SECRET=your_alice_blue_api_secret

# Database
DATABASE_URL=sqlite:///./trading.db

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
EOF
    echo ".env file created successfully!"
else
    echo ".env file already exists."
fi

# Export environment variables for current session
export CODACY_ORGANIZATION_PROVIDER=gh
export CODACY_USERNAME=hrninfomeet-wq
export CODACY_PROJECT_NAME=barakahtraderlite

echo ""
echo "Environment variables set:"
echo "CODACY_ORGANIZATION_PROVIDER=$CODACY_ORGANIZATION_PROVIDER"
echo "CODACY_USERNAME=$CODACY_USERNAME"
echo "CODACY_PROJECT_NAME=$CODACY_PROJECT_NAME"
echo ""
echo "⚠️  IMPORTANT: You need to set your CODACY_API_TOKEN!"
echo "1. Go to: https://app.codacy.com/account/api-tokens"
echo "2. Create a new API token"
echo "3. Replace 'your_codacy_api_token_here' in .env file with your actual token"
echo ""
echo "Then run: source .env"
echo "Or manually export: export CODACY_API_TOKEN=your_actual_token"
