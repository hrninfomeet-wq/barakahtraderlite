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
        self.user_id = os.getenv('ALICEBLUE_USER_ID')
        self.app_code = os.getenv('ALICEBLUE_APP_CODE')
        self.api_secret = os.getenv('ALICEBLUE_API_SECRET')
        self.base_url = os.getenv('ALICEBLUE_API_BASE_URL', 'https://ant.aliceblueonline.com/api/v2')
        self.redirect_uri = os.getenv('ALICEBLUE_REDIRECT_URI', 'http://localhost:5000/api/providers/auth/aliceblue/callback')
        self.access_token = None  # Will be set after authentication
        
        # Log initialization status
        has_user = "✓" if self.user_id else "✗"
        has_secret = "✓" if self.api_secret else "✗"
        logger.info(f"AliceBlueAPIService initialized - User ID: {has_user}, Secret: {has_secret}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        return bool(self.user_id and self.api_secret and self.app_code and self.access_token)
    
    def get_auth_url(self) -> str:
        """Generate AliceBlue OAuth URL for user authentication"""
        if not self.app_code:
            raise ValueError("AliceBlue app code not configured")
            
        # AliceBlue OAuth URL construction
        auth_url = f"https://ant.aliceblueonline.com/oauth2/auth?" \
                  f"client_id={self.app_code}&" \
                  f"response_type=code&" \
                  f"redirect_uri={self.redirect_uri}&" \
                  f"state=aliceblue_auth"
        
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                # AliceBlue token exchange endpoint
                response = await client.post(
                    f"{self.base_url}/oauth2/token",
                    data={
                        'client_id': self.app_code,
                        'client_secret': self.api_secret,
                        'code': auth_code,
                        'redirect_uri': self.redirect_uri,
                        'grant_type': 'authorization_code',
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get('access_token')
                    logger.info("AliceBlue token exchange successful")
                    return token_data
                else:
                    logger.error(f"AliceBlue token exchange failed: {response.status_code} - {response.text}")
                    return {"error": "Token exchange failed", "details": response.text}
                    
        except Exception as e:
            logger.error(f"AliceBlue token exchange error: {str(e)}")
            return {"error": "Token exchange failed", "exception": str(e)}
    
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