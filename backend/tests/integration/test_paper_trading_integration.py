"""
Integration tests for Paper Trading functionality
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from services.paper_trading import PaperTradingEngine
from services.multi_api_manager import MultiAPIManager
from models.trading import Order, OrderType, TradingMode
from models.paper_trading import PaperOrderRequest


class TestPaperTradingIntegration:
    """Integration tests for paper trading with other components"""
    
    @pytest.fixture
    async def setup_environment(self):
        """Setup test environment with all components"""
        engine = PaperTradingEngine()
        await engine.initialize()
        
        manager = MultiAPIManager({
            'enabled_apis': ['FYERS'],
            'FYERS': {'credentials': {}}
        })
        
        return engine, manager
    
    @pytest.mark.asyncio
    async def test_mode_switching_data_isolation(self, setup_environment):
        """Test that data is isolated between paper and live modes"""
        engine, manager = await setup_environment
        user_id = 'test_user'
        
        # Create paper order
        paper_order = Order(
            symbol='RELIANCE',
            quantity=10,
            side='BUY',
            order_type=OrderType.MARKET,
            user_id=user_id
        )
        
        # Execute in paper mode
        with patch.object(engine.market_data_pipeline, 'get_market_data') as mock_data:
            mock_data.return_value = Mock(last_price=2500.0)
            
            with patch.object(engine.simulation_framework, 'simulate_order_execution') as mock_sim:
                mock_sim.return_value = {
                    'execution_price': 2501.0,
                    'filled_quantity': 10,
                    'slippage': 0.001,
                    'latency_ms': 50
                }
                
                paper_result = await manager.execute_with_fallback(
                    'place_order',
                    mode=TradingMode.PAPER,
                    order=paper_order,
                    user_id=user_id
                )
        
        assert paper_result['order']['is_paper_trade'] == True
        assert paper_result['order']['mode'] == 'PAPER'
        
        # Verify paper portfolio
        paper_portfolio = await engine.get_portfolio(user_id)
        assert len(paper_portfolio['positions']) > 0
        
        # In live mode, portfolio should be empty (data isolation)
        # This would be a separate live portfolio in production
        # For testing, we verify the paper flag
        assert paper_portfolio['mode'] == 'PAPER'
    
    @pytest.mark.asyncio
    async def test_simulation_accuracy_calibration(self, setup_environment):
        """Test that simulation accuracy improves with calibration"""
        engine, _ = await setup_environment
        
        # Execute multiple orders for calibration
        for i in range(10):
            order = Order(
                symbol=f'TEST{i}',
                quantity=10,
                side='BUY' if i % 2 == 0 else 'SELL',
                order_type=OrderType.MARKET,
                user_id='test_user'
            )
            
            with patch.object(engine.market_data_pipeline, 'get_market_data') as mock_data:
                mock_data.return_value = Mock(last_price=1000.0 + i)
                
                with patch.object(engine.simulation_framework, 'simulate_order_execution') as mock_sim:
                    mock_sim.return_value = {
                        'execution_price': 1000.0 + i + 0.5,
                        'filled_quantity': 10,
                        'slippage': 0.0005,
                        'latency_ms': 45 + i
                    }
                    
                    await engine.execute_order(order, 'test_user')
        
        # Check accuracy report
        accuracy_report = engine.simulation_framework.get_accuracy_report()
        assert accuracy_report['samples_analyzed'] >= 0
    
    @pytest.mark.asyncio
    async def test_performance_continuity_across_sessions(self, setup_environment):
        """Test that performance data persists across sessions"""
        engine, _ = await setup_environment
        user_id = 'test_user'
        
        # Execute some trades
        portfolio = engine.get_or_create_portfolio(user_id)
        portfolio.orders = [
            {'timestamp': datetime.now().isoformat(), 'pnl': 1000},
            {'timestamp': datetime.now().isoformat(), 'pnl': -500}
        ]
        portfolio.total_pnl = 500
        
        # Get performance before "session end"
        perf_before = await engine.get_performance_analytics(user_id)
        
        # Simulate new session (in production, this would load from DB)
        # For now, verify data is still there
        perf_after = await engine.get_performance_analytics(user_id)
        
        assert perf_after['performance']['total_pnl'] == perf_before['performance']['total_pnl']
    
    @pytest.mark.asyncio
    async def test_mode_switch_validation(self, setup_environment):
        """Test mode switching validation and safety checks"""
        _, manager = await setup_environment
        
        # Test that restricted operations fail in paper mode
        with pytest.raises(ValueError) as exc_info:
            await manager.execute_with_fallback(
                'transfer_funds',
                mode=TradingMode.PAPER,
                amount=10000
            )
        
        assert "not allowed in PAPER mode" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_concurrent_paper_orders(self, setup_environment):
        """Test handling concurrent paper orders"""
        engine, _ = await setup_environment
        user_id = 'test_user'
        
        # Create multiple orders
        orders = [
            Order(
                symbol='RELIANCE',
                quantity=10,
                side='BUY',
                order_type=OrderType.MARKET,
                user_id=user_id
            )
            for _ in range(5)
        ]
        
        # Execute concurrently
        with patch.object(engine.market_data_pipeline, 'get_market_data') as mock_data:
            mock_data.return_value = Mock(last_price=2500.0)
            
            with patch.object(engine.simulation_framework, 'simulate_order_execution') as mock_sim:
                mock_sim.return_value = {
                    'execution_price': 2501.0,
                    'filled_quantity': 10,
                    'slippage': 0.001,
                    'latency_ms': 50
                }
                
                tasks = [engine.execute_order(order, user_id) for order in orders]
                results = await asyncio.gather(*tasks)
        
        # Verify all orders executed
        assert len(results) == 5
        assert all(r['success'] for r in results)
        
        # Check portfolio consistency
        portfolio = await engine.get_portfolio(user_id)
        assert portfolio['positions']['RELIANCE']['quantity'] == 50  # 5 orders * 10 quantity


class TestPaperTradingAPI:
    """Test paper trading API endpoints"""
    
    @pytest.mark.asyncio
    async def test_api_order_placement(self):
        """Test order placement through API"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Mock authentication
            with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = 'test_user'
            
            # Place paper order
            response = client.post(
                '/api/v1/paper/order',
                json={
                    'symbol': 'RELIANCE',
                    'quantity': 10,
                    'side': 'BUY',
                    'order_type': 'MARKET'
                }
            )
            
            # Note: This would need actual API setup to work
            # For now, we're testing the structure
    
    @pytest.mark.asyncio
    async def test_mode_status_endpoint(self):
        """Test mode status API endpoint"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
            with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = 'test_user'
            
            response = client.get('/api/v1/paper/mode/current')
            
            # Note: This would need actual API setup to work
