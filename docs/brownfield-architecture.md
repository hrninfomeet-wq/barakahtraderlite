# Barakah Trader Lite - Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the Barakah Trader Lite codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on enhancements and next phase development.

### Document Scope

**Focused on areas relevant to: Enhanced AI-Powered Personal Trading Engine with Multi-API Integration, Paper Trading, and Educational Features**

### Change Log

| Date   | Version | Description                 | Author    |
| ------ | ------- | --------------------------- | --------- |
| 2025-01-21 | 1.0     | Initial brownfield analysis | BMad Master Agent |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Main Entry**: `backend/main.py` (unified FastAPI backend)
- **Frontend Entry**: `app/page.tsx` (Next.js home page)
- **Trading Interface**: `app/quotes/page.tsx` (main trading UI)
- **Configuration**: `env.local` (API keys, secrets - not committed)
- **Backend Dependencies**: `backend/requirements.txt`
- **Frontend Dependencies**: `package.json`

### Enhancement Impact Areas

Based on PRD requirements, these areas will be affected:
- Multi-API integration (currently single Upstox implementation)
- Paper trading engine (basic implementation exists)
- Educational F&O system (not implemented)
- Advanced strategy engine (not implemented)
- Real-time Greeks calculator (not implemented)

## High Level Architecture

### Technical Summary

**Current State**: Basic Next.js frontend with FastAPI backend, single Upstox API integration, paper trading simulation, and live/demo data toggle functionality.

**Architecture Type**: Simple monolithic backend with React frontend
**Development Status**: MVP with core authentication and paper trading working
**Security Model**: Paper trading enforced, live trading disabled

### Actual Tech Stack

| Category  | Technology | Version | Notes                      |
| --------- | ---------- | ------- | -------------------------- |
| Frontend  | Next.js    | 15.5.3  | React 19.1.0, TypeScript   |
| Backend   | FastAPI    | 0.100.0 | Python 3.11+, async       |
| Database  | SQLite     | N/A     | Local file-based storage   |
| API Client| httpx      | 0.24.0  | Async HTTP client          |
| Auth      | OAuth 2.0  | N/A     | Upstox API integration     |
| Security  | Cryptography| 40.0.0 | Key encryption             |

### Repository Structure Reality Check

- Type: Monorepo with clear separation
- Package Manager: npm (frontend), pip (backend)
- Notable: Dual package management, unified deployment

## Source Tree and Module Organization

### Project Structure (Actual)

```text
barakahtraderlite/
├── app/                      # Next.js frontend
│   ├── quotes/              # Trading interface page
│   ├── layout.tsx           # App layout
│   └── page.tsx             # Home page
├── backend/                 # FastAPI backend
│   ├── main.py              # Unified backend entry (325 lines)
│   ├── services/            # Business logic modules
│   ├── models/              # Data models
│   ├── core/                # Core utilities
│   ├── api/                 # API route modules
│   └── tests/               # Backend tests
├── docs/                    # Documentation
├── public/                  # Static assets
└── env.local               # Environment variables (not committed)
```

### Key Modules and Their Purpose

- **Backend Main**: `backend/main.py` - Single file with all API endpoints (325 lines)
- **Trading Interface**: `app/quotes/page.tsx` - Complete trading UI with Upstox auth
- **Authentication**: Upstox OAuth 2.0 flow with popup window handling
- **Paper Trading**: Simulated order execution with SQLite storage
- **Market Data**: Live/demo data toggle with Upstox API integration

## Data Models and APIs

### Current API Endpoints

**Authentication Endpoints**:
- `GET /api/v1/auth/upstox/status` - Check connection status
- `GET /api/v1/auth/upstox/login` - Initiate OAuth flow
- `POST /api/v1/auth/upstox/authorize` - Handle OAuth callback
- `GET /api/v1/auth/upstox/access-token-request` - Get access token
- `DELETE /api/v1/auth/upstox/disconnect` - Disconnect Upstox

**Market Data Endpoints**:
- `GET /api/v1/market` - Basic market data
- `POST /api/v1/market-data/batch` - Batch market data with live/demo toggle
- `GET /api/v1/system/config/live-data` - Get live data setting
- `POST /api/v1/system/config/live-data` - Toggle live data mode

