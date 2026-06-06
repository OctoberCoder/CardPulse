import pytest
from app.services.encryption import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    original = "AMZ-1234-5678-ABCD"
    encoded = encrypt(original)
    assert encoded != original
    decoded = decrypt(encoded)
    assert decoded == original


def test_encryption_produces_different_outputs():
    code = "TEST-CODE"
    e1 = encrypt(code)
    e2 = encrypt(code)
    assert e1 != e2


def test_decrypt_invalid_data():
    with pytest.raises(Exception):
        decrypt("not-valid-base64!!")
