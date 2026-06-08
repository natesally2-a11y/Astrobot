from __future__ import annotations

from decimal import Decimal

from app.astrology.schemas import BirthProfile
from app.database.models import BirthData, User


def _to_float(value: float | Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def birth_profile_from_user(user: User) -> BirthProfile:
    if user.birth_data is None:
        raise ValueError("user has no birth data")
    return birth_profile_from_model(user.birth_data)


def birth_profile_from_model(birth_data: BirthData) -> BirthProfile:
    return BirthProfile(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        birth_place=birth_data.birth_place,
        latitude=_to_float(birth_data.latitude),
        longitude=_to_float(birth_data.longitude),
        timezone=birth_data.timezone,
    )
