"""
Unit tests for Paper Trading Engine
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from services.paper_trading import PaperTradingEngine, VirtualPortfolio
from models.trading import Order, OrderType, TradingMode
from models.paper_trading import PaperOrderRequest
from services.simulation_accuracy_framework import SimulationAccuracyFramework


class TestVirtualPortfolio:
    """Test virtual portfolio functionality"""
    
    def test_initial_portfolio_state(self):
        """Test initial portfolio state"""
        portfolio = VirtualPortfolio()
        
        assert portfolio.cash_balance == Decimal('500000')
        assert len(portfolio.positions) == 0
        assert portfolio.total_pnl == Decimal('0')
        assert portfolio.margin_available == Decimal('500000')
    
    def test_update_position_buy(self):
        """Test updating position after buy order"""
        portfolio = VirtualPortfolio()
        
        # Execute buy order
        portfolio.update_position(
            symbol='RELIANCE',
            quantity=10,
            price=Decimal('2500'),
            side='BUY'
        )
        
        # Check position
        assert 'RELIANCE' in portfolio.positions
        assert portfolio.positions['RELIANCE']['quantity'] == 10
        assert portfolio.positions['RELIANCE']['avg_price'] == Decimal('2500')
        
        # Check cash balance
        assert portfolio.cash_balance == Decimal('475000')  # 500000 - (10 * 2500)
    
    def test_update_position_sell(self):
        """Test updating position after sell order"""
        portfolio = VirtualPortfolio()
        
        # First buy
        portfolio.update_position('RELIANCE', 10, Decimal('2500'), 'BUY')
        
        # Then sell at profit
        portfolio.update_position('RELIANCE', 5, Decimal('2600'), 'SELL')
        
        # Check position
        assert portfolio.positions['RELIANCE']['quantity'] == 5
        assert portfolio.positions['RELIANCE']['realized_pnl'] == Decimal('500')  # (2600-2500) * 5
        
        # Check total P&L
        assert portfolio.total_pnl == Decimal('500')
    
    def test_margin_calculations(self):
        """Test margin calculations"""
        portfolio = VirtualPortfolio()
        
        # Buy position
        portfolio.update_position('NIFTY', 50, Decimal('20000'), 'BUY')
        
        # Check margin (20% of position value)
        position_value = Decimal('1000000')  # 50 * 20000
        expected_margin = position_value * Decimal('0.2')
        
        assert portfolio.margin_used == expected_margin
        assert portfolio.margin_available == portfolio.cash_balance - portfolio.margin_used


class TestPaperTradingEngine:
    """Test paper trading engine functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create paper trading engine instance"""
        return PaperTradingEngine()
    
    @pytest.fixture
    def sample_order(self):
        """Create sample order"""
        return Order(
            symbol='RELIANCE',
            quantity=10,
            side='BUY',
            order_type=OrderType.MARKET,
            user_id='test_user'
        )
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert not engine.is_initialized
        
        await engine.initialize()
        
        assert engine.is_initialized
        assert engine.simulation_framework is not None
        assert engine.market_simulator is not None
    
    @pytest.mark.asyncio
    async def test_execute_order_success(self, engine, sample_order):
        """Test successful order execution"""
        # Mock market data
        with patch.object(engine.market_data_pipeline, 'get_market_data') as mock_market_data:
            mock_market_data.return_value = Mock(last_price=2500.0)
            
            # Mock simulation
            with patch.object(engine.simulation_framework, 'simulate_order_execution') as mock_simulate:
                mock_simulate.return_value = {
                    'execution_price': 2501.0,
                    'filled_quantity': 10,
                    'slippage': 0.001,
                    'latency_ms': 50
                }
                
                result = await engine.execute_order(sample_order, 'test_user')
                
                assert result['success'] == True
                assert result['order']['order_id'].startswith('PAPER_')
                assert result['order']['executed_price'] == 2501.0
                assert result['order']['is_paper_trade'] == True
    
    @pytest.mark.asyncio
    async def test_execute_order_partial_fill(self, engine, sample_order):
        """Test partial fill order execution"""
        with patch.object(engine.market_data_pipeline, 'get_market_data') as mock_market_data:
            mock_market_data.return_value = Mock(last_price=2500.0)
            
            with patch.object(engine.simulation_framework, 'simulate_order_execution') as mock_simulate:
                mock_simulate.return_value = {
                    'execution_price': 2501.0,
                    'filled_quantity': 7,  # Partial fill
                    'slippage': 0.001,
                    'latency_ms': 50
                }
                
                result = await engine.execute_order(sample_order, 'test_user')
                
                assert result['order']['status'] == 'PARTIAL'
                assert result['order']['executed_quantity'] == 7
    
    @pytest.mark.asyncio
    async def test_get_portfolio(self, engine):
        """Test getting user portfolio"""
        user_id = 'test_user'
        
        # Get initial portfolio
        portfolio = await engine.get_portfolio(user_id)
        
        assert portfolio['user_id'] == user_id
        assert portfolio['mode'] == 'PAPER'
        assert portfolio['portfolio']['cash_balance'] == 500000.0
        assert len(portfolio['positions']) == 0
    
    @pytest.mark.asyncio
    async def test_performance_analytics(self, engine):
        """Test performance analytics calculation"""
        user_id = 'test_user'
        
        # Create some trading history
        portfolio = engine.get_or_create_portfolio(user_id)
        portfolio.pnl_history = [
            {'pnl': 1000},
            {'pnl': -500},
            {'pnl': 2000},
            {'pnl': -300}
        ]
        portfolio.orders = [Mock() for _ in range(4)]
        portfolio.total_pnl = Decimal('2200')
        
        # Get analytics
        analytics = await engine.get_performance_analytics(user_id)
        
        assert analytics['performance']['total_trades'] == 4
        assert analytics['performance']['winning_trades'] == 2
        assert analytics['performance']['losing_trades'] == 2
        assert analytics['performance']['win_rate'] == '50.00%'
    
    @pytest.mark.asyncio
    async def test_reset_portfolio(self, engine):
        """Test portfolio reset"""
        user_id = 'test_user'
        
        # Create and modify portfolio
        portfolio = engine.get_or_create_portfolio(user_id)
        portfolio.cash_balance = Decimal('450000')
        portfolio.positions['RELIANCE'] = {'quantity': 10}
        
        # Reset portfolio
        result = await engine.reset_portfolio(user_id)
        
        assert result['success'] == True
        
        # Check reset portfolio
        new_portfolio = engine.portfolios[user_id]
        assert new_portfolio.cash_balance == Decimal('500000')
        assert len(new_portfolio.positions) == 0


class TestSimulationAccuracy:
    """Test simulation accuracy framework integration"""
    
    @pytest.mark.asyncio
    async def test_simulation_accuracy_tracking(self):
        """Test that simulation accuracy is tracked"""
        engine = PaperTradingEngine()
        await engine.initialize()
        
        # Get accuracy report
        report = engine.simulation_framework.get_accuracy_report()
        
        assert 'current_accuracy' in report
        assert 'samples_analyzed' in report
        assert report['current_accuracy'] >= 0.0
        assert report['current_accuracy'] <= 1.0


class TestModeValidation:
    """Test mode validation in MultiAPIManager"""
    
    @pytest.mark.asyncio
    async def test_paper_mode_routing(self):
        """Test that paper mode routes to paper trading engine"""
        from services.multi_api_manager import MultiAPIManager
        
        manager = MultiAPIManager({})
        
        # Mock paper trading engine
        with patch('services.multi_api_manager.paper_trading_engine') as mock_engine:
            mock_engine.execute_order = AsyncMock(return_value={'success': True})
            
            # Execute in paper mode
            result = await manager.execute_with_fallback(
                'place_order',
                mode=TradingMode.PAPER,
                order=Mock(),
                user_id='test_user'
            )
            
            # Verify paper trading engine was called
            mock_engine.execute_order.assert_called_once()
    
    def test_operation_validation(self):
        """Test operation validation for different modes"""
        from services.multi_api_manager import MultiAPIManager
        
        manager = MultiAPIManager({})
        
        # Test paper mode restrictions
        assert manager._is_operation_allowed('place_order', TradingMode.PAPER) == True
        assert manager._is_operation_allowed('transfer_funds', TradingMode.PAPER) == False
        assert manager._is_operation_allowed('withdraw_funds', TradingMode.PAPER) == False
        
        # Test live mode (no restrictions for now)
        assert manager._is_operation_allowed('place_order', TradingMode.LIVE) == True
        assert manager._is_operation_allowed('transfer_funds', TradingMode.LIVE) == True
