"""
Broker Authentication API - Barakah Trader Lite
Handles OAuth flows for all supported brokers
"""

import os
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from services.broker_manager import broker_manager

router = APIRouter(prefix="/auth", tags=["Broker Authentication"])

class AuthCallbackRequest(BaseModel):
    code: str
    broker: str

@router.get("/{broker_id}/status")
async def get_broker_status(broker_id: str) -> Dict[str, Any]:
    """Get authentication status for a specific broker"""
    try:
        status = broker_manager.get_broker_status(broker_id)
        logger.info(f"Status check for {broker_id}: {status.get('status', 'unknown')}")
        return status
    except Exception as e:
        logger.error(f"Error getting {broker_id} status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get {broker_id} status")

@router.get("/status/all")
async def get_all_broker_statuses() -> Dict[str, Any]:
    """Get authentication status for all brokers"""
    try:
        statuses = broker_manager.get_all_broker_statuses()
        logger.info(f"All broker statuses: {statuses['connected_count']}/{statuses['total_count']} connected")
        return statuses
    except Exception as e:
        logger.error(f"Error getting all broker statuses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get broker statuses")

@router.get("/{broker_id}/login")
async def broker_login(broker_id: str) -> Dict[str, Any]:
    """Initiate OAuth login flow for a specific broker"""
    try:
        auth_url = broker_manager.get_auth_url(broker_id)
        logger.info(f"Generated auth URL for {broker_id}")
        
        return {
            "auth_url": auth_url,
            "broker": broker_id,
            "message": f"Please complete authentication for {broker_id}",
        }
    except ValueError as e:
        logger.error(f"Configuration error for {broker_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating auth URL for {broker_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL for {broker_id}")

