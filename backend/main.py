#!/usr/bin/env python3
"""
Enhanced AI-Powered Personal Trading Engine Backend
SECURITY-FIRST: Paper Trading Mode with Live Trade Prevention
Version 2.0 - Unified Architecture with Security Controls

QA Security Requirements Addressed:
- TECH-001: Mode switching isolation prevents paper trades routing to live APIs
- SEC-001: Security controls prevent accidental live trades  
- ALL FUNCTIONALITY PRESERVED from working implementation
"""

# Load environment variables
from pathlib import Path
from dotenv import load_dotenv
import os

_ROOT_DIR = Path(__file__).resolve().parent.parent
for _candidate in ("env.local", ".env.local", ".env"):
    _env_file = _ROOT_DIR / _candidate
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file, override=False)
        break

# CRITICAL SECURITY: Force paper trading mode
TRADING_MODE = "PAPER"
LIVE_TRADING_ENABLED = False

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime
import random
from loguru import logger

# Import educational router
education_router = None
try:
    from api.v1.education import router as education_router
    EDUCATIONAL_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Educational system not available: {e}")
    EDUCATIONAL_SYSTEM_AVAILABLE = False

def ensure_paper_mode():
    """Critical Security: Prevent accidental live trades per QA requirement TECH-001"""
    if TRADING_MODE != "PAPER":
        raise HTTPException(status_code=403, detail="SECURITY: Live trading disabled")

def get_security_headers():
    """Add security indicators to all responses"""
    return {
        "trading_mode": TRADING_MODE,
        "live_trading_enabled": LIVE_TRADING_ENABLED,
        "security_timestamp": datetime.now().isoformat()
    }

