# **10. Security & Compliance Implementation**

### **10.1 API Credential Security**

#### **10.1.1 Encrypted Credential Storage**
```python
from cryptography.fernet import Fernet
import keyring
import json

class SecureCredentialManager:
    """Secure storage and management of API credentials"""
    
    def __init__(self):
        self.key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.key)
    
    def get_or_create_encryption_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        try:
            key = keyring.get_password("ai_trading_engine", "encryption_key")
            if key:
                return key.encode()
        except Exception:
            pass
        
        # Create new key
        key = Fernet.generate_key()
        keyring.set_password("ai_trading_engine", "encryption_key", key.decode())
        return key
    
    def store_credentials(self, api_name: str, credentials: Dict):
        """Store encrypted API credentials"""
        encrypted_data = self.cipher.encrypt(
            json.dumps(credentials).encode()
        )
        
        keyring.set_password(
            "ai_trading_engine", 
            f"api_creds_{api_name}", 
            encrypted_data.decode()
        )
    
    def get_credentials(self, api_name: str) -> Optional[Dict]:
        """Retrieve and decrypt API credentials"""
        try:
            encrypted_data = keyring.get_password(
                "ai_trading_engine", 
                f"api_creds_{api_name}"
            )
            
            if encrypted_data:
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                return json.loads(decrypted_data.decode())
        except Exception as e:
            st.error(f"Failed to retrieve credentials for {api_name}: {e}")
        
        return None
```

### **10.2 Audit Trail Implementation**

#### **10.2.1 Comprehensive Logging System**
```python
import logging
from datetime import datetime
import sqlite3
import json

class AuditLogger:
    """SEBI-compliant audit trail logging"""
    
    def __init__(self, db_path: str = "audit_trail.db"):
        self.db_path = db_path
        self.initialize_database()
        self.setup_logger()
    
    def initialize_database(self):
        """Initialize audit trail database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(100),
                session_id VARCHAR(100),
                api_source VARCHAR(50),
                event_data TEXT,
                ip_address VARCHAR(45),
                checksum VARCHAR(64),
                INDEX idx_timestamp (timestamp),
                INDEX idx_event_type (event_type)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_trade_event(self, event_type: str, trade_data: Dict):
        """Log trading-related events"""
        self.log_event(
            event_type=event_type,
            event_data=trade_data,
            category="TRADING"
        )
    
    def log_system_event(self, event_type: str, system_data: Dict):
        """Log system events"""
        self.log_event(
            event_type=event_type,
            event_data=system_data,
            category="SYSTEM"
        )
    
    def log_event(self, event_type: str, event_data: Dict, category: str = "GENERAL"):
        """Log any event with full audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate checksum for data integrity
        data_str = json.dumps(event_data, sort_keys=True)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO audit_trail 
            (timestamp, event_type, user_id, session_id, api_source, 
             event_data, ip_address, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            f"{category}_{event_type}",
            st.session_state.get('user_id', 'anonymous'),
            st.session_state.get('session_id'),
            event_data.get('api_source'),
            data_str,
            self.get_client_ip(),
            checksum
        ))
        
        conn.commit()
        conn.close()
```

---
