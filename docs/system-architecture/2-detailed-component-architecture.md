# **2. Detailed Component Architecture**

## **2.1 Frontend Layer - Streamlit with Custom Components**

### **2.1.1 Frontend Architecture**
```python
# Frontend Architecture Overview
frontend/
├── app.py                      # Main Streamlit application
├── components/                 # Custom Streamlit components
│   ├── chart_component/        # NPU-accelerated charts
│   ├── npu_status/            # Hardware monitoring
│   ├── order_dialog/          # Trading execution dialogs
│   ├── multi_monitor/         # Multi-display support
│   └── touch_handler/         # Touch interaction manager
├── pages/                     # Tab-based navigation
│   ├── dashboard.py           # Main trading dashboard
│   ├── charts.py              # Multi-chart analysis
│   ├── fno_strategy.py        # F&O strategy center
│   ├── btst_intelligence.py   # AI-powered BTST
│   ├── portfolio.py           # Cross-API portfolio
│   └── system.py              # Debug and settings
├── utils/                     # Frontend utilities
│   ├── ui_helpers.py          # Common UI components
│   ├── state_manager.py       # Session state management
│   └── performance_monitor.py # Frontend performance tracking
└── assets/                    # Static assets
    ├── css/                   # Custom styling
    ├── js/                    # JavaScript enhancements
    └── icons/                 # UI icons and images
```

### **2.1.2 Key Frontend Components**

**Multi-Monitor Manager**
```python
class MultiMonitorManager:
    """Manages display detection and layout adaptation"""
    
    def __init__(self):
        self.monitors = self.detect_monitors()
        self.layouts = self.load_layout_configs()
        self.current_layout = "single_monitor"
    
    def detect_monitors(self) -> List[Dict]:
        """Detect connected monitors and capabilities"""
        # Implementation for monitor detection
        pass
    
    def adapt_layout(self, monitor_count: int):
        """Adapt UI layout based on monitor configuration"""
        if monitor_count >= 2:
            self.setup_extended_workspace()
        else:
            self.setup_compact_layout()
    
    def setup_extended_workspace(self):
        """Configure extended workspace for multiple monitors"""
        # Move charts to secondary monitor
        # Keep controls on primary monitor
        pass
```

**NPU Status Component**
```python
class NPUStatusComponent:
    """Real-time hardware monitoring component"""
    
    def render_npu_strip(self):
        """Render hardware status strip"""
        hardware_metrics = self.get_hardware_metrics()
        educational_progress = self.get_educational_progress()
        system_status = self.get_system_status()
        
        return st.container().write(f"""
        🧠NPU:{hardware_metrics['npu']}% 
        📊GPU:{hardware_metrics['gpu']}% 
        💾RAM:{hardware_metrics['ram']}GB 
        | 📚F&O Progress:{educational_progress}% 
        | {'🔴LIVE' if system_status['mode'] == 'live' else '🔵PAPER'}
        |⚡API:{system_status['api_count']}/4
        """)
```

### **2.1.3 Touch Interaction System**
```javascript
// Touch interaction handler for Streamlit components
class TouchInteractionManager {
    constructor() {
        this.gestures = new Map();
        this.touchTargets = new Set();
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        document.addEventListener('touchstart', this.handleTouchStart.bind(this));
        document.addEventListener('touchmove', this.handleTouchMove.bind(this));
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Prevent default zoom on multi-touch
        document.addEventListener('gesturestart', (e) => e.preventDefault());
        document.addEventListener('gesturechange', (e) => e.preventDefault());
    }
    
    registerTouchTarget(element, options) {
        """Register element for touch interaction"""
        this.touchTargets.add({
            element: element,
            minSize: options.minSize || '44px',
            actions: options.actions || {},
            hapticFeedback: options.hapticFeedback || true
        });
    }
}
```

## **2.2 Backend Layer - FastAPI with Async Architecture**

