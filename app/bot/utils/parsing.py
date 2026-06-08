from __future__ import annotations

from datetime import date, datetime, time


DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y")
TIME_FORMATS = ("%H:%M", "%H.%M")


def parse_birth_date(value: str) -> date:
    clean = value.strip()
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(clean, fmt).date()
        except ValueError:
            continue
        if parsed > date.today():
            raise ValueError("birth date cannot be in the future")
        return parsed
    raise ValueError("unsupported date format")


def parse_birth_time(value: str) -> time | None:
    clean = value.strip().lower()
    if clean in {"не знаю", "нет", "unknown", "примерно", "-"}:
        return None
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(clean, fmt).time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    raise ValueError("unsupported time format")
