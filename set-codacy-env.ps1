# Set Codacy Environment Variables
Write-Host "Setting Codacy environment variables..." -ForegroundColor Green

# Check if CODACY_API_TOKEN is already set
if (-not $env:CODACY_API_TOKEN) {
    Write-Host "CODACY_API_TOKEN not found in environment." -ForegroundColor Yellow
    Write-Host "Please set your Codacy API token:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://app.codacy.com/account/api-tokens" -ForegroundColor Cyan
    Write-Host "2. Create a new API token" -ForegroundColor Cyan
    Write-Host "3. Set it using: " -ForegroundColor Cyan -NoNewline
    Write-Host '$env:CODACY_API_TOKEN = "your_actual_token"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or add it to your .env file and source it." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Exiting..." -ForegroundColor Red
    exit 1
}
$env:CODACY_ORGANIZATION_PROVIDER = "gh"
$env:CODACY_USERNAME = "hrninfomeet-wq"
$env:CODACY_PROJECT_NAME = "barakahtraderlite"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "CODACY_API_TOKEN: [HIDDEN]" -ForegroundColor Yellow
Write-Host "CODACY_ORGANIZATION_PROVIDER: $($env:CODACY_ORGANIZATION_PROVIDER)" -ForegroundColor Yellow
Write-Host "CODACY_USERNAME: $($env:CODACY_USERNAME)" -ForegroundColor Yellow
Write-Host "CODACY_PROJECT_NAME: $($env:CODACY_PROJECT_NAME)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Now you can run Codacy analysis:" -ForegroundColor Cyan
Write-Host "codacy-analysis-cli analyze --directory backend/ --tool pylint" -ForegroundColor Gray
