"""
FastAPI Application Entry Point
Enhanced AI-Powered Personal Trading Engine Backend
"""

# ------------- ENVIRONMENT VARIABLES -------------
# Load env.local / .env prior to any other imports so that
# downstream modules (e.g., auth router) see the values.
# -------------------------------------------------
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

_ROOT_DIR = Path(__file__).resolve().parent.parent
for _candidate in ("env.local", ".env.local", ".env"):
    _env_file = _ROOT_DIR / _candidate
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file, override=False)
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from core.database import DatabaseManager, AuditLogger
from services.multi_api_manager import MultiAPIManager
from api.v1.system import router as system_router
from api.v1.market_data import router as market_data_router
from api.v1.education import router as education_router
from api.v1.paper_trading import router as paper_trading_router
from api.v1.auth import router as auth_router
from api.v1.strategy import router as strategy_router


# Global variables for dependency injection
db_manager = None
audit_logger = None
api_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager, audit_logger, api_manager

    # Startup
    logger.info("Starting Enhanced AI-Powered Personal Trading Engine Backend")

    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize()
        logger.info("Database initialized successfully")

        # Initialize audit logger
        audit_logger = AuditLogger(db_manager)
        logger.info("Audit logger initialized successfully")

        # Initialize API manager
        config = {
            "enabled_apis": ["flattrade", "fyers", "upstox", "alice_blue"],
            "routing_rules": {
                "place_order": ["fyers", "upstox", "flattrade", "alice_blue"],
                "get_portfolio": ["fyers", "upstox", "flattrade", "alice_blue"],
                "get_market_data": ["upstox", "fyers", "flattrade", "alice_blue"]
            },
            "fallback_chain": ["fyers", "upstox", "flattrade", "alice_blue"],
            "flattrade": {
                "rate_limits": {"requests_per_second": 40},
                "timeout": 30
            },
            "fyers": {
                "rate_limits": {"requests_per_second": 10},
                "timeout": 30
            },
            "upstox": {
                "rate_limits": {"requests_per_second": 50},
                "timeout": 30
            },
            "alice_blue": {
                "rate_limits": {"requests_per_second": 20},
                "timeout": 30
            }
        }

        api_manager = MultiAPIManager(config, audit_logger)
        await api_manager.initialize_apis()
        logger.info("Multi-API manager initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Enhanced AI-Powered Personal Trading Engine Backend")

    try:
        if api_manager:
            await api_manager.shutdown()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Enhanced AI-Powered Personal Trading Engine",
    description="Multi-API trading system with intelligent routing and health monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system_router, prefix="/api/v1")
app.include_router(market_data_router, prefix="/api/v1")
app.include_router(education_router, prefix="/api/v1")
app.include_router(paper_trading_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(strategy_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enhanced AI-Powered Personal Trading Engine Backend",
        "version": "1.0.0",
        "status": "running",
        "timestamp": "2024-01-XX"  # Would be dynamic in production
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-XX",  # Would be dynamic in production
        "services": {
            "database": "healthy" if db_manager else "unhealthy",
            "api_manager": "healthy" if api_manager else "unhealthy",
            "audit_logger": "healthy" if audit_logger else "unhealthy"
        }
    }


if __name__ == "__main__":
    # Configure logging
    logger.add("logs/trading_engine.log", rotation="1 day", retention="7 days")

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