### **2.2.1 Backend Architecture**
```python
# Backend Architecture Overview
backend/
├── main.py                    # FastAPI application entry point
├── core/                      # Core application logic
│   ├── config.py              # Configuration management
│   ├── security.py            # Authentication & authorization
│   ├── database.py            # Database connections
│   └── exceptions.py          # Custom exception handlers
├── api/                       # API route handlers
│   ├── v1/                    # Version 1 API endpoints
│   │   ├── trading.py         # Trading operations
│   │   ├── portfolio.py       # Portfolio management
│   │   ├── market_data.py     # Market data endpoints
│   │   ├── strategies.py      # F&O strategy management
│   │   └── system.py          # System monitoring
│   └── dependencies.py        # Dependency injection
├── services/                  # Business logic services
│   ├── multi_api_manager.py   # Multi-API orchestration
│   ├── trading_engine.py      # Core trading logic
│   ├── risk_manager.py        # Risk management
│   ├── strategy_engine.py     # F&O strategy execution
│   ├── ai_engine.py           # AI/ML processing
│   └── paper_trading.py       # Paper trading engine
├── models/                    # Data models and schemas
│   ├── trading.py             # Trading-related models
│   ├── portfolio.py           # Portfolio models
│   ├── market_data.py         # Market data models
│   └── user.py                # User and session models
├── utils/                     # Utility functions
│   ├── logger.py              # Logging configuration
│   ├── cache.py               # Redis cache manager
│   ├── validators.py          # Data validation
│   └── helpers.py             # Common helper functions
└── tests/                     # Test suites
    ├── unit/                  # Unit tests
    ├── integration/           # Integration tests
    └── load/                  # Load testing
```

### **2.2.2 Multi-API Manager - Core Architecture**

**API Abstraction Layer**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from datetime import datetime

class TradingAPIInterface(ABC):
    """Abstract base class for all trading API implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(config.get('rate_limit', 10))
        self.health_status = "unknown"
        self.last_health_check = None
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with the API provider"""
        pass
    
    @abstractmethod
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place a trading order"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_portfolio(self) -> Portfolio:
        """Get portfolio information"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get real-time market data"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        pass
    
    async def health_check(self) -> bool:
        """Perform health check on API"""
        try:
            # Implement basic connectivity test
            result = await self.get_portfolio()
            self.health_status = "healthy"
            self.last_health_check = datetime.now()
            return True
        except Exception as e:
            self.health_status = f"unhealthy: {str(e)}"
            self.last_health_check = datetime.now()
            return False
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get current rate limit information"""
        return self.rate_limiter.get_status()

class MultiAPIManager:
    """Manages multiple trading API connections with intelligent routing"""
    
    def __init__(self, config: Dict):
        self.apis: Dict[str, TradingAPIInterface] = {}
        self.routing_rules = config.get('routing_rules', {})
        self.fallback_chain = config.get('fallback_chain', [])
        self.health_monitor = HealthMonitor(self.apis)
        self.load_balancer = LoadBalancer(self.apis)
        
    async def initialize_apis(self):
        """Initialize all configured API connections"""
        api_configs = {
            'flattrade': FlattradeAPI,
            'fyers': FyersAPI,
            'upstox': UpstoxAPI,
            'alice_blue': AliceBlueAPI
        }
        
        for api_name, api_class in api_configs.items():
            if api_name in self.config.get('enabled_apis', []):
                self.apis[api_name] = api_class(self.config[api_name])
                await self.apis[api_name].authenticate(
                    self.config[api_name]['credentials']
                )
    
    async def execute_with_fallback(self, operation: str, **kwargs) -> Any:
        """Execute operation with automatic API fallback"""
        preferred_apis = self.routing_rules.get(operation, self.fallback_chain)
        
        for api_name in preferred_apis:
            api = self.apis.get(api_name)
            if not api or not await api.health_check():
                continue
                
            if api.rate_limiter.is_rate_limited():
                continue
            
            try:
                result = await getattr(api, operation)(**kwargs)
                await self.log_successful_operation(api_name, operation, result)
                return result
            except Exception as e:
                await self.log_api_error(api_name, operation, e)
                continue
        
        raise APIException(f"All APIs failed for operation: {operation}")
