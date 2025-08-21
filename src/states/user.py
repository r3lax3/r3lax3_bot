"""
Состояния пользователя (FSM)
"""
from aiogram.fsm.state import State, StateGroup


class UserSG(StateGroup):
    """Состояния пользователя"""
    
    # Основные состояния
    STATE_IDLE = State()  # Дефолтное состояние, главное меню
    
    # Подписки
    STATE_SUBSCRIPTIONS_LIST = State()  # Просмотр списка подписок
    STATE_SUBSCRIPTION_DETAIL = State()  # Просмотр конкретной подписки
    
    # Платежи
    STATE_PAYMENT_METHOD_SELECT = State()  # Выбор платёжного провайдера/плана
    STATE_PAYMENT_PENDING = State()  # Ожидание оплаты
    
    # История платежей
    STATE_PAYMENTS_HISTORY = State()  # Просмотр истории платежей
    STATE_PAYMENT_DETAIL = State()  # Просмотр детали платежа
    
    # Язык и поддержка
    STATE_LANGUAGE_SELECT = State()  # Выбор языка
    STATE_FAQ = State()  # Просмотр FAQ
