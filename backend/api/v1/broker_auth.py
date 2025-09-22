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
            type: '{broker_id.upper()}_AUTH_RESULT',
            success: false,
            error: '{error}'
        }}, 'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}');
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
            type: '{broker_id.upper()}_AUTH_RESULT',
            success: false,
            error: 'Missing authorization code'
        }}, 'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}');
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
                type: '{broker_id.upper()}_AUTH_RESULT',
                success: false,
                error: '{token_result.get("error")}'
            }}, 'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}');
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
            type: '{broker_id.upper()}_AUTH_RESULT',
            success: true,
            code: '{code}'
        }}, 'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}');
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
            type: '{broker_id.upper()}_AUTH_RESULT',
            success: false,
            error: 'Server error during authentication'
        }}, 'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}');
        window.close();
        </script>
        <p>Authentication failed: Server error</p>
        <p>You can close this window.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")

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