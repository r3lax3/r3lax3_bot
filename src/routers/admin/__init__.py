"""
Admin router package aggregator
"""
from aiogram import Router

from . import entry, main, broadcast, users, services

router = Router()

router.include_router(entry.router)
router.include_router(main.router)
router.include_router(broadcast.router)
router.include_router(users.router)
router.include_router(services.router)
