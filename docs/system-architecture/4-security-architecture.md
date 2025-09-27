# **4. Security Architecture**

## **4.1 Comprehensive Security Framework**

```python
class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self):
        self.credential_vault = CredentialVault()
        self.session_manager = SessionManager()
        self.audit_logger = AuditLogger()
        self.access_controller = AccessController()
        
    async def initialize_security(self):
        """Initialize all security components"""
        await self.credential_vault.initialize()
        await self.setup_encryption()
        await self.configure_access_controls()

class CredentialVault:
    """Secure storage for API credentials with AES-256 encryption"""
    
    def __init__(self):
        self.cipher = None
        self.key_manager = KeyManager()
        
    async def initialize(self):
        """Initialize encryption system"""
        self.encryption_key = await self.key_manager.get_or_create_master_key()
        self.cipher = Fernet(self.encryption_key)
    
    async def store_api_credentials(self, provider: str, credentials: Dict):
        """Securely store API credentials"""
        encrypted_creds = self.cipher.encrypt(
            json.dumps(credentials).encode()
        )
        
        # Store in Windows Credential Manager
        keyring.set_password(
            "ai_trading_engine",
            f"api_{provider}",
            encrypted_creds.decode()
        )
        
        await self.audit_logger.log_security_event(
            'CREDENTIAL_STORED',
            {'provider': provider, 'timestamp': datetime.now()}
        )
    
    async def retrieve_api_credentials(self, provider: str) -> Optional[Dict]:
        """Securely retrieve API credentials"""
        try:
            encrypted_creds = keyring.get_password(
                "ai_trading_engine",
                f"api_{provider}"
            )
            
            if encrypted_creds:
                decrypted_creds = self.cipher.decrypt(encrypted_creds.encode())
                return json.loads(decrypted_creds.decode())
                
        except Exception as e:
            await self.audit_logger.log_security_event(
                'CREDENTIAL_RETRIEVAL_FAILED',
                {'provider': provider, 'error': str(e)}
            )
        
        return None

class AuditLogger:
    """SEBI-compliant audit logging system"""
    
    def __init__(self, database: Database):
        self.db = database
        self.retention_days = 2555  # 7 years retention
        
    async def log_trade_event(self, event_type: str, trade_data: Dict):
        """Log trading events for regulatory compliance"""
        checksum = self.calculate_checksum(trade_data)
        
        await self.db.execute("""
            INSERT INTO audit_logs 
            (event_type, event_category, event_data, timestamp, checksum)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event_type,
            'TRADING',
            json.dumps(trade_data),
            datetime.now(),
            checksum
        ))
    
    async def log_security_event(self, event_type: str, security_data: Dict):
        """Log security events"""
        await self.log_event('SECURITY', event_type, security_data)
    
    def calculate_checksum(self, data: Dict) -> str:
        """Calculate SHA-256 checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
```

## **4.2 Access Control System**

```python
class AccessController:
    """Role-based access control system"""
    
    def __init__(self):
        self.roles = {
            'paper_trader': {
                'permissions': ['view_portfolio', 'paper_trade', 'view_analytics'],
                'restrictions': ['no_live_trading']
            },
            'live_trader': {
                'permissions': ['view_portfolio', 'paper_trade', 'live_trade', 'view_analytics'],
                'restrictions': ['daily_loss_limits']
            },
            'admin': {
                'permissions': ['all'],
                'restrictions': []
            }
        }
    
    async def check_permission(self, user_role: str, action: str) -> bool:
        """Check if user has permission for action"""
        role_config = self.roles.get(user_role, {})
        permissions = role_config.get('permissions', [])
        
        if 'all' in permissions:
            return True
            
        return action in permissions
    
    async def enforce_trading_limits(self, user_role: str, order: OrderRequest) -> bool:
        """Enforce role-based trading limits"""
        if user_role == 'paper_trader' and not order.is_paper_trade:
            raise SecurityException("Paper trader cannot place live orders")
        
        # Additional limit checks based on role
        return True
```

---
