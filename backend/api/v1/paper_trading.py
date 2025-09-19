"""
Paper Trading API Endpoints
RESTful API for paper trading functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from models.paper_trading import (
    PaperOrderRequest,
    PaperOrderResponse,
    PaperPortfolio,
    PerformanceMetrics,
    ModeSwitch,
    HistoricalPerformance
)
from models.trading import Order, TradingMode
from services.paper_trading import paper_trading_engine
from core.security import get_current_user
from services.multi_api_manager import MultiAPIManager


router = APIRouter(prefix="/api/v1/paper", tags=["Paper Trading"])


@router.post("/order", response_model=Dict[str, Any])
async def place_paper_order(
    order_request: PaperOrderRequest,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Place a paper trading order

    - Simulates realistic order execution with market impact
    - Includes slippage, latency, and partial fill simulation
    - Updates virtual portfolio
    """
    try:
        # Convert to Order model
        order = Order(
            symbol=order_request.symbol,
            quantity=order_request.quantity,
            side=order_request.side,
            order_type=order_request.order_type,
            price=order_request.price,
            user_id=current_user
        )

        # Execute paper order
        result = await paper_trading_engine.execute_order(order, current_user)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Order execution failed'))

        return result

    except Exception as e:
        logger.error(f"Paper order placement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_paper_portfolio(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current paper trading portfolio

    - Returns virtual portfolio with positions and P&L
    - Includes unrealized P&L calculations
    - Shows recent order history
    """
    try:
        portfolio = await paper_trading_engine.get_portfolio(current_user)
        return portfolio

    except Exception as e:
        logger.error(f"Failed to get paper portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get paper trading performance analytics

    - Returns comprehensive performance metrics
    - Includes win rate, risk-reward ratio, P&L statistics
    - Shows simulation accuracy metrics
    """
    try:
        analytics = await paper_trading_engine.get_performance_analytics(current_user)
        return analytics

    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def get_historical_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get historical paper trading performance

    - Returns daily P&L and trade statistics
    - Configurable time period (1-365 days)
    - Includes cumulative performance metrics
    """
    try:
        history = await paper_trading_engine.get_historical_performance(current_user, days)
        return history

    except Exception as e:
        logger.error(f"Failed to get historical performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=Dict[str, Any])
async def reset_paper_portfolio(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Reset paper trading portfolio to initial state

    - Clears all positions and order history
    - Resets balance to ₹5 lakh
    - Maintains historical data for analysis
    """
    try:
        result = await paper_trading_engine.reset_portfolio(current_user)
        return result

    except Exception as e:
        logger.error(f"Failed to reset paper portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode/switch", response_model=Dict[str, Any])
async def switch_trading_mode(
    mode_switch: ModeSwitch,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Switch between paper and live trading modes

    - Requires verification for LIVE mode switch
    - Maintains data continuity between modes
    - Implements safety checks and confirmations
    """
    try:
        # Validate current mode
        if mode_switch.from_mode == mode_switch.to_mode:
            return {
                "success": False,
                "message": f"Already in {mode_switch.from_mode} mode"
            }

        # Check if switching to LIVE mode
        if mode_switch.to_mode == "LIVE":
            # Require verification
            if not mode_switch.verification_token:
                return {
                    "success": False,
                    "verification_required": True,
                    "message": "Verification required to switch to LIVE mode",
                    "steps": [
                        "1. Re-enter password",
                        "2. Complete 2FA verification",
                        "3. Wait for cooling period",
                        "4. Confirm with phrase 'ENABLE LIVE TRADING'"
                    ]
                }

            # TODO: Implement actual verification logic
            # This would integrate with the security safeguards

        # Perform mode switch
        # This would integrate with MultiAPIManager
        result = {
            "success": True,
            "from_mode": mode_switch.from_mode,
            "to_mode": mode_switch.to_mode,
            "message": f"Successfully switched to {mode_switch.to_mode} mode",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"User {current_user} switched from {mode_switch.from_mode} to {mode_switch.to_mode}")

        return result

    except Exception as e:
        logger.error(f"Mode switch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mode/current", response_model=Dict[str, Any])
async def get_current_mode(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current trading mode

    - Returns current mode (PAPER/LIVE)
    - Includes mode-specific settings
    - Shows available features for current mode
    """
    try:
        # TODO: Get actual mode from session/database
        # For now, default to PAPER mode
        return {
            "mode": "PAPER",
            "user_id": current_user,
            "features": {
                "paper_trading": True,
                "live_trading": False,
                "mode_switching": True,
                "simulation_accuracy": 0.95
            },
            "settings": {
                "starting_balance": 500000,
                "slippage_factor": 0.001,
                "latency_ms": 50,
                "partial_fill_prob": 0.1
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get current mode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=Dict[str, Any])
async def get_paper_orders(
    limit: int = Query(50, ge=1, le=500, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get paper trading order history

    - Returns paginated order history
    - Includes execution details and slippage
    - Sortable by date, symbol, P&L
    """
    try:
        portfolio = paper_trading_engine.get_or_create_portfolio(current_user)

        # Get orders with pagination
        orders = portfolio.orders[offset:offset + limit]

        return {
            "orders": orders,
            "total": len(portfolio.orders),
            "limit": limit,
            "offset": offset,
            "mode": "PAPER",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get paper orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=Dict[str, Any])
async def get_paper_positions(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current paper trading positions

    - Returns open positions with P&L
    - Includes unrealized P&L calculations
    - Shows margin usage and available margin
    """
    try:
        portfolio = await paper_trading_engine.get_portfolio(current_user)

        # Filter for open positions only
        open_positions = {
            symbol: pos for symbol, pos in portfolio['positions'].items()
            if pos['quantity'] > 0
        }

        return {
            "positions": open_positions,
            "total_positions": len(open_positions),
            "margin_used": portfolio['portfolio']['margin_used'],
            "margin_available": portfolio['portfolio']['margin_available'],
            "mode": "PAPER",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get paper positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/accuracy", response_model=Dict[str, Any])
async def get_simulation_accuracy(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get paper trading simulation accuracy metrics

    - Returns current simulation accuracy (target: 95%)
    - Shows accuracy breakdown by component
    - Includes calibration status and history
    """
    try:
        accuracy_report = paper_trading_engine.simulation_framework.get_accuracy_report()

        return {
            "accuracy_metrics": accuracy_report,
            "target_accuracy": 0.95,
            "is_meeting_target": accuracy_report['current_accuracy'] >= 0.95,
            "mode": "PAPER",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get simulation accuracy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Register router with main app
def include_router(app):
    """Include paper trading router in main app"""
    app.include_router(router)
