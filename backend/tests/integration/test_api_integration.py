"""
Integration tests for API components
"""
import sys
import os
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.database import DatabaseManager, AuditLogger
from core.security import SecurityManager, CredentialVault
from services.multi_api_manager import MultiAPIManager
from models.trading import APIProvider


class TestAPIIntegration:
    """Integration tests for API components"""
    
    @pytest_asyncio.fixture
    async def db_manager(self):
        """Create database manager for testing"""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.initialize()
        return db_manager
    
    @pytest_asyncio.fixture
    async def audit_logger(self, db_manager):
        """Create audit logger for testing"""
        return AuditLogger(db_manager)
    
    @pytest_asyncio.fixture
    async def security_manager(self):
        """Create security manager for testing"""
        with patch('keyring.get_password', return_value=None), \
             patch('keyring.set_password'):
            security_manager = SecurityManager()
            await security_manager.initialize()
            return security_manager
    
    @pytest.mark.asyncio
    async def test_credential_storage_and_retrieval(self, security_manager):
        """Test end-to-end credential storage and retrieval"""
        credentials = {
            "api_key": "test_api_key_123",
            "api_secret": "test_api_secret_456"
        }
        
        # Store credentials
        success = await security_manager.credential_vault.store_api_credentials(
            APIProvider.FLATTRADE, credentials
        )
        assert success is True
        
        # Retrieve credentials
        retrieved_creds = await security_manager.credential_vault.retrieve_api_credentials(
            APIProvider.FLATTRADE
        )
        
        assert retrieved_creds == credentials
    
    @pytest.mark.asyncio
    async def test_audit_logging_integration(self, audit_logger):
        """Test audit logging functionality"""
        # Log a security event
        security_data = {
            "event": "credential_access",
            "provider": "flattrade",
            "success": True
        }
        
        success = await audit_logger.log_security_event("CREDENTIAL_ACCESS", security_data)
        assert success is True
        
        # Log API usage
        api_success = await audit_logger.log_api_usage(
            api_provider="flattrade",
            endpoint="/portfolio",
            request_type="GET",
            response_time_ms=150,
            status_code=200
        )
        assert api_success is True
    
    @pytest.mark.asyncio
    async def test_multi_api_manager_integration(self, audit_logger):
        """Test MultiAPIManager integration"""
        config = {
            "enabled_apis": ["flattrade", "fyers"],
            "routing_rules": {
                "get_portfolio": ["flattrade", "fyers"]
            },
            "fallback_chain": ["flattrade", "fyers"],
            "flattrade": {
                "rate_limits": {"requests_per_second": 10}
            },
            "fyers": {
                "rate_limits": {"requests_per_second": 10}
            }
        }
        
        with patch('backend.services.multi_api_manager.FlattradeAPI'), \
             patch('backend.services.multi_api_manager.FyersAPI'):
            
            manager = MultiAPIManager(config, audit_logger)
            await manager.initialize_apis()
            
            # Test health monitoring
            health_status = await manager.get_health_status()
            assert isinstance(health_status, dict)
            
            # Test shutdown
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_totp_integration(self, security_manager):
        """Test TOTP integration"""
        secret_key = "JBSWY3DPEHPK3PXP"
        
        # Generate TOTP code
        code = security_manager.totp_manager.generate_totp_code(secret_key)
        assert code is not None
        assert len(code) == 6
        
        # Verify TOTP code
        is_valid = security_manager.totp_manager.verify_totp_code(secret_key, code)
        assert is_valid is True
        
        # Test invalid code
        is_invalid = security_manager.totp_manager.verify_totp_code(secret_key, "123456")
        assert is_invalid is False
    
    @pytest.mark.asyncio
    async def test_database_cleanup(self, db_manager, audit_logger):
        """Test database cleanup functionality"""
        # Log some test events
        for i in range(5):
            await audit_logger.log_system_event("TEST_EVENT", {"test_id": i})
        
        # Test cleanup (would normally clean up old logs)
        # In this test, we just verify the function runs without error
        cleaned_count = await audit_logger.cleanup_old_logs()
        assert isinstance(cleaned_count, int)
    
    @pytest.mark.asyncio
    async def test_end_to_end_credential_flow(self, security_manager, audit_logger):
        """Test complete credential management flow"""
        # Test credential storage
        credentials = {
            "api_key": "integration_test_key",
            "api_secret": "integration_test_secret",
            "totp_secret": "JBSWY3DPEHPK3PXP"
        }
        
        # Store credentials
        store_success = await security_manager.credential_vault.store_api_credentials(
            APIProvider.UPSTOX, credentials
        )
        assert store_success is True
        
        # Log credential access
        access_success = await audit_logger.log_credential_access(
            provider="upstox",
            operation="STORE",
            success=True,
            ip_address="127.0.0.1"
        )
        assert access_success is True
        
        # Retrieve credentials
        retrieved_creds = await security_manager.credential_vault.retrieve_api_credentials(
            APIProvider.UPSTOX
        )
        assert retrieved_creds == credentials
        
        # Test TOTP with retrieved secret
        totp_secret = retrieved_creds.get("totp_secret")
        if totp_secret:
            code = security_manager.totp_manager.generate_totp_code(totp_secret)
            is_valid = security_manager.totp_manager.verify_totp_code(totp_secret, code)
            assert is_valid is True
        
        # List stored providers
        providers = await security_manager.credential_vault.list_stored_providers()
        assert APIProvider.UPSTOX in providers
        
        # Delete credentials
        delete_success = await security_manager.credential_vault.delete_api_credentials(
            APIProvider.UPSTOX
        )
        assert delete_success is True
        
        # Verify deletion
        deleted_creds = await security_manager.credential_vault.retrieve_api_credentials(
            APIProvider.UPSTOX
        )
        assert deleted_creds is None


class TestDatabaseIntegration:
    """Test database integration"""
    
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database initialization"""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.initialize()
        
        # Test session creation
        session = db_manager.get_session()
        assert session is not None
        session.close()
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self):
        """Test audit log creation"""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.initialize()
        
        audit_logger = AuditLogger(db_manager)
        
        # Log an event
        success = await audit_logger.log_system_event(
            "TEST_EVENT",
            {"test": "data", "timestamp": datetime.now().isoformat()}
        )
        
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__])
