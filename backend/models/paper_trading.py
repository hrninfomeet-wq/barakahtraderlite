"""
Paper Trading Models
Data models for paper trading functionality
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
# from decimal import Decimal  # Unused
from pydantic import BaseModel, Field, ConfigDict
# from enum import Enum  # Unused

from models.trading import OrderType


class PaperOrderRequest(BaseModel):
    """Request model for paper trading orders"""
    model_config = ConfigDict(
        from_attributes=True,  # Replaces orm_mode
        json_schema_extra = {
            'examples': [{'symbol': 'NIFTY', 'quantity': 50, 'order_type': 'buy', 'price': '18000.00'}]
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., gt=0, description="Order quantity")
    side: str = Field(..., pattern="^(BUY|SELL)$", description="Order side")
    order_type: OrderType = Field(OrderType.MARKET, description="Order type")
    price: Optional[float] = Field(None, description="Limit price for LIMIT orders")
    stop_price: Optional[float] = Field(None, description="Stop price for STOP orders")


class PaperOrderResponse(BaseModel):
    """Response model for paper trading orders"""
    model_config = ConfigDict(from_attributes=True)

    order_id: str = Field(..., description="Paper order ID")
    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., description="Requested quantity")
    executed_quantity: int = Field(..., description="Executed quantity")
    side: str = Field(..., description="Order side")
    status: str = Field(..., description="Order status")
    requested_price: Optional[float] = Field(None, description="Requested price")
    executed_price: float = Field(..., description="Execution price")
    slippage: float = Field(..., description="Slippage amount")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    timestamp: str = Field(..., description="Order timestamp")
    is_paper_trade: bool = Field(True, description="Paper trade indicator")
    mode: str = Field("PAPER", description="Trading mode")


class VirtualPosition(BaseModel):
    """Virtual position in paper trading"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., description="Position quantity")
    avg_price: float = Field(..., description="Average entry price")
    current_price: Optional[float] = Field(None, description="Current market price")
    realized_pnl: float = Field(0.0, description="Realized P&L")
    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")
    margin_used: float = Field(0.0, description="Margin used")

    @property
    def total_pnl(self) -> float:
        """Calculate total P&L"""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def position_value(self) -> float:
        """Calculate position value"""
        return self.quantity * self.avg_price


class PaperPortfolio(BaseModel):
    """Paper trading portfolio model"""
    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="User ID")
    mode: str = Field("PAPER", description="Trading mode")
    cash_balance: float = Field(500000.0, description="Cash balance")
    positions: List[VirtualPosition] = Field(default_factory=list, description="Open positions")
    total_pnl: float = Field(0.0, description="Total P&L")
    margin_used: float = Field(0.0, description="Total margin used")
    margin_available: float = Field(500000.0, description="Available margin")
    portfolio_value: float = Field(500000.0, description="Total portfolio value")

    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(pos.position_value for pos in self.positions)
        return self.cash_balance + positions_value + self.total_pnl

    def calculate_margin(self) -> Dict[str, float]:
        """Calculate margin requirements"""
        total_margin = sum(pos.margin_used for pos in self.positions)
        return {
            "used": total_margin,
            "available": self.cash_balance - total_margin,
            "total": self.cash_balance
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics for paper trading"""
    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
        "example": {
            "total_trades": 50,
            "winning_trades": 30,
            "losing_trades": 20,
            "win_rate": 60.0,
            "total_pnl": 25000.0,
            "average_profit": 1500.0,
            "average_loss": 750.0,
            "risk_reward_ratio": 2.0,
            "return_percentage": 5.0
        }
    })

    total_trades: int = Field(0, description="Total number of trades")
    winning_trades: int = Field(0, description="Number of winning trades")
    losing_trades: int = Field(0, description="Number of losing trades")
    win_rate: float = Field(0.0, description="Win rate percentage")
    total_pnl: float = Field(0.0, description="Total P&L")
    average_profit: float = Field(0.0, description="Average profit per winning trade")
    average_loss: float = Field(0.0, description="Average loss per losing trade")
    risk_reward_ratio: float = Field(0.0, description="Risk-reward ratio")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    return_percentage: float = Field(0.0, description="Return percentage")


class SimulationAccuracy(BaseModel):
    """Simulation accuracy metrics"""
    model_config = ConfigDict(from_attributes=True)

    current_accuracy: float = Field(..., description="Current simulation accuracy")
    target_accuracy: float = Field(0.95, description="Target accuracy")
    samples_analyzed: int = Field(..., description="Number of samples analyzed")
    slippage_accuracy: float = Field(..., description="Slippage simulation accuracy")
    latency_accuracy: float = Field(..., description="Latency simulation accuracy")
    fill_rate_accuracy: float = Field(..., description="Fill rate accuracy")
    last_calibration: str = Field(..., description="Last calibration timestamp")

    @property
    def is_meeting_target(self) -> bool:
        """Check if accuracy meets target"""
        return self.current_accuracy >= self.target_accuracy


class PaperTradingSession(BaseModel):
    """Paper trading session information"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    initial_balance: float = Field(500000.0, description="Initial balance")
    final_balance: Optional[float] = Field(None, description="Final balance")
    total_orders: int = Field(0, description="Total orders placed")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")

    @property
    def session_duration(self) -> Optional[float]:
        """Calculate session duration in hours"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return None

    @property
    def session_return(self) -> Optional[float]:
        """Calculate session return percentage"""
        if self.final_balance:
            return ((self.final_balance - self.initial_balance) / self.initial_balance) * 100
        return None


class ModeSwitch(BaseModel):
    """Mode switch request/response model"""
    model_config = ConfigDict(from_attributes=True, json_schema_extra = {
        "example": {
            "from_mode": "PAPER",
            "to_mode": "LIVE",
            "user_id": "user123",
            "verification_required": True,
            "message": "Verification required for mode switch"
        }
    })

    from_mode: str = Field(..., pattern="^(PAPER|LIVE)$", description="Current mode")
    to_mode: str = Field(..., pattern="^(PAPER|LIVE)$", description="Target mode")
    user_id: str = Field(..., description="User ID")
    verification_required: bool = Field(True, description="Verification required flag")
    verification_token: Optional[str] = Field(None, description="Verification token")
    switch_time: Optional[datetime] = Field(None, description="Switch timestamp")
    success: bool = Field(False, description="Switch success status")
    message: str = Field(..., description="Status message")


class HistoricalPerformance(BaseModel):
    """Historical performance data"""
    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="User ID")
    mode: str = Field("PAPER", description="Trading mode")
    period_days: int = Field(..., description="Period in days")
    daily_performance: List[Dict[str, Any]] = Field(..., description="Daily performance data")
    cumulative_pnl: List[float] = Field(..., description="Cumulative P&L series")
    peak_value: float = Field(..., description="Peak portfolio value")
    trough_value: float = Field(..., description="Trough portfolio value")
    total_return: float = Field(..., description="Total return percentage")
    volatility: float = Field(..., description="Return volatility")

    @property
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if self.peak_value > 0:
            return ((self.peak_value - self.trough_value) / self.peak_value) * 100
        return 0.0
