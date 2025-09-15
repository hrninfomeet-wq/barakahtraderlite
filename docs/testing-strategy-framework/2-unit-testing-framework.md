# **2. Unit Testing Framework**

## **2.1 Unit Testing Structure**

```python
# Core unit testing framework
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import numpy as np

class TestTradingEngine:
    """Comprehensive trading engine unit tests"""
    
    @pytest.fixture
    def trading_engine(self):
        """Trading engine test fixture"""
        from backend.services.trading_engine import TradingEngine
        from backend.services.multi_api_manager import MultiAPIManager
        from backend.services.risk_manager import RiskManager
        
        # Mock dependencies
        api_manager = MagicMock(spec=MultiAPIManager)
        risk_manager = MagicMock(spec=RiskManager)
        
        engine = TradingEngine(
            multi_api_manager=api_manager,
            risk_manager=risk_manager
        )
        
        return engine
    
    @pytest.fixture
    def sample_order(self):
        """Sample order for testing"""
        from backend.models.trading import OrderRequest
        
        return OrderRequest(
            symbol="NIFTY25SEP25840CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=50,
            order_type="MARKET",
            price=52.0,
            product_type="MIS",
            api_provider="flattrade"
        )
    
    @pytest.mark.asyncio
    async def test_place_order_success(self, trading_engine, sample_order):
        """Test successful order placement"""
        # Mock risk validation
        trading_engine.risk_manager.validate_order.return_value = MagicMock(
            approved=True, reason=None
        )
        
        # Mock API execution
        expected_response = MagicMock(
            order_id="TEST_12345",
            status="COMPLETE",
            executed_price=52.50,
            executed_quantity=50
        )
        
        trading_engine.multi_api_manager.execute_with_fallback.return_value = expected_response
        
        # Execute test
        result = await trading_engine.place_order(sample_order)
        
        # Assertions
        assert result.order_id == "TEST_12345"
        assert result.status == "COMPLETE"
        assert result.executed_price == 52.50
        assert result.executed_quantity == 50
        
        # Verify risk validation called
        trading_engine.risk_manager.validate_order.assert_called_once_with(sample_order)
        
        # Verify API execution called
        trading_engine.multi_api_manager.execute_with_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_place_order_risk_rejection(self, trading_engine, sample_order):
        """Test order rejection due to risk limits"""
        # Mock risk rejection
        trading_engine.risk_manager.validate_order.return_value = MagicMock(
            approved=False, 
            reason="Daily loss limit exceeded"
        )
        
        # Execute test and expect exception
        with pytest.raises(Exception) as exc_info:
            await trading_engine.place_order(sample_order)
        
        assert "Daily loss limit exceeded" in str(exc_info.value)
        
        # Verify API was not called
        trading_engine.multi_api_manager.execute_with_fallback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_order_execution_latency(self, trading_engine, sample_order):
        """Test order execution meets latency requirements"""
        import time
        
        # Mock successful execution with controlled timing
        async def mock_execute(*args, **kwargs):
            await asyncio.sleep(0.025)  # 25ms delay
            return MagicMock(order_id="LATENCY_TEST", status="COMPLETE")
        
        trading_engine.risk_manager.validate_order.return_value = MagicMock(approved=True)
        trading_engine.multi_api_manager.execute_with_fallback = mock_execute
        
        # Measure execution time
        start_time = time.time()
        result = await trading_engine.place_order(sample_order)
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert latency requirement met
        assert execution_time < 30, f"Execution time {execution_time:.2f}ms exceeds 30ms requirement"
        assert result.order_id == "LATENCY_TEST"

class TestGreeksCalculator:
    """NPU-accelerated Greeks calculator tests"""
    
    @pytest.fixture
    def greeks_calculator(self):
        """Greeks calculator test fixture"""
        from backend.services.greeks_calculator import GreeksCalculator
        return GreeksCalculator()
    
    @pytest.fixture
    def sample_option_position(self):
        """Sample option position for Greeks testing"""
        from backend.models.portfolio import Position
        
        return Position(
            symbol="NIFTY25SEP25840CE",
            quantity=50,
            average_price=52.0,
            current_price=55.0,
            strike_price=25840,
            expiry_date=datetime(2025, 9, 25),
            option_type="CE",
            underlying_price=25850
        )
    
    @pytest.mark.asyncio
    async def test_calculate_greeks_performance(self, greeks_calculator, sample_option_position):
        """Test Greeks calculation performance requirement"""
        import time
        
        # Measure Greeks calculation time
        start_time = time.time()
        greeks = await greeks_calculator.calculate_position_greeks(sample_option_position)
        calculation_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert performance requirement
        assert calculation_time < 10, f"Greeks calculation {calculation_time:.2f}ms exceeds 10ms requirement"
        
        # Verify Greeks structure
        assert hasattr(greeks, 'delta')
        assert hasattr(greeks, 'gamma')
        assert hasattr(greeks, 'theta')
        assert hasattr(greeks, 'vega')
        assert hasattr(greeks, 'rho')
        
        # Verify Greeks values are reasonable
        assert 0 <= greeks.delta <= 1  # Call option delta range
        assert greeks.gamma >= 0       # Gamma always positive
        assert greeks.theta <= 0       # Theta typically negative (time decay)
    
    @pytest.mark.asyncio
    async def test_portfolio_greeks_aggregation(self, greeks_calculator):
        """Test portfolio-level Greeks aggregation"""
        from backend.models.portfolio import Position
        
        # Create multiple positions
        positions = [
            Position(
                symbol="NIFTY25SEP25800CE", quantity=50, strike_price=25800,
                option_type="CE", current_price=75.0, underlying_price=25850
            ),
            Position(
                symbol="NIFTY25SEP25900CE", quantity=-25, strike_price=25900,
                option_type="CE", current_price=30.0, underlying_price=25850
            )
        ]
        
        # Calculate portfolio Greeks
        portfolio_greeks = await greeks_calculator.calculate_portfolio_greeks(positions)
        
        # Verify aggregation
        assert portfolio_greeks.delta is not None
        assert portfolio_greeks.positions == 2
        assert portfolio_greeks.last_updated is not None

class TestPaperTradingEngine:
    """Paper trading engine validation tests"""
    
    @pytest.fixture
    def paper_engine(self):
        """Paper trading engine fixture"""
        from backend.services.paper_trading_engine import PaperTradingEngine
        return PaperTradingEngine()
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for simulation"""
        return {
            "NIFTY25SEP25840CE": {
                "last_price": 52.0,
                "bid": 51.5,
                "ask": 52.5,
                "volume": 1000,
                "timestamp": datetime.now(timezone.utc)
            }
        }
    
    @pytest.mark.asyncio
    async def test_paper_order_execution_accuracy(self, paper_engine, sample_order, sample_market_data):
        """Test paper trading simulation accuracy"""
        # Mock market data
        with patch.object(paper_engine, 'get_current_market_data', return_value=sample_market_data["NIFTY25SEP25840CE"]):
            
            # Execute paper order
            result = await paper_engine.execute_order(sample_order)
            
            # Verify execution attributes
            assert result.is_paper_trade is True
            assert result.order_id.startswith("PAPER_")
            assert result.status in ["COMPLETE", "PARTIAL"]
            assert result.executed_quantity > 0
            
            # Verify realistic execution price (within slippage bounds)
            market_price = sample_market_data["NIFTY25SEP25840CE"]["last_price"]
            slippage_threshold = market_price * 0.002  # 0.2% max slippage
            
            assert abs(result.executed_price - market_price) <= slippage_threshold
    
    @pytest.mark.asyncio
    async def test_paper_portfolio_tracking(self, paper_engine, sample_order):
        """Test paper trading portfolio tracking accuracy"""
        # Execute multiple orders
        orders = [
            sample_order,
            # Add opposite order
            sample_order._replace(transaction_type="SELL", quantity=25)
        ]
        
        results = []
        for order in orders:
            with patch.object(paper_engine, 'get_current_market_data', return_value={"last_price": 52.0}):
                result = await paper_engine.execute_order(order)
                results.append(result)
        
        # Verify portfolio tracking
        portfolio = paper_engine.get_virtual_portfolio()
        
        # Net position should be 25 (50 bought - 25 sold)
        net_quantity = 0
        for position in portfolio.values():
            if position['symbol'] == sample_order.symbol:
                net_quantity = position['quantity']
        
        assert net_quantity == 25

class TestBTSTAnalyzer:
    """BTST intelligence engine tests"""
    
    @pytest.fixture
    def btst_analyzer(self):
        """BTST analyzer fixture"""
        from backend.services.btst_analyzer import BTSTAnalyzer
        return BTSTAnalyzer()
    
    @pytest.mark.asyncio
    async def test_btst_time_restriction(self, btst_analyzer):
        """Test BTST time-based activation (2:15 PM+ only)"""
        from datetime import time
        
        # Test before 2:15 PM
        morning_time = datetime.now().replace(hour=10, minute=30, second=0)
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = morning_time
            
            recommendations = await btst_analyzer.analyze_btst_candidates({}, morning_time)
            
            # Should return empty list before 2:15 PM
            assert recommendations == []
    
    @pytest.mark.asyncio
    async def test_btst_confidence_threshold(self, btst_analyzer):
        """Test BTST confidence threshold enforcement (8.5/10)"""
        afternoon_time = datetime.now().replace(hour=14, minute=30, second=0)
        
        # Mock market data
        market_data = {
            "RELIANCE": {"close": 2845, "volume": 100000},
            "TCS": {"close": 3465, "volume": 80000}
        }
        
        # Mock analysis factors to return different confidence levels
        with patch.object(btst_analyzer, 'analyze_factor') as mock_analyze:
            # RELIANCE: High confidence (should qualify)
            # TCS: Low confidence (should not qualify)
            
            def side_effect(symbol, factor, data):
                if symbol == "RELIANCE":
                    return 9.0  # High confidence
                else:
                    return 7.0  # Below threshold
            
            mock_analyze.side_effect = side_effect
            
            recommendations = await btst_analyzer.analyze_btst_candidates(market_data, afternoon_time)
            
            # Only RELIANCE should qualify
            assert len(recommendations) == 1
            assert recommendations[0].symbol == "RELIANCE"
            assert recommendations[0].confidence >= 8.5
    
    @pytest.mark.asyncio
    async def test_zero_force_policy(self, btst_analyzer):
        """Test zero-force policy implementation"""
        afternoon_time = datetime.now().replace(hour=14, minute=30, second=0)
        
        # Mock market data
        market_data = {
            "STOCK1": {"close": 100},
            "STOCK2": {"close": 200}
        }
        
        # Mock all factors to return low confidence
        with patch.object(btst_analyzer, 'analyze_factor', return_value=7.0):  # Below 8.5 threshold
            
            recommendations = await btst_analyzer.analyze_btst_candidates(market_data, afternoon_time)
            
            # Should return empty list (zero-force policy)
            assert recommendations == []
```

