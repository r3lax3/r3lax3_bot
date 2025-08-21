"""
Утилиты для форматирования
"""
from datetime import datetime
from typing import Optional
from src.i18n.translations import translations


def format_date(date_str: str, language: str = "ru") -> str:
    """Форматирование даты согласно языку пользователя"""
    try:
        # Парсим ISO8601 дату
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        if language == "ru":
            return dt.strftime("%d.%m.%Y %H:%M")
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_str


def format_money(amount: float, currency: str) -> str:
    """Форматирование денежных сумм"""
    # Определяем количество десятичных знаков для валюты
    decimal_places = 2 if currency in ["RUB", "USD", "EUR"] else 2
    
    # Форматируем с нужным количеством знаков после запятой
    formatted_amount = f"{amount:.{decimal_places}f}".rstrip('0').rstrip('.')
    
    return f"{formatted_amount} {currency}"


def format_status(status: str, language: str = "ru") -> str:
    """Форматирование статусов для пользователя"""
    status_mapping = {
        "active": "status.active",
        "expired": "status.expired", 
        "paused": "status.paused",
        "created": "status.pending",
        "pending": "status.pending",
        "paid": "status.paid",
        "failed": "status.failed",
        "canceled": "status.canceled",
        "refunded": "status.refunded",
        "chargeback": "status.chargeback"
    }
    
    key = status_mapping.get(status, status)
    return translations.get(key, language)


def truncate_service_name(name: str, max_length: int = 10) -> str:
    """Усечение названия сервиса с многоточием"""
    if len(name) <= max_length:
        return name
    
    return name[:max_length] + "…"


def calculate_minutes_until_expiry(expires_at: str) -> int:
    """Вычисление минут до истечения счета"""
    try:
        dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = dt - now
        
        minutes = int(diff.total_seconds() / 60)
        return max(0, minutes)
    except (ValueError, TypeError):
        return 0


def format_payment_description(
    payment_id: str,
    provider: str,
    amount: float,
    currency: str,
    status: str,
    date: str,
    description: Optional[str] = None,
    external_id: Optional[str] = None,
    language: str = "ru"
) -> str:
    """Форматирование описания платежа"""
    # Определяем какой ключ использовать в зависимости от наличия полей
    if description and external_id:
        key = "payments.detail.title"
    elif description:
        key = "payments.detail.no_external_id"
    elif external_id:
        key = "payments.detail.no_description"
    else:
        key = "payments.detail.no_description_no_external"
    
    # Подставляем значения
    return translations.get(key, language).format(
        payment_id=payment_id,
        provider=provider,
        amount=amount,
        currency=currency,
        status=format_status(status, language),
        date=format_date(date, language),
        description=description or "",
        external_id=external_id or ""
    )
