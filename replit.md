# replit.md

## Overview

Barakah Trader Lite is an AI-powered personal trading engine designed for the Indian stock market. The project is currently in MVP phase with a working Next.js frontend (React 19.1.0) and FastAPI backend that supports paper trading simulation. The system integrates with trading APIs (currently Upstox OAuth 2.0) and includes security controls to prevent accidental live trading. The architecture is designed to support multi-API integration across Indian brokers (FLATTRADE, FYERS, Alice Blue) and advanced F&O (Futures & Options) strategies with educational features.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Next.js 15.5.3 with React 19.1.0 and TypeScript
- **Styling**: Tailwind CSS 4 with custom trading interface components
- **Authentication**: OAuth 2.0 popup flow with message passing for broker integration
- **State Management**: React hooks with local state management
- **UI Pattern**: Single-page trading interface with real-time data updates

### Backend Architecture
- **Framework**: FastAPI with async/await support for high-performance API handling
- **Current Structure**: Monolithic single-file backend (325 lines) requiring modularization
- **Security Model**: Paper trading enforcement with AES-256 encryption and JWT tokens
- **API Design**: RESTful endpoints for authentication, market data, and paper trading operations
- **Database**: SQLite with async operations and WAL mode for concurrent access
- **Trading Engine**: Paper trading simulation with order history and P&L tracking

### Data Storage Solutions
- **Primary Database**: SQLite with async operations for order history and user data
- **Session Management**: In-memory session handling with secure token storage
- **Cache Strategy**: Redis planned for market data caching (not yet implemented)
- **Data Models**: Pydantic v2 models with strict type validation

### Authentication and Authorization
- **OAuth Integration**: Upstox OAuth 2.0 with popup-based authentication flow
- **Security Controls**: Multi-layer security preventing live trading execution
- **Token Management**: AES-256-GCM encrypted token storage with secure environment-based key management
- **API Key Handling**: Environment-based configuration with CREDENTIAL_VAULT_KEY for master encryption
- **Recent Security Upgrade**: Complete migration from Fernet (AES-128) to AES-256-GCM authenticated encryption

### Performance Considerations
- **Target Latency**: Sub-30ms order execution with <50ms UI response times
- **Hardware Optimization**: Designed for Intel NPU (13 TOPS) and GPU (77 TOPS) acceleration
- **Async Operations**: Full async/await implementation throughout the stack
- **Real-time Updates**: Live market data integration with automatic refresh

### Development Workflow Integration
- **BMAD Method**: Structured development using Business-Model-Agile-Development methodology
- **Quality Assurance**: Comprehensive testing strategy with unit, integration, and E2E tests
- **Documentation**: Extensive architectural documentation and development guides
- **Agent-Based Development**: AI agent system for different development roles (PM, Dev, QA, etc.)

## External Dependencies

### Trading APIs and Brokers
- **Upstox API**: Primary integration for OAuth authentication and market data (currently implemented)
- **FLATTRADE API**: Planned for order execution and portfolio management
- **FYERS API**: Planned for advanced charting and analytics
- **Alice Blue API**: Planned as backup data source and redundancy

### Core Python Dependencies
- **FastAPI**: Web framework for high-performance API development
- **Uvicorn**: ASGI server with standard extensions for production deployment
- **Pydantic**: Data validation and settings management using Python type annotations
- **SQLAlchemy**: Database ORM with async support for SQLite operations
- **cryptography**: Encryption and security utilities for sensitive data handling
- **httpx/aiohttp**: Async HTTP clients for external API integration

### Frontend Dependencies
- **Next.js**: React framework with App Router for modern web development
- **React**: UI library with latest features (19.1.0)
- **TypeScript**: Type safety and enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development

### Development and Testing Tools
- **pytest**: Testing framework with async support for comprehensive test coverage
- **python-dotenv**: Environment variable management for configuration
- **loguru**: Structured logging with rotation and performance monitoring

### External Services
- **Google Gemini Pro**: AI/ML integration for trading strategy analysis (planned)
- **Market Data Providers**: Real-time and historical data feeds from Indian exchanges
- **Windows Credential Manager**: Secure storage for API keys and sensitive configuration

### Planned Integrations
- **Redis**: Caching layer for market data and session management
- **Intel NPU/GPU Libraries**: Hardware acceleration for AI model inference
- **Backtrader**: Backtesting framework for strategy validation
- **TA-Lib**: Technical analysis library for indicator calculations

## Recent Changes

### Security System Upgrade (September 2025)
- **COMPLETED**: Successfully upgraded CredentialVault from Fernet (AES-128) to AES-256-GCM encryption
- **COMPLETED**: Implemented secure environment-variable-based master key management via CREDENTIAL_VAULT_KEY
- **COMPLETED**: Added robust key format handling supporting base64 and hex encoded 32-byte keys
- **COMPLETED**: Verified complete token persistence across backend restarts with proper expiry handling
- **COMPLETED**: Resolved keyrings.alt dependency for Replit environment compatibility
- **COMPLETED**: All security requirements now met with authenticated encryption and secure key management