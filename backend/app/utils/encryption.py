import base64
from functools import lru_cache
from cryptography.fernet import Fernet
from app.config.settings import settings


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    raw = bytes.fromhex(key)  # 32 bytes from 64-char hex
    b64 = base64.urlsafe_b64encode(raw)
    return Fernet(b64)


def encrypt_token(token: str) -> str:
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()
