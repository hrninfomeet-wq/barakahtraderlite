# 🔧 Troubleshooting Guide

**Quick Solutions**: Common issues and their fixes to prevent time waste during development.

---

## 🚨 **CRITICAL ISSUES**

### **Virtual Environment Not Active**
```bash
# SYMPTOM: ModuleNotFoundError, ImportError
# SOLUTION: Activate virtual environment
venv\Scripts\activate

# VERIFY: Check for (venv) in prompt
echo "Virtual environment should show (venv) prefix"
```

### **Dependencies Not Installed**
```bash
# SYMPTOM: No module named 'numpy', 'pandas', etc.
# SOLUTION: Install dependencies
pip install -r backend/requirements.txt

# VERIFY: Test critical imports
python -c "import numpy, pandas; print('Dependencies OK')"
```

### **Import Path Errors**
```bash
# SYMPTOM: No module named 'backend', 'models', 'services'
# SOLUTION: Use correct import paths
from backend.services.module import Class  # ✅ CORRECT
from services.module import Class          # ❌ WRONG

# VERIFY: Test import paths
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine"
```

---

## 🔍 **COMMON ERROR PATTERNS**

### **Pydantic Configuration Errors**
```python
# SYMPTOM: "Config" and "model_config" cannot be used together
# SOLUTION: Use only model_config in Pydantic v2
class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    # Remove any class Config: declarations

# VERIFY: Model instantiation works
model = Model(**data)
```

### **FastAPI Dependency Errors**
```python
# SYMPTOM: cannot import name 'get_current_user'
# SOLUTION: Add placeholder function
def get_current_user() -> str:
    """Placeholder for authentication"""
    return "default_user"

# VERIFY: Import works
from backend.core.security import get_current_user
```

### **Test Import Errors**
```python
# SYMPTOM: ModuleNotFoundError in tests
# SOLUTION: Use backend. prefix in imports
from backend.services.paper_trading import PaperTradingEngine  # ✅ CORRECT
from services.paper_trading import PaperTradingEngine          # ❌ WRONG

# VERIFY: Test runs successfully
python -m pytest backend/tests/unit/test_paper_trading.py -v
```

---

## 🛠️ **QUICK FIXES**

### **Environment Reset**
```bash
# Complete environment reset
cd C:\Users\haroo\OneDrive\Documents\My Projects\barakahtraderlite
venv\Scripts\activate
pip install -r backend/requirements.txt --force-reinstall
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Reset Complete')"
```

### **Import Path Fix**
```bash
# Find all files with incorrect imports
grep -r "from models\." backend/
grep -r "from services\." backend/
grep -r "from core\." backend/

# Fix pattern: Replace with backend. prefix
# from models.trading → from backend.models.trading
# from services.module → from backend.services.module
# from core.module → from backend.core.module
```

### **Test Suite Reset**
```bash
# Clear test cache and run fresh
python -m pytest backend/tests/ --cache-clear -v
```

---

## 🔍 **DEBUGGING COMMANDS**

### **Environment Debugging**
```bash
# Check virtual environment
echo $VIRTUAL_ENV
which python
python --version

# Check installed packages
pip list | grep -E "(numpy|pandas|fastapi|pydantic)"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### **Import Debugging**
```bash
# Test specific imports
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Paper Trading OK')"
python -c "import sys; sys.path.insert(0, '.'); from backend.models.trading import Order; print('Trading Models OK')"
python -c "import sys; sys.path.insert(0, '.'); from backend.core.security import get_current_user; print('Security OK')"
```

### **Project Structure Debugging**
```bash
# Check project structure
ls -la backend/
ls -la backend/services/
ls -la backend/models/
ls -la backend/core/

# Check for __init__.py files
find backend/ -name "__init__.py"
```

---

## 📋 **VALIDATION SCRIPTS**

### **Quick Health Check**
```python
#!/usr/bin/env python3
"""Quick System Health Check"""
import sys

def check_environment():
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
        from backend.core.security import get_current_user
        return True
    except Exception:
        return False

