"""
Database Schema and Audit Logging System
SEBI-compliant audit logging with 7-year retention
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.sql import func  # Unused
# import aiosqlite  # Unused
from loguru import logger

# from models.trading import APIProvider  # Unused

Base = declarative_base()


class AuditLog(Base):
    """SEBI-compliant audit logging table"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(30), nullable=False)  # TRADING/SYSTEM/ERROR/SECURITY
    user_session = Column(String(100))
    api_provider = Column(String(20))
    event_data = Column(Text)  # JSON data
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    checksum = Column(String(64), nullable=False)  # For data integrity

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', timestamp='{self.timestamp}')>"


class APIUsageLog(Base):
    """API usage tracking table"""
    __tablename__ = 'api_usage_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_provider = Column(String(20), nullable=False)
    endpoint = Column(String(100), nullable=False)
    request_type = Column(String(10), nullable=False)  # GET/POST/PUT/DELETE
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    rate_limit_remaining = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class MarketDataCache(Base):
    """Market data cache table"""
    __tablename__ = 'market_data_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    data_type = Column(String(20), nullable=False)  # PRICE/VOLUME/ORDERBOOK/etc
    data_json = Column(Text, nullable=False)  # JSON serialized market data
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_time = Column(DateTime, nullable=False, index=True)
    source = Column(String(20), nullable=False)  # FYERS/UPSTOX/etc
    confidence_score = Column(Float, default=1.0)

    def __repr__(self):
        return f"<MarketDataCache(symbol='{self.symbol}', timestamp='{self.timestamp}')>"


class MarketDataValidation(Base):
    """Market data validation results table"""
    __tablename__ = 'market_data_validation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    validation_tier = Column(String(20), nullable=False)  # FAST/CROSS_SOURCE/DEEP
    validation_status = Column(String(20), nullable=False)  # validated/discrepancy_detected/failed
    confidence_score = Column(Float, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    discrepancy_details = Column(Text)  # JSON details of discrepancies
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<MarketDataValidation(symbol='{self.symbol}', status='{self.validation_status}')>"


class WebSocketConnectionLog(Base):
    """WebSocket connection monitoring table"""
    __tablename__ = 'websocket_connection_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)  # CONNECTED/DISCONNECTED/RECONNECTING
    subscribed_symbols_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_heartbeat = Column(DateTime)
    connected_at = Column(DateTime)
    disconnected_at = Column(DateTime)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<WebSocketConnectionLog(connection_id='{self.connection_id}', status='{self.status}')>"


class CredentialAccessLog(Base):
    """Credential access tracking for security auditing"""
    __tablename__ = 'credential_access_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(20), nullable=False)
    operation = Column(String(20), nullable=False)  # STORE/RETRIEVE/DELETE
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CredentialAccessLog(id={self.id}, provider='{self.provider}', operation='{self.operation}')>"


class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, database_url: str = "sqlite:///./trading_engine.db"):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """Initialize database engine and create tables"""
        try:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()


class AuditLogger:
    """SEBI-compliant audit logging system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.retention_days = 2555  # 7 years retention

    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for data integrity"""
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""

    async def log_event(self, event_type: str, event_category: str, event_data: Dict[str, Any],
                       user_session: Optional[str] = None, api_provider: Optional[str] = None,
                       ip_address: Optional[str] = None) -> bool:
        """Log event with SEBI compliance"""
        try:
            checksum = self.calculate_checksum(event_data)

            session = self.db_manager.get_session()

            audit_log = AuditLog(
                event_type=event_type,
                event_category=event_category,
                event_data=json.dumps(event_data, default=str),
                user_session=user_session,
                api_provider=api_provider,
                ip_address=ip_address,
                timestamp=datetime.now(),
                checksum=checksum
            )

            session.add(audit_log)
            session.commit()
            session.close()

            logger.info(f"Logged audit event: {event_type} - {event_category}")
            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    async def log_trade_event(self, event_type: str, trade_data: Dict[str, Any],
                            user_session: Optional[str] = None, api_provider: Optional[str] = None) -> bool:
        """Log trading events for regulatory compliance"""
        return await self.log_event(
            event_type=event_type,
            event_category="TRADING",
            event_data=trade_data,
            user_session=user_session,
            api_provider=api_provider
        )

    async def log_security_event(self, event_type: str, security_data: Dict[str, Any],
                                ip_address: Optional[str] = None) -> bool:
        """Log security events"""
        return await self.log_event(
            event_type=event_type,
            event_category="SECURITY",
            event_data=security_data,
            ip_address=ip_address
        )

    async def log_system_event(self, event_type: str, system_data: Dict[str, Any]) -> bool:
        """Log system events"""
        return await self.log_event(
            event_type=event_type,
            event_category="SYSTEM",
            event_data=system_data
        )

    async def log_api_usage(self, api_provider: str, endpoint: str, request_type: str,
                           response_time_ms: Optional[int] = None, status_code: Optional[int] = None,
                           rate_limit_remaining: Optional[int] = None) -> bool:
        """Log API usage for monitoring and compliance"""
        try:
            session = self.db_manager.get_session()

            api_log = APIUsageLog(
                api_provider=api_provider,
                endpoint=endpoint,
                request_type=request_type,
                response_time_ms=response_time_ms,
                status_code=status_code,
                rate_limit_remaining=rate_limit_remaining,
                timestamp=datetime.now()
            )

            session.add(api_log)
            session.commit()
            session.close()

            return True

        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
            return False

    async def log_credential_access(self, provider: str, operation: str, success: bool,
                                  error_message: Optional[str] = None,
                                  ip_address: Optional[str] = None,
                                  user_agent: Optional[str] = None) -> bool:
        """Log credential access for security auditing"""
        try:
            session = self.db_manager.get_session()

            cred_log = CredentialAccessLog(
                provider=provider,
                operation=operation,
                success=success,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now()
            )

            session.add(cred_log)
            session.commit()
            session.close()

            return True

        except Exception as e:
            logger.error(f"Failed to log credential access: {e}")
            return False

    async def cleanup_old_logs(self) -> int:
        """Clean up logs older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            session = self.db_manager.get_session()

            # Count logs to be deleted
            count = session.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).count()

            # Delete old logs
            session.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
            session.query(APIUsageLog).filter(APIUsageLog.timestamp < cutoff_date).delete()
            session.query(CredentialAccessLog).filter(CredentialAccessLog.timestamp < cutoff_date).delete()

            session.commit()
            session.close()

            logger.info(f"Cleaned up {count} old audit logs")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0

ENGINE = create_engine('sqlite:///:memory:')  # Mock in-memory DB for testing
SessionLocal = sessionmaker(bind=ENGINE)

def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
