from enum import StrEnum
from typing import TypeVar

from sqlalchemy import Enum

E = TypeVar("E", bound=StrEnum)


def pg_enum(enum_class: type[E], name: str) -> Enum:
    return Enum(enum_class, name=name, values_callable=lambda x: [member.value for member in x])
