"""
Tiered Data Validation Architecture for Market Data Pipeline
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
import statistics

from models.market_data import (
    MarketData, ValidationResult, ValidationTier, Alert, DataType
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Validation performance metrics"""
    tier: ValidationTier
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    average_processing_time_ms: float = 0.0
    accuracy_percentage: float = 0.0
    last_updated: datetime = None


class BaseValidator:
    """Base class for all validators"""
    
    def __init__(self, tier: ValidationTier, max_processing_time_ms: float):
        self.tier = tier
        self.max_processing_time_ms = max_processing_time_ms
        self.metrics = ValidationMetrics(tier=tier)
        self.processing_times = deque(maxlen=1000)  # Keep last 1000 processing times
        
    async def validate(self, data: MarketData) -> ValidationResult:
        """Validate market data"""
        start_time = time.time()
        
        try:
            result = await self._perform_validation(data)
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            self._update_metrics(result, processing_time_ms)
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Validation error in {self.tier.value} validator: {e}")
            
            result = ValidationResult(
                status="failed",
                confidence=0.0,
                tier_used=self.tier,
                processing_time_ms=processing_time_ms,
                recommended_action="retry_validation"
            )
            
            self._update_metrics(result, processing_time_ms)
            return result
    
    async def _perform_validation(self, data: MarketData) -> ValidationResult:
        """Perform actual validation - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _update_metrics(self, result: ValidationResult, processing_time_ms: float):
        """Update validation metrics"""
        self.metrics.total_validations += 1
        self.metrics.last_updated = datetime.now()
        
        if result.status == "validated":
            self.metrics.successful_validations += 1
        else:
            self.metrics.failed_validations += 1
        
        # Update processing time
        self.processing_times.append(processing_time_ms)
        self.metrics.average_processing_time_ms = statistics.mean(self.processing_times)
        
        # Update accuracy
        if self.metrics.total_validations > 0:
            self.metrics.accuracy_percentage = (
                self.metrics.successful_validations / self.metrics.total_validations * 100
            )
    
    def is_performance_acceptable(self) -> bool:
        """Check if validator performance is acceptable"""
        return (
            self.metrics.average_processing_time_ms <= self.max_processing_time_ms and
            self.metrics.accuracy_percentage >= 95.0
        )


class FastValidator(BaseValidator):
    """Tier 1: Fast validation for high-frequency symbols (<5ms)"""
    
    def __init__(self):
        super().__init__(ValidationTier.FAST, 5.0)
        
    async def _perform_validation(self, data: MarketData) -> ValidationResult:
        """Fast validation with basic checks"""
        # Basic data integrity checks
        if data.last_price <= 0:
            return ValidationResult(
                status="failed",
                confidence=0.0,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="reject_data",
                discrepancy_details={"error": "Invalid price"}
            )
        
        if data.volume < 0:
            return ValidationResult(
                status="failed",
                confidence=0.0,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="reject_data",
                discrepancy_details={"error": "Invalid volume"}
            )
        
        # Check timestamp freshness (within last 5 minutes)
        if data.timestamp < datetime.now() - timedelta(minutes=5):
            return ValidationResult(
                status="discrepancy_detected",
                confidence=0.7,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="use_with_caution",
                discrepancy_details={"error": "Stale data"}
            )
        
        # Check for reasonable price changes (not more than 20% in one update)
        if hasattr(data, 'previous_price') and data.previous_price:
            price_change_percent = abs((data.last_price - data.previous_price) / data.previous_price * 100)
            if price_change_percent > 20:
                return ValidationResult(
                    status="discrepancy_detected",
                    confidence=0.8,
                    tier_used=self.tier,
                    processing_time_ms=0.0,
                    recommended_action="cross_validate",
                    discrepancy_details={"error": "Large price change", "change_percent": price_change_percent}
                )
        
        return ValidationResult(
            status="validated",
            confidence=0.95,
            tier_used=self.tier,
            processing_time_ms=0.0,
            recommended_action="use_primary_data"
        )


class CrossSourceValidator(BaseValidator):
    """Tier 2: Cross-source validation for medium importance (<20ms)"""
    
    def __init__(self, secondary_sources: List[str]):
        super().__init__(ValidationTier.CROSS_SOURCE, 20.0)
        self.secondary_sources = secondary_sources
        self.discrepancy_threshold = 0.01  # 1% price difference threshold
        self.historical_data = defaultdict(lambda: deque(maxlen=100))  # Keep last 100 prices per symbol
        
    async def _perform_validation(self, data: MarketData) -> ValidationResult:
        """Cross-source validation with secondary data sources"""
        # Store historical data
        self.historical_data[data.symbol].append({
            'price': data.last_price,
            'timestamp': data.timestamp,
            'source': data.source
        })
        
        # Get secondary source data (simulated - in real implementation, fetch from other sources)
        secondary_data = await self._get_secondary_source_data(data.symbol)
        
        if not secondary_data:
            # No secondary data available, fall back to fast validation
            fast_validator = FastValidator()
            return await fast_validator.validate(data)
        
        # Compare prices across sources
        price_discrepancy = abs(data.last_price - secondary_data['price']) / secondary_data['price']
        
        if price_discrepancy > self.discrepancy_threshold:
            # Check historical patterns to determine if this is normal volatility
            is_normal_volatility = self._check_historical_volatility(data.symbol, data.last_price)
            
            if not is_normal_volatility:
                return ValidationResult(
                    status="discrepancy_detected",
                    confidence=0.85,
                    tier_used=self.tier,
                    processing_time_ms=0.0,
                    recommended_action="use_consensus_price",
                    discrepancy_details={
                        "price_discrepancy": price_discrepancy,
                        "primary_price": data.last_price,
                        "secondary_price": secondary_data['price'],
                        "threshold": self.discrepancy_threshold
                    }
                )
        
        # Validate against historical patterns
        historical_validation = self._validate_against_history(data)
        if historical_validation['status'] == 'anomaly':
            return ValidationResult(
                status="discrepancy_detected",
                confidence=0.9,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="investigate_anomaly",
                discrepancy_details=historical_validation['details']
            )
        
        return ValidationResult(
            status="validated",
            confidence=0.98,
            tier_used=self.tier,
            processing_time_ms=0.0,
            recommended_action="use_primary_data"
        )
    
    async def _get_secondary_source_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get secondary source data (simulated)"""
        # In real implementation, this would fetch from other data sources
        # For now, simulate with historical average
        if symbol in self.historical_data and len(self.historical_data[symbol]) >= 1:
            recent_prices = [entry['price'] for entry in list(self.historical_data[symbol])[-10:]]
            return {
                'price': statistics.mean(recent_prices),
                'timestamp': datetime.now(),
                'source': 'historical_average'
            }
        return None
    
    def _check_historical_volatility(self, symbol: str, current_price: float) -> bool:
        """Check if current price change is within normal volatility"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < 5:
            # With limited data, be more conservative - check percentage change
            if symbol in self.historical_data and len(self.historical_data[symbol]) > 0:
                recent_prices = [entry['price'] for entry in list(self.historical_data[symbol])[-10:]]
                avg_price = statistics.mean(recent_prices)
                if avg_price > 0:
                    price_change_percent = abs(current_price - avg_price) / avg_price
                    return price_change_percent <= 0.02  # 2% change threshold for limited data
            return True  # No data, assume normal
        
        recent_prices = [entry['price'] for entry in list(self.historical_data[symbol])[-10:]]
        avg_price = statistics.mean(recent_prices)
        std_dev = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        
        # Check if current price is within 2 standard deviations
        if std_dev > 0:
            z_score = abs(current_price - avg_price) / std_dev
            return z_score <= 2.0  # Within 2 standard deviations is normal
        
        # If no standard deviation, check for large percentage changes
        if avg_price > 0:
            price_change_percent = abs(current_price - avg_price) / avg_price
            return price_change_percent <= 0.05  # 5% change threshold
        
        return True
    
    def _validate_against_history(self, data: MarketData) -> Dict[str, Any]:
        """Validate data against historical patterns"""
        if data.symbol not in self.historical_data or len(self.historical_data[data.symbol]) < 5:
            return {'status': 'normal'}
        
        recent_entries = list(self.historical_data[data.symbol])[-5:]
        recent_prices = [entry['price'] for entry in recent_entries]
        
        # Check for sudden price jumps
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            price_changes.append(change)
        
        avg_change = statistics.mean(price_changes) if price_changes else 0
        current_change = abs(data.last_price - recent_prices[-1]) / recent_prices[-1] if recent_prices else 0
        
        # If current change is more than 5x the average change, it's an anomaly
        if avg_change > 0 and current_change > avg_change * 5:
            return {
                'status': 'anomaly',
                'details': {
                    'current_change': current_change,
                    'average_change': avg_change,
                    'anomaly_ratio': current_change / avg_change if avg_change > 0 else 0
                }
            }
        
        return {'status': 'normal'}


class DeepValidator(BaseValidator):
    """Tier 3: Deep validation for critical symbols (<50ms)"""
    
    def __init__(self, cross_source_validator: CrossSourceValidator):
        super().__init__(ValidationTier.DEEP, 50.0)
        self.cross_source_validator = cross_source_validator
        self.market_indicators = {}  # Market-wide indicators
        self.correlation_data = defaultdict(list)  # Correlation with other symbols
        
    async def _perform_validation(self, data: MarketData) -> ValidationResult:
        """Deep validation with comprehensive analysis"""
        # Start with cross-source validation
        cross_source_result = await self.cross_source_validator.validate(data)
        
        if cross_source_result.status == "failed":
            return cross_source_result
        
        # Market context validation
        market_context_result = await self._validate_market_context(data)
        if market_context_result['status'] == 'anomaly':
            return ValidationResult(
                status="discrepancy_detected",
                confidence=0.92,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="market_context_anomaly",
                discrepancy_details=market_context_result['details']
            )
        
        # Correlation validation
        correlation_result = await self._validate_correlations(data)
        if correlation_result['status'] == 'anomaly':
            return ValidationResult(
                status="discrepancy_detected",
                confidence=0.88,
                tier_used=self.tier,
                processing_time_ms=0.0,
                recommended_action="correlation_anomaly",
                discrepancy_details=correlation_result['details']
            )
        
        # Advanced statistical validation
        statistical_result = await self._statistical_validation(data)
        
        # Combine results
        confidence = min(cross_source_result.confidence, statistical_result['confidence'])
        
        return ValidationResult(
            status="validated",
            confidence=confidence,
            tier_used=self.tier,
            processing_time_ms=0.0,
            recommended_action="use_validated_data"
        )
    
    async def _validate_market_context(self, data: MarketData) -> Dict[str, Any]:
        """Validate against market-wide context"""
        # Check if symbol is moving against market trend
        market_trend = await self._get_market_trend(data.symbol)
        
        if market_trend:
            symbol_trend = self._calculate_symbol_trend(data.symbol)
            
            # If symbol is moving strongly against market, it might be an anomaly
            if abs(symbol_trend - market_trend) > 0.1:  # 10% difference
                return {
                    'status': 'anomaly',
                    'details': {
                        'symbol_trend': symbol_trend,
                        'market_trend': market_trend,
                        'divergence': abs(symbol_trend - market_trend)
                    }
                }
        
        return {'status': 'normal'}
    
    async def _validate_correlations(self, data: MarketData) -> Dict[str, Any]:
        """Validate against correlated symbols"""
        correlated_symbols = self._get_correlated_symbols(data.symbol)
        
        if not correlated_symbols:
            return {'status': 'normal'}
        
        # Check if symbol is moving in expected direction with correlated symbols
        correlation_anomalies = []
        
        for corr_symbol in correlated_symbols:
            if corr_symbol in self.cross_source_validator.historical_data:
                corr_data = list(self.cross_source_validator.historical_data[corr_symbol])
                if len(corr_data) >= 2:
                    corr_change = (corr_data[-1]['price'] - corr_data[-2]['price']) / corr_data[-2]['price']
                    symbol_change = self._get_recent_price_change(data.symbol)
                    
                    # Check correlation consistency
                    if symbol_change * corr_change < 0:  # Moving in opposite directions
                        correlation_anomalies.append({
                            'symbol': corr_symbol,
                            'symbol_change': symbol_change,
                            'correlated_change': corr_change
                        })
        
        if len(correlation_anomalies) > len(correlated_symbols) * 0.5:  # More than 50% anomalies
            return {
                'status': 'anomaly',
                'details': {
                    'correlation_anomalies': correlation_anomalies,
                    'anomaly_ratio': len(correlation_anomalies) / len(correlated_symbols)
                }
            }
        
        return {'status': 'normal'}
    
    async def _statistical_validation(self, data: MarketData) -> Dict[str, Any]:
        """Advanced statistical validation"""
        if data.symbol not in self.cross_source_validator.historical_data:
            return {'status': 'normal', 'confidence': 0.95}
        
        historical_data = list(self.cross_source_validator.historical_data[data.symbol])
        if len(historical_data) < 20:
            return {'status': 'normal', 'confidence': 0.95}
        
        prices = [entry['price'] for entry in historical_data[-20:]]  # Last 20 prices
        current_price = data.last_price
        
        # Z-score analysis
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        
        if std_dev > 0:
            z_score = abs(current_price - mean_price) / std_dev
            
            # Z-score > 3 is statistically significant anomaly
            if z_score > 3:
                return {
                    'status': 'anomaly',
                    'confidence': 0.7,
                    'details': {
                        'z_score': z_score,
                        'mean_price': mean_price,
                        'std_dev': std_dev,
                        'current_price': current_price
                    }
                }
            
            # Z-score > 2 is potentially anomalous
            elif z_score > 2:
                confidence = 0.85
            else:
                confidence = 0.95
        else:
            # No standard deviation (all prices same), check for large percentage change
            price_change_percent = abs(current_price - mean_price) / mean_price if mean_price > 0 else 0
            if price_change_percent > 0.05:  # 5% change threshold
                return {
                    'status': 'anomaly',
                    'confidence': 0.7,
                    'details': {
                        'price_change_percent': price_change_percent,
                        'mean_price': mean_price,
                        'current_price': current_price,
                        'reason': 'large_change_no_volatility'
                    }
                }
            confidence = 0.95
        
        return {'status': 'normal', 'confidence': confidence}
    
    async def _get_market_trend(self, symbol: str) -> Optional[float]:
        """Get market trend for symbol's sector/index"""
        # Simplified market trend calculation
        # In real implementation, this would fetch from market indices
        return 0.02  # 2% positive trend
    
    def _calculate_symbol_trend(self, symbol: str) -> float:
        """Calculate symbol's recent trend"""
        if symbol not in self.cross_source_validator.historical_data:
            return 0.0
        
        data = list(self.cross_source_validator.historical_data[symbol])
        if len(data) < 5:
            return 0.0
        
        # Calculate trend over last 5 data points
        recent_prices = [entry['price'] for entry in data[-5:]]
        first_price = recent_prices[0]
        last_price = recent_prices[-1]
        
        return (last_price - first_price) / first_price
    
    def _get_correlated_symbols(self, symbol: str) -> List[str]:
        """Get symbols correlated with the given symbol"""
        # Simplified correlation mapping
        correlations = {
            'NIFTY50': ['BANKNIFTY', 'FINNIFTY'],
            'RELIANCE': ['ONGC', 'BPCL'],
            'TCS': ['INFY', 'WIPRO']
        }
        return correlations.get(symbol, [])
    
    def _get_recent_price_change(self, symbol: str) -> float:
        """Get recent price change for symbol"""
        if symbol not in self.cross_source_validator.historical_data:
            return 0.0
        
        data = list(self.cross_source_validator.historical_data[symbol])
        if len(data) < 2:
            return 0.0
        
        current_price = data[-1]['price']
        previous_price = data[-2]['price']
        
        return (current_price - previous_price) / previous_price


