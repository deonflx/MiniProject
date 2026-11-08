import base64
import hashlib
import hmac
import os
import re
from django.conf import settings
from cryptography.fernet import Fernet

def _get_encryption_key() -> bytes:
    """
    Returns a valid 32-byte Fernet key.
    Uses DATA_ENCRYPTION_KEY if provided in .env, or derives one deterministically
    from DJANGO_SECRET_KEY as a safe fallback.
    """
    custom_key = os.getenv("DATA_ENCRYPTION_KEY")
    if custom_key:
        try:
            return custom_key.strip().encode("utf-8")
        except Exception:
            pass

    # Deterministic fallback derivation from SECRET_KEY
    secret = getattr(settings, "SECRET_KEY", "fallback-secret-key-32-bytes-minimum")
    digest = hashlib.sha256(f"fernet-encryption-{secret}".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

def _get_hash_salt() -> bytes:
    """Returns the secret salt used for HMAC one-way hashing."""
    salt = os.getenv("HASH_SALT")
    if salt:
        return salt.strip().encode("utf-8")
    secret = getattr(settings, "SECRET_KEY", "default-salt")
    return hashlib.sha256(f"salt-{secret}".encode("utf-8")).digest()

_fernet_instance = None

def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(_get_encryption_key())
    return _fernet_instance

def encrypt_field(value: str | float | int | None) -> str:
    """Encrypts a plaintext value and returns a base64 ciphertext string."""
    if value is None or value == "":
        return ""
    text_val = str(value)
    return get_fernet().encrypt(text_val.encode("utf-8")).decode("utf-8")

def decrypt_field(token: str | None) -> str:
    """Decrypts a base64 ciphertext string back to plaintext."""
    if not token:
        return ""
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        # If decryption fails (e.g. data was already plaintext during migration)
        return token

def hash_identity(raw_val: str | None) -> str:
    """
    Produces a secure deterministic HMAC-SHA256 hex digest for indexed lookups.
    Normalizes input by stripping spaces and standardizing casing.
    """
    if not raw_val:
        return ""
    normalized = re.sub(r"\s+", "", str(raw_val)).upper()
    return hmac.new(_get_hash_salt(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()

def mask_aadhaar(aadhaar: str | None) -> str:
    """Returns a masked Aadhaar string like 'XXXX-XXXX-1234'."""
    if not aadhaar:
        return ""
    digits = re.sub(r"\D", "", str(aadhaar))
    if len(digits) >= 4:
        return f"XXXX-XXXX-{digits[-4:]}"
    return "XXXX-XXXX-XXXX"

def mask_pan(pan: str | None) -> str:
    """Returns a masked PAN string like 'XXXXXX1234F'."""
    if not pan:
        return ""
    clean = re.sub(r"\s", "", str(pan)).upper()
    if len(clean) == 10:
        return f"XXXXXX{clean[6:]}"
    return clean[:2] + "X" * (len(clean) - 4) + clean[-2:] if len(clean) >= 4 else "XXXXXXXXXX"
