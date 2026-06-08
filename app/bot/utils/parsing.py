from datetime import date, time


def parse_birth_date(value: str) -> date:
    normalized = value.strip().replace("/", ".").replace("-", ".")
    parts = normalized.split(".")
    if len(parts) != 3:
        raise ValueError("Expected date in DD.MM.YYYY format.")

    if len(parts[0]) == 4:
        year, month, day = (int(part) for part in parts)
    else:
        day, month, year = (int(part) for part in parts)
    if year < 100:
        year += 1900 if year > 30 else 2000
    return date(year, month, day)


def parse_birth_time(value: str) -> time | None:
    normalized = value.strip().lower()
    if normalized in {"не знаю", "нет", "unknown", "примерно", "неизвестно"}:
        return None

    normalized = normalized.replace(".", ":")
    parts = normalized.split(":")
    if len(parts) == 1:
        hour = int(parts[0])
        minute = 0
    elif len(parts) == 2:
        hour, minute = (int(part) for part in parts)
    else:
        raise ValueError("Expected time in HH:MM format.")

    return time(hour=hour, minute=minute)


def parse_partner_data(value: str) -> tuple[date, time | None, str]:
    parts = [part.strip() for part in value.split(";")]
    if len(parts) < 3:
        raise ValueError("Use: DD.MM.YYYY; HH:MM; City")
    return parse_birth_date(parts[0]), parse_birth_time(parts[1]), parts[2]