## **2.2 Performance Unit Tests**

```python
class TestPerformanceRequirements:
    """Performance-focused unit tests"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_ui_response_time(self):
        """Test UI response time requirement (<50ms)"""
        from frontend.utils.ui_helpers import process_dashboard_data
        
        # Sample data processing
        large_dataset = [{"symbol": f"STOCK{i}", "price": i * 10} for i in range(1000)]
        
        start_time = time.time()
        result = await process_dashboard_data(large_dataset)
        processing_time = (time.time() - start_time) * 1000
        
        assert processing_time < 50, f"UI processing {processing_time:.2f}ms exceeds 50ms requirement"
        assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_chart_rendering_performance(self):
        """Test chart rendering performance (<100ms)"""
        from frontend.components.chart_component import render_chart
        
        # Generate test data
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(1000)]
        prices = [25000 + (i % 100) for i in range(1000)]
        chart_data = list(zip(timestamps, prices))
        
        start_time = time.time()
        chart = await render_chart(chart_data, chart_type="candlestick")
        rendering_time = (time.time() - start_time) * 1000
        
        assert rendering_time < 100, f"Chart rendering {rendering_time:.2f}ms exceeds 100ms requirement"
        assert chart is not None
    
    @pytest.mark.performance
    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency"""
        import psutil
        import gc
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate large data processing
        large_data_structure = []
        for i in range(100000):
            large_data_structure.append({
                "timestamp": datetime.now(),
                "symbol": f"SYMBOL{i}",
                "price": i * 1.5,
                "volume": i * 100
            })
        
        # Process data
        processed_data = [item for item in large_data_structure if item["price"] > 1000]
        
        # Check memory usage
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - baseline_memory
        
        # Cleanup
        del large_data_structure
        del processed_data
        gc.collect()
        
        # Memory increase should be reasonable
        assert memory_increase < 500, f"Memory usage increased by {memory_increase:.2f}MB (limit: 500MB)"
```

---
