# **Enhanced AI-Powered Trading Engine: Development Environment Setup Guide**

*Version 1.0 - Complete Setup Instructions*  
*Date: September 14, 2025*  
*Optimized for Yoga Pro 7 14IAH10*

---

## **Executive Summary**

This guide provides comprehensive instructions for setting up the complete development environment for the Enhanced AI-Powered Personal Trading Engine on the Yoga Pro 7 14IAH10. The setup optimizes for Intel NPU, GPU acceleration, and 32GB RAM utilization while maintaining development efficiency and debugging capabilities.

---

## **1. Hardware Optimization Setup**

### **1.1 Windows 11 Configuration**

```powershell
# Enable Developer Mode
Settings > Update & Security > For developers > Developer mode

# Enable Windows Subsystem for Linux (Optional)
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Configure Power Management for Performance
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# Enable High Performance GPU Scheduling
# Settings > System > Display > Graphics settings > Hardware-accelerated GPU scheduling

# Configure Virtual Memory (32GB RAM optimization)
# System > Advanced system settings > Performance Settings > Advanced > Virtual memory
# Set to 16GB minimum, 32GB maximum
```

### **1.2 Intel NPU & GPU Drivers**

```bash
# Download and install Intel NPU drivers
# Visit: https://www.intel.com/content/www/us/en/support/articles/000005520/processors.html

# Install Intel Graphics Driver (latest)
# Visit: https://www.intel.com/content/www/us/en/support/detect.html

# Verify NPU availability
Device Manager > System devices > Intel(R) Neural Processing Unit

# Verify GPU capabilities
dxdiag > Display tab > Intel Iris Xe Graphics
```

---

## **2. Python Development Environment**

### **2.1 Python Installation & Configuration**

```bash
# Install Python 3.11+ (Official release)
# Download from: https://www.python.org/downloads/

# Verify installation
python --version  # Should be 3.11+
pip --version

# Install pipenv for virtual environment management
pip install pipenv

# Create project directory
mkdir C:\TradingEngine
cd C:\TradingEngine

# Initialize virtual environment
pipenv install python==3.11
pipenv shell

# Upgrade pip and install wheel
python -m pip install --upgrade pip
pip install wheel setuptools
```

### **2.2 Core Dependencies Installation**

```bash
# Install core frameworks
pip install fastapi[all]==0.104.1
pip install streamlit==1.28.1
pip install plotly==5.17.0
pip install pandas==2.1.3
pip install numpy==1.25.2
pip install scipy==1.11.4

# Install async and HTTP libraries
pip install aiohttp==3.9.1
pip install asyncio-mqtt==0.13.0
pip install websockets==12.0

# Install database and caching
pip install sqlite3  # Built-in with Python
pip install redis==5.0.1
pip install sqlalchemy==2.0.23

# Install AI/ML frameworks
pip install tensorflow==2.15.0
pip install torch==2.1.1
pip install scikit-learn==1.3.2
pip install openvino==2023.2.0

# Install trading and financial libraries
pip install yfinance==0.2.22
pip install ta-lib==0.4.28
pip install backtrader==1.9.78.123

# Install utility libraries
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0
pip install pytest==7.4.3
pip install black==23.11.0
pip install flake8==6.1.0
```

### **2.3 Intel NPU Optimization Setup**

```bash
# Install Intel OpenVINO toolkit for NPU
pip install openvino-dev[tensorflow2,pytorch]==2023.2.0

# Install Intel Neural Compressor (optional optimization)
pip install neural-compressor==2.4

# Install Intel Extension for TensorFlow
pip install intel-extension-for-tensorflow==2.14.0

# Verify NPU availability in Python
python -c "
import openvino as ov
core = ov.Core()
devices = core.available_devices
print('Available devices:', devices)
if 'NPU' in devices:
    print('NPU is available and ready!')
else:
    print('NPU not detected, using CPU fallback')
"
```

---

## **3. Database Setup**

### **3.1 SQLite Configuration**

