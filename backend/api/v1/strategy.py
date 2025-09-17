"""
Strategy and Backtesting API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from models.strategy import OptionsStrategy
from services.backtest_engine import backtest_engine
from services.monte_carlo_simulator import monte_carlo_simulator, walk_forward_optimizer
from services.paper_trading_deployer import paper_trading_deployer
from services.strategy_validator import strategy_validator
from core.security import get_current_user

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


@router.post("/validate")
async def validate_strategy(
    strategy: OptionsStrategy,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate strategy configuration"""
    try:
        result = await strategy_validator.validate_strategy(strategy)
        return {
            "is_valid": result.is_valid,
            "errors": result.errors if hasattr(result, 'errors') else [],
            "warnings": result.warnings if hasattr(result, 'warnings') else []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backtest/run")
async def run_backtest(
    strategy: OptionsStrategy,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Run backtest on strategy"""
    try:
        # Get historical data (placeholder - would fetch from data pipeline)
        historical_data = pd.DataFrame()  # This would be fetched from Story 1.3 pipeline
        
        # Run backtest
        result = await backtest_engine.run_backtest(
            strategy,
            historical_data,
            initial_capital
        )
        
        return {
            "strategy_id": result.strategy_id,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "total_pnl": result.total_pnl,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/monte-carlo")
async def run_monte_carlo(
    strategy: OptionsStrategy,
    num_simulations: int = 1000,
    background_tasks: BackgroundTasks = None,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Run Monte Carlo simulation"""
    try:
        # Get historical data
        historical_data = pd.DataFrame()  # Placeholder
        
        # Run simulation (could be background task for large simulations)
        result = await monte_carlo_simulator.run_simulation(
            strategy,
            historical_data,
            num_simulations
        )
        
        return {
            "simulations": result.simulations,
            "mean_return": result.mean_return,
            "std_return": result.std_return,
            "var_95": result.var_95,
            "var_99": result.var_99,
            "max_drawdown_mean": result.max_drawdown_mean,
            "max_drawdown_worst": result.max_drawdown_worst,
            "win_rate_mean": result.win_rate_mean,
            "profit_factor_mean": result.profit_factor_mean,
            "confidence_level": result.confidence_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/optimize")
async def optimize_strategy(
    strategy: OptionsStrategy,
    parameter_ranges: Dict[str, List[Any]],
    num_windows: int = 5,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Run walk-forward optimization"""
    try:
        # Get historical data
        historical_data = pd.DataFrame()  # Placeholder
        
        # Run optimization
        result = await walk_forward_optimizer.optimize(
            strategy,
            historical_data,
            parameter_ranges,
            num_windows=num_windows
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/paper")
async def deploy_to_paper_trading(
    strategy: OptionsStrategy,
    backtest_id: str,
    min_confidence: float = 0.8,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Deploy strategy to paper trading"""
    try:
        # Get backtest result (would fetch from database)
        # For now, creating a mock result
        from services.backtest_engine import BacktestResult
        backtest_result = BacktestResult()
        backtest_result.sharpe_ratio = 1.5
        backtest_result.win_rate = 60
        backtest_result.profit_factor = 1.8
        backtest_result.max_drawdown = 15
        backtest_result.total_trades = 50
        
        # Deploy strategy
        result = await paper_trading_deployer.deploy_strategy(
            strategy,
            backtest_result,
            min_confidence
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployed/{deployment_id}/performance")
async def get_deployed_strategy_performance(
    deployment_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get performance of deployed strategy"""
    try:
        result = await paper_trading_deployer.get_strategy_performance(deployment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/deployed/{deployment_id}")
async def stop_deployed_strategy(
    deployment_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop a deployed strategy"""
    try:
        result = await paper_trading_deployer.stop_strategy(deployment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recommendations")
async def get_strategy_recommendations(
    market_conditions: Optional[Dict[str, Any]] = None,
    current_user: str = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get strategy recommendations based on market conditions"""
    try:
        # This would analyze current market conditions and recommend strategies
        recommendations = []
        
        # Placeholder logic
        if market_conditions:
            volatility = market_conditions.get('volatility', 'medium')
            trend = market_conditions.get('trend', 'neutral')
            
            if volatility == 'high':
                recommendations.append({
                    'strategy': 'Iron Condor',
                    'reason': 'High volatility favors premium selling strategies',
                    'confidence': 0.8
                })
            elif trend == 'bullish':
                recommendations.append({
                    'strategy': 'Bull Call Spread',
                    'reason': 'Bullish trend with defined risk',
                    'confidence': 0.75
                })
                
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
