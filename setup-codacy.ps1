# Codacy Environment Setup Script for PowerShell
Write-Host "Setting up Codacy environment variables..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    
    $envContent = @"
# Codacy Configuration
CODACY_API_TOKEN=YKqLap06omBDqZHI0vrJ
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
"@
    
    $envContent | Out-File -FilePath .env -Encoding UTF8
    Write-Host ".env file created successfully!" -ForegroundColor Green
} else {
    Write-Host ".env file already exists." -ForegroundColor Yellow
}

# Set environment variables for current session
$env:CODACY_ORGANIZATION_PROVIDER = "gh"
$env:CODACY_USERNAME = "hrninfomeet-wq"
$env:CODACY_PROJECT_NAME = "barakahtraderlite"

Write-Host ""
Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "CODACY_ORGANIZATION_PROVIDER=$($env:CODACY_ORGANIZATION_PROVIDER)"
Write-Host "CODACY_USERNAME=$($env:CODACY_USERNAME)"
Write-Host "CODACY_PROJECT_NAME=$($env:CODACY_PROJECT_NAME)"
Write-Host ""
Write-Host "⚠️  IMPORTANT: You need to set your CODACY_API_TOKEN!" -ForegroundColor Red
Write-Host "1. Go to: https://app.codacy.com/account/api-tokens" -ForegroundColor Cyan
Write-Host "2. Create a new API token" -ForegroundColor Cyan
Write-Host "3. Replace 'your_codacy_api_token_here' in .env file with your actual token" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then set the token manually:" -ForegroundColor Yellow
Write-Host '$env:CODACY_API_TOKEN = "your_actual_token"' -ForegroundColor Gray
