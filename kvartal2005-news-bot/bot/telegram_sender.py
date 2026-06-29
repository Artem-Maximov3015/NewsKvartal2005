# -*- coding: utf-8 -*-
"""Отправка сообщений в Telegram через Bot API."""

import requests


class TelegramSendError(Exception):
    pass


def send_message(bot_token: str, chat_id: str, text: str, timeout: int = 15) -> None:
    """Отправляет одно текстовое сообщение (HTML-разметка) в чат/канал."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, data=payload, timeout=timeout)
    if not resp.ok:
        raise TelegramSendError(f"{resp.status_code}: {resp.text}")
