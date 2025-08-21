"""
Фабрики для callback данных
"""
from aiogram.filters.callback_data import CallbackData


class SubscriptionCallback(CallbackData, prefix="sub"):
    """Callback для подписок"""
    action: str  # t - тип действия
    page: int = 1  # p - страница
    subscription_id: int = 0  # id - ID подписки


class PaymentCallback(CallbackData, prefix="pay"):
    """Callback для платежей"""
    action: str  # t - тип действия
    payment_id: str = ""  # id - ID платежа
    page: int = 1  # p - страница


class PaymentHistoryCallback(CallbackData, prefix="ph"):
    """Callback для истории платежей"""
    page: int = 1  # p - страница


class PaymentDetailCallback(CallbackData, prefix="pd"):
    """Callback для детали платежа"""
    payment_id: str  # id - ID платежа


class RenewCallback(CallbackData, prefix="renew"):
    """Callback для продления подписки"""
    subscription_id: int  # id - ID подписки


class AdminCallback(CallbackData, prefix="admin"):
    """Callback для админ функций"""
    action: str  # t - тип действия
    target_id: int = 0  # id - целевой ID
    page: int = 1  # p - страница


class AdminExtendCallback(CallbackData, prefix="aex"):
    """Callback для продления подписки (админ)"""
    action: str  # select_plan | confirm | cancel
    subscription_id: int
    plan: str = ""


class NavigationCallback(CallbackData, prefix="nav"):
    """Callback для навигации"""
    action: str  # t - тип действия
    target: str = "main"  # to - куда вернуться


class LanguageCallback(CallbackData, prefix="lang"):
    """Callback для смены языка"""
    language: str  # l - язык (ru/en)


class AdminServiceCallback(CallbackData, prefix="asvc"):
    """Callback для действий с сервисом (админ)"""
    action: str  # start | pause | resume
    service_id: int