```python
# Create database setup script: setup_database.py
import sqlite3
import os
from pathlib import Path

def setup_database():
    """Initialize SQLite database with optimized settings"""
    
    # Create data directory
    data_dir = Path("C:/TradingEngine/data")
    data_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = data_dir / "trading_engine.db"
    
    # Connect with optimized settings
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        timeout=30.0
    )
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap
    
    # Create tables
    create_tables(conn)
    
    conn.close()
    print(f"Database initialized at: {db_path}")

def create_tables(conn):
    """Create all required database tables"""
    
    # Execute SQL from system architecture
    sql_script = """
    -- Core trading tables
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id VARCHAR(50) UNIQUE NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        exchange VARCHAR(10) NOT NULL,
        transaction_type VARCHAR(4) NOT NULL,
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
    
    CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
    CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
    CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
    
    -- Add all other tables from system architecture...
    """
    
    conn.executescript(sql_script)
    conn.commit()

if __name__ == "__main__":
    setup_database()
```

### **3.2 Redis Setup (Optional High-Performance Caching)**

```bash
# Download Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# Install Redis (if using)
# Extract to C:\Tools\Redis\

# Create Redis configuration file: redis.conf
# maxmemory 4gb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10
# save 60 10000

# Start Redis server
cd C:\Tools\Redis
redis-server.exe redis.conf

# Test Redis connection
redis-cli ping  # Should return PONG
```

---

## **4. API Integration Setup**

### **4.1 Create API Configuration Framework**

```python
# Create config/api_config.py
from dataclasses import dataclass
from typing import Dict, Optional
import os
from cryptography.fernet import Fernet
import keyring

@dataclass
class APIConfig:
    """API configuration structure"""
    name: str
    base_url: str
    rate_limit_per_second: int
    websocket_url: Optional[str] = None
    websocket_symbol_limit: Optional[int] = None
    timeout: int = 30
    retry_attempts: int = 3

# API Configurations
API_CONFIGS = {
    'flattrade': APIConfig(
        name='FLATTRADE',
        base_url='https://piconnect.flattrade.in/PiConnectTP',
        rate_limit_per_second=100,  # Generous assumption
        timeout=30
    ),
    'fyers': APIConfig(
        name='FYERS',
        base_url='https://api.fyers.in/api/v2',
        rate_limit_per_second=10,
        websocket_url='wss://api.fyers.in/socket/v2',
        websocket_symbol_limit=200,
        timeout=30
    ),
    'upstox': APIConfig(
        name='UPSTOX',
        base_url='https://api.upstox.com/v2',
        rate_limit_per_second=50,
        websocket_url='wss://ws-api.upstox.com/v2',
        websocket_symbol_limit=None,  # Unlimited
        timeout=30
    ),
    'alice_blue': APIConfig(
        name='ALICE_BLUE',
        base_url='https://ant.aliceblueonline.com/rest/AliceBlueAPIService',
        rate_limit_per_second=10,  # Conservative estimate
        timeout=30
    )
}

class SecureAPIManager:
    """Secure API credential management"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        try:
            key = keyring.get_password("ai_trading_engine", "encryption_key")
            if key:
                return key.encode()
        except Exception:
            pass
        
        # Create new key
        key = Fernet.generate_key()
        keyring.set_password("ai_trading_engine", "encryption_key", key.decode())
        return key
    
    def store_credentials(self, api_name: str, credentials: Dict):
        """Store encrypted API credentials"""
        import json
        
        encrypted_data = self.cipher.encrypt(
            json.dumps(credentials).encode()
        )
        
        keyring.set_password(
            "ai_trading_engine",
            f"api_creds_{api_name}",
            encrypted_data.decode()
        )
        print(f"Credentials stored securely for {api_name}")
    
    def get_credentials(self, api_name: str) -> Optional[Dict]:
        """Retrieve and decrypt API credentials"""
        try:
            import json
            
            encrypted_data = keyring.get_password(
                "ai_trading_engine",
                f"api_creds_{api_name}"
            )
            
            if encrypted_data:
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Failed to retrieve credentials for {api_name}: {e}")
        
        return None

# Example usage script
if __name__ == "__main__":
    manager = SecureAPIManager()
    
    # Example: Store FLATTRADE credentials (replace with actual)
    flattrade_creds = {
        "user_id": "your_user_id",
        "password": "your_password",
        "totp_key": "your_totp_secret",
        "api_key": "your_api_key"
    }
    
    manager.store_credentials("flattrade", flattrade_creds)
```

### **4.2 API Testing Framework**