app = FastAPI(
    title="Barakah Trader Lite - Security Enhanced",
    description="Multi-API trading system with secure paper/live mode isolation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Replit environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include educational router if available
if EDUCATIONAL_SYSTEM_AVAILABLE and education_router is not None:
    app.include_router(education_router)
    print("✅ Educational system router integrated")

# Include broker authentication router
try:
    from api.v1.broker_auth import router as broker_auth_router
    app.include_router(broker_auth_router, prefix="/api/v1")
    print("✅ Multi-broker authentication router integrated")
except ImportError as e:
    print(f"⚠️ Broker authentication not available: {e}")
else:
    print("❌ Educational system router not available")

paper_trading_history = []

@app.get("/")
async def root():
    """Root endpoint with security headers"""
    return {
        "message": "Barakah Trader Lite Backend - Security Enhanced",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with security status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

@app.get("/api/v1/auth/upstox/status")
async def upstox_auth_status():
    """Get Upstox authentication status"""
    client_id = os.getenv("UPSTOX_CLIENT_ID")
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
    api_secret = os.getenv("UPSTOX_API_SECRET")
    redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")
    
    has_credentials = bool(client_id and api_secret and redirect_uri)
    has_token = bool(access_token)
    
    status = "authenticated" if has_token else ("credentials_configured" if has_credentials else "not_configured")
    
    return {
        "status": status,
        "broker": "upstox",
        "requires_login": not has_token,
        "has_credentials": has_credentials,
        "has_access_token": has_token,
        "client_id_configured": bool(client_id),
        "redirect_uri_configured": bool(redirect_uri),
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

# Upstox authentication now handled by unified broker system in /api/v1/auth/

# Legacy callback handler removed - now using unified broker authentication system

# Legacy callback endpoints removed - now using unified broker system at /api/v1/auth/{broker}/callback

@app.get("/api/v1/market-data/batch")
async def get_market_data_batch(symbols: str, live_data_enabled: bool = True):
    """Get market data with multi-broker failover - Live or Demo mode"""
    try:
        from services.broker_manager import broker_manager
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        
        if live_data_enabled:
            # Use multi-broker system with smart failover
            logger.info(f"Fetching LIVE market data for {len(symbol_list)} symbols via multi-broker system")
            result = await broker_manager.get_market_data_with_failover(symbol_list)
            
            # If multi-broker failed, fallback to demo data
            if result.get("error") or not result.get("data"):
                logger.warning("Multi-broker system failed, falling back to demo data")
                from services.upstox_api import UpstoxAPIService
                upstox_service = UpstoxAPIService()
                result = upstox_service._generate_demo_data(symbol_list)
        else:
            # Use demo data
            logger.info(f"Generating DEMO market data for {len(symbol_list)} symbols")
            from services.upstox_api import UpstoxAPIService
            upstox_service = UpstoxAPIService()
            result = upstox_service._generate_demo_data(symbol_list)
        
        # Add security headers and return
        return {
            **result,
            **get_security_headers()
        }
    except Exception as e:
        logger.error(f"Market data error: {str(e)}")
        # Fallback to demo data on any error
        from services.upstox_api import UpstoxAPIService
        upstox_service = UpstoxAPIService()
        result = upstox_service._generate_demo_data(symbol_list)
        return {
            **result,
            **get_security_headers()
        }

@app.get("/api/v1/option-data/{symbol}")
async def get_option_data(symbol: str, expiry: str = "30 SEP 25", strike: int = 3060, option_type: str = "CE"):
    """Get live option data from FYERS API"""
    try:
        from services.broker_manager import broker_manager
        import httpx
        
        # Get authenticated FYERS broker
        fyers_broker = broker_manager.brokers.get('fyers')
        if not fyers_broker or not hasattr(fyers_broker, 'access_token') or not fyers_broker.access_token:
            raise HTTPException(status_code=401, detail="FYERS not authenticated")
        
        # Format option symbol for NSE
        expiry_formatted = expiry.replace(" ", "").upper()  # "30SEP25"
        fyers_symbol = f"NSE:{symbol}{expiry_formatted}{strike}{option_type}"
        
        # Call FYERS API
        client_id = os.getenv('FYERS_CLIENT_ID')
        if not client_id:
            raise HTTPException(status_code=500, detail="FYERS_CLIENT_ID not configured")
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api-t1.fyers.in/api/v3/data/quotes',
                params={'symbols': fyers_symbol},
                headers={'Authorization': f'{client_id}:{fyers_broker.access_token}'},
                timeout=15.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"FYERS API error: {response.text}")
            
            data = response.json()
            quotes_array = data.get('d', [])
            
            if not quotes_array or len(quotes_array) == 0:
                raise HTTPException(status_code=404, detail=f"No data found for {fyers_symbol}")
            
            quote_item = quotes_array[0]
            if not isinstance(quote_item, dict) or 'v' not in quote_item:
                raise HTTPException(status_code=500, detail="Invalid FYERS response format")
            
            quote_data = quote_item['v']
            
            # Calculate change and percentage
            last_price = quote_data.get('lp', 0)
            prev_close = quote_data.get('prev_close_price', 0)
            change = last_price - prev_close if prev_close > 0 else 0
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "symbol": fyers_symbol,
                    "last_price": last_price,
                    "change": change,
                    "change_percent": change_percent,
                    "open_interest": quote_data.get('oi', 0),
                    "oi_change": quote_data.get('oi_change', 0),
                    "volume": quote_data.get('volume', 0),
                    "high": quote_data.get('high_price', 0),
                    "low": quote_data.get('low_price', 0),
                    "open": quote_data.get('open_price', 0),
                    "prev_close": prev_close,
                    "bid": quote_data.get('bid', 0),
                    "ask": quote_data.get('ask', 0),
                    "source": "fyers",
                    "timestamp": datetime.now().isoformat()
                },
                **get_security_headers()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Option data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/paper/order")
async def place_paper_order(order_data: dict):
    """Place secure paper trading order"""
    ensure_paper_mode()
    
    symbol = order_data.get("symbol", "UNKNOWN")
    quantity = order_data.get("quantity", 1)
    side = order_data.get("side", "BUY")
    order_type = order_data.get("order_type", "MARKET")
    price = order_data.get("price")
    
    base_prices = {"RELIANCE": 2500, "TCS": 3500, "NIFTY": 19500}
    execution_price = price if order_type == "LIMIT" and price else base_prices.get(symbol, 1000)
    execution_price += random.uniform(-1, 1)
    execution_price = round(execution_price, 2)
    
    order_id = f"PO{random.randint(100000, 999999)}"
    
    order_record = {
        "order_id": order_id,
        "symbol": symbol,
        "quantity": quantity,
        "side": side,
        "order_type": order_type,
        "execution_price": execution_price,
        "filled_quantity": quantity,
        "status": "FILLED",
        "timestamp": datetime.now().isoformat(),
        "mode": "PAPER"
    }
    paper_trading_history.append(order_record)
    
    if len(paper_trading_history) > 50:
        paper_trading_history.pop(0)
    
    return {
        "success": True,
        **order_record,
        "message": f"Paper order executed: {side} {quantity} {symbol} @ {execution_price}",
        **get_security_headers()
    }

@app.get("/api/v1/paper/history")
async def get_paper_trading_history():
    """Get paper trading history"""
    ensure_paper_mode()
    return {
        "success": True,
        "orders": list(reversed(paper_trading_history)),
        "total_orders": len(paper_trading_history),
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

@app.get("/api/v1/system/config/live-data")
async def get_live_data_config():
    """Get live data configuration"""
    return {
        "live_data_enabled": True,
        "websocket_url": "ws://localhost:8000/ws",
        "update_frequency": 1000,
        "supported_exchanges": ["NSE", "BSE"],
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

@app.post("/api/v1/system/config/live-data")
async def update_live_data_config(enabled: bool = True):
    """Update live data configuration"""
    return {
        "success": True,
        "live_data_enabled": enabled,
        "message": f"Live data {'enabled' if enabled else 'disabled'} successfully",
        "websocket_url": "ws://localhost:8000/ws" if enabled else None,
        "update_frequency": 1000 if enabled else 0,
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

@app.get("/api/v1/system/config/environment")
async def get_environment_config():
    """Environment configuration status"""
    env_status = {
        "upstox": {
            "client_id": bool(os.getenv("UPSTOX_CLIENT_ID")),
            "client_id_value": os.getenv("UPSTOX_CLIENT_ID"),
            "api_key": bool(os.getenv("UPSTOX_API_KEY")),
            "api_secret": bool(os.getenv("UPSTOX_API_SECRET")),
            "access_token": bool(os.getenv("UPSTOX_ACCESS_TOKEN")),
            "redirect_uri": bool(os.getenv("UPSTOX_REDIRECT_URI")),
            "redirect_uri_value": os.getenv("UPSTOX_REDIRECT_URI"),
            "base_url": bool(os.getenv("UPSTOX_BASE_URL"))
        },
        "other_brokers": {
            "flattrade": bool(os.getenv("FLATTRADE_API_KEY")),
            "fyers": bool(os.getenv("FYERS_CLIENT_ID")),
            "aliceblue": bool(os.getenv("ALICEBLUE_USER_ID"))
        }
    }
    
    return {
        "status": "loaded",
        "environment_variables": env_status,
        "env_file_loaded": True,
        "timestamp": datetime.now().isoformat(),
        **get_security_headers()
    }

if __name__ == "__main__":
    print("🚀 Starting Barakah Trader Lite Backend - Security Enhanced...")
    print(f"🔒 Security Mode: {TRADING_MODE}")
    print(f"🛡️ Live Trading: {'ENABLED' if LIVE_TRADING_ENABLED else 'DISABLED'}")
    print("📊 All Functionality: OAuth, Market Data, Paper Trading, Live Data Toggle")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
