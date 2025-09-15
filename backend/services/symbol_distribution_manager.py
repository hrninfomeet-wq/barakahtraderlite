"""
Symbol Distribution Manager for Intelligent Symbol Allocation
Story 1.3: Real-Time Multi-Source Market Data Pipeline
"""

import math
import asyncio
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from backend.models.market_data import SymbolDistribution

logger = logging.getLogger(__name__)


class SymbolDistributionManager:
    """Intelligently distributes symbols across available connections"""
    
    def __init__(self):
        # Configuration - Set these first before calling other methods
        self.fyers_max_symbols = 200
        self.upstox_max_symbols = float('inf')  # Unlimited
        self.high_frequency_threshold = 100  # Accesses per hour
        self.medium_frequency_threshold = 50
        
        self.symbol_priority = self._load_symbol_priority()
        self.connection_capacity = self._calculate_connection_capacity()
        self.symbol_frequency = defaultdict(int)
        self.symbol_last_access = {}
        self.distribution_history = []
        
    def _load_symbol_priority(self) -> Dict[str, int]:
        """Load symbol priority configuration"""
        # Priority levels: 1=highest, 5=lowest
        return {
            # High priority symbols (major indices and liquid stocks)
            'NIFTY50': 1,
            'BANKNIFTY': 1,
            'FINNIFTY': 1,
            'RELIANCE': 1,
            'TCS': 1,
            'HDFCBANK': 1,
            'INFY': 1,
            'ICICIBANK': 1,
            'KOTAKBANK': 1,
            'HINDUNILVR': 1,
            
            # Medium priority symbols
            'NIFTY100': 2,
            'NIFTY200': 2,
            'NIFTY500': 2,
            
            # Default priority for unknown symbols
            '_default': 3
        }
    
    def _calculate_connection_capacity(self) -> Dict[str, int]:
        """Calculate connection capacity for each provider"""
        return {
            'fyers': self.fyers_max_symbols,
            'upstox': self.upstox_max_symbols
        }
    
    def get_symbol_priority(self, symbol: str) -> int:
        """Get priority for a symbol"""
        return self.symbol_priority.get(symbol, self.symbol_priority['_default'])
    
    def update_symbol_usage(self, symbol: str):
        """Update symbol usage statistics"""
        self.symbol_frequency[symbol] += 1
        self.symbol_last_access[symbol] = datetime.now()
    
    def get_symbol_frequency_category(self, symbol: str) -> str:
        """Get frequency category for a symbol"""
        frequency = self.symbol_frequency.get(symbol, 0)
        
        if frequency >= self.high_frequency_threshold:
            return 'high'
        elif frequency >= self.medium_frequency_threshold:
            return 'medium'
        else:
            return 'low'
    
    def distribute_symbols(self, requested_symbols: List[str]) -> SymbolDistribution:
        """Distribute symbols optimally across available connections"""
        logger.info(f"Distributing {len(requested_symbols)} symbols across connections")
        
        # Update usage statistics
        for symbol in requested_symbols:
            self.update_symbol_usage(symbol)
        
        # Categorize symbols by frequency and priority
        symbol_categories = self._categorize_symbols(requested_symbols)
        
        # Calculate required FYERS pools
        fyers_pools_needed = self._calculate_fyers_pools_needed(symbol_categories)
        
        # Distribute high-frequency symbols to FYERS pools
        fyers_distribution = self._distribute_to_fyers_pools(
            symbol_categories['high_frequency'], 
            fyers_pools_needed
        )
        
        # Distribute remaining symbols to UPSTOX
        upstox_symbols = (
            symbol_categories['medium_frequency'] + 
            symbol_categories['low_frequency']
        )
        
        # Create distribution result
        distribution = SymbolDistribution(
            fyers_pools=fyers_distribution,
            upstox_pool=upstox_symbols,
            total_symbols=len(requested_symbols)
        )
        
        # Record distribution history
        self._record_distribution(distribution)
        
        logger.info(f"Symbol distribution completed: {len(fyers_distribution)} FYERS pools, "
                   f"{len(upstox_symbols)} UPSTOX symbols")
        
        return distribution
    
    def _categorize_symbols(self, symbols: List[str]) -> Dict[str, List[str]]:
        """Categorize symbols by frequency and priority"""
        categories = {
            'high_frequency': [],
            'medium_frequency': [],
            'low_frequency': []
        }
        
        for symbol in symbols:
            frequency_category = self.get_symbol_frequency_category(symbol)
            priority = self.get_symbol_priority(symbol)
            
            # High-frequency symbols get priority to FYERS
            if frequency_category == 'high' or priority <= 2:
                categories['high_frequency'].append(symbol)
            elif frequency_category == 'medium' or priority == 3:
                categories['medium_frequency'].append(symbol)
            else:
                categories['low_frequency'].append(symbol)
        
        # Sort by priority within each category
        for category in categories:
            categories[category].sort(key=lambda s: self.get_symbol_priority(s))
        
        return categories
    
    def _calculate_fyers_pools_needed(self, symbol_categories: Dict[str, List[str]]) -> int:
        """Calculate number of FYERS pools needed"""
        high_freq_symbols = len(symbol_categories['high_frequency'])
        return max(1, math.ceil(high_freq_symbols / self.fyers_max_symbols))
    
    def _distribute_to_fyers_pools(self, high_frequency_symbols: List[str], 
                                  pools_needed: int) -> List[Dict[str, List[str]]]:
        """Distribute high-frequency symbols across FYERS pools"""
        if not high_frequency_symbols:
            return []
        
        pools = []
        symbols_per_pool = math.ceil(len(high_frequency_symbols) / pools_needed)
        
        for i in range(pools_needed):
            start_idx = i * symbols_per_pool
            end_idx = min(start_idx + symbols_per_pool, len(high_frequency_symbols))
            pool_symbols = high_frequency_symbols[start_idx:end_idx]
            
            if pool_symbols:  # Only create pool if it has symbols
                pools.append({
                    'pool_id': f'fyers_pool_{i}',
                    'symbols': pool_symbols,
                    'symbol_count': len(pool_symbols)
                })
        
        return pools
    
    def _record_distribution(self, distribution: SymbolDistribution):
        """Record distribution for analytics"""
        record = {
            'timestamp': datetime.now(),
            'total_symbols': distribution.total_symbols,
            'fyers_pools': len(distribution.fyers_pools),
            'upstox_symbols': len(distribution.upstox_pool),
            'distribution': distribution.model_dump()
        }
        
        self.distribution_history.append(record)
        
        # Keep only last 1000 records
        if len(self.distribution_history) > 1000:
            self.distribution_history = self.distribution_history[-1000:]
    
    def get_distribution_analytics(self) -> Dict[str, any]:
        """Get distribution analytics"""
        if not self.distribution_history:
            return {}
        
        recent_distributions = [
            d for d in self.distribution_history 
            if d['timestamp'] > datetime.now() - timedelta(hours=24)
        ]
        
        if not recent_distributions:
            return {}
        
        avg_fyers_pools = sum(d['fyers_pools'] for d in recent_distributions) / len(recent_distributions)
        avg_upstox_symbols = sum(d['upstox_symbols'] for d in recent_distributions) / len(recent_distributions)
        avg_total_symbols = sum(d['total_symbols'] for d in recent_distributions) / len(recent_distributions)
        
        return {
            'total_distributions': len(recent_distributions),
            'avg_fyers_pools': round(avg_fyers_pools, 2),
            'avg_upstox_symbols': round(avg_upstox_symbols, 2),
            'avg_total_symbols': round(avg_total_symbols, 2),
            'fyers_utilization': round(avg_total_symbols / (avg_fyers_pools * self.fyers_max_symbols) * 100, 2),
            'most_accessed_symbols': self._get_most_accessed_symbols(10)
        }
    
    def _get_most_accessed_symbols(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get most accessed symbols"""
        sorted_symbols = sorted(
            self.symbol_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {
                'symbol': symbol,
                'access_count': count,
                'last_access': self.symbol_last_access.get(symbol),
                'frequency_category': self.get_symbol_frequency_category(symbol),
                'priority': self.get_symbol_priority(symbol)
            }
            for symbol, count in sorted_symbols
        ]
    
    def optimize_distribution(self) -> Dict[str, any]:
        """Analyze and suggest distribution optimizations"""
        analytics = self.get_distribution_analytics()
        
        if not analytics:
            return {'status': 'no_data', 'message': 'No distribution data available'}
        
        suggestions = []
        
        # Check FYERS utilization
        fyers_utilization = analytics.get('fyers_utilization', 0)
        if fyers_utilization > 90:
            suggestions.append({
                'type': 'high_utilization',
                'message': f'FYERS pools are {fyers_utilization}% utilized. Consider adding more pools.',
                'severity': 'medium'
            })
        elif fyers_utilization < 50:
            suggestions.append({
                'type': 'low_utilization',
                'message': f'FYERS pools are only {fyers_utilization}% utilized. Consider consolidating pools.',
                'severity': 'low'
            })
        
        # Check symbol distribution balance
        avg_fyers_pools = analytics.get('avg_fyers_pools', 0)
        avg_upstox_symbols = analytics.get('avg_upstox_symbols', 0)
        
        if avg_upstox_symbols > avg_fyers_pools * self.fyers_max_symbols:
            suggestions.append({
                'type': 'unbalanced_distribution',
                'message': 'UPSTOX is handling more symbols than FYERS pools combined. Consider redistributing.',
                'severity': 'medium'
            })
        
        return {
            'status': 'analyzed',
            'analytics': analytics,
            'suggestions': suggestions,
            'optimization_score': self._calculate_optimization_score(analytics)
        }
    
    def _calculate_optimization_score(self, analytics: Dict[str, any]) -> float:
        """Calculate optimization score (0-100, higher is better)"""
        fyers_utilization = analytics.get('fyers_utilization', 0)
        
        # Optimal utilization is 70-85%
        if 70 <= fyers_utilization <= 85:
            utilization_score = 100
        elif fyers_utilization > 85:
            utilization_score = max(0, 100 - (fyers_utilization - 85) * 5)
        else:
            utilization_score = max(0, 100 - (70 - fyers_utilization) * 3)
        
        return round(utilization_score, 2)
    
    def get_symbol_statistics(self) -> Dict[str, any]:
        """Get comprehensive symbol statistics"""
        total_symbols = len(self.symbol_frequency)
        
        if total_symbols == 0:
            return {'total_symbols': 0}
        
        frequency_categories = defaultdict(int)
        priority_categories = defaultdict(int)
        
        for symbol in self.symbol_frequency.keys():
            frequency_categories[self.get_symbol_frequency_category(symbol)] += 1
            priority_categories[self.get_symbol_priority(symbol)] += 1
        
        return {
            'total_symbols': total_symbols,
            'frequency_distribution': dict(frequency_categories),
            'priority_distribution': dict(priority_categories),
            'most_accessed_symbols': self._get_most_accessed_symbols(20),
            'distribution_analytics': self.get_distribution_analytics(),
            'optimization_suggestions': self.optimize_distribution()
        }
