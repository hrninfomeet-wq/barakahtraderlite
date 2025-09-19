"""
Monte Carlo Simulation and Walk-Forward Optimization
Implements strategy robustness testing and parameter optimization
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.backtest_engine import BacktestEngine, BacktestResult
from models.strategy import OptionsStrategy


class MonteCarloResult:
    """Monte Carlo simulation result"""
    def __init__(self):
        self.simulations: int = 0
        self.mean_return: float = 0.0
        self.std_return: float = 0.0
        self.var_95: float = 0.0  # Value at Risk 95%
        self.var_99: float = 0.0  # Value at Risk 99%
        self.max_drawdown_mean: float = 0.0
        self.max_drawdown_worst: float = 0.0
        self.win_rate_mean: float = 0.0
        self.profit_factor_mean: float = 0.0
        self.confidence_level: float = 0.0
        self.paths: List[List[float]] = []


class MonteCarloSimulator:
    """Monte Carlo simulation for strategy robustness testing"""

    def __init__(self):
        """Initialize Monte Carlo simulator"""
        self.backtest_engine = BacktestEngine()
        self.executor = ThreadPoolExecutor(max_workers=4)  # For parallel simulations
        logger.info("Monte Carlo Simulator initialized")

    async def run_simulation(
        self,
        strategy: OptionsStrategy,
        historical_data: pd.DataFrame,
        num_simulations: int = 1000,
        confidence_level: float = 0.95
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for strategy robustness (AC2.3.3)

        Args:
            strategy: Strategy to test
            historical_data: Historical market data
            num_simulations: Number of simulation runs
            confidence_level: Confidence level for statistics

        Returns:
            MonteCarloResult with simulation statistics
        """
        try:
            logger.info(f"Starting Monte Carlo simulation with {num_simulations} iterations")

            # Store results from each simulation
            returns = []
            max_drawdowns = []
            win_rates = []
            profit_factors = []
            equity_paths = []

            # Run simulations with data resampling
            for i in range(num_simulations):
                # Resample data with replacement (bootstrap)
                resampled_data = self._resample_data(historical_data)

                # Add random noise to simulate market variations
                noisy_data = self._add_market_noise(resampled_data)

                # Run backtest on modified data
                result = await self.backtest_engine.run_backtest(
                    strategy,
                    noisy_data,
                    initial_capital=100000.0
                )

                # Collect metrics
                returns.append(result.total_pnl / 100000.0 * 100)  # Return percentage
                max_drawdowns.append(result.max_drawdown)
                win_rates.append(result.win_rate)
                profit_factors.append(result.profit_factor)

                # Store equity curve for path analysis
                if hasattr(result, 'equity_curve') and result.equity_curve:
                    equity_paths.append(result.equity_curve)

                # Log progress every 100 simulations
                if (i + 1) % 100 == 0:
                    logger.info(f"Completed {i + 1}/{num_simulations} simulations")

            # Calculate statistics
            mc_result = MonteCarloResult()
            mc_result.simulations = num_simulations

            # Return statistics
            mc_result.mean_return = np.mean(returns)
            mc_result.std_return = np.std(returns)

            # Value at Risk calculations
            mc_result.var_95 = np.percentile(returns, 5)  # 95% VaR
            mc_result.var_99 = np.percentile(returns, 1)  # 99% VaR

            # Drawdown statistics
            mc_result.max_drawdown_mean = np.mean(max_drawdowns)
            mc_result.max_drawdown_worst = np.max(max_drawdowns)

            # Performance statistics
            mc_result.win_rate_mean = np.mean(win_rates)
            mc_result.profit_factor_mean = np.mean(profit_factors)

            # Calculate confidence in strategy
            profitable_runs = sum(1 for r in returns if r > 0)
            mc_result.confidence_level = profitable_runs / num_simulations * 100

            # Store sample paths for visualization
            mc_result.paths = equity_paths[:10]  # Keep first 10 paths

            logger.info(f"Monte Carlo complete. Mean return: {mc_result.mean_return:.2f}%, "
                       f"Confidence: {mc_result.confidence_level:.1f}%")

            return mc_result

        except Exception as e:
            logger.error(f"Monte Carlo simulation failed: {str(e)}")
            raise

    def _resample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample data with replacement (bootstrap)"""
        # Random sampling with replacement
        sample_size = len(df)
        indices = np.random.choice(df.index, size=sample_size, replace=True)
        resampled = df.loc[indices].reset_index(drop=True)

        # Sort by date if index is datetime
        if pd.api.types.is_datetime64_any_dtype(df.index):
            resampled = resampled.sort_index()

        return resampled

    def _add_market_noise(self, df: pd.DataFrame, noise_level: float = 0.01) -> pd.DataFrame:
        """Add random noise to simulate market variations"""
        noisy_df = df.copy()

        # Add noise to OHLC data
        for col in ['open', 'high', 'low', 'close']:
            if col in noisy_df.columns:
                noise = np.random.normal(0, noise_level, len(noisy_df))
                noisy_df[col] = noisy_df[col] * (1 + noise)

        # Ensure data consistency (high >= low, etc.)
        noisy_df['high'] = noisy_df[['open', 'high', 'close']].max(axis=1)
        noisy_df['low'] = noisy_df[['open', 'low', 'close']].min(axis=1)

        return noisy_df


class WalkForwardOptimizer:
    """Walk-forward optimization for strategy parameter refinement"""

    def __init__(self):
        """Initialize walk-forward optimizer"""
        self.backtest_engine = BacktestEngine()
        logger.info("Walk-Forward Optimizer initialized")

    async def optimize(
        self,
        strategy: OptionsStrategy,
        historical_data: pd.DataFrame,
        parameter_ranges: Dict[str, List[Any]],
        in_sample_ratio: float = 0.7,
        num_windows: int = 5
    ) -> Dict[str, Any]:
        """
        Perform walk-forward optimization (AC2.3.5)

        Args:
            strategy: Base strategy to optimize
            historical_data: Historical data
            parameter_ranges: Parameters to optimize with their ranges
            in_sample_ratio: Ratio of data for in-sample optimization
            num_windows: Number of walk-forward windows

        Returns:
            Optimal parameters and performance metrics
        """
        try:
            logger.info(f"Starting walk-forward optimization with {num_windows} windows")

            # Calculate window sizes
            total_days = len(historical_data)
            window_size = total_days // num_windows
            in_sample_size = int(window_size * in_sample_ratio)
            out_sample_size = window_size - in_sample_size

            # Store results from each window
            window_results = []
            optimal_params_history = []

            for window in range(num_windows):
                # Define window boundaries
                start_idx = window * out_sample_size
                in_sample_end = start_idx + in_sample_size
                out_sample_end = min(in_sample_end + out_sample_size, total_days)

                # Split data
                in_sample_data = historical_data.iloc[start_idx:in_sample_end]
                out_sample_data = historical_data.iloc[in_sample_end:out_sample_end]

                logger.info(f"Window {window + 1}: Optimizing on {len(in_sample_data)} bars, "
                           f"testing on {len(out_sample_data)} bars")

                # Find optimal parameters on in-sample data
                optimal_params = await self._optimize_parameters(
                    strategy,
                    in_sample_data,
                    parameter_ranges
                )

                optimal_params_history.append(optimal_params)

                # Test optimal parameters on out-of-sample data
                optimized_strategy = self._apply_parameters(strategy, optimal_params)
                out_sample_result = await self.backtest_engine.run_backtest(
                    optimized_strategy,
                    out_sample_data
                )

                window_results.append({
                    'window': window + 1,
                    'params': optimal_params,
                    'in_sample_size': len(in_sample_data),
                    'out_sample_size': len(out_sample_data),
                    'out_sample_return': out_sample_result.total_pnl,
                    'out_sample_sharpe': out_sample_result.sharpe_ratio,
                    'out_sample_drawdown': out_sample_result.max_drawdown
                })

            # Analyze results across all windows
            optimization_result = self._analyze_walk_forward_results(
                window_results,
                optimal_params_history
            )

            logger.info(f"Walk-forward optimization complete. "
                       f"Average out-sample return: {optimization_result['avg_return']:.2f}")

            return optimization_result

        except Exception as e:
            logger.error(f"Walk-forward optimization failed: {str(e)}")
            raise

    async def _optimize_parameters(
        self,
        strategy: OptionsStrategy,
        data: pd.DataFrame,
        parameter_ranges: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Find optimal parameters using grid search"""
        best_params = {}
        best_sharpe = -np.inf

        # Generate parameter combinations (simplified grid search)
        param_combinations = self._generate_parameter_grid(parameter_ranges)

        for params in param_combinations:
            # Apply parameters to strategy
            test_strategy = self._apply_parameters(strategy, params)

            # Run backtest
            result = await self.backtest_engine.run_backtest(test_strategy, data)

            # Use Sharpe ratio as optimization metric
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_params = params

        return best_params

    def _generate_parameter_grid(self, ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for grid search"""
        import itertools

        keys = list(ranges.keys())
        values = list(ranges.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    def _apply_parameters(
        self,
        strategy: OptionsStrategy,
        params: Dict[str, Any]
    ) -> OptionsStrategy:
        """Apply parameters to strategy (creates modified copy)"""
        # This would modify strategy parameters
        # Implementation depends on specific strategy structure
        modified_strategy = strategy.copy()

        # Example: Apply parameters to strategy
        for key, value in params.items():
            if hasattr(modified_strategy, key):
                setattr(modified_strategy, key, value)

        return modified_strategy

    def _analyze_walk_forward_results(
        self,
        window_results: List[Dict],
        params_history: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze walk-forward optimization results"""
        # Calculate average out-of-sample performance
        avg_return = np.mean([r['out_sample_return'] for r in window_results])
        avg_sharpe = np.mean([r['out_sample_sharpe'] for r in window_results])
        avg_drawdown = np.mean([r['out_sample_drawdown'] for r in window_results])

        # Find most consistent parameters
        # (parameters that appear most frequently as optimal)
        from collections import Counter
        param_consistency = {}

        for param_name in params_history[0].keys():
            values = [p[param_name] for p in params_history]
            most_common = Counter(values).most_common(1)[0]
            param_consistency[param_name] = {
                'value': most_common[0],
                'frequency': most_common[1] / len(params_history)
            }

        return {
            'avg_return': avg_return,
            'avg_sharpe': avg_sharpe,
            'avg_drawdown': avg_drawdown,
            'window_results': window_results,
            'optimal_params': param_consistency,
            'robustness_score': min(param_consistency[p]['frequency'] for p in param_consistency)
        }


# Create singleton instances
monte_carlo_simulator = MonteCarloSimulator()
walk_forward_optimizer = WalkForwardOptimizer()