**Paper Trading Endpoints**:
- `POST /api/v1/paper/order` - Place paper trade order
- `GET /api/v1/paper/history` - Get trading history

### Data Models

- **Trading History**: Stored in SQLite with order details, timestamps, P&L
- **Market Data**: Real-time quotes with source attribution (live/demo)
- **User State**: Frontend-managed authentication and preferences

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Single File Backend**: All 325 lines of backend logic in one file - needs modularization
2. **Limited API Integration**: Only Upstox implemented, missing FLATTRADE, FYERS, Alice Blue
3. **No Greeks Calculation**: F&O strategies and Greeks calculator not implemented
4. **Basic Paper Trading**: Simple simulation without realistic market impact modeling
5. **No Educational System**: F&O learning modules completely missing
6. **Limited Testing**: Basic test structure exists but minimal coverage

### Workarounds and Gotchas

- **Security Override**: `TRADING_MODE = "PAPER"` hardcoded to prevent live trades
- **Environment Variables**: Must use `env.local` (not committed) for API keys
- **CORS Configuration**: Restricted to `localhost:3000` for security
- **Popup Authentication**: Custom popup window handling for OAuth flow
- **SQLite Database**: File-based storage in `backend/trading_engine.db`

## Integration Points and External Dependencies

### External Services

| Service  | Purpose  | Integration Type | Status                      |
| -------- | -------- | ---------------- | --------------------------- |
| Upstox   | Market Data & Auth | OAuth 2.0 + REST API | ✅ Implemented |
| FLATTRADE | Primary Execution | REST API | ❌ Not implemented |
| FYERS    | Analytics & Charting | REST API + WebSocket | ❌ Not implemented |
| Alice Blue | Backup Execution | REST API | ❌ Not implemented |

### Internal Integration Points

- **Frontend-Backend**: REST API on port 8000, expects specific headers
- **Authentication Flow**: Popup window with `postMessage` communication
- **Database**: SQLite file-based with async operations
- **Environment**: `env.local` file for secrets (not committed to git)

## Development and Deployment

### Local Development Setup

**Current Working Setup**:
1. Backend: `python backend/main.py` (runs on port 8000)
2. Frontend: `npm run dev` (runs on port 3000)
3. Environment: Copy `env.example` to `env.local` and configure API keys

**Known Issues**:
- Python virtual environment must be activated
- Upstox API keys must be valid and properly configured
- CORS restricted to localhost:3000

### Build and Deployment Process

- **Backend**: Direct Python execution (no build step)
- **Frontend**: `npm run build` for production
- **Database**: SQLite file created automatically
- **Environment**: Manual `env.local` configuration required

## Testing Reality

### Current Test Coverage

- **Unit Tests**: Basic structure in `backend/tests/` (minimal coverage)
- **Integration Tests**: Basic API endpoint tests
- **Frontend Tests**: None implemented
- **E2E Tests**: None implemented
- **Manual Testing**: Primary validation method

### Running Tests

```bash
cd backend
pytest                    # Run backend tests
# Frontend tests: Not implemented
```

## Enhancement Impact Analysis

### Files That Will Need Major Modification

Based on PRD requirements, these files need significant changes:

**Backend Modifications**:
- `backend/main.py` - Modularize into separate routers and services
- `backend/services/` - Implement multi-API management, Greeks calculator, strategy engine
- `backend/models/` - Add F&O models, strategy models, educational content models
- `backend/core/` - Add NPU integration, advanced security, audit logging

**Frontend Modifications**:
- `app/quotes/page.tsx` - Add F&O strategy interface, Greeks visualization, educational modules
- `app/` - Create new pages for strategy center, educational system, portfolio management
- `package.json` - Add dependencies for advanced charting, NPU integration

### New Files/Modules Needed

