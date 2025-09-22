"""
Fyers API Service - Barakah Trader Lite
Handles Fyers API authentication and market data integration
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

class FyersAPIService:
    def __init__(self):
        """Initialize Fyers API service with credentials from environment"""
        self.client_id = os.getenv('FYERS_CLIENT_ID')
        self.api_key = os.getenv('FYERS_API_KEY')
        self.api_secret = os.getenv('FYERS_API_SECRET')
        self.access_token = os.getenv('FYERS_ACCESS_TOKEN')
        self.base_url = 'https://api-t1.fyers.in/api/v3'
        # Use Replit domain for OAuth redirect
        replit_domain = os.getenv('REPLIT_DEV_DOMAIN') or 'localhost:8000'
        self.redirect_uri = f'https://{replit_domain}/api/v1/auth/fyers/callback'
        
        # Log initialization status
        has_key = "✓" if self.api_key else "✗"
        has_token = "✓" if self.access_token else "✗"
        logger.info(f"FyersAPIService initialized - API Key: {has_key}, Token: {has_token}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        return bool(self.api_key and self.access_token and self.client_id)
    
    def get_auth_url(self) -> str:
        """Generate Fyers OAuth URL for user authentication"""
        if not self.api_key:
            raise ValueError("Fyers API key not configured")
            
        # Fyers OAuth URL construction
        auth_url = f"https://myapi.fyers.in/oauth2/authorize?" \
                  f"client_id={self.api_key}&" \
                  f"response_type=code&" \
                  f"redirect_uri={self.redirect_uri}&" \
                  f"state=fyers_auth"
        
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                # Fyers token exchange endpoint
                response = await client.post(
                    "https://myapi.fyers.in/oauth2/token",
                    data={
                        'client_id': self.api_key,
                        'client_secret': self.api_secret,
                        'code': auth_code,
                        'redirect_uri': self.redirect_uri,
                        'grant_type': 'authorization_code',
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Fyers token exchange successful")
                    return token_data
                else:
                    logger.error(f"Fyers token exchange failed: {response.status_code} - {response.text}")
                    return {"error": "Token exchange failed", "details": response.text}
                    
        except Exception as e:
            logger.error(f"Fyers token exchange error: {str(e)}")
            return {"error": "Token exchange failed", "exception": str(e)}
    
    async def get_market_data(self, symbols: list) -> Dict[str, Any]:
        """Fetch market data for given symbols from Fyers API"""
        if not self.has_credentials():
            logger.warning("Fyers API credentials not available")
            return {"error": "No valid credentials"}
        
        try:
            # Map common symbols to Fyers format
            symbol_mapping = {
                'RELIANCE': 'NSE:RELIANCE-EQ',
                'TCS': 'NSE:TCS-EQ',
                'NIFTY': 'NSE:NIFTY50-INDEX',
                'BANKNIFTY': 'NSE:NIFTYBANK-INDEX',
            }
            
            # Prepare symbols for API call
            fyers_symbols = []
            for symbol in symbols:
                fyers_symbol = symbol_mapping.get(symbol.upper(), f'NSE:{symbol.upper()}-EQ')
                fyers_symbols.append(fyers_symbol)
            
            logger.info(f"Fetching Fyers market data for {len(fyers_symbols)} symbols")
            
            async with httpx.AsyncClient() as client:
                # Fyers market data endpoint
                symbols_str = ','.join(fyers_symbols)
                response = await client.get(
                    f"{self.base_url}/data/quotes",
                    params={
                        'symbols': symbols_str,
                    },
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json',
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Fyers API success: received data for {len(fyers_symbols)} symbols")
                    
                    # Transform Fyers response to our standard format
                    result = {}
                    quotes = data.get('d', {})
                    
                    for i, symbol in enumerate(symbols):
                        fyers_symbol = fyers_symbols[i]
                        if fyers_symbol in quotes:
                            quote_data = quotes[fyers_symbol]['v']
                            result[symbol.upper()] = {
                                'last_price': float(quote_data.get('lp', 0)),
                                'timestamp': datetime.now().isoformat(),
                                'change': float(quote_data.get('ch', 0)),
                                'change_percent': float(quote_data.get('chp', 0)),
                                'volume': int(quote_data.get('volume', 0)),
                                'high': float(quote_data.get('h', 0)),
                                'low': float(quote_data.get('l', 0)),
                                'open': float(quote_data.get('o', 0)),
                            }
                    
                    return {"success": True, "data": result, "source": "fyers"}
                    
                else:
                    logger.error(f"Fyers API error: {response.status_code} - {response.text}")
                    return {"error": "API request failed", "status_code": response.status_code}
                    
        except asyncio.TimeoutError:
            logger.error("Fyers API request timeout")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"Fyers API error: {str(e)}")
            return {"error": "API request failed", "exception": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            'has_api_key': bool(self.api_key),
            'has_access_token': bool(self.access_token),
            'has_credentials': self.has_credentials(),
            'status': 'authenticated' if self.has_credentials() else 'disconnected',
            'requires_login': not bool(self.access_token),
            'provider': 'fyers',
        }
    
    def disconnect(self):
        """Clear stored credentials"""
        self.access_token = None
        logger.info("Fyers API disconnected")
        return {"message": "Fyers disconnected successfully"}

# Singleton instance
fyers_service = FyersAPIService()