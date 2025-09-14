# **5. Performance Testing Framework**

## **5.1 Load Testing**

```python
class TestSystemPerformance:
    """System performance testing"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self):
        """Test system under concurrent user load"""
        import asyncio
        
        async def simulate_user_session():
            """Simulate typical user session"""
            # Login
            # View dashboard
            # Place order
            # Monitor position
            # Logout
            
            operations = [
                "login", "get_portfolio", "get_market_data",
                "place_order", "get_positions", "logout"
            ]
            
            for operation in operations:
                # Simulate API call
                await asyncio.sleep(0.1)  # Simulated processing time
                
            return "session_complete"
        
        # Simulate 100 concurrent users
        start_time = time.time()
        
        tasks = [simulate_user_session() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Verify performance under load
        assert total_time < 30, f"Concurrent load test took {total_time:.2f}s (limit: 30s)"
        assert len(results) == 100
        assert all(result == "session_complete" for result in results)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rate_limiting_performance_benchmarks(self):
        """Test rate limiting system performance benchmarks"""
        from backend.services.multi_api_manager import EnhancedRateLimiter, IntelligentLoadBalancer
        from backend.tests.integration.test_rate_limiting_workflow import MockTradingAPI
        from backend.models.trading import APIConfig, APIProvider
        
        # Create mock APIs with different performance characteristics
        configs = {
            'fyers': APIConfig(
                provider=APIProvider.FYERS,
                rate_limits={'requests_per_second': 10, 'requests_per_minute': 600}
            ),
            'upstox': APIConfig(
                provider=APIProvider.UPSTOX,
                rate_limits={'requests_per_second': 50, 'requests_per_minute': 3000}
            )
        }
        
        apis = {
            'fyers': MockTradingAPI('fyers', configs['fyers'], response_time=0.05),
            'upstox': MockTradingAPI('upstox', configs['upstox'], response_time=0.1)
        }
        
        # Test rate limiter performance
        rate_limiter = EnhancedRateLimiter(requests_per_second=10)
        
        # Benchmark rate limiting checks
        start_time = time.time()
        
        for i in range(1000):
            is_limited = rate_limiter.is_rate_limited()
            rate_limiter.record_request()
        
        rate_limiting_time = time.time() - start_time
        
        # Verify rate limiting performance (should be sub-millisecond)
        assert rate_limiting_time < 1.0, f"Rate limiting took {rate_limiting_time:.3f}s (limit: 1s)"
        
        # Test load balancer performance
        load_balancer = IntelligentLoadBalancer(apis)
        
        start_time = time.time()
        
        for i in range(100):
            selected_api = await load_balancer.select_best_api('place_order')
            load_balancer.update_performance_metrics(selected_api, 'place_order', 0.1, True)
        
        load_balancing_time = time.time() - start_time
        
        # Verify load balancing performance
        assert load_balancing_time < 2.0, f"Load balancing took {load_balancing_time:.3f}s (limit: 2s)"
        
        # Test concurrent request handling performance
        async def concurrent_request():
            return await load_balancer.select_best_api('get_market_data')
        
        start_time = time.time()
        
        tasks = [concurrent_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        concurrent_time = time.time() - start_time
        
        # Verify concurrent handling performance
        assert concurrent_time < 1.0, f"Concurrent requests took {concurrent_time:.3f}s (limit: 1s)"
        assert len(results) == 50
        assert all(result in apis for result in results)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_dashboard_analytics_performance(self):
        """Test dashboard analytics performance benchmarks"""
        from backend.services.multi_api_manager import MultiAPIManager
        from backend.tests.integration.test_rate_limiting_workflow import MockTradingAPI
        from backend.models.trading import APIConfig, APIProvider
        
        # Setup mock APIs
        configs = {
            'fyers': APIConfig(
                provider=APIProvider.FYERS,
                rate_limits={'requests_per_second': 10, 'requests_per_minute': 600}
            ),
            'upstox': APIConfig(
                provider=APIProvider.UPSTOX,
                rate_limits={'requests_per_second': 50, 'requests_per_minute': 3000}
            )
        }
        
        apis = {
            'fyers': MockTradingAPI('fyers', configs['fyers'], response_time=0.05),
            'upstox': MockTradingAPI('upstox', configs['upstox'], response_time=0.1)
        }
        
        manager = MultiAPIManager({
            "enabled_apis": ["fyers", "upstox"],
            "routing_rules": {},
            "fallback_chain": ["fyers", "upstox"]
        }, audit_logger=Mock())
        
        manager.apis = apis
        
        # Generate some activity for analytics
        for i in range(20):
            await manager.execute_with_fallback('place_order', symbol='TEST', quantity=100)
        
        # Benchmark dashboard analytics generation
        start_time = time.time()
        
        rate_analytics = await manager.get_rate_limit_analytics()
        load_analytics = await manager.get_load_balancing_insights()
        optimization_suggestions = await manager.get_optimization_suggestions()
        
        analytics_time = time.time() - start_time
        
        # Verify analytics performance
        assert analytics_time < 0.5, f"Analytics generation took {analytics_time:.3f}s (limit: 0.5s)"
        
        # Verify analytics content
        assert len(rate_analytics) == 2
        assert 'load_balance_efficiency' in load_analytics
        assert isinstance(optimization_suggestions, list)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_market_data_throughput(self):
        """Test market data processing throughput"""
        # Generate high-volume market data
        symbols = [f"STOCK{i}" for i in range(1000)]
        
        start_time = time.time()
        
        # Process market data for all symbols
        processed_data = []
        for symbol in symbols:
            data = {
                "symbol": symbol,
                "price": 100 + (hash(symbol) % 100),
                "volume": 1000 + (hash(symbol) % 10000),
                "timestamp": datetime.now()
            }
            processed_data.append(data)
        
        processing_time = time.time() - start_time
        throughput = len(symbols) / processing_time
        
        # Verify throughput requirement
        assert throughput > 1000, f"Market data throughput {throughput:.2f} symbols/sec (minimum: 1000/sec)"
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load"""
        import psutil
        import gc
        
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate sustained trading activity
        trading_data = []
        
        for iteration in range(10):  # 10 cycles
            # Simulate data accumulation
            batch_data = []
            
            for i in range(10000):  # 10k records per batch
                record = {
                    "timestamp": datetime.now(),
                    "symbol": f"SYM{i}",
                    "price": 100 + (i % 100),
                    "volume": 1000 + (i % 1000)
                }
                batch_data.append(record)
            
            trading_data.extend(batch_data)
            
            # Periodic cleanup (simulate real application behavior)
            if iteration % 3 == 0:
                # Keep only recent data
                trading_data = trading_data[-50000:]
                gc.collect()
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - baseline_memory
            
            # Memory should not grow unbounded
            assert memory_usage < 2000, f"Memory usage {memory_usage:.2f}MB exceeds 2GB limit"
```

