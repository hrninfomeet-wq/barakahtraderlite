# FYERS API Integration Guide

**Complete Guide for Setting Up FYERS API Authentication in Barakah Trader Lite**

> **Important**: This guide is based on real implementation experience and lessons learned. Follow these steps precisely to avoid common pitfalls and ensure seamless integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Security System Setup](#security-system-setup)
3. [FYERS API Configuration](#fyers-api-configuration)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Integration](#frontend-integration)
6. [Testing & Verification](#testing--verification)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Maintenance Guidelines](#maintenance-guidelines)

## Prerequisites

### Required Dependencies

Ensure these dependencies are installed in `pyproject.toml`:

```toml
dependencies = [
    "fastapi>=0.117.1",
    "cryptography>=46.0.1",
    "keyring>=25.6.0",
    "keyrings.alt>=5.0.2",  # Critical: Must be "keyrings.alt" (dot, not hyphen)
    "loguru>=0.7.3",
    "pydantic>=2.11.9",
    "aiohttp>=3.12.15",
    "httpx>=0.28.1",
    "uvicorn[standard]>=0.36.0"
]
```

### Environment Variables Required

```bash
# Replit Secrets (use Replit's secrets management)
FYERS_CLIENT_ID=your_fyers_client_id
FYERS_API_SECRET=your_fyers_api_secret
CREDENTIAL_VAULT_KEY=your_32_byte_aes256_key
```

## Security System Setup

### 1. Generate AES-256 Encryption Key

**CRITICAL**: The security system requires a proper 32-byte AES-256 key.

```bash
# Generate secure 32-byte key
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

Store this key as `CREDENTIAL_VAULT_KEY` in Replit Secrets.

### 2. Verify Security System

The `CredentialVault` class handles:
- AES-256-GCM encryption with Additional Authenticated Data (AAD)
- Token persistence across backend restarts
- Automatic token expiry detection and cleanup
- Secure key management from environment variables

**Key Requirements**:
- Must be exactly 32 bytes (base64 or hex encoded)
- No weak password-based derivation allowed
- Environment-based storage only

## FYERS API Configuration

### 1. FYERS Developer Account Setup

1. **Register**: Create account at [FYERS API Portal](https://myapi.fyers.in/)
2. **Create App**: Go to "My Apps" → "Create New App"
3. **App Configuration**:
   - **App Type**: User App (not Web App)
   - **Redirect URI**: Uses Fyers' fixed URI `https://trade.fyers.in/api-login/redirect-uri/index.html`
   - **App Description**: Barakah Trader Lite Integration

4. **Obtain Credentials**:
   - **Client ID**: Format `ABC12345-100` (your app identifier)
   - **Secret Key**: Long alphanumeric string

> **Important**: User App type is recommended for desktop/mobile applications. The redirect URI is fixed by Fyers and cannot be customized.

### 2. Replit Secrets Configuration

Add these to Replit Secrets (not .env file):

```bash
FYERS_CLIENT_ID=ABC12345-100
FYERS_API_SECRET=your_secret_key_here
CREDENTIAL_VAULT_KEY=your_generated_32_byte_key
```

## Backend Implementation

### 1. Security Module Integration

The `backend/core/security.py` should include:

```python
class CredentialVault:
    """AES-256-GCM encrypted storage for API credentials"""
    
    async def initialize(self):
        """Initialize with strict 32-byte key validation"""
        
    async def store_auth_token(self, provider: APIProvider, token_data: Dict) -> bool:
        """Store encrypted token with AAD binding"""
        
    async def retrieve_auth_token(self, provider: APIProvider) -> Optional[Dict]:
        """Retrieve and validate token with expiry check"""
```

### 2. FYERS Service Implementation

Located in `backend/services/fyers_api.py`:

```python
class FyersAPIService:
    def __init__(self):
        self.base_url = "https://api-t1.fyers.in/api/v3"  # Trading API v3
        self.redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"  # Fixed for User App
        
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL for User App"""
        
    async def exchange_code_for_token(self, auth_code: str) -> Dict:
        """Exchange authorization code for access token using User App flow"""
        
    async def _store_token(self, token_data: Dict) -> None:
        """Store token using CredentialVault.store_auth_token()"""
```

### 3. API Endpoints

In `backend/api/v1/broker_auth.py`:

```python
@router.get("/{broker_id}/login")  # e.g., /api/v1/auth/fyers/login
async def broker_login(broker_id: str):
    """Initiate FYERS OAuth flow - returns auth_url"""
    
@router.get("/{broker_id}/callback")  # e.g., /api/v1/auth/fyers/callback
async def broker_callback(broker_id: str, code: str):
    """Handle OAuth callback and exchange code for token"""
    
@router.get("/{broker_id}/status")  # e.g., /api/v1/auth/fyers/status
async def get_broker_status(broker_id: str):
    """Check FYERS authentication status"""

@router.post("/exchange-code")  # Custom endpoint for manual code input
async def exchange_auth_code(request: AuthCallbackRequest):
    """Manual code exchange endpoint for User App flow"""
```

## Frontend Integration

### 1. OAuth Popup Implementation (User App Flow)

```typescript
// Frontend authentication flow for User App
const authenticateWithFyers = async () => {
  // Get auth URL from backend
  const response = await fetch('/api/v1/auth/fyers/login');
  const { auth_url } = await response.json();
  
  // Open popup for OAuth - User will be redirected to Fyers' fixed page
  const popup = window.open(
    auth_url,
    'fyersAuth',
    'width=600,height=700,scrollbars=yes,resizable=yes'
  );
  
  // For User App, user must manually copy auth code from Fyers' page
  // Show instructions to user about copying the code
  
  // Listen for completion message from callback
  const handleMessage = (event) => {
    if (event.data.type === 'FYERS_AUTH_SUCCESS') {
      popup.close();
      checkBrokerStatus();
    } else if (event.data.type === 'FYERS_AUTH_ERROR') {
      popup.close();
      console.error('Auth failed:', event.data.error);
    }
  };
  
  window.addEventListener('message', handleMessage);
  
  // Alternative: Provide manual code input for User App flow
  // This is often needed since User App redirects to Fyers' page
  showAuthCodeInputDialog();
};

// Optional: Manual auth code input for User App
const exchangeAuthCode = async (authCode: string) => {
  const response = await fetch('/api/v1/auth/exchange-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: authCode, broker: 'fyers' })
  });
  
  const result = await response.json();
  if (result.success) {
    checkBrokerStatus();
  }
};
```

### 2. Status Monitoring

```typescript
const checkFyersStatus = async () => {
  try {
    const response = await fetch('/api/v1/auth/fyers/status');
    const status = await response.json();
    return status.authenticated;
  } catch (error) {
    console.error('Error checking FYERS status:', error);
    return false;
  }
};
```

## Testing & Verification

### 1. Security System Test

```python
# Test AES-256-GCM encryption
async def test_security_system():
    vault = CredentialVault()
    await vault.initialize()
    
    # Test token storage and retrieval (User App)
    test_token = {
        'access_token': 'test_token_xyz',
        'expires_at': (datetime.now() + timedelta(hours=8)).isoformat(),
        'lifetime_hours': 8,
        'token_type': 'fyers_access_token'
    }
    
    stored = await vault.store_auth_token(APIProvider.FYERS, test_token)
    retrieved = await vault.retrieve_auth_token(APIProvider.FYERS)
    
    assert stored and retrieved
    assert retrieved['access_token'] == test_token['access_token']
```

### 2. End-to-End Authentication Test

1. **Backend Test**: Verify auth endpoints respond correctly
   ```bash
   # Test status endpoint
   curl http://localhost:8000/api/v1/auth/fyers/status
   
   # Test login endpoint (get auth URL)
   curl http://localhost:8000/api/v1/auth/fyers/login
   ```

2. **Frontend Test**: Test OAuth popup flow or manual code exchange
3. **Persistence Test**: Restart backend and verify token retrieval
4. **Expiry Test**: Test automatic cleanup of expired tokens

### 3. Verification Checklist

- [ ] CREDENTIAL_VAULT_KEY is proper 32-byte AES-256 key
- [ ] FYERS credentials stored in Replit Secrets
- [ ] Backend starts without security errors
- [ ] Auth endpoints return proper responses
- [ ] Frontend OAuth popup opens correctly
- [ ] Token storage persists across backend restarts
- [ ] Expired tokens are automatically cleaned up

## Common Issues & Solutions

### Issue 1: "Credential vault initialization failed"

**Cause**: Incorrect CREDENTIAL_VAULT_KEY format
**Solution**: Generate proper 32-byte key:
```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### Issue 2: "Keyring backend does not support persistence"

**Cause**: Missing or incorrect keyrings.alt dependency
**Solution**: Ensure `pyproject.toml` has `"keyrings.alt>=5.0.2"` (dot, not hyphen)

### Issue 3: OAuth popup blocked or User App redirect confusion

**Cause**: Browser popup blocker or confusion about User App flow
**Solution**: 
- Ensure popup is triggered by user action
- For User App: User must manually copy auth code from Fyers' redirect page
- Consider implementing manual code input field as alternative
- Configure proper CORS headers in FastAPI

### Issue 4: Token expires unexpectedly

**Cause**: FYERS tokens have 8-hour expiry
**Solution**: 
- Implement token refresh logic
- Handle 401 errors gracefully
- Store refresh tokens if available

### Issue 5: "No auth token found" after restart

**Cause**: Keyring backend not persisting data
**Solution**:
- Verify keyrings.alt installation
- Check PlaintextKeyring is active in logs
- Ensure file system persistence in Replit

## Maintenance Guidelines

### Regular Tasks

1. **Token Monitoring**: Check token expiry and refresh rates
2. **Security Audits**: Verify encryption keys and storage security
3. **API Updates**: Monitor FYERS API changes and deprecations
4. **Error Monitoring**: Track authentication failure rates

### Best Practices

1. **Never log tokens or secrets**
2. **Use environment variables for all sensitive data**
3. **Implement proper error handling for all API calls**
4. **Test token persistence after each deployment**
5. **Monitor token expiry and implement refresh logic**

### Emergency Procedures

**If tokens are compromised**:
1. Revoke all tokens in FYERS portal
2. Generate new CREDENTIAL_VAULT_KEY
3. Update Replit Secrets
4. Restart backend to clear cached credentials
5. Re-authenticate all users

**If authentication fails system-wide**:
1. Check FYERS API status
2. Verify Replit Secrets are accessible
3. Test security system initialization
4. Check keyring backend functionality
5. Restart backend if necessary

## Success Indicators

A successful FYERS API integration will show:

- ✅ Backend starts without security errors
- ✅ OAuth popup opens and completes successfully  
- ✅ Tokens persist across backend restarts
- ✅ Token expiry is detected and handled
- ✅ All API calls use proper authentication
- ✅ No sensitive data appears in logs
- ✅ System handles authentication failures gracefully

## Notes for Future AI Agents

1. **Follow this guide precisely** - Each step has been validated through real implementation
2. **Security is paramount** - Never compromise on the AES-256-GCM encryption requirements
3. **Test thoroughly** - Verify each component before proceeding to the next
4. **Monitor logs** - The security system provides detailed logging for debugging
5. **Document changes** - Update this guide if you discover new issues or solutions

---

**Last Updated**: September 2025  
**Implementation Status**: Tested and Verified  
**Security Level**: Bank-Grade AES-256-GCM Encryption