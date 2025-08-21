"""
Конфигурация бота
"""
import os
from typing import List
from pydantic import BaseSettings, Field


class BotConfig(BaseSettings):
    """Конфигурация бота"""
    
    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")
    
    # Backend API
    backend_api_base_url: str = Field(..., env="BACKEND_API_BASE_URL")
    backend_api_token: str = Field(..., env="BACKEND_API_TOKEN")
    
    # Support and Language
    support_link: str = Field(..., env="SUPPORT_LINK")
    default_language: str = Field("ru", env="DEFAULT_LANGUAGE")
    timezone: str = Field("UTC", env="TIMEZONE")
    
    # Redis
    fsm_storage_url: str = Field(..., env="FSM_STORAGE_URL")
    redis_key_prefix: str = Field("clubifybot:", env="REDIS_KEY_PREFIX")
    
    # Admin
    admin_user_ids: List[int] = Field(default_factory=list)
    
    # Internal Webhook
    bot_internal_webhook_token: str = Field(..., env="BOT_INTERNAL_WEBHOOK_TOKEN")
    internal_server_host: str = Field("0.0.0.0", env="INTERNAL_SERVER_HOST")
    internal_server_port: int = Field(8080, env="INTERNAL_SERVER_PORT")
    
    # Bot Settings
    telegram_delivery_rps: int = Field(20, env="TELEGRAM_DELIVERY_RPS")
    broadcast_batch_size: int = Field(1000, env="BROADCAST_BATCH_SIZE")
    use_long_polling: bool = Field(True, env="USE_LONG_POLLING")
    idempotency_enabled: bool = Field(True, env="IDEMPOTENCY_ENABLED")
    
    # Internal webhook path
    internal_webhook_path: str = Field("/internal/payments/notify", env="INTERNAL_WEBHOOK_PATH")
    
    # Offers Directory
    offers_dir: str = Field("assets/offers", env="OFFERS_DIR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Парсим admin_user_ids из строки
        admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
        if admin_ids_str:
            self.admin_user_ids = [
                int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()
            ]


# Глобальный экземпляр конфигурации
config = BotConfig()
