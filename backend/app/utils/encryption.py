import json

from cryptography.fernet import Fernet

from app.config import settings


def get_fernet() -> Fernet:
    key = settings.cookie_encryption_key
    if not key:
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_cookies(cookies: list[dict]) -> bytes:
    return get_fernet().encrypt(json.dumps(cookies).encode())


def decrypt_cookies(data: bytes) -> list[dict]:
    return json.loads(get_fernet().decrypt(data).decode())
