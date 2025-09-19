"""
Market Data Service - Core Real-Time Data Pipeline
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import uuid

from models.market_data import (
    MarketData, MarketDataRequest, MarketDataResponse, PerformanceMetrics,
    ValidationResult, Alert, DataType, ValidationTier
)
from services.websocket_connection_pool import WebSocketConnectionPool
from services.tiered_data_validation import TieredDataValidationArchitecture
from services.real_time_performance_architecture import RealTimePerformanceArchitecture
from services.symbol_distribution_manager import SymbolDistributionManager

logger = logging.getLogger(__name__)


class MarketDataPipeline:
    """Main market data pipeline orchestrating all components"""

    def __init__(self, redis_client=None):
        self.pipeline_id = str(uuid.uuid4())
        self.is_running = False

        # Core components
        self.websocket_pool = WebSocketConnectionPool()
        self.validation_architecture = TieredDataValidationArchitecture()
        self.performance_architecture = RealTimePerformanceArchitecture(
            redis_client=redis_client,
            websocket_pool=self.websocket_pool
        )
        self.symbol_distribution = SymbolDistributionManager()

        # Pipeline state
        self.subscribed_symbols = set()
        self.data_streams = {}
        self.performance_metrics = PerformanceMetrics(
            response_time_ms=0.0,
            cache_hit_rate=0.0,
            validation_accuracy=0.0,
            connection_uptime=0.0,
            error_rate=0.0,
            throughput_symbols_per_second=0.0
        )

        # Event handlers
        self.data_handlers: List[Callable[[MarketData], Any]] = []
        self.alert_handlers: List[Callable[[Alert], Any]] = []

        # Pipeline tasks
        self.pipeline_tasks = []

    async def initialize(self):
        """Initialize the market data pipeline"""
        logger.info(f"Initializing Market Data Pipeline: {self.pipeline_id}")

        try:
            # Initialize core components
            await self.websocket_pool.initialize()
            await self.performance_architecture.initialize()

            # Start pipeline tasks
            self._start_pipeline_tasks()

            self.is_running = True
            logger.info(f"Market Data Pipeline initialized successfully: {self.pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to initialize Market Data Pipeline: {e}")
            await self.shutdown()
            raise

    async def shutdown(self):
        """Shutdown the market data pipeline"""
        logger.info(f"Shutting down Market Data Pipeline: {self.pipeline_id}")
        self.is_running = False

        # Cancel all pipeline tasks
        for task in self.pipeline_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.pipeline_tasks:
            await asyncio.gather(*self.pipeline_tasks, return_exceptions=True)

        # Shutdown core components
        await self.performance_architecture.shutdown()
        await self.websocket_pool.shutdown()

        logger.info(f"Market Data Pipeline shutdown complete: {self.pipeline_id}")

    def _start_pipeline_tasks(self):
        """Start background pipeline tasks"""
        # Data processing task
        self.pipeline_tasks.append(
            asyncio.create_task(self._data_processing_loop())
        )

        # Performance monitoring task
        self.pipeline_tasks.append(
            asyncio.create_task(self._performance_monitoring_loop())
        )

        # Health monitoring task
        self.pipeline_tasks.append(
            asyncio.create_task(self._health_monitoring_loop())
        )

        # Cache optimization task
        self.pipeline_tasks.append(
            asyncio.create_task(self._cache_optimization_loop())
        )

    async def get_market_data(self, request: MarketDataRequest) -> MarketDataResponse:
        """Get market data with comprehensive processing"""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Processing market data request {request_id} for {len(request.symbols)} symbols")

        try:
            # Validate request
            if not request.symbols:
                raise ValueError("No symbols specified in request")

            # Get data from performance architecture
            raw_data = await self.performance_architecture.get_market_data(request.symbols)

            # Validate data using tiered validation
            validated_data = {}
            validation_results = {}

            for symbol, data in raw_data.items():
                validation_result = await self.validation_architecture.validate_data(data)
                validation_results[symbol] = validation_result

                # Only include data that passes validation
                if validation_result.status == "validated":
                    validated_data[symbol] = data
                elif validation_result.status == "discrepancy_detected":
                    # Include with lower confidence
                    data.confidence_score = validation_result.confidence
                    validated_data[symbol] = data

                # Create alert for validation issues
                if validation_result.status in ["discrepancy_detected", "failed"]:
                    await self._create_validation_alert(symbol, validation_result)

            # Calculate performance metrics
            processing_time_ms = (time.time() - start_time) * 1000
            cache_hit_rate = self.performance_architecture.l1_cache.hit_count / (
                self.performance_architecture.l1_cache.hit_count +
                self.performance_architecture.l1_cache.miss_count
            ) if (self.performance_architecture.l1_cache.hit_count +
                  self.performance_architecture.l1_cache.miss_count) > 0 else 0

            # Create response
            response = MarketDataResponse(
                request_id=request_id,
                symbols_requested=request.symbols,
                symbols_returned=list(validated_data.keys()),
                data=validated_data,
                performance_metrics=PerformanceMetrics(
                    response_time_ms=processing_time_ms,
                    cache_hit_rate=cache_hit_rate,
                    validation_accuracy=len(validated_data) / len(request.symbols) if request.symbols else 0,
                    connection_uptime=self._calculate_connection_uptime(),
                    error_rate=self._calculate_error_rate(),
                    throughput_symbols_per_second=len(request.symbols) / (processing_time_ms / 1000) if processing_time_ms > 0 else 0
                ),
                validation_results=validation_results,
                cache_hit_rate=cache_hit_rate,
                processing_time_ms=processing_time_ms
            )

            logger.info(f"Market data request {request_id} completed: "
                       f"{len(validated_data)}/{len(request.symbols)} symbols, "
                       f"{processing_time_ms:.2f}ms")

            return response

        except Exception as e:
            logger.error(f"Error processing market data request {request_id}: {e}")

            # Return error response
            return MarketDataResponse(
                request_id=request_id,
                symbols_requested=request.symbols,
                symbols_returned=[],
                data={},
                performance_metrics=PerformanceMetrics(
                    response_time_ms=(time.time() - start_time) * 1000,
                    cache_hit_rate=0.0,
                    validation_accuracy=0.0,
                    connection_uptime=0.0,
                    error_rate=1.0,
                    throughput_symbols_per_second=0.0
                ),
                validation_results={},
                cache_hit_rate=0.0,
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def subscribe_to_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to real-time data for symbols"""
        try:
            # Update symbol distribution
            for symbol in symbols:
                self.symbol_distribution.update_symbol_usage(symbol)

            # Subscribe via WebSocket pool
            subscription_results = await self.websocket_pool.subscribe_symbols(symbols)

            # Check if any subscriptions were successful
            success_count = sum(1 for success in subscription_results.values() if success)

            if success_count > 0:
                self.subscribed_symbols.update(symbols)
                logger.info(f"Successfully subscribed to {success_count}/{len(symbols)} symbols")

                # Notify data handlers about new subscriptions
                for handler in self.data_handlers:
                    try:
                        await handler(None)  # Subscription notification
                    except Exception as e:
                        logger.error(f"Error in data handler during subscription: {e}")

                return True
            else:
                logger.error(f"Failed to subscribe to any of {len(symbols)} symbols")
                return False

        except Exception as e:
            logger.error(f"Error subscribing to symbols: {e}")
            return False

    async def unsubscribe_from_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from real-time data for symbols"""
        try:
            # Remove from subscribed symbols
            self.subscribed_symbols -= set(symbols)

            # Unsubscribe via WebSocket pool
            # Note: WebSocket pool doesn't have unsubscribe method yet, would need to be implemented

            logger.info(f"Unsubscribed from {len(symbols)} symbols")
            return True

        except Exception as e:
            logger.error(f"Error unsubscribing from symbols: {e}")
            return False

    def add_data_handler(self, handler: Callable[[MarketData], Any]):
        """Add handler for real-time market data"""
        self.data_handlers.append(handler)

        # Add to WebSocket pool as well
        self.websocket_pool.add_data_handler(handler)

    def add_alert_handler(self, handler: Callable[[Alert], Any]):
        """Add handler for alerts"""
        self.alert_handlers.append(handler)

    async def _data_processing_loop(self):
        """Continuous data processing loop"""
        while self.is_running:
            try:
                # Process any pending data streams
                await self._process_data_streams()

                # Wait before next iteration
                await asyncio.sleep(0.1)  # 100ms processing interval

            except Exception as e:
                logger.error(f"Error in data processing loop: {e}")
                await asyncio.sleep(1)

    async def _process_data_streams(self):
        """Process incoming data streams"""
        # This would process real-time data from WebSocket streams
        # For now, this is a placeholder for the actual stream processing logic
        pass

    async def _performance_monitoring_loop(self):
        """Continuous performance monitoring"""
        while self.is_running:
            try:
                # Update performance metrics
                await self._update_performance_metrics()

                # Check performance thresholds
                await self._check_performance_thresholds()

                # Wait before next check
                await asyncio.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _update_performance_metrics(self):
        """Update pipeline performance metrics"""
        try:
            # Get metrics from all components
            performance_metrics = self.performance_architecture.get_performance_metrics()
            validation_metrics = self.validation_architecture.get_validation_metrics()
            connection_status = self.websocket_pool.get_connection_status()

            # Calculate overall metrics
            self.performance_metrics.cache_hit_rate = (
                performance_metrics['l1_cache']['hit_rate'] * 0.6 +  # L1 weight
                performance_metrics['l2_cache']['hit_rate'] * 0.4    # L2 weight
            )

            self.performance_metrics.validation_accuracy = validation_metrics.get('overall_accuracy', 0.0) / 100

            self.performance_metrics.connection_uptime = (
                connection_status['healthy_connections'] /
                connection_status['total_connections']
                if connection_status['total_connections'] > 0 else 0
            )

            self.performance_metrics.response_time_ms = performance_metrics['performance_monitor'].get('avg_response_time_ms', 0.0)
            self.performance_metrics.throughput_symbols_per_second = performance_metrics['performance_monitor'].get('avg_throughput_symbols_per_second', 0.0)

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    async def _check_performance_thresholds(self):
        """Check if performance thresholds are exceeded"""
        # Check response time threshold (100ms)
        if self.performance_metrics.response_time_ms > 100:
            await self._create_performance_alert(
                "high_response_time",
                f"Response time exceeded threshold: {self.performance_metrics.response_time_ms:.2f}ms > 100ms"
            )

        # Check cache hit rate threshold (70%)
        if self.performance_metrics.cache_hit_rate < 0.7:
            await self._create_performance_alert(
                "low_cache_hit_rate",
                f"Cache hit rate below threshold: {self.performance_metrics.cache_hit_rate:.2%} < 70%"
            )

        # Check validation accuracy threshold (99.5%)
        if self.performance_metrics.validation_accuracy < 0.995:
            await self._create_performance_alert(
                "low_validation_accuracy",
                f"Validation accuracy below threshold: {self.performance_metrics.validation_accuracy:.2%} < 99.5%"
            )

    async def _health_monitoring_loop(self):
        """Continuous health monitoring"""
        while self.is_running:
            try:
                # Check connection health
                connection_status = self.websocket_pool.get_connection_status()

                if connection_status['healthy_connections'] < connection_status['total_connections']:
                    unhealthy_count = connection_status['total_connections'] - connection_status['healthy_connections']
                    await self._create_health_alert(
                        "unhealthy_connections",
                        f"{unhealthy_count} unhealthy connections detected"
                    )

                # Check component health
                if not self.performance_architecture.is_running:
                    await self._create_health_alert(
                        "performance_architecture_down",
                        "Performance architecture is not running"
                    )

                # Wait before next check
                await asyncio.sleep(30)  # Health check every 30 seconds

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _cache_optimization_loop(self):
        """Continuous cache optimization"""
        while self.is_running:
            try:
                # Analyze cache performance
                cache_metrics = self.performance_architecture.l1_cache.get_performance_metrics()

                # If cache hit rate is low, trigger optimization
                if cache_metrics['hit_rate'] < 0.8:
                    await self._optimize_cache_performance()

                # Wait before next optimization cycle
                await asyncio.sleep(60)  # Optimize every minute

            except Exception as e:
                logger.error(f"Error in cache optimization loop: {e}")
                await asyncio.sleep(30)

    async def _optimize_cache_performance(self):
        """Optimize cache performance"""
        logger.info("Triggering cache optimization")

        try:
            # Increase L1 cache size if possible
            if self.performance_architecture.l1_cache.max_size < 20000:
                self.performance_architecture.l1_cache.max_size = min(
                    self.performance_architecture.l1_cache.max_size * 1.5,
                    20000
                )
                logger.info(f"Increased L1 cache size to {self.performance_architecture.l1_cache.max_size}")

            # Warm cache with frequently accessed symbols
            frequent_symbols = self.symbol_distribution._get_most_accessed_symbols(20)
            for symbol_info in frequent_symbols:
                symbol = symbol_info['symbol']
                await self.performance_architecture.get_market_data([symbol])

        except Exception as e:
            logger.error(f"Error optimizing cache performance: {e}")

    async def _create_validation_alert(self, symbol: str, validation_result: ValidationResult):
        """Create alert for validation issues"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="validation_discrepancy",
            severity="medium" if validation_result.status == "discrepancy_detected" else "high",
            message=f"Validation issue for {symbol}: {validation_result.recommended_action}",
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _create_performance_alert(self, alert_type: str, message: str):
        """Create alert for performance issues"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity="medium",
            message=message,
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _create_health_alert(self, alert_type: str, message: str):
        """Create alert for health issues"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity="high",
            message=message,
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def _calculate_connection_uptime(self) -> float:
        """Calculate overall connection uptime"""
        connection_status = self.websocket_pool.get_connection_status()
        if connection_status['total_connections'] == 0:
            return 0.0
        return connection_status['healthy_connections'] / connection_status['total_connections']

    def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        # This would calculate error rate based on failed requests vs total requests
        # For now, return 0 as placeholder
        return 0.0

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        return {
            'pipeline_id': self.pipeline_id,
            'is_running': self.is_running,
            'subscribed_symbols': list(self.subscribed_symbols),
            'performance_metrics': self.performance_metrics.model_dump(),
            'connection_status': self.websocket_pool.get_connection_status(),
            'validation_metrics': self.validation_architecture.get_validation_metrics(),
            'performance_architecture_metrics': self.performance_architecture.get_performance_metrics(),
            'symbol_distribution_analytics': self.symbol_distribution.get_symbol_statistics()
        }