```

**Intelligent Load Balancer**
```python
class LoadBalancer:
    """Intelligent load balancing across multiple APIs"""
    
    def __init__(self, apis: Dict[str, TradingAPIInterface]):
        self.apis = apis
        self.performance_metrics = {}
        self.current_loads = {}
        
    async def select_best_api(self, operation: str) -> str:
        """Select the best API for a given operation"""
        available_apis = [
            name for name, api in self.apis.items() 
            if api.health_status == "healthy" and not api.rate_limiter.is_rate_limited()
        ]
        
        if not available_apis:
            raise NoAvailableAPIException("No healthy APIs available")
        
        # Score APIs based on performance and current load
        scores = {}
        for api_name in available_apis:
            performance_score = self.get_performance_score(api_name, operation)
            load_score = self.get_load_score(api_name)
            scores[api_name] = (performance_score + load_score) / 2
        
        # Return API with highest score
        return max(scores, key=scores.get)
    
    def get_performance_score(self, api_name: str, operation: str) -> float:
        """Calculate performance score for API and operation"""
        metrics = self.performance_metrics.get(api_name, {}).get(operation, {})
        
        avg_latency = metrics.get('avg_latency', 1000)  # ms
        success_rate = metrics.get('success_rate', 0.5)  # 0-1
        
        # Lower latency and higher success rate = higher score
        latency_score = max(0, (1000 - avg_latency) / 1000)
        return (latency_score + success_rate) / 2
    
    def get_load_score(self, api_name: str) -> float:
        """Calculate current load score for API"""
        current_load = self.current_loads.get(api_name, 0)
        rate_limit = self.apis[api_name].get_rate_limits().get('requests_per_second', 10)
        
        # Lower current load = higher score
        return max(0, (rate_limit - current_load) / rate_limit)
