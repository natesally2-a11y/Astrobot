from datetime import date, time

from app.bot.utils.parsing import parse_birth_date, parse_birth_time, parse_partner_data


def test_parse_birth_date_user_format() -> None:
    assert parse_birth_date("24.03.1992") == date(1992, 3, 24)


def test_parse_birth_date_iso_format() -> None:
    assert parse_birth_date("1992-03-24") == date(1992, 3, 24)


def test_parse_birth_time_unknown() -> None:
    assert parse_birth_time("не знаю") is None


def test_parse_partner_data() -> None:
    birth_date, birth_time, city = parse_partner_data("15.07.1990; 18:20; Казань")
    assert birth_date == date(1990, 7, 15)
    assert birth_time == time(18, 20)
    assert city == "Казань"
