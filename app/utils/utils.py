import random
import hashlib
import base62
from typing import Any
from sqlalchemy import inspect
from datetime import date, datetime
from typing import Any
from app.core.redis import cache

def alchemy_obj_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy model instance into a JSON-safe dict of its column values."""
    if obj is None:
        return {}
    
    result = {}
    for c in inspect(obj).mapper.column_attrs:
        val = getattr(obj, c.key)
        
        # Convert date and datetime objects to ISO strings
        if isinstance(val, (datetime, date)):
            result[c.key] = val.isoformat()
        else:
            result[c.key] = val
            
    return result

def md5_to_base62(text: str) -> str:
    # 1. Generate the MD5 raw byte array (16 bytes)
    md5_bytes = hashlib.md5(text.encode('utf-8')).digest()
    
    # 2. Convert bytes to a single big integer
    # 'big' ensures leading zeros in bytes don't skew the value order
    hash_int = int.from_bytes(md5_bytes, byteorder='big')
    
    # 3. Encode that large integer into Base62
    return base62.encode(hash_int)


async def set_with_jitter(key,value,ttl:int):
    if(ttl<=0):
        raise ValueError(f"invalid ttl value of {ttl}")

    max_jitter=int(ttl*0.1)
    jitter= random.randint(0,max_jitter)
    ttl_with_jitter=ttl+jitter
    await cache.set(key,value,ttl_with_jitter)


async def refresh_cache_entry(short_code:str,ttl:int=3600,refresh_threshold=0.2,cb=None):
    remaining = await cache._client.ttl(short_code)
    if remaining in [-1,-2] :
        return
    if remaining >= ttl*refresh_threshold:
        return 
    #  sync from db
    if cb is not None:
       await cb()
    
    


