"""
Reply клавиатуры
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.i18n.translations import translations


def get_main_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = [
        [
            KeyboardButton(text=translations.get("menu.main.subscriptions", language)),
            KeyboardButton(text=translations.get("menu.main.payment_history", language))
        ],
        [
            KeyboardButton(text=translations.get("menu.main.language", language)),
            KeyboardButton(text=translations.get("menu.main.support", language))
        ],
        [
            KeyboardButton(text=translations.get("menu.main.faq", language))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_main_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Главная клавиатура для админа"""
    keyboard = [
        [
            KeyboardButton(text=translations.get("menu.main.subscriptions", language)),
            KeyboardButton(text=translations.get("menu.main.payment_history", language))
        ],
        [
            KeyboardButton(text=translations.get("menu.main.language", language)),
            KeyboardButton(text=translations.get("menu.main.support", language))
        ],
        [
            KeyboardButton(text=translations.get("menu.main.faq", language))
        ],
        [
            KeyboardButton(text=translations.get("menu.main.admin_panel", language))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_back_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [KeyboardButton(text=translations.get("nav.back", language))]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
