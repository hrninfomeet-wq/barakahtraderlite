# **9. Performance Monitoring & Analytics**

### **9.1 NPU Utilization Tracking**

#### **9.1.1 Hardware Performance Monitor**
```python
import psutil
import py3nvml.py3nvml as nvml

class HardwareMonitor:
    """Monitor NPU, GPU, and system performance"""
    
    def __init__(self):
        self.metrics = {
            'npu_utilization': 0,
            'gpu_utilization': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        self.initialize_monitoring()
    
    def initialize_monitoring(self):
        """Initialize hardware monitoring capabilities"""
        try:
            # Initialize NVIDIA ML for GPU monitoring
            nvml.nvmlInit()
            self.gpu_available = True
        except:
            self.gpu_available = False
    
    async def get_npu_utilization(self) -> float:
        """Get NPU utilization percentage"""
        try:
            # Intel NPU monitoring (platform-specific)
            npu_stats = self.read_intel_npu_stats()
            return npu_stats['utilization_percent']
        except Exception as e:
            st.warning(f"NPU monitoring unavailable: {e}")
            return 0.0
    
    async def get_real_time_metrics(self) -> Dict:
        """Get all hardware metrics for UI display"""
        return {
            'npu_utilization': await self.get_npu_utilization(),
            'gpu_utilization': self.get_gpu_utilization(),
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(interval=0.1),
            'disk_io': psutil.disk_io_counters()._asdict(),
            'network_io': psutil.net_io_counters()._asdict()
        }
```

### **9.2 Trading Performance Analytics**

#### **9.2.1 Strategy Performance Tracker**
```python
class StrategyPerformanceTracker:
    """Track and analyze trading strategy performance"""
    
    def __init__(self):
        self.trades = []
        self.strategies = {}
        self.benchmarks = {}
    
    def record_trade(self, trade: TradeRecord):
        """Record completed trade for analysis"""
        self.trades.append(trade)
        
        # Update strategy metrics
        strategy_name = trade.strategy
        if strategy_name not in self.strategies:
            self.strategies[strategy_name] = StrategyMetrics()
        
        self.strategies[strategy_name].add_trade(trade)
    
    def calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return {}
        
        returns = [trade.pnl_percent for trade in self.trades]
        
        return {
            'total_pnl': sum(trade.pnl for trade in self.trades),
            'total_return_percent': self.calculate_total_return(),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
            'max_drawdown': self.calculate_max_drawdown(),
            'win_rate': len([t for t in self.trades if t.pnl > 0]) / len(self.trades),
            'avg_win': self.calculate_avg_win(),
            'avg_loss': self.calculate_avg_loss(),
            'profit_factor': self.calculate_profit_factor()
        }
```

---
