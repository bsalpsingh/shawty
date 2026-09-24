
import hashlib
import base62
from typing import Any
from sqlalchemy import inspect

def alchemy_obj_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy model instance into a plain dict of its column values."""
    if obj is None:
        return {}
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def md5_to_base62(text: str) -> str:
    # 1. Generate the MD5 raw byte array (16 bytes)
    md5_bytes = hashlib.md5(text.encode('utf-8')).digest()
    
    # 2. Convert bytes to a single big integer
    # 'big' ensures leading zeros in bytes don't skew the value order
    hash_int = int.from_bytes(md5_bytes, byteorder='big')
    
    # 3. Encode that large integer into Base62
    return base62.encode(hash_int)

