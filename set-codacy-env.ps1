# Set Codacy Environment Variables
Write-Host "Setting Codacy environment variables..." -ForegroundColor Green

$env:CODACY_API_TOKEN = "FdjPWqekcDZ4WTZ5M634"
$env:CODACY_ORGANIZATION_PROVIDER = "gh"
$env:CODACY_USERNAME = "hrninfomeet-wq"
$env:CODACY_PROJECT_NAME = "barakahtraderlite"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "CODACY_API_TOKEN: $($env:CODACY_API_TOKEN)" -ForegroundColor Yellow
Write-Host "CODACY_ORGANIZATION_PROVIDER: $($env:CODACY_ORGANIZATION_PROVIDER)" -ForegroundColor Yellow
Write-Host "CODACY_USERNAME: $($env:CODACY_USERNAME)" -ForegroundColor Yellow
Write-Host "CODACY_PROJECT_NAME: $($env:CODACY_PROJECT_NAME)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Now you can run Codacy analysis:" -ForegroundColor Cyan
Write-Host "codacy-analysis-cli analyze --directory backend/ --tool pylint" -ForegroundColor Gray
