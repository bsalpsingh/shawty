
from typing import Any
from sqlalchemy import inspect
from datetime import date, datetime
from typing import Any


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
