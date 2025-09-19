"""
Paper Trading Deployment Service
Enables direct strategy deployment from backtesting to paper trading
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from models.strategy import OptionsStrategy
from models.trading import TradingMode, Order, OrderType
from services.paper_trading import PaperTradingEngine
from services.backtest_engine import BacktestResult
from services.strategy_validator import strategy_validator


class PaperTradingDeployer:
    """Deploys backtested strategies to paper trading with validation"""

    def __init__(self):
        """Initialize paper trading deployer"""
        self.paper_engine = PaperTradingEngine()
        self.active_strategies: Dict[str, OptionsStrategy] = {}
        logger.info("Paper Trading Deployer initialized")

    async def deploy_strategy(
        self,
        strategy: OptionsStrategy,
        backtest_result: BacktestResult,
        min_confidence: float = 0.8
    ) -> Dict[str, Any]:
        """
        Deploy strategy from backtest to paper trading (AC2.3.4)

        Args:
            strategy: Strategy to deploy
            backtest_result: Backtest results for validation
            min_confidence: Minimum confidence level required

        Returns:
            Deployment status and details
        """
        try:
            # Validate mode - ensure paper trading mode
            if not await self._validate_trading_mode():
                return {
                    'status': 'failed',
                    'reason': 'System not in paper trading mode'
                }

            # Validate backtest results meet criteria
            validation = await self._validate_backtest_results(
                backtest_result,
                min_confidence
            )

            if not validation['passed']:
                return {
                    'status': 'failed',
                    'reason': validation['reason'],
                    'metrics': validation['metrics']
                }

            # Validate strategy configuration
            strategy_validation = await strategy_validator.validate_strategy(strategy)

            if not strategy_validation.is_valid:
                return {
                    'status': 'failed',
                    'reason': 'Strategy validation failed',
                    'errors': strategy_validation.errors
                }

            # Deploy strategy to paper trading
            deployment_id = await self._deploy_to_paper(strategy)

            # Register active strategy
            self.active_strategies[deployment_id] = strategy

            logger.info(f"Strategy {strategy.name} deployed to paper trading. "
                       f"ID: {deployment_id}")

            return {
                'status': 'success',
                'deployment_id': deployment_id,
                'strategy_name': strategy.name,
                'mode': 'PAPER',
                'timestamp': datetime.now().isoformat(),
                'backtest_metrics': {
                    'sharpe_ratio': backtest_result.sharpe_ratio,
                    'win_rate': backtest_result.win_rate,
                    'profit_factor': backtest_result.profit_factor,
                    'max_drawdown': backtest_result.max_drawdown
                }
            }

        except Exception as e:
            logger.error(f"Strategy deployment failed: {str(e)}")
            return {
                'status': 'error',
                'reason': str(e)
            }

    async def _validate_trading_mode(self) -> bool:
        """Validate system is in paper trading mode"""
        # Check current trading mode
        # This would interface with the multi-API manager
        # For now, assuming paper mode check
        return True  # Placeholder - implement actual mode check

    async def _validate_backtest_results(
        self,
        result: BacktestResult,
        min_confidence: float
    ) -> Dict[str, Any]:
        """Validate backtest results meet deployment criteria"""
        metrics = {
            'sharpe_ratio': result.sharpe_ratio,
            'win_rate': result.win_rate,
            'profit_factor': result.profit_factor,
            'max_drawdown': result.max_drawdown,
            'total_trades': result.total_trades
        }

        # Check minimum criteria
        if result.sharpe_ratio < 0.5:
            return {
                'passed': False,
                'reason': f'Sharpe ratio too low: {result.sharpe_ratio:.2f} < 0.5',
                'metrics': metrics
            }

        if result.win_rate < 40:
            return {
                'passed': False,
                'reason': f'Win rate too low: {result.win_rate:.1f}% < 40%',
                'metrics': metrics
            }

        if result.max_drawdown > 20:
            return {
                'passed': False,
                'reason': f'Max drawdown too high: {result.max_drawdown:.1f}% > 20%',
                'metrics': metrics
            }

        if result.total_trades < 10:
            return {
                'passed': False,
                'reason': f'Insufficient trades: {result.total_trades} < 10',
                'metrics': metrics
            }

        # Calculate confidence score
        confidence_score = (
            (result.sharpe_ratio / 2.0) * 0.3 +  # Sharpe contribution
            (result.win_rate / 100.0) * 0.3 +    # Win rate contribution
            (min(result.profit_factor / 2.0, 1.0)) * 0.2 +  # Profit factor
            ((20 - result.max_drawdown) / 20.0) * 0.2  # Drawdown inverse
        )

        if confidence_score < min_confidence:
            return {
                'passed': False,
                'reason': f'Confidence score too low: {confidence_score:.2f} < {min_confidence}',
                'metrics': metrics
            }

        return {
            'passed': True,
            'confidence_score': confidence_score,
            'metrics': metrics
        }

    async def _deploy_to_paper(self, strategy: OptionsStrategy) -> str:
        """Deploy strategy to paper trading engine"""
        # Generate deployment ID
        deployment_id = f"DEPLOY_{strategy.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize paper trading for this strategy
        await self.paper_engine.initialize()

        # Register strategy with paper engine
        # This would set up the strategy for automated execution
        # For now, returning deployment ID

        return deployment_id

    async def execute_strategy_trade(
        self,
        deployment_id: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a trade based on strategy signal"""
        if deployment_id not in self.active_strategies:
            return {
                'status': 'error',
                'reason': 'Strategy not deployed'
            }

        strategy = self.active_strategies[deployment_id]

        # Create order from signal
        order = Order(
            symbol=signal['symbol'],
            quantity=signal['quantity'],
            order_type=OrderType[signal['order_type']],
            price=signal.get('price'),
            user_id=f"strategy_{deployment_id}"
        )

        # Execute via paper trading engine
        result = await self.paper_engine.execute_order(order, f"strategy_{deployment_id}")

        return {
            'status': 'executed',
            'order_id': result['order_id'],
            'deployment_id': deployment_id,
            'is_paper_trade': True
        }

    async def stop_strategy(self, deployment_id: str) -> Dict[str, Any]:
        """Stop an active strategy"""
        if deployment_id not in self.active_strategies:
            return {
                'status': 'error',
                'reason': 'Strategy not found'
            }

        # Close all positions for this strategy
        # This would interface with paper trading engine

        # Remove from active strategies
        del self.active_strategies[deployment_id]

        logger.info(f"Strategy {deployment_id} stopped")

        return {
            'status': 'stopped',
            'deployment_id': deployment_id,
            'timestamp': datetime.now().isoformat()
        }

    async def get_strategy_performance(
        self,
        deployment_id: str
    ) -> Dict[str, Any]:
        """Get performance metrics for deployed strategy"""
        if deployment_id not in self.active_strategies:
            return {
                'status': 'error',
                'reason': 'Strategy not found'
            }

        # Get performance from paper trading engine
        # This would fetch real-time metrics

        return {
            'status': 'success',
            'deployment_id': deployment_id,
            'metrics': {
                'pnl': 0.0,  # Placeholder
                'trades': 0,
                'win_rate': 0.0,
                'positions': []
            }
        }


# Create singleton instance
paper_trading_deployer = PaperTradingDeployer()



