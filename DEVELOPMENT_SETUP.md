# 🛠️ Development Environment Setup Guide

**CRITICAL**: Follow this guide BEFORE starting ANY development work to prevent time waste and token loss.

---

## 🚨 **MANDATORY PRE-DEVELOPMENT CHECKLIST**

### **Step 1: Environment Activation** ⚠️ **CRITICAL**
```bash
# ALWAYS activate virtual environment FIRST
cd C:\Users\haroo\OneDrive\Documents\My Projects\barakahtraderlite
venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
echo "Virtual environment activated"
```

### **Step 2: Dependency Verification** ⚠️ **CRITICAL**
```bash
# Install/verify all dependencies BEFORE any testing
pip install -r backend/requirements.txt

# Verify critical dependencies
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
```

### **Step 3: Import Path Validation** ⚠️ **CRITICAL**
```bash
# Test critical imports to catch path issues early
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('✅ Paper Trading OK')"
python -c "import sys; sys.path.insert(0, '.'); from backend.models.trading import Order; print('✅ Trading Models OK')"
python -c "import sys; sys.path.insert(0, '.'); from backend.core.security import get_current_user; print('✅ Security OK')"
```

### **Step 4: System Health Check** ⚠️ **CRITICAL**
```bash
# Run comprehensive validation
python -c "
import sys; sys.path.insert(0, '.')
try:
    from backend.services.simulation_accuracy_framework import SimulationConfig
    from backend.services.paper_trading import VirtualPortfolio
    from backend.models.trading import TradingMode
    print('🎉 ALL SYSTEMS OPERATIONAL')
except Exception as e:
    print(f'❌ SYSTEM ERROR: {e}')
    sys.exit(1)
"
```

---

## 🔧 **ENVIRONMENT REQUIREMENTS**

### **Python Version**
- **Required**: Python 3.12.0
- **Virtual Environment**: `venv/` (project-local)
- **Activation**: `venv\Scripts\activate`

### **Critical Dependencies**
```
✅ numpy>=1.24.0          # Data analysis & simulation
✅ pandas>=2.0.0           # Data processing
✅ fastapi>=0.116.1        # API framework
✅ pydantic>=2.11.9        # Data validation
✅ pytest>=8.4.2          # Testing framework
✅ loguru                  # Logging
✅ asyncio                 # Async operations
```

### **Project Structure**
```
barakahtraderlite/
├── venv/                  # Virtual environment (ALWAYS activate)
├── backend/               # Backend code
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   ├── api/               # API endpoints
│   ├── core/              # Core utilities
│   └── tests/             # Test suites
└── docs/                  # Documentation
```

---

## 🚀 **QUICK START COMMANDS**

### **For Any Development Task:**
```bash
# 1. Navigate to project
cd C:\Users\haroo\OneDrive\Documents\My Projects\barakahtraderlite

# 2. Activate environment
venv\Scripts\activate

# 3. Verify dependencies
pip install -r backend/requirements.txt

# 4. Test critical imports
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Ready!')"

# 5. Start development work
```

### **For Testing:**
```bash
# Ensure environment is active
venv\Scripts\activate

# Run tests from project root
python -m pytest backend/tests/ -v --tb=short

# Run specific test file
python -m pytest backend/tests/unit/test_paper_trading.py -v
```

### **For API Development:**
```bash
# Ensure environment is active
venv\Scripts\activate

# Start FastAPI server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## ⚠️ **COMMON MISTAKES TO AVOID**

### **❌ DON'T DO THIS:**
1. **Start coding without activating venv** → Import errors
2. **Test imports before installing dependencies** → False failures  
3. **Assume import paths work** → Multiple fix rounds
4. **Fix issues reactively** → Inefficient execution
5. **Skip upfront validation** → Time waste

### **✅ ALWAYS DO THIS:**
1. **Activate venv FIRST** → Clean environment
2. **Install dependencies BEFORE testing** → No false failures
3. **Validate imports upfront** → Catch issues early
4. **Plan systematically** → Efficient execution
5. **Create validation scripts** → Comprehensive testing

---

## 🔍 **TROUBLESHOOTING**

### **Import Errors**
```bash
# Check if venv is active
echo $VIRTUAL_ENV  # Should show venv path

# Reinstall dependencies
pip install -r backend/requirements.txt

# Test import paths
python -c "import sys; print(sys.path)"
```

### **Module Not Found**
```bash
# Check project structure
ls -la backend/

# Verify import paths use 'backend.' prefix
grep -r "from backend\." backend/
```

### **Dependency Issues**
```bash
# Update pip
python -m pip install --upgrade pip

# Reinstall all dependencies
pip install -r backend/requirements.txt --force-reinstall
```

---

## 📋 **VALIDATION SCRIPT**

Create this script and run it before any development:

```python
#!/usr/bin/env python3
"""Pre-Development Validation Script"""
import sys
import subprocess

def check_venv():
    """Check if virtual environment is active"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_dependencies():
    """Check critical dependencies"""
    try:
        import numpy, pandas, fastapi, pydantic
        return True
    except ImportError:
        return False

def check_imports():
    """Check critical imports"""
    try:
        sys.path.insert(0, '.')
        from backend.services.paper_trading import PaperTradingEngine
        from backend.models.trading import Order
        return True
    except Exception:
        return False

def main():
    print("🔍 Pre-Development Validation...")
    
    if not check_venv():
        print("❌ Virtual environment not active!")
        print("Run: venv\\Scripts\\activate")
        return False
    
    if not check_dependencies():
        print("❌ Dependencies missing!")
        print("Run: pip install -r backend/requirements.txt")
        return False
    
    if not check_imports():
        print("❌ Import paths broken!")
        print("Check import statements")
        return False
    
    print("✅ Environment ready for development!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

**⚠️ REMEMBER: Environment setup is CRITICAL. Skip this at your own peril!**

*This guide prevents the mistakes that cost 45 minutes and 2000 tokens in previous execution.*

