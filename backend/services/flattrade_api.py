"""
Flattrade API Service - Barakah Trader Lite
Handles Flattrade API authentication and market data integration
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

class FlattradeAPIService:
    def __init__(self):
        """Initialize Flattrade API service with credentials from environment"""
        self.api_key = os.getenv('FLATTRADE_API_KEY')
        self.api_secret = os.getenv('FLATTRADE_API_SECRET')
        self.access_token = os.getenv('FLATTRADE_ACCESS_TOKEN')
        self.client_code = os.getenv('FLATTRADE_CLIENT_CODE')
        self.request_code = os.getenv('FLATTRADE_REQUEST_CODE')
        self.api_url = os.getenv('FLATTRADE_API_URL', 'https://piconnect.flattrade.in/PiConnectTP/')
        # Use Replit domain for OAuth redirect
        replit_domain = os.getenv('REPLIT_DEV_DOMAIN') or 'localhost:8000'
        self.redirect_uri = os.getenv('FLATTRADE_REDIRECT_URI', f'https://{replit_domain}/api/v1/auth/flattrade/callback')
        
        # Log initialization status
        has_key = "✓" if self.api_key else "✗"
        has_token = "✓" if self.access_token else "✗"
        logger.info(f"FlattradeAPIService initialized - API Key: {has_key}, Token: {has_token}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        return bool(self.api_key and self.access_token and self.client_code)
    
    def get_auth_url(self) -> str:
        """Generate Flattrade OAuth URL for user authentication"""
        if not self.api_key:
            raise ValueError("Flattrade API key not configured")
            
        # Flattrade OAuth URL construction
        auth_url = f"{self.api_url}Connect/Login?" \
                  f"AppKey={self.api_key}&" \
                  f"ResponseType=code&" \
                  f"RedirectURI={self.redirect_uri}"
        
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                # Flattrade token exchange endpoint
                response = await client.post(
                    f"{self.api_url}Connect/Token",
                    data={
                        'AppKey': self.api_key,
                        'AppSecret': self.api_secret,
                        'AuthCode': auth_code,
                        'RedirectURI': self.redirect_uri,
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Flattrade token exchange successful")
                    return token_data
                else:
                    logger.error(f"Flattrade token exchange failed: {response.status_code} - {response.text}")
                    return {"error": "Token exchange failed", "details": response.text}
                    
        except Exception as e:
            logger.error(f"Flattrade token exchange error: {str(e)}")
            return {"error": "Token exchange failed", "exception": str(e)}
    
    async def get_market_data(self, symbols: list) -> Dict[str, Any]:
        """Fetch market data for given symbols from Flattrade API"""
        if not self.has_credentials():
            logger.warning("Flattrade API credentials not available")
            return {"error": "No valid credentials"}
        
        try:
            # Map common symbols to Flattrade instrument tokens
            symbol_mapping = {
                'RELIANCE': 'NSE|2885',  # Reliance Industries
                'TCS': 'NSE|11536',      # TCS
                'NIFTY': 'NSE|26000',    # Nifty 50
                'BANKNIFTY': 'NSE|26009', # Bank Nifty
            }
            
            # Prepare instruments for API call
            instruments = []
            for symbol in symbols:
                flattrade_symbol = symbol_mapping.get(symbol.upper(), f'NSE|{symbol.upper()}')
                instruments.append(flattrade_symbol)
            
            logger.info(f"Fetching Flattrade market data for {len(instruments)} symbols")
            
            async with httpx.AsyncClient() as client:
                # Flattrade market data endpoint
                response = await client.post(
                    f"{self.api_url}MarketData/GetQuotes",
                    json={
                        'uid': self.client_code,
                        'actid': self.client_code,
                        'exch': 'NSE',
                        'token': instruments,
                    },
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json',
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Flattrade API success: received data for {len(instruments)} instruments")
                    
                    # Transform Flattrade response to our standard format
                    result = {}
                    for i, symbol in enumerate(symbols):
                        if i < len(data.get('values', [])):
                            quote_data = data['values'][i]
                            result[symbol.upper()] = {
                                'last_price': float(quote_data.get('lp', 0)),
                                'timestamp': datetime.now().isoformat(),
                                'change': float(quote_data.get('c', 0)),
                                'change_percent': float(quote_data.get('pc', 0)),
                                'volume': int(quote_data.get('v', 0)),
                                'high': float(quote_data.get('h', 0)),
                                'low': float(quote_data.get('l', 0)),
                                'open': float(quote_data.get('o', 0)),
                            }
                    
                    return {"success": True, "data": result, "source": "flattrade"}
                    
                else:
                    logger.error(f"Flattrade API error: {response.status_code} - {response.text}")
                    return {"error": "API request failed", "status_code": response.status_code}
                    
        except asyncio.TimeoutError:
            logger.error("Flattrade API request timeout")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"Flattrade API error: {str(e)}")
            return {"error": "API request failed", "exception": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            'has_api_key': bool(self.api_key),
            'has_access_token': bool(self.access_token),
            'has_credentials': self.has_credentials(),
            'status': 'authenticated' if self.has_credentials() else 'disconnected',
            'requires_login': not bool(self.access_token),
            'provider': 'flattrade',
        }
    
    def disconnect(self):
        """Clear stored credentials"""
        self.access_token = None
        logger.info("Flattrade API disconnected")
        return {"message": "Flattrade disconnected successfully"}

# Singleton instance
flattrade_service = FlattradeAPIService()