```

### **2.2.3 Trading Engine Architecture**

**Core Trading Engine**
```python
class TradingEngine:
    """Core trading execution engine"""
    
    def __init__(self, multi_api_manager: MultiAPIManager, 
                 risk_manager: RiskManager, audit_logger: AuditLogger):
        self.multi_api_manager = multi_api_manager
        self.risk_manager = risk_manager
        self.audit_logger = audit_logger
        self.paper_trading_mode = False
        
    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place a trading order with full risk management"""
        
        # Risk validation
        risk_check = await self.risk_manager.validate_order(order_request)
        if not risk_check.approved:
            raise RiskException(risk_check.reason)
        
        # Route to paper trading if in paper mode
        if self.paper_trading_mode:
            return await self.paper_trading_engine.execute_order(order_request)
        
        # Execute via best available API
        try:
            api_name = await self.multi_api_manager.load_balancer.select_best_api('place_order')
            order_response = await self.multi_api_manager.execute_with_fallback(
                'place_order', order=order_request
            )
            
            # Log successful order
            await self.audit_logger.log_trade_event('ORDER_PLACED', {
                'order_id': order_response.order_id,
                'symbol': order_request.symbol,
                'quantity': order_request.quantity,
                'price': order_request.price,
                'api_used': api_name,
                'timestamp': datetime.now()
            })
            
            return order_response
            
        except Exception as e:
            await self.audit_logger.log_trade_event('ORDER_FAILED', {
                'symbol': order_request.symbol,
                'error': str(e),
                'timestamp': datetime.now()
            })
            raise TradingException(f"Order execution failed: {str(e)}")
    
    async def get_unified_portfolio(self) -> UnifiedPortfolio:
        """Get consolidated portfolio across all APIs"""
        portfolios = {}
        
        for api_name in self.multi_api_manager.apis.keys():
            try:
                portfolio = await self.multi_api_manager.execute_with_fallback(
                    'get_portfolio', api_name=api_name
                )
                portfolios[api_name] = portfolio
            except Exception as e:
                logger.warning(f"Failed to get portfolio from {api_name}: {e}")
        
        return UnifiedPortfolio.merge(portfolios)
```

**Paper Trading Engine**
```python
class PaperTradingEngine:
    """Realistic paper trading simulation engine"""
    
    def __init__(self):
        self.virtual_portfolio = {}
        self.virtual_cash = 500000  # ₹5 lakh starting capital
        self.order_history = []
        self.simulation_config = {
            'slippage_factor': 0.001,  # 0.1% slippage
            'latency_ms': 50,          # 50ms simulated latency
            'partial_fill_prob': 0.1   # 10% chance of partial fill
        }
    
    async def execute_order(self, order: OrderRequest) -> OrderResponse:
        """Execute order in paper trading mode with realistic simulation"""
        
        # Simulate processing delay
        await asyncio.sleep(self.simulation_config['latency_ms'] / 1000)
        
        # Get current market price
        market_data = await self.get_current_market_data(order.symbol)
        current_price = market_data.last_price
        
        # Calculate realistic execution price with slippage
        execution_price = self.calculate_execution_price(order, current_price)
        
        # Simulate partial fills
        executed_quantity = self.simulate_partial_fill(order.quantity)
        
        # Update virtual portfolio
        self.update_virtual_portfolio(order, execution_price, executed_quantity)
        
        # Create order response
        order_response = OrderResponse(
            order_id=f"PAPER_{len(self.order_history) + 1}",
            status="COMPLETE" if executed_quantity == order.quantity else "PARTIAL",
            executed_price=execution_price,
            executed_quantity=executed_quantity,
            timestamp=datetime.now(),
            is_paper_trade=True
        )
        
        self.order_history.append(order_response)
        return order_response
    
    def calculate_execution_price(self, order: OrderRequest, market_price: float) -> float:
        """Calculate realistic execution price including slippage"""
        slippage = market_price * self.simulation_config['slippage_factor']
        
        if order.transaction_type == "BUY":
            return market_price + slippage
        else:
            return market_price - slippage
    
    def simulate_partial_fill(self, requested_quantity: int) -> int:
        """Simulate partial fills based on market conditions"""
        if random.random() < self.simulation_config['partial_fill_prob']:
            return int(requested_quantity * random.uniform(0.7, 0.9))
        return requested_quantity
```

## **2.3 AI/ML Engine Architecture**

### **2.3.1 NPU-Accelerated AI Engine**

**Multi-Model AI Architecture**
```python
class AIEngine:
    """Comprehensive AI/ML processing engine"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.npu_processor = NPUProcessor()
        self.gpu_processor = GPUProcessor()
        self.gemini_client = GeminiProClient(config['gemini_api_key'])
        self.local_llm = LocalLLMManager()
        self.pattern_recognizer = PatternRecognizer()
        self.btst_analyzer = BTSTAnalyzer()
        
    async def analyze_market_patterns(self, market_data: Dict) -> List[Pattern]:
        """NPU-accelerated pattern recognition"""
        # Preprocess data for NPU
        processed_data = await self.preprocess_for_npu(market_data)
        
        # Run pattern recognition on NPU
        patterns = await self.npu_processor.recognize_patterns(processed_data)
        
        # Post-process and score patterns
        scored_patterns = []
        for pattern in patterns:
            confidence = await self.calculate_pattern_confidence(pattern)
            if confidence >= 7.0:  # Only high-confidence patterns
                scored_patterns.append(PatternResult(
                    pattern_type=pattern.type,
                    confidence=confidence,
                    entry_price=pattern.entry_price,
                    target_price=pattern.target_price,
                    stop_loss=pattern.stop_loss,
                    timeframe=pattern.timeframe
                ))
        
        return scored_patterns

class NPUProcessor:
    """Intel NPU processing for pattern recognition"""
    
    def __init__(self):
        self.model_cache = {}
        self.initialize_npu()
    
    def initialize_npu(self):
        """Initialize NPU for AI processing"""
        try:
            # Initialize Intel NPU via OpenVINO
            import openvino as ov
            self.core = ov.Core()
            self.available_devices = self.core.available_devices
            
            if 'NPU' in self.available_devices:
                self.device = 'NPU'
                logger.info("NPU device initialized successfully")
            else:
                self.device = 'CPU'  # Fallback to CPU
                logger.warning("NPU not available, falling back to CPU")
                
        except Exception as e:
            logger.error(f"NPU initialization failed: {e}")
            self.device = 'CPU'
    
    async def recognize_patterns(self, data: np.ndarray) -> List[Pattern]:
        """Run pattern recognition on NPU"""
        # Load optimized model for NPU
        model = await self.load_pattern_model()
        
        # Run inference
        results = model(data)
        
        # Convert results to pattern objects
        patterns = self.parse_pattern_results(results)
        return patterns
    
    async def load_pattern_model(self):
        """Load pattern recognition model optimized for NPU"""
        if 'pattern_model' not in self.model_cache:
            # Load pre-trained model optimized for Indian markets
            model_path = "models/indian_market_patterns.xml"
            self.model_cache['pattern_model'] = self.core.compile_model(
                model_path, self.device
            )
        
        return self.model_cache['pattern_model']

