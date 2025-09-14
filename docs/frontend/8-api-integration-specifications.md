# **8. API Integration Specifications**

### **8.1 Multi-API Abstraction Layer**

#### **8.1.1 Unified API Interface**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class TradingAPIInterface(ABC):
    """Abstract base class for all trading API implementations"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        pass
    
    @abstractmethod
    async def get_portfolio(self) -> Dict:
        pass
    
    @abstractmethod
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict:
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict:
        pass

class UnifiedAPIManager:
    """Manages multiple API connections with intelligent routing"""
    
    def __init__(self):
        self.apis = {
            'flattrade': FlattradeAPI(),
            'fyers': FyersAPI(),
            'upstox': UpstoxAPI(),
            'alice_blue': AliceBlueAPI()
        }
        self.routing_rules = {
            'orders': ['flattrade', 'upstox', 'alice_blue'],
            'market_data': ['fyers', 'upstox'],
            'portfolio': ['fyers', 'flattrade']
        }
    
    async def execute_with_fallback(self, operation: str, **kwargs):
        """Execute operation with automatic API fallback"""
        apis_to_try = self.routing_rules.get(operation, list(self.apis.keys()))
        
        for api_name in apis_to_try:
            api = self.apis[api_name]
            
            if not api.is_available():
                continue
                
            if api.is_rate_limited():
                continue
            
            try:
                result = await getattr(api, operation)(**kwargs)
                self.log_successful_operation(api_name, operation)
                return result
            except Exception as e:
                self.log_api_error(api_name, operation, e)
                continue
        
        raise Exception(f"All APIs failed for operation: {operation}")
```

### **8.2 Paper Trading Implementation**

#### **8.2.1 Virtual Execution Engine**
```python
class PaperTradingEngine:
    """Simulates realistic order execution without real money"""
    
    def __init__(self):
        self.virtual_portfolio = {}
        self.virtual_cash = 500000  # ₹5 lakh virtual capital
        self.order_history = []
        self.simulation_parameters = {
            'slippage_factor': 0.001,  # 0.1% slippage
            'latency_simulation': 50,   # 50ms simulated latency
            'partial_fill_probability': 0.1
        }
    
    async def simulate_order_execution(self, order: OrderRequest) -> OrderResponse:
        """Simulate realistic order execution with market impact"""
        
        # Simulate order processing delay
        await asyncio.sleep(
            self.simulation_parameters['latency_simulation'] / 1000
        )
        
        # Get current market price
        market_price = await self.get_current_price(order.symbol)
        
        # Calculate execution price with slippage
        execution_price = self.calculate_execution_price(
            order, market_price
        )
        
        # Check for partial fills
        executed_quantity = self.simulate_partial_fill(order.quantity)
        
        # Update virtual portfolio
        self.update_virtual_portfolio(order, execution_price, executed_quantity)
        
        return OrderResponse(
            order_id=f"PAPER_{len(self.order_history) + 1}",
            status="COMPLETE" if executed_quantity == order.quantity else "PARTIAL",
            executed_price=execution_price,
            executed_quantity=executed_quantity,
            timestamp=datetime.now()
        )
    
    def calculate_execution_price(self, order: OrderRequest, market_price: float) -> float:
        """Calculate realistic execution price with slippage"""
        slippage = market_price * self.simulation_parameters['slippage_factor']
        
        if order.transaction_type == "BUY":
            return market_price + slippage
        else:
            return market_price - slippage
```

---
