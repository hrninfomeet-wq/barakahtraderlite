"""
Security Management System
Handles credential storage, encryption, and authentication using AES-256-GCM
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import keyring
import pyotp
from loguru import logger
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user from token - placeholder"""
    # In production, verify token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
    return "test_user"  # Mock user

from models.trading import (
    APIProvider, EncryptedCredentials, TOTPConfig
)


class SecurityException(Exception):
    """Custom security exception"""
    pass


class KeyManager:
    """Manages AES-256 encryption keys with secure environment variable storage"""

    def __init__(self):
        self._master_key = None
        self.service_name = "ai_trading_engine"

    async def get_or_create_master_key(self) -> bytes:
        """Get AES-256 master encryption key from secure environment variable"""
        if self._master_key:
            return self._master_key

        # Get master key from secure environment variable
        master_key_hex = os.getenv("CREDENTIAL_VAULT_KEY")
        
        if not master_key_hex:
            raise SecurityException(
                "CREDENTIAL_VAULT_KEY environment variable not set. "
                "This 32-byte (256-bit) key is required for AES-256 encryption."
            )
        
        try:
            # Try to decode as base64 first (common format), then hex
            import base64
            
            # Strictly require a 32-byte cryptographically random key
            try:
                # Try base64 decode first (most common secure format)
                raw_key = base64.b64decode(master_key_hex)
                logger.info("Master key decoded from base64 format")
            except Exception:
                try:
                    # Fallback to hex format
                    raw_key = bytes.fromhex(master_key_hex)
                    logger.info("Master key decoded from hex format")
                except Exception:
                    raise SecurityException(
                        "CREDENTIAL_VAULT_KEY must be a valid base64 or hex encoded 32-byte key. "
                        "Generate with: python -c 'import os, base64; print(base64.b64encode(os.urandom(32)).decode())'"
                    )
            
            # Strictly enforce 32-byte requirement for security
            if len(raw_key) != 32:
                raise SecurityException(
                    f"CREDENTIAL_VAULT_KEY must be exactly 32 bytes for AES-256 security. "
                    f"Got {len(raw_key)} bytes. Generate a proper key with: "
                    f"python -c 'import os, base64; print(base64.b64encode(os.urandom(32)).decode())'"
                )
            
            self._master_key = raw_key
            logger.info("AES-256 master encryption key loaded (32 bytes, cryptographically secure)")
            
        except Exception as e:
            raise SecurityException(f"Failed to process CREDENTIAL_VAULT_KEY: {e}")

        return self._master_key


