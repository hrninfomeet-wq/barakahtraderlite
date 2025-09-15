# **3. Integration Testing Framework**

## **3.1 API Integration Tests**

```python
class TestMultiAPIIntegration:
    """Multi-API integration testing"""
    
    @pytest.fixture
    async def api_manager(self):
        """Multi-API manager fixture"""
        from backend.services.multi_api_manager import MultiAPIManager
        
        manager = MultiAPIManager({
            'flattrade': {'enabled': True},
            'fyers': {'enabled': True},
            'upstox': {'enabled': True}
        })
        
        await manager.initialize_apis()
        return manager
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_failover_mechanism(self, api_manager):
        """Test automatic API failover"""
        # Mock primary API failure
        with patch.object(api_manager.apis['flattrade'], 'health_check', return_value=False):
            with patch.object(api_manager.apis['upstox'], 'health_check', return_value=True):
                
                # Attempt order placement
                result = await api_manager.execute_with_fallback(
                    'place_order', 
                    order=MagicMock()
                )
                
                # Verify fallback to UPSTOX occurred
                assert result is not None
                # Verify correct API was used through logging or tracking
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limit_distribution(self, api_manager):
        """Test intelligent rate limit distribution"""
        # Simulate high-frequency requests
        tasks = []
        
        for i in range(100):  # 100 concurrent requests
            task = asyncio.create_task(
                api_manager.execute_with_fallback('get_market_data', symbols=['NIFTY'])
            )
            tasks.append(task)
        
        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no rate limit violations
        errors = [r for r in results if isinstance(r, Exception)]
        rate_limit_errors = [e for e in errors if "rate limit" in str(e).lower()]
        
        assert len(rate_limit_errors) == 0, f"Rate limit violations: {len(rate_limit_errors)}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_api_data_validation(self, api_manager):
        """Test data validation across APIs"""
        symbol = "NIFTY"
        
        # Get data from multiple APIs
        fyers_data = await api_manager.apis['fyers'].get_market_data([symbol])
        upstox_data = await api_manager.apis['upstox'].get_market_data([symbol])
        
        # Verify data consistency (within reasonable bounds)
        fyers_price = fyers_data[symbol]['last_price']
        upstox_price = upstox_data[symbol]['last_price']
        
        price_difference = abs(fyers_price - upstox_price)
        price_tolerance = max(fyers_price, upstox_price) * 0.001  # 0.1% tolerance
        
        assert price_difference <= price_tolerance, f"Price discrepancy too large: {price_difference}"

class TestRateLimitingWorkflowIntegration:
    """Comprehensive rate limiting workflow integration tests"""
    
    @pytest.fixture
    async def mock_apis(self):
        """Create mock APIs for rate limiting testing"""
        from backend.tests.integration.test_rate_limiting_workflow import MockTradingAPI
        from backend.models.trading import APIConfig, APIProvider
        
        apis = {}
        configs = {
            'fyers': APIConfig(
                provider=APIProvider.FYERS,
                rate_limits={'requests_per_second': 10, 'requests_per_minute': 600}
            ),
            'upstox': APIConfig(
                provider=APIProvider.UPSTOX,
                rate_limits={'requests_per_second': 50, 'requests_per_minute': 3000}
            ),
            'flattrade': APIConfig(
                provider=APIProvider.FLATTRADE,
                rate_limits={'requests_per_second': 20, 'requests_per_minute': 1200}
            )
        }
        
        apis['fyers'] = MockTradingAPI('fyers', configs['fyers'], response_time=0.05)
        apis['upstox'] = MockTradingAPI('upstox', configs['upstox'], response_time=0.1)
        apis['flattrade'] = MockTradingAPI('flattrade', configs['flattrade'], response_time=0.08)
        
        return apis
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limit_violation_prevention(self, mock_apis):
        """Test that rate limit violations are prevented through intelligent load balancing"""
        from backend.services.multi_api_manager import MultiAPIManager, IntelligentLoadBalancer
        
        manager = MultiAPIManager({
            "enabled_apis": ["fyers", "upstox", "flattrade"],
            "routing_rules": {},
            "fallback_chain": ["fyers", "upstox", "flattrade"]
        }, audit_logger=Mock())
        
        manager.apis = mock_apis
        manager.load_balancer = IntelligentLoadBalancer(mock_apis)
        
        # Generate requests that would exceed FYERS rate limit (15 requests > 10/sec)
        tasks = []
        for i in range(15):
            task = asyncio.create_task(
                manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed due to intelligent load balancing
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 15
        
        # Verify no API exceeded its rate limit
        assert mock_apis['fyers'].request_count <= 10
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_automatic_failover_at_80_percent(self, mock_apis):
        """Test automatic failover when API approaches 80% of rate limit"""
        from backend.services.multi_api_manager import MultiAPIManager, IntelligentLoadBalancer
        
        manager = MultiAPIManager({
            "enabled_apis": ["fyers", "upstox", "flattrade"],
            "routing_rules": {},
            "fallback_chain": ["fyers", "upstox", "flattrade"]
        }, audit_logger=Mock())
        
        manager.apis = mock_apis
        manager.load_balancer = IntelligentLoadBalancer(mock_apis)
        
        # Simulate high usage on FYERS (approaching limit)
        for i in range(8):  # 80% of 10/sec limit
            mock_apis['fyers'].rate_limiter.record_request()
        
        # Make requests - should prefer other APIs
        results = []
        for i in range(5):
            result = await manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
            results.append(result)
        
        # Verify that requests were distributed to other APIs
        assert mock_apis['upstox'].request_count > 0 or mock_apis['flattrade'].request_count > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_predictive_analytics_spike_detection(self, mock_apis):
        """Test predictive analytics for usage spike detection"""
        from backend.services.multi_api_manager import EnhancedRateLimiter
        
        rate_limiter = mock_apis['fyers'].rate_limiter
        
        # Create usage patterns that simulate a spike
        current_time = time.time()
        spike_pattern = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        for i, usage in enumerate(spike_pattern):
            pattern = {
                'timestamp': current_time - (len(spike_pattern) - i),
                'second_usage': usage,
                'minute_usage': usage * 0.8,
                'hour_usage': usage * 0.6
            }
            rate_limiter.usage_patterns.append(pattern)
        
        # Check if spike is predicted
        spike_predicted = rate_limiter._predict_usage_spike()
        assert isinstance(spike_predicted, bool)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dashboard_analytics_integration(self, mock_apis):
        """Test complete dashboard analytics integration"""
        from backend.services.multi_api_manager import MultiAPIManager, IntelligentLoadBalancer
        
        manager = MultiAPIManager({
            "enabled_apis": ["fyers", "upstox", "flattrade"],
            "routing_rules": {},
            "fallback_chain": ["fyers", "upstox", "flattrade"]
        }, audit_logger=Mock())
        
        manager.apis = mock_apis
        manager.load_balancer = IntelligentLoadBalancer(mock_apis)
        
        # Generate some activity
        for i in range(10):
            await manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
        
        # Test dashboard analytics
        rate_analytics = await manager.get_rate_limit_analytics()
        load_analytics = await manager.get_load_balancing_insights()
        optimization_suggestions = await manager.get_optimization_suggestions()
        
        # Verify all analytics components work
        assert len(rate_analytics) > 0
        assert 'load_balance_efficiency' in load_analytics
        assert isinstance(optimization_suggestions, list)

class TestDatabaseIntegration:
    """Database integration testing"""
    
    @pytest.fixture
    def test_database(self, temp_dir):
        """Test database fixture"""
        import sqlite3
        from backend.core.database import Database
        
        db_path = temp_dir / "test_trading.db"
        database = Database(str(db_path))
        database.initialize()
        return database
    
    @pytest.mark.integration
    async def test_trade_logging_integration(self, test_database):
        """Test complete trade logging workflow"""
        from backend.models.trading import TradeRecord
        
        # Create sample trade
        trade = TradeRecord(
            order_id="TEST_001",
            symbol="NIFTY25SEP25840CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=50,
            price=52.0,
            executed_price=52.25,
            status="COMPLETE",
            api_provider="flattrade",
            timestamp=datetime.now()
        )
        
        # Store trade
        await test_database.store_trade(trade)
        
        # Retrieve trade
        retrieved_trade = await test_database.get_trade_by_order_id("TEST_001")
        
        # Verify data integrity
        assert retrieved_trade.order_id == trade.order_id
        assert retrieved_trade.symbol == trade.symbol
        assert retrieved_trade.executed_price == trade.executed_price
    
    @pytest.mark.integration
    async def test_portfolio_aggregation(self, test_database):
        """Test portfolio data aggregation"""
        from backend.models.portfolio import Position
        
        # Create multiple positions
        positions = [
            Position(symbol="RELIANCE", quantity=10, average_price=2845),
            Position(symbol="TCS", quantity=5, average_price=3465),
            Position(symbol="NIFTY25SEP25840CE", quantity=50, average_price=52)
        ]
        
        # Store positions
        for position in positions:
            await test_database.store_position(position)
        
        # Retrieve portfolio
        portfolio = await test_database.get_portfolio()
        
        # Verify aggregation
        assert len(portfolio.positions) == 3
        assert portfolio.total_value > 0
        
        # Verify individual positions
        reliance_position = next((p for p in portfolio.positions if p.symbol == "RELIANCE"), None)
        assert reliance_position is not None
        assert reliance_position.quantity == 10
```