@router.get("/{broker_id}/callback")
async def broker_callback(broker_id: str, code: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback from broker"""
    if error:
        logger.error(f"{broker_id} OAuth error: {error}")
        # Return HTML that communicates with parent window
        html_content = f"""
        <html>
        <body>
        <script>
        window.opener.postMessage({{
            type: '{broker_id.upper()}_AUTH_ERROR',
            success: false,
            error: '{error}'
        }}, '*');
        window.close();
        </script>
        <p>Authentication failed: {error}</p>
        <p>You can close this window.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    if not code:
        logger.error(f"{broker_id} callback missing authorization code")
        html_content = f"""
        <html>
        <body>
        <script>
        window.opener.postMessage({{
            type: '{broker_id.upper()}_AUTH_ERROR',
            success: false,
            error: 'Missing authorization code'
        }}, '*');
        window.close();
        </script>
        <p>Authentication failed: Missing authorization code</p>
        <p>You can close this window.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    try:
        # Exchange code for token
        token_result = await broker_manager.exchange_code_for_token(broker_id, code)
        
        if token_result.get("error"):
            logger.error(f"{broker_id} token exchange failed: {token_result.get('error')}")
            html_content = f"""
            <html>
            <body>
            <script>
            window.opener.postMessage({{
                type: '{broker_id.upper()}_AUTH_ERROR',
                success: false,
                error: '{token_result.get("error")}'
            }}, '*');
            window.close();
            </script>
            <p>Token exchange failed: {token_result.get('error')}</p>
            <p>You can close this window.</p>
            </body>
            </html>
            """
            return Response(content=html_content, media_type="text/html")
        
        logger.info(f"{broker_id} authentication successful")
        
        # Return success HTML that communicates with parent window
        html_content = f"""
        <html>
        <body>
        <script>
        window.opener.postMessage({{
            type: '{broker_id.upper()}_AUTH_SUCCESS',
            success: true,
            broker: '{broker_id}'
        }}, '*');
        window.close();
        </script>
        <h2>✅ Authentication Successful!</h2>
        <p>{broker_id.capitalize()} has been connected successfully.</p>
        <p>You can close this window and return to the main application.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"{broker_id} callback error: {str(e)}")
        html_content = f"""
        <html>
        <body>
        <script>
        window.opener.postMessage({{
            type: '{broker_id.upper()}_AUTH_ERROR',
            success: false,
            error: 'Server error during authentication'
        }}, '*');
        window.close();
        </script>
        <p>Authentication failed: Server error</p>
        <p>You can close this window.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")

@router.post("/{broker_id}/api-key")
async def authenticate_broker_with_api_key(broker_id: str, request: Request) -> Dict[str, Any]:
    """Authenticate broker using API key (for brokers that don't use OAuth)"""
    try:
        # Get API key from request body
        body = await request.json()
        api_key = body.get('api_key')
        
        if not api_key:
            logger.error(f"{broker_id} API key authentication missing api_key")
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Authenticate using broker manager
        result = await broker_manager.authenticate_with_api_key(broker_id, api_key)
        
        if result.get('success'):
            logger.info(f"{broker_id} API key authentication successful")
            return {
                "success": True,
                "message": f"{broker_id} authenticated successfully with API key",
                "broker": broker_id
            }
        else:
            logger.error(f"{broker_id} API key authentication failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get('error', 'Authentication failed'))
            
    except ValueError as e:
        logger.error(f"Configuration error for {broker_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during {broker_id} API key authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to authenticate {broker_id} with API key")

@router.delete("/{broker_id}/disconnect")
async def disconnect_broker(broker_id: str) -> Dict[str, Any]:
    """Disconnect a specific broker"""
    try:
        result = broker_manager.disconnect_broker(broker_id)
        logger.info(f"Disconnected {broker_id}")
        return result
    except Exception as e:
        logger.error(f"Error disconnecting {broker_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect {broker_id}")

@router.post("/{broker_id}/test")
async def test_broker_connection(broker_id: str) -> Dict[str, Any]:
    """Test connection for a specific broker"""
    try:
        # Test with a simple market data call
        test_symbols = ["RELIANCE", "TCS"]
        
        if broker_id == "upstox":
            result = await broker_manager.brokers['upstox'].get_market_data(test_symbols)
        elif broker_id == "flattrade":
            result = await broker_manager.brokers['flattrade'].get_market_data(test_symbols)
        elif broker_id == "fyers":
            result = await broker_manager.brokers['fyers'].get_market_data(test_symbols)
        elif broker_id == "aliceblue":
            result = await broker_manager.brokers['aliceblue'].get_market_data(test_symbols)
        else:
            raise ValueError(f"Unknown broker: {broker_id}")
        
        if result.get("success") or result.get("data"):
            logger.info(f"{broker_id} connection test successful")
            return {
                "success": True,
                "message": f"{broker_id} connection test passed",
                "test_result": result
            }
        else:
            logger.warning(f"{broker_id} connection test failed: {result.get('error')}")
            return {
                "success": False,
                "message": f"{broker_id} connection test failed",
                "error": result.get('error')
            }
            
    except Exception as e:
        logger.error(f"Error testing {broker_id} connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test {broker_id} connection")

@router.get("/fyers/url")
async def get_fyers_auth_url() -> Dict[str, Any]:
    """Get Fyers User App authentication URL"""
    try:
        fyers_service = broker_manager.brokers.get('fyers')
        if not fyers_service:
            return {"error": "Fyers service not available"}
        
        auth_url = fyers_service.get_auth_url()
        logger.info("Generated Fyers User App authentication URL")
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error(f"Error generating Fyers auth URL: {str(e)}")
        return {"error": f"Failed to generate auth URL: {str(e)}"}

@router.post("/fyers/manual-auth")
async def fyers_manual_auth(request: Dict[str, str]) -> Dict[str, Any]:
    """Handle manual Fyers User App authentication with authorization code"""
    try:
        auth_code = request.get('auth_code')
        if not auth_code:
            return {"success": False, "error": "Authorization code is required"}
        
        logger.info(f"Processing manual Fyers authentication with code: {auth_code[:20]}...")
        
        # Exchange code for token using Fyers service
        token_result = await broker_manager.exchange_code_for_token('fyers', auth_code)
        
        if token_result.get("error"):
            logger.error(f"Fyers manual auth token exchange failed: {token_result.get('error')}")
            return {"success": False, "error": token_result.get('error')}
        
        logger.info("Fyers manual authentication successful")
        return {"success": True, "message": "Fyers authentication completed successfully"}
        
    except Exception as e:
        logger.error(f"Error in manual Fyers authentication: {str(e)}")
        return {"success": False, "error": f"Authentication failed: {str(e)}"}

@router.get("/fyers/holdings")
async def get_fyers_holdings():
    """Get user's holdings from Fyers API"""
    try:
        fyers_service = broker_manager.brokers.get('fyers')
        if not fyers_service:
            return {"success": False, "error": "Fyers service not available"}
        
        result = await fyers_service.get_holdings()
        logger.info(f"Fyers holdings API call: {result.get('success', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch Fyers holdings: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/fyers/profile")
async def get_fyers_profile():
    """Get user's account profile from Fyers API"""
    try:
        fyers_service = broker_manager.brokers.get('fyers')
        if not fyers_service:
            return {"success": False, "error": "Fyers service not available"}
        
        result = await fyers_service.get_account_profile()
        logger.info(f"Fyers profile API call: {result.get('success', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch Fyers profile: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/fyers/funds")
async def get_fyers_funds():
    """Get user's funds and margin information from Fyers API"""
    try:
        fyers_service = broker_manager.brokers.get('fyers')
        if not fyers_service:
            return {"success": False, "error": "Fyers service not available"}
        
        result = await fyers_service.get_funds()
        logger.info(f"Fyers funds API call: {result.get('success', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch Fyers funds: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/health")
async def get_broker_health() -> Dict[str, Any]:
    """Get overall health summary of all brokers"""
    try:
        health = broker_manager.get_health_summary()
        logger.info(f"Broker system health: {health['status']} ({health['health_score']:.1f}%)")
        return health
    except Exception as e:
        logger.error(f"Error getting broker health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get broker health")