# MCP Environment Variables Setup Script
# Run this script to configure all required environment variables for MCP servers

Write-Host "=== MCP Environment Variables Setup ===" -ForegroundColor Green

# GitHub Personal Access Token
if (-not $env:GITHUB_PERSONAL_ACCESS_TOKEN) {
    $token = Read-Host "Enter your GitHub Personal Access Token"
    [System.Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", $token, "User")
    Write-Host "✓ GITHUB_PERSONAL_ACCESS_TOKEN set" -ForegroundColor Green
} else {
    Write-Host "✓ GITHUB_PERSONAL_ACCESS_TOKEN already set" -ForegroundColor Yellow
}

# Google Gemini API Key
if (-not $env:GOOGLE_GEMINI_API_KEY) {
    $token = Read-Host "Enter your Google Gemini API Key"
    [System.Environment]::SetEnvironmentVariable("GOOGLE_GEMINI_API_KEY", $token, "User")
    Write-Host "✓ GOOGLE_GEMINI_API_KEY set" -ForegroundColor Green
} else {
    Write-Host "✓ GOOGLE_GEMINI_API_KEY already set" -ForegroundColor Yellow
}

# Codacy Account Token
if (-not $env:CODACY_ACCOUNT_TOKEN) {
    $token = Read-Host "Enter your Codacy Account Token"
    [System.Environment]::SetEnvironmentVariable("CODACY_ACCOUNT_TOKEN", $token, "User")
    Write-Host "✓ CODACY_ACCOUNT_TOKEN set" -ForegroundColor Green
} else {
    Write-Host "✓ CODACY_ACCOUNT_TOKEN already set" -ForegroundColor Yellow
}

# TestSprite API Key
if (-not $env:TESTSPRITE_API_KEY) {
    $token = Read-Host "Enter your TestSprite API Key"
    [System.Environment]::SetEnvironmentVariable("TESTSPRITE_API_KEY", $token, "User")
    Write-Host "✓ TESTSPRITE_API_KEY set" -ForegroundColor Green
} else {
    Write-Host "✓ TESTSPRITE_API_KEY already set" -ForegroundColor Yellow
}

# Context7 API Key
if (-not $env:CONTEXT7_API_KEY) {
    $token = Read-Host "Enter your Context7 API Key (from Smithery.ai)"
    [System.Environment]::SetEnvironmentVariable("CONTEXT7_API_KEY", $token, "User")
    Write-Host "✓ CONTEXT7_API_KEY set" -ForegroundColor Green
} else {
    Write-Host "✓ CONTEXT7_API_KEY already set" -ForegroundColor Yellow
}

# Exa API Key
if (-not $env:EXA_API_KEY) {
    $token = Read-Host "Enter your Exa API Key (from Smithery.ai)"
    [System.Environment]::SetEnvironmentVariable("EXA_API_KEY", $token, "User")
    Write-Host "✓ EXA_API_KEY set" -ForegroundColor Green
} else {
    Write-Host "✓ EXA_API_KEY already set" -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE to load the new environment variables." -ForegroundColor Yellow
Write-Host "You can now use your MCP servers with Context7 and Exa Search!" -ForegroundColor Green

# Optional: Display current environment variables (masked for security)
Write-Host "`n=== Current Environment Variables ===" -ForegroundColor Cyan
$vars = @("GITHUB_PERSONAL_ACCESS_TOKEN", "GOOGLE_GEMINI_API_KEY", "CODACY_ACCOUNT_TOKEN", "TESTSPRITE_API_KEY", "CONTEXT7_API_KEY", "EXA_API_KEY")
foreach ($var in $vars) {
    $value = [System.Environment]::GetEnvironmentVariable($var, "User")
    if ($value) {
        $masked = "*" * ($value.Length - 4) + $value.Substring($value.Length - 4)
        Write-Host "$var = $masked" -ForegroundColor Cyan
    } else {
        Write-Host "$var = [NOT SET]" -ForegroundColor Red
    }
}

