"""
Fallback Data Source Manager for Automatic Failover
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from enum import Enum
# import json  # Unused

from models.market_data import (
    MarketData, DataType, ValidationTier, Alert
)

logger = logging.getLogger(__name__)


class DataSourceStatus(str, Enum):
    """Data source status"""
    ACTIVE = "ACTIVE"
    STANDBY = "STANDBY"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class DataSourcePriority(str, Enum):
    """Data source priority"""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"
    FALLBACK = "FALLBACK"


class DataSource:
    """Represents a data source with health and performance metrics"""

    def __init__(self, source_id: str, name: str, priority: DataSourcePriority,
                 api_endpoint: str, max_symbols: int = 1000):
        self.source_id = source_id
        self.name = name
        self.priority = priority
        self.api_endpoint = api_endpoint
        self.max_symbols = max_symbols

        # Health metrics
        self.status = DataSourceStatus.UNKNOWN
        self.last_health_check = None
        self.health_check_interval = 30  # seconds
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # Performance metrics
        self.response_times = deque(maxlen=100)
        self.success_rate = deque(maxlen=100)
        self.availability_score = 1.0

        # Connection metrics
        self.active_connections = 0
        self.max_connections = 10
        self.last_response_time = None

        # Data quality metrics
        self.data_accuracy = 1.0
        self.data_freshness = 1.0

    async def health_check(self) -> bool:
        """Perform health check on data source"""
        start_time = time.time()

        try:
            # Simulate health check (in real implementation, this would ping the API)
            await asyncio.sleep(0.01)  # 10ms simulated check

            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            self.last_response_time = response_time
            self.last_health_check = datetime.now()

            # Determine if source is healthy
            avg_response_time = sum(self.response_times) / len(self.response_times)
            is_healthy = (
                avg_response_time < 1000 and  # Less than 1 second
                self.consecutive_failures < self.max_consecutive_failures
            )

            if is_healthy:
                self.status = DataSourceStatus.ACTIVE
                self.consecutive_failures = 0
                self.success_rate.append(1)
            else:
                self.status = DataSourceStatus.FAILED
                self.consecutive_failures += 1
                self.success_rate.append(0)

            # Update availability score
            self.availability_score = sum(self.success_rate) / len(self.success_rate) if self.success_rate else 0

            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self.status = DataSourceStatus.FAILED
            self.consecutive_failures += 1
            self.success_rate.append(0)
            self.last_health_check = datetime.now()
            return False

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get market data from this source"""
        if self.status != DataSourceStatus.ACTIVE:
            raise Exception(f"Data source {self.name} is not active (status: {self.status})")

        start_time = time.time()

        try:
            # Simulate API call
            await asyncio.sleep(0.05)  # 50ms simulated API call

            results = {}
            for symbol in symbols:
                # Simulate market data response
                market_data = MarketData(
                    symbol=symbol,
                    exchange="NSE",
                    last_price=1000.0 + hash(f"{symbol}_{self.source_id}") % 1000,
                    volume=1000000 + hash(f"{symbol}_{self.source_id}") % 1000000,
                    timestamp=datetime.now(),
                    data_type=DataType.PRICE,
                    source=self.source_id,
                    validation_tier=ValidationTier.FAST,
                    confidence_score=self.data_accuracy
                )
                results[symbol] = market_data

            # Record successful call
            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            self.success_rate.append(1)
            self.availability_score = sum(self.success_rate) / len(self.success_rate)

            return results

        except Exception as e:
            logger.error(f"Failed to get market data from {self.name}: {e}")
            self.success_rate.append(0)
            self.availability_score = sum(self.success_rate) / len(self.success_rate)
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get data source metrics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        return {
            'source_id': self.source_id,
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority.value,
            'availability_score': self.availability_score,
            'avg_response_time_ms': avg_response_time,
            'last_response_time_ms': self.last_response_time,
            'consecutive_failures': self.consecutive_failures,
            'active_connections': self.active_connections,
            'max_connections': self.max_connections,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'data_accuracy': self.data_accuracy,
            'data_freshness': self.data_freshness
        }


