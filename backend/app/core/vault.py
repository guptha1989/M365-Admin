import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings

logger = logging.getLogger("m365_admin.vault")

def _get_fernet_key() -> bytes:
    """Derives a deterministic 32-byte Fernet key from settings.ENCRYPTION_KEY or SECRET_KEY."""
    raw_secret = (settings.ENCRYPTION_KEY or settings.SECRET_KEY).encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"m365_admin_sql_express_vault_salt",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(raw_secret))

def encrypt_key(plain_text: str) -> str:
    """Encrypts a plaintext API/LLM key using AES-256 Fernet encryption."""
    if not plain_text:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encrypting API key in AES-256 vault: {e}")
        return plain_text

def decrypt_key(cipher_text: str) -> str:
    """Decrypts an encrypted API/LLM key from the AES-256 Fernet vault."""
    if not cipher_text:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.warning(f"Decryption failed or plaintext returned: {e}")
        return cipher_text
