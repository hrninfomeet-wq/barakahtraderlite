"""
Paper Trading Engine Implementation
Provides realistic paper trading simulation with market impact modeling
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, field
from decimal import Decimal
from loguru import logger
from backend.models.trading import Order
from backend.services.simulation_accuracy_framework import (
    SimulationAccuracyFramework,
    SimulationConfig,
    MarketSimulator
)
from backend.services.market_data_service import MarketDataPipeline, MarketDataRequest, DataType
# from core.database import get_db_session  # Unused


@dataclass
class VirtualPortfolio:
    """Virtual portfolio for paper trading"""
    cash_balance: Decimal = Decimal('500000')  # ₹5 lakh starting capital
    positions: Dict[str, Dict] = field(default_factory=dict)
    orders: List[Dict] = field(default_factory=list)
    pnl_history: List[Dict] = field(default_factory=list)
    total_pnl: Decimal = Decimal('0')
    margin_used: Decimal = Decimal('0')
    margin_available: Decimal = Decimal('500000')

    def update_position(self, symbol: str, quantity: int, price: Decimal, side: str):
        """Update position after trade execution"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': Decimal('0'),
                'realized_pnl': Decimal('0'),
                'unrealized_pnl': Decimal('0')
            }

        pos = self.positions[symbol]

        if side == 'BUY':
            # Calculate new average price
            total_value = (pos['quantity'] * pos['avg_price']) + (quantity * price)
            new_quantity = pos['quantity'] + quantity
            pos['avg_price'] = total_value / new_quantity if new_quantity != 0 else Decimal('0')
            pos['quantity'] = new_quantity

            # Update cash balance
            self.cash_balance -= (quantity * price)

        else:  # SELL
            if pos['quantity'] >= quantity:
                # Calculate realized P&L
                realized_pnl = (price - pos['avg_price']) * quantity
                pos['realized_pnl'] += realized_pnl
                self.total_pnl += realized_pnl

                # Update position
                pos['quantity'] -= quantity

                # Update cash balance
                self.cash_balance += (quantity * price)

        # Update margin
        self._update_margin()

    def _update_margin(self):
        """Update margin calculations"""
        # Simplified margin calculation (20% of position value)
        total_position_value = Decimal('0')
        for symbol, pos in self.positions.items():
            if pos['quantity'] > 0:
                total_position_value += pos['quantity'] * pos['avg_price']

        self.margin_used = total_position_value * Decimal('0.2')  # 20% margin
        self.margin_available = self.cash_balance - self.margin_used

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        return {
            'cash_balance': float(self.cash_balance),
            'positions': len([p for p in self.positions.values() if p['quantity'] > 0]),
            'total_pnl': float(self.total_pnl),
            'margin_used': float(self.margin_used),
            'margin_available': float(self.margin_available),
            'portfolio_value': float(self.cash_balance + self.total_pnl)
        }


