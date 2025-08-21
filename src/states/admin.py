"""
Состояния администратора (FSM)
"""
from aiogram.fsm.state import State, StateGroup


class AdminSG(StateGroup):
    """Состояния администратора"""
    
    # Основные состояния админа
    STATE_ADMIN_MAIN = State()  # Главное меню админа
    
    # Рассылка
    STATE_ADMIN_BROADCAST = State()  # Настройка и рассылка
    STATE_ADMIN_BROADCAST_TEXT = State()  # Ввод текста рассылки
    STATE_ADMIN_BROADCAST_SEGMENT = State()  # Выбор сегмента
    STATE_ADMIN_BROADCAST_PREVIEW = State()  # Предпросмотр и подтверждение
    
    # Пользователи
    STATE_ADMIN_USER_SEARCH = State()  # Поиск пользователя
    STATE_ADMIN_USER_EDIT = State()  # Редактор пользователя/подписок
    
    # Сервисы
    STATE_ADMIN_SERVICES = State()  # Список сервисов
    STATE_ADMIN_SERVICE_DETAIL = State()  # Информация и управление сервисом
    
    # Статистика
    STATE_ADMIN_STATS = State()  # Просмотр статистики