**Backend**:
- `backend/services/multi_api_manager.py` - Multi-API orchestration
- `backend/services/greeks_calculator.py` - Real-time Greeks calculation
- `backend/services/strategy_engine.py` - F&O strategy automation
- `backend/services/educational_system.py` - Learning management
- `backend/models/fno_models.py` - F&O data models
- `backend/api/v1/strategies/` - Strategy-specific endpoints
- `backend/api/v1/education/` - Educational content endpoints

**Frontend**:
- `app/strategies/page.tsx` - F&O strategy interface
- `app/education/page.tsx` - Educational learning center
- `app/portfolio/page.tsx` - Portfolio management
- `components/greeks-calculator.tsx` - Greeks visualization
- `components/strategy-builder.tsx` - Strategy setup interface

### Integration Considerations

- **Multi-API Integration**: Must implement failover and load balancing
- **NPU Integration**: Hardware optimization for pattern recognition
- **Security Enhancement**: Audit logging, advanced authentication
- **Educational Integration**: Seamless connection with trading features
- **Performance Optimization**: Sub-30ms execution requirements

## Current Implementation Status

### ✅ Completed Features

1. **Basic Authentication**: Upstox OAuth 2.0 flow working
2. **Paper Trading**: Basic order simulation with SQLite storage
3. **Live/Demo Data Toggle**: Working market data switching
4. **Frontend Interface**: Functional trading UI with order placement
5. **Security Controls**: Paper trading mode enforcement
6. **Trading History**: Order log with auto-refresh capability

### 🚧 Partially Implemented

1. **Market Data**: Only Upstox integration, missing other APIs
2. **Backend Architecture**: Single file needs modularization
3. **Testing**: Basic structure exists but minimal coverage

### ❌ Not Implemented (PRD Requirements)

1. **Multi-API Integration**: FLATTRADE, FYERS, Alice Blue missing
2. **F&O Strategy Engine**: No options strategies implemented
3. **Greeks Calculator**: No real-time Greeks calculation
4. **Educational System**: No learning modules or tutorials
5. **NPU Integration**: No hardware acceleration
6. **Advanced Portfolio Management**: Basic implementation only
7. **Backtesting Framework**: No historical strategy testing
8. **MCX Commodities**: No commodity trading support
9. **Volatility Analysis**: No IV/HV comparison
10. **Advanced Risk Management**: Basic controls only

## Next Phase Development Priorities

### Phase 1: Multi-API Foundation (Weeks 1-2)
- Implement FLATTRADE, FYERS, Alice Blue API integrations
- Create unified API management system
- Add intelligent load balancing and failover

### Phase 2: F&O Strategy Engine (Weeks 3-4)
- Implement Greeks calculator with NPU acceleration
- Create strategy templates (Iron Condor, Butterfly, etc.)
- Add automated strategy execution and monitoring

### Phase 3: Educational System (Weeks 5-6)
- Build learning management system
- Create interactive tutorials and progress tracking
- Integrate educational content with trading interface

### Phase 4: Advanced Features (Weeks 7-8)
- Implement NPU-accelerated pattern recognition
- Add backtesting framework
- Create advanced portfolio management tools

## Appendix - Useful Commands and Scripts

### Development Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend
npm install
npm run dev

# Testing
cd backend
pytest
```

### Debugging and Troubleshooting

- **Logs**: Check terminal output for backend logs
- **Database**: SQLite file at `backend/trading_engine.db`
- **Environment**: Verify `env.local` has correct API keys
- **CORS Issues**: Ensure frontend runs on localhost:3000
- **API Issues**: Check Upstox API key validity and redirect URI

### Critical Configuration

**Environment Variables Required**:
```bash
UPSTOX_CLIENT_ID=your_api_key
UPSTOX_API_SECRET=your_secret
UPSTOX_ACCESS_TOKEN=your_token
UPSTOX_REDIRECT_URI=http://localhost:8000/api/v1/auth/upstox/callback
```

**Security Settings**:
- Paper trading mode enforced: `TRADING_MODE = "PAPER"`
- CORS restricted to localhost:3000
- All sensitive data in `env.local` (not committed)

---

*This brownfield architecture document reflects the current state of Barakah Trader Lite as of January 21, 2025. It serves as the foundation for next phase development focusing on multi-API integration, F&O strategy implementation, and educational system development.*