class PaperTradingEngine:
    """Main paper trading engine with realistic simulation"""

    def __init__(self):
        self.simulation_framework = SimulationAccuracyFramework()
        self.market_simulator = MarketSimulator(SimulationConfig())
        self.market_data_pipeline = MarketDataPipeline()
        self.portfolios: Dict[str, VirtualPortfolio] = {}
        self.order_history: List[Dict] = []
        self.is_initialized = False

    async def initialize(self):
        """Initialize paper trading engine"""
        if not self.is_initialized:
            await self.simulation_framework.initialize()
            await self.market_data_pipeline.initialize()
            self.is_initialized = True
            logger.info("Paper Trading Engine initialized")

    def get_or_create_portfolio(self, user_id: str) -> VirtualPortfolio:
        """Get or create virtual portfolio for user"""
        if user_id not in self.portfolios:
            self.portfolios[user_id] = VirtualPortfolio()
            logger.info(f"Created new virtual portfolio for user {user_id}")
        return self.portfolios[user_id]

    async def execute_order(self, order: Order, user_id: str) -> Dict[str, Any]:
        """Execute order in paper trading mode with realistic simulation"""
        if not self.is_initialized:
            await self.initialize()

        portfolio = self.get_or_create_portfolio(user_id)

        # Get current market data
        request = MarketDataRequest(symbols=[order.symbol], data_types=[DataType.PRICE])
        market_data_response = await self.market_data_pipeline.get_market_data(request)

        # Compatibility: allow tests to mock either a response with .data or a direct MarketData-like object
        market_data = None
        if market_data_response is None:
            market_data = None
        elif hasattr(market_data_response, 'data') and isinstance(market_data_response.data, dict):
            market_data = market_data_response.data.get(order.symbol)
        elif hasattr(market_data_response, 'last_price'):
            # Direct MarketData mock provided
            market_data = market_data_response

        if not market_data or not hasattr(market_data, 'last_price'):
            return {
                'success': False,
                'error': 'Market data not available',
                'order_id': None
            }

        # Simulate execution with realistic market impact
        execution_result = await self.simulation_framework.simulate_order_execution(
            order=order,
            current_price=market_data.last_price
        )

        # Create order response
        order_id = f"PAPER_{uuid.uuid4().hex[:8].upper()}"
        order_response = {
            'order_id': order_id,
            'symbol': order.symbol,
            'quantity': order.quantity,
            'requested_price': order.price,
            'executed_price': execution_result['execution_price'],
            'executed_quantity': execution_result['filled_quantity'],
            'status': 'COMPLETE' if execution_result['filled_quantity'] == order.quantity else 'PARTIAL',
            'slippage': execution_result['slippage'],
            'execution_time_ms': execution_result['latency_ms'],
            'timestamp': datetime.now().isoformat(),
            'is_paper_trade': True,
            'mode': 'PAPER'
        }

        # Update portfolio
        portfolio.update_position(
            symbol=order.symbol,
            quantity=execution_result['filled_quantity'],
            price=Decimal(str(execution_result['execution_price'])),
            side=order.side
        )

        # Store order in history
        self.order_history.append(order_response)
        portfolio.orders.append(order_response)

        # Log execution
        logger.info(
            f"Paper order executed: {order_id} - {order.symbol} "
            f"{order.quantity}@{execution_result['execution_price']:.2f} "
            f"(slippage: {execution_result['slippage']:.4f})"
        )

        return {
            'success': True,
            'order': order_response,
            'portfolio_summary': portfolio.get_portfolio_summary()
        }

    async def get_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get user's paper trading portfolio"""
        portfolio = self.get_or_create_portfolio(user_id)

        # Calculate unrealized P&L for open positions
        for symbol, position in portfolio.positions.items():
            if position['quantity'] > 0:
                request = MarketDataRequest(symbols=[symbol], data_types=[DataType.PRICE])
                market_data_response = await self.market_data_pipeline.get_market_data(request)

                # Compatibility handling for portfolio valuation as well
                current_md = None
                if market_data_response is None:
                    current_md = None
                elif hasattr(market_data_response, 'data') and isinstance(market_data_response.data, dict):
                    current_md = market_data_response.data.get(symbol)
                elif hasattr(market_data_response, 'last_price'):
                    current_md = market_data_response

                if current_md:
                    current_price = Decimal(str(current_md.last_price))
                    position['unrealized_pnl'] = (
                        (current_price - position['avg_price']) * position['quantity']
                    )

        return {
            'user_id': user_id,
            'mode': 'PAPER',
            'portfolio': portfolio.get_portfolio_summary(),
            'positions': portfolio.positions,
            'recent_orders': portfolio.orders[-10:] if portfolio.orders else [],
            'timestamp': datetime.now().isoformat()
        }

    async def get_performance_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get paper trading performance analytics"""
        portfolio = self.get_or_create_portfolio(user_id)

        if not portfolio.orders:
            return {
                'user_id': user_id,
                'mode': 'PAPER',
                'message': 'No trading activity yet',
                'timestamp': datetime.now().isoformat()
            }

        # Calculate performance metrics
        total_trades = len(portfolio.orders)
        winning_trades = len([o for o in portfolio.pnl_history if o.get('pnl', 0) > 0])
        losing_trades = len([o for o in portfolio.pnl_history if o.get('pnl', 0) < 0])

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate average P&L
        avg_profit = (
            sum([o['pnl'] for o in portfolio.pnl_history if o.get('pnl', 0) > 0]) / winning_trades
            if winning_trades > 0 else 0
        )
        avg_loss = (
            sum([o['pnl'] for o in portfolio.pnl_history if o.get('pnl', 0) < 0]) / losing_trades
            if losing_trades > 0 else 0
        )

        # Risk-reward ratio
        risk_reward = abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')

        # Get simulation accuracy
        accuracy_report = self.simulation_framework.get_accuracy_report()

        return {
            'user_id': user_id,
            'mode': 'PAPER',
            'performance': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': f"{win_rate:.2f}%",
                'total_pnl': float(portfolio.total_pnl),
                'average_profit': float(avg_profit),
                'average_loss': float(avg_loss),
                'risk_reward_ratio': f"{risk_reward:.2f}",
                'portfolio_value': float(portfolio.cash_balance + portfolio.total_pnl),
                'return_percentage': float(
                    (portfolio.total_pnl / Decimal('500000')) * 100
                )
            },
            'simulation_accuracy': accuracy_report,
            'timestamp': datetime.now().isoformat()
        }

    async def reset_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Reset paper trading portfolio to initial state"""
        self.portfolios[user_id] = VirtualPortfolio()

        logger.info(f"Reset paper trading portfolio for user {user_id}")

        return {
            'success': True,
            'message': 'Paper trading portfolio reset successfully',
            'portfolio': self.portfolios[user_id].get_portfolio_summary(),
            'timestamp': datetime.now().isoformat()
        }

    async def get_historical_performance(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical paper trading performance"""
        portfolio = self.get_or_create_portfolio(user_id)

        # Filter orders by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_orders = [
            o for o in portfolio.orders
            if datetime.fromisoformat(o['timestamp']) > cutoff_date
        ]

        # Group by date for daily P&L
        daily_pnl = {}
        for order in recent_orders:
            date = datetime.fromisoformat(order['timestamp']).date()
            if date not in daily_pnl:
                daily_pnl[date] = {'trades': 0, 'pnl': 0}

            daily_pnl[date]['trades'] += 1
            # Note: Actual P&L calculation would need position tracking

        return {
            'user_id': user_id,
            'mode': 'PAPER',
            'period_days': days,
            'total_orders': len(recent_orders),
            'daily_performance': [
                {
                    'date': str(date),
                    'trades': data['trades'],
                    'pnl': data['pnl']
                }
                for date, data in sorted(daily_pnl.items())
            ],
            'timestamp': datetime.now().isoformat()
        }


# Global instance
paper_trading_engine = PaperTradingEngine()

