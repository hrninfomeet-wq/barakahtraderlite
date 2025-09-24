"""
Fyers API Service - Barakah Trader Lite
Handles Fyers API authentication and market data integration
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional
import json
import hashlib
from datetime import datetime
from loguru import logger
from core.security import CredentialVault
from models.trading import APIProvider

class FyersAPIService:
    def __init__(self):
        """Initialize Fyers API service with credentials from environment"""
        # For User App type, use environment variables for security
        self.client_id = os.getenv('FYERS_CLIENT_ID')
        self.api_key = self.client_id  # Same as client_id for User App
        self.api_secret = os.getenv('FYERS_API_SECRET')
        self.access_token = None
        self.base_url = 'https://api-t1.fyers.in'
        # For User App, use the official Fyers redirect URI
        self.redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
        
        # Initialize credential vault for secure token storage
        self.credential_vault = CredentialVault()
        self._load_stored_token()
        
        # Log initialization status
        has_key = "✓" if self.api_key else "✗"
        has_token = "✓" if self.access_token else "✗"
        logger.info(f"FyersAPIService initialized - API Key: {has_key}, Token: {has_token}")
    
    def _load_stored_token(self):
        """Load stored access token from secure storage"""
        try:
            # Load from environment variable for now
            # In production, would use proper secure storage
            self.access_token = os.getenv('FYERS_ACCESS_TOKEN')
            if self.access_token:
                logger.info("Fyers token loaded from environment")
            else:
                logger.debug("No Fyers token found in environment")
        except Exception as e:
            logger.warning(f"Failed to load stored Fyers token: {e}")
            self.access_token = None
    
    async def _store_token(self, token_data: Dict[str, Any]):
        """Store access token securely"""
        try:
            if 'access_token' in token_data:
                # Store in environment for persistence across requests
                # In production, would use proper secure storage like CredentialVault
                os.environ['FYERS_ACCESS_TOKEN'] = token_data['access_token']
                logger.info("Fyers token stored successfully")
        except Exception as e:
            logger.error(f"Failed to store Fyers token: {e}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials for API calls"""
        return bool(self.api_key and self.access_token)
    
    def get_auth_url(self) -> str:
        """Generate Fyers OAuth URL for user authentication - User App format"""
        if not self.client_id:
            raise ValueError("Fyers client_id not configured")
            
        # Fyers User App OAuth URL construction - matches official samples
        # Using the exact format from official Fyers User App documentation
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?" \
                  f"client_id={self.client_id}&" \
                  f"redirect_uri={self.redirect_uri}&" \
                  f"response_type=code&" \
                  f"state=sample_state"
        
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            # Check required credentials
            if not self.api_key or not self.api_secret:
                return {"error": "Missing Fyers API credentials", "details": "API key or secret not configured"}
            
            # Generate appIdHash as per Fyers User App v3 API specification
            app_id_hash = hashlib.sha256(f"{self.client_id}:{self.api_secret}".encode('utf-8')).hexdigest()
            
            async with httpx.AsyncClient() as client:
                # Fyers v3 token exchange endpoint - updated to correct URL
                response = await client.post(
                    "https://api-t1.fyers.in/api/v3/validate-authcode",
                    json={
                        'grant_type': 'authorization_code',
                        'appIdHash': app_id_hash,
                        'code': auth_code,
                        'client_id': self.client_id  # User App client_id
                    },
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    # Save the access token to the service instance and persist it
                    if 'access_token' in token_data:
                        self.access_token = token_data['access_token']
                        await self._store_token(token_data)
                        logger.info(f"Fyers token exchange successful - token saved and persisted")
                    else:
                        logger.warning(f"Fyers token response missing access_token: {token_data}")
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
                'WIPRO': 'NSE:WIPRO-EQ',
                'DEVYANI': 'NSE:DEVYANI-EQ',
                'DEVIT': 'NSE:DEVYANI-EQ',  # Alternative name for DEVYANI
                'BEL': 'NSE:BEL-EQ',
                'TATAMOTORS': 'NSE:TATAMOTORS-EQ',
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
                        'Authorization': f'{self.client_id}:{self.access_token}',
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Fyers API success: received data for {len(fyers_symbols)} symbols")
                    
                    # Transform Fyers response to our standard format
                    # Fyers v3 returns array under 'd' key: [{'symbol': 'NSE:RELIANCE-EQ', 'v': {...}}, ...]
                    result = {}
                    quotes_array = data.get('d', [])
                    
                    # Create symbol mapping for quick lookup
                    symbol_to_original = {fyers_symbols[i]: symbols[i] for i in range(len(symbols))}
                    
                    for quote_item in quotes_array:
                        if isinstance(quote_item, dict) and 'n' in quote_item and 'v' in quote_item:
                            fyers_symbol = quote_item['n']  # 'n' contains the symbol name in Fyers API
                            quote_data = quote_item['v']
                            original_symbol = symbol_to_original.get(fyers_symbol)
                            
                            if original_symbol:
                                result[original_symbol.upper()] = {
                                    'last_price': float(quote_data.get('lp', 0)),
                                    'timestamp': datetime.now().isoformat(),
                                    'change': float(quote_data.get('ch', 0)),
                                    'change_percent': float(quote_data.get('chp', 0)),
                                    'volume': int(quote_data.get('volume', 0)),
                                    'high': float(quote_data.get('high_price', 0)),
                                    'low': float(quote_data.get('low_price', 0)),
                                    'open': float(quote_data.get('open_price', 0)),
                                    'prev_close': float(quote_data.get('prev_close_price', 0)),
                                    'bid': float(quote_data.get('bid', 0)),
                                    'ask': float(quote_data.get('ask', 0)),
                                }
                    
                    # Ensure we have data for all requested symbols
                    for symbol in symbols:
                        if symbol.upper() not in result:
                            result[symbol.upper()] = {
                                'last_price': None,
                                'error': 'No data received',
                                'timestamp': datetime.now().isoformat()
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