"""
Unit tests for CredentialVault and security components
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.trading import APIProvider, EncryptedCredentials
from core.security import (
    CredentialVault, KeyManager, TOTPManager, SecurityManager, SecurityException
)


class TestKeyManager:
    """Test KeyManager functionality"""

    @pytest.mark.asyncio
    async def test_get_or_create_master_key_new_key(self):
        """Test creating new master key"""
        with patch('keyring.get_password', return_value=None), \
             patch('keyring.set_password') as mock_set:

            key_manager = KeyManager()
            key = await key_manager.get_or_create_master_key()

            assert key is not None
            assert len(key) == 44  # Fernet key length
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_master_key_existing_key(self):
        """Test retrieving existing master key"""
        existing_key = "test_key_1234567890123456789012345678901234567890"

        with patch('keyring.get_password', return_value=existing_key):
            key_manager = KeyManager()
            key = await key_manager.get_or_create_master_key()

            assert key == existing_key.encode()


class TestCredentialVault:
    """Test CredentialVault functionality"""

    @pytest.fixture
    def vault(self):
        """Create CredentialVault instance for testing"""
        return CredentialVault()

    @pytest.mark.asyncio
    async def test_initialize(self, vault):
        """Test vault initialization"""
        # Generate a proper 32-byte key for testing
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()

        with patch.object(vault.key_manager, 'get_or_create_master_key', return_value=test_key):
            await vault.initialize()
            assert vault.cipher is not None

    @pytest.mark.asyncio
    async def test_validate_credentials_flattrade(self, vault):
        """Test credential validation for FLATTRADE"""
        valid_creds = {"api_key": "test_key", "api_secret": "test_secret"}

        # Should not raise exception
        vault._validate_credentials(APIProvider.FLATTRADE, valid_creds)

    @pytest.mark.asyncio
    async def test_validate_credentials_missing_fields(self, vault):
        """Test credential validation with missing fields"""
        invalid_creds = {"api_key": "test_key"}  # Missing api_secret

        with pytest.raises(SecurityException, match="Missing required credential fields"):
            vault._validate_credentials(APIProvider.FLATTRADE, invalid_creds)

    @pytest.mark.asyncio
    async def test_store_api_credentials(self, vault):
        """Test storing API credentials"""
        credentials = {"api_key": "test_key", "api_secret": "test_secret"}

        with patch.object(vault, 'initialize'), \
             patch('keyring.set_password') as mock_set, \
             patch.object(vault, '_validate_credentials'):

            vault.cipher = Mock()
            vault.cipher.encrypt.return_value = b'encrypted_data'

            result = await vault.store_api_credentials(APIProvider.FLATTRADE, credentials)

            assert result is True
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_api_credentials(self, vault):
        """Test retrieving API credentials"""
        credentials = {"api_key": "test_key", "api_secret": "test_secret"}

        with patch('keyring.get_password', return_value='encrypted_data'), \
             patch.object(vault, 'initialize'):

            vault.cipher = Mock()
            vault.cipher.decrypt.return_value = json.dumps(credentials).encode()

            result = await vault.retrieve_api_credentials(APIProvider.FLATTRADE)

            assert result == credentials

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_credentials(self, vault):
        """Test retrieving non-existent credentials"""
        with patch('keyring.get_password', return_value=None), \
             patch.object(vault, 'initialize'):

            result = await vault.retrieve_api_credentials(APIProvider.FLATTRADE)

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_api_credentials(self, vault):
        """Test deleting API credentials"""
        with patch('keyring.delete_password') as mock_delete:
            result = await vault.delete_api_credentials(APIProvider.FLATTRADE)

            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_stored_providers(self, vault):
        """Test listing stored providers"""
        with patch('keyring.get_password') as mock_get:
            mock_get.side_effect = lambda service, key: "data" if key == "api_flattrade" else None

            providers = await vault.list_stored_providers()

            assert APIProvider.FLATTRADE in providers


class TestTOTPManager:
    """Test TOTP functionality"""

    @pytest.fixture
    def vault(self):
        """Create mock vault for testing"""
        return Mock()

    @pytest.fixture
    def totp_manager(self, vault):
        """Create TOTPManager instance"""
        return TOTPManager(vault)

    def test_generate_totp_code(self, totp_manager):
        """Test TOTP code generation"""
        secret_key = "JBSWY3DPEHPK3PXP"

        code = totp_manager.generate_totp_code(secret_key)

        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_totp_code_valid(self, totp_manager):
        """Test TOTP code verification with valid code"""
        secret_key = "JBSWY3DPEHPK3PXP"
        code = totp_manager.generate_totp_code(secret_key)

        result = totp_manager.verify_totp_code(secret_key, code)

        assert result is True

    def test_verify_totp_code_invalid(self, totp_manager):
        """Test TOTP code verification with invalid code"""
        secret_key = "JBSWY3DPEHPK3PXP"
        invalid_code = "123456"

        result = totp_manager.verify_totp_code(secret_key, invalid_code)

        assert result is False

    def test_get_totp_uri(self, totp_manager):
        """Test TOTP URI generation"""
        secret_key = "JBSWY3DPEHPK3PXP"
        account_name = "test_user"

        uri = totp_manager.get_totp_uri(secret_key, account_name)

        assert uri is not None
        assert "otpauth://totp" in uri
        assert account_name in uri


class TestSecurityManager:
    """Test SecurityManager functionality"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test security manager initialization"""
        with patch('core.security.CredentialVault') as mock_vault_class:
            mock_vault = AsyncMock()
            mock_vault.initialize.return_value = None
            mock_vault_class.return_value = mock_vault

            security_manager = SecurityManager()
            await security_manager.initialize()

            mock_vault.initialize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
