import hashlib, hmac, os

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"{salt.hex()}${key.hex()}"

def verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split("$")
    key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                         n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(key, bytes.fromhex(key_hex))