"""
Встроенный HTTP-сервер для внутренних уведомлений от Backend API
"""
import asyncio
import json
import logging
from typing import Optional
from aiohttp import web
from aiogram import Bot

from src.bot.config import config
from src.storage.redis_helper import RedisHelper
from src.i18n.translations import translations
from src.clients.backend_api import api_client
from src.keyboards.inline import (
	get_payment_waiting_keyboard,
	get_payment_failed_keyboard,
	get_subscription_detail_keyboard,
)
from src.utils.formatters import calculate_minutes_until_expiry, format_date

logger = logging.getLogger(__name__)


def _unauthorized() -> web.Response:
	return web.Response(status=401, text="unauthorized")


def _bad_request(msg: str) -> web.Response:
	return web.Response(status=400, text=msg)


async def _edit_or_send(
	bot: Bot,
	redis_helper: RedisHelper,
	tg_id: int,
	payment_id: str,
	text: str,
	reply_markup,
) -> None:
	"""Редактировать сохранённое сообщение ожидания или отправить новое"""
	context = await redis_helper.get_payment_context(payment_id)
	message_id: Optional[int] = context.get("message_id") if context else None
	try:
		if message_id:
			await bot.edit_message_text(
				chat_id=tg_id,
				message_id=message_id,
				text=text,
				reply_markup=reply_markup,
			)
		else:
			msg = await bot.send_message(chat_id=tg_id, text=text, reply_markup=reply_markup)
			await redis_helper.update_payment_message_id(payment_id, msg.message_id)
	except Exception:
		# Если редактирование не удалось (удалено/устарело) — отправляем новое
		msg = await bot.send_message(chat_id=tg_id, text=text, reply_markup=reply_markup)
		await redis_helper.update_payment_message_id(payment_id, msg.message_id)


async def _handle_payment_notify(request: web.Request) -> web.Response:
	"""Обработка уведомления об изменении статуса платежа"""
	if request.headers.get("X-Internal-Token") != config.bot_internal_webhook_token:
		return _unauthorized()
	try:
		payload = await request.json()
		payment_id = payload.get("payment_id")
		status = payload.get("status")
		if not payment_id or not status:
			return _bad_request("missing fields")
		# Получаем контекст
		redis_helper: RedisHelper = request.app["redis_helper"]
		bot: Bot = request.app["bot"]
		context = await redis_helper.get_payment_context(payment_id)
		if not context:
			# Контекста нет — показываем пользователю лаконичное сообщение по платежу, если сможем запросить
			try:
				payment = await api_client.get_payment(payment_id)
				# Без tg_id не можем отправить — пропускаем
			except Exception:
				return web.Response(status=202, text="no-context")
			return web.Response(status=202, text="no-context")
		tg_id = int(context["tg_id"])
		subscription_id = int(context["subscription_id"]) if context.get("subscription_id") else None
		# Получаем детали платежа, чтобы иметь expires_at/pay_link
		try:
			payment = await api_client.get_payment(payment_id)
		except Exception as e:
			logger.error(f"get_payment failed: {e}")
			payment = {}
		expires_at = payment.get("expires_at")
		pay_link = payment.get("pay_link") or payment.get("link")
		qr_url = payment.get("qr") or payment.get("qr_url")
		language = request.app.get("default_language", config.default_language)
		# В зависимости от статуса обновляем UI
		if status in ("created", "pending"):
			minutes = calculate_minutes_until_expiry(expires_at) if expires_at else 0
			text = translations.get("payment.waiting.title", language, minutes=minutes)
			kb = get_payment_waiting_keyboard(payment_id, pay_link=pay_link, qr_url=qr_url, language=language)
			await _edit_or_send(bot, redis_helper, tg_id, payment_id, text, kb)
		elif status == "paid":
			# Переходим к карточке подписки
			until_text = "—"
			try:
				if subscription_id:
					sub = await api_client.get_subscription(subscription_id)
					until = sub.get("until_date")
					until_text = format_date(until, language) if until else "—"
			except Exception:
				pass
			text = translations.get("payment.success.title", language, until_date=until_text)
			kb = get_subscription_detail_keyboard(subscription_id, language) if subscription_id else None
			await _edit_or_send(bot, redis_helper, tg_id, payment_id, text, kb)
			# Чистим контекст
			await redis_helper.clear_payment_context(payment_id)
		else:
			# Неуспехи/прочее
			text = translations.get("payment.failed.title", language)
			kb = get_payment_failed_keyboard(payment_id, subscription_id, language) if subscription_id else None
			await _edit_or_send(bot, redis_helper, tg_id, payment_id, text, kb)
		return web.Response(status=200, text="ok")
	except Exception as e:
		logger.error(f"notify error: {e}")
		return web.Response(status=500, text="error")


async def _handle_notification_renew(request: web.Request) -> web.Response:
	"""Отправить пользователю напоминание о продлении"""
	if request.headers.get("X-Internal-Token") != config.bot_internal_webhook_token:
		return _unauthorized()
	try:
		payload = await request.json()
		tg_id = int(payload.get("tg_id"))
		subscription_id = int(payload.get("subscription_id"))
		if not tg_id or not subscription_id:
			return _bad_request("missing fields")
		bot: Bot = request.app["bot"]
		language = request.app.get("default_language", config.default_language)
		from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
		from src.keyboards.factories import RenewCallback
		kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔁 Renew", callback_data=RenewCallback(subscription_id=subscription_id).pack())]])
		text = translations.get("notification.subscription_expiring", language, date="soon")
		await bot.send_message(chat_id=tg_id, text=text, reply_markup=kb)
		return web.Response(status=200, text="ok")
	except Exception as e:
		logger.error(f"renew error: {e}")
		return web.Response(status=500, text="error")


def _build_app(bot: Bot, redis_helper: RedisHelper) -> web.Application:
	app = web.Application()
	app["bot"] = bot
	app["redis_helper"] = redis_helper
	app["default_language"] = config.default_language
	# Роуты
	app.router.add_post(config.internal_webhook_path if hasattr(config, "internal_webhook_path") else "/internal/payments/notify", _handle_payment_notify)
	app.router.add_post("/internal/notifications/renew", _handle_notification_renew)
	return app


async def start_internal_server(bot: Bot, redis_helper: RedisHelper):
	"""Запуск aiohttp-сервера; функция не завершается до отмены"""
	app = _build_app(bot, redis_helper)
	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, host=config.internal_server_host, port=config.internal_server_port)
	await site.start()
	logger.info(f"Internal server started at {config.internal_server_host}:{config.internal_server_port}")
	# Держим сервер живым
	stop_event = asyncio.Event()
	try:
		await stop_event.wait()
	except asyncio.CancelledError:
		logger.info("Internal server shutting down...")
		await runner.cleanup()
		raise