```python
# Create tests/test_api_integration.py
import asyncio
import aiohttp
import pytest
from config.api_config import API_CONFIGS, SecureAPIManager

class APIHealthChecker:
    """Test API connectivity and health"""
    
    def __init__(self):
        self.credential_manager = SecureAPIManager()
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_api_connectivity(self, api_name: str) -> Dict:
        """Test basic API connectivity"""
        config = API_CONFIGS[api_name]
        
        try:
            async with self.session.get(
                config.base_url,
                timeout=aiohttp.ClientTimeout(total=config.timeout)
            ) as response:
                return {
                    'api': api_name,
                    'status': 'connected',
                    'response_code': response.status,
                    'latency_ms': response.headers.get('X-Response-Time', 'unknown')
                }
        except Exception as e:
            return {
                'api': api_name,
                'status': 'failed',
                'error': str(e),
                'latency_ms': 'timeout'
            }
    
    async def test_all_apis(self) -> Dict:
        """Test connectivity to all configured APIs"""
        tasks = [
            self.test_api_connectivity(api_name)
            for api_name in API_CONFIGS.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

# Test runner
async def main():
    async with APIHealthChecker() as checker:
        results = await checker.test_all_apis()
        
        print("API Connectivity Test Results:")
        print("=" * 50)
        
        for result in results['results']:
            if isinstance(result, dict):
                status_icon = "✅" if result['status'] == 'connected' else "❌"
                print(f"{status_icon} {result['api']}: {result['status']}")
                if 'latency_ms' in result:
                    print(f"   Latency: {result['latency_ms']}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
            else:
                print(f"❌ Error: {result}")

if __name__ == "__main__":
    import datetime
    asyncio.run(main())
```

---

## **5. Development Tools Setup**

### **5.1 VS Code Configuration**

```json
// Create .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.pylintEnabled": false,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/node_modules": true,
        ".venv": false
    },
    "python.analysis.autoImportCompletions": true,
    "python.analysis.typeCheckingMode": "basic"
}
```

```json
// Create .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Backend",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/main.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Streamlit Frontend",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "${workspaceFolder}/frontend/app.py",
                "--server.port=8501"
            ],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Database Setup",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/setup_database.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### **5.2 Required VS Code Extensions**

```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.flake8
code --install-extension ms-python.black-formatter
code --install-extension ms-vscode.vscode-json
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-python.debugpy
code --install-extension ms-vscode.test-adapter-converter
```

---

## **6. Project Structure Setup**

### **6.1 Create Directory Structure**

```bash
# Create complete project structure
mkdir -p C:/TradingEngine/{
backend/{api,core,models,services,utils,tests},
frontend/{components,pages,utils,assets},
data/{databases,cache,logs,models},
config,
scripts,
docs,
tests/{unit,integration,performance},
.venv
}

# Navigate to project directory
cd C:/TradingEngine
```

### **6.2 Initialize Git Repository**

```bash
# Initialize Git repository
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# Cache
.cache/
.pytest_cache/

# Environment variables
.env
.env.local

# API Keys and secrets
config/secrets/
*.key
*.pem

# Data files
data/cache/
data/logs/
data/temp/

# OS
.DS_Store
Thumbs.db

# Trading specific
trades/
positions/
backtest_results/
EOF

# Initial commit
git add .
git commit -m "Initial project setup with development environment"
```

---

## **7. Performance & Monitoring Setup**

### **7.1 Performance Monitoring Configuration**

```python
# Create monitoring/performance_monitor.py
import psutil
import time
import logging
from dataclasses import dataclass
from typing import Dict, List
import asyncio