class FallbackDataSourceManager:
    """Manages multiple data sources with automatic failover"""

    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}
        self.source_priorities = defaultdict(list)  # Priority -> List of sources
        self.current_primary = None
        self.failover_history = deque(maxlen=100)

        # Health monitoring
        self.health_monitor_task = None
        self.is_monitoring = False

        # Failover configuration
        self.failover_threshold = 0.8  # Availability score threshold
        self.failover_cooldown = 60  # seconds between failover attempts
        self.last_failover_time = None

        # Alert handlers
        self.alert_handlers: List[callable] = []

    def add_data_source(self, source: DataSource):
        """Add a data source to the manager"""
        self.data_sources[source.source_id] = source
        self.source_priorities[source.priority].append(source)

        # Sort by priority
        for priority in self.source_priorities:
            self.source_priorities[priority].sort(key=lambda s: s.availability_score, reverse=True)

        # Set primary if none exists
        if not self.current_primary:
            self.current_primary = source

        logger.info(f"Added data source: {source.name} (priority: {source.priority.value})")

    async def initialize(self):
        """Initialize the fallback manager"""
        logger.info("Initializing Fallback Data Source Manager")

        # Perform initial health checks
        await self._perform_initial_health_checks()

        # Start health monitoring
        self.is_monitoring = True
        self.health_monitor_task = asyncio.create_task(self._health_monitoring_loop())

        logger.info("Fallback Data Source Manager initialized")

    async def shutdown(self):
        """Shutdown the fallback manager"""
        logger.info("Shutting down Fallback Data Source Manager")
        self.is_monitoring = False

        if self.health_monitor_task:
            self.health_monitor_task.cancel()

        logger.info("Fallback Data Source Manager shutdown complete")

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get market data with automatic failover"""
        if not self.data_sources:
            raise Exception("No data sources available")

        # Try sources in priority order
        for priority in [DataSourcePriority.PRIMARY, DataSourcePriority.SECONDARY,
                        DataSourcePriority.TERTIARY, DataSourcePriority.FALLBACK]:

            sources = self.source_priorities.get(priority, [])

            for source in sources:
                if source.status == DataSourceStatus.ACTIVE:
                    try:
                        logger.info(f"Attempting to get data from {source.name}")
                        results = await source.get_market_data(symbols)

                        # Record successful data retrieval
                        self._record_successful_retrieval(source)

                        return results

                    except Exception as e:
                        logger.warning(f"Failed to get data from {source.name}: {e}")
                        await self._handle_source_failure(source)
                        continue

            # If no sources in this priority worked, try next priority
            logger.warning(f"No active sources found in priority {priority.value}")

        # If all sources failed
        raise Exception("All data sources failed to provide market data")

    async def _perform_initial_health_checks(self):
        """Perform initial health checks on all sources"""
        health_check_tasks = []

        for source in self.data_sources.values():
            health_check_tasks.append(source.health_check())

        if health_check_tasks:
            results = await asyncio.gather(*health_check_tasks, return_exceptions=True)

            # Update source statuses based on health check results
            for i, (source, result) in enumerate(zip(self.data_sources.values(), results)):
                if isinstance(result, Exception):
                    logger.error(f"Health check failed for {source.name}: {result}")
                    source.status = DataSourceStatus.FAILED
                elif result:
                    source.status = DataSourceStatus.ACTIVE
                else:
                    source.status = DataSourceStatus.FAILED

        # Set primary source
        await self._update_primary_source()

    async def _health_monitoring_loop(self):
        """Continuous health monitoring of all sources"""
        while self.is_monitoring:
            try:
                # Perform health checks
                await self._perform_health_checks()

                # Update primary source if needed
                await self._update_primary_source()

                # Check for failover conditions
                await self._check_failover_conditions()

                # Wait before next health check cycle
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _perform_health_checks(self):
        """Perform health checks on all sources"""
        health_check_tasks = []

        for source in self.data_sources.values():
            # Only check if enough time has passed since last check
            if (not source.last_health_check or
                datetime.now() - source.last_health_check > timedelta(seconds=source.health_check_interval)):
                health_check_tasks.append(source.health_check())

        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)

    async def _update_primary_source(self):
        """Update primary source based on availability and priority"""
        best_source = None
        best_score = -1

        # Find best source by priority and availability
        for priority in [DataSourcePriority.PRIMARY, DataSourcePriority.SECONDARY,
                        DataSourcePriority.TERTIARY, DataSourcePriority.FALLBACK]:

            sources = self.source_priorities.get(priority, [])

            for source in sources:
                if source.status == DataSourceStatus.ACTIVE:
                    # Calculate composite score
                    score = (
                        source.availability_score * 0.4 +
                        (1 - source.data_accuracy) * 0.3 +
                        (1 - source.data_freshness) * 0.3
                    )

                    if score > best_score:
                        best_score = score
                        best_source = source

        # Update primary source if changed
        if best_source and best_source != self.current_primary:
            old_primary = self.current_primary
            self.current_primary = best_source

            logger.info(f"Primary source changed from {old_primary.name if old_primary else 'None'} to {best_source.name}")

            # Record failover
            self._record_failover(old_primary, best_source, "primary_source_change")

    async def _check_failover_conditions(self):
        """Check if failover conditions are met"""
        if not self.current_primary:
            return

        # Check if primary source needs failover
        if (self.current_primary.availability_score < self.failover_threshold and
            self.current_primary.status == DataSourceStatus.ACTIVE):

            # Check failover cooldown
            if (self.last_failover_time and
                datetime.now() - self.last_failover_time < timedelta(seconds=self.failover_cooldown)):
                return

            await self._trigger_failover(self.current_primary, "low_availability")

    async def _trigger_failover(self, failed_source: DataSource, reason: str):
        """Trigger failover to next best source"""
        logger.warning(f"Triggering failover from {failed_source.name} due to: {reason}")

        # Find next best source
        next_source = self._find_next_best_source(failed_source)

        if next_source:
            # Perform failover
            old_primary = self.current_primary
            self.current_primary = next_source
            self.last_failover_time = datetime.now()

            # Record failover
            self._record_failover(old_primary, next_source, reason)

            # Create alert
            await self._create_failover_alert(failed_source, next_source, reason)

            logger.info(f"Failover completed: {failed_source.name} -> {next_source.name}")
        else:
            logger.error(f"No alternative source available for failover from {failed_source.name}")
            await self._create_no_failover_alert(failed_source, reason)

    def _find_next_best_source(self, exclude_source: DataSource) -> Optional[DataSource]:
        """Find the next best source excluding the given one"""
        best_source = None
        best_score = -1

        for priority in [DataSourcePriority.PRIMARY, DataSourcePriority.SECONDARY,
                        DataSourcePriority.TERTIARY, DataSourcePriority.FALLBACK]:

            sources = self.source_priorities.get(priority, [])

            for source in sources:
                if source != exclude_source and source.status == DataSourceStatus.ACTIVE:
                    # Calculate composite score
                    score = (
                        source.availability_score * 0.4 +
                        (1 - source.data_accuracy) * 0.3 +
                        (1 - source.data_freshness) * 0.3
                    )

                    if score > best_score:
                        best_score = score
                        best_source = source

        return best_source

    async def _handle_source_failure(self, source: DataSource):
        """Handle source failure"""
        logger.error(f"Source failure detected: {source.name}")

        # Update source status
        source.status = DataSourceStatus.FAILED
        source.consecutive_failures += 1

        # Create failure alert
        await self._create_source_failure_alert(source)

        # Trigger failover if this is the primary source
        if source == self.current_primary:
            await self._trigger_failover(source, "source_failure")

    def _record_successful_retrieval(self, source: DataSource):
        """Record successful data retrieval"""
        # Update source metrics
        source.success_rate.append(1)
        source.availability_score = sum(source.success_rate) / len(source.success_rate)
        source.consecutive_failures = 0

        if source.status == DataSourceStatus.FAILED:
            source.status = DataSourceStatus.ACTIVE
            logger.info(f"Source {source.name} recovered")

    def _record_failover(self, from_source: Optional[DataSource], to_source: DataSource, reason: str):
        """Record failover event"""
        failover_record = {
            'timestamp': datetime.now(),
            'from_source': from_source.source_id if from_source else None,
            'to_source': to_source.source_id,
            'reason': reason
        }

        self.failover_history.append(failover_record)

    async def _create_failover_alert(self, failed_source: DataSource, new_source: DataSource, reason: str):
        """Create alert for failover event"""
        alert = Alert(
            alert_id=f"failover_{int(time.time())}",
            alert_type="failover",
            severity="high",
            message=f"Failover triggered: {failed_source.name} -> {new_source.name} (reason: {reason})",
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _create_source_failure_alert(self, source: DataSource):
        """Create alert for source failure"""
        alert = Alert(
            alert_id=f"source_failure_{int(time.time())}",
            alert_type="source_failure",
            severity="medium",
            message=f"Data source {source.name} has failed (consecutive failures: {source.consecutive_failures})",
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _create_no_failover_alert(self, failed_source: DataSource, reason: str):
        """Create alert when no failover is possible"""
        alert = Alert(
            alert_id=f"no_failover_{int(time.time())}",
            alert_type="no_failover",
            severity="critical",
            message=f"No alternative source available for failover from {failed_source.name} (reason: {reason})",
            timestamp=datetime.now()
        )

        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def add_alert_handler(self, handler: callable):
        """Add alert handler"""
        self.alert_handlers.append(handler)

    def get_manager_status(self) -> Dict[str, Any]:
        """Get comprehensive manager status"""
        return {
            'current_primary': self.current_primary.source_id if self.current_primary else None,
            'total_sources': len(self.data_sources),
            'active_sources': sum(1 for s in self.data_sources.values() if s.status == DataSourceStatus.ACTIVE),
            'failed_sources': sum(1 for s in self.data_sources.values() if s.status == DataSourceStatus.FAILED),
            'source_metrics': {source_id: source.get_metrics() for source_id, source in self.data_sources.items()},
            'failover_history': list(self.failover_history),
            'last_failover_time': self.last_failover_time.isoformat() if self.last_failover_time else None,
            'is_monitoring': self.is_monitoring
        }
