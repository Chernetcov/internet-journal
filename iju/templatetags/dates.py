from datetime import date, datetime

from django import template

register = template.Library()

MONTHS_RU = [
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


@register.filter
def rus_date(value):
    """Форматирует дату как «11 октября 2026» на русском языке.

    Принимает datetime или строку даты. Использует полный месяц на русском.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        # Пытаемся распарсить ISO-формат (YYYY-MM-DD или с временем)
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return value

    if not isinstance(value, (datetime, date)):
        return str(value)

    return f"{value.day} {MONTHS_RU[value.month]} {value.year}"


@register.filter
def month_name(value):
    """Возвращает название месяца на русском языке (например, «октября»).

    Принимает число месяца (1–12) или datetime.
    """
    if value is None:
        return ""

    if isinstance(value, (datetime, date)):
        month = value.month
    elif isinstance(value, int):
        month = value
    else:
        try:
            month = int(value)
        except (ValueError, TypeError):
            return str(value)

    if not 1 <= month <= 12:
        return str(month)

    return MONTHS_RU[month]
