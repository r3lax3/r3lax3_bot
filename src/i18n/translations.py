"""
Локализация бота
"""
from typing import Dict, Any


class Translations:
    """Класс для управления переводами"""
    
    def __init__(self):
        self.translations = {
            "ru": self._get_russian_translations(),
            "en": self._get_english_translations()
        }
    
    def get(self, key: str, language: str = "ru", **kwargs) -> str:
        """Получить перевод по ключу"""
        if language not in self.translations:
            language = "ru"
        
        text = self.translations[language].get(key, key)
        
        # Подставляем плейсхолдеры
        if kwargs:
            text = text.format(**kwargs)
        
        return text
    
    def _get_russian_translations(self) -> Dict[str, str]:
        """Русские переводы"""
        return {
            # Главное меню
            "menu.main.title": "Главное меню. Выберите действие.",
            "menu.main.subscriptions": "Подписки",
            "menu.main.payment_history": "История платежей",
            "menu.main.language": "Смена языка",
            "menu.main.support": "Техподдержка",
            "menu.main.faq": "FAQ",
            "menu.main.admin_panel": "Админ-панель",
            
            # Подписки
            "subscriptions.list.title": "Список текущих подписок.\n\nНажмите на подписку для управления",
            "subscriptions.list.empty": "У вас пока нет активных подписок",
            "subscriptions.detail.title": "Название услуги: {service_name}\nПодписка активна: {until_date}",
            "subscriptions.detail.expired": "Название услуги: {service_name}\nПодписка активна: Нет",
            "subscriptions.detail.renew": "Продлить подписку",
            "subscriptions.detail.back": "Назад",
            
            # Платежи
            "payment.method_select.title": "Выберите способ оплаты и период",
            "payment.waiting.title": "Мы создали счёт. Оплатите его в течение {minutes} минут. После оплаты статус обновится автоматически.",
            "payment.success.title": "Оплата получена. Подписка активна до {until_date}.",
            "payment.failed.title": "Оплата не завершена. Попробуйте снова или выберите другой способ.",
            "payment.open_invoice": "Открыть счёт",
            "payment.check_status": "Проверить статус",
            "payment.cancel": "Отмена",
            "payment.retry": "Повторить",
            "payment.change_method": "Сменить способ",
            "payment.terms_pdf": "Оферта (PDF)",
            
            # История платежей
            "payments.history.title": "История платежей (последние {n}). Выберите платеж для подробностей.",
            "payments.history.empty": "История платежей пуста",
            "payments.detail.title": "Платёж {payment_id}\nПровайдер: {provider}\nСумма: {amount} {currency}\nСтатус: {status}\nДата: {date}\nОписание: {description}\nВнешний ID: {external_id}",
            "payments.detail.no_description": "Платёж {payment_id}\nПровайдер: {provider}\nСумма: {amount} {currency}\nСтатус: {status}\nДата: {date}\nОписание: —\nВнешний ID: {external_id}",
            "payments.detail.no_external_id": "Платёж {payment_id}\nПровайдер: {provider}\nСумма: {amount} {currency}\nСтатус: {status}\nДата: {date}\nОписание: {description}\nВнешний ID: —",
            "payments.detail.no_description_no_external": "Платёж {payment_id}\nПровайдер: {provider}\nСумма: {amount} {currency}\nСтатус: {status}\nДата: {date}\nОписание: —\nВнешний ID: —",
            
            # Язык
            "language.switched.ru": "Язык переключен на русский.",
            "language.switched.en": "Language switched to English.",
            
            # Поддержка
            "support.title": "По вопросам — {support_link}",
            
            # FAQ
            "faq.title": "Часто задаваемые вопросы",
            "faq.back": "Назад",
            
            # Оферта
            "offers.pdf.title": "Нажмите, чтобы получить оферту (PDF)",
            "offers.pdf.unavailable": "Оферта недоступна",
            
            # Навигация
            "nav.back": "Назад",
            "nav.main": "Главное меню",
            
            # Пагинация
            "pagination.page": "◀️ {page}/{pages} ▶️",
            
            # Статусы
            "status.active": "Активна",
            "status.expired": "Истекла",
            "status.paused": "Пауза",
            "status.pending": "Ожидание",
            "status.paid": "Оплачен",
            "status.failed": "Не завершён",
            "status.canceled": "Отменён",
            "status.refunded": "Возврат",
            "status.chargeback": "Чарджбэк",
            
            # Ошибки
            "error.service_unavailable": "Сервис недоступен, попробуйте позже",
            "error.network_error": "Ошибка сети, попробуйте позже",
            "error.retry": "Повторить",
            "error.too_many_requests": "Слишком много запросов. Попробуйте позже",
            
            # Админ
            "admin.broadcast.title": "Рассылка",
            "admin.broadcast.enter_text": "Введите текст рассылки (до 3500 символов):",
            "admin.broadcast.select_segment": "Выберите сегмент получателей:",
            "admin.broadcast.segment.all": "Все пользователи",
            "admin.broadcast.segment.active_subs": "С активными подписками",
            "admin.broadcast.segment.no_active_subs": "Без активных подписок",
            "admin.broadcast.segment.service": "Пользователи сервиса {service_id}",
            "admin.broadcast.preview": "Предпросмотр:\n\n{text}\n\nСегмент: {segment}\n\nОтправить всем?",
            "admin.broadcast.confirm.yes": "Да",
            "admin.broadcast.confirm.no": "Нет",
            "admin.broadcast.sending": "Отправка рассылки...",
            "admin.broadcast.complete": "Рассылка завершена\nДоставлено: {delivered}\nОшибки: {failed}\nПропущено: {skipped}",
            "admin.extend.select_plan": "Выберите план:",
            
            "admin.stats.title": "Статистика",
            "admin.stats.users_total": "Всего пользователей: {total}",
            "admin.stats.users_active": "Активных пользователей: {active}",
            "admin.stats.subscriptions_active": "Активных подписок: {active}",
            "admin.stats.monthly_revenue": "Месячный доход: {amount} {currency}",
            
            "admin.users.title": "Пользователи",
            "admin.users.search": "Поиск пользователя (по @username, tg_id или части имени):",
            "admin.users.not_found": "Пользователь не найден",
            "admin.users.profile": "Профиль пользователя {tg_id}\nЯзык: {language}\nПодписок: {subscriptions_count}",
            "admin.users.extend": "Продлить",
            "admin.users.edit_subscription": "Изменить подписку",
            
            "admin.services.title": "Сервисы",
            "admin.services.list": "Список сервисов:",
            "admin.services.status.running": "Запущена",
            "admin.services.status.paused": "Пауза",
            "admin.services.status.stopped": "Остановлена",
            "admin.services.status.error": "Ошибка",
            "admin.services.start": "Запустить",
            "admin.services.pause": "Пауза",
            "admin.services.resume": "Возобновить",
            "admin.services.stop": "Остановить",
            "admin.services.update_config": "Обновить конфигурацию",
            
            # Приветствие
            "welcome.first_time": "Добро пожаловать! Это ваш первый запуск бота.\n\nЗдесь вы можете:\n• Просматривать и управлять подписками\n• Продлевать подписки\n• Видеть историю платежей\n• Получить поддержку\n\nВыберите действие в главном меню.",
            "welcome.returning": "С возвращением! Выберите действие в главном меню.",
            
            # Уведомления
            "notification.subscription_expiring": "Подписка заканчивается {date}. Нажмите «Продлить» для продления.",
            "notification.subscription_expired": "Подписка истекла. Нажмите «Продлить» для возобновления.",
        }
    
    def _get_english_translations(self) -> Dict[str, str]:
        """Английские переводы"""
        return {
            # Main Menu
            "menu.main.title": "Main menu. Choose an action.",
            "menu.main.subscriptions": "Subscriptions",
            "menu.main.payment_history": "Payment history",
            "menu.main.language": "Language",
            "menu.main.support": "Support",
            "menu.main.faq": "FAQ",
            "menu.main.admin_panel": "Admin Panel",
            
            # Subscriptions
            "subscriptions.list.title": "Your active subscriptions.\n\nTap a subscription to manage",
            "subscriptions.list.empty": "You don't have any active subscriptions yet",
            "subscriptions.detail.title": "Service name: {service_name}\nSubscription active: {until_date}",
            "subscriptions.detail.expired": "Service name: {service_name}\nSubscription active: No",
            "subscriptions.detail.renew": "Renew",
            "subscriptions.detail.back": "Back",
            
            # Payments
            "payment.method_select.title": "Choose payment method and period",
            "payment.waiting.title": "Invoice created. Please pay within {minutes} minutes. Status will update automatically after payment.",
            "payment.success.title": "Payment received. Subscription is active until {until_date}.",
            "payment.failed.title": "Payment not completed. Try again or choose a different method.",
            "payment.open_invoice": "Open Invoice",
            "payment.check_status": "Check Status",
            "payment.cancel": "Cancel",
            "payment.retry": "Retry",
            "payment.change_method": "Change Method",
            "payment.terms_pdf": "Terms (PDF)",
            
            # Payment History
            "payments.history.title": "Payment history (last {n}). Choose a payment for details.",
            "payments.history.empty": "Payment history is empty",
            "payments.detail.title": "Payment {payment_id}\nProvider: {provider}\nAmount: {amount} {currency}\nStatus: {status}\nDate: {date}\nDescription: {description}\nExternal ID: {external_id}",
            "payments.detail.no_description": "Payment {payment_id}\nProvider: {provider}\nAmount: {amount} {currency}\nStatus: {status}\nDate: {date}\nDescription: —\nExternal ID: {external_id}",
            "payments.detail.no_external_id": "Payment {payment_id}\nProvider: {provider}\nAmount: {amount} {currency}\nStatus: {status}\nDate: {date}\nDescription: {description}\nExternal ID: —",
            "payments.detail.no_description_no_external": "Payment {payment_id}\nProvider: {provider}\nAmount: {amount} {currency}\nStatus: {status}\nDate: {date}\nDescription: —\nExternal ID: —",
            
            # Language
            "language.switched.ru": "Language switched to Russian.",
            "language.switched.en": "Language switched to English.",
            
            # Support
            "support.title": "Support — {support_link}",
            
            # FAQ
            "faq.title": "Frequently Asked Questions",
            "faq.back": "Back",
            
            # Terms
            "offers.pdf.title": "Tap to get the Terms (PDF)",
            "offers.pdf.unavailable": "Terms unavailable",
            
            # Navigation
            "nav.back": "Back",
            "nav.main": "Main Menu",
            
            # Pagination
            "pagination.page": "◀️ {page}/{pages} ▶️",
            
            # Statuses
            "status.active": "Active",
            "status.expired": "Expired",
            "status.paused": "Paused",
            "status.pending": "Pending",
            "status.paid": "Paid",
            "status.failed": "Failed",
            "status.canceled": "Canceled",
            "status.refunded": "Refunded",
            "status.chargeback": "Chargeback",
            
            # Errors
            "error.service_unavailable": "Service unavailable, try later",
            "error.network_error": "Network error, try later",
            "error.retry": "Retry",
            "error.too_many_requests": "Too many requests. Please try again later",
            
            # Admin
            "admin.broadcast.title": "Broadcast",
            "admin.broadcast.enter_text": "Enter broadcast text (up to 3500 characters):",
            "admin.broadcast.select_segment": "Select recipient segment:",
            "admin.broadcast.segment.all": "All users",
            "admin.broadcast.segment.active_subs": "With active subscriptions",
            "admin.broadcast.segment.no_active_subs": "Without active subscriptions",
            "admin.broadcast.segment.service": "Service {service_id} users",
            "admin.broadcast.preview": "Preview:\n\n{text}\n\nSegment: {segment}\n\nSend to all?",
            "admin.broadcast.confirm.yes": "Yes",
            "admin.broadcast.confirm.no": "No",
            "admin.broadcast.sending": "Sending broadcast...",
            "admin.broadcast.complete": "Broadcast completed\nDelivered: {delivered}\nFailed: {failed}\nSkipped: {skipped}",
            "admin.extend.select_plan": "Select plan:",
            
            "admin.stats.title": "Statistics",
            "admin.stats.users_total": "Total users: {total}",
            "admin.stats.users_active": "Active users: {active}",
            "admin.stats.subscriptions_active": "Active subscriptions: {active}",
            "admin.stats.monthly_revenue": "Monthly revenue: {amount} {currency}",
            
            "admin.users.title": "Users",
            "admin.users.search": "Search user (by @username, tg_id or part of name):",
            "admin.users.not_found": "User not found",
            "admin.users.profile": "User profile {tg_id}\nLanguage: {language}\nSubscriptions: {subscriptions_count}",
            "admin.users.extend": "Extend",
            "admin.users.edit_subscription": "Edit subscription",
            
            "admin.services.title": "Services",
            "admin.services.list": "Services list:",
            "admin.services.status.running": "Running",
            "admin.services.status.paused": "Paused",
            "admin.services.status.stopped": "Stopped",
            "admin.services.status.error": "Error",
            "admin.services.start": "Start",
            "admin.services.pause": "Pause",
            "admin.services.resume": "Resume",
            "admin.services.stop": "Stop",
            "admin.services.update_config": "Update config",
            
            # Welcome
            "welcome.first_time": "Welcome! This is your first time using the bot.\n\nHere you can:\n• View and manage subscriptions\n• Renew subscriptions\n• See payment history\n• Get support\n\nChoose an action in the main menu.",
            "welcome.returning": "Welcome back! Choose an action in the main menu.",
            
            # Notifications
            "notification.subscription_expiring": "Subscription expires {date}. Tap 'Renew' to extend.",
            "notification.subscription_expired": "Subscription expired. Tap 'Renew' to renew.",
        }


# Глобальный экземпляр переводов
translations = Translations()
