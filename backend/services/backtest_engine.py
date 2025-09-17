"""
Backtesting Engine Service
Implements comprehensive strategy backtesting with Backtrader
"""
import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger
import asyncio

from models.strategy import (
    OptionsStrategy, StrategyLeg, RiskParameters,
    StrategyValidationResult, StrategyType
)
from models.trading import OrderType, OrderStatus, TradingMode


class BacktestResult:
    """Backtest execution result"""
    def __init__(self):
        self.strategy_id: str = ""
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        self.total_pnl: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
        self.equity_curve: List[float] = []
        self.trades: List[Dict] = []
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.initial_capital: float = 100000.0
        self.final_capital: float = 100000.0
        

class BacktraderStrategy(bt.Strategy):
    """Base Backtrader strategy wrapper"""
    
    def __init__(self):
        self.trades = []
        self.order = None
        
    def next(self):
        """Execute strategy logic on each bar"""
        if not self.position:
            # Example entry logic - customize per strategy
            if self.data.close[0] > self.data.close[-1]:
                self.order = self.buy()
        else:
            # Example exit logic
            if len(self) >= self.position.size + 5:
                self.order = self.sell()
                
    def notify_order(self, order):
        """Track order execution"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                
            self.trades.append({
                'date': self.data.datetime.date(0),
                'price': order.executed.price,
                'size': order.executed.size,
                'type': 'BUY' if order.isbuy() else 'SELL',
                'pnl': order.executed.pnl if hasattr(order.executed, 'pnl') else 0
            })
            
    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.data.datetime.date(0)
        logger.debug(f'{dt.isoformat()} {txt}')


class BacktestEngine:
    """Main backtesting engine with Backtrader integration"""
    
    def __init__(self):
        """Initialize backtesting engine"""
        self.cerebro = None
        self.results = []
        self.data_validator = DataValidator()
        logger.info("Backtest Engine initialized")
        
    async def run_backtest(
        self, 
        strategy: OptionsStrategy,
        historical_data: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001
    ) -> BacktestResult:
        """
        Run backtest on strategy with historical data
        
        Args:
            strategy: Strategy configuration
            historical_data: DataFrame with OHLCV data
            initial_capital: Starting capital
            commission: Commission rate
            
        Returns:
            BacktestResult with metrics
        """
        try:
            # Validate data
            if not await self.data_validator.validate_historical_data(historical_data):
                raise ValueError("Invalid historical data")
                
            # Initialize Cerebro engine
            self.cerebro = bt.Cerebro()
            
            # Set initial capital
            self.cerebro.broker.setcash(initial_capital)
            self.cerebro.broker.setcommission(commission=commission)
            
            # Add data feed
            data_feed = self._prepare_data_feed(historical_data)
            self.cerebro.adddata(data_feed)
            
            # Add strategy
            self.cerebro.addstrategy(BacktraderStrategy)
            
            # Add analyzers
            self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            # Run backtest
            logger.info(f"Starting backtest for strategy: {strategy.name}")
            results = self.cerebro.run()
            
            # Process results
            backtest_result = await self._process_results(
                results[0], 
                strategy,
                initial_capital
            )
            
            logger.info(f"Backtest complete. PnL: {backtest_result.total_pnl:.2f}")
            return backtest_result
            
        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}")
            raise
            
    def _prepare_data_feed(self, df: pd.DataFrame) -> bt.feeds.PandasData:
        """Convert DataFrame to Backtrader data feed"""
        # Ensure required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        # Convert to Backtrader format
        data_feed = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # Use index as datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
        
        return data_feed
        
    async def _process_results(
        self, 
        strategy_result,
        strategy: OptionsStrategy,
        initial_capital: float
    ) -> BacktestResult:
        """Process backtest results into structured format"""
        result = BacktestResult()
        result.strategy_id = strategy.name
        result.initial_capital = initial_capital
        
        # Get analyzers
        sharpe = strategy_result.analyzers.sharpe.get_analysis()
        drawdown = strategy_result.analyzers.drawdown.get_analysis()
        trades = strategy_result.analyzers.trades.get_analysis()
        
        # Calculate metrics
        result.sharpe_ratio = sharpe.get('sharperatio', 0) or 0
        result.max_drawdown = drawdown.get('max', {}).get('drawdown', 0) or 0
        
        # Trade statistics
        total_trades = trades.get('total', {})
        result.total_trades = total_trades.get('total', 0)
        
        won_trades = trades.get('won', {})
        result.winning_trades = won_trades.get('total', 0)
        
        lost_trades = trades.get('lost', {})
        result.losing_trades = lost_trades.get('total', 0)
        
        # Calculate win rate
        if result.total_trades > 0:
            result.win_rate = (result.winning_trades / result.total_trades) * 100
        
        # Calculate profit factor
        gross_profit = won_trades.get('pnl', {}).get('total', 0) or 0
        gross_loss = abs(lost_trades.get('pnl', {}).get('total', 0) or 0)
        
        if gross_loss > 0:
            result.profit_factor = gross_profit / gross_loss
        else:
            result.profit_factor = gross_profit if gross_profit > 0 else 0
            
        # Final capital and PnL
        result.final_capital = self.cerebro.broker.getvalue()
        result.total_pnl = result.final_capital - initial_capital
        
        # Get trade list
        if hasattr(strategy_result, 'trades'):
            result.trades = strategy_result.trades
            
        return result


class DataValidator:
    """Validates historical data for backtesting"""
    
    async def validate_historical_data(self, df: pd.DataFrame) -> bool:
        """
        Validate historical data integrity
        
        Args:
            df: Historical data DataFrame
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if DataFrame is empty
            if df.empty:
                logger.error("Historical data is empty")
                return False
                
            # Check required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing columns: {missing_cols}")
                return False
                
            # Check for NaN values
            if df[required_cols].isnull().any().any():
                logger.warning("Data contains NaN values, will forward-fill")
                df[required_cols] = df[required_cols].ffill()
                
            # Check data consistency (high >= low, etc.)
            invalid_rows = df[(df['high'] < df['low']) | 
                              (df['high'] < df['open']) | 
                              (df['high'] < df['close']) |
                              (df['low'] > df['open']) |
                              (df['low'] > df['close'])]
                              
            if not invalid_rows.empty:
                logger.warning(f"Found {len(invalid_rows)} rows with invalid OHLC relationships")
                # Could fix or reject based on requirements
                
            # Check date range (5+ years for AC2.3.1)
            if hasattr(df.index, 'date'):
                date_range = (df.index[-1] - df.index[0]).days / 365.25
                if date_range < 5:
                    logger.warning(f"Data covers only {date_range:.1f} years, less than 5 years required")
                    
            logger.info(f"Data validation passed for {len(df)} rows")
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {str(e)}")
            return False


# Create singleton instance
backtest_engine = BacktestEngine()