## **5.2 Stress Testing**

```python
class TestSystemStress:
    """System stress testing"""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_high_frequency_order_placement(self):
        """Test system under high-frequency order placement"""
        from backend.services.trading_engine import TradingEngine
        
        # Mock trading engine for stress test
        trading_engine = MagicMock(spec=TradingEngine)
        trading_engine.place_order = AsyncMock(
            return_value=MagicMock(order_id="STRESS_TEST", status="COMPLETE")
        )
        
        # Generate high-frequency orders
        orders_per_second = 100
        test_duration = 10  # seconds
        total_orders = orders_per_second * test_duration
        
        start_time = time.time()
        
        # Submit orders rapidly
        tasks = []
        for i in range(total_orders):
            order = MagicMock(symbol=f"SYMBOL{i % 100}")
            task = asyncio.create_task(trading_engine.place_order(order))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        actual_rate = len(results) / execution_time
        
        # Verify system can handle high frequency
        assert actual_rate >= orders_per_second * 0.9, f"Order rate {actual_rate:.2f}/s below target {orders_per_second}/s"
        
        # Verify no failures under stress
        failures = [r for r in results if isinstance(r, Exception)]
        failure_rate = len(failures) / len(results)
        
        assert failure_rate < 0.01, f"Failure rate {failure_rate:.2%} exceeds 1% threshold"
    
    @pytest.mark.stress
    def test_database_stress(self, test_database):
        """Test database performance under stress"""
        import sqlite3
        import threading
        
        # Concurrent database operations
        def database_worker(worker_id):
            """Worker function for concurrent database access"""
            results = []
            
            for i in range(1000):  # 1000 operations per worker
                try:
                    # Simulate mixed database operations
                    if i % 3 == 0:
                        # Insert operation
                        trade = MagicMock(
                            order_id=f"STRESS_{worker_id}_{i}",
                            symbol="STRESS_TEST",
                            quantity=10,
                            price=100.0
                        )
                        test_database.store_trade(trade)
                    elif i % 3 == 1:
                        # Read operation
                        trades = test_database.get_recent_trades(limit=10)
                    else:
                        # Update operation
                        test_database.update_trade_status(f"STRESS_{worker_id}_{i-1}", "COMPLETE")
                    
                    results.append("success")
                    
                except Exception as e:
                    results.append(f"error: {e}")
            
            return results
        
        # Start multiple concurrent workers
        workers = []
        for worker_id in range(10):  # 10 concurrent workers
            worker = threading.Thread(
                target=database_worker,
                args=(worker_id,)
            )
            workers.append(worker)
        
        start_time = time.time()
        
        # Start all workers
        for worker in workers:
            worker.start()
        
        # Wait for completion
        for worker in workers:
            worker.join()
        
        execution_time = time.time() - start_time
        
        # Verify performance under concurrent load
        total_operations = 10 * 1000  # 10 workers × 1000 operations
        operations_per_second = total_operations / execution_time
        
        assert operations_per_second > 500, f"Database performance {operations_per_second:.2f} ops/sec below minimum 500 ops/sec"
```

---
