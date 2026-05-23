from decimal import Decimal
from typing import Any
from uuid import UUID


def to_str_id(value: UUID | str | None) -> str | None:
    if value is None:
        return None
    return str(value)


def model_to_dict(obj: Any, extra: dict | None = None) -> dict:
    data: dict[str, Any] = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
    if hasattr(obj, "__table__"):
        for col in obj.__table__.columns:
            val = getattr(obj, col.name)
            if isinstance(val, UUID):
                data[col.name] = str(val)
            elif isinstance(val, Decimal):
                data[col.name] = val
            else:
                data[col.name] = val
    if extra:
        data.update(extra)
    return data
