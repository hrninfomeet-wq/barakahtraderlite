"""
Real-Time Performance Architecture with Multi-Layer Caching
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import json
import pickle
import hashlib

from models.market_data import (
    MarketData, CacheEntry, PerformanceMetrics, ValidationTier, DataType
)

logger = logging.getLogger(__name__)


class L1MemoryCache:
    """L1 Memory Cache for <1ms access times"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.access_times = deque(maxlen=1000)  # Track access performance
        self.hit_count = 0
        self.miss_count = 0
        
    async def get(self, key: str) -> Optional[MarketData]:
        """Get data from L1 cache"""
        start_time = time.time()
        
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                self.miss_count += 1
                self._record_access_time(time.time() - start_time)
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            self.hit_count += 1
            self._record_access_time(time.time() - start_time)
            
            return entry.data
        else:
            self.miss_count += 1
            self._record_access_time(time.time() - start_time)
            return None
    
    async def set(self, key: str, data: MarketData, ttl_seconds: float = 1.0):
        """Set data in L1 cache"""
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            await self._evict_oldest()
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        entry = CacheEntry(
            key=key,
            data=data,
            expires_at=expires_at
        )
        
        self.cache[key] = entry
    
    async def _evict_oldest(self):
        """Evict oldest entries when cache is full"""
        # Remove 10% of cache entries (least recently accessed)
        evict_count = max(1, len(self.cache) // 10)
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest entries
        for i in range(evict_count):
            key = sorted_entries[i][0]
            del self.cache[key]
    
    def _record_access_time(self, access_time: float):
        """Record access time for performance monitoring"""
        self.access_times.append(access_time * 1000)  # Convert to milliseconds
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get L1 cache performance metrics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        avg_access_time = (
            sum(self.access_times) / len(self.access_times) 
            if self.access_times else 0
        )
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'avg_access_time_ms': avg_access_time,
            'total_requests': total_requests
        }