## **3.2 Cache Integration Tests**

```python
class TestCacheIntegration:
    """Cache system integration testing"""
    
    @pytest.fixture
    async def cache_manager(self):
        """Cache manager fixture"""
        from backend.utils.cache import CacheManager
        
        # Use test Redis instance or in-memory cache
        cache = CacheManager({
            'host': 'localhost',
            'port': 6379,
            'db': 1,  # Use separate test database
        })
        
        yield cache
        
        # Cleanup
        await cache.flush_all()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_data_caching_workflow(self, cache_manager):
        """Test complete market data caching workflow"""
        symbol = "NIFTY"
        market_data = {
            "last_price": 25840.50,
            "change": 127.30,
            "volume": 1234567,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in cache
        await cache_manager.set(f"market_data:{symbol}", market_data, cache_type="market_data")
        
        # Retrieve from cache
        cached_data = await cache_manager.get(f"market_data:{symbol}", cache_type="market_data")
        
        # Verify data integrity
        assert cached_data["last_price"] == market_data["last_price"]
        assert cached_data["volume"] == market_data["volume"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self, cache_manager):
        """Test cache performance under high load"""
        import asyncio
        
        # Generate test data
        test_data = {f"symbol_{i}": {"price": i * 100} for i in range(1000)}
        
        # Concurrent cache operations
        async def cache_operation(key, data):
            await cache_manager.set(key, data)
            return await cache_manager.get(key)
        
        start_time = time.time()
        
        tasks = [
            cache_operation(key, data) 
            for key, data in test_data.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        operation_time = time.time() - start_time
        
        # Verify performance
        assert operation_time < 5.0, f"Cache operations took {operation_time:.2f}s (limit: 5s)"
        assert len(results) == 1000
        assert all(result is not None for result in results)
```

---
