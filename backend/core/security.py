"""
Security Management System
Handles credential storage, encryption, and authentication
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import keyring
import pyotp
from loguru import logger

from models.trading import (
    APIProvider, EncryptedCredentials, TOTPConfig, APIConfig
)


class SecurityException(Exception):
    """Custom security exception"""
    pass


class KeyManager:
    """Manages encryption keys and secure storage"""
    
    def __init__(self):
        self._master_key = None
        self.service_name = "ai_trading_engine"
        
    async def get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        if self._master_key:
            return self._master_key
            
        # Try to retrieve existing key
        stored_key = keyring.get_password(self.service_name, "master_key")
        
        if stored_key:
            self._master_key = stored_key.encode()
        else:
            # Generate new key
            self._master_key = Fernet.generate_key()
            keyring.set_password(
                self.service_name, 
                "master_key", 
                self._master_key.decode()
            )
            logger.info("Generated new master encryption key")
            
        return self._master_key


class CredentialVault:
    """Secure storage for API credentials with AES-256 encryption"""
    
    def __init__(self):
        self.key_manager = KeyManager()
        self.cipher = None
        self.service_name = "ai_trading_engine"
        
    async def initialize(self):
        """Initialize encryption system"""
        try:
            encryption_key = await self.key_manager.get_or_create_master_key()
            self.cipher = Fernet(encryption_key)
            logger.info("CredentialVault initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CredentialVault: {e}")
            raise SecurityException(f"Credential vault initialization failed: {e}")
    
    async def store_api_credentials(self, provider: APIProvider, credentials: Dict[str, Any]) -> bool:
        """Securely store API credentials"""
        try:
            if not self.cipher:
                await self.initialize()
            
            # Validate credentials format
            self._validate_credentials(provider, credentials)
            
            # Encrypt credentials
            credentials_json = json.dumps(credentials, default=str)
            encrypted_creds = self.cipher.encrypt(credentials_json.encode())
            
            # Create encrypted credentials object
            encrypted_cred_obj = EncryptedCredentials(
                provider=provider,
                encrypted_data=encrypted_creds,
                created_at=datetime.now(),
                access_count=0
            )
            
            # Store in Windows Credential Manager
            keyring.set_password(
                self.service_name,
                f"api_{provider.value}",
                encrypted_creds.decode()
            )
            
            logger.info(f"Stored encrypted credentials for {provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {provider.value}: {e}")
            raise SecurityException(f"Credential storage failed: {e}")
    
    async def retrieve_api_credentials(self, provider: APIProvider) -> Optional[Dict[str, Any]]:
        """Securely retrieve API credentials"""
        try:
            if not self.cipher:
                await self.initialize()
            
            encrypted_creds = keyring.get_password(
                self.service_name,
                f"api_{provider.value}"
            )
            
            if not encrypted_creds:
                logger.warning(f"No credentials found for {provider.value}")
                return None
            
            # Decrypt credentials
            decrypted_creds = self.cipher.decrypt(encrypted_creds.encode())
            credentials = json.loads(decrypted_creds.decode())
            
            logger.info(f"Retrieved credentials for {provider.value}")
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