class L2RedisCache:
    """L2 Redis Cache for <5ms access times"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.hit_count = 0
        self.miss_count = 0
        self.access_times = deque(maxlen=1000)
        
    async def get(self, key: str) -> Optional[MarketData]:
        """Get data from L2 cache"""
        start_time = time.time()
        
        try:
            if self.redis_client:
                cached_data = await self.redis_client.get(f"market_data:{key}")
                if cached_data:
                    data_dict = json.loads(cached_data)
                    market_data = MarketData(**data_dict)
                    self.hit_count += 1
                    self._record_access_time(time.time() - start_time)
                    return market_data
            
            self.miss_count += 1
            self._record_access_time(time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            self.miss_count += 1
            return None
    
    async def set(self, key: str, data: MarketData, ttl_seconds: float = 5.0):
        """Set data in L2 cache"""
        try:
            if self.redis_client:
                data_dict = data.dict()
                await self.redis_client.setex(
                    f"market_data:{key}",
                    int(ttl_seconds),
                    json.dumps(data_dict, default=str)
                )
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
    
    async def batch_get(self, keys: List[str]) -> Dict[str, MarketData]:
        """Batch get from L2 cache"""
        results = {}
        
        if not self.redis_client:
            return results
        
        try:
            cache_keys = [f"market_data:{key}" for key in keys]
            cached_data = await self.redis_client.mget(cache_keys)
            
            for i, data in enumerate(cached_data):
                if data:
                    try:
                        data_dict = json.loads(data)
                        market_data = MarketData(**data_dict)
                        results[keys[i]] = market_data
                        self.hit_count += 1
                    except Exception as e:
                        logger.error(f"Error parsing cached data for {keys[i]}: {e}")
                        self.miss_count += 1
                else:
                    self.miss_count += 1
                    
        except Exception as e:
            logger.error(f"L2 batch get error: {e}")
            self.miss_count += len(keys)
        
        return results
    
    def _record_access_time(self, access_time: float):
        """Record access time for performance monitoring"""
        self.access_times.append(access_time * 1000)  # Convert to milliseconds
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get L2 cache performance metrics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        avg_access_time = (
            sum(self.access_times) / len(self.access_times) 
            if self.access_times else 0
        )
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'avg_access_time_ms': avg_access_time,
            'total_requests': total_requests
        }


class L3APILayer:
    """L3 API Layer for <50ms direct API access"""
    
    def __init__(self, websocket_pool=None):
        self.websocket_pool = websocket_pool
        self.api_call_times = deque(maxlen=1000)
        self.successful_calls = 0
        self.failed_calls = 0
        
    async def batch_get(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get data directly from APIs"""
        start_time = time.time()
        results = {}
        
        try:
            if self.websocket_pool:
                # Subscribe to symbols if not already subscribed
                subscription_results = await self.websocket_pool.subscribe_symbols(symbols)
                
                # For now, simulate API response
                # In real implementation, this would fetch from subscribed WebSocket streams
                for symbol in symbols:
                    # Simulate API response with current timestamp
                    market_data = MarketData(
                        symbol=symbol,
                        exchange="NSE",
                        last_price=1000.0 + hash(symbol) % 1000,  # Simulate price
                        volume=1000000 + hash(symbol) % 1000000,  # Simulate volume
                        timestamp=datetime.now(),
                        data_type=DataType.PRICE,
                        source="api_direct",
                        validation_tier=ValidationTier.FAST
                    )
                    results[symbol] = market_data
                
                self.successful_calls += 1
            else:
                logger.error("No WebSocket pool available for API access")
                self.failed_calls += len(symbols)
                
        except Exception as e:
            logger.error(f"L3 API layer error: {e}")
            self.failed_calls += len(symbols)
        
        # Record performance
        api_time = time.time() - start_time
        self.api_call_times.append(api_time * 1000)  # Convert to milliseconds
        
        return results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get L3 API layer performance metrics"""
        total_calls = self.successful_calls + self.failed_calls
        success_rate = self.successful_calls / total_calls if total_calls > 0 else 0
        
        avg_response_time = (
            sum(self.api_call_times) / len(self.api_call_times) 
            if self.api_call_times else 0
        )
        
        return {
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': success_rate,
            'avg_response_time_ms': avg_response_time,
            'total_calls': total_calls
        }


class L4FallbackLayer:
    """L4 Fallback Layer for <100ms backup sources"""
    
    def __init__(self):
        self.fallback_sources = [
            "google_finance",
            "yahoo_finance", 
            "alpha_vantage"
        ]
        self.current_source_index = 0
        self.fallback_times = deque(maxlen=1000)
        self.successful_fallbacks = 0
        self.failed_fallbacks = 0
        
    async def batch_get(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get data from fallback sources"""
        start_time = time.time()
        results = {}
        
        for symbol in symbols:
            success = False
            
            # Try each fallback source until one succeeds
            for attempt in range(len(self.fallback_sources)):
                source = self.fallback_sources[self.current_source_index]
                
                try:
                    # Simulate fallback API call
                    market_data = await self._fetch_from_fallback_source(symbol, source)
                    if market_data:
                        results[symbol] = market_data
                        success = True
                        break
                except Exception as e:
                    logger.error(f"Fallback source {source} failed for {symbol}: {e}")
                
                # Move to next source
                self.current_source_index = (self.current_source_index + 1) % len(self.fallback_sources)
            
            if not success:
                logger.error(f"All fallback sources failed for {symbol}")
        
        # Record performance
        fallback_time = time.time() - start_time
        self.fallback_times.append(fallback_time * 1000)
        
        if results:
            self.successful_fallbacks += 1
        else:
            self.failed_fallbacks += 1
        
        return results
    
    async def _fetch_from_fallback_source(self, symbol: str, source: str) -> Optional[MarketData]:
        """Fetch data from specific fallback source"""
        # Simulate API delay
        await asyncio.sleep(0.01)  # 10ms delay
        
        # Simulate fallback response
        return MarketData(
            symbol=symbol,
            exchange="NSE",
            last_price=1000.0 + hash(f"{symbol}_{source}") % 1000,
            volume=1000000 + hash(f"{symbol}_{source}") % 1000000,
            timestamp=datetime.now(),
            data_type=DataType.PRICE,
            source=f"fallback_{source}",
            validation_tier=ValidationTier.FAST,
            confidence_score=0.8  # Lower confidence for fallback data
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get L4 fallback layer performance metrics"""
        total_fallbacks = self.successful_fallbacks + self.failed_fallbacks
        success_rate = self.successful_fallbacks / total_fallbacks if total_fallbacks > 0 else 0
        
        avg_response_time = (
            sum(self.fallback_times) / len(self.fallback_times) 
            if self.fallback_times else 0
        )
        
        return {
            'successful_fallbacks': self.successful_fallbacks,
            'failed_fallbacks': self.failed_fallbacks,
            'success_rate': success_rate,
            'avg_response_time_ms': avg_response_time,
            'total_fallbacks': total_fallbacks,
            'current_source': self.fallback_sources[self.current_source_index]
        }


class RealTimePerformanceArchitecture:
    """Multi-layer performance architecture for sub-100ms delivery"""
    
    def __init__(self, redis_client=None, websocket_pool=None):
        self.l1_cache = L1MemoryCache(max_size=10000)
        self.l2_cache = L2RedisCache(redis_client)
        self.l3_api = L3APILayer(websocket_pool)
        self.l4_fallback = L4FallbackLayer()
        
        self.data_layers = {
            'l1': self.l1_cache,
            'l2': self.l2_cache,
            'l3': self.l3_api,
            'l4': self.l4_fallback
        }
        
        self.performance_monitor = PerformanceMonitor(self)
        self.cache_warming_task = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize the performance architecture"""
        logger.info("Initializing Real-Time Performance Architecture")
        
        # Start performance monitoring
        self.performance_monitor.start()
        
        # Start cache warming
        self.cache_warming_task = asyncio.create_task(self._cache_warming_loop())
        
        self.is_running = True
        logger.info("Real-Time Performance Architecture initialized")
    
    async def shutdown(self):
        """Shutdown the performance architecture"""
        logger.info("Shutting down Real-Time Performance Architecture")
        self.is_running = False
        
        # Stop performance monitoring
        self.performance_monitor.stop()
        
        # Cancel cache warming task
        if self.cache_warming_task:
            self.cache_warming_task.cancel()
        
        logger.info("Real-Time Performance Architecture shutdown complete")
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get market data with multi-layer caching"""
        start_time = time.time()
        results = {}
        missing_symbols = symbols.copy()
        
        # L1 Cache (Memory) - <1ms
        for symbol in symbols:
            data = await self.l1_cache.get(symbol)
            if data and self._is_data_fresh(data, max_age_seconds=0.1):  # 100ms freshness
                results[symbol] = data
                missing_symbols.remove(symbol)
        
        # L2 Cache (Redis) - <5ms
        if missing_symbols:
            redis_data = await self.l2_cache.batch_get(missing_symbols)
            fresh_redis_data = {}
            
            for symbol, data in redis_data.items():
                if data and self._is_data_fresh(data, max_age_seconds=1.0):  # 1 second freshness
                    results[symbol] = data
                    fresh_redis_data[symbol] = data
                    missing_symbols.remove(symbol)
            
            # Update L1 cache with fresh L2 data
            for symbol, data in fresh_redis_data.items():
                await self.l1_cache.set(symbol, data, ttl_seconds=0.1)
        
        # L3 API (Direct) - <50ms
        if missing_symbols:
            api_data = await self.l3_api.batch_get(missing_symbols)
            fresh_api_data = {}
            
            for symbol, data in api_data.items():
                if data:
                    results[symbol] = data
                    fresh_api_data[symbol] = data
                    missing_symbols.remove(symbol)
            
            # Update caches with fresh API data
            for symbol, data in fresh_api_data.items():
                await self.l1_cache.set(symbol, data, ttl_seconds=0.1)
                await self.l2_cache.set(symbol, data, ttl_seconds=5.0)
        
        # L4 Fallback - <100ms
        if missing_symbols:
            fallback_data = await self.l4_fallback.batch_get(missing_symbols)
            
            for symbol, data in fallback_data.items():
                if data:
                    results[symbol] = data
                    # Don't cache fallback data as it's less reliable
        
        # Record performance
        total_time = time.time() - start_time
        await self.performance_monitor.record_request(symbols, results, total_time)
        
        return results
    
    def _is_data_fresh(self, data: MarketData, max_age_seconds: float) -> bool:
        """Check if data is fresh enough"""
        age = (datetime.now() - data.timestamp).total_seconds()
        return age <= max_age_seconds
    
    async def _cache_warming_loop(self):
        """Continuously warm cache with frequently accessed symbols"""
        while self.is_running:
            try:
                # Get frequently accessed symbols from distribution manager
                # This would be integrated with the symbol distribution manager
                frequent_symbols = ['NIFTY50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK']
                
                # Pre-fetch data for frequent symbols
                for symbol in frequent_symbols:
                    existing_data = await self.l1_cache.get(symbol)
                    if not existing_data or not self._is_data_fresh(existing_data, max_age_seconds=1.0):
                        # Fetch fresh data
                        fresh_data = await self.l3_api.batch_get([symbol])
                        if symbol in fresh_data:
                            await self.l1_cache.set(symbol, fresh_data[symbol], ttl_seconds=1.0)
                            await self.l2_cache.set(symbol, fresh_data[symbol], ttl_seconds=5.0)
                
                # Wait before next warming cycle
                await asyncio.sleep(10)  # Warm cache every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in cache warming loop: {e}")
                await asyncio.sleep(5)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            'l1_cache': self.l1_cache.get_performance_metrics(),
            'l2_cache': self.l2_cache.get_performance_metrics(),
            'l3_api': self.l3_api.get_performance_metrics(),
            'l4_fallback': self.l4_fallback.get_performance_metrics(),
            'performance_monitor': self.performance_monitor.get_metrics()
        }


class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self, performance_architecture: RealTimePerformanceArchitecture):
        self.architecture = performance_architecture
        self.metrics = {
            'response_times': deque(maxlen=1000),
            'cache_hit_rates': deque(maxlen=1000),
            'api_health': {},
            'error_rates': deque(maxlen=1000),
            'throughput': deque(maxlen=1000)
        }
        self.optimization_triggers = {
            'high_response_time': 80,  # 80ms threshold
            'low_cache_hit_rate': 0.7,  # 70% threshold
            'high_error_rate': 0.1  # 10% threshold
        }
        self.monitoring_task = None
        self.is_monitoring = False
        
    def start(self):
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.monitoring_task = asyncio.create_task(self._monitor_performance())
            self.is_monitoring = True
            logger.info("Performance monitoring started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("Performance monitoring stopped")
    
    async def record_request(self, symbols: List[str], results: Dict[str, MarketData], 
                           response_time: float):
        """Record request performance"""
        self.metrics['response_times'].append(response_time * 1000)  # Convert to ms
        self.metrics['throughput'].append(len(symbols) / response_time if response_time > 0 else 0)
        
        # Calculate cache hit rate for this request
        hit_rate = len(results) / len(symbols) if symbols else 0
        self.metrics['cache_hit_rates'].append(hit_rate)
        
        # Record errors (symbols requested but not returned)
        error_rate = (len(symbols) - len(results)) / len(symbols) if symbols else 0
        self.metrics['error_rates'].append(error_rate)
    
    async def _monitor_performance(self):
        """Continuous performance monitoring"""
        while self.is_monitoring:
            try:
                await self._check_performance_thresholds()
                await self._trigger_optimizations_if_needed()
                await asyncio.sleep(5)  # Monitor every 5 seconds
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _check_performance_thresholds(self):
        """Check if performance thresholds are exceeded"""
        if not self.metrics['response_times']:
            return
        
        current_avg_response = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        current_hit_rate = sum(self.metrics['cache_hit_rates']) / len(self.metrics['cache_hit_rates'])
        current_error_rate = sum(self.metrics['error_rates']) / len(self.metrics['error_rates'])
        
        # Check thresholds
        if current_avg_response > self.optimization_triggers['high_response_time']:
            logger.warning(f"High response time detected: {current_avg_response:.2f}ms")
            await self._trigger_response_time_optimization()
        
        if current_hit_rate < self.optimization_triggers['low_cache_hit_rate']:
            logger.warning(f"Low cache hit rate detected: {current_hit_rate:.2%}")
            await self._trigger_cache_optimization()
        
        if current_error_rate > self.optimization_triggers['high_error_rate']:
            logger.warning(f"High error rate detected: {current_error_rate:.2%}")
            await self._trigger_error_rate_optimization()
    
    async def _trigger_optimizations_if_needed(self):
        """Trigger optimizations based on performance metrics"""
        # This method would implement specific optimization strategies
        pass
    
    async def _trigger_response_time_optimization(self):
        """Optimize for response time"""
        logger.info("Triggering response time optimization")
        # Increase L1 cache size
        # Optimize symbol distribution
        # Scale connection pools
    
    async def _trigger_cache_optimization(self):
        """Optimize cache performance"""
        logger.info("Triggering cache optimization")
        # Increase cache TTL
        # Implement cache warming
        # Optimize cache eviction
    
    async def _trigger_error_rate_optimization(self):
        """Optimize for error rate"""
        logger.info("Triggering error rate optimization")
        # Improve fallback mechanisms
        # Enhance error handling
        # Scale resources
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = {}
        
        if self.metrics['response_times']:
            metrics['avg_response_time_ms'] = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            metrics['max_response_time_ms'] = max(self.metrics['response_times'])
            metrics['min_response_time_ms'] = min(self.metrics['response_times'])
        
        if self.metrics['cache_hit_rates']:
            metrics['avg_cache_hit_rate'] = sum(self.metrics['cache_hit_rates']) / len(self.metrics['cache_hit_rates'])
        
        if self.metrics['throughput']:
            metrics['avg_throughput_symbols_per_second'] = sum(self.metrics['throughput']) / len(self.metrics['throughput'])
        
        if self.metrics['error_rates']:
            metrics['avg_error_rate'] = sum(self.metrics['error_rates']) / len(self.metrics['error_rates'])
        
        return metrics
