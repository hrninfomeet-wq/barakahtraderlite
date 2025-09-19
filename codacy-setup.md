# Codacy Environment Setup

## Step 1: Get Your Codacy API Token

1. Go to [Codacy Account Settings](https://app.codacy.com/account/api-tokens)
2. Sign in with your GitHub account
3. Create a new API token
4. Copy the token

## Step 2: Set Environment Variables

### Option A: Create `.env` file (Recommended)
Create a `.env` file in your project root with:

```bash
# Codacy Configuration
CODACY_API_TOKEN=your_codacy_api_token_here
CODACY_ORGANIZATION_PROVIDER=gh
CODACY_USERNAME=hrninfomeet-wq
CODACY_PROJECT_NAME=barakahtraderlite
```

### Option B: Export in Terminal (Temporary)
```bash
export CODACY_API_TOKEN=your_codacy_api_token_here
export CODACY_ORGANIZATION_PROVIDER=gh
export CODACY_USERNAME=hrninfomeet-wq
export CODACY_PROJECT_NAME=barakahtraderlite
```

### Option C: PowerShell (Windows)
```powershell
$env:CODACY_API_TOKEN="your_codacy_api_token_here"
$env:CODACY_ORGANIZATION_PROVIDER="gh"
$env:CODACY_USERNAME="hrninfomeet-wq"
$env:CODACY_PROJECT_NAME="barakahtraderlite"
```

## Step 3: Verify Setup
```bash
# Test the configuration
codacy-analysis-cli analyze --directory backend/ --tool pylint
```

## Step 4: Run Analysis
```bash
# Analyze entire project
codacy-analysis-cli analyze --directory .

# Analyze with specific output format
codacy-analysis-cli analyze --directory . --format json --output codacy-results.json
```

## Next Steps
Once you have your API token, replace `your_codacy_api_token_here` with your actual token.
