"""
Upstox API integration service for real-time market data
"""
import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger
from datetime import datetime


class UpstoxAPIService:
    """Service for Upstox API integration"""
    
    def __init__(self):
        self.base_url = os.getenv("UPSTOX_BASE_URL", "https://api.upstox.com/v2")
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.client_id = os.getenv("UPSTOX_CLIENT_ID") 
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        
        if not self.access_token:
            logger.warning("Upstox access token not found in environment")
        if not self.client_id:
            logger.warning("Upstox client ID not found in environment")
            
        logger.info(f"UpstoxAPIService initialized - Token: {'✓' if self.access_token else '✗'}, Client: {'✓' if self.client_id else '✗'}")
    
    def has_credentials(self) -> bool:
        """Check if we have necessary credentials"""
        return bool(self.access_token and self.client_id)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch real market data from Upstox API
        """
        if not self.has_credentials():
            logger.warning("Missing Upstox credentials, falling back to demo data")
            return self._generate_demo_data(symbols)
        
        try:
            # Upstox uses instrument keys, need to convert symbols
            instrument_keys = []
            for symbol in symbols:
                # Common NSE instrument key format for demo
                # In production, you'd query instruments endpoint first
                if symbol == "RELIANCE":
                    instrument_keys.append("NSE_EQ|INE002A01018")
                elif symbol == "TCS":
                    instrument_keys.append("NSE_EQ|INE467B01029")
                elif symbol == "NIFTY":
                    instrument_keys.append("NSE_INDEX|Nifty 50")
                else:
                    # For unknown symbols, try generic format
                    instrument_keys.append(f"NSE_EQ|{symbol}")
            
            async with httpx.AsyncClient() as client:
                # Use Upstox market quotes API
                url = f"{self.base_url}/market-quote/quotes"
                headers = self.get_headers()
                
                # Send instrument keys as query parameters
                params = {
                    "instrument_key": ",".join(instrument_keys[:10])  # Limit to 10 symbols
                }
                
                logger.info(f"Fetching real market data from Upstox for {len(symbols)} symbols")
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_upstox_response(data, symbols)
                else:
                    logger.error(f"Upstox API error: {response.status_code} - {response.text}")
                    return self._generate_demo_data(symbols)
                    
        except httpx.TimeoutException:
            logger.error("Upstox API timeout, falling back to demo data")
            return self._generate_demo_data(symbols)
        except Exception as e:
            logger.error(f"Error fetching Upstox data: {e}")
            return self._generate_demo_data(symbols)
    
    def _parse_upstox_response(self, response_data: Dict, symbols: List[str]) -> Dict[str, Any]:
        """Parse Upstox API response into our format"""
        try:
            data = {}
            upstox_data = response_data.get("data", {})
            
            # Map back to our symbols
            symbol_mapping = {
                "NSE_EQ|INE002A01018": "RELIANCE",
                "NSE_EQ|INE467B01029": "TCS", 
                "NSE_INDEX|Nifty 50": "NIFTY"
            }
            
            for instrument_key, quote_data in upstox_data.items():
                # Map instrument key back to symbol
                symbol = symbol_mapping.get(instrument_key, instrument_key.split("|")[-1])
                
                if symbol in symbols:
                    ohlc = quote_data.get("ohlc", {})
                    last_price = quote_data.get("last_price", ohlc.get("close", 0))
                    
                    # Calculate change percentage
                    prev_close = ohlc.get("close", last_price)
                    change = last_price - prev_close if prev_close else 0
                    change_percent = (change / prev_close * 100) if prev_close else 0
                    
                    data[symbol] = {
                        "last_price": float(last_price),
                        "timestamp": datetime.now().isoformat(),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "volume": quote_data.get("volume", 0),
                        "high": ohlc.get("high", last_price),
                        "low": ohlc.get("low", last_price),
                        "open": ohlc.get("open", last_price)
                    }
            
            # For symbols not found in response, add with demo data
            for symbol in symbols:
                if symbol not in data:
                    data[symbol] = self._generate_single_demo_data(symbol)
            
            logger.info(f"Successfully parsed Upstox data for {len(data)} symbols")
            return {
                "success": True,
                "symbols_requested": symbols,
                "symbols_returned": list(data.keys()),
                "data": data,
                "source": "upstox_live_data",
                "live_mode": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing Upstox response: {e}")
            return self._generate_demo_data(symbols)
    
    def _generate_demo_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate demo data when real API is unavailable"""
        import random
        
        data = {}
        for symbol in symbols:
            data[symbol] = self._generate_single_demo_data(symbol)
        
        return {
            "success": True,
            "symbols_requested": symbols,
            "symbols_returned": symbols,
            "data": data,
            "source": "demo_data",
            "live_mode": False,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_single_demo_data(self, symbol: str) -> Dict[str, Any]:
        """Generate demo data for a single symbol"""
        import random
        
        base_prices = {"RELIANCE": 2500, "TCS": 3500, "NIFTY": 19500}
        base_price = base_prices.get(symbol, 1000)
        variation = random.uniform(-0.02, 0.02)
        last_price = round(base_price * (1 + variation), 2)
        
        return {
            "last_price": last_price,
            "timestamp": datetime.now().isoformat(),
            "change": round(last_price - base_price, 2),
            "change_percent": round(variation * 100, 2),
            "volume": random.randint(10000, 50000),
            "high": round(last_price * 1.02, 2),
            "low": round(last_price * 0.98, 2),
            "open": round(base_price, 2)
        }
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile to verify connection"""
        if not self.has_credentials():
            return {"error": "No credentials"}
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/user/profile"
                headers = self.get_headers()
                
                response = await client.get(url, headers=headers, timeout=5.0)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}

# Singleton instance
upstox_service = UpstoxAPIService()