def main():
    print("🔍 Quick Health Check...")
    
    if not check_environment():
        print("❌ Virtual environment not active")
        return False
    
    if not check_dependencies():
        print("❌ Dependencies missing")
        return False
    
    if not check_imports():
        print("❌ Import issues")
        return False
    
    print("✅ System healthy!")
    return True

if __name__ == "__main__":
    main()
```

### **Comprehensive Validation**
```python
#!/usr/bin/env python3
"""Comprehensive System Validation"""
import sys

def test_all_components():
    """Test all critical components"""
    sys.path.insert(0, '.')
    
    tests = [
        ("NumPy", lambda: __import__('numpy')),
        ("Pandas", lambda: __import__('pandas')),
        ("FastAPI", lambda: __import__('fastapi')),
        ("Paper Trading", lambda: __import__('backend.services.paper_trading')),
        ("Trading Models", lambda: __import__('backend.models.trading')),
        ("Security", lambda: __import__('backend.core.security')),
    ]
    
    results = []
    for name, test in tests:
        try:
            test()
            results.append((name, True, "OK"))
        except Exception as e:
            results.append((name, False, str(e)))
    
    return results

def main():
    print("🔍 Comprehensive Validation...")
    results = test_all_components()
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
    
    print(f"\n📊 Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        return True
    else:
        print("⚠️ Issues found - check above")
        return False

if __name__ == "__main__":
    main()
```

---

## 🚨 **EMERGENCY PROCEDURES**

### **Complete System Reset**
```bash
# 1. Deactivate and reactivate venv
deactivate
venv\Scripts\activate

# 2. Reinstall all dependencies
pip install -r backend/requirements.txt --force-reinstall

# 3. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 4. Run validation
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Reset Complete')"
```

### **Import Path Mass Fix**
```bash
# Fix all import paths in one go
find backend/ -name "*.py" -exec sed -i 's/from models\./from backend.models./g' {} \;
find backend/ -name "*.py" -exec sed -i 's/from services\./from backend.services./g' {} \;
find backend/ -name "*.py" -exec sed -i 's/from core\./from backend.core./g' {} \;

# Verify fixes
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Mass Fix Complete')"
```

### **Test Suite Recovery**
```bash
# Clear all test artifacts
rm -rf .pytest_cache/
rm -rf backend/tests/__pycache__/
rm -rf backend/tests/*/__pycache__/

# Run tests with fresh cache
python -m pytest backend/tests/ --cache-clear -v
```

---

## 📊 **PREVENTION STRATEGIES**

### **Daily Maintenance**
```bash
# Run this daily to prevent issues
venv\Scripts\activate
pip install -r backend/requirements.txt
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Daily Check OK')"
```

### **Pre-Development Checklist**
```bash
# Run this before every development session
1. venv\Scripts\activate
2. pip install -r backend/requirements.txt
3. python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine"
4. git status
5. echo "Ready for development!"
```

### **Weekly Deep Clean**
```bash
# Run this weekly for system health
venv\Scripts\activate
pip install -r backend/requirements.txt --upgrade
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Weekly Clean OK')"
```

---

## 🎯 **QUICK REFERENCE**

### **Most Common Issues**
1. **Virtual environment not active** → `venv\Scripts\activate`
2. **Dependencies missing** → `pip install -r backend/requirements.txt`
3. **Import path errors** → Use `backend.` prefix
4. **Pydantic config conflicts** → Use only `model_config`
5. **Test import errors** → Fix import paths in test files

### **Emergency Commands**
```bash
# Environment issues
venv\Scripts\activate && pip install -r backend/requirements.txt

# Import issues
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine"

# Test issues
python -m pytest backend/tests/ --cache-clear -v

# Git issues
git status && git add . && git commit -m "WIP: Fix issues"
```

### **Success Indicators**
- ✅ Virtual environment active (venv) in prompt
- ✅ Dependencies installed (numpy, pandas, fastapi, pydantic)
- ✅ Imports working (backend.services.paper_trading)
- ✅ Tests running (pytest completes successfully)
- ✅ System validation passes (all components OK)

---

**⚠️ REMEMBER**: These solutions prevent the mistakes that cost 45 minutes and 2000 tokens. **Use this guide proactively, not reactively.**

*This troubleshooting guide ensures quick resolution of common issues and prevents time waste during development.*