@dataclass
class PerformanceMetrics:
    """Performance metrics structure"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    npu_utilization: float = 0.0
    gpu_utilization: float = 0.0

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitoring = False
        self.logger = logging.getLogger(__name__)
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous performance monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries (about 8 hours at 30s intervals)
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                # Log warnings for high usage
                await self.check_performance_thresholds(metrics)
                
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            npu_utilization=await self.get_npu_utilization(),
            gpu_utilization=await self.get_gpu_utilization()
        )
    
    async def get_npu_utilization(self) -> float:
        """Get NPU utilization (platform-specific implementation needed)"""
        try:
            # Placeholder for Intel NPU monitoring
            # This would require platform-specific implementation
            return 0.0
        except Exception:
            return 0.0
    
    async def get_gpu_utilization(self) -> float:
        """Get GPU utilization"""
        try:
            # For Intel integrated graphics
            # This would require platform-specific implementation
            return 0.0
        except Exception:
            return 0.0
    
    async def check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check performance thresholds and log warnings"""
        if metrics.cpu_percent > 80:
            self.logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > 70:
            self.logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_usage_percent > 90:
            self.logger.warning(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
    
    def get_latest_metrics(self) -> PerformanceMetrics:
        """Get the latest performance metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_metrics(self, last_n: int = 10) -> Dict:
        """Get average metrics for last N entries"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-last_n:]
        
        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'avg_npu_utilization': sum(m.npu_utilization for m in recent_metrics) / len(recent_metrics),
            'avg_gpu_utilization': sum(m.gpu_utilization for m in recent_metrics) / len(recent_metrics)
        }
```

### **7.2 Logging Configuration**

```python
# Create utils/logging_config.py
import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / 'trading_engine.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / 'trading_engine_errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Performance log handler
    perf_handler = logging.handlers.RotatingFileHandler(
        log_path / 'performance.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(logging.Formatter(
        '%(asctime)s - PERF - %(message)s'
    ))
    
    # Create performance logger
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False
    
    logging.info("Logging system initialized")
```

---

## **8. Testing Framework Setup**

### **8.1 Testing Configuration**

```ini
# Create pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    -q 
    --strict-markers
    --disable-warnings
    --cov=backend
    --cov=frontend
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=90
testpaths = 
    tests
python_files = 
    test_*.py
    *_test.py
python_classes = 
    Test*
python_functions = 
    test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
    performance: marks tests as performance tests
```

### **8.2 Testing Utilities**

```python
# Create tests/conftest.py
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_api_response():
    """Mock API response for testing"""
    return {
        "status": "success",
        "data": {
            "symbol": "NIFTY",
            "price": 25840.50,
            "timestamp": "2025-09-14T10:30:00Z"
        }
    }

@pytest.fixture
def mock_trading_engine():
    """Mock trading engine for testing"""
    engine = MagicMock()
    engine.place_order = AsyncMock(return_value={"order_id": "TEST_001", "status": "PLACED"})
    engine.get_positions = AsyncMock(return_value=[])
    engine.get_portfolio = AsyncMock(return_value={"total_value": 100000})
    return engine

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "NIFTY": {
            "last_price": 25840.50,
            "change": 127.30,
            "change_percent": 0.49,
            "volume": 1234567,
            "timestamp": "2025-09-14T10:30:00Z"
        }
    }
```

---

## **9. Environment Validation Script**

```python
# Create scripts/validate_environment.py
import sys
import subprocess
import importlib
import platform
from pathlib import Path

