# ✅ Pre-Development Checklist

**MANDATORY**: Complete ALL items before starting ANY development work.

---

## 🚨 **CRITICAL PRE-CHECKS** (5 minutes)

### **Environment Setup**
- [ ] **Navigate to project root**: `cd C:\Users\haroo\OneDrive\Documents\My Projects\barakahtraderlite`
- [ ] **Activate virtual environment**: `venv\Scripts\activate` 
- [ ] **Verify venv active**: Check for `(venv)` in terminal prompt
- [ ] **Install dependencies**: `pip install -r backend/requirements.txt`

### **System Validation**
- [ ] **Test NumPy**: `python -c "import numpy; print('NumPy OK')"`
- [ ] **Test Pandas**: `python -c "import pandas; print('Pandas OK')"`
- [ ] **Test FastAPI**: `python -c "import fastapi; print('FastAPI OK')"`
- [ ] **Test Backend Imports**: `python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('Backend OK')"`

### **Project State Analysis**
- [ ] **Check git status**: `git status`
- [ ] **Review recent changes**: `git log --oneline -5`
- [ ] **Identify current branch**: `git branch`
- [ ] **Check for uncommitted changes**: Ensure clean working directory

---

## 🔍 **ANALYSIS PHASE** (10 minutes)

### **Task Understanding**
- [ ] **Read task requirements completely**
- [ ] **Identify affected files/modules**
- [ ] **Map import dependencies**
- [ ] **Plan execution approach**
- [ ] **Estimate time requirements**

### **Impact Assessment**
- [ ] **List files to be modified**
- [ ] **Check for breaking changes**
- [ ] **Plan testing strategy**
- [ ] **Identify rollback plan**
- [ ] **Document expected outcomes**

### **Risk Evaluation**
- [ ] **Identify potential issues**
- [ ] **Plan mitigation strategies**
- [ ] **Prepare contingency plans**
- [ ] **Set quality gates**
- [ ] **Define success criteria**

---

## 🛠️ **PREPARATION PHASE** (5 minutes)

### **Development Tools**
- [ ] **Create validation script** (if needed)
- [ ] **Set up test environment**
- [ ] **Prepare debugging tools**
- [ ] **Configure logging** (if needed)
- [ ] **Backup critical files** (if needed)

### **Documentation**
- [ ] **Update task documentation**
- [ ] **Create progress tracking**
- [ ] **Set up checkpoint system**
- [ ] **Plan documentation updates**
- [ ] **Prepare completion report**

---

## ⚠️ **MANDATORY VALIDATION** (2 minutes)

### **Final Pre-Check**
```bash
# Run this validation before starting ANY work
python -c "
import sys
sys.path.insert(0, '.')

# Check environment
if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    print('❌ VENV NOT ACTIVE - STOP AND ACTIVATE FIRST!')
    sys.exit(1)

# Check dependencies
try:
    import numpy, pandas, fastapi, pydantic
    print('✅ Dependencies OK')
except ImportError as e:
    print(f'❌ MISSING DEPENDENCIES: {e}')
    sys.exit(1)

# Check imports
try:
    from backend.services.paper_trading import PaperTradingEngine
    from backend.models.trading import Order
    print('✅ Imports OK')
except Exception as e:
    print(f'❌ IMPORT ERROR: {e}')
    sys.exit(1)

print('🎉 READY TO START DEVELOPMENT!')
"
```

---

## 📋 **EXECUTION PHASES**

### **Phase 1: Analysis & Planning**
- [ ] Complete pre-development checklist
- [ ] Analyze current state
- [ ] Plan execution approach
- [ ] Set up validation framework

### **Phase 2: Implementation**
- [ ] Follow planned approach
- [ ] Implement changes systematically
- [ ] Validate each step
- [ ] Document progress

### **Phase 3: Testing & Validation**
- [ ] Run comprehensive tests
- [ ] Validate functionality
- [ ] Check for regressions
- [ ] Verify requirements met

### **Phase 4: Documentation & Cleanup**
- [ ] Update documentation
- [ ] Clean up temporary files
- [ ] Prepare deployment guide
- [ ] Complete final validation

---

## 🚫 **COMMON MISTAKES TO AVOID**

### **Environment Issues**
- ❌ Starting without activating venv
- ❌ Testing before installing dependencies
- ❌ Assuming import paths work
- ❌ Skipping system validation

### **Process Issues**
- ❌ Reactive problem solving
- ❌ No upfront analysis
- ❌ Missing validation checkpoints
- ❌ Poor documentation planning

### **Technical Issues**
- ❌ Not checking project state
- ❌ Ignoring git status
- ❌ Skipping risk assessment
- ❌ No rollback planning

---

## 📊 **SUCCESS METRICS**

### **Time Efficiency**
- ✅ Complete checklist in < 20 minutes
- ✅ No environment-related delays
- ✅ No import path debugging
- ✅ Systematic execution approach

### **Quality Assurance**
- ✅ All validations pass
- ✅ No breaking changes
- ✅ Comprehensive testing
- ✅ Clean documentation

### **Process Compliance**
- ✅ Follow BMAD methodology
- ✅ Proper agent deployment
- ✅ Quality gates respected
- ✅ Complete audit trail

---

## 🎯 **QUICK REFERENCE**

### **Emergency Commands**
```bash
# If environment issues
venv\Scripts\activate
pip install -r backend/requirements.txt

# If import issues
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine"

# If test issues
python -m pytest backend/tests/ -v --tb=short

# If git issues
git status
git add .
git commit -m "WIP: [task description]"
```

### **Validation Commands**
```bash
# Environment check
echo $VIRTUAL_ENV

# Dependency check
pip list | grep -E "(numpy|pandas|fastapi|pydantic)"

# Import check
python -c "import sys; sys.path.insert(0, '.'); from backend.services.paper_trading import PaperTradingEngine; print('OK')"
```

---

**⚠️ CRITICAL**: This checklist prevents the mistakes that cost 45 minutes and 2000 tokens in previous execution. **DO NOT SKIP ANY ITEM.**

*Complete this checklist before every development task to ensure efficient execution.*




