"""
Утилиты валидации для админских фич
"""
from typing import Tuple


def validate_broadcast_segment(raw: str) -> Tuple[bool, str]:
    """Проверка сегмента: all|active_subs|no_active_subs|service:<id>"""
    raw = (raw or "").strip()
    if raw in {"all", "active_subs", "no_active_subs"}:
        return True, raw
    if raw.startswith("service:"):
        rest = raw.split(":", 1)[1]
        if rest.isdigit():
            return True, raw
        return False, "service:<id> must have numeric id"
    return False, "segment must be one of: all|active_subs|no_active_subs|service:<id>"


def clamp_page(page: int, pages: int) -> int:
    """Клипуем страницу в диапазон 1..pages"""
    if pages <= 0:
        return 1
    if page < 1:
        return 1
    if page > pages:
        return pages
    return page