class BTSTAnalyzer:
    """AI-powered BTST analysis with strict scoring"""
    
    def __init__(self):
        self.min_confidence = 8.5  # Strict minimum confidence
        self.analysis_factors = [
            'technical_analysis',
            'fii_dii_flows',
            'news_sentiment',
            'volume_analysis',
            'market_regime',
            'options_flow'
        ]
    
    async def analyze_btst_candidates(self, market_data: Dict, 
                                   current_time: datetime) -> List[BTSTRecommendation]:
        """Analyze BTST candidates with strict time and confidence controls"""
        
        # Strict time check - only after 2:15 PM IST
        market_time = current_time.replace(tzinfo=IST_TZ)
        if market_time.hour < 14 or (market_time.hour == 14 and market_time.minute < 15):
            return []  # No recommendations before 2:15 PM
        
        recommendations = []
        
        for symbol in market_data.keys():
            # Multi-factor analysis
            analysis_scores = {}
            
            for factor in self.analysis_factors:
                score = await self.analyze_factor(symbol, factor, market_data[symbol])
                analysis_scores[factor] = score
            
            # Calculate overall confidence
            overall_confidence = self.calculate_overall_confidence(analysis_scores)
            
            # Only recommend if confidence >= 8.5
            if overall_confidence >= self.min_confidence:
                recommendation = BTSTRecommendation(
                    symbol=symbol,
                    confidence=overall_confidence,
                    analysis_breakdown=analysis_scores,
                    entry_price=market_data[symbol]['close'],
                    target_price=self.calculate_target(symbol, market_data[symbol]),
                    stop_loss=self.calculate_stop_loss(symbol, market_data[symbol]),
                    position_size=self.calculate_position_size(symbol, overall_confidence),
                    reasoning=self.generate_reasoning(analysis_scores)
                )
                recommendations.append(recommendation)
        
        # Sort by confidence (highest first)
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        # Zero-force policy: return empty list if no high-confidence trades
        if not recommendations:
            logger.info(f"BTST: No trades meet minimum confidence threshold of {self.min_confidence}")
        
        return recommendations
    
    async def analyze_factor(self, symbol: str, factor: str, data: Dict) -> float:
        """Analyze individual factor for BTST scoring"""
        if factor == 'technical_analysis':
            return await self.analyze_technical_patterns(symbol, data)
        elif factor == 'fii_dii_flows':
            return await self.analyze_institutional_flows(symbol, data)
        elif factor == 'news_sentiment':
            return await self.analyze_news_sentiment(symbol)
        elif factor == 'volume_analysis':
            return await self.analyze_volume_patterns(symbol, data)
        elif factor == 'market_regime':
            return await self.analyze_market_regime(data)
        elif factor == 'options_flow':
            return await self.analyze_options_flow(symbol, data)
        else:
            return 5.0  # Neutral score
    
    def calculate_overall_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate overall confidence from individual factor scores"""
        # Weighted average with higher weight for technical analysis
        weights = {
            'technical_analysis': 0.25,
            'fii_dii_flows': 0.20,
            'news_sentiment': 0.15,
            'volume_analysis': 0.20,
            'market_regime': 0.10,
            'options_flow': 0.10
        }
        
        weighted_sum = sum(scores[factor] * weights[factor] for factor in scores)
        return round(weighted_sum, 1)
```

### **2.3.2 F&O Greeks Calculator**

**NPU-Accelerated Greeks Engine**
```python
class GreeksCalculator:
    """NPU-accelerated Greeks calculation engine"""
    
    def __init__(self):
        self.npu_processor = NPUProcessor()
        self.black_scholes_model = BlackScholesModel()
        self.volatility_model = VolatilityModel()
    
    async def calculate_portfolio_greeks(self, positions: List[Position]) -> PortfolioGreeks:
        """Calculate portfolio-level Greeks using NPU acceleration"""
        
        # Prepare data for batch processing
        options_data = []
        for position in positions:
            if position.instrument_type == 'OPTION':
                option_data = {
                    'symbol': position.symbol,
                    'strike': position.strike_price,
                    'expiry': position.expiry_date,
                    'option_type': position.option_type,
                    'quantity': position.quantity,
                    'spot_price': position.current_price,
                    'iv': await self.get_implied_volatility(position.symbol)
                }
                options_data.append(option_data)
        
        if not options_data:
            return PortfolioGreeks.zero()
        
        # Batch calculate Greeks using NPU
        greeks_results = await self.npu_processor.calculate_greeks_batch(options_data)
        
        # Aggregate portfolio Greeks
        portfolio_delta = sum(result['delta'] * result['quantity'] for result in greeks_results)
        portfolio_gamma = sum(result['gamma'] * result['quantity'] for result in greeks_results)
        portfolio_theta = sum(result['theta'] * result['quantity'] for result in greeks_results)
        portfolio_vega = sum(result['vega'] * result['quantity'] for result in greeks_results)
        portfolio_rho = sum(result['rho'] * result['quantity'] for result in greeks_results)
        
        return PortfolioGreeks(
            delta=portfolio_delta,
            gamma=portfolio_gamma,
            theta=portfolio_theta,
            vega=portfolio_vega,
            rho=portfolio_rho,
            positions=len(options_data),
            last_updated=datetime.now()
        )
    
    async def get_implied_volatility(self, symbol: str) -> float:
        """Get implied volatility for option calculations"""
        # Retrieve from volatility model or market data
        return await self.volatility_model.get_iv(symbol)

class VolatilityModel:
    """Advanced volatility modeling for Indian markets"""
    
    def __init__(self):
        self.cache = {}
        self.models = {
            'garch': GARCHModel(),
            'realized': RealizedVolatilityModel(),
            'implied': ImpliedVolatilityModel()
        }
    
    async def get_volatility_surface(self, symbol: str) -> VolatilitySurface:
        """Generate volatility surface for options chain"""
        options_chain = await self.get_options_chain(symbol)
        
        surface_data = {}
        for expiry in options_chain.expiries:
            for strike in options_chain.strikes:
                iv = await self.calculate_implied_volatility(symbol, strike, expiry)
                surface_data[(strike, expiry)] = iv
        
        return VolatilitySurface(symbol, surface_data)
```

## **2.4 Data Layer Architecture**

### **2.4.1 Database Schema Design**

**SQLite Database Schema**
```sql
-- Core trading tables
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(4) NOT NULL, -- BUY/SELL
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    executed_price DECIMAL(10,2),
    status VARCHAR(20) NOT NULL,
    api_provider VARCHAR(20) NOT NULL,
    strategy VARCHAR(50),
    is_paper_trade BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_strategy ON trades(strategy);

-- Portfolio positions
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL, -- EQUITY/OPTION/FUTURE
    quantity INTEGER NOT NULL,
    average_price DECIMAL(10,2) NOT NULL,
    current_price DECIMAL(10,2),
    unrealized_pnl DECIMAL(12,2),
    api_provider VARCHAR(20) NOT NULL,
    expiry_date DATE,
    strike_price DECIMAL(10,2),
    option_type VARCHAR(4), -- CE/PE
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_expiry ON positions(expiry_date);

-- F&O strategies tracking
CREATE TABLE strategy_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id VARCHAR(50) NOT NULL,
    strategy_type VARCHAR(30) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    legs TEXT NOT NULL, -- JSON array of strategy legs
    entry_date DATE NOT NULL,
    expiry_date DATE,
    status VARCHAR(20) NOT NULL, -- ACTIVE/CLOSED/EXPIRED
    total_premium DECIMAL(10,2),
    current_pnl DECIMAL(12,2),
    max_profit DECIMAL(10,2),
    max_loss DECIMAL(10,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Market data cache
CREATE TABLE market_data_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- PRICE/VOLUME/OI
    data_json TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    expiry_time DATETIME NOT NULL
);

CREATE INDEX idx_market_cache_symbol ON market_data_cache(symbol, timestamp);

-- System audit logs
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30) NOT NULL, -- TRADING/SYSTEM/ERROR
    user_session VARCHAR(100),
    api_provider VARCHAR(20),
    event_data TEXT, -- JSON data
    ip_address VARCHAR(45),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64) -- For data integrity
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);

-- Performance analytics
CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    pnl DECIMAL(12,2) NOT NULL,
    return_percent DECIMAL(8,4),
    holding_period_hours INTEGER,
    risk_adjusted_return DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Educational progress tracking
CREATE TABLE learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name VARCHAR(50) NOT NULL,
    lesson_id VARCHAR(30) NOT NULL,
    completion_status VARCHAR(20) NOT NULL, -- COMPLETED/IN_PROGRESS/NOT_STARTED
    score INTEGER, -- Quiz/assessment score
    time_spent_minutes INTEGER,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
CREATE TABLE api_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_provider VARCHAR(20) NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    request_type VARCHAR(10) NOT NULL, -- GET/POST/PUT/DELETE
    response_time_ms INTEGER,
    status_code INTEGER,
    rate_limit_remaining INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_provider ON api_usage_logs(api_provider, timestamp);
```

### **2.4.2 Cache Management System**

**Redis Cache Architecture**
```python
class CacheManager:
    """Redis-based cache management for high-performance data access"""
    
    def __init__(self, redis_config: Dict):
        self.redis_client = redis.asyncio.Redis(**redis_config)
        self.default_ttl = 300  # 5 minutes default TTL
        self.cache_strategies = {
            'market_data': {'ttl': 1, 'compression': True},      # 1 second for live data
            'portfolio': {'ttl': 30, 'compression': False},      # 30 seconds
            'api_limits': {'ttl': 60, 'compression': False},     # 1 minute
            'patterns': {'ttl': 300, 'compression': True},       # 5 minutes
            'greeks': {'ttl': 5, 'compression': False},          # 5 seconds
        }
    
    async def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """Get data from cache with optional decompression"""
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            
            strategy = self.cache_strategies.get(cache_type, {})
            if strategy.get('compression', False):
                data = self.decompress(data)
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, cache_type: str = 'default', 
                  ttl: Optional[int] = None) -> bool:
        """Set data in cache with optional compression"""
        try:
            strategy = self.cache_strategies.get(cache_type, {})
            ttl = ttl or strategy.get('ttl', self.default_ttl)
            
            data = json.dumps(value)
            if strategy.get('compression', False):
                data = self.compress(data)
            
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = await self.redis_client.keys(pattern)
        if keys:
            await self.redis_client.delete(*keys)
    
    def compress(self, data: str) -> bytes:
        """Compress data for storage efficiency"""
        return gzip.compress(data.encode('utf-8'))
    
    def decompress(self, data: bytes) -> str:
        """Decompress data for retrieval"""
        return gzip.decompress(data).decode('utf-8')

class DataPipeline:
    """High-performance data pipeline with intelligent caching"""
    
    def __init__(self, cache_manager: CacheManager, database: Database):
        self.cache = cache_manager
        self.db = database
        self.websocket_manager = WebSocketManager()
        
    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get real-time market data with intelligent caching"""
        results = {}
        cache_misses = []
        
        # Check cache first
        for symbol in symbols:
            cache_key = f"market_data:{symbol}"
            cached_data = await self.cache.get(cache_key, 'market_data')
            
            if cached_data:
                results[symbol] = MarketData.from_dict(cached_data)
            else:
                cache_misses.append(symbol)
        
        # Fetch missing data from APIs
        if cache_misses:
            fresh_data = await self.fetch_from_apis(cache_misses)
            
            for symbol, data in fresh_data.items():
                results[symbol] = data
                # Cache for future requests
                await self.cache.set(
                    f"market_data:{symbol}", 
                    data.to_dict(), 
                    'market_data'
                )
        
        return results
    
    async def fetch_from_apis(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Fetch data from multiple APIs with load balancing"""
        # Implementation for multi-API data fetching
        pass
```

---
