# **7.1 System Monitoring Architecture**

```python
class SystemMonitor:
    """Comprehensive system monitoring and alerting"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.performance_tracker = PerformanceTracker()
        
    async def monitor_system_health(self):
        """Continuous system health monitoring"""
        while True:
            health_metrics = await self.collect_health_metrics()
            
            # Check critical metrics
            for metric_name, value in health_metrics.items():
                threshold = self.get_threshold(metric_name)
                if self.exceeds_threshold(value, threshold):
                    await self.alert_manager.send_alert(
                        metric_name, value, threshold
                    )
            
            # Store metrics for historical analysis
            await self.metrics_collector.store_metrics(health_metrics)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def collect_health_metrics(self) -> Dict[str, float]:
        """Collect comprehensive system health metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'npu_utilization': await self.get_npu_utilization(),
            'gpu_utilization': await self.get_gpu_utilization(),
            'api_response_times': await self.measure_api_response_times(),
            'database_performance': await self.measure_db_performance(),
            'cache_hit_ratio': await self.get_cache_hit_ratio(),
            'active_connections': await self.count_active_connections(),
            'error_rate': await self.calculate_error_rate(),
            # Rate Limiting Dashboard Metrics (Story 1.2)
            'rate_limit_analytics': await self.get_rate_limit_analytics(),
            'load_balancing_insights': await self.get_load_balancing_insights(),
            'optimization_suggestions': await self.get_optimization_suggestions()
        }
    
    async def get_rate_limit_analytics(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting analytics for dashboard"""
        from backend.services.multi_api_manager import MultiAPIManager
        
        # This would be injected via dependency injection in real implementation
        api_manager = MultiAPIManager(config={}, audit_logger=None)
        
        return await api_manager.get_rate_limit_analytics()
    
    async def get_load_balancing_insights(self) -> Dict[str, Any]:
        """Get load balancing performance insights for dashboard"""
        from backend.services.multi_api_manager import MultiAPIManager
        
        api_manager = MultiAPIManager(config={}, audit_logger=None)
        
        return await api_manager.get_load_balancing_insights()
    
    async def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions for dashboard"""
        from backend.services.multi_api_manager import MultiAPIManager
        
        api_manager = MultiAPIManager(config={}, audit_logger=None)
        
        return await api_manager.get_optimization_suggestions()

class AlertManager:
    """Intelligent alerting system"""
    
    def __init__(self):
        self.alert_channels = {
            'console': ConsoleAlerts(),
            'desktop': DesktopNotifications(),
            'email': EmailAlerts(),  # Optional
            'sms': SMSAlerts()       # Optional
        }
        
    async def send_alert(self, metric: str, value: float, threshold: float):
        """Send alerts through configured channels"""
        alert_message = self.format_alert_message(metric, value, threshold)
        
        # Determine alert severity
        severity = self.calculate_severity(metric, value, threshold)
        
        # Send through appropriate channels
        for channel_name, channel in self.alert_channels.items():
            if await self.should_use_channel(channel_name, severity):
                await channel.send_alert(alert_message, severity)
```
