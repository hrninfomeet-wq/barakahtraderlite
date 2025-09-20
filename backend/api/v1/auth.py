"""
Authentication endpoints for broker integrations (Upstox OAuth)
"""
from datetime import datetime
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from loguru import logger
import aiohttp
from urllib.parse import quote

from models.trading import APIProvider
from core.security import CredentialVault, SecurityException


router = APIRouter(prefix="/auth", tags=["auth"]) 


@router.get("/upstox/login")
async def upstox_login(state: str = "secure-state"):
    """Redirect user to Upstox authorization page."""
    # Upstox OAuth expects client_id = API Key
    client_id = os.environ.get("UPSTOX_API_KEY") or os.environ.get("UPSTOX_CLIENT_ID")
    redirect_uri = os.environ.get("UPSTOX_REDIRECT_URI")
    base_url = os.environ.get("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="UPSTOX_CLIENT_ID/API_KEY and UPSTOX_REDIRECT_URI are required")

    encoded_redirect = quote(redirect_uri, safe=":/")
    auth_url = (
        f"{base_url}/login/authorization/dialog?client_id={client_id}"
        f"&redirect_uri={encoded_redirect}&response_type=code&state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/upstox/callback")
async def upstox_callback(code: str = Query(...), state: str = Query(None)):
    """Handle Upstox OAuth callback: exchange code for access token and store securely."""
    # Upstox OAuth expects client_id = API Key
    client_id = os.environ.get("UPSTOX_API_KEY") or os.environ.get("UPSTOX_CLIENT_ID")
    client_secret = os.environ.get("UPSTOX_API_SECRET")
    redirect_uri = os.environ.get("UPSTOX_REDIRECT_URI")
    base_url = os.environ.get("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Missing Upstox OAuth configuration")

    token_url = f"{base_url}/login/authorization/token"
    form = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(token_url, data=form) as resp:
                data = await resp.json()
                if resp.status != 200:
                    logger.error(f"Upstox token exchange failed {resp.status}: {data}")
                    raise HTTPException(status_code=resp.status, detail=data)
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as e:
        logger.error(f"Upstox token exchange network error: {e}")
        raise HTTPException(status_code=502, detail="Network error during token exchange")

    # Expected fields: access_token, refresh_token, expires_in
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in") or 0

    if not access_token:
        raise HTTPException(status_code=500, detail="Access token missing in Upstox response")

    # Store in credential vault
    try:
        vault = CredentialVault()
        await vault.initialize()
        await vault.store_api_credentials(
            APIProvider.UPSTOX,
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "obtained_at": datetime.now().isoformat(),
            },
        )
    except SecurityException as se:
        logger.error(f"Failed to store Upstox credentials: {se}")
        raise HTTPException(status_code=500, detail="Secure storage failed")

    # Make token available to current process as a convenience (not persistence)
    os.environ["UPSTOX_ACCESS_TOKEN"] = access_token
    if refresh_token:
        os.environ["UPSTOX_REFRESH_TOKEN"] = refresh_token

    return JSONResponse({
        "success": True,
        "provider": "upstox",
        "stored": True,
        "expires_in": expires_in,
        "message": "Upstox connected successfully. You can close this tab." 
    })


@router.get("/upstox/status")
async def upstox_status():
    """Return token presence and age information for Upstox OAuth."""
    # Try secure store first
    creds = None
    try:
        vault = CredentialVault()
        await vault.initialize()
        creds = await vault.retrieve_api_credentials(APIProvider.UPSTOX)
    except SecurityException:
        creds = None

    access_token = (creds or {}).get("access_token") or os.environ.get("UPSTOX_ACCESS_TOKEN")
    obtained_at_str = (creds or {}).get("obtained_at")
    expires_in = (creds or {}).get("expires_in")

    age_seconds = None
    if obtained_at_str:
        try:
            obtained_dt = datetime.fromisoformat(obtained_at_str)
            age_seconds = int((datetime.now() - obtained_dt).total_seconds())
        except Exception:
            age_seconds = None

    # Validate token by making a test API call if we have a token
    is_valid = False
    if access_token:
        try:
            base_url = os.environ.get("UPSTOX_BASE_URL", "https://api.upstox.com/v2")
            headers = {"Authorization": f"Bearer {access_token}"}
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{base_url}/user/profile", headers=headers) as resp:
                    is_valid = resp.status == 200
        except Exception:
            is_valid = False

    return JSONResponse({
        "provider": "upstox",
        "has_token": bool(access_token),
        "is_valid": is_valid,
        "age_seconds": age_seconds,
        "expires_in": expires_in,
    })


@router.delete("/upstox/disconnect")
async def upstox_disconnect():
    """Disconnect and clear Upstox authentication."""
    try:
        # Clear from secure store
        vault = CredentialVault()
        await vault.initialize()
        await vault.delete_api_credentials(APIProvider.UPSTOX)
    except SecurityException:
        pass

    # Clear from environment variables
    if "UPSTOX_ACCESS_TOKEN" in os.environ:
        del os.environ["UPSTOX_ACCESS_TOKEN"]
    if "UPSTOX_REFRESH_TOKEN" in os.environ:
        del os.environ["UPSTOX_REFRESH_TOKEN"]

    return JSONResponse({
        "success": True,
        "provider": "upstox",
        "message": "Upstox disconnected successfully"
    })


# Helper to include router

def include_router(app):
    app.include_router(router)
