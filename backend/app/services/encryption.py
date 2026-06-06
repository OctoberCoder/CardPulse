from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import get_settings
import os
import base64


def _get_key() -> bytes:
    key = get_settings().encryption_key
    return key.encode().ljust(32, b'\0')[:32]


def encrypt(plaintext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt(encoded: str) -> str:
    key = _get_key()
    data = base64.urlsafe_b64decode(encoded)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
