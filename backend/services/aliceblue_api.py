"""
AliceBlue API Service - Barakah Trader Lite
Comprehensive AliceBlue API integration with OAuth 2.0 flow and full trading capabilities
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime, timedelta
from loguru import logger
from core.security import CredentialVault
from models.trading import APIProvider

class AliceBlueAPIService:
    def __init__(self):
        """Initialize AliceBlue API service with OAuth 2.0 credentials"""
        # OAuth 2.0 Configuration - Individual Trader API credentials
        self.user_id = os.getenv('ALICEBLUE_USER_ID', 'AB104570')
        # Force use of Individual Trader app code temporarily until env vars update
        env_api_key = os.getenv('ALICEBLUE_API_KEY')
        if env_api_key and len(env_api_key) > 50:  # Old vendor key detected
            self.api_key = '7vDzljpGdC'  # Individual Trader app code
            logger.info("Using Individual Trader app code (temp override)")
        else:
            self.api_key = env_api_key
        self.app_code = self.api_key  # Same as API key for AliceBlue
        self.api_secret = os.getenv('ALICEBLUE_API_SECRET')
        
        # Validate required credentials
        if not self.api_key:
            logger.error("ALICEBLUE_API_KEY environment variable is required")
        if not self.api_secret:
            logger.error("ALICEBLUE_API_SECRET environment variable is required")
        if not self.user_id:
            logger.error("ALICEBLUE_USER_ID environment variable is required")
        
        # AliceBlue API URLs
        self.base_url = 'https://ant.aliceblueonline.com/open-api/od/v1'
        # Auth URL will be constructed dynamically using environment API key
        
        # OAuth configuration
        replit_domain = os.getenv('REPLIT_DEV_DOMAIN', 'localhost:5000')
        self.redirect_uri = f'http://{replit_domain}/api/v1/auth/aliceblue/callback'
        
        # Session management
        self.access_token = None
        self.session_id = None
        self.token_expires_at = None
        
        # Initialize credential vault for secure token storage
        self.credential_vault = CredentialVault()
        self._load_stored_token()
        
        # Log initialization status
        has_key = "✓" if self.api_key else "✗"
        has_secret = "✓" if self.api_secret else "✗"
        has_token = "✓" if self.access_token else "✗"
        logger.info(f"AliceBlueAPIService initialized - API Key: {has_key}, Secret: {has_secret}, Token: {has_token}")
    
    def _load_stored_token(self):
        """Load stored access token with expiry check from secure CredentialVault"""
        try:
            # Skip token loading during initialization to avoid event loop issues
            # Token will be loaded asynchronously when needed
            logger.debug("Token loading deferred - will load asynchronously when needed")
            self.access_token = None
            self.session_id = None
            self.token_expires_at = None
                
        except Exception as e:
            logger.warning(f"Failed to initialize token loading: {e}")
            self.access_token = None
            self.session_id = None
            self.token_expires_at = None
    
    async def _ensure_token_loaded(self):
        """Safely load stored token in async context"""
        try:
            from models.trading import APIProvider
            
            # Check if we already have a valid token
            if self.access_token and self.token_expires_at:
                if datetime.now() < self.token_expires_at - timedelta(minutes=30):
                    return  # Token is still valid
            
            # Initialize credential vault if needed
            await self.credential_vault.initialize()
            
            # Retrieve token from secure CredentialVault
            token_data = await self.credential_vault.retrieve_auth_token(APIProvider.ALICEBLUE)
            
            if token_data:
                self.access_token = token_data.get('access_token')
                self.session_id = token_data.get('session_id')
                expires_str = token_data.get('expires_at')
                
                if expires_str:
                    self.token_expires_at = datetime.fromisoformat(expires_str)
                else:
                    # Fallback to stored_at + 24 hours for AliceBlue tokens
                    stored_at_str = token_data.get('stored_at')
                    if stored_at_str:
                        stored_at = datetime.fromisoformat(stored_at_str)
                        self.token_expires_at = stored_at + timedelta(hours=24)
                    else:
                        self.token_expires_at = datetime.now() + timedelta(hours=24)
                
                logger.info("AliceBlue token loaded from secure CredentialVault")
            else:
                logger.debug("No AliceBlue token found in CredentialVault")
                
        except Exception as e:
            logger.warning(f"Failed to load stored AliceBlue token from CredentialVault: {e}")
    
    async def _store_token(self, token_data: Dict[str, Any]):
        """Store access token with expiry information in secure CredentialVault"""
        try:
            from models.trading import APIProvider
            
            if 'access_token' in token_data or 'session_id' in token_data:
                self.access_token = token_data.get('access_token')
                self.session_id = token_data.get('session_id')
                
                # Calculate expiry time (AliceBlue tokens typically last 24 hours)
                expires_at = datetime.now() + timedelta(hours=24)
                self.token_expires_at = expires_at
                
                # Prepare token data for secure storage
                secure_token_data = {
                    'access_token': self.access_token,
                    'session_id': self.session_id,
                    'expires_at': expires_at.isoformat(),
                    'lifetime_hours': 24,
                    'token_type': 'aliceblue_session_token'
                }
                
                # Store in secure CredentialVault
                await self.credential_vault.store_auth_token(
                    APIProvider.ALICEBLUE, 
                    secure_token_data
                )
                
                logger.info(f"AliceBlue token securely stored - expires at {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Failed to store AliceBlue token in CredentialVault: {e}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        # Check environment variables first
        if not self.api_key:
            logger.warning("AliceBlue API key not configured in environment")
            return False
        if not self.api_secret:
            logger.warning("AliceBlue API secret not configured in environment")
            return False
        if not self.user_id:
            logger.warning("AliceBlue User ID not configured in environment")
            return False
            
        # Check for access token
        if not (self.access_token or self.session_id):
            return False
            
        # Check if token has expired
        if self.token_expires_at and datetime.now() >= self.token_expires_at - timedelta(minutes=30):
            logger.warning("AliceBlue token has expired or will expire soon")
            return False
            
        return True
    
    def get_auth_url(self) -> str:
        """Generate AliceBlue OAuth URL for user authentication"""
        if not self.api_key:
            raise ValueError("AliceBlue API key not configured in environment variables")
            
        # AliceBlue auth URL construction using environment API key (dynamic)
        auth_url = f"https://ant.aliceblueonline.com/?appcode={self.api_key}&redirect_uri={self.redirect_uri}"
        
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for access token using SHA-256 checksum authentication"""
        try:
            # Check required credentials
            if not self.api_key or not self.api_secret:
                return {"error": "Missing AliceBlue API credentials", "details": "API key or secret not configured"}
            
            # Use provided user_id or default
            actual_user_id = user_id or self.user_id
            
            # Generate SHA-256 checksum as specified: userId + authCode + apiSecret
            checksum_string = f"{actual_user_id}{auth_code}{self.api_secret}"
            checksum = hashlib.sha256(checksum_string.encode('utf-8')).hexdigest()
            
            async with httpx.AsyncClient() as client:
                # AliceBlue session endpoint as specified
                response = await client.post(
                    f"{self.base_url}/vendor/getUserDetails",
                    json={
                        'userId': actual_user_id,
                        'authCode': auth_code,
                        'checksum': checksum,
                        'appCode': self.api_key
                    },
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'BarakahTrader/1.0',
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'success' and data.get('data'):
                        session_data = data['data']
                        session_id = session_data.get('sessionId') or session_data.get('sessionID')
                        
                        if session_id:
                            # Store token securely
                            token_data = {
                                'session_id': session_id,
                                'access_token': session_id,  # Use session_id as access_token
                                'user_id': actual_user_id
                            }
                            
                            await self._store_token(token_data)
                            
                            logger.info("AliceBlue OAuth authentication successful")
                            return {
                                "success": True,
                                "access_token": session_id,
                                "session_id": session_id,
                                "expires_in": 86400,  # 24 hours
                                "token_type": "Bearer"
                            }
                        else:
                            return {"error": "No session ID received", "details": data}
                    else:
                        error_msg = data.get('message', 'Authentication failed')
                        return {"error": f"Authentication failed: {error_msg}", "details": data}
                else:
                    error_text = response.text
                    logger.error(f"AliceBlue auth failed: {response.status_code} - {error_text}")
                    return {"error": "Authentication request failed", "status_code": response.status_code, "details": error_text}
                    
        except Exception as e:
            logger.error(f"AliceBlue token exchange error: {str(e)}")
            return {"error": "Token exchange failed", "exception": str(e)}
    
    async def _make_authenticated_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request to AliceBlue"""
        # Ensure token is loaded
        await self._ensure_token_loaded()
        
        if not self.has_credentials():
            return {"error": "No valid credentials available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token or self.session_id}',
            'Content-Type': 'application/json',
            'User-Agent': 'BarakahTrader/1.0',
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == 'GET':
                    response = await client.get(url, headers=headers, timeout=30.0)
                elif method.upper() == 'POST':
                    response = await client.post(url, json=data, headers=headers, timeout=30.0)
                elif method.upper() == 'PUT':
                    response = await client.put(url, json=data, headers=headers, timeout=30.0)
                elif method.upper() == 'DELETE':
                    response = await client.delete(url, headers=headers, timeout=30.0)
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"AliceBlue API error: {response.status_code} - {response.text}")
                    return {"error": "API request failed", "status_code": response.status_code, "details": response.text}
                    
        except Exception as e:
            logger.error(f"AliceBlue API request error: {str(e)}")
            return {"error": "API request failed", "exception": str(e)}
    
    # ===============================
    # ORDER MANAGEMENT APIs
    # ===============================
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a new order"""
        logger.info(f"Placing AliceBlue order: {order_data}")
        return await self._make_authenticated_request('POST', '/orders', order_data)
    
    async def modify_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing order"""
        logger.info(f"Modifying AliceBlue order {order_id}: {order_data}")
        return await self._make_authenticated_request('PUT', f'/orders/{order_id}', order_data)
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        logger.info(f"Cancelling AliceBlue order: {order_id}")
        return await self._make_authenticated_request('DELETE', f'/orders/{order_id}')
    
    async def get_order_history(self) -> Dict[str, Any]:
        """Get order history"""
        logger.info("Fetching AliceBlue order history")
        return await self._make_authenticated_request('GET', '/orders')
    
    async def get_order_book(self) -> Dict[str, Any]:
        """Get current order book"""
        logger.info("Fetching AliceBlue order book")
        return await self._make_authenticated_request('GET', '/orders/pending')
    
    async def get_trade_book(self) -> Dict[str, Any]:
        """Get trade book / executed orders"""
        logger.info("Fetching AliceBlue trade book")
        return await self._make_authenticated_request('GET', '/trades')
    
    # ===============================
    # PORTFOLIO MANAGEMENT APIs
    # ===============================
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        logger.info("Fetching AliceBlue positions")
        return await self._make_authenticated_request('GET', '/positions')
    
    async def get_holdings(self) -> Dict[str, Any]:
        """Get holdings / investments"""
        logger.info("Fetching AliceBlue holdings")
        return await self._make_authenticated_request('GET', '/holdings')
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        logger.info("Fetching AliceBlue portfolio summary")
        return await self._make_authenticated_request('GET', '/portfolio')
    
    # ===============================
    # MARKET DATA APIs
    # ===============================
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch market data for given symbols from AliceBlue API"""
        # Ensure token is loaded
        await self._ensure_token_loaded()
        
        if not self.has_credentials():
            logger.warning("AliceBlue API credentials not available")
            return {"error": "No valid credentials"}
        
        try:
            # Map common symbols to AliceBlue format
            symbol_mapping = {
                'RELIANCE': 'NSE:RELIANCE-EQ',
                'TCS': 'NSE:TCS-EQ',
                'NIFTY': 'NSE:NIFTY50-INDEX',
                'BANKNIFTY': 'NSE:BANKNIFTY-INDEX',
            }
            
            # Prepare symbols for API call
            alice_symbols = []
            for symbol in symbols:
                alice_symbol = symbol_mapping.get(symbol.upper(), f'NSE:{symbol.upper()}-EQ')
                alice_symbols.append(alice_symbol)
            
            logger.info(f"Fetching AliceBlue market data for {len(alice_symbols)} symbols")
            
            # Use AliceBlue quote API
            quote_data = {
                'symbols': alice_symbols
            }
            
            result = await self._make_authenticated_request('POST', '/quotes', quote_data)
            
            if result.get('status') == 'success' and result.get('data'):
                quotes = result['data']
                
                # Transform AliceBlue response to our standard format
                transformed_result = {}
                
                for i, symbol in enumerate(symbols):
                    if i < len(quotes):
                        quote = quotes[i]
                        transformed_result[symbol.upper()] = {
                            'last_price': float(quote.get('ltp', 0)),
                            'timestamp': datetime.now().isoformat(),
                            'change': float(quote.get('netChange', 0)),
                            'change_percent': float(quote.get('pChange', 0)),
                            'volume': int(quote.get('volume', 0)),
                            'high': float(quote.get('dayHigh', 0)),
                            'low': float(quote.get('dayLow', 0)),
                            'open': float(quote.get('dayOpen', 0)),
                            'bid': float(quote.get('bid', 0)),
                            'ask': float(quote.get('ask', 0)),
                        }
                
                return {"success": True, "data": transformed_result, "source": "aliceblue"}
            else:
                return {"error": result.get('message', 'Failed to fetch market data'), "details": result}
                    
        except Exception as e:
            logger.error(f"AliceBlue market data error: {str(e)}")
            return {"error": "Market data request failed", "exception": str(e)}
    
    async def get_historical_data(self, symbol: str, interval: str = '1day', from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
        """Get historical data for a symbol"""
        logger.info(f"Fetching AliceBlue historical data for {symbol}")
        
        params = {
            'symbol': symbol,
            'interval': interval
        }
        
        if from_date:
            params['from_date'] = from_date
        if to_date:
            params['to_date'] = to_date
            
        return await self._make_authenticated_request('GET', f'/historical?{self._build_query_string(params)}')
    
    # ===============================
    # FUNDS AND PROFILE APIs
    # ===============================
    
    async def get_funds(self) -> Dict[str, Any]:
        """Get available funds and margins"""
        logger.info("Fetching AliceBlue funds")
        return await self._make_authenticated_request('GET', '/funds')
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        logger.info("Fetching AliceBlue profile")
        return await self._make_authenticated_request('GET', '/profile')
    
    # ===============================
    # UTILITY METHODS
    # ===============================
    
    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """Build query string from parameters"""
        return '&'.join([f"{k}={v}" for k, v in params.items() if v is not None])
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        # Try to load token first
        await self._ensure_token_loaded()
        
        return {
            'has_api_key': bool(self.api_key),
            'has_api_secret': bool(self.api_secret),
            'has_access_token': bool(self.access_token or self.session_id),
            'has_credentials': self.has_credentials(),
            'status': 'authenticated' if self.has_credentials() else 'disconnected',
            'provider': 'aliceblue',
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
        }
    
    async def logout(self) -> Dict[str, Any]:
        """Clear stored tokens and logout"""
        try:
            # Clear tokens from CredentialVault
            await self.credential_vault.delete_auth_token(APIProvider.ALICEBLUE)
            
            # Clear local tokens
            self.access_token = None
            self.session_id = None
            self.token_expires_at = None
            
            logger.info("AliceBlue logout successful")
            return {"success": True, "message": "AliceBlue logged out successfully"}
            
        except Exception as e:
            logger.error(f"AliceBlue logout error: {str(e)}")
            return {"error": "Logout failed", "exception": str(e)}

# Singleton instance
aliceblue_service = AliceBlueAPIService()