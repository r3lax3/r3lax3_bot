"""
Routers aggregator: import this in the bot and forget about internals
"""
from aiogram import Router

from . import user, subscriptions, payments, history
from .admin import router as admin_router

router = Router()
router.include_router(user.router)
router.include_router(subscriptions.router)
router.include_router(payments.router)
router.include_router(history.router)
router.include_router(admin_router)