class CredentialVault:
    """Secure storage for API credentials with AES-256-GCM encryption"""

    def __init__(self):
        self.key_manager = KeyManager()
        self.cipher: Optional[AESGCM] = None
        self.service_name = "ai_trading_engine"

    async def initialize(self):
        """Initialize AES-256-GCM encryption system with persistence verification"""
        try:
            encryption_key = await self.key_manager.get_or_create_master_key()
            self.cipher = AESGCM(encryption_key)
            
            # Verify keyring persistence capability
            await self._verify_keyring_persistence()
            
            logger.info("CredentialVault initialized with AES-256-GCM encryption and verified persistence")
        except Exception as e:
            logger.error(f"Failed to initialize CredentialVault: {e}")
            raise SecurityException(f"Credential vault initialization failed: {e}")
    
    async def _verify_keyring_persistence(self):
        """Verify that keyring supports persistent storage"""
        try:
            # Test persistence by storing and retrieving a test value
            test_key = "vault_persistence_test"
            test_value = "test_persistence_value"
            
            keyring.set_password(self.service_name, test_key, test_value)
            retrieved = keyring.get_password(self.service_name, test_key)
            
            if retrieved != test_value:
                raise SecurityException("Keyring persistence test failed")
            
            # Clean up test value
            keyring.delete_password(self.service_name, test_key)
            
            # Check keyring backend type
            backend = keyring.get_keyring()
            logger.info(f"Keyring backend verified: {type(backend).__name__}")
            
        except Exception as e:
            logger.error(f"Keyring persistence verification failed: {e}")
            raise SecurityException(
                f"Keyring backend does not support persistence: {e}. "
                f"Ensure keyrings.alt is properly installed for file-based storage."
            )

    async def store_api_credentials(self, provider: APIProvider, credentials: Dict[str, Any]) -> bool:
        """Securely store API credentials using AES-256-GCM"""
        try:
            if not self.cipher:
                await self.initialize()

            # Validate credentials format
            self._validate_credentials(provider, credentials)

            # Encrypt credentials using AES-256-GCM with AAD
            credentials_json = json.dumps(credentials, default=str)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            aad = provider.value.encode('utf-8')  # Additional authenticated data
            if not isinstance(self.cipher, AESGCM):
                raise SecurityException("Cipher not properly initialized")
            ciphertext = self.cipher.encrypt(nonce, credentials_json.encode(), aad)
            
            # Combine nonce + ciphertext for storage
            encrypted_data = nonce + ciphertext

            # Create encrypted credentials object
            encrypted_cred_obj = EncryptedCredentials(
                provider=provider,
                encrypted_data=encrypted_data,
                created_at=datetime.now(),
                access_count=0
            )

            # Store in credential manager (base64 encode for safe storage)
            import base64
            keyring.set_password(
                self.service_name,
                f"api_{provider.value}",
                base64.b64encode(encrypted_data).decode()
            )

            logger.info(f"Stored AES-256-GCM encrypted credentials for {provider.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to store credentials for {provider.value}: {e}")
            raise SecurityException(f"Credential storage failed: {e}")

    async def retrieve_api_credentials(self, provider: APIProvider) -> Optional[Dict[str, Any]]:
        """Securely retrieve API credentials using AES-256-GCM"""
        try:
            if not self.cipher:
                await self.initialize()

            encrypted_creds_b64 = keyring.get_password(
                self.service_name,
                f"api_{provider.value}"
            )

            if not encrypted_creds_b64:
                logger.warning(f"No credentials found for {provider.value}")
                return None

            # Decode base64 and extract nonce + ciphertext
            import base64
            encrypted_data = base64.b64decode(encrypted_creds_b64.encode())
            nonce = encrypted_data[:12]  # First 12 bytes are nonce
            ciphertext = encrypted_data[12:]  # Rest is ciphertext
            
            # Decrypt using AES-256-GCM with AAD
            aad = provider.value.encode('utf-8')  # Additional authenticated data
            if not isinstance(self.cipher, AESGCM):
                raise SecurityException("Cipher not properly initialized")
            decrypted_creds = self.cipher.decrypt(nonce, ciphertext, aad)
            credentials = json.loads(decrypted_creds.decode())

            logger.info(f"Retrieved AES-256-GCM encrypted credentials for {provider.value}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {provider.value}: {e}")
            raise SecurityException(f"Credential retrieval failed: {e}")

    def _validate_credentials(self, provider: APIProvider, credentials: Dict[str, Any]) -> None:
        """Validate credential format based on provider"""
        required_fields = {
            APIProvider.FLATTRADE: ["api_key", "api_secret"],
            APIProvider.FYERS: ["app_id", "app_secret", "redirect_uri"],
            APIProvider.UPSTOX: ["api_key", "api_secret"],
            APIProvider.ALICE_BLUE: ["user_id", "password", "api_key"]
        }

        required = required_fields.get(provider, [])
        missing_fields = [field for field in required if field not in credentials]

        if missing_fields:
            raise SecurityException(
                f"Missing required credential fields for {provider.value}: {missing_fields}"
            )

    async def delete_api_credentials(self, provider: APIProvider) -> bool:
        """Delete stored API credentials"""
        try:
            keyring.delete_password(self.service_name, f"api_{provider.value}")
            logger.info(f"Deleted credentials for {provider.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials for {provider.value}: {e}")
            return False

    async def list_stored_providers(self) -> list[APIProvider]:
        """List providers with stored credentials"""
        stored_providers = []

        for provider in APIProvider:
            try:
                if keyring.get_password(self.service_name, f"api_{provider.value}"):
                    stored_providers.append(provider)
            except Exception:
                continue

        return stored_providers

    async def store_auth_token(self, provider: APIProvider, token_data: Dict[str, Any]) -> bool:
        """Securely store authentication token using AES-256-GCM with expiry information"""
        try:
            if not self.cipher:
                await self.initialize()

            # Add metadata to token data
            token_with_metadata = {
                **token_data,
                "stored_at": datetime.now().isoformat(),
                "provider": provider.value
            }

            # Encrypt token data using AES-256-GCM with AAD
            token_json = json.dumps(token_with_metadata, default=str)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            aad = provider.value.encode('utf-8')  # Additional authenticated data
            if not isinstance(self.cipher, AESGCM):
                raise SecurityException("Cipher not properly initialized")
            ciphertext = self.cipher.encrypt(nonce, token_json.encode(), aad)
            
            # Combine nonce + ciphertext for storage
            encrypted_data = nonce + ciphertext

            # Store in credential manager with 'token_' prefix (base64 encode)
            import base64
            keyring.set_password(
                self.service_name,
                f"token_{provider.value}",
                base64.b64encode(encrypted_data).decode()
            )

            logger.info(f"Stored AES-256-GCM encrypted auth token for {provider.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to store auth token for {provider.value}: {e}")
            raise SecurityException(f"Token storage failed: {e}")

    async def retrieve_auth_token(self, provider: APIProvider) -> Optional[Dict[str, Any]]:
        """Securely retrieve authentication token using AES-256-GCM with expiry validation"""
        try:
            if not self.cipher:
                await self.initialize()

            encrypted_token_b64 = keyring.get_password(
                self.service_name,
                f"token_{provider.value}"
            )

            if not encrypted_token_b64:
                logger.debug(f"No auth token found for {provider.value}")
                return None

            # Decode base64 and extract nonce + ciphertext
            import base64
            encrypted_data = base64.b64decode(encrypted_token_b64.encode())
            nonce = encrypted_data[:12]  # First 12 bytes are nonce
            ciphertext = encrypted_data[12:]  # Rest is ciphertext
            
            # Decrypt using AES-256-GCM with AAD
            aad = provider.value.encode('utf-8')  # Additional authenticated data
            if not isinstance(self.cipher, AESGCM):
                raise SecurityException("Cipher not properly initialized")
            decrypted_token = self.cipher.decrypt(nonce, ciphertext, aad)
            token_data = json.loads(decrypted_token.decode())

            # Check if token has expired
            if self._is_token_expired(token_data):
                logger.warning(f"Auth token for {provider.value} has expired")
                await self.delete_auth_token(provider)  # Clean up expired token
                return None

            logger.debug(f"Retrieved valid AES-256-GCM encrypted auth token for {provider.value}")
            return token_data

        except Exception as e:
            logger.error(f"Failed to retrieve auth token for {provider.value}: {e}")
            return None

    async def delete_auth_token(self, provider: APIProvider) -> bool:
        """Delete stored authentication token"""
        try:
            keyring.delete_password(self.service_name, f"token_{provider.value}")
            logger.info(f"Deleted auth token for {provider.value}")
            return True
        except Exception as e:
            logger.debug(f"No auth token to delete for {provider.value}: {e}")
            return False

    def _is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if authentication token has expired"""
        try:
            # Check for expires_at field (ISO format)
            if "expires_at" in token_data:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                # Add 30 minute buffer for safety
                buffer_time = expires_at - timedelta(minutes=30)
                return datetime.now() >= buffer_time

            # Check for stored_at + duration (for tokens with known lifetime)
            if "stored_at" in token_data:
                stored_at = datetime.fromisoformat(token_data["stored_at"])
                # Fyers tokens typically last 8 hours
                token_lifetime_hours = token_data.get("lifetime_hours", 8)
                expires_at = stored_at + timedelta(hours=token_lifetime_hours)
                buffer_time = expires_at - timedelta(minutes=30)
                return datetime.now() >= buffer_time

            # If no expiry info, consider token valid (legacy case)
            return False

        except Exception as e:
            logger.error(f"Error checking token expiry: {e}")
            return True  # Err on side of caution

    async def list_stored_tokens(self) -> Dict[str, Dict[str, Any]]:
        """List all stored auth tokens with their status"""
        token_status = {}
        
        for provider in APIProvider:
            try:
                token_data = await self.retrieve_auth_token(provider)
                if token_data:
                    token_status[provider.value] = {
                        "has_token": True,
                        "stored_at": token_data.get("stored_at"),
                        "expires_at": token_data.get("expires_at"),
                        "is_expired": self._is_token_expired(token_data)
                    }
                else:
                    token_status[provider.value] = {"has_token": False}
            except Exception:
                token_status[provider.value] = {"has_token": False, "error": True}

        return token_status


class TOTPManager:
    """Two-Factor Authentication Manager"""

    def __init__(self, credential_vault: CredentialVault):
        self.credential_vault = credential_vault

    async def setup_totp(self, provider: APIProvider, secret_key: str, account_name: str) -> TOTPConfig:
        """Setup TOTP for a provider"""
        try:
            totp_config = TOTPConfig(
                secret_key=secret_key,
                account_name=account_name,
                issuer="AI Trading Engine"
            )

            # Store TOTP config securely
            await self.credential_vault.store_api_credentials(
                provider,
                {"totp_config": totp_config.dict()}
            )

            logger.info(f"TOTP setup completed for {provider.value}")
            return totp_config

        except Exception as e:
            logger.error(f"Failed to setup TOTP for {provider.value}: {e}")
            raise SecurityException(f"TOTP setup failed: {e}")

    def generate_totp_code(self, secret_key: str) -> str:
        """Generate TOTP code"""
        try:
            totp = pyotp.TOTP(secret_key)
            return totp.now()
        except Exception as e:
            logger.error(f"Failed to generate TOTP code: {e}")
            raise SecurityException(f"TOTP code generation failed: {e}")

    def verify_totp_code(self, secret_key: str, code: str) -> bool:
        """Verify TOTP code"""
        try:
            totp = pyotp.TOTP(secret_key)
            return totp.verify(code, valid_window=1)  # Allow 1 window of tolerance
        except Exception as e:
            logger.error(f"Failed to verify TOTP code: {e}")
            return False

    def get_totp_uri(self, secret_key: str, account_name: str, issuer: str = "AI Trading Engine") -> str:
        """Generate TOTP URI for QR code"""
        totp = pyotp.TOTP(secret_key)
        return totp.provisioning_uri(
            name=account_name,
            issuer_name=issuer
        )


class SecurityManager:
    """Comprehensive security management system"""

    def __init__(self):
        self.credential_vault = CredentialVault()
        self.totp_manager = TOTPManager(self.credential_vault)

    async def initialize(self):
        """Initialize all security components"""
        try:
            await self.credential_vault.initialize()
            logger.info("SecurityManager initialized successfully")
        except Exception as e:
            logger.error(f"SecurityManager initialization failed: {e}")
            raise SecurityException(f"Security manager initialization failed: {e}")
