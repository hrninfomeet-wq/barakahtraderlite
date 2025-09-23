"""
AliceBlue API Service - Barakah Trader Lite
Handles AliceBlue API authentication and market data integration
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

class AliceBlueAPIService:
    def __init__(self):
        """Initialize AliceBlue API service with credentials from environment"""
        # Check for User ID in environment with fallback to AB104570
        self.user_id = os.getenv('ALICEBLUE_USER_ID') or 'AB104570'
        self.app_code = os.getenv('ALICEBLUE_APP_CODE')
        self.api_secret = os.getenv('ALICEBLUE_API_SECRET')
        self.base_url = os.getenv('ALICEBLUE_API_BASE_URL', 'https://v2api.aliceblueonline.com/restpy/api')
        # Use Replit domain for OAuth redirect
        replit_domain = os.getenv('REPLIT_DEV_DOMAIN') or 'localhost:8000'
        self.redirect_uri = f'https://{replit_domain}/api/v1/auth/aliceblue/callback'
        self.access_token = None  # Will be set after authentication
        
        # Log initialization status
        has_user = "✓" if self.user_id else "✗"
        has_secret = "✓" if self.api_secret else "✗"
        logger.info(f"AliceBlueAPIService initialized - User ID: {has_user}, Secret: {has_secret}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        return bool(self.user_id and self.api_secret and self.app_code and self.access_token)
    
    def get_auth_url(self) -> str:
        """AliceBlue uses session-based authentication with username/password"""
        # AliceBlue uses session-based authentication, not OAuth2
        # Return a special URL to indicate session auth is needed
        return "session_auth_required"
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """AliceBlue doesn't use OAuth2 - this method shouldn't be called"""
        return {"error": "AliceBlue uses session-based authentication, not OAuth2. Use login_and_get_session_id() instead."}
    
    async def login_and_get_session_id(self, username: str, password: str, twofa: str, app_id: str, api_secret: str) -> Dict[str, Any]:
        """AliceBlue session-based authentication - official library pattern"""
        try:
            if not all([username, password, twofa, app_id, api_secret]):
                return {"error": "All credentials required: username, password, 2FA, app_id, api_secret"}
            
            # AliceBlue developer console API endpoints
            api_base = "https://v2api.aliceblueonline.com/restpy/api"
            
            async with httpx.AsyncClient() as client:
                # Step 1: Get encryption key
                enc_response = await client.get(
                    f"{api_base}/admin/enckey",
                    timeout=30.0
                )
                
                if enc_response.status_code != 200:
                    return {"error": "Failed to get encryption key", "details": enc_response.text}
                
                enc_data = enc_response.json()
                if not enc_data.get('encKey'):
                    return {"error": "Invalid encryption key response"}
                
                encryption_key = enc_data['encKey']
                
                # Step 2: Generate checksum - password + app_secret + encryption_key
                import hashlib
                combined_string = f"{password}{api_secret}{encryption_key}"
                checksum = hashlib.sha256(combined_string.encode()).hexdigest()
                
                # Step 3: Login and get session ID
                login_payload = {
                    "userId": username,
                    "userData": checksum,
                    "twoFA": twofa,
                    "appId": app_id
                }
                
                auth_response = await client.post(
                    f"{api_base}/customer/login",
                    json=login_payload,
                    timeout=30.0
                )
                
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    if auth_data.get('stat') == 'Ok' and auth_data.get('sessionID'):
                        self.access_token = auth_data.get('sessionID')
                        # Store credentials for future use
                        self.user_id = username
                        self.app_code = app_id
                        self.api_secret = api_secret
                        logger.info("AliceBlue session authentication successful")
                        return {"success": True, "session_id": self.access_token}
                    else:
                        error_msg = auth_data.get('emsg', 'Login failed')
                        return {"error": f"Authentication failed: {error_msg}"}
                else:
                    return {"error": "Login request failed", "details": auth_response.text}
                    
        except Exception as e:
            logger.error(f"AliceBlue session authentication error: {str(e)}")
            return {"error": "Authentication failed", "exception": str(e)}
    
    async def get_market_data(self, symbols: list) -> Dict[str, Any]:
        """Fetch market data for given symbols from AliceBlue API"""
        if not self.has_credentials():
            logger.warning("AliceBlue API credentials not available")
            return {"error": "No valid credentials"}
        
        try:
            # Map common symbols to AliceBlue format
            symbol_mapping = {
                'RELIANCE': 'RELIANCE',
                'TCS': 'TCS',
                'NIFTY': 'NIFTY 50',
                'BANKNIFTY': 'NIFTY BANK',
            }
            
            # Prepare symbols for API call
            alice_symbols = []
            for symbol in symbols:
                alice_symbol = symbol_mapping.get(symbol.upper(), symbol.upper())
                alice_symbols.append(alice_symbol)
            
            logger.info(f"Fetching AliceBlue market data for {len(alice_symbols)} symbols")
            
            async with httpx.AsyncClient() as client:
                # AliceBlue market data endpoint
                response = await client.post(
                    f"{self.base_url}/marketdata/getltp",
                    json={
                        'exch': 'NSE',
                        'symbol': alice_symbols,
                    },
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json',
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"AliceBlue API success: received data for {len(alice_symbols)} symbols")
                    
                    # Transform AliceBlue response to our standard format
                    result = {}
                    quotes_data = data.get('data', [])
                    
                    for i, symbol in enumerate(symbols):
                        if i < len(quotes_data):
                            quote_data = quotes_data[i]
                            result[symbol.upper()] = {
                                'last_price': float(quote_data.get('ltp', 0)),
                                'timestamp': datetime.now().isoformat(),
                                'change': float(quote_data.get('change', 0)),
                                'change_percent': float(quote_data.get('pChange', 0)),
                                'volume': int(quote_data.get('volume', 0)),
                                'high': float(quote_data.get('high', 0)),
                                'low': float(quote_data.get('low', 0)),
                                'open': float(quote_data.get('open', 0)),
                            }
                    
                    return {"success": True, "data": result, "source": "aliceblue"}
                    
                else:
                    logger.error(f"AliceBlue API error: {response.status_code} - {response.text}")
                    return {"error": "API request failed", "status_code": response.status_code}
                    
        except asyncio.TimeoutError:
            logger.error("AliceBlue API request timeout")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"AliceBlue API error: {str(e)}")
            return {"error": "API request failed", "exception": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            'has_user_id': bool(self.user_id),
            'has_access_token': bool(self.access_token),
            'has_credentials': self.has_credentials(),
            'status': 'authenticated' if self.has_credentials() else 'disconnected',
            'requires_login': not bool(self.access_token),
            'provider': 'aliceblue',
        }
    
    def disconnect(self):
        """Clear stored credentials"""
        self.access_token = None
        logger.info("AliceBlue API disconnected")
        return {"message": "AliceBlue disconnected successfully"}

# Singleton instance
aliceblue_service = AliceBlueAPIService()