class TieredDataValidationArchitecture:
    """Main tiered validation architecture"""
    
    def __init__(self):
        self.fast_validator = FastValidator()
        self.cross_source_validator = CrossSourceValidator(['fyers', 'upstox'])
        self.deep_validator = DeepValidator(self.cross_source_validator)
        
        self.validators = {
            ValidationTier.FAST: self.fast_validator,
            ValidationTier.CROSS_SOURCE: self.cross_source_validator,
            ValidationTier.DEEP: self.deep_validator
        }
        
        self.symbol_tiers = {}  # Track which tier each symbol uses
        self.accuracy_tracker = AccuracyTracker()
        
    async def validate_data(self, data: MarketData) -> ValidationResult:
        """Validate data using appropriate tier"""
        # Determine validation tier for symbol
        tier = self._determine_validation_tier(data.symbol)
        
        # Perform validation
        validator = self.validators[tier]
        result = await validator.validate(data)
        
        # Track accuracy
        self.accuracy_tracker.record_validation(data.symbol, result)
        
        # Adjust tier if needed
        await self._adjust_tier_if_needed(data.symbol, result)
        
        return result
    
    def _determine_validation_tier(self, symbol: str) -> ValidationTier:
        """Determine appropriate validation tier for symbol"""
        # Check if symbol has a specific tier assigned
        if symbol in self.symbol_tiers:
            return self.symbol_tiers[symbol]
        
        # Determine tier based on symbol characteristics
        priority_symbols = ['NIFTY50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK']
        
        if symbol in priority_symbols:
            return ValidationTier.DEEP
        elif symbol.startswith('NIFTY') or symbol in ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY']:
            return ValidationTier.CROSS_SOURCE
        else:
            return ValidationTier.FAST
    
    async def _adjust_tier_if_needed(self, symbol: str, result: ValidationResult):
        """Adjust validation tier based on results"""
        current_tier = self.symbol_tiers.get(symbol, self._determine_validation_tier(symbol))
        
        # If validation is failing frequently, increase tier
        recent_results = self.accuracy_tracker.get_recent_results(symbol, 10)
        if len(recent_results) >= 5:
            failure_rate = sum(1 for r in recent_results if r.status != "validated") / len(recent_results)
            
            if failure_rate > 0.2:  # More than 20% failures
                if current_tier == ValidationTier.FAST:
                    self.symbol_tiers[symbol] = ValidationTier.CROSS_SOURCE
                    logger.info(f"Upgraded validation tier for {symbol} to CROSS_SOURCE due to high failure rate")
                elif current_tier == ValidationTier.CROSS_SOURCE:
                    self.symbol_tiers[symbol] = ValidationTier.DEEP
                    logger.info(f"Upgraded validation tier for {symbol} to DEEP due to high failure rate")
            
            # If validation is performing well, consider downgrading tier
            elif failure_rate < 0.05:  # Less than 5% failures
                if current_tier == ValidationTier.DEEP:
                    # Only downgrade if performance is good
                    validator = self.validators[current_tier]
                    if validator.is_performance_acceptable():
                        self.symbol_tiers[symbol] = ValidationTier.CROSS_SOURCE
                        logger.info(f"Downgraded validation tier for {symbol} to CROSS_SOURCE due to good performance")
                elif current_tier == ValidationTier.CROSS_SOURCE:
                    validator = self.validators[current_tier]
                    if validator.is_performance_acceptable():
                        self.symbol_tiers[symbol] = ValidationTier.FAST
                        logger.info(f"Downgraded validation tier for {symbol} to FAST due to good performance")
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get comprehensive validation metrics"""
        metrics = {}
        
        for tier, validator in self.validators.items():
            metrics[tier.value] = {
                'total_validations': validator.metrics.total_validations,
                'successful_validations': validator.metrics.successful_validations,
                'failed_validations': validator.metrics.failed_validations,
                'average_processing_time_ms': validator.metrics.average_processing_time_ms,
                'accuracy_percentage': validator.metrics.accuracy_percentage,
                'is_performance_acceptable': validator.is_performance_acceptable(),
                'last_updated': validator.metrics.last_updated.isoformat() if validator.metrics.last_updated else None
            }
        
        # Overall accuracy
        overall_accuracy = self.accuracy_tracker.get_overall_accuracy()
        metrics['overall_accuracy'] = overall_accuracy
        
        # Symbol tier distribution
        tier_distribution = defaultdict(int)
        for symbol, tier in self.symbol_tiers.items():
            tier_distribution[tier.value] += 1
        
        metrics['symbol_tier_distribution'] = dict(tier_distribution)
        
        return metrics


class AccuracyTracker:
    """Track validation accuracy across all symbols"""
    
    def __init__(self):
        self.validation_history = defaultdict(list)
        self.max_history_per_symbol = 1000
    
    def record_validation(self, symbol: str, result: ValidationResult):
        """Record validation result for a symbol"""
        # Handle both enum and string values for tier_used
        tier_value = result.tier_used
        if hasattr(tier_value, 'value'):
            tier_value = tier_value.value
        
        self.validation_history[symbol].append({
            'timestamp': datetime.now(),
            'status': result.status,
            'confidence': result.confidence,
            'tier': tier_value
        })
        
        # Keep only recent history
        if len(self.validation_history[symbol]) > self.max_history_per_symbol:
            self.validation_history[symbol] = self.validation_history[symbol][-self.max_history_per_symbol:]
    
    def get_recent_results(self, symbol: str, count: int) -> List[ValidationResult]:
        """Get recent validation results for a symbol"""
        if symbol not in self.validation_history:
            return []
        
        recent_entries = self.validation_history[symbol][-count:]
        return [
            ValidationResult(
                status=entry['status'],
                confidence=entry['confidence'],
                tier_used=ValidationTier(entry['tier']),
                processing_time_ms=0.0,
                recommended_action=""
            )
            for entry in recent_entries
        ]
    
    def get_overall_accuracy(self) -> float:
        """Get overall validation accuracy across all symbols"""
        if not self.validation_history:
            return 0.0
        
        total_validations = 0
        successful_validations = 0
        
        for symbol_history in self.validation_history.values():
            total_validations += len(symbol_history)
            successful_validations += sum(1 for entry in symbol_history if entry['status'] == 'validated')
        
        if total_validations == 0:
            return 0.0
        
        return successful_validations / total_validations * 100