class EnvironmentValidator:
    """Validate complete development environment setup"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def check_python_version(self):
        """Check Python version compatibility"""
        self.total_checks += 1
        version = sys.version_info
        
        if version.major == 3 and version.minor >= 11:
            print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
            self.success_count += 1
        else:
            error_msg = f"❌ Python version {version.major}.{version.minor} is not supported. Requires 3.11+"
            print(error_msg)
            self.errors.append(error_msg)
    
    def check_system_requirements(self):
        """Check system requirements"""
        self.total_checks += 1
        
        # Check Windows version
        system = platform.system()
        if system != "Windows":
            self.warnings.append(f"⚠️ System {system} - optimized for Windows 11")
        else:
            print(f"✅ Operating System: {system} {platform.release()}")
            self.success_count += 1
    
    def check_required_packages(self):
        """Check if all required packages are installed"""
        required_packages = [
            'fastapi', 'streamlit', 'plotly', 'pandas', 'numpy',
            'aiohttp', 'sqlalchemy', 'redis', 'tensorflow',
            'openvino', 'yfinance', 'pytest'
        ]
        
        for package in required_packages:
            self.total_checks += 1
            try:
                importlib.import_module(package)
                print(f"✅ Package: {package}")
                self.success_count += 1
            except ImportError:
                error_msg = f"❌ Missing package: {package}"
                print(error_msg)
                self.errors.append(error_msg)
    
    def check_directories(self):
        """Check if required directories exist"""
        required_dirs = [
            'backend', 'frontend', 'data', 'config',
            'tests', 'logs', 'scripts'
        ]
        
        for dir_name in required_dirs:
            self.total_checks += 1
            dir_path = Path(dir_name)
            
            if dir_path.exists():
                print(f"✅ Directory: {dir_name}")
                self.success_count += 1
            else:
                error_msg = f"❌ Missing directory: {dir_name}"
                print(error_msg)
                self.errors.append(error_msg)
    
    def check_hardware_capabilities(self):
        """Check hardware capabilities"""
        import psutil
        
        # Memory check
        self.total_checks += 1
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= 16:
            print(f"✅ Memory: {memory_gb:.1f} GB")
            self.success_count += 1
            if memory_gb < 32:
                self.warnings.append(f"⚠️ Memory {memory_gb:.1f}GB - 32GB recommended")
        else:
            error_msg = f"❌ Insufficient memory: {memory_gb:.1f}GB (16GB minimum)"
            print(error_msg)
            self.errors.append(error_msg)
        
        # CPU check
        self.total_checks += 1
        cpu_count = psutil.cpu_count()
        if cpu_count >= 8:
            print(f"✅ CPU cores: {cpu_count}")
            self.success_count += 1
        else:
            warning_msg = f"⚠️ CPU cores: {cpu_count} (8+ recommended)"
            print(warning_msg)
            self.warnings.append(warning_msg)
    
    def check_npu_availability(self):
        """Check NPU availability"""
        self.total_checks += 1
        
        try:
            import openvino as ov
            core = ov.Core()
            devices = core.available_devices
            
            if 'NPU' in devices:
                print("✅ Intel NPU: Available")
                self.success_count += 1
            else:
                warning_msg = "⚠️ Intel NPU: Not detected (CPU fallback will be used)"
                print(warning_msg)
                self.warnings.append(warning_msg)
                
        except Exception as e:
            warning_msg = f"⚠️ NPU check failed: {e}"
            print(warning_msg)
            self.warnings.append(warning_msg)
    
    def run_validation(self):
        """Run complete environment validation"""
        print("Environment Validation Report")
        print("=" * 50)
        
        self.check_python_version()
        self.check_system_requirements()
        self.check_required_packages()
        self.check_directories()
        self.check_hardware_capabilities()
        self.check_npu_availability()
        
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {self.success_count}/{self.total_checks}")
        
        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   {error}")
            return False
        else:
            print("\n🎉 Environment validation successful!")
            print("Ready to start development!")
            return True

if __name__ == "__main__":
    validator = EnvironmentValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)
```

---

## **10. Quick Start Commands**

```bash
# Clone the complete setup (once environment is ready)
cd C:/TradingEngine

# Activate virtual environment
pipenv shell

# Validate environment
python scripts/validate_environment.py

# Setup database
python scripts/setup_database.py

# Test API connectivity
python tests/test_api_integration.py

# Start development servers (in separate terminals)

# Terminal 1: Backend
python backend/main.py

# Terminal 2: Frontend
streamlit run frontend/app.py --server.port=8501

# Terminal 3: Redis (if using)
redis-server config/redis.conf

# Run tests
pytest tests/ -v

# Check code quality
black backend/ frontend/
flake8 backend/ frontend/
```

---

## **11. Troubleshooting Guide**

### **11.1 Common Issues**

**NPU Not Detected:**
```bash
# Install Intel NPU drivers from Intel website
# Verify in Device Manager
# Restart after driver installation
# Run OpenVINO benchmark tool: benchmark_app --help
```

**Redis Connection Issues:**
```bash
# Check if Redis is running: redis-cli ping
# Verify port 6379 is not blocked
# Check Redis logs in installation directory
# Restart Redis service
```

**API Authentication Failures:**
```bash
# Verify credentials are stored: python -c "from config.api_config import SecureAPIManager; print(SecureAPIManager().get_credentials('flattrade'))"
# Check API key permissions on broker platforms
# Verify TOTP codes are generating correctly
# Test with simple API call first
```

**Performance Issues:**
```bash
# Monitor system resources: python monitoring/performance_monitor.py
# Check for memory leaks: python -m memory_profiler script.py
# Profile code execution: python -m cProfile script.py
# Optimize database queries: PRAGMA optimize
```

---

**Environment setup complete! Ready for Phase 1 development! 🚀**