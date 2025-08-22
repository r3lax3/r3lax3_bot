"""
Inline клавиатуры
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.i18n.translations import translations
from src.keyboards.factories import (
    SubscriptionCallback, PaymentCallback, PaymentHistoryCallback,
    PaymentDetailCallback, RenewCallback, AdminCallback,
    NavigationCallback, LanguageCallback
)
from typing import Optional
from src.utils.formatters import format_status, truncate_service_name, format_date


def get_subscriptions_list_keyboard(
    subscriptions: list, 
    current_page: int, 
    total_pages: int,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для списка подписок"""
    keyboard = []
    
    # Кнопки подписок
    for sub in subscriptions:
        service_name = sub.get("service_name", "Unknown")
        truncated_name = truncate_service_name(service_name)
        status_text = format_status(sub.get("status", "unknown"), language)
        button_text = f"{truncated_name} | {status_text}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=SubscriptionCallback(
                    action="detail",
                    subscription_id=sub["id"]
                ).pack()
            )
        ])
    
    # Пагинация
    if total_pages > 1:
        pagination_row = []
        
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=SubscriptionCallback(
                        action="list",
                        page=current_page - 1
                    ).pack()
                )
            )
        
        pagination_row.append(
            InlineKeyboardButton(
                text=translations.get("pagination.page", language).format(
                    page=current_page, pages=total_pages
                ),
                callback_data="no_action"
            )
        )
        
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=SubscriptionCallback(
                        action="list",
                        page=current_page + 1
                    ).pack()
                )
            )
        
        keyboard.append(pagination_row)
    
    # Кнопка назад
    keyboard.append([
        InlineKeyboardButton(
            text=translations.get("nav.back", language),
            callback_data=NavigationCallback(action="back", target="main").pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscription_detail_keyboard(
    subscription_id: int,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для детали подписки"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations.get("subscriptions.detail.renew", language),
                callback_data=RenewCallback(subscription_id=subscription_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("nav.back", language),
                callback_data=SubscriptionCallback(action="list", page=1).pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_method_select_keyboard(
    providers: list,
    plans: list,
    subscription_id: int,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора способа оплаты"""
    keyboard = []
    
    # Кнопки провайдеров и планов
    for provider in providers:
        for plan in plans:
            plan_code = plan["code"]
            amount = plan["amount"]
            currency = plan["currency"]
            
            button_text = f"{provider.upper()} - {plan_code} ({amount} {currency})"
            
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=PaymentCallback(
                        action="select",
                        payment_id=f"{subscription_id}:{provider}:{plan_code}"
                    ).pack()
                )
            ])
    
    # Кнопка оферты
    keyboard.append([
        InlineKeyboardButton(
            text=translations.get("payment.terms_pdf", language),
            callback_data=PaymentCallback(
                action="terms",
                payment_id=str(subscription_id)
            ).pack()
        )
    ])
    
    # Кнопка назад
    keyboard.append([
        InlineKeyboardButton(
            text=translations.get("nav.back", language),
            callback_data=SubscriptionCallback(
                action="detail",
                subscription_id=subscription_id
            ).pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_waiting_keyboard(
    payment_id: str,
    pay_link: Optional[str] = None,
    qr_url: Optional[str] = None,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для ожидания оплаты"""
    keyboard = []
    
    if pay_link:
        keyboard.append([
            InlineKeyboardButton(
                text=translations.get("payment.open_invoice", language),
                url=pay_link
            )
        ])
    
    keyboard.extend([
        [
            InlineKeyboardButton(
                text=translations.get("payment.check_status", language),
                callback_data=PaymentCallback(
                    action="check",
                    payment_id=payment_id
                ).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("payment.cancel", language),
                callback_data=PaymentCallback(
                    action="cancel",
                    payment_id=payment_id
                ).pack()
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_failed_keyboard(
    payment_id: str,
    subscription_id: int,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для неуспешной оплаты"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations.get("payment.retry", language),
                callback_data=RenewCallback(subscription_id=subscription_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("payment.change_method", language),
                callback_data=PaymentCallback(action="change_method", payment_id=str(subscription_id)).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("nav.back", language),
                callback_data=SubscriptionCallback(
                    action="detail",
                    subscription_id=subscription_id
                ).pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payments_history_keyboard(
    payments: list,
    current_page: int,
    total_pages: int,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура для истории платежей"""
    keyboard = []
    
    # Кнопки платежей
    for payment in payments:
        date = payment.get("date", "")
        amount = payment.get("amount", 0)
        currency = payment.get("currency", "")
        provider = payment.get("provider", "")
        status = payment.get("status", "")
        formatted_date = format_date(date, language)
        status_text = format_status(status, language)
        button_text = f"{formatted_date} — {amount}{currency} — {provider} — {status_text}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=PaymentDetailCallback(
                    payment_id=payment["id"]
                ).pack()
            )
        ])
    
    # Пагинация
    if total_pages > 1:
        pagination_row = []
        
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=PaymentHistoryCallback(page=current_page - 1).pack()
                )
            )
        
        pagination_row.append(
            InlineKeyboardButton(
                text=translations.get("pagination.page", language).format(
                    page=current_page, pages=total_pages
                ),
                callback_data="no_action"
            )
        )
        
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=PaymentHistoryCallback(page=current_page + 1).pack()
                )
            )
        
        keyboard.append(pagination_row)
    
    # Кнопка назад
    keyboard.append([
        InlineKeyboardButton(
            text=translations.get("nav.back", language),
            callback_data=NavigationCallback(action="back", target="main").pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_select_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для выбора языка"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data=LanguageCallback(language="ru").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="🇺🇸 English",
                callback_data=LanguageCallback(language="en").pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_main_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Главная клавиатура админа"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=translations.get("admin.broadcast.title", language),
                callback_data=AdminCallback(action="broadcast").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("admin.stats.title", language),
                callback_data=AdminCallback(action="stats").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("admin.users.title", language),
                callback_data=AdminCallback(action="users").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("admin.services.title", language),
                callback_data=AdminCallback(action="services").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=translations.get("nav.back", language),
                callback_data=NavigationCallback(action="back", target="main").pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
